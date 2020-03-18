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
  運用基盤連携処理

[引数]
  HTTPリクエスト

[戻り値]
  HTTPレスポンス
"""

import json
import traceback
import requests
import urllib3
import ssl
from urllib3.exceptions import InsecureRequestWarning

from django.conf import settings
from django.urls import reverse

from libs.commonlibs.oase_logger import OaseLogger

urllib3.disable_warnings(InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context
logger = OaseLogger.get_instance()


def send_request(request_data_dic):
    """
    [メソッド概要]
      一括用に整形済データをリクエストに投げる
    """

    logger.logic_log('LOSI00001', 'request_data_dic: %s' % len(request_data_dic))

    result = True
    msg = ''

    try:

        # リクエストデータの有無確認
        if len(request_data_dic) <= 0:
            result = False
            logger.system_log('LOSM25001')
            raise

        # jsonの文字列形式ヘ
        json_str = json.dumps(request_data_dic)

        # リクエストを投げる
        url = settings.HOST_NAME + reverse('web_app:event:bulk_eventsrequest')

        r = requests.post(
            url,
            headers={'content-type': 'application/json'},
            data=json_str.encode('utf-8'),
            verify=False
        )

        # レスポンスからデータを取得
        try:
            r_content = json.loads(r.content.decode('utf-8'))
        except json.JSONDecodeError:
            result = False
            logger.system_log('LOSM25002', traceback.format_exc())
            raise

        # リクエストの実行中に失敗した場合
        if not r_content["result"]:
            result = False
            msg = r_content["msg"]
            logger.system_log('LOSM25003', 'result: %s, msg: %s' % (result, msg))

    except Exception as e:
        if result:
            result = False
            logger.system_log('LOSM25004', traceback.format_exc())

    logger.logic_log('LOSI00002', 'result: %s' % (result))

    return result
