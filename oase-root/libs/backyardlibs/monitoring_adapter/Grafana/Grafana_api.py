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
Grafana apiを使って現在発生している障害を取得する。


"""
import json
import urllib
import requests 
import os
import sys
import hashlib
import pprint
import django
import traceback
import base64

# import検索パス追加
my_path = os.path.dirname(os.path.abspath(__file__))
tmp_path = my_path.split('oase-root')
root_dir_path = tmp_path[0] + 'oase-root'
sys.path.append(root_dir_path)

# OASE モジュール import
# #LOCAL_PATCH#
os.environ['DJANGO_SETTINGS_MODULE'] = 'confs.frameworkconfs.settings'
django.setup()

from django.conf                 import settings
from libs.commonlibs.oase_logger import OaseLogger
from libs.commonlibs.aes_cipher  import AESCipher
from web_app.models.Grafana_monitoring_models import GrafanaAdapter

logger = OaseLogger.get_instance() # ロガー初期化

class GrafanaApi(object):

    def __init__(self, request_rec):
        """
        Grafana API インスタンスを返す
        [引数]
          request_rec: 対象Grafana監視マスタレコード
        """

        self.request_id = 1
        self.uri = request_rec.uri
        self.auth_token = None
        self.username = ''
        self.passwd = ''

        if request_rec.username and request_rec.password:
            req_pw = request_rec.password
            cipher = AESCipher(settings.AES_KEY)
            decrypted_password = cipher.decrypt(req_pw)

            self.passwd = decrypted_password
            self.username = request_rec.username


    def _request(self, params):
        """
        Grafana API にリクエストを送信する
        id は現行特に必要ないため単純にインクリメントした数値を代入している。
        [引数]
          params: Grafana API のメソッドのパラメータ
          auth_token: Grafana API の認証トークン
        [戻り値]
          dict型に変換したレスポンス
        """

        data = params
        basic_auth = None
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        if self.auth_token:
            headers['Authorization'] = 'Bearer %s' % (self.auth_token)

        elif self.username and self.passwd:
            basic_auth = requests.auth.HTTPBasicAuth(self.username, self.passwd)


        try:
            if data:
                response = requests.post(self.uri, data=data, headers=headers, auth=basic_auth)

            else:
                response = requests.get(self.uri, headers=headers, auth=basic_auth)

            self.request_id += 1

        except requests.exceptions.ConnectTimeout:
            # "リトライについて検討すべき"
            logger.system_log('LOSM30026', 'Grafana', 'Grafana Timeout error.')
            raise

        except requests.exceptions.RequestException:
            logger.system_log('LOSM30026', 'Grafana', 'RequestException error.')
            raise

        if response.status_code != 200:
            # 200以外は関知しない 上位で処理
            raise Exception('Failed to get response. sts_code=%s, reason=%s' % (response.status_code, getattr(response, 'text', '')))

        try:
            resp = json.loads(response.text)

        except Exception as e:
            logger.system_log('LOSM30026', 'Grafana', 'JSON decode error. response=%s' % response)
            logger.logic_log('LOSI00005', traceback.format_exc())
            raise

        return resp

    def get_active_triggers(self, last_change_since=None, now=None):
        """
        現在発生している障害を全て取得する。
        発生しているhostidとhost名も要求する。
        [戻り値]
        result: 発生中の障害情報
        """

        params = {}

        try:
            response = self._request(params)
        except Exception as e:
            raise

        if self._has_error(response):
            logger.system_log('LOSM30026', 'Grafana', 'GetResponse error.')
            raise Exception('response error')


        return response


    def logout(self):
        """
        ログアウトを行う。
        成功した場合レスポンスの'result'キーの値がTrueになる。
        [戻り値]
        bool
        """
        try:
            response = self._request('user.logout', [])
        except:
            raise

        return response


    def _has_error(self, response):
        if response != None:
            return True if 'error' in response else False
        else:
            return True


if __name__ == '__main__':
    GrafanaAdapter = GrafanaAdapter(
                grafana_disp_name = 'a',
                uri              = 'http://10.197.18.217:3000/',
                username         = 'admin',
                password         = '90ecc336d6200b1389eb49c4b557ee42892345c2f727453ae82c96e6de94098e',
                match_evtime     = '',
                match_instance   = '',
                rule_type_id     = '1',
                last_update_user = 'admin'
            )

    api = GrafanaApi(GrafanaAdapter)
    his_lastchange = 0
    response = api.get_active_triggers('2021-01-01T00:00:00.000Z','2021-03-01T00:00:00.000Z')

    pprint.pprint(response)

    # ログアウト
    #result = api.logout()


