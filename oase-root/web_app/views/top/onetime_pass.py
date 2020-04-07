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
    ワンタイムパスワード発行画面コントローラ

"""

import json
import re
import traceback
import hashlib
import pytz
import datetime

from django.http import HttpResponse
from django.http import HttpResponseServerError
from django.db import transaction
from django.conf import settings

from libs.commonlibs.oase_logger import OaseLogger
from libs.commonlibs.common import Common

from libs.webcommonlibs.decorator import *
from libs.webcommonlibs.password  import RandomPassword
from libs.webcommonlibs.oase_mail import *

from web_app.models.models import System
from web_app.models.models import User
from web_app.templatetags.common import get_message

logger = OaseLogger.get_instance() # ロガー初期化

#@check_allowed_ad(settings.LOGIN_REDIRECT_URL)
def onetime_pass_exec(request):
    """
    [メソッド概要]
      ワンタイムパスワード発行処理
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    ##################################################
    # requestデータ構造チェック
    ##################################################
    json_str = request.POST.get('user_info', None)

    if json_str == None:
        msg = get_message('MOSJA32009')
        logger.user_log('LOSM17011', request=request)
        return HttpResponseServerError(msg)

    data = json.loads(json_str)

    if not 'user_info' in data and \
        not 'loginId' in data['user_info'] and \
        not 'mailAddr' in data['user_info'] :
        msg = get_message('MOSJA32009')
        logger.user_log('LOSM17011', request=request)
        return HttpResponseServerError(msg)

    # request内容
    error_flag = False
    error_msg = {}
    user = {}
    password = ''
    ttl_hour = ''

    try:
        with transaction.atomic():
            ##################################################
            # 入力データチェック
            ##################################################
            login_id = data['user_info']['loginId']
            mail_address = data['user_info']['mailAddr']
            user, error_flag, error_msg = _validate(request, login_id, mail_address)

            ##################################################
            # ランダムパスワード生成
            ##################################################
            if error_flag == False:
                ttl_hour = int(System.objects.get(config_id='INITIAL_PASS_VALID_PERIOD').value)

                # ランダムパスワード生成
                password = RandomPassword().get_password()
                update_time = datetime.datetime.now(pytz.timezone('UTC'))

                user.password = Common.oase_hash(password)
                user.last_update_user = user.user_name
                user.last_update_timestamp = update_time
                user.password_last_modified = update_time
                password_expire = None
                if ttl_hour == 0:
                    # datetime supportで日時がずれoverflowするため9000年とした
                    password_expire = datetime.datetime.strptime('9000-12-31 23:59:59', '%Y-%m-%d %H:%M:%S')
                else:
                    password_expire = update_time + datetime.timedelta(hours=ttl_hour)
                user.password_expire = password_expire
                user.save()

    except User.DoesNotExist:
        error_flag = True
        error_msg['loginId'] = get_message('MOSJA32031')
        logger.user_log('LOSM17014', login_id, request=request)

    except Exception as e:
        error_flag = True
        logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
        error_msg['db'] = get_message('MOSJA32019') + str('\n') + str(e.args)

    ##################################################
    # ユーザにワンタイムパスワードをメールで通知
    ##################################################

    # 署名用URL生成
    req_protcol = request.scheme
    req_host    = request.get_host()
    login_url   = reverse('web_app:top:login')
    inquiry_url = reverse('web_app:top:inquiry')
    login_url   = '%s://%s%s' % (req_protcol, req_host, login_url)
    inquiry_url = '%s://%s%s' % (req_protcol, req_host, inquiry_url)

    if error_flag == False:
        smtp = OASEMailSMTP()
        user_mail = OASEMailOnetimePasswd(
            mail_address, mail_address, user.user_name, password, ttl_hour, inquiry_url, login_url
        )

        send_result = smtp.send_mail(user_mail)
        if send_result:
            send_result = get_message(send_result)
            error_flag = True
            error_msg['mail'] = send_result
            logger.logic_log('LOSE17000', send_result, request=request)

    # 結果レスポンス
    response_data = {}
    response_data['status'] = 'success' if error_flag == False else 'failure'
    response_data['error_msg'] = error_msg

    response_json = json.dumps(response_data)
    logger.logic_log('LOSI00002', response_data['status'], request=request)

    return HttpResponse(response_json, content_type="application/json")

################################################
def _validate(request, login_id, mail_address):
    """
    [メソッド概要]
      入力データチェック
    """
    user = {}
    error_msg = {}
    error_flag = False

    if not login_id:
        error_flag = True
        error_msg['loginId'] = get_message('MOSJA00003')
        logger.user_log('LOSM17012', 'login_id', request=request)

    if not mail_address:
        error_flag = True
        error_msg['mailAddr'] = get_message('MOSJA00003')
        logger.user_log('LOSM17012', 'mail_address', request=request)

    # loginIdでuser情報取得(Userの対象レコードをロック)
    if error_flag == False:
        user = User.objects.select_for_update().get(login_id=login_id)

        # mailAddrが違う場合
        if user.mail_address != mail_address:
            error_flag = True
            error_msg['mailAddr'] = get_message('MOSJA32032')
            logger.user_log('LOSM17013', user.mail_address,
                            mail_address, request=request)

    return user, error_flag, error_msg
