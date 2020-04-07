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
    パスワード期限切れ時のパスワード変更画面コントローラ

"""

import json
import re
import traceback
import pytz
import datetime

from django.http import HttpResponse
from django.http import HttpResponseServerError
from django.shortcuts import render
from django.db import transaction
from django.conf import settings

from libs.commonlibs.common import Common
from libs.commonlibs.oase_logger import OaseLogger

from libs.webcommonlibs.decorator import *
from web_app.models.models import PasswordHistory
from web_app.models.models import System
from web_app.models.models import User
from web_app.templatetags.common import get_message

logger = OaseLogger.get_instance() # ロガー初期化

@check_allowed_ad(settings.LOGIN_REDIRECT_URL)
def pass_ch_exec(request):
    """
    [メソッド概要]
      パスワード変更処理
    """
    
    logger.logic_log('LOSI00001', 'user_id: %s, session_key: %s' % (request.user.user_id, request.session.session_key))

    # requestデータ構造チェック
    json_str = request.POST.get('user_info', None)

    if json_str == None:
        msg = get_message('MOSJA32009', request.user.get_lang_mode())
        logger.user_log('LOSM17000')
        return HttpResponseServerError(msg)

    data = json.loads(json_str)

    if not 'user_info' in data and \
        not 'oldPw' in data['user_info'] and \
        not 'newPw' in data['user_info'] and \
        not 'newPwConf' in data['user_info'] :
        msg = get_message('MOSJA32009', request.user.get_lang_mode())
        logger.user_log('LOSM17000')
        return HttpResponseServerError(msg)

    uid = request.user.user_id
    
    if not 'loginId' in data['user_info'] and uid == '':
        msg = get_message('MOSJA32009', request.user.get_lang_mode())
        logger.user_log('LOSM17000')
        return HttpResponseServerError(msg)

    error_flag = False
    error_msg  = {}
    

    try:
        with transaction.atomic():

            # request内容チェック
            update_time = datetime.datetime.now(pytz.timezone('UTC'))
            password_generation = 0
            pw_history_list = PasswordHistory.objects.filter(user_id=uid).order_by('last_update_timestamp')

            ##################################################
            # 入力値チェック
            ##################################################
            # Userの対象レコードをロック
            user = User.objects.select_for_update().get(user_id=uid)
            error_msg = _validate(request, data, user)
            
            ##################################################
            # パスワード判定
            ##################################################
            if len(error_msg) <= 0:
                # 同一パスワード設定不可世代数取得
                password_generation = int(System.objects.get(config_id='Pass_generate_manage').value)

            new_password_hash = Common.oase_hash(data['user_info']['newPw'])

            # パスワード履歴テーブルが0以上かつパスワード履歴チェックフラグがTrueの場合、世代数分新パスワードと比較
            if len(pw_history_list) > 0 and user.pass_hist_check_flag:
                for pw_history in pw_history_list:
                    if pw_history.password == new_password_hash:
                        error_msg['newPw'] = get_message('MOSJA32018', request.user.get_lang_mode())
                        logger.user_log('LOSM17008', request=request)

            ##################################################
            # ユーザ情報更新
            ##################################################
            if len(error_msg) <= 0:

                logger.user_log('LOSI17000', uid, request.session.session_key, password_generation, len(pw_history_list))

                user.password = new_password_hash
                user.last_update_user = user.user_name
                user.last_update_timestamp = update_time
                user.password_last_modified = update_time
                user.password_expire = None
                user.save(force_update=True)

                ##################################################
                # パスワード履歴の更新
                ##################################################
                if password_generation > 0:

                    pw_history_list_length = len(pw_history_list)
                    if password_generation <= pw_history_list_length:
                        loop = (pw_history_list_length - password_generation) + 1
                        for i in range(loop):
                            pw_history_list[i].delete()

                    new_pw_history = PasswordHistory(
                        user_id                = user.user_id,
                        password               = new_password_hash,
                        last_update_timestamp  = update_time,
                        last_update_user       = user.user_name,
                    )
                    new_pw_history.save(force_insert=True)

    except User.DoesNotExist:
        error_msg['user'] = get_message('MOSJA32010', request.user.get_lang_mode())
        logger.logic_log('LOSM17001', request=request)

    except System.DoesNotExist:
        error_msg['system'] = get_message('MOSJA32011', request.user.get_lang_mode())
        logger.logic_log('LOSM17007', 'Pass_generate_manage', request=request)

    except Exception as e:
        traceback.print_exc()
        error_msg['db'] = get_message('MOSJA32019', request.user.get_lang_mode()) + str(e.args)
        logger.logic_log('LOSM17009', 'traceback: %s' % (traceback.format_exc()), request=request)


    if len(error_msg) > 0:
        error_flag = True

    # 結果レスポンス
    response_data = {}
    response_data['status'] = 'success' if error_flag == False else 'failure'
    response_data['error_msg'] = error_msg

    response_json = json.dumps(response_data, ensure_ascii=False)
    
    logger.logic_log('LOSI00002', 'user_id: %s, session_key: %s' % (request.user.user_id, request.session.session_key))

    return HttpResponse(response_json, content_type="application/json")

################################################
def _validate(request, data, user):
    """
    [メソッド概要]
      入力チェック
    """

    logger.logic_log('LOSI00001', 'user_id: %s, session_key: %s' % (user.user_id, request.session.session_key))
    error_msg = {}

    if not user:
        error_msg['user'] = get_message('MOSJA32010', request.user.get_lang_mode())
        logger.user_log('LOSM17001', request=request)
        logger.logic_log('LOSI00002', 'user_id: %s, session_key: %s' % (request.user.user_id, request.session.session_key))
        return error_msg

    # old_password_check
    input_old_password = data['user_info']['oldPw']
    if len(input_old_password) == 0:
        error_msg['oldPw'] = get_message('MOSJA32012', request.user.get_lang_mode())
        logger.user_log('LOSM17002', request=request)
    else:
        password_hash = Common.oase_hash(input_old_password)
        if user.password != password_hash:
            error_msg['oldPw'] = get_message('MOSJA32013', request.user.get_lang_mode())
            logger.user_log('LOSM17003', request=request)

    # new_password_check
    new_password = data['user_info']['newPw']
    if len(new_password) == 0:
        error_msg['newPw'] = get_message('MOSJA32014', request.user.get_lang_mode())
        logger.user_log('LOSM17004', request=request)

    else:
        re_obj = re.match(r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!#$%&()*+,-./;<=>?@\[\]^_{}|~]).{8,}$', new_password)
        if not re_obj:
            error_msg['newPw'] = get_message('MOSJA32015', request.user.get_lang_mode())
            logger.user_log('LOSM17005', request=request)

    new_password_conf = data['user_info']['newPwConf']
    if new_password != new_password_conf:
        error_msg['newPwConf'] = get_message('MOSJA32016', request.user.get_lang_mode())
        logger.user_log('LOSM17006', request=request)

    logger.logic_log('LOSI00002', 'user_id: %s, session_key: %s' % (request.user.user_id, request.session.session_key))
    return error_msg
