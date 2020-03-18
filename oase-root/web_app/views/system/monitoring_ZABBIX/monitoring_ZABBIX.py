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
    ZABBIXアダプタ用画面表示補助クラス

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

from web_app.models.ZABBIX_monitoring_models import ZabbixAdapter, ZabbixMatchInfo, ZabbixMonitoringHistory
from web_app.models.models import RuleType, DataObject
from web_app.templatetags.common import get_message
from web_app.views.system.monitoring import get_rule_type_data_obj_dict

from web_app.serializers.unicode_check import UnicodeCheck

logger = OaseLogger.get_instance() # ロガー初期化

#-------------------
# ZABBIX項目
#-------------------
ZABBIX_ITEMS = [
                   'triggerid',
                   'expression',
                   'description',
                   'url',
                   'status',
                   'value',
                   'priority',
                   'lastchange',
                   'comments',
                   'error',
                   'templateid',
                   'type',
                   'state',
                   'flags',
                   'recovery_mode',
                   'recovery_expression',
                   'correlation_mode',
                   'correlation_tag',
                   'manual_close',
                   'details',
                   'hosts',
               ]

class ZABBIXAdapterInfo():

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

        return 'system/ZABBIX/monitoring_ZABBIX.html'

    def get_zabbix_items(self):
        
        zabbix_item_list = ','.join(ZABBIX_ITEMS)

        return zabbix_item_list

    def get_info_list(self, request):

        protocol_dict = self.get_define()['dict']
        rule_type_data_obj_dict = get_rule_type_data_obj_dict(request)

        try:
            zabbix_adapter_obj_list = ZabbixAdapter.objects.filter(rule_type_id__in=rule_type_data_obj_dict.keys())
        except Exception as e:
            # ここでの例外は大外で拾う
            raise

        zabbix_adapter_dto_list = []
        cipher = AESCipher(settings.AES_KEY)
        for zabbix_obj in zabbix_adapter_obj_list:
            zabbix_info = zabbix_obj.__dict__
            if zabbix_obj.password:
                zabbix_info['password'] = cipher.decrypt(zabbix_obj.password)
                zabbix_info['protocol_str'] = protocol_dict[zabbix_obj.protocol]

            

            zabbix_info['editable'] = rule_type_data_obj_dict[zabbix_obj.rule_type_id]['editable']
            zabbix_info['active'] = rule_type_data_obj_dict[zabbix_obj.rule_type_id]['active']

            if zabbix_info['active']:
                zabbix_info['rule_type_name'] = rule_type_data_obj_dict[zabbix_obj.rule_type_id]['rule_type_name']

                zmi_list = []
                # 突合情報取得
                try:
                    zmi_list = list(ZabbixMatchInfo.objects.filter(zabbix_adapter_id=zabbix_obj.zabbix_adapter_id).values('data_object_id', 'zabbix_response_key'))
                except Exception as e:
                    # ここでの例外は大外で拾う
                    raise

                zabbix_info['match_list'] = {str(match_info['data_object_id']): match_info['zabbix_response_key'] for match_info in zmi_list}

            else:
                zabbix_info['rule_type_id'] = -1
                zabbix_info['rule_type_name'] = ""
                zabbix_info['match_list'] = {}

            zabbix_adapter_dto_list.append(zabbix_info)

        return zabbix_adapter_dto_list


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
        ZabbixAdapter.objects.select_for_update().filter(pk=adapter_id)

        logger.logic_log('LOSI00002', 'Record locked.(zabbix_adapter_id=%s)' % adapter_id, request=request)


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
            ZabbixAdapter.objects.select_for_update().filter(pk=delete_id)
            ZabbixAdapter.objects.get(pk=delete_id).delete()
            ZabbixMatchInfo.objects.filter(zabbix_adapter_id=delete_id).delete()
        except ZabbixAdapter.DoesNotExist:
            logger.logic_log('LOSM07006', "zabbix_adapter_id", delete_id, request=request)
            response = {
                'status': 'deleted',
                'msg': get_message('MOSJA26127',lang),
            }
        except Exception as e:
            logger.logic_log('LOSI00005', 'zabbix_adapter_id: %s, trace: %s' % (delete_id, traceback.format_exc()), request=request)
            response = {
                'status': 'failure',
                'msg': get_message('MOSJA26101', lang),
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
            'zabbix_disp_name' : '',
            'protocol' : '',
            'hostname' : '',
            'port' : '',
            'username' : '',
            'password' : '',
            'rule_type_id':'',
            'match_list':'',
        }
        now = datetime.datetime.now(pytz.timezone('UTC'))

        # 成功時データ
        response = {"status": "success",}

        try:
            zabbix_adapter_id = rq['zabbix_adapter_id']
            # 更新または削除の時は更新前にレコードロック
            ZabbixAdapter.objects.select_for_update().get(pk=zabbix_adapter_id)

            #入力チェック
            error_flag = self._validate(rq, error_msg, request, 'edit')

            if error_flag:
                raise UserWarning('validation error.')

            # パスワードを暗号化
            cipher = AESCipher(settings.AES_KEY)
            encrypted_password = cipher.encrypt(rq['password'])
            
            # ZABBIXアダプタの更新
            adapter = ZabbixAdapter.objects.get(pk=zabbix_adapter_id)
            adapter.zabbix_disp_name      = rq['zabbix_disp_name']
            adapter.hostname              = rq['hostname']
            adapter.username              = rq['username']
            adapter.password              = encrypted_password
            adapter.protocol              = rq['protocol']
            adapter.port                  = rq['port']
            adapter.rule_type_id          = rq['rule_type_id']
            adapter.last_update_user      = request.user.user_name
            adapter.last_update_timestamp = now
            adapter.save(force_update=True)
            
            # 変更の有無にかかわらず既存のZABBIX突合情報の削除
            ZabbixMatchInfo.objects.filter(zabbix_adapter_id=zabbix_adapter_id).delete()
            
            # ZABBIX突合情報の保存
            create_match_list = []
            for data_object_id, zabbix_response_key in rq['match_list'].items():
                match = ZabbixMatchInfo(
                    zabbix_adapter_id     = zabbix_adapter_id,
                    data_object_id        = data_object_id,
                    zabbix_response_key   = zabbix_response_key,
                    last_update_user      = request.user.user_name,
                    last_update_timestamp = now,
                )

                create_match_list.append(match)

            ZabbixMatchInfo.objects.bulk_create(create_match_list)

        except ZabbixAdapter.DoesNotExist:
            logger.logic_log('LOSM07006', "zabbix_adapter_id", zabbix_adapter_id, request=request)
            response = {
                'status': 'deleted',
                'msg': get_message('MOSJA26127',lang),
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
            'zabbix_disp_name' : '',
            'protocol' : '',
            'hostname' : '',
            'port' : '',
            'username' : '',
            'password' : '',
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

            # パスワードを暗号化
            cipher = AESCipher(settings.AES_KEY)
            encrypted_password = cipher.encrypt(rq['password'])

            # ZABBIXアダプタの追加
            zabbix_adp = ZabbixAdapter(
                zabbix_disp_name = rq['zabbix_disp_name'],
                hostname         = rq['hostname'],
                username         = rq['username'],
                password         = encrypted_password,
                protocol         = rq['protocol'],
                port             = rq['port'],
                rule_type_id     = rq['rule_type_id'],
                last_update_user = request.user.user_name,
                last_update_timestamp = now,
            )
            zabbix_adp.save(force_insert=True)
            
            # 保存したアダプタのadapter_idを取得
            zabbix_adpid = zabbix_adp.zabbix_adapter_id

            # ZABBIX突合情報の保存
            create_match_list = []
            for data_object_id, zabbix_response_key in rq['match_list'].items():

                match = ZabbixMatchInfo(
                            zabbix_adapter_id     = zabbix_adpid,
                            data_object_id        = data_object_id, 
                            zabbix_response_key   = zabbix_response_key,
                            last_update_user      = request.user.user_name,
                            last_update_timestamp = now,
                        )
                create_match_list.append(match)

            ZabbixMatchInfo.objects.bulk_create(create_match_list)


        except ZabbixAdapter.DoesNotExist:
            logger.logic_log('LOSM07001', 'hostname: %s rule_type_id: %s' % (rq['hostname'], rq['rule_type_id']), request=request)
            response = {
                'status': 'deleted',
                'msg': get_message('MOSJA26127',lang),
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
        emo_flag_zabbix_disp_name = False
        emo_flag_hostname = False
        rule_type_id_error_flag = False
        lang = request.user.get_lang_mode()

        # zabbix_disp_name未入力チェック
        if len(rq['zabbix_disp_name']) == 0:
            error_flag = True
            error_msg['zabbix_disp_name'] += get_message('MOSJA26102', lang) + '\n'
            logger.user_log('LOSM07001', 'zabbix_disp_name', request=request)

        # zabbix_disp_name長さチェック
        if len(rq['zabbix_disp_name']) > 64:
            error_flag = True
            error_msg['zabbix_disp_name'] += get_message('MOSJA26103', lang) + '\n'
            logger.user_log('LOSM07002', 'zabbix_disp_name', 64, rq['zabbix_disp_name'], request=request)

        # zabbix_disp_name絵文字使用チェック
        value_list = emo_chk.is_emotion(rq['zabbix_disp_name'])
        if len(value_list) > 0:
            error_flag = True
            emo_flag_zabbix_disp_name   = True
            error_msg['zabbix_disp_name'] += get_message('MOSJA26104', lang) + '\n'
            logger.user_log('LOSM07008', rq['zabbix_disp_name'], request=request)

        # protocol未入力チェック
        if len(rq['protocol']) == 0:
            error_flag = True
            error_msg['protocol'] += get_message('MOSJA26105', lang) + '\n'
            logger.user_log('LOSM07001', 'protocol', request=request)

        # protocol長さチェック
        if len(rq['protocol']) > 64:
            error_flag = True
            error_msg['protocol'] += get_message('MOSJA26106', lang) + '\n'
            logger.user_log('LOSM07002', 'protocol', 64, rq['protocol'], request=request)

        # hostname未入力チェック
        if len(rq['hostname']) == 0:
            error_flag = True
            error_msg['hostname'] += get_message('MOSJA26107', lang) + '\n'
            logger.user_log('LOSM07001', 'hostname', request=request)

        # hostname長さチェック
        if len(rq['hostname']) > 128:
            error_flag = True
            error_msg['hostname'] += get_message('MOSJA26108', lang) + '\n'
            logger.user_log('LOSM07002', 'hostname', 128, rq['hostname'], request=request)

        # hostname絵文字使用チェック
        value_list = emo_chk.is_emotion(rq['hostname'])
        if len(value_list) > 0:
            error_flag = True
            emo_flag_hostname = True
            error_msg['hostname'] += get_message('MOSJA26109', lang) + '\n'
            logger.user_log('LOSM07008', rq['hostname'], request=request)

        # port未入力チェック
        if len(rq['port']) == 0:
            error_flag = True
            error_msg['port'] += get_message('MOSJA26110', lang) + '\n'
            logger.user_log('LOSM07001', 'port', request=request)

        # port長さチェック
        try:
            tmp_port = int(rq['port'])
            if 0 > tmp_port or tmp_port > 65535:
                error_flag = True
                error_msg['port'] += get_message('MOSJA26111', lang) + '\n'
                logger.user_log('LOSM07003', 'port', rq['port'], request=request)
        except ValueError:
            error_flag = True
            error_msg['port'] += get_message('MOSJA26111', lang) + '\n'
            logger.user_log('LOSM07003', 'port', rq['port'], request=request)

        # username未入力チェック
        if len(rq['username']) == 0:
            error_flag = True
            error_msg['username'] += get_message('MOSJA26112', lang) + '\n'
            logger.user_log('LOSM07001', 'username', request=request)

        # username長さチェック
        if len(rq['username']) > 64:
            error_flag = True
            error_msg['username'] += get_message('MOSJA26113', lang) + '\n'
            logger.user_log('LOSM07002', 'username', 64, rq['username'], request=request)

        # username絵文字使用チェック
        value_list = emo_chk.is_emotion(rq['username'])
        if len(value_list) > 0:
            error_flag = True
            error_msg['username'] += get_message('MOSJA26114', lang) + '\n'
            logger.user_log('LOSM07008', rq['username'], request=request)

        # password未入力チェック
        if len(rq['password']) == 0:
            error_flag = True
            error_msg['password'] += get_message('MOSJA26115', lang) + '\n'
            logger.user_log('LOSM07001', 'password', request=request)

        # password長さチェック
        # 追加の場合
        if rq['zabbix_adapter_id'] == '0':
            if len(rq['password']) > 64:
                error_flag = True
                error_msg['password'] += get_message('MOSJA26116', lang) + '\n'
                logger.user_log('LOSM07002', 'password', 64, rq['password'], request=request)

            # password絵文字使用チェック
            value_list = emo_chk.is_emotion(rq['password'])
            if len(value_list) > 0:
                error_flag = True
                error_msg['password'] += get_message('MOSJA26117', lang) + '\n'
                logger.user_log('LOSM07008', rq['password'], request=request)

        # 変更の場合
        else:
            old_password = ZabbixAdapter.objects.get(zabbix_adapter_id=rq['zabbix_adapter_id']).password
            # パスワード復号
            cipher = AESCipher(settings.AES_KEY)
            old_password_dec = cipher.decrypt(old_password)
            if old_password != rq['password']:
                if len(rq['password']) > 64:
                    error_flag = True
                    error_msg['password'] += get_message('MOSJA26116', lang) + '\n'
                    logger.user_log('LOSM07002', 'password', 64, rq['password'], request=request)

                # password絵文字使用チェック
                value_list = emo_chk.is_emotion(rq['password'])
                if len(value_list) > 0:
                    error_flag = True
                    error_msg['password'] += get_message('MOSJA26117', lang) + '\n'
                    logger.user_log('LOSM07008', rq['password'], request=request)

        # rule_type_id未入力チェック
        if len(rq['rule_type_id']) == 0:
            error_flag = True
            rule_type_id_error_flag = True
            error_msg['rule_type_id'] += get_message('MOSJA26118', lang) + '\n'
            logger.user_log('LOSM07001', 'rule_type_id', request=request)
        
        # rule_type_id存在チェック
        else:
            check_rule_id = RuleType.objects.filter(rule_type_id=rq['rule_type_id'])
            if len(check_rule_id) < 1:
                error_flag = True
                rule_type_id_error_flag = True
                error_msg['rule_type_id'] += get_message('MOSJA26119', lang) + '\n'
                logger.user_log('LOSM07001', 'rule_type_id', request=request)

        if not rule_type_id_error_flag:
            # 突合情報存在チェック

            # 条件名の数を取得
            do_list = DataObject.objects.filter(rule_type_id=rq['rule_type_id']).values_list('data_object_id', flat=True)

            # Zabbix項目チェック
            for data_object_id, zabbix_response_key in rq['match_list'].items():
                id_name = 'zabbix-' + data_object_id
                error_msg.setdefault(id_name,'')

                # 条件名とZabbix項目の数があっているかチェック
                if len(do_list) != len(rq['match_list'].keys()):
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26121', request.user.get_lang_mode()) + '\n'
                    logger.user_log('LOSM07007', len(do_list), len(rq['match_list'].items()), request=request)

                if len(zabbix_response_key) == 0:
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26122', lang) + '\n'
                    logger.user_log('LOSM07001', 'zabbix_response_key', request=request)

                if len(zabbix_response_key) > 32:
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26128', lang) + '\n'
                    logger.user_log('LOSM07002', 'zabbix_response_key', 32, zabbix_response_key, request=request)
                
                # Zabbix項目絵文字使用チェック
                value_list = emo_chk.is_emotion(zabbix_response_key)
                if len(value_list) > 0:
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26123', lang) + '\n'
                    logger.user_log('LOSM07008', rq['zabbix_disp_name'], request=request)

                # 使用可能名チェック
                if zabbix_response_key not in ZABBIX_ITEMS:
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26147', lang) + '\n'
                    logger.user_log('LOSM07009', rq['zabbix_disp_name'], request=request)

        # zabbix_disp_name重複チェック
        if not emo_flag_zabbix_disp_name:
            duplication = ZabbixAdapter.objects.filter(zabbix_disp_name=rq['zabbix_disp_name'])
            if len(duplication) == 1 and int(rq['zabbix_adapter_id']) != duplication[0].zabbix_adapter_id:
                error_flag = True
                error_msg['zabbix_disp_name'] += get_message('MOSJA26124', lang) + '\n'
                logger.user_log('LOSM07004', 'zabbix_disp_name', rq['zabbix_disp_name'], request=request)

        # hostname重複チェック
        if not emo_flag_hostname:
            duplication = ZabbixAdapter.objects.filter(hostname=rq['hostname'], rule_type_id=rq['rule_type_id'])

            # ホスト名重複かつルール種別名が同一の場合
            if len(duplication) == 1 and int(rq['zabbix_adapter_id']) != duplication[0].zabbix_adapter_id:
                error_flag = True
                error_msg['hostname'] += get_message('MOSJA26125', request.user.get_lang_mode()) + '\n'
                logger.user_log('LOSM07004', 'hostname', rq['hostname'], request=request)

        # 疎通確認
        if not error_flag:
            resp_code = -1
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    resp_code = sock.connect_ex((rq['hostname'], int(rq['port']))) # host名名前解決が必要/etc/hostsとか
                    sock.close()
            except:
                pass
            if resp_code != 0:
                error_flag = True
                error_msg['hostname'] += get_message('MOSJA26126', lang) + '\n'
                logger.user_log('LOSM07005', rq['hostname'], rq['port'], request=request)
        

        logger.logic_log('LOSI00002', 'return: %s' % error_flag)
        return error_flag
