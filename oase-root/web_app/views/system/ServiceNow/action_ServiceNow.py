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
    ServiceNowアクション用画面表示補助クラス

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
from web_app.models.ServiceNow_models import ServiceNowDriver
from web_app.templatetags.common import get_message
from web_app.serializers.unicode_check import UnicodeCheck

logger = OaseLogger.get_instance() # ロガー初期化

class ServiceNowDriverInfo():

    def __init__(self, drv_id, act_id, name, ver, icon_name):

        self.drv_id    = drv_id
        self.act_id    = act_id
        self.name      = name
        self.ver       = ver
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
        return 'system/ServiceNow/action_ServiceNow.html'


    @classmethod
    def get_info_list(cls, user_groups):

        try:
            servicenow_driver_obj_list = ServiceNowDriver.objects.all()

        except Exception as e:
            raise

        protocol_dict = cls.get_define()['dict']
        servicenow_driver_dto_list = []
        cipher = AESCipher(settings.AES_KEY)
        for servicenow_obj in servicenow_driver_obj_list:
            servicenow_info = servicenow_obj.__dict__
            if servicenow_obj.password:
                servicenow_info['password'] = cipher.decrypt(servicenow_obj.password)
            servicenow_info['protocol'] = protocol_dict[servicenow_obj.protocol]

            servicenow_driver_dto_list.append(servicenow_info)

        return servicenow_driver_dto_list


    @classmethod
    def get_group_list(cls):
        """
        [概要]
        グループ一覧を取得する
        ServiceNowでは不要のため空で返却する。
        """

        return []


    @classmethod
    def get_define(cls):

        protocol_dict = {key_value['v']: key_value['k']  for key_value in defs.HTTP_PROTOCOL.LIST_ALL}

        defines = {
            'list_all': defs.HTTP_PROTOCOL.LIST_ALL,
            'dict': protocol_dict,
        }

        return defines


    def record_lock(self, json_str, request):

        logger.logic_log('LOSI00001', 'None', request=request)

        driver_id = self.get_driver_id()

        # 更新前にレコードロック
        if json_str['json_str']['ope'] in (defs.DABASE_OPECODE.OPE_UPDATE, defs.DABASE_OPECODE.OPE_DELETE):
            drvinfo_modify = int(json_str['json_str']['servicenow_driver_id'])
            ServiceNowDriver.objects.select_for_update().filter(pk=drvinfo_modify)

        logger.logic_log('LOSI00002', 'Record locked.(driver_id=%s)' % driver_id, request=request)


    def modify(self, json_str, request):
        """
        [メソッド概要]
          アクション設定のDB更新処理
        """

        logger.logic_log('LOSI00001', 'None', request=request)

        error_flag = False
        error_msg  = {
            'servicenow_disp_name' : '',
            'protocol' : '',
            'hostname' : '',
            'port' : '',
            'username' : '',
            'password' : '',
            'proxy' : '',
        }
        now      = datetime.datetime.now(pytz.timezone('UTC'))
        emo_chk  = UnicodeCheck()
        response = {"status": "success",}

        try:
            rq = json_str['json_str']
            ope = int(rq['ope'])
            # 削除以外の場合の入力チェック
            if ope != defs.DABASE_OPECODE.OPE_DELETE:
                error_flag = self._validate(rq, error_msg, request)
            if error_flag:
                raise UserWarning('validation error.')

            # パスワードを暗号化
            cipher = AESCipher(settings.AES_KEY)

            if ope == defs.DABASE_OPECODE.OPE_UPDATE:
                encrypted_password = cipher.encrypt(rq['password'])

                driver_info_mod = ServiceNowDriver.objects.get(servicenow_driver_id=rq['servicenow_driver_id'])
                driver_info_mod.servicenow_disp_name = rq['servicenow_disp_name']
                driver_info_mod.protocol = rq['protocol']
                driver_info_mod.hostname = rq['hostname']
                driver_info_mod.port = rq['port']
                driver_info_mod.username = rq['username']
                driver_info_mod.password = encrypted_password
                driver_info_mod.proxy = rq['proxy']
                driver_info_mod.last_update_user = request.user.user_name
                driver_info_mod.last_update_timestamp = now
                driver_info_mod.save(force_update=True)

            elif ope == defs.DABASE_OPECODE.OPE_DELETE:
                ServiceNowDriver.objects.filter(pk=rq['servicenow_driver_id']).delete()

            elif ope == defs.DABASE_OPECODE.OPE_INSERT:
                encrypted_password = cipher.encrypt(rq['password'])

                driver_info_reg = ServiceNowDriver(
                    servicenow_disp_name = rq['servicenow_disp_name'],
                    protocol = rq['protocol'],
                    hostname = rq['hostname'],
                    port = rq['port'],
                    username = rq['username'],
                    password = encrypted_password,
                    count = 0,
                    proxy = rq['proxy'],
                    last_update_user = request.user.user_name,
                    last_update_timestamp = now
                ).save(force_insert=True)

        except ServiceNowDriver.DoesNotExist:
            logger.logic_log('LOSM07006', "servicenow_driver_id", servicenow_driver_id, request=request)

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
        emo_flag_servicenow_disp_name = False
        emo_flag_hostname = False

        if len(rq['servicenow_disp_name']) == 0:
            error_flag = True
            error_msg['servicenow_disp_name'] += get_message('MOSJA27400', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07001', 'servicenow_disp_name', request=request)

        if len(rq['servicenow_disp_name']) > 64:
            error_flag = True
            error_msg['servicenow_disp_name'] += get_message('MOSJA27401', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07002', 'servicenow_disp_name', 64, rq['servicenow_disp_name'], request=request)

        # 絵文字チェック
        value_list = emo_chk.is_emotion(rq['servicenow_disp_name'])
        if len(value_list) > 0:
            error_flag = True
            emo_flag   = True
            error_msg['servicenow_disp_name'] += get_message(
                'MOSJA27402', request.user.get_lang_mode()) + '\n'

        if len(rq['protocol']) == 0:
            error_flag = True
            error_msg['protocol'] += get_message('MOSJA27403', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07001', 'protocol', request=request)

        if len(rq['protocol']) > 8:
            error_flag = True
            error_msg['protocol'] += get_message('MOSJA27404', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07002', 'protocol', 64, rq['protocol'], request=request)

        if len(rq['hostname']) == 0:
            error_flag = True
            error_msg['hostname'] += get_message('MOSJA27405', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07001', 'hostname', request=request)

        if len(rq['hostname']) > 128:
            error_flag = True
            error_msg['hostname'] += get_message('MOSJA27406', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07002', 'hostname', 128, rq['hostname'], request=request)

        # 絵文字チェック
        value_list = emo_chk.is_emotion(rq['hostname'])
        if len(value_list) > 0:
            emo_flag_hostname = True
            error_msg['hostname'] += get_message('MOSJA27407', request.user.get_lang_mode()) + '\n'

        if len(rq['port']) == 0:
            error_flag = True
            error_msg['port'] += get_message('MOSJA27408', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07001', 'port', request=request)

        try:
            tmp_port = int(rq['port'])
            if 0 > tmp_port or tmp_port > 65535:
                error_flag = True
                error_msg['port'] += get_message('MOSJA27409', request.user.get_lang_mode()) + '\n'
                logger.user_log('LOSM07003', 'port', rq['port'], request=request)
        except ValueError:
            error_flag = True
            error_msg['port'] += get_message('MOSJA27409', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07003', 'port', rq['port'], request=request)

        if len(rq['username']) == 0:
            error_flag = True
            error_msg['username'] += get_message('MOSJA27410', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07001', 'username', request=request)

        if len(rq['username']) > 64:
            error_flag = True
            error_msg['username'] += get_message('MOSJA27411', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07002', 'username', 64, rq['username'], request=request)

        # 絵文字チェック
        value_list = emo_chk.is_emotion(rq['username'])
        if len(value_list) > 0:
            error_flag = True
            error_msg['username'] += get_message('MOSJA27412', request.user.get_lang_mode()) + '\n'

        if len(rq['password']) == 0:
            error_flag = True
            error_msg['password'] += get_message('MOSJA27413', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07001', 'password', request=request)

        if len(rq['password']) > 64:
            error_flag = True
            error_msg['password'] += get_message('MOSJA27414', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07002', 'password', 64, rq['password'], request=request)

        # 絵文字チェック
        value_list = emo_chk.is_emotion(rq['password'])
        if len(value_list) > 0:
            error_flag = True
            error_msg['password'] += get_message('MOSJA27415', request.user.get_lang_mode()) + '\n'

        if len(rq['proxy']) > 256:
            error_flag = True
            error_msg['proxy'] += get_message('MOSJA27421', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07002', 'proxy', 256, rq['proxy'], request=request)

        # 絵文字チェック
        value_list = emo_chk.is_emotion(rq['proxy'])
        if len(value_list) > 0:
            error_flag = True
            error_msg['proxy'] += get_message('MOSJA27422', request.user.get_lang_mode()) + '\n'

        if not emo_flag:
            duplication = ServiceNowDriver.objects.filter(servicenow_disp_name=rq['servicenow_disp_name'])
            if len(duplication) == 1 and int(rq['servicenow_driver_id']) != duplication[0].servicenow_driver_id:
                error_flag = True
                error_msg['servicenow_disp_name'] += get_message('MOSJA27416', request.user.get_lang_mode()) + '\n'
                logger.user_log('LOSM07004', 'servicenow_disp_name', rq['servicenow_disp_name'], request=request)

        if not emo_flag_hostname:
            duplication = ServiceNowDriver.objects.filter(hostname=rq['hostname'])
            if len(duplication) == 1 and int(rq['servicenow_driver_id']) != duplication[0].servicenow_driver_id:
                error_flag = True
                error_msg['hostname'] += get_message('MOSJA27418', request.user.get_lang_mode()) + '\n'
                logger.user_log('LOSM07004', 'hostname', rq['hostname'], request=request)

        #if error_flag == False:

            # 疎通確認
        #    resp_code = -1
        #    try:
        #        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        #            resp_code = sock.connect_ex((rq['hostname'], int(rq['port'])))
        #            sock.close()
        #    except Exception as e:
        #        pass
        #    if resp_code != 0:
        #        error_flag = True
                # todo 仮でこのエラーは名前に入れている
        #        error_msg['servicenow_disp_name'] += get_message('MOSJA27417', request.user.get_lang_mode()) + '\n'
        #        logger.user_log('LOSM07005', rq['hostname'], rq['port'], request=request)

        return error_flag

