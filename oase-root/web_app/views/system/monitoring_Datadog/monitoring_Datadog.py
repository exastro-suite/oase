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
    Datadogアダプタ用画面表示補助クラス
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

from web_app.models.Datadog_monitoring_models import DatadogAdapter, DatadogMatchInfo, DatadogMonitoringHistory
from web_app.models.models import RuleType, DataObject
from web_app.templatetags.common import get_message
from web_app.views.system.monitoring import get_rule_type_data_obj_dict

from web_app.serializers.unicode_check import UnicodeCheck

logger = OaseLogger.get_instance() # ロガー初期化


#-------------------
# Datadog項目
#-------------------
Datadog_ITEMS = [
                   'values',
               ]

class DatadogAdapterInfo():

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

        return 'system/Datadog/monitoring_Datadog.html'

    def get_datadog_items(self):

        datadog_item_list = ','.join(Datadog_ITEMS)

        return datadog_item_list


    def get_info_list(self, request):

        protocol_dict = self.get_define()['dict']
        rule_type_data_obj_dict = get_rule_type_data_obj_dict(request)

        try:
            datadog_adapter_obj_list = DatadogAdapter.objects.filter(rule_type_id__in=rule_type_data_obj_dict.keys())
        except Exception as e:
            # ここでの例外は大外で拾う
            raise

        datadog_adapter_dto_list = []

        for datadog_obj in datadog_adapter_obj_list:
            datadog_info = datadog_obj.__dict__

            datadog_info['editable'] = rule_type_data_obj_dict[datadog_obj.rule_type_id]['editable']
            datadog_info['active'] = rule_type_data_obj_dict[datadog_obj.rule_type_id]['active']

            if datadog_info['active']:
                datadog_info['rule_type_name'] = rule_type_data_obj_dict[datadog_obj.rule_type_id]['rule_type_name']

                zmi_list = []
                # 突合情報取得
                try:
                    zmi_list = list(DatadogMatchInfo.objects.filter(datadog_adapter_id=datadog_obj.datadog_adapter_id).values('data_object_id', 'datadog_response_key'))
                except Exception as e:
                    # ここでの例外は大外で拾う
                    raise

                datadog_info['match_list'] = {str(match_info['data_object_id']): match_info['datadog_response_key'] for match_info in zmi_list}

            else:
                datadog_info['rule_type_id'] = -1
                datadog_info['rule_type_name'] = ""
                datadog_info['match_list'] = {}

            datadog_adapter_dto_list.append(datadog_info)

        return datadog_adapter_dto_list


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
        DatadogAdapter.objects.select_for_update().filter(pk=adapter_id)

        logger.logic_log('LOSI00002', 'Record locked.(datadog_adapter_id=%s)' % adapter_id, request=request)


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
            DatadogAdapter.objects.select_for_update().filter(pk=delete_id)
            DatadogAdapter.objects.get(pk=delete_id).delete()
            DatadogMatchInfo.objects.filter(datadog_adapter_id=delete_id).delete()
        except DatadogAdapter.DoesNotExist:
            # ログID追加
            logger.logic_log('LOSM39001', "datadog_adapter_id", delete_id, request=request)
            response = {
                'status': 'deleted',
                'msg': get_message('MOSJA26417',lang),
            }
        except Exception as e:
            logger.logic_log('LOSI00005', 'datadog_adapter_id: %s, trace: %s' % (delete_id, traceback.format_exc()), request=request)
            response = {
                'status': 'failure',
                'msg': get_message('MOSJA26440', lang),
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
            'datadog_disp_name' : '',
            'uri'               : '',
            'api_key'           : '',
            'application_key'   : '',
            'proxy'             : '',
            'rule_type_id'      : '',
            'match_list'        : '',
        }
        now = datetime.datetime.now(pytz.timezone('UTC'))

        # 成功時データ
        response = {"status": "success",}

        try:
            datadog_adapter_id = rq['datadog_adapter_id']
            # 更新または削除の時は更新前にレコードロック
            DatadogAdapter.objects.select_for_update().get(pk=datadog_adapter_id)

            #入力チェック
            error_flag = self._validate(rq, error_msg, request, 'edit')

            if error_flag:
                raise UserWarning('validation error.')

            # Datadogアダプタの更新
            adapter = DatadogAdapter.objects.get(pk=datadog_adapter_id)
            adapter.datadog_disp_name     = rq['datadog_disp_name']
            adapter.uri                   = rq['uri']
            adapter.api_key               = rq['api_key']
            adapter.application_key       = rq['application_key']
            adapter.proxy                 = rq['proxy']
            adapter.rule_type_id          = rq['rule_type_id']
            adapter.last_update_user      = request.user.user_name
            adapter.last_update_timestamp = now
            adapter.save(force_update=True)

            # 変更の有無にかかわらず既存のGrafana突合情報の削除
            DatadogMatchInfo.objects.filter(datadog_adapter_id=datadog_adapter_id).delete()

            # Datadog突合情報の保存
            create_match_list = []
            for data_object_id, datadog_response_key in rq['match_list'].items():
                match = DatadogMatchInfo(
                    datadog_adapter_id      = datadog_adapter_id,
                    data_object_id          = data_object_id,
                    datadog_response_key    = datadog_response_key,
                    last_update_user        = request.user.user_name,
                    last_update_timestamp   = now,
                )

                create_match_list.append(match)

            DatadogMatchInfo.objects.bulk_create(create_match_list)

        except DatadogAdapter.DoesNotExist:
            logger.logic_log('LOSM39001', "datadog_adapter_id", datadog_adapter_id, request=request)
            response = {
                'status': 'deleted',
                'msg': get_message('MOSJA26417',lang),
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
            'datadog_disp_name' : '',
            'uri'               : '',
            'api_key'           : '',
            'application_key'   : '',
            'proxy'             : '',
            'rule_type_id'      :'',
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

            # Datadogアダプタの追加
            datadog_adp = DatadogAdapter(
                datadog_disp_name     = rq['datadog_disp_name'],
                uri                   = rq['uri'],
                api_key               = rq['api_key'],
                application_key       = rq['application_key'],
                rule_type_id          = rq['rule_type_id'],
                proxy                 = rq['proxy'],
                last_update_user      = request.user.user_name,
                last_update_timestamp = now,
            )
            datadog_adp.save(force_insert=True)

            # 保存したアダプタのadapter_idを取得
            datadog_adpid = datadog_adp.datadog_adapter_id

            # Datadog突合情報の保存
            create_match_list = []
            for data_object_id, datadog_response_key in rq['match_list'].items():

                match = DatadogMatchInfo(
                            datadog_adapter_id      = datadog_adpid,
                            data_object_id          = data_object_id, 
                            datadog_response_key    = datadog_response_key,
                            last_update_user        = request.user.user_name,
                            last_update_timestamp   = now,
                        )
                create_match_list.append(match)

            DatadogMatchInfo.objects.bulk_create(create_match_list)


        except DatadogAdapter.DoesNotExist:
            logger.logic_log('LOSM39002', 'uri: %s rule_type_id: %s' % (rq['uri'], rq['rule_type_id']), request=request)
            response = {
                'status': 'deleted',
                'msg': get_message('MOSJA26417',lang),
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
        emo_flag_datadog_disp_name = False
        emo_flag_uri = False
        rule_type_id_error_flag = False
        lang = request.user.get_lang_mode()

        # datadog_disp_name未入力チェック
        if len(rq['datadog_disp_name']) == 0:
            error_flag = True
            error_msg['datadog_disp_name'] += get_message('MOSJA26418', lang) + '\n'
            logger.user_log('LOSM39002', 'datadog_disp_name', request=request)

        # datadog_disp_name長さチェック
        if len(rq['datadog_disp_name']) > 64:
            error_flag = True
            error_msg['datadog_disp_name'] += get_message('MOSJA26419', lang) + '\n'
            logger.user_log('LOSM39003', 'datadog_disp_name', 64, rq['datadog_disp_name'], request=request)

        # datadog_disp_name絵文字使用チェック
        value_list = emo_chk.is_emotion(rq['datadog_disp_name'])
        if len(value_list) > 0:
            error_flag = True
            emo_flag_datadog_disp_name   = True
            error_msg['datadog_disp_name'] += get_message('MOSJA26420', lang) + '\n'
            logger.user_log('LOSM39005', rq['datadog_disp_name'], request=request)

        # URI未入力チェック
        if len(rq['uri']) == 0:
            error_flag = True
            error_msg['uri'] += get_message('MOSJA26441', lang) + '\n'
            logger.user_log('LOSM39002', 'uri', request=request)

        # URI長さチェック
        if len(rq['uri']) > 512:
            error_flag = True
            error_msg['uri'] += get_message('MOSJA26442', lang) + '\n'
            logger.user_log('LOSM39003', 'uri', 512, rq['uri'], request=request)

        # URI絵文字使用チェック
        value_list = emo_chk.is_emotion(rq['uri'])
        if len(value_list) > 0:
            error_flag = True
            emo_flag_uri = True
            error_msg['uri'] += get_message('MOSJA26443', lang) + '\n'
            logger.user_log('LOSM39005', rq['uri'], request=request)

        # api_key未入力チェック
        if len(rq['api_key']) == 0:
            error_flag = True
            error_msg['api_key'] += get_message('MOSJA26421', lang) + '\n'
            logger.user_log('LOSM39008', 'api_key', request=request)

        # api_key長さチェック
        if len(rq['api_key']) > 48:
            error_flag = True
            error_msg['api_key'] += get_message('MOSJA26422', lang) + '\n'
            logger.user_log('LOSM39009', 'api_key', 48, rq['api_key'], request=request)

        # api_key絵文字使用チェック
        value_list = emo_chk.is_emotion(rq['api_key'])
        if len(value_list) > 0:
            error_flag = True
            error_msg['api_key'] += get_message('MOSJA26423', lang) + '\n'
            logger.user_log('LOSM39010', rq['api_key'], request=request)

        # application_key未入力チェック
        if len(rq['application_key']) == 0:
            error_flag = True
            error_msg['application_key'] += get_message('MOSJA26425', lang) + '\n'
            logger.user_log('LOSM39008', 'application_key', request=request)

        # application_key長さチェック
        if len(rq['application_key']) > 48:
            error_flag = True
            error_msg['application_key'] += get_message('MOSJA26424', lang) + '\n'
            logger.user_log('LOSM39009', 'application_key', 48, rq['application_key'], request=request)

        # application_key絵文字使用チェック
        value_list = emo_chk.is_emotion(rq['application_key'])
        if len(value_list) > 0:
            error_flag = True
            error_msg['application_key'] += get_message('MOSJA26426', lang) + '\n'
            logger.user_log('LOSM39010', rq['application_key'], request=request)

        # プロキシ長さチェック
        if len(rq['proxy']) > 256:
            error_flag = True
            error_msg['proxy'] += get_message('MOSJA26445', lang) + '\n'
            logger.user_log('LOSM39003', 'proxy', 256, rq['proxy'], request=request)

        # プロキシ絵文字使用チェック
        value_list = emo_chk.is_emotion(rq['proxy'])
        if len(value_list) > 0:
            error_flag = True
            emo_flag_uri = True
            error_msg['proxy'] += get_message('MOSJA26446', lang) + '\n'
            logger.user_log('LOSM39005', rq['proxy'], request=request)

        # rule_type_id未入力チェック
        if len(rq['rule_type_id']) == 0:
            error_flag = True
            rule_type_id_error_flag = True
            error_msg['rule_type_id'] += get_message('MOSJA26427', lang) + '\n'
            logger.user_log('LOSM39002', 'rule_type_id', request=request)

        # rule_type_id存在チェック
        else:
            check_rule_id = RuleType.objects.filter(rule_type_id=rq['rule_type_id'])
            if len(check_rule_id) < 1:
                error_flag = True
                rule_type_id_error_flag = True
                error_msg['rule_type_id'] += get_message('MOSJA26428', lang) + '\n'
                logger.user_log('LOSM39002', 'rule_type_id', request=request)

            # 突合情報存在チェック

            # 条件名の数を取得
            do_list = DataObject.objects.filter(rule_type_id=rq['rule_type_id']).values_list('data_object_id', flat=True)

            # Datadog項目チェック
            for data_object_id, datadog_response_key in rq['match_list'].items():
                id_name = 'datadog-' + data_object_id
                error_msg.setdefault(id_name,'')

                # 条件名とDatadog項目の数があっているかチェック
                if len(do_list) != len(rq['match_list'].keys()):
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26444', request.user.get_lang_mode()) + '\n'
                    logger.user_log('LOSM39007', len(do_list), len(rq['match_list'].items()), request=request)

                if len(datadog_response_key) == 0:
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26429', lang) + '\n'
                    logger.user_log('LOSM39002', 'datadog_response_key', request=request)

                if len(datadog_response_key) > 128:
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26430', lang) + '\n'
                    logger.user_log('LOSM39003', 'datadog_response_key', 128, datadog_response_key, request=request)

                # Datadog項目絵文字使用チェック
                value_list = emo_chk.is_emotion(datadog_response_key)
                if len(value_list) > 0:
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26431', lang) + '\n'
                    logger.user_log('LOSM39005', rq['datadog_disp_name'], request=request)

        # datadog_disp_name重複チェック
        if not emo_flag_datadog_disp_name:
            duplication = DatadogAdapter.objects.filter(datadog_disp_name=rq['datadog_disp_name'])
            if len(duplication) >= 1 and int(rq['datadog_adapter_id']) != duplication[0].datadog_adapter_id:
                error_flag = True
                error_msg['datadog_disp_name'] += get_message('MOSJA26433', lang) + '\n'
                logger.user_log('LOSM39004', 'datadog_disp_name', rq['datadog_disp_name'], request=request)

        # ホスト名重複かつルール種別名が同一の場合、今回はURIは固定
        duplication = DatadogAdapter.objects.filter(rule_type_id=rq['rule_type_id'])
        if len(duplication) >= 1 and int(rq['datadog_adapter_id']) != duplication[0].datadog_adapter_id:
            error_flag = True
            error_msg['rule_type_id'] += get_message('MOSJA26434', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM39004', 'rule_type_id',rq['rule_type_id'], request=request)


        logger.logic_log('LOSI00002', 'return: %s' % error_flag)
        return error_flag

