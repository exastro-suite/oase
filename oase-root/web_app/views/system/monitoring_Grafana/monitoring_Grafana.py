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
    Grafanaアダプタ用画面表示補助クラス
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

from web_app.models.Grafana_monitoring_models import GrafanaAdapter, GrafanaMatchInfo, GrafanaMonitoringHistory
from web_app.models.models import RuleType, DataObject
from web_app.templatetags.common import get_message
from web_app.views.system.monitoring import get_rule_type_data_obj_dict

from web_app.serializers.unicode_check import UnicodeCheck

logger = OaseLogger.get_instance() # ロガー初期化


#-------------------
# Grafana項目
#-------------------
Grafana_ITEMS = [
                   'values',
               ]

class GrafanaAdapterInfo():

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

        return 'system/Grafana/monitoring_Grafana.html'

    def get_grafana_items(self):

        grafana_item_list = ','.join(Grafana_ITEMS)

        return grafana_item_list


    def get_info_list(self, request):

        protocol_dict = self.get_define()['dict']
        rule_type_data_obj_dict = get_rule_type_data_obj_dict(request)

        try:
            grafana_adapter_obj_list = GrafanaAdapter.objects.filter(rule_type_id__in=rule_type_data_obj_dict.keys())
        except Exception as e:
            # ここでの例外は大外で拾う
            raise

        grafana_adapter_dto_list = []
        cipher = AESCipher(settings.AES_KEY)
        for grafana_obj in grafana_adapter_obj_list:
            grafana_info = grafana_obj.__dict__
            if grafana_obj.password:
                grafana_info['password'] = cipher.decrypt(grafana_obj.password)

            grafana_info['editable'] = rule_type_data_obj_dict[grafana_obj.rule_type_id]['editable']
            grafana_info['active'] = rule_type_data_obj_dict[grafana_obj.rule_type_id]['active']

            if grafana_info['active']:
                grafana_info['rule_type_name'] = rule_type_data_obj_dict[grafana_obj.rule_type_id]['rule_type_name']

                zmi_list = []
                # 突合情報取得
                try:
                    zmi_list = list(GrafanaMatchInfo.objects.filter(grafana_adapter_id=grafana_obj.grafana_adapter_id).values('data_object_id', 'grafana_response_key'))
                except Exception as e:
                    # ここでの例外は大外で拾う
                    raise

                grafana_info['match_list'] = {str(match_info['data_object_id']): match_info['grafana_response_key'] for match_info in zmi_list}

            else:
                grafana_info['rule_type_id'] = -1
                grafana_info['rule_type_name'] = ""
                grafana_info['match_list'] = {}

            grafana_adapter_dto_list.append(grafana_info)

        return grafana_adapter_dto_list


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
        GrafanaAdapter.objects.select_for_update().filter(pk=adapter_id)

        logger.logic_log('LOSI00002', 'Record locked.(grafana_adapter_id=%s)' % adapter_id, request=request)


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
            GrafanaAdapter.objects.select_for_update().filter(pk=delete_id)
            GrafanaAdapter.objects.get(pk=delete_id).delete()
            GrafanaMatchInfo.objects.filter(grafana_adapter_id=delete_id).delete()
        except GrafanaAdapter.DoesNotExist:
            # ログID追加
            logger.logic_log('LOSM33001', "grafana_adapter_id", delete_id, request=request)
            response = {
                'status': 'deleted',
                'msg': get_message('MOSJA26326',lang),
            }
        except Exception as e:
            logger.logic_log('LOSI00005', 'grafana_adapter_id: %s, trace: %s' % (delete_id, traceback.format_exc()), request=request)
            response = {
                'status': 'failure',
                'msg': get_message('MOSJA26327', lang),
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
            'grafana_disp_name' : '',
            'uri'                  : '',
            'username'             : '',
            'password'             : '',
            'rule_type_id'         : '',
            'match_list'           : '',
            'evtime'               : '',
            'instance'             : '',
        }
        now = datetime.datetime.now(pytz.timezone('UTC'))

        # 成功時データ
        response = {"status": "success",}

        try:
            grafana_adapter_id = rq['grafana_adapter_id']
            # 更新または削除の時は更新前にレコードロック
            GrafanaAdapter.objects.select_for_update().get(pk=grafana_adapter_id)

            #入力チェック
            error_flag = self._validate(rq, error_msg, request, 'edit')

            if error_flag:
                raise UserWarning('validation error.')

            # パスワードを暗号化
            cipher = AESCipher(settings.AES_KEY)
            encrypted_password = cipher.encrypt(rq['password'])

            # Grafanaアダプタの更新
            adapter = GrafanaAdapter.objects.get(pk=grafana_adapter_id)
            adapter.grafana_disp_name     = rq['grafana_disp_name']
            adapter.uri                   = rq['uri']
            adapter.username              = rq['username']
            adapter.password              = encrypted_password
            adapter.match_evtime          = rq['evtime']
            adapter.match_instance        = rq['instance']
            adapter.rule_type_id          = rq['rule_type_id']
            adapter.last_update_user      = request.user.user_name
            adapter.last_update_timestamp = now
            adapter.save(force_update=True)

            # 変更の有無にかかわらず既存のGrafana突合情報の削除
            GrafanaMatchInfo.objects.filter(grafana_adapter_id=grafana_adapter_id).delete()

            # Grafana突合情報の保存
            create_match_list = []
            for data_object_id, grafana_response_key in rq['match_list'].items():
                match = GrafanaMatchInfo(
                    grafana_adapter_id      = grafana_adapter_id,
                    data_object_id          = data_object_id,
                    grafana_response_key    = grafana_response_key,
                    last_update_user        = request.user.user_name,
                    last_update_timestamp   = now,
                )

                create_match_list.append(match)

            GrafanaMatchInfo.objects.bulk_create(create_match_list)

        except GrafanaAdapter.DoesNotExist:
            logger.logic_log('LOSM33001', "grafana_adapter_id", grafana_adapter_id, request=request)
            response = {
                'status': 'deleted',
                'msg': get_message('MOSJA26326',lang),
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
            'grafana_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'rule_type_id':'',
            'evtime'               : '',
            'instance'             : '',
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

            # パスワードを暗号化
            cipher = AESCipher(settings.AES_KEY)
            encrypted_password = cipher.encrypt(rq['password'])

            # Grafanaアダプタの追加
            grafana_adp = GrafanaAdapter(
                grafana_disp_name  = rq['grafana_disp_name'],
                uri                   = rq['uri'],
                match_evtime          = rq['evtime'],
                match_instance        = rq['instance'],
                username              = rq['username'],
                password              = encrypted_password,
                rule_type_id          = rq['rule_type_id'],
                last_update_user      = request.user.user_name,
                last_update_timestamp = now,
            )
            grafana_adp.save(force_insert=True)

            # 保存したアダプタのadapter_idを取得
            grafana_adpid = grafana_adp.grafana_adapter_id

            # Grafana突合情報の保存
            create_match_list = []
            for data_object_id, grafana_response_key in rq['match_list'].items():

                match = GrafanaMatchInfo(
                            grafana_adapter_id      = grafana_adpid,
                            data_object_id          = data_object_id, 
                            grafana_response_key    = grafana_response_key,
                            last_update_user        = request.user.user_name,
                            last_update_timestamp   = now,
                        )
                create_match_list.append(match)

            GrafanaMatchInfo.objects.bulk_create(create_match_list)


        except GrafanaAdapter.DoesNotExist:
            logger.logic_log('LOSM33002', 'uri: %s rule_type_id: %s' % (rq['uri'], rq['rule_type_id']), request=request)
            response = {
                'status': 'deleted',
                'msg': get_message('MOSJA26326',lang),
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
        emo_flag_grafana_disp_name = False
        emo_flag_uri = False
        rule_type_id_error_flag = False
        lang = request.user.get_lang_mode()

        # grafana_disp_name未入力チェック
        if len(rq['grafana_disp_name']) == 0:
            error_flag = True
            error_msg['grafana_disp_name'] += get_message('MOSJA26328', lang) + '\n'
            logger.user_log('LOSM33002', 'grafana_disp_name', request=request)

        # grafana_disp_name長さチェック
        if len(rq['grafana_disp_name']) > 64:
            error_flag = True
            error_msg['grafana_disp_name'] += get_message('MOSJA26329', lang) + '\n'
            logger.user_log('LOSM33003', 'grafana_disp_name', 64, rq['grafana_disp_name'], request=request)

        # grafana_disp_name絵文字使用チェック
        value_list = emo_chk.is_emotion(rq['grafana_disp_name'])
        if len(value_list) > 0:
            error_flag = True
            emo_flag_grafana_disp_name   = True
            error_msg['grafana_disp_name'] += get_message('MOSJA26330', lang) + '\n'
            logger.user_log('LOSM33005', rq['grafana_disp_name'], request=request)

        # URI未入力チェック
        if len(rq['uri']) == 0:
            error_flag = True
            error_msg['uri'] += get_message('MOSJA26331', lang) + '\n'
            logger.user_log('LOSM33002', 'uri', request=request)

        # URI長さチェック
        if len(rq['uri']) > 512:
            error_flag = True
            error_msg['uri'] += get_message('MOSJA26332', lang) + '\n'
            logger.user_log('LOSM33003', 'uri', 512, rq['uri'], request=request)

        # URI絵文字使用チェック
        value_list = emo_chk.is_emotion(rq['uri'])
        if len(value_list) > 0:
            error_flag = True
            emo_flag_uri = True
            error_msg['uri'] += get_message('MOSJA26333', lang) + '\n'
            logger.user_log('LOSM33005', rq['uri'], request=request)

        # username未入力チェック
        if len(rq['username']) == 0:
            error_flag = True
            error_msg['username'] += get_message('MOSJA26334', lang) + '\n'
            logger.user_log('LOSM33008', 'username', request=request)

        # username長さチェック
        if len(rq['username']) > 64:
            error_flag = True
            error_msg['username'] += get_message('MOSJA26335', lang) + '\n'
            logger.user_log('LOSM33009', 'username', 64, rq['username'], request=request)

        # username絵文字使用チェック
        value_list = emo_chk.is_emotion(rq['username'])
        if len(value_list) > 0:
            error_flag = True
            error_msg['username'] += get_message('MOSJA26336', lang) + '\n'
            logger.user_log('LOSM33010', rq['username'], request=request)

        # password未入力チェック
        if len(rq['password']) == 0:
            error_flag = True
            error_msg['password'] += get_message('MOSJA26337', lang) + '\n'
            logger.user_log('LOSM33008', 'password', request=request)

        # password長さチェック
        # 追加の場合
        if rq['grafana_adapter_id'] == '0':
            if len(rq['password']) > 64:
                error_flag = True
                error_msg['password'] += get_message('MOSJA26338', lang) + '\n'
                logger.user_log('LOSM33009', 'password', 64, rq['password'], request=request)

            # password絵文字使用チェック
            value_list = emo_chk.is_emotion(rq['password'])
            if len(value_list) > 0:
                error_flag = True
                error_msg['password'] += get_message('MOSJA26339', lang) + '\n'
                logger.user_log('LOSM33010', rq['password'], request=request)

        # 変更の場合
        else:
            old_password = GrafanaAdapter.objects.get(grafana_adapter_id=rq['grafana_adapter_id']).password
            # パスワード復号
            cipher = AESCipher(settings.AES_KEY)
            old_password_dec = cipher.decrypt(old_password)
            if old_password != rq['password']:
                if len(rq['password']) > 64:
                    error_flag = True
                    error_msg['password'] += get_message('MOSJA26338', lang) + '\n'
                    logger.user_log('LOSM33009', 'password', 64, rq['password'], request=request)

                # password絵文字使用チェック
                value_list = emo_chk.is_emotion(rq['password'])
                if len(value_list) > 0:
                    error_flag = True
                    error_msg['password'] += get_message('MOSJA26339', lang) + '\n'
                    logger.user_log('LOSM33010', rq['password'], request=request)

        # rule_type_id未入力チェック
        if len(rq['rule_type_id']) == 0:
            error_flag = True
            rule_type_id_error_flag = True
            error_msg['rule_type_id'] += get_message('MOSJA26323', lang) + '\n'
            logger.user_log('LOSM33002', 'rule_type_id', request=request)

        # rule_type_id存在チェック
        else:
            check_rule_id = RuleType.objects.filter(rule_type_id=rq['rule_type_id'])
            if len(check_rule_id) < 1:
                error_flag = True
                rule_type_id_error_flag = True
                error_msg['rule_type_id'] += get_message('MOSJA26340', lang) + '\n'
                logger.user_log('LOSM33002', 'rule_type_id', request=request)

        if not rule_type_id_error_flag:
            # evtime未入力チェック
            if len(rq['evtime']) == 0:
                error_flag = True
                error_msg['evtime'] += get_message('MOSJA26341', lang) + '\n'
                logger.user_log('LOSM33002', 'evtime', request=request)

            # evtime長さチェック
            if len(rq['evtime']) > 128:
                error_flag = True
                error_msg['evtime'] += get_message('MOSJA26342', lang) + '\n'
                logger.user_log('LOSM33003', 'evtime', 128, rq['evtime'], request=request)

            # evtime絵文字使用チェック
            value_list = emo_chk.is_emotion(rq['evtime'])
            if len(value_list) > 0:
                error_flag = True
                error_msg['evtime'] += get_message('MOSJA26343', lang) + '\n'
                logger.user_log('LOSM33005', rq['evtime'], request=request)

            # instance未入力チェック
            if len(rq['instance']) == 0:
                error_flag = True
                error_msg['instance'] += get_message('MOSJA26344', lang) + '\n'
                logger.user_log('LOSM33002', 'instance', request=request)

            # instance長さチェック
            if len(rq['instance']) > 128:
                error_flag = True
                error_msg['instance'] += get_message('MOSJA26345', lang) + '\n'
                logger.user_log('LOSM33003', 'instance', 128, rq['instance'], request=request)

            # instance絵文字使用チェック
            value_list = emo_chk.is_emotion(rq['instance'])
            if len(value_list) > 0:
                error_flag = True
                error_msg['instance'] += get_message('MOSJA26346', lang) + '\n'
                logger.user_log('LOSM33005', rq['instance'], request=request)


            # 突合情報存在チェック

            # 条件名の数を取得
            do_list = DataObject.objects.filter(rule_type_id=rq['rule_type_id']).values_list('data_object_id', flat=True)

            # Grafana項目チェック
            for data_object_id, grafana_response_key in rq['match_list'].items():
                id_name = 'grafana-' + data_object_id
                error_msg.setdefault(id_name,'')

                # 条件名とGrafana項目の数があっているかチェック
                if len(do_list) != len(rq['match_list'].keys()):
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26347', request.user.get_lang_mode()) + '\n'
                    logger.user_log('LOSM33007', len(do_list), len(rq['match_list'].items()), request=request)

                if len(grafana_response_key) == 0:
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26348', lang) + '\n'
                    logger.user_log('LOSM33002', 'grafana_response_key', request=request)

                if len(grafana_response_key) > 128:
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26349', lang) + '\n'
                    logger.user_log('LOSM33003', 'grafana_response_key', 128, grafana_response_key, request=request)

                # Grafana項目絵文字使用チェック
                value_list = emo_chk.is_emotion(grafana_response_key)
                if len(value_list) > 0:
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26350', lang) + '\n'
                    logger.user_log('LOSM33005', rq['grafana_disp_name'], request=request)

                # 使用可能名チェック
                """
                if grafana_response_key not in Grafana_ITEMS:
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26351', lang) + '\n'
                    logger.user_log('LOSM33006', rq['grafana_disp_name'], request=request)
                """

        # grafana_disp_name重複チェック
        if not emo_flag_grafana_disp_name:
            duplication = GrafanaAdapter.objects.filter(grafana_disp_name=rq['grafana_disp_name'])
            if len(duplication) == 1 and int(rq['grafana_adapter_id']) != duplication[0].grafana_adapter_id:
                error_flag = True
                error_msg['grafana_disp_name'] += get_message('MOSJA26315', lang) + '\n'
                logger.user_log('LOSM33004', 'grafana_disp_name', rq['grafana_disp_name'], request=request)

        # uri重複チェック
        if not emo_flag_uri:
            duplication = GrafanaAdapter.objects.filter(uri=rq['uri'], rule_type_id=rq['rule_type_id'])

            # ホスト名重複かつルール種別名が同一の場合
            if len(duplication) == 1 and int(rq['grafana_adapter_id']) != duplication[0].grafana_adapter_id:
                error_flag = True
                error_msg['uri'] += get_message('MOSJA26316', request.user.get_lang_mode()) + '\n'
                logger.user_log('LOSM33004', 'uri', rq['uri'], request=request)


        logger.logic_log('LOSI00002', 'return: %s' % error_flag)
        return error_flag

