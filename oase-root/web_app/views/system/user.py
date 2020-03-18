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
  ユーザページの表示処理
  また、ユーザページからのリクエスト受信処理

[引数]
  HTTPリクエスト

[戻り値]
  HTTPレスポンス

"""


import copy
import datetime
import hashlib
import json
import traceback
import re
import pytz

from django.http import HttpResponse, Http404
from django.shortcuts import render,redirect
from django.db import transaction
from django.db.models import Q
from django.views.decorators.http import require_POST

from libs.commonlibs import define as defs
from libs.commonlibs.oase_logger import OaseLogger
from libs.commonlibs.common import Common

from libs.webcommonlibs.decorator import *
from libs.webcommonlibs.password  import RandomPassword
from libs.webcommonlibs.oase_mail import *
from libs.webcommonlibs.common import Common as WebCommon
from web_app.models.models import Group, User, UserGroup, PasswordHistory, System
from web_app.templatetags.common import get_message
from web_app.serializers.unicode_check import UnicodeCheck

logger = OaseLogger.get_instance() # ロガー初期化

MENU_ID = 2141002004
@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_EVERY)
def user(request):
    """
    [メソッド概要]
      ユーザページの一覧画面（参照モード）
    """

    msg = ''
    permission_type = request.user_config.get_menu_auth_type(MENU_ID)
    hasUpdateAuthority = True if permission_type == defs.ALLOWED_MENTENANCE and System.objects.get(config_id='ADCOLLABORATION').value == '0' else False

    logger.logic_log('LOSI00001', 'None', request=request)

    try:
        # グループ情報取得
        group_list, group_dict = _getGroupData(request=request)

        # アカウント情報取得
        user_list, search_info = _getUserData({}, request=request)
        filter_list = _create_filter_list(user_list, request=request)

    except:
        msg = get_message('MOSJA24001', request.user.get_lang_mode())
        logger.logic_log('LOSM05000', 'traceback: %s' % traceback.format_exc(), request=request)
        raise Http404

    data = {
        'msg'               : msg,
        'user_list'         : user_list,
        'opelist_add'       : defs.DABASE_OPECODE.OPELIST_ADD,
        'opelist_mod'       : defs.DABASE_OPECODE.OPELIST_MOD,
        'filter_list'       : filter_list,
        'group_list'        : group_list,
        'search_info'       : search_info,
        'mainmenu_list'     : request.user_config.get_menu_list(),
        'edit_mode'         : False,
        'hasUpdateAuthority': hasUpdateAuthority,
        'actdirflg'         : System.objects.get(config_id='ADCOLLABORATION').value,
        'user_name'         : request.user.user_name,
        'lang_mode'         : request.user.get_lang_mode(),
    }

    logger.logic_log('LOSI00002', 'None', request=request)

    return render(request, 'system/user_disp.html', data)

@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def edit(request):
    """
    [メソッド概要]
      ユーザの編集画面
    """

    msg = ''
    permission_type = request.user_config.get_menu_auth_type(MENU_ID)
    hasUpdateAuthority = True if permission_type == defs.ALLOWED_MENTENANCE and System.objects.get(config_id='ADCOLLABORATION').value == '0' else False

    logger.logic_log('LOSI00001', 'permission_type: %s, hasUpdateAuthority: %s' % (permission_type, hasUpdateAuthority) , request=request)

    # AD連携していたらHttp404
    if not hasUpdateAuthority:
        logger.user_log('LOSM05001', request=request)
        raise Http404

    try:
        # グループ情報取得
        group_list, group_dict = _getGroupData(request=request)

        # アカウント情報取得
        filters = request.POST.get('filters', None)
        filters = json.loads(filters)

        user_list, search_info = _getUserData(filters, edit=True, request=request)
        filter_list = _create_filter_list(user_list, request=request)

    except:
        msg = get_message('MOSJA24001', request.user.get_lang_mode())
        logger.logic_log('LOSM05000', 'traceback: %s' % traceback.format_exc(), request=request )
        raise Http404

    data = {
        'msg'               : msg,
        'user_list'         : user_list,
        'opelist_add'       : defs.DABASE_OPECODE.OPELIST_ADD,
        'opelist_mod'       : defs.DABASE_OPECODE.OPELIST_MOD,
        'filter_list'       : filter_list,
        'group_list'        : group_list,
        'search_info'       : search_info,
        'mainmenu_list'     : request.user_config.get_menu_list(),
        'edit_mode'         : True,
        'hasUpdateAuthority': hasUpdateAuthority,
        'actdirflg'         : System.objects.get(config_id='ADCOLLABORATION').value,
        'user_name'         : request.user.user_name,
        'lang_mode'         : request.user.get_lang_mode(),
    }

    logger.logic_log('LOSI00002', 'permission_type: %s, hasUpdateAuthority: %s' % (permission_type, hasUpdateAuthority), request=request)
    return render(request, 'system/user_edit.html', data)


def _create_filter_list(user_list, request=None):
    """
    [メソッド概要]
      フィルタのリストを作成する
    [引数]
      user_list    :_getUserData(filters)により作成されるuser_list
      request :logger.logic_logでuserId sessionIDを表示するために使用する
    [戻り値]
      filter_list
    """

    logger.logic_log('LOSI00001', 'user_list: %s' % len(user_list), request=request)

    filter_list = []
    pulldown_list = [ {'k':u,'v':u} for u in sorted({u["user_name"] for u in user_list}) ]
    pulldown_list.insert(0, {'k':'','v':''})
    filter_list.append(
        {
            'colno'   : 'user_name',
            'caption' : 'ユーザ名',
            'like'    : True,
            'fromto'  : None,
            'pulldown': copy.copy(pulldown_list),
            'calendar': None,
        }
    )

    pulldown_list = [ {'k':u,'v':u} for u in sorted({u["login_id"] for u in user_list}) ]
    pulldown_list.insert(0, {'k':'','v':''})
    filter_list.append(
        {
            'colno'   : 'login_id',
            'caption' : 'ログインID',
            'like'    : True,
            'fromto'  : None,
            'pulldown': copy.copy(pulldown_list),
            'calendar': None,
        }
    )

    pulldown_list = [ {'k':u,'v':u} for u in sorted({u["mail"] for u in user_list}) ]
    pulldown_list.insert(0, {'k':'','v':''})
    filter_list.append(
        {
            'colno'   : 'mail_address',
            'caption' : 'メールアドレス',
            'like'    : True,
            'fromto'  : None,
            'pulldown': copy.copy(pulldown_list),
            'calendar': None,
        }
    )

    # アクティブユーザが所属しているグループ名を昇順で取得する
    group_names = sorted({ gn for u in user_list for gn in u["group_name"]})

    # グループ名のリストを作成
    pulldown_list =[{'k':group_names[i], 'v':group_names[i]} for i in range(len(group_names))]
    pulldown_list.insert(0, {'k':'','v':''})
    filter_list.append(
        {
            'colno'   : 'group_name',
            'caption' : 'グループ名',
            'like'    : True,
            'fromto'  : None,
            'pulldown': copy.copy(pulldown_list),
            'calendar': None,
        }
    )

    uuname_list = sorted({u["upd_user"] for u in user_list})
    pulldown_list =[{'k':uuname_list[i], 'v':uuname_list[i]} for i in range(len(uuname_list))]
    pulldown_list.insert(0, {'k':'','v':''})
    filter_list.append(
        {
            'colno'   : 'last_update_user',
            'caption' : '最終更新者',
            'like'    : True,
            'fromto'  : None,
            'pulldown': copy.copy(pulldown_list),
            'calendar': None,
        }
    )

    filter_list.append(
        {
            'colno'   : 'last_update_timestamp',
            'caption' : '最終更新日時',
            'like'    : None,
            'fromto'  : None,
            'pulldown': [],
            'calendar': True,
        }
    )

    logger.logic_log('LOSI00002', 'filter_list: %s' % filter_list, request=request)
    return filter_list


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def modify(request):
    """
    [メソッド概要]
      データ更新処理
    """
    #====アカウント追加時の初期値====#
    disp = defs.DISP_MODE.DEFAULT
    lang = defs.LANG_MODE.JP

    msg                  = ''
    error_msg            = ''
    error_msg_user_name  = ''
    error_msg_login_id   = ''
    error_msg_mail       = ''
    error_msg_user_group = ''

    json_str = request.POST.get('json_str',None)

    logger.logic_log('LOSI00001', 'json_str: %s' % json_str, request=request)

    if json_str is None:
        msg = get_message('MOSJA24001', request.user.get_lang_mode())
        logger.user_log('LOSM05002', request=request)
        raise Http404

    try:
        with transaction.atomic():
            json_str = json.loads(json_str)

            #=================ロック=============================#
            # リクエストされたグループIDを取得
            group_ids_req = []
            for rq in json_str['insertInfo']:
                for gid in rq['add_group_id']:
                    if len(gid) != 0:
                        gid = int(gid)
                        if gid not in group_ids_req:
                            group_ids_req.append(gid)

            for rq in json_str['updateInfo']:
                for gid in rq['add_group_id']:
                    if len(gid) != 0:
                        gid = int(gid)
                        if gid not in group_ids_req:
                            group_ids_req.append(gid)

                for gid in rq['del_group_id']:
                    if len(gid) != 0:
                        gid = int(gid)
                        if gid not in group_ids_req:
                            group_ids_req.append(gid)

            group_ids_req.sort()

            # グループ管理をロック
            group_ids_db = []
            for gid in group_ids_req:
                gr = Group.objects.select_for_update().filter(group_id=gid)
                if len(gr) <= 0:
                    logger.user_log('LOSM05005', 'group_id: %s' % gid , request=request)
                    continue

                group_ids_db.append(gr[0].group_id)

            group_ids_diff = list(set(group_ids_req) ^ set(group_ids_db))


            # 更新レコードのリスト作成(administrator除く)
            update_info = []
            update_userid_list = []
            for rq in json_str['updateInfo']:
                if int(rq['user_id']) != 1:
                    update_info.append(rq)
                    update_userid_list.append(int(rq['user_id']))
                else:
                    logger.user_log('LOSM05008', 'update_user_info: %s ' % rq , request=request)

            # 削除レコードのリスト作成(administrator除く)
            del_info = []
            del_userid_list = []
            for rq in json_str['delInfo']:
                if int(rq['user_id']) != 1:
                    del_info.append(rq)
                    del_userid_list.append(int(rq['user_id']))
                else:
                    logger.user_log('LOSM05008', 'delete_user_info: %s ' % rq , request=request)

            # 更新/削除ユーザをロック
            mod_user_list = update_userid_list + del_userid_list 
            mod_user_list.sort()
            for m in mod_user_list:
                User.objects.select_for_update().filter(pk=m)


            #=================チェック===========================#
            # 入力データチェック データ不正であればresponseを返す
            error_flag, error_msg_user_name, error_msg_login_id, error_msg_mail, error_msg_user_group = _validate(json_str, group_ids_diff, request=request)
            if error_flag:
                response_json = json.dumps({
                    'status'              : 'failure',
                    'error_msg_user_name' : error_msg_user_name,
                    'error_msg_login_id'  : error_msg_login_id,
                    'error_msg_mail'      : error_msg_mail,
                    'error_msg_user_group': error_msg_user_group,
                    'msg'                 : '',
                })

                logger.user_log('LOSM05004', 'error_msg_user_name: %s' % error_msg_user_name, request=request)
                logger.user_log('LOSM05004', 'error_msg_login_id: %s' % error_msg_login_id, request=request)
                logger.user_log('LOSM05004', 'error_msg_mail: %s' % error_msg_mail, request=request)
                logger.user_log('LOSM05004', 'error_msg_user_group: %s' % error_msg_user_group, request=request)
                logger.logic_log('LOSI00002', 'json_str: %s' % json_str, request=request)

                return HttpResponse(response_json, content_type="application/json")

            #=================更新===============================#
            update_list = []
            del_usergroup_list = {}
            add_usergroup_list = {}
            user_info = {}
            
            logger.user_log('LOSI05000', update_info, request=request)
            
            for rq in update_info:
                user_info[int(rq['user_id'])] = {
                    'user_name': rq['user_name'],
                    'login_id' : rq['login_id'], 
                    'mail'     : rq['mail'],
                    'add_group_id' : rq['add_group_id'],
                    'del_group_id' : rq['del_group_id'],
                }

            users = User.objects.filter(pk__in=update_userid_list, disuse_flag='0')
            for u in users:
                u.user_name    = user_info[u.pk]['user_name']
                u.login_id     = user_info[u.pk]['login_id']
                u.mail_address = user_info[u.pk]['mail']
                u.last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC'))
                u.last_update_user = request.user.user_name

                add_usergroup_list[u.user_id] = [int(s) for s in user_info[u.pk]['add_group_id']]
                del_usergroup_list[u.user_id] = [int(s) for s in user_info[u.pk]['del_group_id']]
                update_list.append(u)

            for u in update_list:
                u.save()
                if u.pk in add_usergroup_list:
                    for g in add_usergroup_list[u.pk]:
                        ug = UserGroup(
                            user_id = u.pk,
                            group_id = g,
                            last_update_user = request.user.user_name,
                            )
                        ug.save(force_insert=True)
                if u.pk in del_usergroup_list:
                    UserGroup.objects.filter(user_id=u.pk, group_id__in=del_usergroup_list[u.pk]).delete()

            logger.user_log('LOSI05001', update_info, request=request)

            #=================削除===============================#
            logger.user_log('LOSI05002', del_info, request=request)
            
            User.objects.filter(pk__in=del_userid_list).delete()
            UserGroup.objects.filter(user_id__in=del_userid_list).delete()
            PasswordHistory.objects.filter(user_id__in=del_userid_list).delete()

            logger.user_log('LOSI05003', del_info, request=request)

            #==================新規追加===============================#
            insert_list = []
            insert_usergroup_list = {}
            insert_list_pwhist = []
            create_list = []
            create_err_flag = False
            ttl_hour = int(System.objects.get(config_id='INITIAL_PASS_VALID_PERIOD').value)

            for rq in json_str['insertInfo']:
                # ランダムパスワード生成
                password = RandomPassword().get_password()
                password_hash = Common.oase_hash(password)
                password_expire = None
                if ttl_hour == 0:
                    # datetime supportで日時がずれoverflowするため9000年とした
                    password_expire = datetime.datetime.strptime('9000-12-31 23:59:59', '%Y-%m-%d %H:%M:%S')
                else:
                    password_expire = datetime.datetime.now(pytz.timezone('UTC')) + datetime.timedelta(hours=ttl_hour)

                user = User( 
                    user_name    = rq['user_name'],
                    login_id     = rq['login_id'],
                    mail_address = rq['mail'],
                    password     = password_hash,
                    disp_mode_id = disp,
                    lang_mode_id = lang,
                    password_count = 0,
                    password_expire = password_expire,
                    last_update_user = request.user.user_name,
                    last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
                )

                insert_list.append(user)
                insert_usergroup_list[rq['login_id']] = rq['add_group_id']

                create_info = {
                    'name' : rq['user_name'],
                    'mail' : rq['mail'],
                    'pass' : password,
                    'id'   : rq['login_id'],
                }
                create_list.append(create_info)

            Pass_generate_manage = int(System.objects.get(config_id='Pass_generate_manage').value)
            logger.user_log('LOSI05004', json_str['insertInfo'], Pass_generate_manage, request=request)
            # create処理
            for i in insert_list:
                i.save(force_insert=True)
                # userが登録できたらusergroupを登録
                for j in insert_usergroup_list[i.login_id]:
                    usergroup = UserGroup(
                        user_id = i.pk,
                        group_id = j,
                        last_update_user = request.user.user_name,
                    )
                    usergroup.save(force_insert=True)

                if Pass_generate_manage > 0:
                    passwd_history = PasswordHistory(
                       user_id  = i.user_id,
                       password = password_hash,
                       last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
                       last_update_user = request.user.user_name,
                    )
                    insert_list_pwhist.append(passwd_history)

            if len(insert_list_pwhist) > 0:
                PasswordHistory.objects.bulk_create(insert_list_pwhist)

            logger.user_log('LOSI05005', json_str['insertInfo'], Pass_generate_manage, request=request)

            # 署名用URL生成
            req_protcol = request.scheme
            req_host    = request.get_host()
            login_url   = reverse('web_app:top:login')
            inquiry_url = reverse('web_app:top:inquiry')
            login_url   = '%s://%s%s' % (req_protcol, req_host, login_url)
            inquiry_url = '%s://%s%s' % (req_protcol, req_host, inquiry_url)

            # 新規登録ユーザに初期ユーザIDをメールで通知
            msg_ids = []
            if len(create_list) > 0 and create_err_flag == False:
                smtp = OASEMailSMTP(request=request)
                for u in create_list:
                    user_mail = OASEMailInitialLoginID(
                        request.user.mail_address, u['mail'], u['name'], u['id'], ttl_hour, inquiry_url, login_url
                    )
                    send_result = smtp.send_mail(user_mail)

                    logger.logic_log('LOSI05006', u['mail'], u['id'], request=request)
                    if send_result and send_result not in msg_ids:
                        msg_ids.append(send_result)
                        send_result = get_message(send_result, request.user.get_lang_mode())
                        error_flag = True
                        if msg:
                            msg += '\n'
                        msg += send_result

            # 新規登録ユーザに初期パスワードをメールで通知
            if len(create_list) > 0 and create_err_flag == False:
                smtp = OASEMailSMTP(request=request)
                for u in create_list:
                    user_mail = OASEMailInitialPasswd(
                        request.user.mail_address, u['mail'], u['name'], u['pass'], ttl_hour, inquiry_url, login_url
                    )
                    send_result = smtp.send_mail(user_mail)

                    logger.logic_log('LOSI05007', u['mail'], request=request)
                    if send_result and send_result not in msg_ids:
                        msg_ids.append(send_result)
                        send_result = get_message(send_result, request.user.get_lang_mode())
                        error_flag = True
                        if msg:
                            msg += '\n'
                        msg += send_result

    except Exception as e:
        error_flag = True
        logger.logic_log('LOSM05003', 'json_str: %s, traceback: %s' % (json_str, traceback.format_exc()), request=request)

    # 結果レスポンス
    response_data = {}

    # 異常処理
    if error_flag == True:

        response_data['status'] = 'failure'
        response_data['error_msg'] = error_msg
        response_data['msg'] = msg
        logger.logic_log('LOSM05007', 'json_str: %s, response_data: %s, traceback: %s' % (json_str, response_data, traceback.format_exc()), request=request)

    # 正常処理
    else:
        response_data['status'] = 'success'
        response_data['redirect_url'] = '/oase_web/system/user'

    response_json = json.dumps(response_data)

    logger.logic_log('LOSI00002', 'json_str: %s, response_json: %s' % (json_str, response_json), request=request)
    return HttpResponse(response_json, content_type="application/json")

def _validate(json_str, group_ids_diff=[], request=None):
    """
    [メソッド概要]
      入力チェック
    [引数]
      request :logger.logic_logでuserId sessionIDを表示するために使用する
    [戻り値]
      error_flag
      error_msg_user_name
      error_msg_login_id
      error_msg_mail
      error_msg_user_group
    """

    error_flag           = False
    error_msg_user_name  = {}
    error_msg_login_id   = {}
    error_msg_mail       = {}
    error_msg_user_group = {}
    chk_login            = []
    chk_mail             = []
    loginID_pattern      = r'^[a-zA-Z0-9.@_\-]+$'
    mail_pattern         = r'^([\w!#$%&\'*+\-\/=?^`{|}~]+(\.[\w!#$%&\'*+\-\/=?^`{|}~]+)*|"([\w!#$%&\'*+\-\/=?^`{|}~. ()<>\[\]:;@,]|\\[\\"])+")@(([a-zA-Z\d\-]+\.)+[a-zA-Z]+|\[(\d{1,3}(\.\d{1,3}){3}|IPv6:[\da-fA-F]{0,4}(:[\da-fA-F]{0,4}){1,5}(:\d{1,3}(\.\d{1,3}){3}|(:[\da-fA-F]{0,4}){0,2}))\])$'
    emo_chk              = UnicodeCheck()

    logger.logic_log('LOSI00001', 'json_str: %s' % json_str, request=request)

    # jsonの形式チェック
    if {'insertInfo','updateInfo','delInfo'} != set(list(json_str.keys())):
        logger.user_log('LOSM05002', request=request)

        raise TypeError( 'json_strの形式不正')
    loginID_repatter = re.compile(loginID_pattern)
    mail_repatter = re.compile(mail_pattern)

    for k,v in json_str.items():
        for rq in v:
            # 削除の場合は飛ばす
            if k == 'delInfo':
                continue

            error_msg_user_name[rq['row_id']]  = ''
            error_msg_login_id[rq['row_id']]   = ''
            error_msg_mail[rq['row_id']]       = ''
            error_msg_user_group[rq['row_id']] = ''

            if 'user_name' in rq and len(rq['user_name']) == 0:
                error_msg_user_name[rq['row_id']] += get_message('MOSJA24005', request.user.get_lang_mode()) + '\n'

            if 'login_id' in rq and len(rq['login_id']) == 0:
                error_msg_login_id[rq['row_id']] += get_message('MOSJA24006', request.user.get_lang_mode()) + '\n'

            if 'mail' in rq and len(rq['mail']) == 0:
                error_msg_mail[rq['row_id']] += get_message('MOSJA24007', request.user.get_lang_mode()) + '\n'

            if k == 'insertInfo':
                if 'add_group_id' not in rq:
                    error_msg_user_group[rq['row_id']] += get_message('MOSJA24008', request.user.get_lang_mode()) + '\n'

            if 'add_group_id' in rq:
                for gid in rq['add_group_id']:
                    if len(gid) == 0:
                        error_msg_user_group[rq['row_id']] += get_message('MOSJA24008', request.user.get_lang_mode()) + '\n'
                        break

                    gid = int(gid)
                    if gid in group_ids_diff:
                        error_msg_user_group[rq['row_id']] += get_message('MOSJA24016', request.user.get_lang_mode()) + '\n'
                        break

            if 'del_group_id' in rq:
                for gid in rq['del_group_id']:
                    gid = int(gid)
                    if gid in group_ids_diff:
                        error_msg_user_group[rq['row_id']] += get_message('MOSJA24019', request.user.get_lang_mode()) + '\n'
                        break

            if 'user_name' in rq and len(rq['user_name']) > 64:
                error_msg_user_name[rq['row_id']] += get_message('MOSJA24011', request.user.get_lang_mode()) + '\n'

            if 'login_id' in rq and len(rq['login_id']) > 32:
                error_msg_login_id[rq['row_id']] += get_message('MOSJA24012', request.user.get_lang_mode()) + '\n'

            if 'mail' in rq and len(rq['mail']) > 256:
                error_msg_mail[rq['row_id']] += get_message('MOSJA24013', request.user.get_lang_mode()) + '\n'

            if chk_login.count(rq['login_id']) > 0:
                error_msg_login_id[rq['row_id']] += get_message('MOSJA24017', request.user.get_lang_mode()) + '\n'

            # user_name絵文字チェック
            value_list = emo_chk.is_emotion(rq['user_name'])
            if len(value_list) > 0:
                error_msg_user_name[rq['row_id']] += get_message('MOSJA24022', request.user.get_lang_mode(), strConName='ユーザ名') + '\n'

            # login_id絵文字チェック
            value_list = emo_chk.is_emotion(rq['login_id'])
            if len(value_list) > 0:
                error_msg_login_id[rq['row_id']] += get_message('MOSJA24022', request.user.get_lang_mode(), strConName='ログインID') + '\n'

            # mail絵文字チェック
            value_list = emo_chk.is_emotion(rq['mail'])
            if len(value_list) > 0:
                error_msg_mail[rq['row_id']] += get_message('MOSJA24022', request.user.get_lang_mode(), strConName='メールアドレス') + '\n'

            else:
                duplication = User.objects.filter(login_id=rq['login_id'])
                if len(duplication) == 1 and int(rq['user_id']) != duplication[0].user_id:
                    error_msg_login_id[rq['row_id']] += get_message('MOSJA24017', request.user.get_lang_mode()) + '\n'

            if chk_mail.count(rq['mail']) > 0:
                error_msg_mail[rq['row_id']] += get_message('MOSJA24018', request.user.get_lang_mode()) + '\n'

            else:
                duplication = User.objects.filter(mail_address=rq['mail'])
                if len(duplication) == 1 and int(rq['user_id']) != duplication[0].user_id:
                    error_msg_mail[rq['row_id']] += get_message('MOSJA24018', request.user.get_lang_mode()) + '\n'

            if 'login_id' in rq and len(rq['login_id']) != 0:
                re_obj = loginID_repatter.match(rq['login_id'])
                if not re_obj:
                    error_msg_login_id[rq['row_id']] += get_message('MOSJA24021', request.user.get_lang_mode()) + '\n'

            if 'mail' in rq and len(rq['mail']) != 0:
                re_obj = mail_repatter.match(rq['mail'])
                if not re_obj:
                    error_msg_mail[rq['row_id']] += get_message('MOSJA24014', request.user.get_lang_mode()) + '\n'

            if len(error_msg_user_name[rq['row_id']]) > 0:
                error_flag = True
            elif len(error_msg_login_id[rq['row_id']]) > 0:
                error_flag = True
            elif len(error_msg_mail[rq['row_id']]) > 0:
                error_flag = True
            elif len(error_msg_user_group[rq['row_id']]) > 0:
                error_flag = True

            chk_login.append(rq['login_id'])
            chk_mail.append(rq['mail'])

    logger.logic_log('LOSI00002', 'error_flag: %s' % error_flag, request=request)
    return error_flag, error_msg_user_name, error_msg_login_id, error_msg_mail, error_msg_user_group


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_EVERY)
@require_POST
def data(request):
    """
    [メソッド概要]
      (フィルタ実行時の)データ取得
    """
    msg = ''

    logger.logic_log('LOSI00001', 'None', request=request)

    user_list = []
    search_info = []
    try:
        # グループ情報取得
        group_list, group_dict = _getGroupData(request=request)

        # アカウント情報取得
        filters = request.POST.get('filters',None)
        filters = json.loads(filters)
        user_list, search_info = _getUserData(filters, request=request)

    except Exception as e:
        msg = get_message('MOSJA24001', request.user.get_lang_mode())
        logger.logic_log('LOSM05000', 'traceback: %s' % traceback.format_exc(), request=request)

    data = {
        'msg'        : msg,
        'user_list'  : user_list,
        'group_list' : group_list,
        'search_info': search_info,
        'opelist_add': defs.DABASE_OPECODE.OPELIST_ADD,
        'opelist_mod': defs.DABASE_OPECODE.OPELIST_MOD,
        'edit_mode'  : False,
        'actdirflg'  : System.objects.get(config_id='ADCOLLABORATION').value,
        'lang_mode'  : request.user.get_lang_mode(),
    }

    logger.logic_log('LOSI00002', 'data: %s' % data, request=request)
    return render(request, 'system/user_data_disp.html', data)


def _getGroupData(request=None):
    """
    [メソッド概要]
      データ更新処理
    [引数]
      request :logger.logic_logでuserId sessionIDを表示するために使用する
    [戻り値]
      group_list
      group_dict
    """
    
    logger.logic_log('LOSI00001', 'None', request=request)
    
    groups = Group.objects.filter(pk__gte=1).order_by('group_id')
    group_list = groups.values('group_id', 'group_name')

    group_dict = {g.group_id:g.group_name  for g in groups}

    logger.logic_log('LOSI00002', 'group_dict: %s' % group_dict, request=request)

    return group_list, group_dict


def _getUserData(filters, edit=False, request=None):
    """
    [メソッド概要]
      データ更新処理
    [引数]
      edit : bool 編集モードか否か デフォルトは一覧モード
      request :logger.logic_logでuserId sessionIDを表示するために使用する
    [戻り値]
      user_list
    """

    logger.logic_log('LOSI00001', 'filters: %s' % filters, request=request)

    # リスト表示用 編集モードと一覧モードでフィルタを分ける
    where_info = {'pk__gt':1, 'disuse_flag':'0'} if edit else {'pk__gt':0, 'disuse_flag':'0'}
    where_group_info = {}

    WebCommon.convert_filters(filters, where_info)
    search_info =  _get_search_info(where_info)

    # グループのフィルタ情報をwhere_infoから抽出
    if 'group_name__contains' in where_info:
        where_group_info['group_name__contains'] = where_info.pop('group_name__contains')
    if 'group_name__in' in where_info:
        where_group_info['group_name__in'] = where_info.pop('group_name__in')


    # フィルタ情報によるデータ抽出
    user = User.objects.filter(**where_info)

    if len(where_group_info):
        ug_list  = []
        gid_list = Group.objects.filter(**where_group_info).values_list('group_id', flat=True)
        if len(gid_list) > 0:
            ug_list = list(UserGroup.objects.filter(group_id__in=gid_list).values_list('user_id', flat=True).distinct())

        if len(ug_list) > 0:
            user = user.filter(pk__in=ug_list)

        else:
            logger.user_log('LOSM05006', 'Group: %s' % where_info['Group'], request=request)
            logger.logic_log('LOSI00002', 'None', request=request)
            return []


    # 抽出結果を画面表示用に整形
    user_list = []
    for u in user:
        group_id_list, group_name_list = u.get_group_info()
        user_info = {
            'user_id'  : u.user_id,
            'user_name': u.user_name,
            'login_id' : u.login_id,
            'mail'     : u.mail_address,
            'group_id' : group_id_list,
            'upd_user': u.last_update_user,
            'updated'  : u.last_update_timestamp,
            'group_name' : group_name_list,
            'upd_user_name' : u.last_update_user,
        }
        user_list.append(user_info)

    logger.logic_log('LOSI00002', 'user_list: %s' % len(user_list), request=request)

    return user_list, search_info


def _get_search_info(where_info):
    """
    [メソッド概要]
    フィルター検索内容を赤くするための情報を作成
    [引数]
    where_info : dict  mail_templateの検索情報
    [戻り値]
    """
    logger.logic_log('LOSI00001', 'where_info: %s' % (where_info))

    # フィルタ結果表示用
    search_info = {
        'user_name' : [],
        'login_id' : [],
        'mail_address' : [],
        'group_id' : [],
        'last_update_user' : [],
    }

    if 'user_name__contains' in where_info:
        search_info['user_name'].append(where_info['user_name__contains'])

    if 'user_name__in' in where_info:
        search_info['user_name'].extend(where_info['user_name__in'])

    if 'login_id__contains' in where_info:
        search_info['login_id'].append(where_info['login_id__contains'])

    if 'login_id__in' in where_info:
        search_info['login_id'].extend(where_info['login_id__in'])

    if 'mail_address__contains' in where_info:
        search_info['mail_address'].append(where_info['mail_address__contains'])

    if 'mail_address__in' in where_info:
        search_info['mail_address'].extend(where_info['mail_address__in'])

    if 'group_name__contains' in where_info:
        search_info['group_id'].append(where_info['group_name__contains'])

    if 'group_name__in' in where_info:
        search_info['group_id'].extend(where_info['group_name__in'])

    if 'last_update_user__in' in where_info:
        search_info['last_update_user'].extend(where_info['last_update_user__in'])

    logger.logic_log('LOSI00002', 'search_info: %s' % search_info)

    return search_info

