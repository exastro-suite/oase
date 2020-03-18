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
    ロック画面のコントローラ

"""

import json
import traceback

from django.http import HttpResponse, Http404
from django.shortcuts import render,redirect
from django.db import transaction
from django.views.decorators.http import require_POST

from libs.commonlibs import define as defs
from libs.commonlibs.oase_logger import OaseLogger

from libs.webcommonlibs.decorator import *
from libs.webcommonlibs.oase_mail import *
from libs.webcommonlibs.sys_config import *
from web_app.models.models import User, AccessPermission
from web_app.templatetags.common import get_message

logger = OaseLogger.get_instance() # ロガー初期化

def has_permission_user_auth(request):
    """
    [メソッド概要]
    ユーザの権限を確認
    権限なしならFalseを返す。
    """
    user_id = request.user.pk

    # administrator
    if user_id == 1:
        logger.logic_log('LOSI18000', request=request)
        return True

    else:
        notification_type = int(System.objects.get(config_id="NOTIFICATION_DESTINATION_TYPE").value)

        # administrator + ユーザ権限を持つユーザ
        if notification_type == 1:
            if user_id in get_userid_at_user_auth():
                logger.logic_log('LOSI18001', request=request)
                return True


        # administrator + 指定したloginID
        elif notification_type == 2:
            if user_id in get_lock_auth_user():
                logger.logic_log('LOSI18002', request=request)
                return True

    logger.logic_log('LOSM18000', request=request)
    return False

def locked_user(request):
    """
    [メソッド概要]
      アカウントロックユーザ一覧表示
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    if not has_permission_user_auth(request):
        return HttpResponseRedirect(reverse('web_app:top:notpermitted'))

    user_list = _get_user_data() 

    data = {
        'user_list'         : user_list,
        'mainmenu_list'     : request.user_config.get_menu_list(),
        'user_name'         : request.user.user_name,
        'account_lock_time' : request.user.account_lock_time,
        'lang_mode'         : request.user.get_lang_mode(),
    }
    
    logger.logic_log('LOSI00002', 'user_list count: %s' % (len(user_list)), request=request)
    return render(request, 'user/locked_user.html', data)

@require_POST
def unlock(request):
    """
    [メソッド概要]
      アカウントロックユーザの解除処理
    """
    error_flag = False
    auth_flag  = True
    json_str = request.POST.get('json_str',None)

    logger.logic_log('LOSI00001', 'json_str: %s' % json_str, request=request)

    dict_json_str = ast.literal_eval(json_str)
    dct = json.dumps(dict_json_str)

    if not has_permission_user_auth(request):
        auth_flag = False

    else:
        try:
            with transaction.atomic():
                User.objects.filter(user_id= str(dict_json_str['unlockInfo'])).update(
                    password_count = 0,
                    account_lock_time = None,
                    account_lock_times = 0,
                    account_lock_flag = False
                )

        except Exception as e:
            error_flag = True

    # 結果レスポンス
    response_data = {
        'redirect_url' : '/oase_web/user/locked_user'
    }

    # 削除権限なし
    if not auth_flag:
        response_data['status'] = 'nopermission'

    # 異常処理
    elif error_flag == True:
        response_data['status'] = 'failure'
        logger.logic_log('LOSM18001', 'json_str: %s, response_data: %s, traceback: %s' % (json_str, response_data, traceback.format_exc()), request=request)
    # 正常処理
    else:
        response_data['status'] = 'success'

    response_json = json.dumps(response_data)

    logger.logic_log('LOSI00002', 'json_str: %s, response_json: %s' % (json_str, response_json), request=request)
    return HttpResponse(response_json, content_type="application/json")



def _get_user_data():
    """
    [メソッド概要]
      データ更新処理
    [引数]
      request :logger.logic_logでuserId sessionIDを表示するために使用する
    [戻り値]
      user_list
    """
    logger.logic_log('LOSI00001', 'None')

    where_info = {
        'pk__gt' : 1,
        'account_lock_flag' : 1
    }
    user_list = User.objects.filter(**where_info) 

    logger.logic_log('LOSI00002', 'user_list: %s' % len(user_list))
    return user_list
