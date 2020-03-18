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
    ActiveDirectory連携機能

"""

import ast
import copy
import json
import os
import django
import sys
import traceback
import pytz
import datetime

my_path = os.path.dirname(os.path.abspath(__file__))
tmp_path = my_path.split('oase-root')
root_dir_path = tmp_path[0] + 'oase-root'
sys.path.append(root_dir_path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'confs.frameworkconfs.settings'
django.setup()

from django.db import transaction
from django.conf import settings

from libs.backyardlibs.ad_collaboration.ad_data_transporter import AdDataTransporter
from libs.commonlibs import define as defs
from libs.commonlibs.oase_logger import OaseLogger
from web_app.models.models import AccessPermission
from web_app.models.models import Group
from web_app.models.models import User
from web_app.models.models import UserGroup
from web_app.models.models import System

AD_COLLABORATION_USER_ID = -2140000004
BACKYARD_USER = User.objects.get(pk=AD_COLLABORATION_USER_ID)

class AdCollabExecutor():

    def __init__(self):
        """
        [概要]
            コンストラクタ

        [引数]
            なし
        """

        self.__logger = OaseLogger.get_instance()

    def _data_clean(self, ad_on_flag):
        """
        [概要]
            データ削除処理

        [引数]
            ad_on_flag: AD連携がONかOFFか
        """

        self.__logger.logic_log('LOSI00001', 'ad_on_flag: %s' % ad_on_flag)

        # ADがONなら、AD以外の(フラグ「0」)のデータを削除、OFFなら逆
        target_flag = '0' if ad_on_flag else '1'

        # ADフラグに応じてユーザ,グループ関連のレコードを削除
        del_groupid_list = list(Group.objects.filter(ad_data_flag=target_flag).exclude(pk__lte=1).values_list('group_id', flat=True))
        Group.objects.filter(pk__in=del_groupid_list).delete()
        AccessPermission.objects.filter(group_id__in=del_groupid_list).delete()
        User.objects.filter(ad_data_flag=target_flag).exclude(pk__lte=1).delete()
        UserGroup.objects.filter(ad_data_flag=target_flag).exclude(pk__lte=1).delete()

        self.__logger.logic_log('LOSI00002', '')

    def _collaborate_data(self, ad_data):
        """
        [概要]
            AD データ連携処理

        [引数]
            ad_data: 連携するADデータ

            # ad_data['group'] = [groupname]

            # ad_data['user'] = ad_users
            #   ad_users[login_id] = {
            #       'login_id'   : login_id,
            #       'display_name': display_name,
            #       'mail'       : mail,
            #       'group'      : [adgp],
            #   }
        """

        self.__logger.logic_log('LOSI00001', 'ad_data: %s' % json.dumps(ad_data))

        # --------------------------------
        # データ整理
        # --------------------------------
        ### システム設定のグループ名変換(AD_attribute->OASE_group_name) ###
        system_confs_group_list = System.objects.get(config_id='TARGET_GROUP_LIST').value
        groups_list = ast.literal_eval(system_confs_group_list)
        groups_dict = {}
        for g in groups_list:
            groups_dict.update(g)

        ### グループ ###
        cur_ad_grp_name_set = set([groups_dict[ad_gname] for ad_gname in ad_data['group']])
        oase_ad_group = list(Group.objects.filter(ad_data_flag='1'))
        oase_ad_grp_dict = {grp.group_name: grp for grp in oase_ad_group}
        oase_ad_grp_name_set = set(oase_ad_grp_dict.keys())

        ### ユーザ ###
        cur_ad_user_dict = ad_data['user']
        cur_ad_user_login_id_set = set(cur_ad_user_dict.keys())
        oase_ad_user = list(User.objects.filter(ad_data_flag='1', disuse_flag='0'))
        oase_ad_user_dict = {user.login_id: user for user in oase_ad_user}
        oase_ad_user_login_id_set = set(oase_ad_user_dict.keys())

        ### ユーザグループ ###
        user_group_link = []
        for login_id, user_info in ad_data['user'].items():
            for user_group_name in user_info['group']:
                user_group_link.append(login_id + ':' + groups_dict[user_group_name])
        cur_ad_user_grp_key_set = set(user_group_link)
        oase_ad_user_group = list(UserGroup.objects.filter(ad_data_flag='1'))
        oase_ad_user_user_id_dict = {user.user_id: user.login_id for user in oase_ad_user}
        oase_ad_grp_grp_id_dict = {grp.group_id: grp.group_name for grp in oase_ad_group}
        oase_ad_user_grp_dict = { # {login_id+group_name: user_group_id} としたい
                oase_ad_user_user_id_dict[usrgrp.user_id] + ':' + oase_ad_grp_grp_id_dict[usrgrp.group_id]: usrgrp
                    for usrgrp in oase_ad_user_group
            }
        oase_ad_user_grp_key_set = set(oase_ad_user_grp_dict.keys())

        now = datetime.datetime.now(pytz.timezone('UTC'))
        modified_user_id_link_user_grp = []

        # --------------------------------
        # 追加系(グループ → ユーザ → ユーザグループ)
        # --------------------------------

        ### グループ ###
        add_target_grp = cur_ad_grp_name_set - oase_ad_grp_name_set
        add_grp_bulk_list = []
        tmp_grp = None
        for agrp_name in add_target_grp:
            tmp_grp = Group(
                        group_name = agrp_name,
                        summary = '',
                        ad_data_flag = '1',
                        last_update_user = BACKYARD_USER.user_name,
                        last_update_timestamp = now
                    )
            add_grp_bulk_list.append(copy.deepcopy(tmp_grp))

        self.__logger.logic_log('LOSI11000', 'add_grp_bulk_list: %s' % ','.join([g.group_name for g in add_grp_bulk_list]))
        if len(add_grp_bulk_list) > 0:
            Group.objects.bulk_create(add_grp_bulk_list)

            # 権限を追加
            # 選択されたグループを取得
            inserted_group_name = []
            for group in add_grp_bulk_list:
                inserted_group_name.append(group.group_name)

            inserted_group_list = Group.objects.filter(group_name__in=inserted_group_name)

            permission_list = []
            permission_record = None
            for inserted_group in inserted_group_list:
                for menu_id in defs.MENU:

                    permission_record = AccessPermission(
                            group_id = inserted_group.group_id,
                            menu_id = menu_id,
                            permission_type_id = defs.ALLOWED_MENTENANCE if menu_id == 2141003001 else defs.NO_AUTHORIZATION,
                            last_update_user = BACKYARD_USER.user_name,
                            last_update_timestamp = now
                        )

                    permission_list.append(copy.deepcopy(permission_record))

            AccessPermission.objects.bulk_create(permission_list)

        ### ユーザ ###
        add_target_user_login_id = cur_ad_user_login_id_set - oase_ad_user_login_id_set
        add_user_bulk_list = []
        tmp_user = None
        for auser_login_id in add_target_user_login_id:
            ad_user_info = cur_ad_user_dict[auser_login_id]
            tmp_user = User(
                        login_id = ad_user_info['login_id'],
                        user_name = ad_user_info['display_name'],
                        password = 'oase_ad_collaboration', # 仮...ログインでは使われない
                        mail_address = ad_user_info['mail'] if len(ad_user_info['mail']) > 0 else 'oase_ad_collaboration_' + ad_user_info['login_id'],
                        lang_mode_id = defs.LANG_MODE.JP,
                        disp_mode_id = defs.DISP_MODE.DEFAULT,
                        ad_data_flag = '1',
                        disuse_flag = '0',
                        last_update_user = BACKYARD_USER.user_name,
                        last_update_timestamp = now
                    )
            add_user_bulk_list.append(copy.deepcopy(tmp_user))

        self.__logger.logic_log('LOSI11000', 'add_user_bulk_list: %s' % ','.join([u.user_name + '(' + u.login_id + ')' for u in add_user_bulk_list]))
        if len(add_user_bulk_list) > 0:
            User.objects.bulk_create(add_user_bulk_list)

        ### ユーザグループ ###
          # ユーザとグループは新規分も考慮して再取得
        oase_ad_user_after = list(User.objects.filter(ad_data_flag='1', disuse_flag='0'))
        oase_ad_user_dict_after = {user.login_id: user for user in oase_ad_user_after}
        oase_ad_group_after = list(Group.objects.filter(ad_data_flag='1'))
        oase_ad_grp_dict_after = {grp.group_name: grp for grp in oase_ad_group_after}

        add_target_user_grp_key = cur_ad_user_grp_key_set - oase_ad_user_grp_key_set
        add_user_grp_bulk_list = []
        for auser_grp_key in add_target_user_grp_key:
            login_id, group_name = auser_grp_key.split(':')
            tmp_user_group = UserGroup(
                        user_id = oase_ad_user_dict_after[login_id].user_id,
                        group_id = oase_ad_grp_dict_after[group_name].group_id,
                        ad_data_flag = '1',
                        last_update_user = BACKYARD_USER.user_name,
                        last_update_timestamp = now
                    )
            add_user_grp_bulk_list.append(copy.deepcopy(tmp_user_group))
            modified_user_id_link_user_grp.append(tmp_user_group.user_id)

        self.__logger.logic_log('LOSI11000', 'add_user_grp_bulk_list: %s' % ','.join([str(ug.user_id) + '-' + str(ug.group_id) for ug in add_user_grp_bulk_list]))
        if len(add_user_grp_bulk_list) > 0:
            UserGroup.objects.bulk_create(add_user_grp_bulk_list)

        # --------------------------------
        # 削除系(ユーザグループ → ユーザ → グループ)
        # --------------------------------
        ### ユーザグループ ###
        del_target_user_grp_key = oase_ad_user_grp_key_set - cur_ad_user_grp_key_set
        del_user_grp_id_list = []
        for user_grp_key in del_target_user_grp_key:
            del_user_grp_id_list.append(oase_ad_user_grp_dict[user_grp_key].user_group_id)
            modified_user_id_link_user_grp.append(oase_ad_user_grp_dict[user_grp_key].user_id)

        self.__logger.logic_log('LOSI11000', 'del_user_grp_id_list: %s' % ','.join(map(str, del_user_grp_id_list)))
        if len(del_user_grp_id_list) > 0:
            UserGroup.objects.filter(ad_data_flag='1',pk__in=del_user_grp_id_list).delete()

        ### ユーザ ###
        del_target_user_login_id = oase_ad_user_login_id_set - cur_ad_user_login_id_set
        del_user_id_list = [oase_ad_user_dict[d].user_id for d in del_target_user_login_id]

        if len(del_user_id_list) > 0:
            User.objects.filter(ad_data_flag='1',pk__in=del_user_id_list).delete()

        ### グループ ###
        del_target_grp_name = oase_ad_grp_name_set - cur_ad_grp_name_set
        del_grp_id_list = [oase_ad_grp_dict[d].group_id for d in del_target_grp_name]

        self.__logger.logic_log('LOSI11000', 'del_grp_id_list: %s' % ','.join(map(str, del_grp_id_list)))
        if len(del_grp_id_list) > 0:
            # delGrpQuerySet = Group.objects.filter(ad_data_flag='1',pk__in=del_grp_id_list)
            # delGrpQuerySet._raw_delete(delGrpQuerySet.db)
            AccessPermission.objects.filter(pk__in=del_grp_id_list).delete()
            Group.objects.filter(ad_data_flag='1', pk__in=del_grp_id_list).delete()

        # --------------------------------
        # 更新系(ユーザ)
        # --------------------------------
        ### ユーザ ###
        modify_target_user_login_id = oase_ad_user_login_id_set & cur_ad_user_login_id_set
        self.__logger.logic_log('LOSI11000', 'modify_target_user_login_id: %s' % ','.join(map(str, modify_target_user_login_id)))
        for user_login_id in modify_target_user_login_id:
            db_user = oase_ad_user_dict[user_login_id]
            ad_user = cur_ad_user_dict[user_login_id]

            modify_flag = False
            if db_user.user_name != ad_user['display_name']:
                db_user.user_name = ad_user['display_name']
                modify_flag = True
            if db_user.mail_address != ad_user['mail']:
                if not (db_user.mail_address.startswith('oase_ad_collaboration_') and len(ad_user['mail']) == 0):
                    db_user.mail_address = ad_user['mail']
                    modify_flag = True
            if modify_flag == True:
                db_user.last_update_user = BACKYARD_USER.user_name
                db_user.last_update_timestamp = now
                db_user.save()

        # 処理途中でユーザグループが変更されたユーザの最終更新日時を更新する
        self.__logger.logic_log('LOSI11000', 'modified_user_id_link_user_grp: %s' % ','.join(map(str, modified_user_id_link_user_grp)))
        if len(modified_user_id_link_user_grp) > 0:
            User.objects.filter(ad_data_flag='1',pk__in=modified_user_id_link_user_grp) \
                .update(
                        last_update_user = BACKYARD_USER.user_name,
                        last_update_timestamp = now
                    )

        self.__logger.logic_log('LOSI00002', '')

    def execute(self):
        """
        [概要]
            AD連携 メイン処理

        [引数]
            無し

        [戻り値]
            bool: 成功/失敗
        """

        self.__logger.logic_log('LOSI00001', 'None')
        try:

            with transaction.atomic():
                self.__logger.system_log('LOSI00010')

                #--------------------------
                # システム設定取得
                #--------------------------
                conf_ad_collab = System.objects.select_for_update().get(config_id='ADCOLLABORATION')
                self.__logger.logic_log('LOSI11001', 'ADCOLLABORATION=>value: %s' % conf_ad_collab.value)

                if conf_ad_collab.value == '1':
                    #--------------------------
                    # AD連携が Onなら
                    #--------------------------

                    transporter = AdDataTransporter(self.__logger)

                    ad_data = transporter.get_groups_and_users()

                    # groupとuserをロック
                    Group.objects.select_for_update().filter(pk__gt=1)
                    User.objects.select_for_update().filter(pk__gt=1)

                    self._data_clean(ad_on_flag=True)

                    self._collaborate_data(ad_data)

                else:
                    #--------------------------
                    # AD連携が Offなら
                    #--------------------------

                    # groupとuserをロック
                    Group.objects.select_for_update().filter(pk__gt=1)
                    User.objects.select_for_update().filter(pk__gt=1)

                    self._data_clean(ad_on_flag=False)

                self.__logger.system_log('LOSI00011')

        except Exception as e:

            self.__logger.system_log('LOSI00012')
            self.__logger.system_log('LOSI00005', traceback.format_exc())
            self.__logger.system_log('LOSM11000')

            self.__logger.logic_log('LOSI00002', 'fail')
            print(self.__logger.get_last_error())
            return False

        self.__logger.logic_log('LOSI00002', 'success')
        return True


#--------------------------
# メイン処理
#--------------------------
if __name__=='__main__':

    executor = AdCollabExecutor()
    executor.execute()
