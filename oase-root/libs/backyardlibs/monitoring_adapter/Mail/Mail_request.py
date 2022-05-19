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
import pika
import multiprocessing
from urllib3.exceptions import InsecureRequestWarning

from django.conf import settings
from django.urls import reverse

from libs.commonlibs.oase_logger import OaseLogger
from libs.backyardlibs.monitoring_adapter.oase_monitoring_adapter_common_libs import _produce
from libs.backyardlibs.monitoring_adapter.oase_monitoring_adapter_common_libs import _rabbitMQ_conf
from libs.webcommonlibs.events_request import EventsRequestCommon

urllib3.disable_warnings(InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context
logger = OaseLogger.get_instance()

# 設定情報読み込み
_mq_settings = None

# RabbitMQ接続
_channel    = None
_connection = None
_properties = None

mq_lock = multiprocessing.Lock()


def send_request(request_data_dic):
    """
    [メソッド概要]
      RabbitMQに整形済データをリクエストに投げる
    """

    logger.logic_log('LOSI00001', 'request_data_dic: %s' % len(request_data_dic))

    result = True
    msg = ''
    trace_id_list = []
    data_count = 0

    try:

        data_count = len(request_data_dic['request'])
        # リクエストデータの有無確認
        if data_count <= 0:
            result = False
            # ログ追加
            logger.system_log('LOSM30011')
            raise

        trace_id_list = EventsRequestCommon.generate_trace_id(req=data_count)
        if len(trace_id_list) != data_count:
            result = False
            # ログ追加
            logger.system_log('LOSM30028')
            raise

        for i, data in enumerate(request_data_dic['request']):

            data['traceid'] = trace_id_list[i]
            data = json.dumps(data)

            _rabbitMQ_conf()

            # RabbitMQへ送信
            mq_lock.acquire()
            _produce(data)
            mq_lock.release()

    except Exception as e:
        if result:
            result = False
            # ログ追加
            logger.system_log('LOSM30010', traceback.format_exc())

    logger.logic_log('LOSI00002', 'result: %s' % (result))

    return result
