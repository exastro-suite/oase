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
  ログイン／ログアウト処理

[引数]


[戻り値]


"""


import traceback
import pytz
import datetime
import requests
import json
import urllib.parse
import base64
import ast
import secrets

from datetime import timedelta

from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth import login  as auth_login
from django.contrib.auth import logout as auth_logout
from django.conf import settings
from django.urls import reverse
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.db import transaction

from libs.commonlibs import define as defs
from libs.commonlibs.oase_logger import OaseLogger
from libs.middleware.oase_auth import *
from libs.webcommonlibs.oase_exception import *
from libs.webcommonlibs.decorator import *
from web_app.models.models import User, SsoInfo
from .login import _get_value_session_timeout

logger = OaseLogger.get_instance() # ロガー初期化


################################################
# アクセストークン取得要求
################################################
def _token_request_ptrn1(request, sso, code):
    """
    [メソッド概要]
      アクセストークン取得リクエスト形式その1
    [引数]
      request : コールバックURLのリクエスト情報
      sso     : SsoInfoオブジェクトのインスタンス
      code    : コールバック時受信の認証プロバイダーcode
    """

    headers  = {'Content-Type': 'application/json'}
    req_data = {
        'code'          : code,
        'client_id'     : sso.clientid,
        'client_secret' : sso.clientsecret,
    }

    logger.logic_log('LOSI10015', sso.accesstokenuri, req_data, request=request)

    resp = requests.post(
         sso.accesstokenuri,
         data=json.dumps(req_data),
         headers=headers
    )

    logger.logic_log(
        'LOSI10017',
        resp.status_code,
        'reason=%s, txt=%s' % (resp.reason, resp.text),
        request=request
    )

    return resp


################################################
def _token_request_ptrn2(request, sso, code):
    """
    [メソッド概要]
      アクセストークン取得リクエスト形式その2
    [引数]
      request : コールバックURLのリクエスト情報
      sso     : SsoInfoオブジェクトのインスタンス
      code    : コールバック時受信の認証プロバイダーcode
    """

    basic_info   = '%s:%s' % (sso.clientid, sso.clientsecret)
    basic_info   = base64.b64encode(basic_info.encode())
    redirect_uri = '%s://%s%s' % (request.scheme, request.get_host(), reverse('web_app:top:sso_callback'))

    req_data = {
        'code'          : code,
        'client_id'     : sso.clientid,
        'client_secret' : sso.clientsecret,
        'redirect_uri'  : redirect_uri,
        'grant_type'    : 'authorization_code',
    }

    logger.logic_log('LOSI10015', sso.accesstokenuri, req_data, request=request)

    resp = requests.post(
         sso.accesstokenuri,
         data=req_data
    )

    logger.logic_log(
        'LOSI10017',
        resp.status_code,
        'reason=%s, txt=%s' % (resp.reason, resp.text),
        request=request
    )

    return resp


################################################
# ユーザー情報取得要求
################################################
def _user_info_request_ptrn1(request, sso, access_token):
    """
    [メソッド概要]
      ユーザー情報取得リクエスト形式その1
    [引数]
      request      : コールバックURLのリクエスト情報
      sso          : SsoInfoオブジェクトのインスタンス
      access_token : 認証プロバイダー払い出しトークン
    """

    headers   = {'authorization': 'token %s' % (access_token)}
    req_data  = {'access_token' : access_token}

    logger.logic_log('LOSI10016', sso.resourceowneruri, access_token, request=request)

    resp = requests.get(sso.resourceowneruri, headers=headers, params=req_data)

    logger.logic_log(
        'LOSI10017',
        resp.status_code,
        'reason=%s, txt=%s' % (resp.reason, resp.text),
        request=request
    )

    return resp


################################################
def _user_info_request_ptrn2(request, sso, access_token):
    """
    [メソッド概要]
      ユーザー情報取得リクエスト形式その2
    [引数]
      request      : コールバックURLのリクエスト情報
      sso          : SsoInfoオブジェクトのインスタンス
      access_token : 認証プロバイダー払い出しトークン
    """

    headers   = {'authorization': 'Bearer %s' % (access_token)}
    req_data  = {'schema':'openid'}

    logger.logic_log('LOSI10016', sso.resourceowneruri, access_token, request=request)

    resp = requests.get(sso.resourceowneruri, headers=headers, params=req_data)

    logger.logic_log(
        'LOSI10017',
        resp.status_code,
        'reason=%s, txt=%s' % (resp.reason, resp.text),
        request=request
    )

    return resp


################################################
# view関数
################################################
def auth(request, sso_id):
    """
    [メソッド概要]
      view関数 : SSO認証リクエスト
    [引数]
      sso_id   : SSO認証ID
    """

    logger.logic_log('LOSI00001', 'sso_id=%s' % (sso_id), request=request)

    req_data    = {}
    resp_params = None

    try:
        sso_id = int(sso_id)

        # DBからSSO情報取得
        sso = SsoInfo.objects.get(sso_id=sso_id)


        # SSO情報チェック
        check_keys = ['authorizationuri', 'clientid']
        for k in check_keys:
            if not (hasattr(sso, k) and getattr(sso, k, None)):
                logger.user_log('LOSM10003', k, request=request)
                raise OASELoginError('MOSJA10044')


        # 認証プロバイダーへ認証要求
        state        = secrets.token_hex(16)
        auth_uri     = sso.authorizationuri
        redirect_uri = '%s://%s%s' % (request.scheme, request.get_host(), reverse('web_app:top:sso_callback'))

        req_data = {
            'client_id'     : sso.clientid,
            'redirect_uri'  : redirect_uri,
            'response_type' : 'code',
            'state'         : state,
        }

        if sso.scope:
            req_data['scope'] =  urllib.parse.quote(sso.scope)


        logger.logic_log('LOSI10014', auth_uri, req_data, request=request)

        for k, v in req_data.items():
            if '?' not in auth_uri:
                auth_uri = '%s?%s=%s' % (auth_uri, k, v)

            else:
                auth_uri = '%s&%s=%s' % (auth_uri, k, v)

        request.session['sso_id'] = str(sso_id)
        request.session['state']  = state
        return HttpResponseRedirect(auth_uri)


    except OASELoginError as e:
        request.session['msg'] = e.msg_id

    except SsoInfo.DoesNotExist:
        request.session['msg'] = 'MOSJA10044'
        logger.user_log('LOSM10004', sso_id, request=request)

    except Exception as e:
        request.session['msg'] = 'MOSJA10010'
        logger.logic_log('LOSM00001', '%s' % (traceback.format_exc()), request=request)


    return redirect(settings.LOGIN_URL)


################################################
def callback(request):
    """
    [メソッド概要]
      view関数 : SSO認証プロバイダーからのコールバック
    """

    code        = request.GET.get('code',  '')
    state_query = request.GET.get('state', '')
    sso_id      = request.session['sso_id']

    logger.logic_log('LOSI00001', 'sso_id=%s, code=%s' % (sso_id, code), request=request)

    uid      = 0
    next_url = settings.LOGIN_URL

    try:
        sso_id = int(sso_id)
        state  = request.session.pop('state')

        if state_query and state != state_query:
            logger.system_log('LOSM10007', sso_id, state_query, state)
            raise OASELoginError('MOSJA10010')

        ########################################
        # SSO情報取得
        ########################################
        # DBからSSO情報取得
        sso = SsoInfo.objects.get(sso_id=sso_id)


        # SSO情報チェック
        check_keys = ['clientid', 'clientsecret', 'accesstokenuri', 'resourceowneruri', 'id', 'name']
        for k in check_keys:
            if not (hasattr(sso, k) and getattr(sso, k, None)):
                logger.user_log('LOSM10003', k, request=request)
                raise OASELoginError('MOSJA10044')


        ########################################
        # アクセストークン取得
        ########################################
        # プロバイダーからトークン取得要求
        func_list = [
            _token_request_ptrn1,
            _token_request_ptrn2,
        ]

        for f in func_list:
            resp = f(request, sso, code)
            if resp.status_code == 200:
                break

        else:
            logger.user_log('LOSM10005', sso_id, request=request)
            raise OASELoginError('MOSJA10010')


        try:
            resp_params = ast.literal_eval(resp.text)

        except Exception as e:
            resp_params = {k: v for k, v in [p.split('=') for p in resp.text.split('&')]}

        access_token = resp_params['access_token']


        ########################################
        # ユーザー情報取得
        ########################################
        # プロバイダーからユーザー情報取得要求
        func_list = [
            _user_info_request_ptrn1,
            _user_info_request_ptrn2,
        ]

        for f in func_list:
            resp_data = f(request, sso, access_token)
            if resp.status_code == 200:
                break

        else:
            logger.user_log('LOSM10006', sso_id, request=request)
            raise OASELoginError('MOSJA10010')


        user_info = resp_data.json()

        user_id   = str(user_info.get(sso.id))
        user_name = str(user_info.get(sso.name))
        email     = user_info.get(sso.email) if sso.email else ''
        image_url = user_info.get(sso.imageurl) if sso.imageurl else ''


        ########################################
        # ユーザー情報保存
        ########################################
        # プロバイダーから取得したユーザー情報をカラムの制限に合わせる
        user_id   = user_id[:256]
        user_name = user_name[:64]
        email     = email[:256] if email else ''

        user_id   = '%s-%s' % (user_id, str(sso_id).zfill(11))

        # ユーザー情報をOASE側に保存
        with transaction.atomic():

            # OASE側に既に存在する場合、ユーザー情報を更新
            oase_user_info = User.objects.filter(login_id=user_id, login_id__contains=user_id, sso_id=sso_id)
            if len(oase_user_info) > 0:
                oase_user_info = oase_user_info[0]
                oase_user_info.user_name    = user_name
                oase_user_info.mail_address = email if email else ''
                oase_user_info.disuse_flag  = str(defs.ENABLE)
                oase_user_info.save(force_update=True)

            # OASE側に存在しない場合、ユーザー情報を登録
            else:
                oase_user_info = User(
                    login_id              = user_id,
                    user_name             = user_name,
                    password              = '',
                    mail_address          = email if email else '',
                    lang_mode_id          = defs.LANG_MODE.JP,
                    disp_mode_id          = defs.DISP_MODE.DEFAULT,
                    sso_id                = sso_id,
                    password_count        = 0,
                    password_expire       = datetime.datetime.strptime('9000-12-31 23:59:59', '%Y-%m-%d %H:%M:%S'),
                    last_update_user      = user_name,
                    last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
                )
                oase_user_info.save(force_insert=True)

            # 所属グループがなければ、デフォルトを割り当て
            rcnt = UserGroup.objects.filter(user_id=oase_user_info.user_id).count()
            if rcnt <= 0:
                UserGroup(
                    user_id          = oase_user_info.user_id,
                    group_id         = defs.GROUP_DEFINE.GROUP_ID_SSO,
                    last_update_user = user_name,
                ).save(force_insert=True)


        # セッション情報作成
        backend = SSOClientAuthBackend()
        auth_login(request, oase_user_info, backend=backend.full_name)
        timeout_val = _get_value_session_timeout()
        now = datetime.datetime.now(pytz.timezone('UTC'))
        request.session['cookie_age']         = (now + timedelta(minutes=timeout_val)).strftime('%Y-%m-%d %H:%M:%S')
        request.session[LANGUAGE_SESSION_KEY] = oase_user_info.get_lang_mode().lower()
        request.session['sso_id']             = str(sso_id)
        request.session['sso_name']           = sso.provider_name
        request.session['sso_imageurl']       = image_url

        uid      = oase_user_info.user_id
        next_url = settings.LOGIN_REDIRECT_URL


    except OASELoginError as e:
        request.session['msg'] = e.msg_id

    except SsoInfo.DoesNotExist:
        request.session['msg'] = 'MOSJA10044'
        logger.user_log('LOSM10004', sso_id, request=request)

    except Exception as e:
        request.session['msg'] = 'MOSJA10010'
        logger.logic_log('LOSI00001', '%s' % (traceback.format_exc()), request=request)


    logger.logic_log('LOSI00002', 'uid=%s' % (uid), request=request)

    return redirect(next_url)


