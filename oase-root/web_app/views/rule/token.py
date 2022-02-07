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
import secrets
import ast

from pytz import timezone
from django.http import HttpResponse, Http404
from django.shortcuts import render,redirect
from django.db.models import Q, Max
from django.db import transaction
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.conf import settings
from libs.commonlibs import define as defs
from libs.commonlibs.common import Common
from libs.commonlibs.oase_logger import OaseLogger
from libs.webcommonlibs.decorator import *
from libs.webcommonlibs.oase_exception import OASEError
from libs.webcommonlibs.common import TimeConversion
from web_app.models.models import TokenInfo, TokenPermission, Group, AccessPermission
from web_app.templatetags.common import get_message
from web_app.serializers.unicode_check import UnicodeCheck
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
    token_perm_list = []
    token_perm = {}

    logger.logic_log('LOSI00001', 'None', request=request)

    try:
        user_groups = request.user_config.group_id_list
        token_id_list = TokenPermission.objects.filter(
            group_id__in=user_groups, permission_type_id='1').values_list('token_id', flat=True).order_by('token_id')

        token = TokenInfo.objects.filter(
            token_id__in=token_id_list).order_by('token_id')

        group_list = Group.objects.filter(
            group_id__in=user_groups).values('group_id', 'group_name').order_by('group_id')

        group_info = {}
        for group in group_list:
            group_info[group['group_id']] = group['group_name']

        perm_info = {}
        for t in token:
            perm_info[t.token_id] = []
            for group in group_list:
                perm_info[t.token_id].append(
                    {
                        'group_id'           : group['group_id'],
                        'group_name'         : group_info[group['group_id']],
                        'permission_type_id' : 0,
                    }
                )

        tok_grp_info = {}
        TokPerm_list = TokenPermission.objects.filter().values(
            'token_id', 'group_id', 'permission_type_id').order_by('token_id')

        for tok in TokPerm_list:
            tok_id = tok['token_id']
            grp_id = tok['group_id']
            perm   = tok['permission_type_id']

            if tok_id not in perm_info or grp_id not in group_info:
                continue

            tok_grp_info[(tok_id, grp_id)] = perm

        for tok_id, v_list in perm_info.items():
            for v in v_list:
                grp_id = v['group_id']
                if (tok_id, grp_id) in tok_grp_info:
                    v['permission_type_id'] = tok_grp_info[(tok_id, grp_id)]

        token_perm_list = perm_info

        for t in token:
            token_info = {
                'token_id'              : t.token_id,
                'token_name'            : t.token_name,
                'token_data'            : t.token_data,
                'use_start_time'        : t.use_start_time,
                'use_end_time'          : t.use_end_time,
                'last_update_timestamp' : t.last_update_timestamp,
                'last_update_user'      : t.last_update_user,
                'permission'            : token_perm_list[t.token_id] if t.token_id in token_perm_list else []
            }
            token_list.append(token_info)

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


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_EVERY)
def update(request, token_id):
    """
    [メソッド概要]
    指定されたトークン情報の更新
    """

    logger.logic_log('LOSI00001', 'update token request. token_id=%s' % (token_id), request=request)

    response_data = {
        'status'       : 'success',
        'redirect_url' : reverse('web_app:rule:token'),
    }

    now = datetime.datetime.now(pytz.timezone('UTC'))

    try:
        with transaction.atomic():
            upd_record = request.POST.get('upd_record', "{}")
            upd_record = json.loads(upd_record)
            token_info = upd_record['token_info']

            # 権限チェック
            perm_flg = TokenPermission.objects.filter(
                token_id           = token_id,
                group_id__in       = request.user_config.group_id_list,
                permission_type_id = defs.ALLOWED_MENTENANCE
            ).exists()

            if not perm_flg:
                raise OASEError('MOSJA37028', 'LOSI37001', log_params=[token_id, request.user_config.group_id_list])

            # 権限ありのグループ有無チェック
            perm_count = 0
            for pm in token_info['permission']:
                if pm['permission_type_id'] == '1':
                    perm_count = perm_count + 1

            if perm_count < 1:
                raise OASEError('MOSJA37046', 'LOSI37007', log_params=['update', token_id])

            permission_list_reg = []
            for pm in token_info['permission']:
                if pm['permission_type_id'] != '0' and pm['permission_type_id'] != '1':
                    raise OASEError('MOSJA37034', 'LOSI37002', log_params=[token_id, pm['group_id'], pm['permission_type_id']])

                rcnt = TokenPermission.objects.filter(
                    token_id=token_info['token_id'],
                    group_id=pm['group_id']
                ).count()

                if rcnt > 0:
                    TokenPermission.objects.filter(
                        token_id=token_info['token_id'],
                        group_id=pm['group_id']
                    ).update(
                        permission_type_id = pm['permission_type_id'],
                        last_update_timestamp = now,
                        last_update_user = request.user.user_name
                    )
                else:
                    permission_list_reg.append(
                        TokenPermission(
                            token_id=token_info['token_id'],
                            group_id = pm['group_id'],
                            permission_type_id = pm['permission_type_id'],
                            last_update_timestamp = now,
                            last_update_user = request.user.user_name
                        )
                    )

            if len(permission_list_reg) > 0:
                TokenPermission.objects.bulk_create(permission_list_reg)

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
        response_data['error_msg'] = get_message('MOSJA37027', request.user.get_lang_mode())

    logger.logic_log('LOSI00002', 'result:%s, token_id=%s' % (response_data['status'], token_id), request=request)

    response_json = json.dumps(response_data)
    return HttpResponse(response_json, content_type="application/json")


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_EVERY)
def display(request):
    """
    [メソッド概要]
    トークンの再表示
    """

    logger.logic_log('LOSI00001', 're-display token request.', request=request)

    response_data = {
        'status' : 'failure',
        'msg'    : '',
    }

    try:
        # パラメーター取得
        tkn_id = int(request.POST.get('tkn_id', '0'))
        passwd = request.POST.get('passwd', '')
        passwd = Common.oase_hash(passwd)

        # 権限チェック
        perm_flg = TokenPermission.objects.filter(
            token_id           = tkn_id,
            group_id__in       = request.user_config.group_id_list,
            permission_type_id = defs.ALLOWED_MENTENANCE
        ).exists()

        if not perm_flg:
            raise OASEError('MOSJA37035', 'LOSI37003', log_params=[tkn_id, request.user_config.group_id_list])

        # パラメーターチェック
        if passwd != request.user.password:
            raise OASEError('MOSJA37036', 'LOSI37004', log_params=[tkn_id, ])

        # トークン取得
        tkn = TokenInfo.objects.get(token_id=tkn_id).token_data

        # 応答データ
        response_data['status'] = 'success'
        response_data['msg']    = tkn

    except TokenInfo.DoesNotExist:
        logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
        response_data['status'] = 'failure'
        response_data['msg'] = get_message('MOSJA37017', request.user.get_lang_mode())

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
        response_data['msg'] = msg

    except Exception as e:
        logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
        response_data['status'] = 'failure'
        response_data['msg'] = get_message('MOSJA37037', request.user.get_lang_mode())


    logger.logic_log('LOSI00002', 'result:%s, token_id=%s' % (response_data['status'], tkn_id), request=request)

    # 応答
    response_json = json.dumps(response_data)
    return HttpResponse(response_json, content_type="application/json")


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def create(request):
    """
    [メソッド概要]
      データ更新処理
      POSTリクエストのみ
    """

    logger.logic_log('LOSI00001', 'Create New Token', request=request)

    response_data = {
        'status'       : 'success',
        'redirect_url' : reverse('web_app:rule:token'),
    }

    msg = ''
    error_msg = {
        'token_name' : '',
    }

    emo_chk = UnicodeCheck()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    time_zone  = settings.TIME_ZONE

    # トークン生成
    token_value = secrets.token_urlsafe(24)

    # 要求パラメーター取得
    token_name = request.POST.get('token-name', '')
    end_time   = request.POST.get('token-end', '')
    token_perm = request.POST.get('token-perm', '[]')
    token_perm = ast.literal_eval(token_perm)

    try:
        with transaction.atomic():
            # トークン名入力チェック
            if len(token_name) == 0:
                response_data['status'] = 'failure'
                error_msg['token_name'] += get_message('MOSJA37040', request.user.get_lang_mode()) + '\n'

            # トークン名文字列長チェック
            if len(token_name) > 64:
                response_data['status'] = 'failure'
                error_msg['token_name'] += get_message('MOSJA37043', request.user.get_lang_mode()) + '\n'

            # トークン名禁止文字チェック
            emo_flag = False
            value_list = emo_chk.is_emotion(token_name)
            if len(value_list) > 0:
                emo_flag = True
                response_data['status'] = 'failure'
                error_msg['token_name'] += get_message('MOSJA37044', request.user.get_lang_mode()) + '\n'

            # トークン名重複チェック
            if not emo_flag and TokenInfo.objects.filter(token_name=token_name).exists():
                response_data['status'] = 'failure'
                error_msg['token_name'] += get_message('MOSJA37045', request.user.get_lang_mode()) + '\n'


            # 日時のチェック(有効期限は空欄の場合は期限なし)
            if end_time:
                end_time = TimeConversion.get_time_conversion_utc(
                    end_time, time_zone)
            else:
                end_time = None

            if len(error_msg['token_name']) != 0:
                raise Exception()

            # 権限チェック
            permission_list_reg = []
            for pm in token_perm:
                if pm['permission_type_id'] not in ['0', '1']:
                    raise OASEError('MOSJA37039', 'LOSI37006', log_params=[pm['group_id'], pm['permission_type_id']])

            # DB保存
            token_info = TokenInfo(
                token_name            = token_name,
                token_data            = token_value,
                use_start_time        = now,
                use_end_time          = end_time,
                last_update_timestamp = now,
                last_update_user      = request.user.user_name
            )
            token_info.save(force_insert=True)

            permission_list_reg = []
            for pm in token_perm:
                permission_list_reg.append(
                    TokenPermission(
                        token_id              = token_info.token_id,
                        group_id              = pm['group_id'],
                        permission_type_id    = pm['permission_type_id'],
                        last_update_timestamp = now,
                        last_update_user      = request.user.user_name
                    )
                )

            if len(permission_list_reg) > 0:
                TokenPermission.objects.bulk_create(permission_list_reg)

            response_data['status'] = 'success'
            response_data['redirect_url'] = '/oase_web/rule/token'
            response_data['token'] = token_value


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
        response_data['msg'] = msg

    except Exception as e:
        # 異常処理
        logger.system_log('LOSI00005', traceback.format_exc(), request=request)
        response_data['status'] = 'failure'
        response_data['error_msg'] = error_msg

    logger.logic_log('LOSI00002', 'status: %s' % (response_data['status']), request=request)

    # 作成成功時はシグナル送信して、トークンをリロード
    if response_data['status'] == 'success':
        cls = SigToken()
        cls.send_sig()

    response_json = json.dumps(response_data)
    return HttpResponse(response_json, content_type="application/json")

