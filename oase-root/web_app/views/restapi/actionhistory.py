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
  アクション履歴管理データ取得

[引数]
  HTTPリクエスト

[戻り値]
  HTTPレスポンス

"""

import json
import pytz
import datetime
import subprocess
import traceback
import ast

from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from web_app.models.models import ActionHistory, ActionType, DriverType, EventsRequest
from web_app.templatetags.common import get_message
from libs.commonlibs.define import *
from libs.commonlibs.oase_logger import OaseLogger


logger = OaseLogger.get_instance() # ロガー初期化


################################################
@csrf_exempt
def historyrequest(request):
    """
    [メソッド概要]
      アクション履歴管理テーブルのデータ取得リクエストを処理する
    """

    resp_json           = {}
    result              = False
    msg                 = ''
    action_history_list = []
    trace_id            = ''

    logger.system_log('LOSI23000')

    try:
        #########################################
        # リクエストのチェック
        #########################################
        # メソッドのチェック
        if not request or request.method == 'POST':
            msg = 'Invalid request. Must be GET. Not POST.'
            logger.user_log('LOSM23001')
            raise Exception(msg)

        # フォーマットのチェック
        try:
            json_str = json.loads(request.body.decode('UTF-8'))
        except json.JSONDecodeError:
            msg = 'Invalid request format. Must be JSON.'
            logger.user_log('LOSM23002')
            raise Exception(msg)

        trace_id = json_str['traceid']
        objects_list = ActionHistory.objects.filter(trace_id=trace_id).order_by('pk')

        if len(objects_list) > 0:

            for act in objects_list:
                try:
                    driver_type_id = ActionType.objects.get(action_type_id=act.action_type_id).driver_type_id
                    driver_type    = DriverType.objects.get(driver_type_id=driver_type_id)
                except ActionType.DoesNotExist:
                    msg = 'ActionType does not exists.'
                    logger.user_log('LOSM23003', trace_id)
                    raise Exception(msg)
                except DriverType.DoesNotExist:
                    msg = 'DriverType does not exists.'
                    logger.user_log('LOSM23004', trace_id)
                    raise Exception(msg)

                name_version   = driver_type.name + '(ver' + str(driver_type.driver_major_version) + ')'

                action_history                          = {}
                action_history['status']                = get_message(ACTION_HISTORY_STATUS.STATUS_DESCRIPTION[act.status], showMsgId=False)
                action_history['rule_type_name']        = act.rule_type_name
                action_history['rule_name']             = act.rule_name
                action_history['action_type_id']        = name_version
                action_history['last_update_timestamp'] = act.last_update_timestamp.astimezone(pytz.timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M')
                action_history['last_update_user']      = act.last_update_user

                action_history_list.append(action_history)

            result = True
            msg = 'Successful completion.'

            # レスポンス情報の作成
            resp_json = {
                'result'              : result,
                'msg'                 : msg,
                'action_history_list' : action_history_list,
            }

        else:
            try:
                events_request = EventsRequest.objects.get(trace_id=trace_id)
            except EventsRequest.DoesNotExist:
                msg = 'Invalid trace ID'
                logger.user_log('LOSM23005', trace_id)
                raise Exception(msg)

            status = get_message(ACTION_STATUS[events_request.status], showMsgId=False)

            if events_request.request_type_id == PRODUCTION:
                msg = 'Successful completion. (Production environment)'

            elif events_request.request_type_id == STAGING:
                msg = 'Successful completion. (Staging environment)'

            else:
                msg = 'Invalid data.'
                logger.user_log('LOSM23006', trace_id)
                raise Exception(msg)

            result = True

            # レスポンス情報の作成
            resp_json = {
                'result' : result,
                'msg'    : msg,
                'status' : status,
            }

    except Exception as e:
        if not msg:
            msg = 'Unexpected error.'

        logger.system_log('LOSM23007', trace_id, traceback.format_exc())

        # レスポンス情報の作成
        resp_json = {
            'result'              : result,
            'msg'                 : msg,
        }

    resp_json = json.dumps(resp_json, ensure_ascii=False)
    logger.system_log('LOSI23001', trace_id, result, msg)

    # 応答
    return HttpResponse(resp_json)

