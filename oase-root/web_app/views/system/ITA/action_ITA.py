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
    ITAアクション用画面表示補助クラス

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

from web_app.models.models import ActionType, Group
from web_app.models.ITA_models import ItaDriver, ItaPermission
from web_app.templatetags.common import get_message

from web_app.serializers.unicode_check import UnicodeCheck

logger = OaseLogger.get_instance() # ロガー初期化

class ITADriverInfo():

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
        return 'system/ITA/action_ITA.html'

    @classmethod
    def get_info_list(cls, user_groups):

        try:
            ita_driver_obj_list = ItaDriver.objects.all()

        except Exception as e:
            # ここでの例外は大外で拾う
            raise

        protocol_dict = cls.get_define()['dict']
        permission_list = cls.get_permission(ita_driver_obj_list, user_groups)
        editable_ids = cls.get_driver_ids(ita_driver_obj_list, user_groups, [defs.ALLOWED_MENTENANCE,])
        ref_ids = cls.get_driver_ids(ita_driver_obj_list, user_groups, [defs.ALLOWED_MENTENANCE, defs.VIEW_ONLY])

        ita_driver_dto_list = []
        cipher = AESCipher(settings.AES_KEY)
        for ita_obj in ita_driver_obj_list:
            if ita_obj.ita_driver_id not in ref_ids:
                continue

            ita_info = ita_obj.__dict__
            ita_info['password'] = cipher.decrypt(ita_obj.password)
            ita_info['protocol_str'] = protocol_dict[ita_obj.protocol]
            ita_info['editable'] = True if ita_obj.ita_driver_id in editable_ids else False
            ita_info['permission'] = permission_list[ita_obj.ita_driver_id] if ita_obj.ita_driver_id in permission_list else []
            ita_driver_dto_list.append(ita_info)

        return ita_driver_dto_list

    @classmethod
    def get_group_list(cls, user_groups):
        """
        [概要]
        グループ一覧を取得する(システム管理グループを除く)
        """

        grp_list = Group.objects.filter(group_id__in=user_groups).values('group_id', 'group_name').order_by('group_id')
        return grp_list

    @classmethod
    def get_driver_ids(cls, ita_drv_list, user_groups, perms):
        """
        [概要]
        ユーザーグループを用いて更新可能権限を持つドライバーIDを取得する
        """

        drv_ids = []

        drv_ids = list(
            ItaPermission.objects.filter(
                group_id__in=user_groups,
                permission_type_id__in=perms
            ).values_list(
                'ita_driver_id', flat=True
            ).distinct()
        )

        return drv_ids

    @classmethod
    def get_permission(cls, ita_drv_list, user_groups):
        """
        [概要]
        権限情報を作成する
        """

        perm_info = {}

        # グループ情報を取得
        grp_info = {}
        grp_list = cls.get_group_list(user_groups)
        for grp in grp_list:
            grp_info[grp['group_id']] = grp['group_name']

        for drv in ita_drv_list:
            perm_info[drv.ita_driver_id] = []
            for grp in grp_list:
                perm_info[drv.ita_driver_id].append(
                    {
                        'group_id' : grp['group_id'],
                        'group_name' : grp_info[grp['group_id']],
                        'permission_type_id' : defs.NO_AUTHORIZATION,
                    }
                )

        # 権限情報を取得
        drv_grp_info = {}
        ItaPerm_list = ItaPermission.objects.filter().values('ita_driver_id', 'group_id', 'permission_type_id')
        for ita in ItaPerm_list:
            drv_id = ita['ita_driver_id']
            grp_id = ita['group_id']
            perm = ita['permission_type_id']

            # 不明なドライバー、不明なグループは無視
            if drv_id not in perm_info or grp_id not in grp_info:
                continue

            # 登録中の権限を保持
            drv_grp_info[(drv_id, grp_id)] = perm

        # 登録されている権限をセット
        for drv_id, v_list in perm_info.items():
            for v in v_list:
                grp_id = v['group_id']
                if (drv_id, grp_id) in drv_grp_info:
                    v['permission_type_id'] = drv_grp_info[(drv_id, grp_id)]

        return perm_info



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
            drvinfo_modify = int(json_str['json_str']['ita_driver_id'])
            ItaDriver.objects.select_for_update().filter(pk=drvinfo_modify)

        logger.logic_log('LOSI00002', 'Record locked.(driver_id=%s)' % driver_id, request=request)


    def modify(self, json_str, request):
        """
        [メソッド概要]
          グループのDB更新処理
        """

        logger.logic_log('LOSI00001', 'None', request=request)

        error_flag = False
        error_msg  = {
            'ita_disp_name' : '',
            'version' : '',
            'protocol' : '',
            'hostname' : '',
            'port' : '',
            'username' : '',
            'password' : '',
            'permission' : '',
        }
        now = datetime.datetime.now(pytz.timezone('UTC'))
        # 成功時データ
        response = {"status": "success",}

        try:
            rq = json_str['json_str']

            ope = int(rq['ope'])
            if ope != defs.DABASE_OPECODE.OPE_INSERT:
                response = self._chk_permission(request.user_config.group_id_list, rq['ita_driver_id'], response)
                if response['status'] == 'failure':
                    return response

            #削除以外の場合の入力チェック
            if ope != defs.DABASE_OPECODE.OPE_DELETE:
                error_flag = self._validate(rq, error_msg, request)
            if error_flag:
                raise Exception('validation error.')

            # パスワードを暗号化
            cipher = AESCipher(settings.AES_KEY)

            if ope == defs.DABASE_OPECODE.OPE_UPDATE:
                encrypted_password = cipher.encrypt(rq['password'])

                driver = ItaDriver.objects.get(ita_driver_id=rq['ita_driver_id'])
                driver.ita_disp_name = rq['ita_disp_name']
                driver.version = rq['version']
                driver.protocol = rq['protocol']
                driver.hostname = rq['hostname']
                driver.port = rq['port']
                driver.username = rq['username']
                driver.password = encrypted_password
                driver.last_update_user = request.user.user_name
                driver.last_update_timestamp = now
                driver.save(force_update=True)

                permission_list_reg = []
                for pm in rq['permission']:
                    rcnt = ItaPermission.objects.filter(
                        ita_driver_id=rq['ita_driver_id'],
                        group_id=pm['group_id']
                    ).count()

                    if rcnt > 0:
                        ItaPermission.objects.filter(
                            ita_driver_id=rq['ita_driver_id'],
                            group_id=pm['group_id']
                        ).update(
                            permission_type_id = pm['permission_type_id'],
                            last_update_timestamp = now,
                            last_update_user = request.user.user_name
                        )
                    else:
                        permission_list_reg.append(
                            ItaPermission(
                                ita_driver_id = rq['ita_driver_id'],
                                group_id = pm['group_id'],
                                permission_type_id = pm['permission_type_id'],
                                last_update_timestamp = now,
                                last_update_user = request.user.user_name
                            )
                        )

                if len(permission_list_reg) > 0:
                    ItaPermission.objects.bulk_create(permission_list_reg)

            elif ope == defs.DABASE_OPECODE.OPE_DELETE:
                ItaDriver.objects.get(pk=rq['ita_driver_id']).delete()
                ItaPermission.objects.filter(ita_driver_id=rq['ita_driver_id']).delete()

            elif ope == defs.DABASE_OPECODE.OPE_INSERT:
                encrypted_password = cipher.encrypt(rq['password'])

                driver = ItaDriver(
                    ita_disp_name = rq['ita_disp_name'],
                    version = rq['version'],
                    protocol = rq['protocol'],
                    hostname = rq['hostname'],
                    port = rq['port'],
                    username = rq['username'],
                    password = encrypted_password,
                    last_update_user = request.user.user_name,
                    last_update_timestamp = now,
                ).save(force_insert=True)

                ita_driver_id = ItaDriver.objects.get(ita_disp_name=rq['ita_disp_name']).ita_driver_id

                permission_list_reg = []
                for pm in rq['permission']:
                    permission = ItaPermission(
                        ita_driver_id = ita_driver_id,
                        group_id = pm['group_id'],
                        permission_type_id = pm['permission_type_id'],
                        last_update_timestamp = now,
                        last_update_user = request.user.user_name,
                    )
                    permission_list_reg.append(permission)
                ItaPermission.objects.bulk_create(permission_list_reg)
                logger.user_log('LOSI27007', 'web_app.models.ITA_models', request=request)

        except ItaDriver.DoesNotExist:
            logger.logic_log('LOSM07006', "ita_driver_id", ita_driver_id, request=request)

        except Exception as e:
            logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
            alert_msg = error_msg.pop('permission')
            response = {
                    'status': 'failure',
                    'error_msg': error_msg,  # エラー詳細(エラーアイコンで出す)
                    'alert_msg': alert_msg,
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
        emo_flag_ita_disp_name = False
        emo_flag_hostname = False


        if len(rq['ita_disp_name']) == 0:
            error_flag = True
            error_msg['ita_disp_name'] += get_message('MOSJA27101', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07001', 'ita_disp_name', request=request)

        if len(rq['ita_disp_name']) > 64:
            error_flag = True
            error_msg['ita_disp_name'] += get_message('MOSJA27102', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07002', 'ita_disp_name', 64, rq['ita_disp_name'], request=request)

        # 絵文字チェック
        value_list = emo_chk.is_emotion(rq['ita_disp_name'])
        if len(value_list) > 0:
            error_flag = True
            emo_flag_ita_disp_name   = True
            error_msg['ita_disp_name'] += get_message('MOSJA27120', request.user.get_lang_mode(), showMsgId=False) + '\n'

        if len(rq['version']) == 0:
            error_flag = True
            error_msg['version'] += get_message('MOSJA27126', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07001', 'version', request=request)

        if len(rq['version']) > 64:
            error_flag = True
            error_msg['version'] += get_message('MOSJA27127', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07002', 'version', 64, rq['version'], request=request)

        if len(rq['protocol']) == 0:
            error_flag = True
            error_msg['protocol'] += get_message('MOSJA27115', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07001', 'protocol', request=request)

        if len(rq['protocol']) > 8:
            error_flag = True
            error_msg['protocol'] += get_message('MOSJA27116', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07002', 'protocol', 8, rq['protocol'], request=request)

        if len(rq['hostname']) == 0:
            error_flag = True
            error_msg['hostname'] += get_message('MOSJA27103', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07001', 'hostname', request=request)

        if len(rq['hostname']) > 128:
            error_flag = True
            error_msg['hostname'] += get_message('MOSJA27104', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07002', 'hostname', 128, rq['hostname'], request=request)

        # 絵文字チェック
        value_list = emo_chk.is_emotion(rq['hostname'])
        if len(value_list) > 0:
            error_flag = True
            emo_flag_hostname = True
            error_msg['hostname'] += get_message('MOSJA27121', request.user.get_lang_mode(), showMsgId=False) + '\n'

        if len(rq['port']) == 0:
            error_flag = True
            error_msg['port'] += get_message('MOSJA27105', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07001', 'port', request=request)

        try:
            tmp_port = int(rq['port'])
            if 0 > tmp_port or tmp_port > 65535:
                error_flag = True
                error_msg['port'] += get_message('MOSJA27106', request.user.get_lang_mode()) + '\n'
                logger.user_log('LOSM07003', 'port', rq['port'], request=request)
        except ValueError:
            error_flag = True
            error_msg['port'] += get_message('MOSJA27106', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07003', 'port', rq['port'], request=request)

        if len(rq['username']) == 0:
            error_flag = True
            error_msg['username'] += get_message('MOSJA27107', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07001', 'username', request=request)

        if len(rq['username']) > 64:
            error_flag = True
            error_msg['username'] += get_message('MOSJA27108', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07002', 'username', 64, rq['username'], request=request)

        # 絵文字チェック
        value_list = emo_chk.is_emotion(rq['username'])
        if len(value_list) > 0:
            error_flag = True
            error_msg['username'] += get_message('MOSJA27122', request.user.get_lang_mode(), showMsgId=False) + '\n'

        if len(rq['password']) == 0:
            error_flag = True
            error_msg['password'] += get_message('MOSJA27109', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07001', 'password', request=request)

        driver_info_old = ItaDriver.objects.filter(ita_driver_id=rq['ita_driver_id'])
        if len(driver_info_old) > 0 and driver_info_old[0].password != rq['password']:
            if len(rq['password']) > 64:
                error_flag = True
                error_msg['password'] += get_message('MOSJA27110', request.user.get_lang_mode()) + '\n'
                logger.user_log('LOSM07002', 'password', 64, rq['password'], request=request)

            # 絵文字チェック
            value_list = emo_chk.is_emotion(rq['password'])
            if len(value_list) > 0:
                error_flag = True
                error_msg['password'] += get_message('MOSJA27123', request.user.get_lang_mode(), showMsgId=False) + '\n'


        if not emo_flag_ita_disp_name:
            duplication = ItaDriver.objects.filter(ita_disp_name=rq['ita_disp_name'])
            if len(duplication) == 1 and int(rq['ita_driver_id']) != duplication[0].ita_driver_id:
                error_flag = True
                error_msg['ita_disp_name'] += get_message('MOSJA27111', request.user.get_lang_mode()) + '\n'
                logger.user_log('LOSM07004', 'ita_disp_name', rq['ita_disp_name'], request=request)


        if not emo_flag_hostname:
            duplication = ItaDriver.objects.filter(hostname=rq['hostname'])
            if len(duplication) == 1 and int(rq['ita_driver_id']) != duplication[0].ita_driver_id:
                error_flag = True
                error_msg['hostname'] += get_message('MOSJA27112', request.user.get_lang_mode()) + '\n'
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
                error_msg['ita_disp_name'] += get_message('MOSJA27119', request.user.get_lang_mode()) + '\n'
                logger.user_log('LOSM07005', rq['hostname'], rq['port'], request=request)


        # 権限の確認(更新権限を有するグループが1つ以上存在すること)
        perm_count = 0
        for perm_info in rq['permission']:
            if int(perm_info['permission_type_id']) == defs.ALLOWED_MENTENANCE:
                perm_count = perm_count + 1

        if perm_count < 1:
            error_flag = True
            error_msg['permission'] += get_message('MOSJA27128', request.user.get_lang_mode()) + '\n'


        logger.logic_log('LOSI00002', 'return: %s' % error_flag)
        return error_flag

    def _chk_permission(self, group_id_list, ita_driver_id, response):

        pti = ItaPermission.objects.filter(group_id__in=group_id_list, ita_driver_id=ita_driver_id, permission_type_id=1)

        if pti.count() == 0:
            response = {
                'status': 'failure',
                'notpermitted': True,
            }
        return response

