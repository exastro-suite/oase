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
    ServiceNowアクションモジュール

"""

import os
import sys
import traceback
import requests
import json
import ast

# oase-rootまでのバスを取得
my_path = os.path.dirname(os.path.abspath(__file__))
tmp_path = my_path.split('oase-root')
# ログファイルのパスを生成
root_dir_path = tmp_path[0] + 'oase-root'
sys.path.append(root_dir_path)

from django.conf import settings

# ロガー初期化
from libs.commonlibs.oase_logger import OaseLogger
logger = OaseLogger.get_instance()


from libs.commonlibs.define import *
from libs.commonlibs.aes_cipher import AESCipher
from libs.backyardlibs.action_driver.common.driver_core import DriverCore
from web_app.models.models import EventsRequest, RuleType


class ServiceNow1Core(DriverCore):
    """
    [クラス概要]
        ServiceNowアクションクラス
    """

    def __init__(self, TraceID):
        """
        [概要]
            コンストラクタ
        """

        self.TraceID = TraceID
        self.target_table = 'incident'


    def set_target_table(self, target_table):
        """
        [概要]
            リクエスト送信先テーブルの設定
        """

        self.target_table = target_table


    def send_post_request(self, url, user, passwd, data, headers=None, proxies=None):
        """
        [メソッド概要]
            POSTリクエスト送信
        """

        logger.logic_log('LOSI00001', 'trace_id=%s, url=%s' % (self.TraceID, url))

        resp = None

        try:
            resp = requests.post(
                url, auth=(user, passwd), data=data,
                headers=headers, proxies=proxies,
                timeout=30, verify=False
            )

            if resp.status_code != 201:
                logger.logic_log(
                    'LOSI00002',
                    'Error. trace_id=%s, code=%s' % (self.TraceID, resp.status_code)
                )
                return None

        except Exception as ex:
            logger.logic_log('LOSM01500', self.TraceID, traceback.format_exc())
            return None


        logger.logic_log('LOSI00002', 'Success. trace_id=%s' % (self.TraceID))
        return resp


    def send_put_request(self, url, user, passwd, data, headers=None, proxies=None):
        """
        [メソッド概要]
            PUTリクエスト送信
        """

        logger.logic_log('LOSI00001', 'trace_id=%s, url=%s' % (self.TraceID, url))

        try:
            resp = requests.put(
                url, auth=(user, passwd), data=data,
                headers=headers, proxies=proxies,
                timeout=30, verify=False
            )

            if resp.status_code not in [200, 201]:
                logger.logic_log(
                    'LOSI00002',
                    'Error. trace_id=%s, code=%s' % (self.TraceID, resp.status_code)
                )
                return False

        except Exception as ex:
            logger.logic_log('LOSM01502', 'PUT', self.TraceID, traceback.format_exc())
            return False


        logger.logic_log('LOSI00002', 'Success. trace_id=%s' % (self.TraceID))
        return True


    def send_patch_request(self, url, user, passwd, data, headers=None, proxies=None):
        """
        [メソッド概要]
            PATCHリクエスト送信
        """

        logger.logic_log('LOSI00001', 'trace_id=%s, url=%s' % (self.TraceID, url))

        try:
            resp = requests.patch(
                url, auth=(user, passwd), data=data,
                headers=headers, proxies=proxies,
                timeout=30, verify=False
            )

            if resp.status_code not in [200]:
                logger.logic_log(
                    'LOSI00002',
                    'Error. trace_id=%s, code=%s' % (self.TraceID, resp.status_code)
                )
                return False

        except Exception as ex:
            logger.logic_log('LOSM01502', 'PUT', self.TraceID, traceback.format_exc())
            return False

        logger.logic_log('LOSI00002', 'Success. trace_id=%s' % (self.TraceID))
        return True


    def send_get_request(self, url, user, passwd, headers=None, proxies=None):
        """
        [メソッド概要]
            GETリクエスト送信
        """

        logger.logic_log('LOSI00001', 'trace_id=%s, url=%s' % (self.TraceID, url))

        try:
            resp = requests.get(
                url, auth=(user, passwd),
                headers=headers, proxies=proxies,
                timeout=30, verify=False
            )

            if resp.status_code not in [200]:
                logger.logic_log(
                    'LOSI00002',
                    'Error. trace_id=%s, code=%s' % (self.TraceID, resp.status_code)
                )
                return False

        except Exception as ex:
            logger.logic_log('LOSM01502', 'GET', self.TraceID, traceback.format_exc())
            return False

        logger.logic_log('LOSI00002', 'Success. trace_id=%s' % (self.TraceID))
        return resp


    def create_incident(self, drv):

        """
        [メソッド概要]
            インシデント登録リクエスト送信
        """

        logger.logic_log(
            'LOSI00001',
            'trace_id=%s, driver_id=%s' % (self.TraceID, drv.servicenow_driver_id)
        )

        result = False
        sys_id = None

        try:
            cipher = AESCipher(settings.AES_KEY)
            er = EventsRequest.objects.get(trace_id=self.TraceID)
            dname = RuleType.objects.get(rule_type_id=er.rule_type_id).rule_type_name

            # リクエスト送信先
            url = "{}://{}:{}/api/now/table/{}".format(
                drv.protocol, drv.hostname, drv.port, self.target_table
            )

            # ヘッダー情報
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }

            # プロクシ設定
            if drv.proxy:
                proxies = {
                    'http' : drv.proxy,
                    'https': drv.proxy,
                }

            # 認証情報
            user = drv.username
            password = cipher.decrypt(drv.password)

            # リクエストボディ
            ary_data = {}
            ary_data['short_description'] = 'OASE Event Notify'
            ary_data['description'] = {
                'trace_id'      : self.TraceID,
                'decisiontable' : dname,
                'eventdatetime' : er.event_to_time,
                'eventinfo'     : er.event_info
            }
            str_para_json_encoded = json.dumps(ary_data, default=str)

            # リクエスト送信
            result = self.send_post_request(
                url,
                user, password,
                str_para_json_encoded.encode('utf-8'),
                headers=headers, proxies=proxies
            )

            # POSTが正常ならば sys_id を応答情報から取得
            if result:
                resp = ast.literal_eval(result.text)

                if resp and 'result' in resp and 'sys_id' in resp['result']:
                    sys_id = resp['result']['sys_id']

                result = result.status_code

        except Exception as ex:
            logger.logic_log('LOSM01500', self.TraceID, traceback.format_exc())
            return False, None


        logger.logic_log('LOSI00002', 'result=%s, trace_id=%s, sys_id=%s' % (result, self.TraceID, sys_id))
        return result, sys_id


    def modify_incident(self, drv, sys_id, ary_data):

        """
        [メソッド概要]
            インシデント更新リクエスト送信
        """

        logger.logic_log(
            'LOSI00001',
            'trace_id=%s, driver_id=%s, sys_id=%s, data=%s' % (self.TraceID, drv.servicenow_driver_id, sys_id, ary_data)
        )

        result = False

        try:
            cipher = AESCipher(settings.AES_KEY)

            # リクエスト送信先
            url = "{}://{}:{}/api/now/table/{}/{}".format(
                drv.protocol, drv.hostname, drv.port, self.target_table, sys_id
            )

            # ヘッダー情報
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }

            # プロクシ設定
            if drv.proxy:
                proxies = {
                    'http' : drv.proxy,
                    'https': drv.proxy,
                }

            # 認証情報
            user = drv.username
            password = cipher.decrypt(drv.password)

            # リクエストボディ
            str_para_json_encoded = json.dumps(ary_data, default=str)

            # リクエスト送信
            result = self.send_put_request(
                url,
                user, password,
                str_para_json_encoded.encode('utf-8'),
                headers=headers, proxies=proxies
            )

        except Exception as ex:
            logger.logic_log('LOSM01502', 'PUT', self.TraceID, traceback.format_exc())
            return False


        logger.logic_log('LOSI00002', 'result=%s, trace_id=%s, sys_id=%s' % (result, self.TraceID, sys_id))
        return result


    def get_incident(self, drv, sys_id):

        """
        [メソッド概要]
            インシデント取得リクエスト送信
        """

        logger.logic_log(
            'LOSI00001',
            'trace_id=%s, driver_id=%s, sys_id=%s' % (self.TraceID, drv.servicenow_driver_id, sys_id)
        )

        result = False

        try:
            cipher = AESCipher(settings.AES_KEY)

            # リクエスト送信先
            url = "{}://{}:{}/api/now/table/{}/{}?sysparm_display_value=all".format(
                drv.protocol, drv.hostname, drv.port, self.target_table, sys_id
            )

            # ヘッダー情報
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }

            # プロクシ設定
            if drv.proxy:
                proxies = {
                    'http' : drv.proxy,
                    'https': drv.proxy,
                }

            # 認証情報
            user = drv.username
            password = cipher.decrypt(drv.password)

            # リクエスト送信
            result = self.send_get_request(
                url,
                user, password,
                headers=headers, proxies=proxies
            )

        except Exception as ex:
            logger.logic_log('LOSM01502', 'GET', self.TraceID, traceback.format_exc())
            return False


        logger.logic_log('LOSI00002', 'result=%s, trace_id=%s, sys_id=%s' % (result, self.TraceID, sys_id))
        return result


    def modify_workflow(self, drv, sys_id, ary_data):

        """
        [メソッド概要]
            ワークフロースケジュール更新リクエスト送信
        """

        logger.logic_log(
            'LOSI00001',
            'trace_id=%s, driver_id=%s, sys_id=%s, data=%s' % (self.TraceID, drv.servicenow_driver_id, sys_id, ary_data)
        )

        result = False

        try:
            cipher = AESCipher(settings.AES_KEY)

            # リクエスト送信先
            url = "{}://{}:{}/api/now/table/{}/{}".format(
                drv.protocol, drv.hostname, drv.port, self.target_table, sys_id
            )

            # ヘッダー情報
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }

            # プロクシ設定
            if drv.proxy:
                proxies = {
                    'http' : drv.proxy,
                    'https': drv.proxy,
                }

            # 認証情報
            user = drv.username
            password = cipher.decrypt(drv.password)

            # リクエストボディ
            str_para_json_encoded = json.dumps(ary_data, default=str)

            # リクエスト送信
            result = self.send_patch_request(
                url,
                user, password,
                str_para_json_encoded.encode('utf-8'),
                headers=headers, proxies=proxies
            )

        except Exception as ex:
            logger.logic_log('LOSM01502', 'PATCH', self.TraceID, traceback.format_exc())
            return False

        logger.logic_log('LOSI00002', 'result=%s, trace_id=%s, sys_id=%s' % (result, self.TraceID, sys_id))
        return result

