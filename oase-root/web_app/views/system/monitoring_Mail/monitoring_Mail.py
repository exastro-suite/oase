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
    Mailアダプタ用画面表示補助クラス
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

from web_app.models.Mail_monitoring_models import MailAdapter, MailMatchInfo, MailMonitoringHistory
from web_app.models.models import RuleType, DataObject
from web_app.templatetags.common import get_message
from web_app.views.system.monitoring import get_rule_type_data_obj_dict

from web_app.serializers.unicode_check import UnicodeCheck

logger = OaseLogger.get_instance() # ロガー初期化


#-------------------
# Mail項目
#-------------------
MAIL_ITEMS = [
    'message_id',
    'envelope_from',
    'envelope_to',
    'header_from',
    'header_to',
    'mailaddr_from',
    'mailaddr_to',
    'date',
    'subject',
    'body',
]

class MailAdapterInfo():

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

        return 'system/Mail/monitoring_Mail.html'

    def get_mail_items(self):

        mail_item_list = ','.join(MAIL_ITEMS)

        return mail_item_list


    def get_info_list(self, request):

        protocol_dict = self.get_define()['dict']
        rule_type_data_obj_dict = get_rule_type_data_obj_dict(request)

        try:
            mail_adapter_obj_list = MailAdapter.objects.filter(rule_type_id__in=rule_type_data_obj_dict.keys())
        except Exception as e:
            # ここでの例外は大外で拾う
            raise

        mail_adapter_dto_list = []
        cipher = AESCipher(settings.AES_KEY)

        for mail_obj in mail_adapter_obj_list:
            mail_info = mail_obj.__dict__

            if mail_obj.password:
                mail_info['password'] = cipher.decrypt(mail_obj.password)
            mail_info['protocol_str'] = protocol_dict[mail_obj.encryption_protocol]

            mail_info['editable'] = rule_type_data_obj_dict[mail_obj.rule_type_id]['editable']
            mail_info['active'] = rule_type_data_obj_dict[mail_obj.rule_type_id]['active']

            if mail_info['active']:
                mail_info['rule_type_name'] = rule_type_data_obj_dict[mail_obj.rule_type_id]['rule_type_name']

                zmi_list = []
                # 突合情報取得
                try:
                    zmi_list = list(MailMatchInfo.objects.filter(mail_adapter_id=mail_obj.mail_adapter_id).values('data_object_id', 'mail_response_key'))
                except Exception as e:
                    # ここでの例外は大外で拾う
                    raise

                mail_info['match_list'] = {str(match_info['data_object_id']): match_info['mail_response_key'] for match_info in zmi_list}

            else:
                mail_info['rule_type_id'] = -1
                mail_info['rule_type_name'] = ""
                mail_info['match_list'] = {}

            mail_adapter_dto_list.append(mail_info)

        return mail_adapter_dto_list


    def get_define(self):

        protocol_dict = {key_value['v']: key_value['k']  for key_value in defs.IMAP_PROTOCOL.LIST_ALL}

        defines = {
            'list_all': defs.IMAP_PROTOCOL.LIST_ALL,
            'dict': protocol_dict,
        }

        return defines


    def record_lock(self, adapter_id, request):

        logger.logic_log('LOSI00001', 'None', request=request)

        # 更新または削除の時は更新前にレコードロック
        MailAdapter.objects.select_for_update().filter(pk=adapter_id)

        logger.logic_log('LOSI00002', 'Record locked.(mail_adapter_id=%s)' % adapter_id, request=request)


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
            MailAdapter.objects.select_for_update().filter(pk=delete_id)
            MailAdapter.objects.get(pk=delete_id).delete()
            MailMatchInfo.objects.filter(mail_adapter_id=delete_id).delete()
        except MailAdapter.DoesNotExist:
            logger.logic_log('LOSM40001', "mail_adapter_id", delete_id, request=request)
            response = {
                'status': 'deleted',
                'msg': get_message('MOSJA26517',lang),
            }
        except Exception as e:
            logger.logic_log('LOSI00005', 'mail_adapter_id: %s, trace: %s' % (delete_id, traceback.format_exc()), request=request)
            response = {
                'status': 'failure',
                'msg': get_message('MOSJA26546', lang),
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
            'mail_disp_name' : '',
            'protocol'       : '',
            'imap_server'    : '',
            'port'           : '',
            'username'       : '',
            'password'       : '',
            'rule_type_id'   : '',
        }
        now = datetime.datetime.now(pytz.timezone('UTC'))

        # 成功時データ
        response = {"status": "success",}

        try:
            mail_adapter_id = rq['mail_adapter_id']
            # 更新または削除の時は更新前にレコードロック
            MailAdapter.objects.select_for_update().get(pk=mail_adapter_id)

            #入力チェック
            error_flag = self._validate(rq, error_msg, request, 'edit')

            if error_flag:
                raise UserWarning('validation error.')

            cipher = AESCipher(settings.AES_KEY)
            encrypted_password = cipher.encrypt(rq['password']) if rq['password'] else ''

            # Datadogアダプタの更新
            adapter = MailAdapter.objects.get(pk=mail_adapter_id)
            adapter.mail_disp_name        = rq['mail_disp_name']
            adapter.encryption_protocol   = rq['protocol']
            adapter.imap_server           = rq['imap_server']
            adapter.port                  = rq['port']
            adapter.user                  = rq['username']
            adapter.password              = encrypted_password
            adapter.rule_type_id          = rq['rule_type_id']
            adapter.last_update_user      = request.user.user_name
            adapter.last_update_timestamp = now
            adapter.save(force_update=True)

            # 変更の有無にかかわらず既存のMail突合情報の削除
            MailMatchInfo.objects.filter(mail_adapter_id=mail_adapter_id).delete()

            # Mail突合情報の保存
            create_match_list = []
            for data_object_id, mail_response_key in rq['match_list'].items():
                match = MailMatchInfo(
                    mail_adapter_id       = mail_adapter_id,
                    data_object_id        = data_object_id,
                    mail_response_key     = mail_response_key,
                    last_update_user      = request.user.user_name,
                    last_update_timestamp = now,
                )

                create_match_list.append(match)

            MailMatchInfo.objects.bulk_create(create_match_list)

        except MailAdapter.DoesNotExist:
            logger.logic_log('LOSM40001', "datadog_adapter_id", datadog_adapter_id, request=request)
            response = {
                'status': 'deleted',
                'msg': get_message('MOSJA26517',lang),
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
            'mail_disp_name' : '',
            'protocol'       : '',
            'imap_server'    : '',
            'port'           : '',
            'username'       : '',
            'password'       : '',
            'rule_type_id'   : '',
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

            # パスワードを暗号化、空なら空文字
            cipher = AESCipher(settings.AES_KEY)
            encrypted_password = cipher.encrypt(rq['password']) if rq['password'] else ''

            # Mailアダプタの追加
            mail_adp = MailAdapter(
                 mail_disp_name        = rq['mail_disp_name'],
                 encryption_protocol   = rq['protocol'],
                 imap_server           = rq['imap_server'],
                 port                  = rq['port'],
                 user                  = rq['username'],
                 password              = encrypted_password, 
                 rule_type_id          = rq['rule_type_id'],
                 last_update_user      = request.user.user_name,
                 last_update_timestamp = now
            )
            mail_adp.save(force_insert=True)

            # 保存したアダプタのadapter_idを取得
            mail_adpid = mail_adp.mail_adapter_id

            # メール突合情報の保存
            create_match_list = []
            for data_object_id, mail_response_key in rq['match_list'].items():

                match = MailMatchInfo(
                            mail_adapter_id         = mail_adpid,
                            data_object_id          = data_object_id, 
                            mail_response_key       = mail_response_key,
                            last_update_user        = request.user.user_name,
                            last_update_timestamp   = now,
                        )
                create_match_list.append(match)

            MailMatchInfo.objects.bulk_create(create_match_list)


        except MailAdapter.DoesNotExist:
            logger.logic_log('LOSM40002', 'uri: %s rule_type_id: %s' % (rq['uri'], rq['rule_type_id']), request=request)
            response = {
                'status': 'deleted',
                # "データは既に削除されています。"
                'msg': get_message('MOSJA26517',lang),
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
        emo_flag_mail_disp_name = False
        emo_flag_imap_server = False
        rule_type_id_error_flag = False
        lang = request.user.get_lang_mode()

        # mail_disp_name未入力チェック
        if len(rq['mail_disp_name']) == 0:
            error_flag = True          # "必須項目(名前)が入力されていません。入力してください。"
            error_msg['mail_disp_name'] += get_message('MOSJA26518', lang) + '\n'
            logger.user_log('LOSM40002', 'mail_disp_name', request=request)

        # mail_disp_name長さチェック
        if len(rq['mail_disp_name']) > 64:
            error_flag = True
            error_msg['mail_disp_name'] += get_message('MOSJA26519', lang) + '\n'
            logger.user_log('LOSM40003', 'mail_disp_name', 64, rq['mail_disp_name'], request=request)

        # mail_disp_name絵文字使用チェック
        value_list = emo_chk.is_emotion(rq['mail_disp_name'])
        if len(value_list) > 0:
            error_flag = True
            emo_flag_mail_disp_name   = True
            error_msg['mail_disp_name'] += get_message('MOSJA26520', lang) + '\n'
            logger.user_log('LOSM40005', rq['mail_disp_name'], request=request)

        # protocol未入力チェック
        if len(rq['protocol']) == 0:
            error_flag = True
            error_msg['protocol'] += get_message('MOSJA26524', lang) + '\n'
            logger.user_log('LOSM40002', 'protocol', request=request)

        # imap_server未入力チェック
        if len(rq['imap_server']) == 0:
            error_flag = True
            error_msg['imap_server'] += get_message('MOSJA26521', lang) + '\n'
            logger.user_log('LOSM40002', 'imap_server', request=request)

        # imap_server長さチェック
        if len(rq['imap_server']) > 64:
            error_flag = True
            error_msg['imap_server'] += get_message('MOSJA26522', lang) + '\n'
            logger.user_log('LOSM40003', 'imap_server', 64, rq['api_key'], request=request)

        # imap_server絵文字使用チェック
        value_list = emo_chk.is_emotion(rq['imap_server'])
        if len(value_list) > 0:
            error_flag = True
            emo_flag_imap_server = True
            error_msg['imap_server'] += get_message('MOSJA26523', lang) + '\n'
            logger.user_log('LOSM40005', rq['imap_server'], request=request)

        # port未入力チェック
        if len(rq['port']) == 0:
            error_flag = True
            error_msg['port'] += get_message('MOSJA26525', lang) + '\n'
            logger.user_log('LOSM40002', 'port', request=request)

        # port長さチェック
        try:
            tmp_port = int(rq['port'])
            if 0 > tmp_port or tmp_port > 65535:
                error_flag = True
                error_msg['port'] += get_message('MOSJA26526', lang) + '\n'
                logger.user_log('LOSM40008', 'port', rq['port'], request=request)
        except ValueError:
            error_flag = True
            error_msg['port'] += get_message('MOSJA26526', lang) + '\n'
            logger.user_log('LOSM40008', 'port', rq['port'], request=request)

        # username未入力チェック
        if len(rq['username']) == 0:
            error_flag = True
            error_msg['username'] += get_message('MOSJA26527', lang) + '\n'
            logger.user_log('LOSM40002', 'username', request=request)

        # username長さチェック
        if len(rq['username']) > 64:
            error_flag = True
            error_msg['username'] += get_message('MOSJA26528', lang) + '\n'
            logger.user_log('LOSM40003', 'username', 64, rq['username'], request=request)

        # username絵文字使用チェック
        value_list = emo_chk.is_emotion(rq['username'])
        if len(value_list) > 0:
            error_flag = True
            error_msg['username'] += get_message('MOSJA26529', lang) + '\n'
            logger.user_log('LOSM40005', rq['username'], request=request)

        # password未入力チェック
        if len(rq['password']) == 0:
            error_flag = True
            error_msg['password'] += get_message('MOSJA26530', lang) + '\n'
            logger.user_log('LOSM40002', 'password', request=request)

        # password長さチェック
        # 追加の場合
        if rq['mail_adapter_id'] == '0':
            if len(rq['password']) > 64:
                error_flag = True
                error_msg['password'] += get_message('MOSJA26531', lang) + '\n'
                logger.user_log('LOSM40003', 'password', 64, rq['password'], request=request)

            # password絵文字使用チェック
            value_list = emo_chk.is_emotion(rq['password'])
            if len(value_list) > 0:
                error_flag = True
                error_msg['password'] += get_message('MOSJA26532', lang) + '\n'
                logger.user_log('LOSM40005', rq['password'], request=request)

        # 変更の場合
        else:
            old_password = MailAdapter.objects.get(mail_adapter_id=rq['mail_adapter_id']).password
            # パスワード復号
            cipher = AESCipher(settings.AES_KEY)
            old_password_dec = cipher.decrypt(old_password)
            if old_password != rq['password']:
                if len(rq['password']) > 64:
                    error_flag = True
                    error_msg['password'] += get_message('MOSJA26531', lang) + '\n'
                    logger.user_log('LOSM40003', 'password', 64, rq['password'], request=request)

                # password絵文字使用チェック
                value_list = emo_chk.is_emotion(rq['password'])
                if len(value_list) > 0:
                    error_flag = True
                    error_msg['password'] += get_message('MOSJA26532', lang) + '\n'
                    logger.user_log('LOSM40005', rq['password'], request=request)

        # rule_type_id未入力チェック
        if len(rq['rule_type_id']) == 0:
            error_flag = True
            rule_type_id_error_flag = True
            error_msg['rule_type_id'] += get_message('MOSJA26533', lang) + '\n'
            logger.user_log('LOSM40002', 'rule_type_id', request=request)

        # rule_type_id存在チェック
        else:
            check_rule_id = RuleType.objects.filter(rule_type_id=rq['rule_type_id'])
            if len(check_rule_id) < 1:
                error_flag = True
                rule_type_id_error_flag = True
                error_msg['rule_type_id'] += get_message('MOSJA26534', lang) + '\n'
                logger.user_log('LOSM40002', 'rule_type_id', request=request)

        if not rule_type_id_error_flag:
            # 突合情報存在チェック

            # 条件名の数を取得
            do_list = DataObject.objects.filter(rule_type_id=rq['rule_type_id']).values_list('data_object_id', flat=True)

            # メール項目チェック
            for data_object_id, mail_response_key in rq['match_list'].items():
                id_name = 'mail-' + data_object_id
                error_msg.setdefault(id_name,'')

                # 条件名とメール項目の数があっているかチェック
                if len(do_list) != len(rq['match_list'].keys()):
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26535', request.user.get_lang_mode()) + '\n'
                    logger.user_log('LOSM40007', len(do_list), len(rq['match_list'].items()), request=request)

                if len(mail_response_key) == 0:
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26536', lang) + '\n'
                    logger.user_log('LOSM40002', 'mail_response_key', request=request)

                if len(mail_response_key) > 32:
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26537', lang) + '\n'
                    logger.user_log('LOSM40003', 'mail_response_key', 32, mail_response_key, request=request)

                # メール項目絵文字使用チェック
                value_list = emo_chk.is_emotion(mail_response_key)
                if len(value_list) > 0:
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26538', lang) + '\n'
                    logger.user_log('LOSM40005', rq['mail_disp_name'], request=request)

                # 使用可能名チェック
                if mail_response_key not in MAIL_ITEMS:
                    error_flag = True
                    error_msg[id_name] += get_message('MOSJA26539', lang) + '\n'
                    logger.user_log('LOSM40006', rq['mail_disp_name'], request=request)

        # mail_disp_name重複チェック
        if not emo_flag_mail_disp_name:
            duplication = MailAdapter.objects.filter(mail_disp_name=rq['mail_disp_name'])
            if len(duplication) == 1 and int(rq['mail_adapter_id']) != duplication[0].mail_adapter_id:
                error_flag = True
                error_msg['mail_disp_name'] += get_message('MOSJA26540', lang) + '\n'
                logger.user_log('LOSM40004', 'mail_disp_name', rq['mail_disp_name'], request=request)

        # hostname重複チェック
        if not emo_flag_imap_server:
            duplication = MailAdapter.objects.filter(imap_server=rq['imap_server'], rule_type_id=rq['rule_type_id'])

            # ホスト名重複かつルール種別名が同一の場合
            if len(duplication) == 1 and int(rq['mail_adapter_id']) != duplication[0].mail_adapter_id:
                error_flag = True
                error_msg['imap_server'] += get_message('MOSJA26541', request.user.get_lang_mode()) + '\n'
                logger.user_log('LOSM40004', 'imap_server', rq['imap_server'], request=request)

        # 疎通確認
        if not error_flag:
            resp_code = -1
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    resp_code = sock.connect_ex((rq['imap_server'], int(rq['port'])))
                    sock.close()
            except:
                pass
            if resp_code != 0:
                error_flag = True
                error_msg['imap_server'] += get_message('MOSJA26542', lang) + '\n'
                logger.user_log('LOSM40009', rq['imap_server'], rq['port'], request=request)

        logger.logic_log('LOSI00002', 'return: %s' % error_flag)
        return error_flag
