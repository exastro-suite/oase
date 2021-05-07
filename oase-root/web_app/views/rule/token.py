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
 トークンページのデータ処理

"""

import sys
import copy
import pytz
import datetime
import hashlib
import json
import traceback
import re
import socket
import urllib.parse

from django.http import HttpResponse, Http404
from django.shortcuts import render,redirect
from django.db.models import Q, Max
from django.db import transaction
from django.views.decorators.http import require_POST
from django.urls import reverse
from libs.commonlibs import define as defs
from libs.commonlibs.oase_logger import OaseLogger
from libs.webcommonlibs.decorator import *
from libs.webcommonlibs.oase_exception import OASEError
from web_app.models.models import TokenInfo, TokenPermission, Group, AccessPermission
from web_app.templatetags.common import get_message
from importlib import import_module
from web_app.views.event.event import SigToken

logger = OaseLogger.get_instance() # ロガー初期化

MENU_ID = 2141001009

@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_EVERY)
def index(request):
    """
    [メソッド概要]
    """

    permission_type = request.user_config.get_menu_auth_type(MENU_ID)
    hasUpdateAuthority = True if permission_type == defs.ALLOWED_MENTENANCE else False
    token_list = []
    token_id_list = []
    group_list = []

    logger.logic_log('LOSI00001', 'None', request=request)

    try:
        user_groups = request.user_config.group_id_list
        token_id_list = TokenPermission.objects.filter(
            group_id__in=user_groups, permission_type_id='1').values_list('token_id', flat=True).order_by('token_id')

        token = TokenInfo.objects.filter(
            token_id__in=token_id_list).order_by('token_id')

        for t in token:
            token_info = {
                'token_id'              : t.token_id,
                'token_data'            : t.token_data,
                'use_start_time'        : t.use_start_time,
                'use_end_time'          : t.use_end_time,
                'last_update_timestamp' : t.last_update_timestamp,
                'last_update_user'      : t.last_update_user,
            }
            token_list.append(token_info)

        group_list = Group.objects.filter(
            group_id__in=user_groups).values('group_id', 'group_name').order_by('group_id')

    except Exception as e:
        logger.logic_log('LOSI00005', traceback.format_exc(), request=request)

    data = {
        'token_list'         : token_list,
        'hasUpdateAuthority' : hasUpdateAuthority,
        'group_list'         : group_list,
    }

    data.update(request.user_config.get_templates_data(request))

    logger.logic_log('LOSI00002', 'token_count: %s' % (len(token_list)), request=request)

    return render(request,'rule/token.html',data)


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_EVERY)
def delete(request, token_id):
    """
    [メソッド概要]
    指定されたトークン情報の削除
    """

    logger.logic_log('LOSI00001', 'delete token request. token_id=%s' % (token_id), request=request)

    response_data = {
        'status'       : 'success',
        'redirect_url' : reverse('web_app:rule:token'),
    }

    try:
        with transaction.atomic():
            # ロック
            tkn = TokenInfo.objects.select_for_update().get(token_id=token_id)

            # 権限チェック
            perm_flg = TokenPermission.objects.filter(
                token_id           = token_id,
                group_id__in       = request.user_config.group_id_list,
                permission_type_id = defs.ALLOWED_MENTENANCE
            ).exists()

            if not perm_flg:
                raise OASEError('MOSJA37016', 'LOSI37000', log_params=[token_id, request.user_config.group_id_list])

            # トークン情報、トークングループ情報の削除
            tkn.delete()
            TokenPermission.objects.filter(token_id=token_id).delete()

    except TokenInfo.DoesNotExist:
        logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
        response_data['status'] = 'failure'
        response_data['error_msg'] = get_message('MOSJA37017', request.user.get_lang_mode())

    except OASEError as e:
        if e.log_id:
            if e.arg_list and isinstance(e.arg_list, list):
                logger.logic_log(e.log_id, *(e.arg_list), request=request)
            else:
                logger.logic_log(e.log_id, request=request)

        if e.msg_id:
            if e.arg_dict and isinstance(e.arg_dict, dict):
                msg = get_message(e.msg_id, request.user.get_lang_mode(), **(e.arg_dict))
            else:
                msg = get_message(e.msg_id, request.user.get_lang_mode())

        response_data['status'] = 'failure'
        response_data['error_msg'] = msg

    except Exception as e:
        logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
        response_data['status'] = 'failure'
        response_data['error_msg'] = get_message('MOSJA37015', request.user.get_lang_mode())


    logger.logic_log('LOSI00002', 'result:%s, token_id=%s' % (response_data['status'], token_id), request=request)

    # 削除成功時はシグナル送信して、トークンをリロード
    if response_data['status'] == 'success':
        cls = SigToken()
        cls.send_sig()

    # 応答
    response_json = json.dumps(response_data)
    return HttpResponse(response_json, content_type="application/json")


