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
    MAILアクション用画面表示補助クラス

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

from web_app.models.models import ActionType
from web_app.models.mail_models import MailDriver
from web_app.templatetags.common import get_message

from web_app.serializers.unicode_check import UnicodeCheck

logger = OaseLogger.get_instance() # ロガー初期化

class mailDriverInfo():

    def __init__(self, drv_id, act_id, name, ver, icon_name):

        self.drv_id = drv_id
        self.act_id = act_id
        self.name   = name
        self.ver    = ver
        self.icon_name = icon_name


    def __str__(self):

        return '%s(ver%s)' % (self.name, self.ver)


    def get_driver_name(self):

        return '%s Driver ver%s' % (self.name, self.ver)

    def get_driver_id(self):

        return self.drv_id

    def get_icon_name(self):

        return self.icon_name


    @classmethod
    def get_template_file(cls):
        return 'system/mail/action_mail.html'

    @classmethod
    def get_info_list(cls):

        try:
            mail_driver_obj_list = MailDriver.objects.all()

        except Exception as e:
            # ここでの例外は大外で拾う
            raise

        protocol_dict = cls.get_define()['dict']
        mail_driver_dto_list = []
        cipher = AESCipher(settings.AES_KEY)
        for mail_obj in mail_driver_obj_list:
            mail_info = mail_obj.__dict__
            if mail_obj.password:
                mail_info['password'] = cipher.decrypt(mail_obj.password)
            mail_info['protocol_str'] = protocol_dict[mail_obj.protocol]

            mail_driver_dto_list.append(mail_info)

        return mail_driver_dto_list

    @classmethod
    def get_define(cls):

        protocol_dict = {key_value['v']: key_value['k']  for key_value in defs.SMTP_PROTOCOL.LIST_ALL}

        defines = {
            'list_all': defs.SMTP_PROTOCOL.LIST_ALL,
            'dict': protocol_dict,
        }

        return defines


    def record_lock(self, json_str, request):

        logger.logic_log('LOSI00001', 'None', request=request)

        driver_id = self.get_driver_id()

        # 更新前にレコードロック
        if json_str['json_str']['ope'] in (defs.DABASE_OPECODE.OPE_UPDATE, defs.DABASE_OPECODE.OPE_DELETE):
            drvinfo_modify = int(json_str['json_str']['mail_driver_id'])
            MailDriver.objects.select_for_update().filter(pk=drvinfo_modify)

        logger.logic_log('LOSI00002', 'Record locked.(driver_id=%s)' % driver_id, request=request)


    def modify(self, json_str, request):
        """
        [メソッド概要]
          グループのDB更新処理
        """

        logger.logic_log('LOSI00001', 'None', request=request)

        error_flag = False
        error_msg  = {
            'mail_disp_name' : '',
            'protocol' : '',
            'smtp_server' : '',
            'port' : '',
            'user' : '',
            'password' : '',
        }
        now        = datetime.datetime.now(pytz.timezone('UTC'))
        emo_chk    = UnicodeCheck()
        # 成功時データ
        response = {"status": "success",}

        try:
            rq = json_str['json_str']
            ope = int(rq['ope'])
            #削除以外の場合の入力チェック
            if ope != defs.DABASE_OPECODE.OPE_DELETE:
                error_flag = self._validate(rq, error_msg, request)
            if error_flag:
                raise UserWarning('validation error.')


            # パスワードを暗号化 空なら空文字
            cipher = AESCipher(settings.AES_KEY)

            if ope == defs.DABASE_OPECODE.OPE_UPDATE:
                encrypted_password = cipher.encrypt(rq['password']) if rq['password'] else ''
                
                driver_info_mod = MailDriver.objects.get(mail_driver_id=rq['mail_driver_id'])
                driver_info_mod.mail_disp_name = rq['mail_disp_name']
                driver_info_mod.protocol = rq['protocol']
                driver_info_mod.smtp_server = rq['smtp_server']
                driver_info_mod.port = rq['port']
                driver_info_mod.user = rq['user']
                driver_info_mod.password = encrypted_password
                driver_info_mod.last_update_user = request.user.user_name
                driver_info_mod.last_update_timestamp = now
                driver_info_mod.save(force_update=True)

            elif ope == defs.DABASE_OPECODE.OPE_DELETE:
                MailDriver.objects.filter(pk=rq['mail_driver_id']).delete()

            elif ope == defs.DABASE_OPECODE.OPE_INSERT:
                encrypted_password = cipher.encrypt(rq['password']) if rq['password'] else ''

                driver_info_reg = MailDriver(
                    mail_disp_name = rq['mail_disp_name'],
                    protocol = rq['protocol'],
                    smtp_server = rq['smtp_server'],
                    port = rq['port'],
                    user = rq['user'],
                    password = encrypted_password, 
                    last_update_user = request.user.user_name,
                    last_update_timestamp = now
                ).save(force_insert=True)

        except MailDriver.DoesNotExist:
            logger.logic_log('LOSM07006', "mail_driver_id", mail_driver_id, request=request)

        except Exception as e:
            logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
            response = {
                    'status': 'failure',
                    'error_msg': error_msg,  # エラー詳細(エラーアイコンで出す)
            }

        logger.logic_log('LOSI00002', 'response=%s' % response, request=request)

        return response

    def _validate(self, rq, error_msg, request):
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
        emo_flag = False
        emo_flag_ita_disp_name = False
        emo_flag_hostname = False

        if len(rq['mail_disp_name']) == 0:
            error_flag = True
            error_msg['mail_disp_name'] += get_message('MOSJA27201', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07001', 'mail_disp_name', request=request)

        if len(rq['mail_disp_name']) > 64:
            error_flag = True
            error_msg['mail_disp_name'] += get_message('MOSJA27202', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07002', 'mail_disp_name', 64, rq['mail_disp_name'], request=request)

        # 絵文字チェック
        value_list = emo_chk.is_emotion(rq['mail_disp_name'])
        if len(value_list) > 0:
            error_flag = True
            emo_flag   = True
            error_msg['mail_disp_name'] += get_message('MOSJA27216', request.user.get_lang_mode(), showMsgId=False) + '\n'

        if len(rq['protocol']) == 0:
            error_flag = True
            error_msg['protocol'] += get_message('MOSJA27212', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07001', 'protocol', request=request)

        if len(rq['protocol']) > 64:
            error_flag = True
            error_msg['protocol'] += get_message('MOSJA27213', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07002', 'protocol', 64, rq['protocol'], request=request)

        if len(rq['smtp_server']) == 0:
            error_flag = True
            error_msg['smtp_server'] += get_message('MOSJA27203', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07001', 'smtp_server', request=request)

        if len(rq['smtp_server']) > 128:
            error_flag = True
            error_msg['smtp_server'] += get_message('MOSJA27204', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07002', 'smtp_server', 64, rq['smtp_server'], request=request)

        # 絵文字チェック
        value_list = emo_chk.is_emotion(rq['smtp_server'])
        if len(value_list) > 0:
            error_flag = True
            error_msg['smtp_server'] += get_message('MOSJA27217', request.user.get_lang_mode(), showMsgId=False) + '\n'

        if len(rq['port']) == 0:
            error_flag = True
            error_msg['port'] += get_message('MOSJA27205', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07001', 'port', request=request)

        try:
            tmp_port = int(rq['port'])
            if 0 > tmp_port or tmp_port > 65535:
                error_flag = True
                error_msg['port'] += get_message('MOSJA27206', request.user.get_lang_mode()) + '\n'
                logger.user_log('LOSM07003', 'port', rq['port'], request=request)
        except ValueError:
            error_flag = True
            error_msg['port'] += get_message('MOSJA27206', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07003', 'port', rq['port'], request=request)

        if len(rq['user']) > 64:
            error_flag = True
            error_msg['user'] += get_message('MOSJA27207', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07002', 'user', 64, rq['user'], request=request)

        # 絵文字チェック
        value_list = emo_chk.is_emotion(rq['user'])
        if len(value_list) > 0:
            error_flag = True
            error_msg['user'] += get_message('MOSJA27218', request.user.get_lang_mode(), showMsgId=False) + '\n'

        if len(rq['password']) > 64:
            error_flag = True
            error_msg['password'] += get_message('MOSJA27208', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07002', 'password', 64, rq['password'], request=request)

        # 絵文字チェック
        value_list = emo_chk.is_emotion(rq['password'])
        if len(value_list) > 0:
            error_flag = True
            error_msg['password'] += get_message('MOSJA27219', request.user.get_lang_mode(), showMsgId=False) + '\n'

        if not emo_flag:
            duplication = MailDriver.objects.filter(mail_disp_name=rq['mail_disp_name'])
            if len(duplication) == 1 and int(rq['mail_driver_id']) != duplication[0].mail_driver_id:
                error_flag = True
                error_msg['mail_disp_name'] += get_message('MOSJA27209', request.user.get_lang_mode()) + '\n'
                logger.user_log('LOSM07004', 'mail_disp_name', rq['mail_disp_name'], request=request)


        if error_flag == False:

            # 疎通確認
            resp_code = -1
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    resp_code = sock.connect_ex((rq['smtp_server'], int(rq['port']))) # host名名前解決が必要/etc/hostsとか
                    sock.close()
            except Exception as e:
                pass
            if resp_code != 0:
                error_flag = True
                #todo 仮でこのエラーは名前に入れている
                error_msg['mail_disp_name'] += get_message('MOSJA27215', request.user.get_lang_mode()) + '\n'
                logger.user_log('LOSM07005', rq['smtp_server'], rq['port'], request=request)

        return error_flag
