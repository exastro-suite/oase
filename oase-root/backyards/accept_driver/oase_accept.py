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

"""


import os
import sys
import django
import json
import pytz
import datetime
import traceback
import ast
import pika
import time
import threading
import copy
from time import sleep

# --------------------------------
# 環境変数取得
# --------------------------------
try:
    oase_root_dir = os.environ['OASE_ROOT_DIR']
    run_interval = os.environ['RUN_INTERVAL']
    python_module = os.environ['PYTHON_MODULE']
    log_level = os.environ['LOG_LEVEL']
except Exception as e:
    oase_root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../')
    run_interval = "10"
    python_module = "/usr/bin/python3"
    log_level = "NORMAL"

# --------------------------------
# パス追加
# --------------------------------
sys.path.append(oase_root_dir)

# --------------------------------
# django読み込み
# --------------------------------
os.environ['DJANGO_SETTINGS_MODULE'] = 'confs.frameworkconfs.settings'
django.setup()

from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from libs.backyardlibs.backyard_common import disconnect
from libs.commonlibs.oase_logger import OaseLogger
logger = OaseLogger.get_instance() # ロガー初期化

from web_app.models.models import User, EventsRequest, RuleType
from web_app.serializers.events_request import EventsRequestSerializer
from libs.commonlibs import define as defs
from libs.commonlibs.rabbitmq import RabbitMQ

from libs.webcommonlibs.events_request import EventsRequestCommon
from libs.webcommonlibs.common import TimeConversion
from libs.webcommonlibs.oase_exception import OASEError


# MAX件数
MAX_COUNT = 100

THREAD_LOCK = threading.Lock()


################################################################
def check_key_error(trace_id, json_str):
    """
    [メソッド概要]
      イベントリクエストの各キーの正常性チェック
      ※try の中で呼び出すこと
    """

    err_code = EventsRequestCommon.check_events_request_key(json_str)
    if err_code != EventsRequestCommon.REQUEST_OK:
        err_keyname = ''
        if err_code == EventsRequestCommon.REQUEST_ERR_RULETYPE_KEY:
            err_keyname = EventsRequestCommon.KEY_RULETYPE

        elif err_code == EventsRequestCommon.REQUEST_ERR_REQTYPE_KEY:
            err_keyname = EventsRequestCommon.KEY_REQTYPE

        elif err_code == EventsRequestCommon.REQUEST_ERR_DATETIME_KEY:
            err_keyname = EventsRequestCommon.KEY_EVENTTIME

        elif err_code == EventsRequestCommon.REQUEST_ERR_EVINFO_KEY:
            err_keyname = EventsRequestCommon.KEY_EVENTINFO

        logger.user_log('LOSM22001', err_keyname, trace_id)
        raise OASEError('', 'LOSM22004', log_params=[json_str, ])


################################################
def check_evinfo_error(trace_id, json_str, ruletypeid, evinfo_length):
    """
    [メソッド概要]
      イベントリクエストのイベント情報の正常性チェック
      ※try の中で呼び出すこと
    """

    # イベント情報のチェック
    err_code = EventsRequestCommon.check_events_request_len(
        json_str, evinfo_length)
    if err_code != EventsRequestCommon.REQUEST_OK:
        if err_code == EventsRequestCommon.REQUEST_ERR_EVINFO_TYPE:
            logger.user_log('LOSM22002', trace_id,
                            ruletypeid, 0, evinfo_length)
            raise OASEError('', 'LOSM22004', log_params=[json_str, ])

        elif err_code == EventsRequestCommon.REQUEST_ERR_EVINFO_LENGTH:
            logger.user_log('LOSM22002', trace_id, ruletypeid, len(
                json_str[EventsRequestCommon.KEY_EVENTINFO]), evinfo_length)
            raise OASEError('', 'LOSM22004', log_params=[json_str, ])

        raise OASEError('', 'LOSM22004', log_params=[json_str, ])


################################################
def make_evinfo_str(json_str):
    """
    [メソッド概要]
      DB登録用にイベント情報を文字列に整形
    """
    evinfo_str = ''

    for v in json_str[EventsRequestCommon.KEY_EVENTINFO]:
        if evinfo_str:
            evinfo_str += ','

        if not isinstance(v, list):
            evinfo_str += '"%s"' % (v)

        else:
            temp_val = '['
            for i, val in enumerate(v):
                if i > 0:
                    temp_val += ','

                temp_val += '"%s"' % (val)

            temp_val += ']'
            evinfo_str += '%s' % (temp_val)

    return evinfo_str


################################################
def data_list(body, user, rule_type_id_list, label_count_list):
    """ 
    [メソッド概要]
      DB登録するデータをリストにする。
    """

    data_object = None

    now = datetime.datetime.now(pytz.timezone('UTC'))
    evinfo_length = 0
    ruletypeid = 0
    msg = ''
    event_dt = '----/--/-- --:--:--'

    disconnect()

    # フォーマットのチェック
    json_str = json.loads(body.decode('UTF-8'))

    trace_id = json_str[EventsRequestCommon.KEY_TRACEID]
    logger.system_log('LOSI22000', trace_id)

    # キーのチェック
    check_key_error(trace_id, json_str)

    # ルール情報の取得
    reqtypeid = json_str[EventsRequestCommon.KEY_REQTYPE]
    ruletablename = json_str[EventsRequestCommon.KEY_RULETYPE]

    rule_type_id_list.update({ruletablename: 0})
    label_count_list.update({ruletablename: 0})

    rset = RuleType.objects.filter(rule_type_name=ruletablename).values(
        'rule_type_id', 'rule_type_name', 'label_count')
    for rs in rset:
        rule_type_id_list.update(
            {rs['rule_type_name']: rs['rule_type_id']})
        label_count_list.update(
            {rs['rule_type_name']: rs['label_count']})

    if ruletablename in rule_type_id_list:
        ruletypeid = rule_type_id_list[ruletablename]
        evinfo_length = label_count_list[ruletablename]

    # イベント情報のチェック
    check_evinfo_error(trace_id, json_str, ruletypeid, evinfo_length)

    # DB登録用に整形
    time_zone = settings.TIME_ZONE
    evinfo_str = json.dumps(json_str[EventsRequestCommon.KEY_EVENTINFO], ensure_ascii=False)
    evinfo_str = '{"EVENT_INFO":%s}' % (evinfo_str)
    event_dt = json_str[EventsRequestCommon.KEY_EVENTTIME]
    event_dt = TimeConversion.get_time_conversion_utc(
        event_dt, time_zone)

    json_data = {
        'trace_id': trace_id,
        'request_type_id': reqtypeid,
        'rule_type_id': ruletypeid,
        'request_reception_time': now,
        'request_user': 'OASE Web User',
        'request_server': 'OASE Web',
        'event_to_time': event_dt,
        'event_info': evinfo_str,
        'status': defs.UNPROCESS,
        'status_update_id': '',
        'retry_cnt': 0,
        'last_update_timestamp': now,
        'last_update_user': user.user_name,
    }

    # バリデーションチェック
    oters = EventsRequestSerializer(data=json_data)
    result_valid = oters.is_valid()

    # バリデーションエラー
    if result_valid == False:
        msg = '%s' % oters.errors
        logger.user_log('LOSM22003', trace_id, msg)
        raise OASEError('', 'LOSM22004', log_params=[json_str, ])

    # 正常の場合はリスト登録
    else:
        data_object = EventsRequest(
            trace_id=trace_id,
            request_type_id=reqtypeid,
            rule_type_id=ruletypeid,
            request_reception_time=now,
            request_user='OASE Web User',
            request_server='OASE Web',
            event_to_time=event_dt,
            event_info=evinfo_str,
            status=defs.UNPROCESS,
            status_update_id='',
            retry_cnt=0,
            last_update_timestamp=now,
            last_update_user=user.user_name
        ).save(force_insert=True)



################################################
def bulk_create():
    """
    [メソッド概要]
      EventsRequestテーブルに登録
    """

    global data_obj_list
    global thread_flg

    try:
        thread_flg = False
        with THREAD_LOCK:
            data_obj_len = len(data_obj_list)

            if data_obj_len <= 0:
                return

            # 登録用配列にコピー
            tmp_data = copy.deepcopy(data_obj_list)
            data_obj_list = []

        # 一括DB登録
        EventsRequest.objects.bulk_create(tmp_data)

        # 登録用配列初期化
        tmp_data = []

    except Exception as e:
        logger.system_log('LOSM22005', traceback.format_exc())


################################################
def load_ruletype():
    """
    [メソッド概要]
      ルール種別管理テーブル情報を読み込む
    """

    rule_type_id_list = {}
    label_count_list = {}

    ruletype = list(RuleType.objects.all().values(
        'rule_type_id', 'rule_type_name', 'label_count'))
    for rt in ruletype:

        rule_type_id = {}
        label_count = {}

        rule_type_id[rt['rule_type_name']] = rt['rule_type_id']
        label_count[rt['rule_type_name']] = rt['label_count']
        rule_type_id_list.update(rule_type_id)
        label_count_list.update(label_count)

    return rule_type_id_list, label_count_list


################################################
if __name__ == '__main__':

    # 初期化
    loop_count = 0

    # データ読み込み
    rule_type_id_list, label_count_list = load_ruletype()

    # 起動時設定情報取得
    user = User.objects.get(user_id=1)
    accept_settings = RabbitMQ.settings()

    # rabbitMQ接続
    channel, connection = RabbitMQ.connect(accept_settings)

    # キューに接続
    channel.queue_declare(queue=accept_settings['queuename'], durable=True)

    # ループ
    for method_frame, properties, body in channel.consume(accept_settings['queuename']):

        if method_frame:
            try:
                data_list(body, user, rule_type_id_list, label_count_list)
                channel.basic_ack(method_frame.delivery_tag)

            except json.JSONDecodeError:
                channel.basic_ack(method_frame.delivery_tag)
                logger.user_log('LOSM22000', body)

            except OASEError as e:
                channel.basic_ack(method_frame.delivery_tag)
                if e.log_id:
                    if e.arg_list and isinstance(e.arg_list, list):
                        logger.system_log(e.log_id, *(e.arg_list))
                    else:
                        logger.system_log(e.log_id)

            except Exception as e:
                logger.system_log('LOSM22004', traceback.format_exc())
                sys.exit(1)


    # 念のためclose処理
    channel.close()
    connection.close()
