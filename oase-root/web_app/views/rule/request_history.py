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
  リクエスト履歴の表示処理

[引数]
  HTTPリクエスト

[戻り値]
  HTTPレスポンス

"""

import os
import traceback
import json
import pytz
import datetime
import urllib.parse
import ast
from importlib import import_module

from django.shortcuts             import render, redirect
from django.http                  import HttpResponse
from django.db                    import transaction
from django.views.decorators.http import require_POST

from libs.commonlibs              import define as defs
from libs.webcommonlibs.decorator import *
from libs.webcommonlibs.common    import TimeConversion
from libs.webcommonlibs.oase_exception import OASEError
from libs.commonlibs.oase_logger  import OaseLogger
from web_app.models.models        import EventsRequest, RuleType

from web_app.templatetags.common import get_message


MENU_ID = 2141001008
#ロガー初期化
logger = OaseLogger.get_instance()


################################################
@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_EVERY)
def index(request):
    """
    [メソッド概要]
    リクエスト履歴画面の一覧表示
    """
    logger.logic_log('LOSI00001', 'none', request=request)
    msg = ''
    lang = request.user.get_lang_mode()

    try:
        # リクエスト履歴画面のルール別アクセス権限を取得
        permission_info = request.user_config.get_rule_auth_type(MENU_ID)

        # アクセス可能なルール種別IDを取得
        rule_ids_view = permission_info[defs.VIEW_ONLY]
        rule_ids_admin = permission_info[defs.ALLOWED_MENTENANCE]
        rule_ids_all = rule_ids_view + rule_ids_admin 

        # リクエストデータを取得
        request_history_list = EventsRequest.objects.filter(rule_type_id__in=rule_ids_all).order_by('-pk') if len(rule_ids_all) > 0 else []

        table_list = []
        for req in request_history_list:
            # アイコン表示用文字列セット
            status = req.status
            if status in defs.REQUEST_HISTORY_STATUS.ICON_INFO:
                req.class_info = defs.REQUEST_HISTORY_STATUS.ICON_INFO[status]
            else:
                req.class_info = {'status':'attention','name':'owf-attention','description':'リクエストエラー'}

            # ルール種別欄
            rules = RuleType.objects.filter(rule_type_id=req.rule_type_id)

            # 削除されているルール種別の場合リクエスト履歴を表示しない
            if not len(rules):
                continue

            rule_name = rules[0].rule_type_name

            # リクエスト種別欄
            request_name = ''
            if req.request_type_id == 1:
                # request_name = "プロダクション"
                request_name =get_message('MOSJA00094', lang, showMsgId=False)
            elif req.request_type_id == 2:
                # request_name = "ステージング"
                request_name =get_message('MOSJA00093', lang, showMsgId=False)

            table_info = {
                'class_info'             : req.class_info,
                'rule_id'                : req.rule_type_id,
                'rule_name'              : rule_name,
                'request_id'             : req.request_type_id,
                'request_name'           : request_name,
                'request_reception_time' : req.request_reception_time,
                'event_info'             : req.event_info,
                'event_to_time'          : req.event_to_time,
                'trace_id'               : req.trace_id
            }
            table_list.append(table_info)

    except Exception as e:
        msg = get_message('MOSJA36000', lang)
        logger.logic_log('LOSM24000', 'traceback: %s' % traceback.format_exc(), request=request)

    data = {
        'message'              : msg,
        'mainmenu_list'        : request.user_config.get_menu_list(), 
        'user_name'            : request.user.user_name,
        'table_list'           : table_list,
        'user_name'            : request.user.user_name,
        'can_update'           : rule_ids_admin,
        'lang_mode'            : lang,
    }

    logger.logic_log('LOSI00002', 'none', request=request)
    return render(request, 'rule/request_history.html', data)
