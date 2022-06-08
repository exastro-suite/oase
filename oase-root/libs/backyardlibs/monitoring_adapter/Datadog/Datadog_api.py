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
Datadog apiを使って現在発生している障害を取得する。


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
from web_app.models.Datadog_monitoring_models import DatadogAdapter

logger = OaseLogger.get_instance() # ロガー初期化


class DatadogApi(object):

    def __init__(self, request_rec):
        """
        Datadog API インスタンスを返す
        [引数]
          request_rec: 対象Datadog監視マスタレコード
        """

        self.request_id      = 1
        self.uri             = request_rec.uri
        self.api_key         = request_rec.api_key
        self.application_key = request_rec.application_key
        self.proxy           = request_rec.proxy


    def _request(self, last_change_since, now):
        """
        Datadog API にリクエストを送信する
        id は現行特に必要ないため単純にインクリメントした数値を代入している。
        [引数]
          params: Datadog API のメソッドのパラメータ
        [戻り値]
          dict型に変換したレスポンス
        """

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'DD-API-KEY': self.api_key,
            'DD-APPLICATION-KEY': self.application_key,
        }

        # プロクシ設定
        if self.proxy:
            proxies = {
                'http' : self.proxy,
                'https': self.proxy,
            }


        start = str(last_change_since)
        start = start.split('.', 1)[0]
        end   = str(now)
        end   = end.split('.', 1)[0]

        uri = self.uri + '?start=' + start + '&end=' + end

        try:
            if self.proxy:
                response = requests.get(uri, headers=headers, proxies=proxies, verify=False)
            else:
                response = requests.get(uri, headers=headers)

            self.request_id += 1

        except requests.exceptions.ConnectTimeout:
           # "リトライについて検討すべき"
            logger.system_log('LOSM38020', 'Datadog', 'Datadog Timeout error.')
            raise

        except requests.exceptions.RequestException:
            logger.system_log('LOSM38020', 'Datadog', 'RequestException error.')
            raise

        logger.system_log('LOSI38004', response.status_code)

        flg = False
        if response.status_code == 403:
           # 認証に失敗した場合はフラグを立てる
            flg = True

        if response.status_code != 200 and response.status_code != 403:
           # 200と403以外は関知しない 上位で処理
            raise Exception('Failed to get response. sts_code=%s, reason=%s' % (response.status_code, getattr(response, 'text', '')))

        try:
            resp = json.loads(response.text)

        except Exception as e:
            logger.system_log('LOSM38020', 'Datadog', 'JSON decode error. response=%s' % response)
            logger.logic_log('LOSI00005', traceback.format_exc())
            raise

        logger.logic_log('LOSI00002', 'None')
        return resp, flg

    def get_active_triggers(self, last_change_since=None, now=None):
        """
        現在発生している障害を全て取得する。
        発生しているhostidとhost名も要求する。
        [戻り値]
        result: 発生中の障害情報
        """

        try:
            response = self._request(last_change_since, now)
        except Exception as e:
            raise

        if self._has_error(response):
            logger.system_log('LOSM38020', 'Datadog', 'GetResponse error.')
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

