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
 SSO設定画面ページのデータ処理

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
from rest_framework import serializers
from libs.commonlibs import define as defs
from libs.commonlibs.oase_logger import OaseLogger
from libs.webcommonlibs.decorator import *
from libs.webcommonlibs.oase_exception import OASEError
from web_app.models.models import SsoInfo
from web_app.templatetags.common import get_message

from web_app.views.forms.sso_info_form import SsoInfoForm
from web_app.views.forms.common_form import DivErrorList

logger = OaseLogger.get_instance() # ロガー初期化

MENU_ID = 2141002008
@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_EVERY)
def index(request):
    """
    [メソッド概要]
    SSO設定画面 一覧参照
    """

    msg = ''
    permission_type = request.user_config.get_menu_auth_type(MENU_ID)
    hasUpdateAuthority = True if permission_type == defs.ALLOWED_MENTENANCE else False

    logger.logic_log('LOSI00001', 'None', request=request)

    try:
        # SSO設定情報取得
        sso_info_list = SsoInfo.objects.all().order_by('pk')

    except:
        msg = get_message('MOSJA28004', request.user.get_lang_mode())
        logger.logic_log('LOSM29000', 'traceback: %s' % traceback.format_exc(), request=request)
        raise Http404

    data = {
        'msg'               : msg,
        'sso_info_list'     : sso_info_list,
        'mainmenu_list'     : request.user_config.get_menu_list(),
        'edit_mode'         : False,
        'hasUpdateAuthority': hasUpdateAuthority,
        'user_name'         : request.user.user_name,
        'lang_mode'         : request.user.get_lang_mode(),
    }

    logger.logic_log('LOSI00002', 'None', request=request)

    return render(request, 'system/sso_info.html', data)


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def modify(request):
    """
    [メソッド概要]
      新規登録
      POSTリクエストのみ
    """
    logger.logic_log('LOSI00001', 'None', request=request)

    msg = ''
    error_flag = False
    error_msg = {}
    error_msg_top = {}
    response_data = {}
    now = datetime.datetime.now(pytz.timezone('UTC'))

    # アクセスチェック
    add_record = request.POST.get('add_record',"{}")
    add_record = json.loads(add_record)

    request_record_check(add_record, request)

    try:
        with transaction.atomic():
            # SSO情報のバリデーションチェック
            info = add_record['sso_info']

            sso_info_data = {
                'provider_name'    : info['provider_name'],
                'auth_type'        : info['auth_type'],
                'logo'             : info['logo'],
                'visible_flag'     : info['visible_flag'],
                'clientid'         : info['clientid'],
                'clientsecret'     : info['clientsecret'],
                'authorizationuri' : info['authorizationuri'],
                'accesstokenuri'   : info['accesstokenuri'],
                'resourceowneruri' : info['resourceowneruri'],
                'scope'            : info['scope'],
                'id'               : info['id'],
                'name'             : info['name'],
                'email'            : info['email'],
                'imageurl'         : info['imageurl'],
                'proxy'            : info['proxy'],
            }

            # 入力チェック
            f = SsoInfoForm(0, sso_info_data, auto_id=False, error_class=DivErrorList)

            # エラーがあればエラーメッセージを作成
            for content, validate_list in f.errors.items():
                content.replace('_', '-')
                error_msg_top[content] = '\n'.join([get_message(v, request.user.get_lang_mode()) for v in validate_list])
            if len(f.errors.items()):
                raise Exception("validate error")

            sso_info = SsoInfo(
                provider_name         = info['provider_name'],
                auth_type             = info['auth_type'],
                logo                  = info['logo'],
                visible_flag          = info['visible_flag'],
                clientid              = info['clientid'],
                clientsecret          = info['clientsecret'],
                authorizationuri      = info['authorizationuri'],
                accesstokenuri        = info['accesstokenuri'],
                resourceowneruri      = info['resourceowneruri'],
                scope                 = info['scope'],
                id                    = info['id'],
                name                  = info['name'],
                email                 = info['email'],
                imageurl              = info['imageurl'],
                proxy                 = info['proxy'],
                last_update_timestamp = now,
                last_update_user      = request.user.user_name
            )
            sso_info.save(force_insert=True)

            response_data['status'] = 'success'
            response_data['redirect_url'] = '/oase_web/system/sso_info'

    except Exception as e:
        # 異常処理
        logger.system_log('LOSI00005', traceback.format_exc(), request=request)
        response_data['status'] = 'failure'
        response_data['error_msg'] = error_msg
        response_data['error_top'] = error_msg_top
        response_data['error_flag'] = error_flag

    logger.logic_log('LOSI00002', 'status: %s' % (response_data['status']), request=request)

    response_json = json.dumps(response_data)
    return HttpResponse(response_json, content_type="application/json")


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def modify_detail(request, sso_id):
    """
    [メソッド概要]
      データ更新処理(詳細画面)
      POSTリクエストのみ
    """
    logger.logic_log('LOSI00001', 'sso_id: %s' % (sso_id), request=request)

    error_msg = {}
    error_msg_top = {}
    response_data = {}

    key_check = {
        'provider_name',
        'auth_type',
        'logo',
        'visible_flag',
        'clientid',
        'clientsecret',
        'authorizationuri',
        'accesstokenuri',
        'resourceowneruri',
        'scope',
        'id',
        'name',
        'email',
        'imageurl',
        'proxy'
    }

    key_data = [
        'provider_name',
        'auth_type',
        'logo',
        'visible_flag',
        'clientid',
        'clientsecret',
        'authorizationuri',
        'accesstokenuri',
        'resourceowneruri',
        'scope',
        'id',
        'name',
        'email',
        'imageurl',
        'proxy'
    ]

    now = datetime.datetime.now(pytz.timezone('UTC'))

    try:
        with transaction.atomic():
            sso_info = SsoInfo.objects.select_for_update().get(sso_id=sso_id)

            # アクセスチェック
            add_record = request.POST.get('add_record', "{}")
            add_record = json.loads(add_record)

            log_msg = 'posted add_record: %s' % (add_record)
            logger.logic_log('LOSI29000', log_msg, request=request)

            if 'sso_info' not in add_record:
                logger.user_log('LOSM29001', 'sso_info', request=request)
                error_msg = get_message('MOSJA28066', request.user.get_lang_mode())
                raise Exception(get_message('MOSJA28066', request.user.get_lang_mode(), showMsgId=False))

            # キーの存在確認
            if not key_check == set(add_record['sso_info'].keys()):
                logger.user_log('LOSM29002', add_record['sso_info'].keys(), key_data, request=request)
                error_msg = get_message('MOSJA28066', request.user.get_lang_mode())
                raise Exception(get_message('MOSJA28066', request.user.get_lang_mode(), showMsgId=False))

            # バリデーションチェック
            info = add_record['sso_info']

            sso_info_data = {
                'provider_name'    : info['provider_name'],
                'auth_type'        : info['auth_type'],
                'logo'             : info['logo'],
                'visible_flag'     : info['visible_flag'],
                'clientid'         : info['clientid'],
                'clientsecret'     : info['clientsecret'],
                'authorizationuri' : info['authorizationuri'],
                'accesstokenuri'   : info['accesstokenuri'],
                'resourceowneruri' : info['resourceowneruri'],
                'scope'            : info['scope'],
                'id'               : info['id'],
                'name'             : info['name'],
                'email'            : info['email'],
                'imageurl'         : info['imageurl'],
                'proxy'            : info['proxy'],
                'last_update_user' : request.user.user_name,
            }

            # 入力チェック
            f = SsoInfoForm(0, sso_info_data, auto_id=False, error_class=DivErrorList)

            # エラーがあればエラーメッセージを作成
            for content, validate_list in f.errors.items():
                error_msg_top[content] = '\n'.join([get_message(v, request.user.get_lang_mode()) for v in validate_list])
            if len(f.errors.items()):
                raise Exception(get_message('MOSJA00005', request.user.get_lang_mode()))

            select_object = SsoInfo.objects.filter(provider_name=info['provider_name'])

            if len(select_object) == 1 and sso_id != select_object[0].sso_id:
                logger.user_log('LOSM29004', info['provider_name'], sso_id, select_object[0].sso_id, request=request)
                error_msg = get_message('MOSJA00005', request.user.get_lang_mode()).replace('\\n', '\n')
                error_msg_top['provider_name'] = get_message('MOSJA28067', request.user.get_lang_mode())
                raise Exception(get_message('MOSJA28050', request.user.get_lang_mode(), showMsgId=False))

            if info['logo'] != "":
                select_object = SsoInfo.objects.filter(provider_name=info['logo'])

                if len(select_object) == 1 and sso_id != select_object[0].sso_id:
                    logger.user_log('LOSM29005', info['logo'], sso_id, select_object[0].sso_id, request=request)
                    error_msg = get_message('MOSJA00005', request.user.get_lang_mode()).replace('\\n', '\n')
                    error_msg_top['logo'] = get_message('MOSJA28068', request.user.get_lang_mode())
                    raise Exception(get_message('MOSJA28053', request.user.get_lang_mode(), showMsgId=False))

            # データ更新
            SsoInfo.objects.filter(sso_id=sso_id).update(
                provider_name         = info['provider_name'],
                auth_type             = int(info['auth_type']),
                logo                  = info['logo'],
                visible_flag          = int(info['visible_flag']),
                clientid              = info['clientid'],
                clientsecret          = info['clientsecret'],
                authorizationuri      = info['authorizationuri'],
                accesstokenuri        = info['accesstokenuri'],
                resourceowneruri      = info['resourceowneruri'],
                scope                 = info['scope'],
                id                    = info['id'],
                name                  = info['name'],
                email                 = info['email'],
                imageurl              = info['imageurl'],
                proxy                 = info['proxy'],
                last_update_timestamp = now,
                last_update_user      = request.user.user_name
            )

            logger.logic_log('LOSI29001', 'None', request=request)

            # 正常処理
            response_data['status'] = 'success'
            response_data['redirect_url'] = '/oase_web/system/sso_info'

    except Exception as e:
        # 異常処理
        if not error_msg:
            tb = sys.exc_info()[2]
            error_msg = '%s' % (e.with_traceback(tb))
            logger.logic_log('LOSI00005', traceback.format_exc(), request=request)

        response_data['status'] = 'failure'
        response_data['error_msg'] = error_msg
        response_data['error_top'] = error_msg_top


    logger.logic_log('LOSI00002', 'status: %s' % (response_data['status']), request=request)

    response_json = json.dumps(response_data)
    return HttpResponse(response_json, content_type="application/json")


def request_record_check(add_record, request):
    """
    [メソッド概要]
      リクエスト情報のチェック
    [引数]
      add_record : 追加レコード
      request    : リクエスト情報
    [戻り値]
      なし
    """

    if 'sso_info' not in add_record:
        # ログID作成
        logger.user_log('LOSM29003', add_record.keys(), ['sso_info'], request=request)
        raise Http404

    # キーの存在確認
    if 'provider_name' not in add_record['sso_info']:
        logger.user_log('LOSM29003', add_record['sso_info'].keys(), [
                        'provider_name'], request=request)
        raise Http404


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def delete_sso(request, sso_id):
    """
    [メソッド概要]
    データ削除処理
    """

    logger.logic_log('LOSI00001', 'ssoid: %s' % (sso_id), request=request)

    response_data = {}

    try:
        with transaction.atomic():

            try:
                SsoInfo.objects.filter(sso_id=sso_id).delete()
            except Exception as e:
                msg = get_message('MOSJA28070', request.user.get_lang_mode())
                logger.system_log('LOSM29006', sso_id, traceback.format_exc())
                raise Exception()

            response_data['status'] = 'success'
            response_data['redirect_url'] = '/oase_web/system/sso_info'

    except Exception as e:
        # 異常処理
        logger.system_log('LOSI00005', traceback.format_exc(), request=request)
        response_data['status'] = 'failure'
        response_data['error_msg'] = msg if msg else get_message('MOSJA28071', request.user.get_lang_mode())

    logger.logic_log('LOSI00002', 'status: %s' % (response_data['status']), request=request)

    response_json = json.dumps(response_data)
    return HttpResponse(response_json, content_type="application/json")

