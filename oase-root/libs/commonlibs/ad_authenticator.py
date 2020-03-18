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
    ActiveDirectory 認証機能

"""

import os
import sys
from ldap3 import Server
from ldap3 import Connection
from ldap3 import AUTO_BIND_NONE
from ldap3 import SUBTREE
from ldap3 import SYNC
from ldap3 import SIMPLE

# import検索パス追加
this_file_path = os.path.dirname(os.path.abspath(__file__))
tmp_path       = this_file_path.split('oase-root')
root_dir_path  = tmp_path[0] + 'oase-root'
sys.path.append(root_dir_path)

from libs.commonlibs.define import AD_AUTH
from libs.commonlibs.oase_logger import OaseLogger

logger = OaseLogger.get_instance()

class AdAuthenticator:
    """
    [クラス概要]
        ActiveDirectory データ取得クラス
    """

    def __init__(
                self,
                search_path,
                hosts=['localhost',],
                use_ssl=False,
                port=389,
                connect_timeout=3,
                read_timeout=3,
                logger=None):
        """
        [概要]
            コンストラクタ

        [引数]
            search_path : 検索文字列(例:OU=xxx,DC=yyy,DC=zzz)
            hosts       : 対象サーバ名(IP or DNSname)の配列
            use_ssl     : TLSを使うか
            port        : ポート
            connect_timeout: コネクトタイムアウト値(秒)
            read_timeout: 取得タイムアウト値(秒)
            logger      : ロガー
        """

        self._search_path = search_path

        self._hosts = hosts
        self._use_ssl = use_ssl
        self._port = port

        self._connect_timeout = connect_timeout
        self._read_timeout = read_timeout

        self._logger = logger

        self._conn = None

    def authenticate(self, userPrincipalName, password):
        """
        [概要]
            認証

        [引数]
            userPrincipalName: ユーザ名
            password: パスワード
            read_timeout: 取得タイムアウト値(秒)

        [戻り値]
            AD_AUTH結果コード(define.AD_AUTH.RESULT_*)
        """

        # TODO:server_poolのほうが使える？
        server = None
        serverList = []
        for host in self._hosts:
            server = Server(host, port=self._port, use_ssl=self._use_ssl, get_info='ALL', connect_timeout=self._connect_timeout)

            # 対象hostの応答がなければ次のhostへ
            if not server.check_availability() :
                continue

            # 応答があればそれを使用する
            logger.logic_log('LOSI11003', host)
            serverList.append(server)

        if len(serverList) == 0:
            # すべてのhostがNGの場合はエラー
            logger.logic_log('LOSM11001', ', '.join(self._hosts))
            return AD_AUTH.RESULT_OTHER_ERROR

        try:
            # step1. domainに対する認証
            conn = Connection(
                        serverList,
                        auto_bind=AUTO_BIND_NONE,
                        client_strategy=SYNC,
                        user=userPrincipalName,
                        password=password,
                        authentication=SIMPLE,
                        check_names=True,
                        receive_timeout=self._read_timeout
                    )

            if not conn.bind():
                logger.logic_log('LOSM11002', conn.last_error, conn.result['message'])
                result_message = conn.result['message']

                error_code = AD_AUTH.RESULT_OTHER_ERROR
                if AD_AUTH.REGEXP_INVALID_CREDENCIALS_MESSAGE.match(result_message):
                    error_code = AD_AUTH.RESULT_INVALID_CREDENCIALS
                    error_message = 'Authentication information error'
                if AD_AUTH.REGEXP_ACCOUNT_LOCKED_MESSAGE.match(result_message):
                    error_code = AD_AUTH.RESULT_ACCOUNT_LOCKED
                    error_message = 'Account lock status'

                logger.logic_log('LOSM11003', error_code, error_message)
                return error_code

            # step2. 検索文字列で指定される組織内に存在するか
            # TODO 管理者の認証のときは除外する？
            success = conn.search(search_base=self._search_path,
                        search_filter='(userPrincipalName=%s)' % userPrincipalName,
                        search_scope=SUBTREE)
            if not success or len(conn.entries) != 1:
                logger.logic_log('LOSM11004', self._search_path)
                return AD_AUTH.RESULT_INVALID_CREDENCIALS

        except Exception as e:
            logger.system_log('LOSM11005', server.host, userPrincipalName)
            return AD_AUTH.RESULT_OTHER_ERROR

        logger.system_log('LOSI11004', conn)

        # 成功時
        self._conn = conn
        return AD_AUTH.RESULT_SUCCESS

    def get_connection(self):
        """
        [概要]
            コネクション外だし

        [引数]
            なし

        [戻り値]
            接続に成功したコネクション
        """

        return self._conn


########################################
# DEBUG Code
########################################
if __name__=='__main__':

    authenticator = AdAuthenticator(
                            search_path='OU=OASEtestOU,DC=mas,DC=local',
                            hosts=['10.132.34.133',],
                            use_ssl=False,
                            port=389,
                            connect_timeout=3,
                            read_timeout=3
                        )

    authenticator.authenticate(username='OASEAdAdmin', password='P@$$w0rd')
