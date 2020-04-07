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
import pytz
import datetime
import multiprocessing
import socket
import subprocess
import traceback
import ast
import pika
import memcache

from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from retry import retry

from web_app.models.models import User, EventsRequest, DataObject, RuleType
from web_app.serializers.events_request import EventsRequestSerializer
from libs.commonlibs import define as defs
from libs.commonlibs.oase_logger import OaseLogger
from libs.commonlibs.rabbitmq import RabbitMQ
from libs.webcommonlibs.events_request import EventsRequestCommon
from libs.webcommonlibs.common import TimeConversion

logger = OaseLogger.get_instance() # ロガー初期化

# 設定情報読み込み
_mq_settings = None

# RabbitMQ接続
_channel    = None
_connection = None
_properties = None

# ルール種別キャッシュ
ACCEPT_RULE_KEY = 'accept.rule'
RULE_TYPE_KEY   = 'type_id'
LABEL_CNT_KEY   = 'label_count'

mem_client = memcache.Client([settings.CACHES['default']['LOCATION'],])



mq_lock = multiprocessing.Lock()
################################################
@csrf_exempt
def eventsrequest(request):
    """
    [メソッド概要]
      テストリクエスト実行時のリクエストを処理する
    """

    now       = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id  = EventsRequestCommon.generate_trace_id()
    resp_json = {}
    result    = False
    msg       = ''

    logger.system_log('LOSI13001', trace_id)

    try:
        #########################################
        # リクエストのチェック
        #########################################
        # メソッドのチェック
        if not request or request.method == 'GET':
            msg = 'Invalid request. Must be POST. Not GET.'
            logger.user_log('LOSM13001', trace_id)
            raise Exception(msg)

        # フォーマットのチェック
        try:
            json_str = json.loads(request.body.decode('UTF-8'))
        except json.JSONDecodeError:
            msg = 'Invalid request format. Must be JSON.'
            logger.user_log('LOSM13005', trace_id)
            raise Exception(msg)

        if json_str[EventsRequestCommon.KEY_REQTYPE] in [1, '1']:  # 1:プロダクション環境

            # プロダクション環境
            json_str['traceid'] = trace_id
            json_str = json.dumps(json_str)

            # 初回の設定読込で落ちるのめんどくさいのでここに置いとく
            _rabbitMQ_conf()

            # RabbitMQへ送信
            mq_lock.acquire()
            _produce(json_str)
            mq_lock.release()

            result = True
            msg = 'Accept request.'

        elif json_str[EventsRequestCommon.KEY_REQTYPE] in [2, '2']:  # 2:ステージング環境

            # ステージング環境
            user = User.objects.get(user_id=1)

            # キーのチェック
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

                msg = 'Invalid request.'
                logger.user_log('LOSM13002', err_keyname, trace_id)
                raise Exception(msg)

            # ルール情報の取得
            reqtypeid     = json_str[EventsRequestCommon.KEY_REQTYPE]
            ruletablename = json_str[EventsRequestCommon.KEY_RULETYPE]
            ruletypeid    = RuleType.objects.get(rule_table_name=ruletablename).rule_type_id
            evinfo_length = DataObject.objects.filter(rule_type_id=ruletypeid).values('label').distinct().count()

            # イベント情報のチェック
            err_code = EventsRequestCommon.check_events_request_len(json_str, evinfo_length)
            if err_code != EventsRequestCommon.REQUEST_OK:
                if err_code == EventsRequestCommon.REQUEST_ERR_EVINFO_TYPE:
                    msg = 'Unmatch, Number of event information elements.'
                    logger.user_log('LOSM13003', trace_id, ruletypeid, 0, evinfo_length)
                    raise Exception(msg)

                elif err_code == EventsRequestCommon.REQUEST_ERR_EVINFO_LENGTH:
                    msg = 'Unmatch, Number of event information elements.'
                    logger.user_log('LOSM13003', trace_id, ruletypeid, len(json_str[EventsRequestCommon.KEY_EVENTINFO]), evinfo_length)
                    raise Exception(msg)

                raise Exception()


            #########################################
            # リクエストをDBに保存
            #########################################
            # DB登録用に成形
            evinfo_str = ''
            rset = DataObject.objects.filter(rule_type_id=ruletypeid).order_by('data_object_id')

            label_list                     = []
            conditional_expression_id_list = []

            for a in rset:
                if a.label not in label_list:
                    label_list.append(a.label)
                    conditional_expression_id_list.append(a.conditional_expression_id)

            for rs, v in zip(conditional_expression_id_list, json_str[EventsRequestCommon.KEY_EVENTINFO]):
                if evinfo_str:
                    evinfo_str += ','

                # 条件式がリストの場合
                if rs in (13, 14):
                    if not isinstance(v, list):
                        evinfo_str += '%s' % (v)

                    else:
                        temp_val = '['
                        for i, val in enumerate(v):
                            if i > 0:
                                temp_val += ','

                            temp_val += '"%s"' % (val)

                        temp_val += ']'
                        evinfo_str += '%s' % (temp_val)

                # 条件式がリスト以外の場合
                else:
                    evinfo_str += '"%s"' % (v)

            evinfo_str = '{"EVENT_INFO":[%s]}' % (evinfo_str)
            event_dt   = json_str[EventsRequestCommon.KEY_EVENTTIME]
            event_dt   = TimeConversion.get_time_conversion_utc(event_dt, 'Asia/Tokyo')

            json_data = {
                'trace_id'               : trace_id,
                'request_type_id'        : reqtypeid,
                'rule_type_id'           : ruletypeid,
                'request_reception_time' : now,
                'request_user'           : 'OASE Web User',
                'request_server'         : 'OASE Web',
                'event_to_time'          : event_dt,
                'event_info'             : evinfo_str,
                'status'                 : defs.UNPROCESS,
                'status_update_id'       : '',
                'retry_cnt'              : 0,
                'last_update_timestamp'  : now,
                'last_update_user'       : user.user_name,
            }

            # バリデーションチェック
            oters = EventsRequestSerializer(data=json_data)
            result_valid = oters.is_valid()

            # バリデーションエラー
            if result_valid == False:
                msg = '%s' % oters.errors
                logger.user_log('LOSM13004', trace_id, msg)

            # 正常の場合はDB保存
            else:
                oters.save()
                result = True
                msg = 'Accept request.'

        else: # 不明なリクエスト種別

            msg = 'Invalid request type.'
            logger.user_log('LOSM13023', trace_id, json_str[EventsRequestCommon.KEY_REQTYPE])


    except Exception as e:
        if not msg:
            msg = 'Unexpected error.'

        logger.system_log('LOSM13013', trace_id, traceback.format_exc())


    # レスポンス情報の作成
    resp_json = {
        'result' : result,
        'msg'      : msg,
        'trace_id' : trace_id,
    }

    resp_json = json.dumps(resp_json, ensure_ascii=False)

    logger.system_log('LOSI13002', trace_id, result, msg)

    # 応答
    return HttpResponse(resp_json)


################################################
@csrf_exempt
def bulk_eventsrequest(request):
    """
    [メソッド概要]
      一括用のリクエストを処理する
    """

    resp_json         = {}
    result            = False
    rule_type_id_list = {}
    label_count_list  = {}

    logger.system_log('LOSI13023')

    try:
        #########################################
        # リクエストのチェック
        #########################################
        # メソッドのチェック
        if not request or request.method == 'GET':
            logger.system_log('LOSM13025')
            raise Exception()

        # フォーマットのチェック
        try:
            json_str = json.loads(request.body.decode('UTF-8'))
        except json.JSONDecodeError:
            logger.system_log('LOSM13026')
            raise Exception()

        ruletype_info = mem_client.get(ACCEPT_RULE_KEY)
        if ruletype_info is not None:
            rule_type_id_list = ruletype_info[RULE_TYPE_KEY]
            label_count_list  = ruletype_info[LABEL_CNT_KEY]

        for data in json_str['request']:

            # キーのチェック
            err_code = EventsRequestCommon.check_events_request_key(data)
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

                logger.system_log('LOSM13027', err_keyname)
                raise Exception()

            # ルール情報の取得
            reqtypeid  = data[EventsRequestCommon.KEY_REQTYPE]
            ruletablename = data[EventsRequestCommon.KEY_RULETYPE]

            if ruletablename not in rule_type_id_list:
                rule_type_id_list.update({ruletablename:0})
                label_count_list.update({ruletablename:0})

                rset = RuleType.objects.filter(rule_table_name=ruletablename).values('rule_type_id', 'rule_table_name', 'label_count')
                for rs in rset:
                    rule_type_id_list.update({rs['rule_table_name']:rs['rule_type_id']})
                    label_count_list.update({rs['rule_table_name']:rs['label_count']})

                ruletype_info = {RULE_TYPE_KEY:rule_type_id_list, LABEL_CNT_KEY:label_count_list}
                mem_client.set(ACCEPT_RULE_KEY, ruletype_info)

            if ruletablename in rule_type_id_list:
                ruletypeid    = rule_type_id_list[ruletablename]
                evinfo_length = label_count_list[ruletablename]

            # イベント情報のチェック
            err_code = EventsRequestCommon.check_events_request_len(data, evinfo_length)
            if err_code != EventsRequestCommon.REQUEST_OK:
                if err_code == EventsRequestCommon.REQUEST_ERR_EVINFO_TYPE:
                    logger.system_log('LOSM13028', ruletypeid, 0, evinfo_length)
                    raise Exception()

                elif err_code == EventsRequestCommon.REQUEST_ERR_EVINFO_LENGTH:
                    logger.system_log('LOSM13028', ruletypeid, len(data[EventsRequestCommon.KEY_EVENTINFO]), evinfo_length)
                    raise Exception()

                raise Exception()

            trace_id  = EventsRequestCommon.generate_trace_id()
            data['traceid'] = trace_id
            data = json.dumps(data)

            _rabbitMQ_conf()

            # RabbitMQへ送信
            mq_lock.acquire()
            _produce(data)
            mq_lock.release()

        result = True

    except Exception as e:
        logger.system_log('LOSM13029', traceback.format_exc())


    # レスポンス情報の作成
    resp_json = {
        'result' : result,
    }

    resp_json = json.dumps(resp_json, ensure_ascii=False)

    logger.system_log('LOSI13024', result)

    # 応答
    return HttpResponse(resp_json)


@retry(tries=3, delay=0.5)
def _produce(json_str):
    """
    [概要]
        RabbitMQへの接続
        retryデコレータにより、接続エラーが発生した場合はdelay秒間隔でtries回数、再接続を試みる
        tries回数試行しても繋がらなかった場合は呼び元のexceptに飛ぶ
    """
    try:
        global _channel
        global _connection
        global _mq_settings
        global _properties

        _channel.queue_bind(exchange='amq.direct', queue=_mq_settings['queuename'], routing_key=_mq_settings['queuename'])

        _channel.basic_publish(exchange='amq.direct',
            routing_key=_mq_settings['queuename'],
            body=json_str,
            properties=_properties)

    except pika.exceptions.AMQPConnectionError:
        _channel = None
        _rabbitMQ_conf()

        #continue
        raise Exception

    except Exception as e:
        raise


def _rabbitMQ_conf():
    """
    [概要]
        RabbitMQ接続に関しての設定を行う
    """
    global _channel
    global _connection
    global _mq_settings
    global _properties

    try:
        if _channel is None:
            # 設定情報読み込み
            _mq_settings = RabbitMQ.settings()

            # RabbitMQ接続
            _channel, _connection = RabbitMQ.connect(_mq_settings)

            # キューに接続
            _channel.queue_declare(queue=_mq_settings['queuename'], durable=True)

            _properties = pika.BasicProperties(
                content_type='application/json',
                content_encoding='utf-8',
                delivery_mode=2)

    except Exception as e:
        logger.system_log('LOSM13024', traceback.format_exc())

