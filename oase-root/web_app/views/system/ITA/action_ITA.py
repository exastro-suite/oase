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
    def get_info_list(cls):

        try:
            ita_driver_obj_list = ItaDriver.objects.all()

        except Exception as e:
            # ここでの例外は大外で拾う
            raise

        protocol_dict = cls.get_define()['dict']
        permission_list = cls.get_permission()

        ita_driver_dto_list = []
        cipher = AESCipher(settings.AES_KEY)
        for ita_obj in ita_driver_obj_list:
            ita_info = ita_obj.__dict__
            ita_info['password'] = cipher.decrypt(ita_obj.password)
            ita_info['protocol_str'] = protocol_dict[ita_obj.protocol]

            perm_list = []
            perm_dict = {}

            for pm in permission_list:
                logger.logic_log('LOSI00001', ita_obj.ita_driver_id, request=None)
                if ita_obj.ita_driver_id == pm['ita_driver_id']:
                    perm_dict['group_id'] = pm['group_id']
                    perm_dict['group_name'] = pm['group_name']
                    perm_dict['permission_type_id'] = pm['permission_type_id']

            perm_list.append(perm_dict)
            ita_info['permission'] = perm_list
            ita_driver_dto_list.append(ita_info)

        return ita_driver_dto_list


    @classmethod
    def get_group_list(cls, ita_driver_id, permission_list):
        """
        [概要]
        permission情報の格納データ用成型
        """
        perm_list = []
        perm_dict = {}

        # ita_info['permission'] = {'ita_driver_id': 1,  'group_id': 2, 'permission_type_id': 2, 'group_name': '権限なし'}
        for pm in permission_list:
            logger.logic_log('LOSI00001', ita_driver_id, request=None)
            if ita_driver_id == pm['ita_driver_id']:
                pm_data = {pm[group_id], pm[group_name], pm[permission_type_id]}
            perm_dict.append(pm_data)

        perm_list.append(perm_dict)
        return perm_dict


    @classmethod
    def get_group_list(cls):
        """
        [概要]
        グループ一覧を取得する(システム管理グループを除く)
        """

        grp_list = Group.objects.filter(group_id__gt=1).values('group_id', 'group_name')
        return grp_list

    @classmethod
    def get_permission(cls):
        """
        [概要]
        権限情報を作成する
        """

        grp_list = cls.get_group_list()
        ItaPerm_list = ItaPermission.objects.filter().values('ita_driver_id', 'group_id', 'permission_type_id')

        perm_list = []
        for ita in ItaPerm_list:
            ex_flg = False
            for grp in grp_list:
                if ita['group_id'] == grp['group_id']:
                    ita['group_name'] = grp['group_name']
                    perm_list.append(ita)
                    ex_flg = True
                    break
            else:
                if ex_flg == False:
                    ita['group_name'] = '権限なし'
                    perm_list.append(ita)

        return perm_list

    @classmethod
    def get_AutherSettings(cls):
        """
        [概要]
        権限情報を作成する
        """
        imaabd = ITAMessageAnalysissAuthByDriver()
        hasUpdateAuthority = True if imaabd.auth_create_names == defs.ALLOWED_MENTENANCE else False
        object_flg = 0
        drv_msg_ids_disp = []
        drv_msg_ids_edit = []

        drv_msg_ids_disp.extend(imaabd.get_modify_names([defs.VIEW_ONLY, defs.ALLOWED_MENTENANCE]))
        drv_msg_ids_edit.extend(imaabd.get_modify_names(defs.ALLOWED_MENTENANCE))

        try:
            #==================取得=================#
            filters = {}
            if request and request.method == 'POST':
                filters = request.POST.get('filters', None)
                filters = json.loads(filters)

            # 参照以上の権限を持つルール種別IDをフィルター条件に追加
            if '_id' not in filters:
                filters['ita_driver_id'] = {}

            if 'LIST' not in filters['ita_driver_id']:
                filters['ita_driver_id']['LIST'] = []

            filters['ita_driver_id']['LIST'].extend(drv_msg_ids_disp)

            # 情報を取得
            decision_table_list = _select(filters)
            msg = get_message('MOSJA11000', lang) if not decision_table_list else ''

            # ディシジョンテーブル情報に操作権限情報を追加
            for dt in decision_table_list:
                auth_val = imaabd.get_auth_table_val(dt['pk'])
                dt.update(
                    {
                        'allow_view'     : imaabd.allow_view(auth_val, dt['pk']),
                        'allow_create'   : imaabd.allow_create(auth_val, dt['pk']),
                        'allow_update'   : imaabd.allow_update(auth_val, dt['pk']),
                        'allow_delete'   : imaabd.allow_delete(auth_val, dt['pk']),
                    }
                )

            group_list, group_list_default = get_group_list(drv_msg_ids_disp)
            add_group_information(decision_table_list, group_list)

            # 条件名の言語別変換処理
            ce = ConditionalExpression.objects.all()
            for c in ce:
                c.operator_name = get_message(c.operator_name, lang, showMsgId=False)

            #==================編集モード判定=================#
            if request and request.method == 'POST':
                edit_mode = request.POST.get('edit_mode', False)

        except Exception as e:
            msg = get_message('MOSJA11013', lang)
            logger.logic_log('LOSI00005', traceback.format_exc(), request=request)

        return permission_data

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
            'protocol' : '',
            'hostname' : '',
            'port' : '',
            'username' : '',
            'password' : '',
        }
        now = datetime.datetime.now(pytz.timezone('UTC'))
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

            # パスワードを暗号化
            cipher = AESCipher(settings.AES_KEY)

            if ope == defs.DABASE_OPECODE.OPE_UPDATE:
                encrypted_password = cipher.encrypt(rq['password'])

                driver = ItaDriver.objects.get(ita_driver_id=rq['ita_driver_id'])
                driver.ita_disp_name = rq['ita_disp_name']
                driver.protocol = rq['protocol']
                driver.hostname = rq['hostname']
                driver.port = rq['port']
                driver.username = rq['username']
                driver.password = encrypted_password
                driver.last_update_user = request.user.user_name
                driver.last_update_timestamp = now
                driver.save(force_update=True)

                permission = Itapermission.objects.get(ita_permission_id=rq['ita_permission_id'])
                permission.ita_driver_id = rq['ita_driver_id']
                permission.group_id = rq['group_id']
                permission.permission_type_id = rq['permission_type_id']
                permission.last_update_timestamp = now
                permission.last_update_user = request.user.user_name

            elif ope == defs.DABASE_OPECODE.OPE_DELETE:
                ItaDriver.objects.get(pk=rq['ita_driver_id']).delete()
                Itapermission.objects.get(pk=rq['ita_permission_id']).delete()

            elif ope == defs.DABASE_OPECODE.OPE_INSERT:
                encrypted_password = cipher.encrypt(rq['password'])

                driver = ItaDriver(
                    ita_disp_name = rq['ita_disp_name'],
                    protocol = rq['protocol'],
                    hostname = rq['hostname'],
                    port = rq['port'],
                    username = rq['username'],
                    password = encrypted_password,
                    last_update_user = request.user.user_name,
                    last_update_timestamp = now,
                ).save(force_insert=True)

                permission = Itapermission(
                    ita_permission_id = rq['ita_permission_id'],
                    ita_driver_id = rq['ita_driver_id'],
                    group_id = rq['group_id'],
                    permission_type_id = rq['permission_type_id'],
                    last_update_timestamp = now,
                    last_update_user = request.user.user_name,
                )

        except ItaDriver.DoesNotExist:
            logger.logic_log('LOSM07006', "ita_driver_id", ita_driver_id, request=request)

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

        if len(rq['protocol']) == 0:
            error_flag = True
            error_msg['protocol'] += get_message('MOSJA27115', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07001', 'protocol', request=request)

        if len(rq['protocol']) > 64:
            error_flag = True
            error_msg['protocol'] += get_message('MOSJA27116', request.user.get_lang_mode()) + '\n'
            logger.user_log('LOSM07002', 'protocol', 64, rq['protocol'], request=request)

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


        logger.logic_log('LOSI00002', 'return: %s' % error_flag)
        return error_flag


class ITAMessageAnalysissAuthByDriver(object):
    """
    [クラス概要]
      ITAアクションドライバによるメッセージ抽出定義画面の権限制御
    """

    ############################################
    # 値定義
    ############################################
    # 画面操作権限
    ALLOW_403      = 0x0000  # 権限なし(403)
    ALLOW_HIDDEN   = 0x0001  # 非表示
    ALLOW_VIEW     = 0x0002  # 参照可能
    ALLOW_CREATE   = 0x0008  # 新規作成可能
    ALLOW_UPDATE   = 0x0020  # 更新可能
    ALLOW_DELETE   = 0x0040  # 削除可能

    ALLOW_REGIST   = ALLOW_HIDDEN + ALLOW_CREATE
    ALLOW_VIEWONLY = ALLOW_VIEW
    ALLOW_MODIFY   = ALLOW_VIEW   + ALLOW_UPDATE + ALLOW_DELETE
    ALLOW_VIEWREG  = ALLOW_VIEW   + ALLOW_CREATE
    ALLOW_ALL      = ALLOW_VIEW   + ALLOW_CREATE + ALLOW_UPDATE + ALLOW_DELETE

    # 権限種別インデックス
    PERM_INDEX = {
        defs.NO_AUTHORIZATION   : 0,
        defs.VIEW_ONLY          : 1,
        defs.ALLOWED_MENTENANCE : 2,
    }


    ############################################
    # メソッド
    ############################################
    def __init__(self, request):
        """
        [メソッド概要]
          初期化処理
        """

        self.auth_create_analysis = request.user_config.get_menu_auth_type(MENU_ID_CREATE)
        self.auth_modify_analysis = request.user_config.get_activename_auth_type(MENU_ID_MODIFY)

        self.auth_table = [
            #                     メッセージ抽出定義新規追加
            # 権限なし            参照                 更新可能
            [self.ALLOW_403,      self.ALLOW_HIDDEN,   self.ALLOW_REGIST],   # 権限なし
            [self.ALLOW_VIEWONLY, self.ALLOW_VIEWONLY, self.ALLOW_VIEWREG],  # 参照
            [self.ALLOW_MODIFY,   self.ALLOW_MODIFY,   self.ALLOW_ALL],      # 更新可能
        ]


    def get_auth_table_val(self, ita_driver_id):
        """
        [メソッド概要]
          指定ルールの画面操作権限を取得
        [引数]
          ita_driver_id : ITAドライバID
        [戻り値]
          int          : 画面操作権限
        """

        # 指定のルールの権限を取得
        auth_modify = defs.NO_AUTHORIZATION
        if ita_driver_id in self.auth_modify_analysis[defs.NO_AUTHORIZATION]:
            auth_modify = defs.NO_AUTHORIZATION

        elif ita_driver_id in self.auth_modify_analysis[defs.VIEW_ONLY]:
            auth_modify = defs.VIEW_ONLY

        elif ita_driver_id in self.auth_modify_analysis[defs.ALLOWED_MENTENANCE]:
            auth_modify = defs.ALLOWED_MENTENANCE

        # 新規追加画面と更新削除画面の操作権限を取得
        idx_create = self.PERM_INDEX[self.auth_create_analysis]
        idx_modify = self.PERM_INDEX[auth_modify]

        if idx_modify < len(self.auth_table) and idx_create < len(self.auth_table[idx_modify]):
            return self.auth_table[idx_modify][idx_create]

        return self.ALLOW_403


    def get_modify_analysis(self, auth_type_list):

        ret_val = []

        if not isinstance(auth_type_list, list):
            auth_type_list = [auth_type_list, ]

        for auth_type in auth_type_list:
            if auth_type in self.auth_modify_analysis:
                ret_val.extend(self.auth_modify_analysis[auth_type])

        return ret_val


    def is_deny(self, auth_val=None, ita_driver_id=0):
        """
        [メソッド概要]
          403チェック
        [引数]
          ita_driver_id : ITAドライバID
        [戻り値]
          bool         : True=403画面, False=ディシジョンテーブル画面
        """

        if auth_val is None:
            auth_val = self.get_auth_table_val(ita_driver_id)

        if auth_val == self.ALLOW_403:
            return True

        return False


    def is_hidden(self, auth_val=None, ita_driver_id=0):
        """
        [メソッド概要]
          非表示チェック
        [引数]
          ita_driver_id : ITAドライバID
        [戻り値]
          bool         : True=非表示, False=表示
        """

        if auth_val is None:
            auth_val = self.get_auth_table_val(ita_driver_id)

        if auth_val & self.ALLOW_HIDDEN:
            return True

        return False


    def allow_view(self, auth_val=None, ita_driver_id=0):
        """
        [メソッド概要]
          参照可能権限チェック
        [引数]
          ita_driver_id : ITAドライバID
        [戻り値]
          bool         : 参照可否
        """

        if auth_val is None:
            auth_val = self.get_auth_table_val(ita_driver_id)

        if auth_val & self.ALLOW_VIEW:
            return True

        return False


    def allow_download(self, auth_val=None, ita_driver_id=0):
        """
        [メソッド概要]
          DL可能権限チェック
        [引数]
          ita_driver_id : ITAドライバID
        [戻り値]
          bool         : DL可否
        """

        if auth_val is None:
            auth_val = self.get_auth_table_val(ita_driver_id)

        if auth_val & self.ALLOW_DOWNLOAD:
            return True

        return False


    def allow_create(self, auth_val=None, ita_driver_id=0):
        """
        [メソッド概要]
          新規追加権限チェック
        [引数]
          ita_driver_id : ITAドライバID
        [戻り値]
          bool         : 新規追加可否
        """

        if auth_val is None:
            auth_val = self.get_auth_table_val(ita_driver_id)

        if auth_val & self.ALLOW_CREATE:
            return True

        return False


    def allow_copy(self, auth_val=None, ita_driver_id=0):
        """
        [メソッド概要]
          複製権限チェック
        [引数]
          ita_driver_id : ITAドライバID
        [戻り値]
          bool         : 複製可否
        """

        if auth_val is None:
            auth_val = self.get_auth_table_val(ita_driver_id)

        if auth_val & self.ALLOW_COPY:
            return True

        return False


    def allow_update(self, auth_val=None, ita_driver_id=0):
        """
        [メソッド概要]
          更新権限チェック
        [引数]
          ita_driver_id : ITAドライバID
        [戻り値]
          bool         : 更新可否
        """

        if auth_val is None:
            auth_val = self.get_auth_table_val(ita_driver_id)

        if auth_val & self.ALLOW_UPDATE:
            return True

        return False


    def allow_delete(self, auth_val=None, ita_driver_id=0):
        """
        [メソッド概要]
          更新権限チェック
        [引数]
          ita_driver_id : ITAドライバID
        [戻り値]
          bool         : 削除可否
        """

        if auth_val is None:
            auth_val = self.get_auth_table_val(ita_driver_id)

        if auth_val & self.ALLOW_DELETE:
            return True

        return False
