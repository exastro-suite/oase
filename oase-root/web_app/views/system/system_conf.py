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
  システム設定ページの表示処理
  また、システム設定ページからのリクエスト受信処理

[引数]
  HTTPリクエスト

[戻り値]
  HTTPレスポンス

"""


from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db import transaction
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.conf import settings

from rest_framework import serializers
from libs.commonlibs import define as defs
from libs.commonlibs.aes_cipher import AESCipher
from libs.commonlibs.oase_logger import OaseLogger
from libs.webcommonlibs.decorator import *

from web_app.serializers.system import SystemSerializer
from web_app.templatetags.common import get_message
from web_app.models.models import System
from web_app.models.models import Group
from web_app.models.models import PasswordHistory
from web_app.models.models import User

import json
import pytz
import datetime
import traceback
import copy
import requests
import ast
import urllib
import urllib.request
import urllib.parse

MENU_ID = '2141002002'
logger = OaseLogger.get_instance()

################################################
@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_EVERY)
def index(request):
    """
    [メソッド概要]
      システム設定ページの一覧画面
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    system_log_list      = []
    system_session_list  = []
    system_password_list = []
    system_actdir_list   = []
    system_targro_list   = []
    output_flag          = 0
    pass_flag            = 0

    permission_type = request.user_config.get_menu_auth_type(MENU_ID)
    edit = True if permission_type == defs.ALLOWED_MENTENANCE else False

    try:
        # システム設定情報取得
        system_list = System.objects.filter(maintenance_flag='1').order_by('item_id')

        # システム設定情報作成
        for s in system_list:

            system_info = {
                'item_id': s.item_id,
                'config_name': s.config_name,
                'category': s.category,
                'config_id': s.config_id,
                'value': s.value,
                'maintenance_flag' : s.maintenance_flag,
            }

            if s.category == "LOG_STORAGE_PERIOD":
                system_log_list.append(system_info)

            elif s.category == "SESSION_TIMEOUT":
                system_session_list.append(system_info)

            elif s.category == "PASSWORD":
                system_password_list.append(system_info)

            elif s.category == "ACTIVE_DIRECTORY":
                system_actdir_list.append(system_info)
                if s.config_id == "TARGET_GROUP_LIST" and s.value:
                    system_targro_list = ast.literal_eval(s.value)

                # パスワード設定表示判定
                if s.config_id == "ADCOLLABORATION" and s.value == '1':
                    output_flag = 1

                    if request.user.user_id not in (1, -2140000000):
                        pass_flag = 1

    except:
        logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
        logger.system_log('LOSM09001', request=request)

    data = {
        'mainmenu_list'        : request.user_config.get_menu_list(),
        'user_name'            : request.user.user_name,
        'edit'                 : edit,
        'system_log_list'      : system_log_list,
        'system_session_list'  : system_session_list,
        'system_password_list' : system_password_list,
        'system_actdir_list'   : system_actdir_list,
        'system_targro_list'   : system_targro_list,
        'output_flag'          : output_flag,
        'pass_flag'            : pass_flag,
        'disabled_flag'        : settings.DISABLE_WHITE_BLACK_LIST,
        'lang_mode'            : request.user.get_lang_mode(),
    }

    logger.logic_log('LOSI00002', 'edit:%s, pass:%s' % (edit, pass_flag), request=request)

    return render(request, 'system/system_conf_disp.html', data)


################################################
@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
def edit(request):
    """
    [メソッド概要]
      システム設定ページの一覧画面
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    msg = ''
    system_log_list      = []
    system_session_list  = []
    system_password_list = []
    system_actdir_list   = []
    system_targro_list   = []
    output_flag          = 0
    pass_flag            = 0

    permission_type = request.user_config.get_menu_auth_type(MENU_ID)
    edit = True if permission_type == defs.ALLOWED_MENTENANCE else False
    
    try:
        # システム設定情報取得
        system_list = System.objects.filter(maintenance_flag='1').order_by('item_id')

        # システム設定情報作成
        for s in system_list:

            system_info = {
                'item_id': s.item_id,
                'config_name': s.config_name,
                'category': s.category,
                'config_id': s.config_id,
                'value': s.value,
                'maintenance_flag' : s.maintenance_flag,
            }

            if s.category == "LOG_STORAGE_PERIOD":
                system_log_list.append(system_info)

            elif s.category == "SESSION_TIMEOUT":
                system_session_list.append(system_info)

            elif s.category == "PASSWORD":
                system_password_list.append(system_info)

            elif s.category == "ACTIVE_DIRECTORY":

                if s.config_id == "TARGET_GROUP_LIST" and s.value:
                    system_targro_list = ast.literal_eval(s.value)

                # パスワード復号化
                if s.config_id == "ADMINISTRATOR_PW" and s.value is not None and len(s.value) > 0:
                    cipher = AESCipher(settings.AES_KEY)
                    s.value = cipher.decrypt(s.value)

                # 復号化されたパスワードに更新
                system_info['value'] = s.value 
                system_actdir_list.append(system_info)

                if s.config_id == "ADCOLLABORATION" and s.value == '1':
                    output_flag = 1

                    if request.user.user_id not in (1, -2140000000):
                        pass_flag = 1

    except:
        msg = get_message('MOSJA22016', request.user.get_lang_mode())
        logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
        logger.system_log('LOSM09001', request=request)

    data = {
        'mainmenu_list'        : request.user_config.get_menu_list(),
        'user_name'            : request.user.user_name,
        'msg'                  : msg,
        'edit'                 : edit,
        'system_log_list'      : system_log_list,
        'system_session_list'  : system_session_list,
        'system_password_list' : system_password_list,
        'system_actdir_list'   : system_actdir_list,
        'system_targro_list'   : system_targro_list,
        'output_flag'          : output_flag,
        'pass_flag'            : pass_flag,
        'disabled_flag'        : settings.DISABLE_WHITE_BLACK_LIST,
        'lang_mode'            : request.user.get_lang_mode(),
    }

    logger.logic_log('LOSI00002', 'msg:%s, edit:%s, output:%s, pass:%s' % (msg, edit, output_flag, pass_flag), request=request)

    return render(request, 'system/system_conf_edit.html', data)


################################################
@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def modify(request):
    """
    [メソッド概要]
      システム設定のDB更新処理
    """

    logger.logic_log('LOSI00001', '[before_analyze_args]', request=request)

    no_output_ids = ['ADMINISTRATOR_PW', ]

    msg = {}
    error_txt = ''
    error_flag = False
    cipher = AESCipher(settings.AES_KEY)

    adlinkage_new = ''
    adlinkage_old = ''
    adlinkage_flg = 0

    try:
        with transaction.atomic():
            json_str = request.POST.get('json_str',None)
            if json_str is None:
                msg['alertMsg'] = get_message('MOSJA22014', request.user.get_lang_mode())
                logger.user_log('LOSM09002', request=request)
                raise Exception()

            json_str = json.loads(json_str)
            if 'json_str' not in json_str:
                msg['alertMsg'] = get_message('MOSJA22014', request.user.get_lang_mode())
                logger.user_log('LOSM09002', request=request)
                raise Exception()

            for data in json_str['json_str']:
                logger.logic_log('LOSI00003', 'id:%s, config_id:%s, val:%s' % (data['item_id'], data['config_id'], data['value'] if data['config_id'] not in no_output_ids else len(data['value'])), request=request)

            model_serializer = SystemSerializer()

            for data in json_str['json_str']:
                try:
                    model_serializer.validate(data)
                except serializers.ValidationError as e:
                    if data['config_id'] == "TARGET_GROUP_LIST":
                        targetlist = {}
                        for d in e.detail:
                            targetlist[d] = e.detail[d]

                        msg[data['config_id']] = targetlist
                    else:
                        for d in e.detail:
                            msg[data['config_id']] = str(d)

            if len(msg) > 0:
                logger.user_log('LOSM09003', error_txt, request=request)
                raise Exception()

            item_id_info = {} #{ item_id : {'value'} } item_idをkeyにvalueを辞書型で格納
            # 更新データを取得
            for rq in json_str['json_str']:
                item_id_info[rq['item_id']] = rq['value'] #item_idをkeyにvalueを格納

            # 更新データをまとめてロック
            System.objects.select_for_update().filter(item_id__in=list(item_id_info.keys()))

            #更新処理
            for key, value in sorted(item_id_info.items()): #item_idで昇順にソート
                system_data = System.objects.get(item_id=key)

                if system_data.maintenance_flag <= 0:
                    logger.user_log('LOSM09008', system_data.config_id, system_data.maintenance_flag, request=request)
                    msg['alertMsg'] = get_message('MOSJA22014', request.user.get_lang_mode())
                    raise Exception()

                if system_data.value != value:

                    # 「メール通知種別：ログインID指定」のとき「既存のログインID」か確認
                    if system_data.config_id == 'NOTIFICATION_DESTINATION':
                        if value != "" :
                            # フォームの入力値「input_login_list」を取得
                            input_login = value.split(',')
                            input_login_list = list(set(input_login))
                            if 'administrator' in input_login_list :
                                input_login_list.remove('administrator')
                            # DBの値「db_login_id_list」を取得（マイナスユーザを除く）
                            db_data = User.objects.values_list('user_id','login_id')
                            db_login_id_list = []
                            for data in db_data:
                                if data[0] > 1:
                                    db_login_id_list.append(data[1])
                            # ログインIDの登録
                            login_id_lists = []
                            error_ids = []
                            for input_login_id in input_login_list :
                                if input_login_id not in db_login_id_list :
                                    error_ids.append(input_login_id)
                                else :
                                    login_id_lists.append(str(input_login_id))
                            if len(error_ids) != 0:
                                msg['NOTIFICATION_DESTINATION'] = get_message('MOSJA22036', request.user.get_lang_mode(), ids=error_ids)
                                logger.user_log('LOSM09007',error_ids, request=request)
                                raise Exception('validation error.')
                            value = ','.join(login_id_lists)

                    if system_data.config_id == 'ADMINISTRATOR_PW':

                        if len(value) > 64:
                            msg['ADMINISTRATOR_PW'] = get_message('MOSJA22007', request.user.get_lang_mode(), strConName=system_data.config_name)
                            logger.user_log('LOSM09003', '%s: length %s' % (system_data.config_name, len(value)), request=request)
                            raise Exception('validation error.')

                        value = cipher.encrypt(value)

                    if system_data.config_id == 'AD_LINKAGE_TIMER':
                        adlinkage_old = system_data.value
                        adlinkage_new = value

                    if system_data.config_id == 'TARGET_GROUP_LIST':
                        keylist = []
                        vallist = []
                        targetlist = {}

                        for i in range(len(value)):

                            if list(value[i].keys()) not in keylist:
                                keylist.append(list(value[i].keys()))
                            else:
                                targetlist[ i * 2 ] = get_message('MOSJA22024', request.user.get_lang_mode(), key=list(value[i].keys()))
                                msg['TARGET_GROUP_LIST'] = targetlist
                                logger.user_log('LOSM09004', request=request)

                            if list(value[i].values()) not in vallist:
                                vallist.append(list(value[i].values()))
                            else:
                                targetlist[ i * 2 + 1 ] = get_message('MOSJA22024', request.user.get_lang_mode(), key=list(value[i].keys()))
                                msg['TARGET_GROUP_LIST'] = targetlist
                                logger.user_log('LOSM09005', request=request)

                        if len(msg) > 0:
                            raise Exception('validation error.')

                    if system_data.config_id == 'ADCOLLABORATION' and system_data.value == '0' and value == '1':
                        adlinkage_flg = 2  # 2:AD連携実施

                    if system_data.config_id == 'ADCOLLABORATION' and system_data.value == '1' and value == '0':
                        ad_key_list = ['ADMINISTRATOR_USER', 'ADMINISTRATOR_PW', 'ACCESS_POINT', 'AD_LINKAGE_TIMER', 'CONNECTION_TIMEOUT', 'READ_TIMEOUT', 'AUTHSERVER_SEARCH_CHAR', 'TARGET_GROUP_LIST']
                        for ad_key in ad_key_list:
                            adcollabo_date = System.objects.get(config_id=ad_key)

                            if adcollabo_date.config_id == 'AD_LINKAGE_TIMER':
                                adlinkage_old = adcollabo_date.value

                            if adcollabo_date.config_id == 'CONNECTION_TIMEOUT' or adcollabo_date.config_id == 'READ_TIMEOUT':
                                adcollabo_date.value = '30'

                            else:
                                adcollabo_date.value = ''

                            adcollabo_date.last_update_user      = request.user.user_name
                            adcollabo_date.last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC'))
                            adcollabo_date.save()

                        adlinkage_flg = 1  # 1:AD連携解除
                        adlinkage_new = ''

                    system_data.value                 = value
                    system_data.last_update_user      = request.user.user_name
                    system_data.last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC'))
                    system_data.save()

                    # 同一パスワード設定不可世代数変更時処理
                    if system_data.config_id == 'Pass_generate_manage':
                        password_generation = int(value)
                        user_list = User.objects.select_for_update().filter(disuse_flag='0')

                        for user in user_list:
                            uid = user.user_id
                            pw_history_list = PasswordHistory.objects.filter(user_id=uid).order_by('last_update_timestamp')
                            pw_history_list_length = len(pw_history_list)

                            if password_generation < pw_history_list_length:
                                # パスワード履歴の削除
                                del_count = pw_history_list_length - password_generation
                                loop_count = 0

                                for pw_history in pw_history_list:
                                    if loop_count < del_count:
                                        pw_history.delete()
                                        loop_count += 1
                                    else:
                                        break

            # AD連携タイマー設定
            if adlinkage_new != adlinkage_old and getattr(settings, 'EVTIMER_SERVER', None):
                try:
                    if adlinkage_new:
                        adlinkage_new = adlinkage_new.replace(',', '_')
                    else:
                        adlinkage_new = 'None'
                    query = urllib.parse.quote(adlinkage_new)
                    url = settings.EVTIMER_SERVER['path'] % (settings.EVTIMER_SERVER['type'], 'AD_LINKAGE_TIMER', query)
                    url = '%s//%s/%s' % (settings.EVTIMER_SERVER['protocol'], settings.EVTIMER_SERVER['location'], url)

                    te_req = urllib.request.Request(url)
                    with urllib.request.urlopen(te_req) as te_resp:
                        logger.logic_log('LOSI09001', te_resp.status, request=request)

                except urllib.error.HTTPError as e:
                    msg['alertMsg'] = get_message('MOSJA22030', request.user.get_lang_mode())
                    logger.system_log('LOSM09006', e.code, request=request)
                    raise Exception()

                except urllib.error.URLError as e:
                    msg['alertMsg'] = get_message('MOSJA22030', request.user.get_lang_mode())
                    logger.system_log('LOSM09006', e.reason, request=request)
                    raise Exception()

                except Exception as e:
                    msg['alertMsg'] = get_message('MOSJA22030', request.user.get_lang_mode())
                    raise Exception()

    except Exception as e:
        if 'validation error.' != str(e):
            logger.logic_log('LOSM00001', traceback.format_exc(), request=request)
        error_flag = True
        adlinkage_flg = 0
        logger.system_log('LOSM09006', traceback.format_exc(), request=request)


    # 結果レスポンス
    response_data = {}

    # 異常処理
    if error_flag == True:
        response_data['status'] = 'failure'
        response_data['error_msg'] = msg
        response_data['error_txt'] = error_txt
    # 正常処理
    else:
        response_data['status'] = 'success'
        response_data['adflg']  = adlinkage_flg

    response_data['redirect_url'] = reverse('web_app:system:system_conf')

    response_json = json.dumps(response_data, ensure_ascii=False)

    logger.logic_log('LOSI00002', 'response_data: %s' % response_json, request=request)

    return HttpResponse(response_json, content_type="application/json")

@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def run_ad(request):
    """
    [メソッド概要]
    AD連携実行したのちシステム設定にリダイレクト
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    from backyards.ad_collaboration.ad_collaboration import AdCollabExecutor

    executor = AdCollabExecutor()
    result = executor.execute()

    # 結果レスポンス
    response_data = {}

    # 異常処理
    if result == False:
        msg = get_message('MOSJA22015', request.user.get_lang_mode())

        response_data['status'] = 'failure'
        response_data['error_msg'] = msg
    # 正常処理
    else:
        response_data['status'] = 'success'

    response_data['redirect_url'] = reverse('web_app:system:system_conf')
    response_json = json.dumps(response_data, ensure_ascii=False)

    logger.logic_log('LOSI00002', 'response_data: %s' % response_json, request=request)

    return HttpResponse(response_json, content_type="application/json")
