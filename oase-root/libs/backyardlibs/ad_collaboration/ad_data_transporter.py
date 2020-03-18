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
    ActiveDirectory データ取得機能

"""

import ast
import django
import json
import os
import sys

# import検索パス追加
my_path = os.path.dirname(os.path.abspath(__file__))
tmp_path = my_path.split('oase-root')
root_dir_path = tmp_path[0] + 'oase-root'
sys.path.append(root_dir_path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'confs.frameworkconfs.settings'
django.setup()

from django.conf import settings
from libs.commonlibs.aes_cipher import AESCipher
from libs.commonlibs.ad_authenticator import AdAuthenticator
from libs.commonlibs.define import AD_AUTH
from web_app.models.models import System

class AdDataTransporter:
    """
    [クラス概要]
        ActiveDirectory データ取得クラス
    """

    def __init__(self, logger):
        """
        [概要]
            コンストラクタ
        """

        self.__logger = logger
        self._conn = None

    def _get_system_confs(self):
        """
        [概要]
            AD認証に必要なシステム設定取得
        """

        self.__logger.logic_log('LOSI00001', os.path.abspath(__file__), sys._getframe().f_code.co_name, None)

        system_confs = System.objects.filter(category='ACTIVE_DIRECTORY').values('config_id', 'value')
        system_confs_dict = {key_value['config_id']: key_value['value'] for key_value in system_confs}

        # AccessPointのカンマ区切り文字列を、分割して配列化
        tmp_hosts = system_confs_dict['ACCESS_POINT']
        hosts = [host_str.strip() for host_str in tmp_hosts.split(',')]
        system_confs_dict['hosts'] = hosts

        # Group情報の文字列をkey-value化
        tmp_groups = system_confs_dict['TARGET_GROUP_LIST']
        groups_list = ast.literal_eval(tmp_groups)
        groups_dict = {}
        for g in groups_list:
            groups_dict.update(g)

        system_confs_dict['groups'] = groups_dict

        # パスワードの暗号化解除
        cipher = AESCipher(settings.AES_KEY)
        tmp_password = system_confs_dict['ADMINISTRATOR_PW']
        system_confs_dict['ADMINISTRATOR_PW'] = cipher.decrypt(tmp_password)

        self.__logger.logic_log('LOSI00002', '')
        return system_confs_dict

    def _get_groups(self, search_base, target_group_names):
        """
        [概要]
            ADからグループを取得する
        """

        self.__logger.logic_log('LOSI00001', os.path.abspath(__file__), sys._getframe().f_code.co_name,
            'search_base: %s, target_group_names: %s' % (search_base, ','.join(target_group_names)))

        ad_groups = []

        for group_name in target_group_names:
            success = self._conn.search(
                            search_base=search_base,
                            search_filter='(&(objectClass=group)(cn=%s))' % group_name,
                        )
            if not success or len(self._conn.entries) != 1:
                self.__logger.logic_log('LOSI11002', group_name)
                continue

            ad_groups.append(group_name)

        self.__logger.logic_log('LOSI00002', '')
        return ad_groups

    def _get_user_objects(self, search_base, ad_groups):
        """
        [概要]
            ADからユーザを取得する
        """

        self.__logger.logic_log('LOSI00001', os.path.abspath(__file__), sys._getframe().f_code.co_name,
            'search_base: %s, ad_groups: %s' % (search_base, ','.join(ad_groups)))

        ad_users = {}

        for adgp in ad_groups:
            success = self._conn.search(
                            search_base=search_base,
                            search_filter='(&(objectClass=user)(memberof=cn=%s,%s))' % (adgp, search_base),
                            attributes=['userPrincipalName', 'displayName', 'mail'],
                        )

            for entry in self._conn.entries:

                ### DEBUG用メモ entryの中、強制的に見るやつ
                # for d in dir(entry):
                #     print(d)
                #     attr = getattr(entry, d)
                #     print('{}:\t{}'.format(d, attr))

                login_id = str(entry.userPrincipalName)
                display_name = str(entry.displayName)
                mail = str(entry.mail if len(entry.mail) > 0 else '')

                if login_id in ad_users:
                    ad_users[login_id]['group'].append(adgp)
                else:
                    ad_users[login_id] = {
                        'login_id'    : login_id,
                        'display_name': display_name,
                        'mail'        : mail,
                        'group'       : [adgp],
                    }

        self.__logger.logic_log('LOSI00002', '')
        return ad_users

    def get_groups_and_users(self):
        """
        [概要]
            ADに認証して、グループとユーザの情報を取得する
        """

        self.__logger.logic_log('LOSI00001', os.path.abspath(__file__), sys._getframe().f_code.co_name, None)

        system_confs_dict = self._get_system_confs()
        search_path = system_confs_dict['AUTHSERVER_SEARCH_CHAR']

        authenticator = AdAuthenticator(
                                search_path=search_path,
                                hosts=system_confs_dict['hosts'],
                                use_ssl=False, # TODO
                                port=389,      # TODO
                                connect_timeout=int(system_confs_dict['CONNECTION_TIMEOUT']),
                                read_timeout=int(system_confs_dict['READ_TIMEOUT']),
                            )

        conn_result = authenticator.authenticate(system_confs_dict['ADMINISTRATOR_USER'], system_confs_dict['ADMINISTRATOR_PW'])
        if conn_result != AD_AUTH.RESULT_SUCCESS:
            self.__logger.system_log('LOSI00002', 'raise Exception')
            raise Exception('Fail to authenticate with ActiveDirectory.')

        self._conn = authenticator.get_connection()

        ad_groups = self._get_groups(search_path, system_confs_dict['groups'].keys())

        ad_users = self._get_user_objects(search_path, ad_groups)

        ad_data = {'group': ad_groups, 'user': ad_users}

        self.__logger.logic_log('LOSI00002', '')
        return ad_data

########################################
# DEBUG Code
########################################
if __name__=='__main__':

    obj = AdDataTransporter(None)

    ad_data = obj.get_groups_and_users()
    print(ad_data)
