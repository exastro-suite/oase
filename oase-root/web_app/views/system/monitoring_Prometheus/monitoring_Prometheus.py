# Copyright 2019 NEC Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


"""
[概要]
    Prometheusアダプタ用画面表示補助クラス
"""


import pytz
import datetime
import json
import socket
import traceback

from django.http import HttpResponse
from django.http import HttpResponseServerError
from django.db import transaction
from django.conf import settings

from libs.commonlibs import define as defs
from libs.commonlibs.oase_logger import OaseLogger
from libs.commonlibs.aes_cipher import AESCipher

from web_app.models.Prometheus_monitoring_models import PrometheusAdapter, PrometheusMatchInfo, PrometheusMonitoringHistory
from web_app.models.models import RuleType, DataObject
from web_app.templatetags.common import get_message
from web_app.views.system.monitoring import get_rule_type_data_obj_dict

from web_app.serializers.unicode_check import UnicodeCheck

logger = OaseLogger.get_instance() # ロガー初期化


#-------------------
# Prometheus項目
#-------------------
Prometheus_ITEMS = [
                   'values',
               ]

class PrometheusAdapterInfo():

    def __init__(self, adp_id, mni_id, name, ver, icon_name):

        self.adp_id = adp_id
        self.mni_id = mni_id
        self.name   = name
        self.ver    = ver
        self.icon_name = icon_name

    def __str__(self):

        return '%s(ver%s)' % (self.name, self.ver)

    def get_adapter_name(self):

        return '%s Adapter ver%s' % (self.name, self.ver)

    def get_adapter_id(self):

        return self.adp_id

    def get_icon_name(self):

        return self.icon_name

    def get_template_file(self):

        return 'system/Prometheus/monitoring_Prometheus.html'

    def get_prometheus_items(self):

        prometheus_item_list = ','.join(Prometheus_ITEMS)

        return prometheus_item_list


    def get_info_list(self, request):

        protocol_dict = self.get_define()['dict']
        rule_type_data_obj_dict = get_rule_type_data_obj_dict(request)

        try:
            prometheus_adapter_obj_list = PrometheusAdapter.objects.filter(rule_type_id__in=rule_type_data_obj_dict.keys())
        except Exception as e:
            # ここでの例外は大外で拾う
            raise

        prometheus_adapter_dto_list = []
        cipher = AESCipher(settings.AES_KEY)
        for prometheus_obj in prometheus_adapter_obj_list:
            prometheus_info = prometheus_obj.__dict__

            prometheus_info['editable'] = rule_type_data_obj_dict[prometheus_obj.rule_type_id]['editable']
            prometheus_info['active'] = rule_type_data_obj_dict[prometheus_obj.rule_type_id]['active']

            if prometheus_info['active']:
                prometheus_info['rule_type_name'] = rule_type_data_obj_dict[prometheus_obj.rule_type_id]['rule_type_name']

                zmi_list = []
                # 突合情報取得
                try:
                    zmi_list = list(PrometheusMatchInfo.objects.filter(prometheus_adapter_id=prometheus_obj.prometheus_adapter_id).values('data_object_id', 'prometheus_response_key'))
                except Exception as e:
                    # ここでの例外は大外で拾う
                    raise

                prometheus_info['match_list'] = {str(match_info['data_object_id']): match_info['prometheus_response_key'] for match_info in zmi_list}

            else:
                prometheus_info['rule_type_id'] = -1
                prometheus_info['rule_type_name'] = ""
                prometheus_info['match_list'] = {}

            prometheus_adapter_dto_list.append(prometheus_info)

        return prometheus_adapter_dto_list


    def get_define(self):

        protocol_dict = {key_value['v']: key_value['k']  for key_value in defs.HTTP_PROTOCOL.LIST_ALL}

        defines = {
            'list_all': defs.HTTP_PROTOCOL.LIST_ALL,
            'dict': protocol_dict,
        }

        return defines


    def record_lock(self, adapter_id, request):

        logger.logic_log('LOSI00001', 'None', request=request)

        # 更新または削除の時は更新前にレコードロック
        PrometheusAdapter.objects.select_for_update().filter(pk=adapter_id)

        logger.logic_log('LOSI00002', 'Record locked.(prometheus_adapter_id=%s)' % adapter_id, request=request)


    def delete(self, json_str, request):
        """
        [メソッド概要]
          DB削除処理
        """
        logger.logic_log('LOSI00001', 'None', request=request)

        lang = request.user.get_lang_mode()
        response = {"status": "success"}
        delete_id = json_str['record_id']

        try:
            # TBLにロックかける
            PrometheusAdapter.objects.select_for_update().filter(pk=delete_id)
            PrometheusAdapter.objects.get(pk=delete_id).delete()
            PrometheusMatchInfo.objects.filter(prometheus_adapter_id=delete_id).delete()
        except PrometheusAdapter.DoesNotExist:
            # ログID追加
            logger.logic_log('LOSM32004', "prometheus_adapter_id", delete_id, request=request)
            response = {
                'status': 'deleted',
                'msg': get_message('MOSJA26219',lang),
            }
        except Exception as e:
            logger.logic_log('LOSI00005', 'prometheus_adapter_id: %s, trace: %s' % (delete_id, traceback.format_exc()), request=request)
            response = {
                'status': 'failure',
                'msg': get_message('MOSJA26220', lang),
            }

        logger.logic_log('LOSI00002', 'response=%s' % response, request=request)

        return response


    def update(self, rq, request):
        """
        [メソッド概要]
          DB更新処理
        """
        logger.logic_log('LOSI00001', 'None', request=request)
        lang = request.user.get_lang_mode()

        error_flag = False
        error_msg  = {
            'prometheus_disp_name' : '',
            'uri'                  : '',
            'query'                : '',
            'rule_type_id'         : '',
            'match_list'           : '',
        }
        now = datetime.datetime.now(pytz.timezone('UTC'))

        # 成功時データ
        response = {"status": "success",}

        try:
            prometheus_adapter_id = rq['prometheus_adapter_id']
            # 更新または削除の時は更新前にレコードロック
            PrometheusAdapter.objects.select_for_update().get(pk=prometheus_adapter_id)

            #入力チェック
            error_flag = self._validate(rq, error_msg, request, 'edit')

            if error_flag:
                raise UserWarning('validation error.')

            # Prometheusアダプタの更新
            adapter = PrometheusAdapter.objects.get(pk=prometheus_adapter_id)
            adapter.prometheus_disp_name  = rq['prometheus_disp_name']
            adapter.uri                   = rq['uri']
            adapter.metric                = rq['query']
            adapter.rule_type_id          = rq['rule_type_id']
            adapter.last_update_user      = request.user.user_name
            adapter.last_update_timestamp = now
            adapter.save(force_update=True)

            # 変更の有無にかかわらず既存のPrometheus突合情報の削除
            PrometheusMatchInfo.objects.filter(prometheus_adapter_id=prometheus_adapter_id).delete()

            # Prometheus突合情報の保存
            create_match_list = []
            for data_object_id, prometheus_response_key in rq['match_list'].items():
                match = PrometheusMatchInfo(
                    prometheus_adapter_id   = prometheus_adapter_id,
                    data_object_id          = data_object_id,
                    prometheus_response_key = prometheus_response_key,
                    last_update_user        = request.user.user_name,
                    last_update_timestamp   = now,
                )

                create_match_list.append(match)

            PrometheusMatchInfo.objects.bulk_create(create_match_list)

        except PrometheusAdapter.DoesNotExist:
            logger.logic_log('LOSM32004', "prometheus_adapter_id", prometheus_adapter_id, request=request)
            response = {
                'status': 'deleted',
                'msg': get_message('MOSJA26219',lang),
            }

        except Exception as e:
            logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
            response = {
                    'status': 'failure',
                    'msg': error_msg,  # エラー詳細(エラーアイコンで出す)
            }

        logger.logic_log('LOSI00002', 'response=%s' % response, request=request)

        return response


    def create(self, json_str, request):
        """
        [メソッド概要]
          DB作成処理
        """

        logger.logic_log('LOSI00001', 'json_str: %s' %(json_str), request=request)
        lang = request.user.get_lang_mode()

        error_flag = False
        error_msg  = {
            'prometheus_disp_name' : '',
            'uri' : '',
            'query' : '',
            'rule_type_id':'',
        }
        now = datetime.datetime.now(pytz.timezone('UTC'))

        # 成功時データ
        response = {"status": "success",}

        try:
            rq = json_str

            #入力チェック
            error_flag = self._validate(rq, error_msg, request, 'add')

            if error_flag:
                raise UserWarning('validation error.')

            # Prometheusアダプタの追加
            prometheus_adp = PrometheusAdapter(
                prometheus_disp_name  = rq['prometheus_disp_name'],
                uri                   = rq['uri'],
                metric                = rq['query'],
                rule_type_id          = rq['rule_type_id'],
                last_update_user      = request.user.user_name,
                last_update_timestamp = now,
            )
            prometheus_adp.save(force_insert=True)

            # 保存したアダプタのadapter_idを取得
            prometheus_adpid = prometheus_adp.prometheus_adapter_id

            # Prometheus突合情報の保存
            create_match_list = []
            for data_object_id, prometheus_response_key in rq['match_list'].items():

                match = PrometheusMatchInfo(
                            prometheus_adapter_id   = prometheus_adpid,
                            data_object_id          = data_object_id, 
                            prometheus_response_key = prometheus_response_key,
                            last_update_user        = request.user.user_name,
                            last_update_timestamp   = now,
                        )
                create_match_list.append(match)

            PrometheusMatchInfo.objects.bulk_create(create_match_list)


        except PrometheusAdapter.DoesNotExist:
            logger.logic_log('LOSM32001', 'uri: %s rule_type_id: %s' % (rq['uri'], rq['rule_type_id']), request=request)
            response = {
                'status': 'deleted',
                'msg': get_message('MOSJA26219',lang),
            }

        except Exception as e:
            logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
            response = {
                    'status': 'failure',
                    'msg': error_msg,  # エラー詳細(エラーアイコンで出す)
            }

        logger.logic_log('LOSI00002', 'response=%s' % response, request=request)

        return response


    def _validate(self, rq, error_msg, request, mode):
        """
        [概要]
        入力チェック
        [引数]
        rq: dict リクエストされた入力データ
        error_msg: dict
        [戻り値]
        """

        logger.logic_log('LOSI00001', 'data: %s, error_msg:%s'%(rq, error_msg))
        error_flag = False
        emo_chk = UnicodeCheck()
        emo_flag_prometheus_disp_name = False
        emo_flag_uri = False
        rule_type_id_error_flag = False
        lang = request.user.get_lang_mode()

        # prometheus_disp_name未入力チェック
        if len(rq['prometheus_disp_name']) == 0:
            error_flag = True
            error_msg['prometheus_disp_name'] += get_message('MOSJA26221', lang) + '\n'
            logger.user_log('LOSM32001', 'prometheus_disp_name', request=request)

        # prometheus_disp_name長さチェック
        if len(rq['prometheus_disp_name']) > 64:
            error_flag = True
            error_msg['prometheus_disp_name'] += get_message('MOSJA26222', lang) + '\n'
            logger.user_log('LOSM32002', 'prometheus_disp_name', 64, rq['prometheus_disp_name'], request=request)

        # prometheus_disp_name絵文字使用チェック
        value_list = emo_chk.is_emotion(rq['prometheus_disp_name'])
        if len(value_list) > 0:
            error_flag = True
            emo_flag_prometheus_disp_name   = True
            error_msg['prometheus_disp_name'] += get_message('MOSJA26223', lang) + '\n'
            logger.user_log('LOSM32006', rq['prometheus_disp_name'], request=request)

        # URI未入力チェック
        if len(rq['uri']) == 0:
            error_flag = True
            error_msg['uri'] += get_message('MOSJA26224', lang) + '\n'
            logger.user_log('LOSM32001', 'uri', request=request)

        # URI長さチェック
        if len(rq['uri']) > 512:
            error_flag = True
            error_msg['uri'] += get_message('MOSJA26225', lang) + '\n'
            logger.user_log('LOSM32002', 'uri', 512, rq['uri'], request=request)

        # URI絵文字使用チェック
        value_list = emo_chk.is_emotion(rq['uri'])
        if len(value_list) > 0:
            error_flag = True
            emo_flag_uri = True
            error_msg['uri'] += get_message('MOSJA26226', lang) + '\n'
            logger.user_log('LOSM32006', rq['uri'], request=request)

        # query長さチェック
        if len(rq['query']) > 128:
            error_flag = True
            error_msg['query'] += get_message('MOSJA26242', lang) + '\n'
            logger.user_log('LOSM32002', 'query', 128, rq['query'], request=request)

        # query絵文字使用チェック
        value_list = emo_chk.is_emotion(rq['query'])
        if len(value_list) > 0:
            error_flag = True
            error_msg['query'] += get_message('MOSJA26243', lang) + '\n'
            logger.user_log('LOSM32006', rq['query'], request=request)


        # rule_type_id未入力チェック
        if len(rq['rule_type_id']) == 0:
            error_flag = True
            rule_type_id_error_flag = True
            error_msg['rule_type_id'] += get_message('MOSJA26215', lang) + '\n'
            logger.user_log('LOSM32001', 'rule_type_id', request=request)

        # rule_type_id存在チェック
        else:
            check_rule_id = RuleType.objects.filter(rule_type_id=rq['rule_type_id'])
            if len(check_rule_id) < 1:
                error_flag = True
                rule_type_id_error_flag = True
                error_msg['rule_type_id'] += get_message('MOSJA26233', lang) + '\n'
                logger.user_log('LOSM32001', 'rule_type_id', request=request)

        if not rule_type_id_error_flag:
            # 突合情報存在チェック

            # 条件名の数を取得
            do_list = DataObject.objects.filter(rule_type_id=rq['rule_type_id']).values_list('data_object_id', flat=True)

            # Prometheus項目チェック
            for data_object_id, prometheus_response_key in rq['match_list'].items():
                id_name = 'prometheus-' + data_object_id
                error_msg.setdefault(id_name,'')

                # 条件名とPrometheus項目の数があっているかチェック
                if len(do_list) != len(rq['match_list'].keys()):
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26235', request.user.get_lang_mode()) + '\n'
                    logger.user_log('LOSM32005', len(do_list), len(rq['match_list'].items()), request=request)

                if len(prometheus_response_key) == 0:
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26236', lang) + '\n'
                    logger.user_log('LOSM32001', 'prometheus_response_key', request=request)

                if len(prometheus_response_key) > 32:
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26238', lang) + '\n'
                    logger.user_log('LOSM32002', 'prometheus_response_key', 32, prometheus_response_key, request=request)

                # Prometheus項目絵文字使用チェック
                value_list = emo_chk.is_emotion(prometheus_response_key)
                if len(value_list) > 0:
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26237', lang) + '\n'
                    logger.user_log('LOSM32006', rq['prometheus_disp_name'], request=request)

                # 使用可能名チェック
                if prometheus_response_key not in Prometheus_ITEMS:
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26240', lang) + '\n'
                    logger.user_log('LOSM32007', rq['prometheus_disp_name'], request=request)

        # prometheus_disp_name重複チェック
        if not emo_flag_prometheus_disp_name:
            duplication = PrometheusAdapter.objects.filter(prometheus_disp_name=rq['prometheus_disp_name'])
            if len(duplication) == 1 and int(rq['prometheus_adapter_id']) != duplication[0].prometheus_adapter_id:
                error_flag = True
                error_msg['prometheus_disp_name'] += get_message('MOSJA26217', lang) + '\n'
                logger.user_log('LOSM32003', 'prometheus_disp_name', rq['prometheus_disp_name'], request=request)

        # uri重複チェック
        if not emo_flag_uri:
            duplication = PrometheusAdapter.objects.filter(uri=rq['uri'], rule_type_id=rq['rule_type_id'])

            # ホスト名重複かつルール種別名が同一の場合
            if len(duplication) == 1 and int(rq['prometheus_adapter_id']) != duplication[0].prometheus_adapter_id:
                error_flag = True
                error_msg['uri'] += get_message('MOSJA26218', request.user.get_lang_mode()) + '\n'
                logger.user_log('LOSM32003', 'uri', rq['uri'], request=request)


        logger.logic_log('LOSI00002', 'return: %s' % error_flag)
        return error_flag

