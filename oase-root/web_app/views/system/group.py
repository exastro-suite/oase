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
    "グループ"アイテムの画面コントローラ
"""
import pytz
import datetime
import json
import traceback

from django.http import HttpResponse
from django.http import HttpResponseServerError
from django.shortcuts import render
from django.db import transaction
from django.conf import settings
from django.views.decorators.http import require_POST

from libs.commonlibs import define as defs
from libs.commonlibs.oase_logger import OaseLogger
from libs.webcommonlibs.decorator import *
from web_app.models.models import Group
from web_app.models.models import User
from web_app.models.models import UserGroup
from web_app.models.models import AccessPermission
from web_app.models.models import PasswordHistory
from web_app.models.models import System
from web_app.templatetags.common import get_message
from web_app.views.forms.group_form import GroupForm
from libs.webcommonlibs.common import Common as WebCommon

MENU_ID = 2141002003
logger = OaseLogger.get_instance()  # ロガー初期化


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_EVERY)
def group(request):
    """
    [メソッド概要]
      グループ画面
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    # メンテナンス権限チェック
    permission_type = request.user_config.get_menu_auth_type(MENU_ID)
    editable_user = True if permission_type == defs.ALLOWED_MENTENANCE else False

    menu_id_list = [2141001006, 2141002001, 2141002002, 2141002003, 2141002004, 2141002007]
    acs_perm_list = AccessPermission.objects.filter(
        group_id__gte=1,
        menu_id__in=menu_id_list,
    ).order_by('group_id', 'permission_id')

    group_list = []
    group_list_tmp = []
    acs_list = {}
    filter_list = []
    msg = ''
    try:
        # グループ情報取得
        filters = {}
        group_list_tmp = _select(filters)
        group_count = len(group_list_tmp)

        # グループごとにアクセス権限を分けたリストを作成する
        acs_count = len(acs_perm_list)
        menu_count = len(menu_id_list)
        for acs_perm in acs_perm_list:
            if acs_perm.group_id not in acs_list:
                acs_list[acs_perm.group_id] = []

            acs_list[acs_perm.group_id].append(acs_perm)

    except:
        logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
        msg = get_message('MOSJA23018', request.user.get_lang_mode(), showMsgId=False)

    # 一覧画面のgroup_listはアクセス権限も含む
    for group in group_list_tmp:
        group_id = group['group_id']
        if group_id in acs_list:
            group_list.append([group, acs_list[group_id]])

    data = {
        'msg': msg,
        'group_list': group_list,
        'filter_list': filter_list,
        'menu_id_list': menu_id_list,
        'editable_user': editable_user,
        'mainmenu_list': request.user_config.get_menu_list(),
        'filters': json.dumps(filters),
        'actdirflg': System.objects.get(config_id='ADCOLLABORATION').value,
        'user_name': request.user.user_name,
        'lang_mode': request.user.get_lang_mode(),
    }

    logger.logic_log('LOSI00002', 'editable_user: %s, group_list count: %s' %
                     (editable_user, group_count), request=request)

    return render(request, 'system/group_disp.html', data)


@check_allowed_ad(settings.LOGIN_REDIRECT_URL)
@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
def edit(request):
    """
    [メソッド概要]
      グループ画面
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    # メンテナンス権限チェック
    permission_type = request.user_config.get_menu_auth_type(MENU_ID)

    msg = ''
    filter_list = []
    try:
        # グループ情報取得
        filters = {}
        group_list = _select(filters)

    except:
        logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
        msg = get_message('MOSJA23018', request.user.get_lang_mode(), showMsgId=False)

    data = {
        'msg': msg,
        'group_list': group_list,
        'filter_list': filter_list,
        'mainmenu_list': request.user_config.get_menu_list(),
        'opelist_mod': defs.DABASE_OPECODE.OPELIST_MOD,
        'filters': json.dumps(filters),
        'user_name': request.user.user_name,
        'lang_mode': request.user.get_lang_mode(),
    }

    logger.logic_log('LOSI00002', 'group_list count: %s' % (len(group_list)), request=request)

    return render(request, 'system/group_edit.html', data)


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_EVERY)
def complete_permission(request, group_id):

    logger.logic_log('LOSI00001', 'group_id: %s' % (group_id), request=request)

    if not request or request.method != 'POST':
        logger.logic_log('LOSM04004', request=request)
        msg = get_message('MOSJA23019', request.user.get_lang_mode(), showMsgId=False)
        return HttpResponseServerError(msg)

    # 成功時レスポンスデータ
    redirect_url = '/oase_web/system/group'
    response = {
        "status": "success",
        "redirect_url": redirect_url,
    }
    # 変更ボタンが押されたら変更のあったレコードのみ更新する
    # 更新後はgroupにリダイレクトする。
    try:
        with transaction.atomic():
            # 選択されたグループを取得
            selected_group = Group.objects.select_for_update().get(pk=group_id)
            now = datetime.datetime.now(pytz.timezone('UTC'))

            # 選択されたグループIDのメニューのアクセス権限を取得
            # oase_webのメニューIDは2141001001以上
            menu_id_list = [2141001006, 2141002001, 2141002002, 2141002003, 2141002004, 2141002007]
            acs_list_upd = AccessPermission.objects.filter(group_id=group_id, menu_id__in=menu_id_list)

            for acs in acs_list_upd:
                menu_id = str(acs.menu_id)
                if menu_id not in request.POST:
                    continue

                new_type_id = int(request.POST.get(menu_id))

                # 変更があったもののみ更新
                if acs.permission_type_id != new_type_id:
                    acs.permission_type_id = new_type_id
                    acs.last_update_user = request.user.user_name
                    acs.last_update_timestamp = now
                    acs.save(force_update=True)

            selected_group.last_update_user = request.user.user_name
            selected_group.last_update_timestamp = now
            selected_group.save(force_update=True)

    except Exception as e:
        logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
        response['status'] = 'failure'
        response['msg'] = get_message('MOSJA23021', request.user.get_lang_mode())

    response_json = json.dumps(response)
    logger.logic_log('LOSI00002', 'status=%s' % response['status'], request=request)

    return HttpResponse(response_json, content_type="application/json")


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def modify(request):
    """
    [メソッド概要]
      グループのDB更新処理
    """
    logger.logic_log('LOSI00001', 'None', request=request)

    msg = ''
    error_msg = {}
    now = datetime.datetime.now(pytz.timezone('UTC'))

    try:
        with transaction.atomic():
            json_str = json.loads(request.POST.get('json_str', '{}'))
            if 'json_str' not in json_str:
                msg = get_message('MOSJA23019', request.user.get_lang_mode(), showMsgId=False)
                logger.user_log('LOSM04000', 'json_str', request=request)
                raise Exception()

            # 更新前にレコードロック
            group_update_list = [
                rq['group_id']
                for rq in json_str['json_str']
                if int(rq['ope']) in (defs.DABASE_OPECODE.OPE_UPDATE, defs.DABASE_OPECODE.OPE_DELETE)
            ]
            Group.objects.select_for_update().filter(pk__in=group_update_list)

            error_flag, error_msg = _validate(json_str['json_str'], request)
            if error_flag:
                raise Exception('validation error.')

            # 更新データ作成
            group_id_list_reg = []
            group_id_list_mod = []
            sorted_data = sorted(json_str['json_str'], key=lambda x: x['group_id'])
            upd_data = list(filter(lambda x: int(x['ope']) == defs.DABASE_OPECODE.OPE_UPDATE, sorted_data))
            del_data = list(filter(lambda x: int(x['ope']) == defs.DABASE_OPECODE.OPE_DELETE, sorted_data))
            ins_data = list(filter(lambda x: int(x['ope']) == defs.DABASE_OPECODE.OPE_INSERT, sorted_data))

            for rq in upd_data:
                group_id_list_mod = Group.objects.filter(group_id=rq['group_id'])
                if len(group_id_list_mod) <= 0:
                    logger.logic_log('LOSI04000', rq['group_name'], request=request)
                    continue

                # システム管理者はグループ名の更新不可
                if int(rq['group_id']) != 1:
                    group_id_list_mod[0].group_name = rq['group_name']
                group_id_list_mod[0].summary = rq['summary']
                group_id_list_mod[0].last_update_user = request.user.user_name
                group_id_list_mod[0].last_update_timestamp = now
                group_id_list_mod[0].save(force_update=True)

            group_id_list_del = [rq['group_id'] for rq in del_data if int(rq['group_id']) != 1]

            for rq in ins_data:
                group_info = Group(
                    group_name=rq['group_name'],
                    summary=rq['summary'],
                    last_update_user=request.user.user_name,
                    last_update_timestamp=now
                )
                group_id_list_reg.append(group_info)

            # 追加
            Group.objects.bulk_create(group_id_list_reg)

            # 権限を追加
            _bulk_create_access_permission(
                request.user.user_name,
                [i.group_name for i in group_id_list_reg],
                now,
            )

            # 削除対象グループを削除
            Group.objects.filter(pk__in=group_id_list_del).delete()

            # 削除対象ユーザグループに該当するユーザIDを取得
            before_user_list = list(UserGroup.objects.filter(group_id__in=group_id_list_del).values_list('user_id', flat=True).distinct())

            # ユーザグループを削除
            UserGroup.objects.filter(group_id__in=group_id_list_del).delete()

            # どのグループにも所属しないユーザを検索
            after_user_list  = list(UserGroup.objects.filter(user_id__in=before_user_list).values_list('user_id', flat=True).distinct())
            delete_user_list = list(set(before_user_list) ^ set(after_user_list))

            # ユーザ、パスワード履歴、アクセス権限を削除
            User.objects.filter(pk__in=delete_user_list).delete()
            PasswordHistory.objects.filter(user_id__in=delete_user_list).delete()
            AccessPermission.objects.filter(group_id__in=group_id_list_del).delete()

    except Exception as e:
        logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
        msg = get_message('MOSJA23021', request.user.get_lang_mode()) + '\\n' + str(e.args)
        response = {}
        response['status'] = 'failure'
        response['msg'] = msg
        response['error_msg'] = error_msg
        response_json = json.dumps(response)
        return HttpResponse(response_json, content_type="application/json")

    redirect_url = '/oase_web/system/group'
    response_json = '{"status": "success", "redirect_url": "%s"}' % redirect_url

    logger.logic_log('LOSI00002', 'None', request=request)

    return HttpResponse(response_json, content_type="application/json")


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_EVERY)
def data(request):
    """
    [メソッド概要]
      グループのデータ取得
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    msg = ''
    group_list = []

    # メンテナンス権限チェック
    permission_type = request.user_config.get_menu_auth_type(MENU_ID)
    editable_user = True if permission_type == defs.ALLOWED_MENTENANCE else False

    try:
        filters = {}
        group_list = _select(filters)

    except BaseException:
        logger.logic_log('LOSM00001', traceback.format_exc(), request=request)
        msg = get_message('MOSJA23018', request.user.get_lang_mode(), showMsgId=False)

    data = {
        'msg': msg,
        'editable_user': editable_user,
        'group_list': group_list,
        'mainmenu_list': request.user_config.get_menu_list(),
        'opelist_add': defs.DABASE_OPECODE.OPELIST_ADD,
        'opelist_mod': defs.DABASE_OPECODE.OPELIST_MOD,
        'actdirflg': System.objects.get(config_id='ADCOLLABORATION').value,
        'user_name': request.user.user_name,
        'lang_mode': request.user.get_lang_mode(),
    }

    logger.logic_log('LOSI00002', 'editable_user: %s, group_list count: %s' %
                     (editable_user, len(group_list)), request=request)

    return render(request, 'system/group_data_edit.html', data)


def _select(filters={}):
    """
    [メソッド概要]
      グループのデータ取得
    """
    logger.logic_log('LOSI00001', 'filters: %s' % (filters))

    # グループ情報取得
    where_info = {}
    WebCommon.convert_filters(filters, where_info)
    group = Group.objects.filter(**where_info)
    group = group.filter(group_id__gte=1).order_by('group_id')

    # グループ情報作成
    group_list = []
    for g in group:
        group_info_dic                        = {}
        group_info_dic['group_id']            = g.group_id
        group_info_dic['group_name']          = g.group_name
        group_info_dic['summary']             = g.summary
        group_info_dic['last_timestamp']      = g.last_update_timestamp
        group_info_dic['last_update_user']    = g.last_update_user

        group_info_dic['summary_outline']     = ''
        hasBreakLine = True if len(g.summary.splitlines()) > 2 else False
        max_str_length = 20 # セル幅と相談
        if hasBreakLine:
            group_info_dic['summary_outline'] = g.summary.splitlines()[0][:max_str_length]
        elif len(g.summary) > max_str_length: 
            group_info_dic['summary_outline'] = g.summary[:max_str_length]

        group_list.append(group_info_dic)

    return group_list


def _validate(records, request):
    """
    入力チェック
    """
    error_flag = False
    error_msg = {}
    chk_list = []

    for r in records:
        error_msg[r['row_id']] = {'group_name': '', 'summary': ''}
        lang = request.user.get_lang_mode()
        data = {
            'group_name': r['group_name'],
            'summary': r['summary'],
        }
        f = GroupForm(data)

        # 入力値チェック
        if len(f.errors.items()):
            error_flag = True
            for content, validate_list in f.errors.items():
                error_msg[r['row_id']][content] = '\n'.join([get_message(v, lang) for v in validate_list])

        # 入力エラーがなければ重複チェック
        if chk_list.count(r['group_name']) > 0:
            error_flag = True
            error_msg[r['row_id']]['group_name'] += get_message('MOSJA23020', lang) + '\n'
            logger.user_log('LOSM04003', 'group_name', r['group_name'], request=request)

        elif error_msg[r['row_id']]['group_name'] != '':
            duplication = Group.objects.filter(group_name=r['group_name'])

            if len(duplication) == 1 and int(r['group_id']) != duplication[0].group_id:
                error_flag = True
                error_msg[r['row_id']]['group_name'] += get_message('MOSJA23020', lang) + '\n'
                logger.user_log('LOSM04003', 'group_name', r['group_name'], request=request)

        chk_list.append(r['group_name'])

    return error_flag, error_msg


def _bulk_create_access_permission(user_name, group_names, now):
    """
    アクセス権限を複数追加する
    """
    permissions = []
    inserted_groups = Group.objects.filter(group_name__in=group_names)

    for inserted_group in inserted_groups:
        for menu_id in defs.MENU:
            # アクセス権限を設定する必要のないメニューは登録しない
            if menu_id in [2141001007, 2141003003, 2141003004, 2141003005, 2141003006]:
                continue

            permission_type_id = defs.ALLOWED_MENTENANCE if menu_id == 2141003001 else defs.NO_AUTHORIZATION
            instance = AccessPermission(
                group_id=inserted_group.group_id,
                menu_id=menu_id,
                permission_type_id=permission_type_id,
                last_update_user=user_name,
                last_update_timestamp=now,
            )
            permissions.append(instance)

    AccessPermission.objects.bulk_create(permissions)
