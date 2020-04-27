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
  メッセージ解析ページの表示処理
  また、メッセージ解析からのリクエスト受信処理

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

from importlib import import_module

from django.http import HttpResponse, Http404
from django.shortcuts import render,redirect
from django.db import transaction
from django.views.decorators.http import require_POST
from django.conf import settings
from django.urls import reverse

from libs.commonlibs import define as defs
from libs.commonlibs.oase_logger import OaseLogger
from libs.commonlibs.common import Common

from libs.webcommonlibs.decorator import *
from libs.webcommonlibs.password  import RandomPassword
from libs.webcommonlibs.oase_mail import *
from libs.webcommonlibs.common import Common as WebCommon
from web_app.models.models import ActionType, DriverType
from web_app.templatetags.common import get_message
from web_app.serializers.unicode_check import UnicodeCheck
from web_app.views.forms.ita_parameter_match_info_form import ItaParameterMatchInfoForm


logger = OaseLogger.get_instance() # ロガー初期化

MENU_ID = 2141002007


def _get_param_match_info(version, perm_types, user_groups, request=None):
    """
    [メソッド概要]
      指定バージョンに紐づくITAパラメータ抽出条件情報を取得
    [引数]
      version     : ITAドライバーのバージョン
      perm_types  : 取得対象の権限リスト
      user_groups : ユーザー所属グループリスト
      request     : ログ出力用情報(ユーザーID、セッションID)
    [戻り値]
      data_list : list : メッセージ解析情報取得のリスト
      drv_info  : dict : アクション設定されたドライバーのID/名前
    """

    logger.logic_log(
        'LOSI00001',
        'version:%s, perm_types:%s, user_groups:%s' % (
            version, perm_types, user_groups
        ),
        request=request
    )

    # インストールドライバー取得
    rcnt = ActionType.objects.filter(driver_type_id=defs.ITA, disuse_flag='0').count()
    if rcnt <= 0:
        logger.user_log('LOSI27000', defs.ITA, request=request)
        raise Http404

    rset = DriverType.objects.filter(driver_type_id=defs.ITA, driver_major_version=version)
    drv_names = list(rset.values_list('name', flat=True))
    if len(drv_names) <= 0:
        logger.system_log('LOSM27000', defs.ITA, version, request=request)
        raise Http404


    # バージョンが1以上の場合は、ドライバー名にバージョン番号を付与
    drv_name = drv_names[0].capitalize()
    if version > 1:
        drv_name = '%s%s' % (drv_name, version)

    # ドライバー名からアクション設定モジュール名、権限モジュール名をセット
    drv_module_name = '%sDriver' % (drv_name)
    perm_module_name = '%sPermission' % (drv_name)

    # モジュール名からアクション設定モジュールと権限モジュールを取得
    module = import_module('web_app.models.ITA_models')
    drv_module = getattr(module, drv_module_name, None)

    if not drv_module:
        logger.user_log('LOSI27001', drv_module_name, request=request)
        raise Http404

    perm_module = getattr(module, perm_module_name, None)

    if not perm_module:
        logger.user_log('LOSI27001', perm_module_name, request=request)
        raise Http404

    # ユーザー所属グループ別のアクセス可能ドライバーを取得
    enable_drv_ids = []
    if 1 not in user_groups:  # 1=システム管理グループ:全てのドライバーに対して更新権限を持つ
        rset = perm_module.objects.all()
        rset = rset.filter(group_id__in=user_groups)
        rset = rset.filter(permission_type_id__in=perm_types)
        enable_drv_ids = list(rset.values_list('ita_driver_id', flat=True).distinct())

    # アクション設定情報を取得
    drv_ids = []
    drv_info = {}

    rset = drv_module.objects.all()
    if 1 not in user_groups:  # 1=システム管理グループ:全てのドライバーに対して更新権限を持つ
        rset = drv_module.objects.filter(ita_driver_id__in=enable_drv_ids)

    drv_list = rset.values('ita_driver_id', 'ita_disp_name')
    for drv in drv_list:
        drv_ids.append(drv['ita_driver_id'])
        drv_info[drv['ita_driver_id']] = drv['ita_disp_name']

    # ITAメニュー名称を取得
    module_name2 = '%sMenuName' % (drv_name)
    ItaMenuName = getattr(module, module_name2, None)
    if not ItaMenuName:
        logger.user_log('LOSI27001', module_name2, request=request)
        raise Http404

    menu_ids = []
    menu_info = {}

    menu_list = ItaMenuName.objects.all().values('menu_group_id', 'menu_id', 'menu_group_name', 'menu_name')
    for menu in menu_list:
        menu_ids.append(menu['menu_id'])
        value = '%s:%s:%s:%s' % (menu['menu_group_id'], menu['menu_group_name'], menu['menu_id'], menu['menu_name'])
        menu_info[menu['menu_id']] = value

    # メッセージ解析情報取得
    data_list = []
    if len(drv_ids) > 0:
        # ドライバー名からITAパラメータ抽出条件モジュール名をセット
        module_name = '%sParameterMatchInfo' % (drv_name)

        # モジュール名からITAパラメータ抽出条件モジュールを取得
        drv_module = getattr(module, module_name, None)
        if not drv_module:
            logger.user_log('LOSI27001', module_name, request=request)
            raise Http404

        rset = drv_module.objects.filter(ita_driver_id__in=drv_ids)
        Itaname_dict = ItaMenuName.objects.values('ita_driver_id', 'menu_group_id', 'menu_id', 'menu_group_name', 'menu_name')

        for r in rset:
            data_info = {}
            data_info['match_id'] = r.match_id
            data_info['ita_driver_id'] = r.ita_driver_id
            data_info['ita_driver_name'] = drv_info[r.ita_driver_id] if r.ita_driver_id in drv_info else ''
            data_info['menu_id'] = r.menu_id

            disp_name = _make_disp_name(Itaname_dict, r.ita_driver_id, r.menu_id)
            if not disp_name:
                continue

            data_info['disp_name'] = disp_name
            data_info['parameter_name'] = r.parameter_name
            data_info['order'] = r.order
            data_info['conditional_name'] = r.conditional_name
            data_info['extraction_method1'] = r.extraction_method1
            data_info['extraction_method2'] = r.extraction_method2
            data_info['last_update_timestamp'] = r.last_update_timestamp
            data_info['last_update_user'] = r.last_update_user
            data_list.append(data_info)

    logger.logic_log('LOSI00002', 'drv_ids:%s, data_count:%s' % (drv_ids, len(data_list)), request=request)
    logger.logic_log('LOSI00002', menu_info, request=request)

    return data_list, drv_info, menu_info


def _make_disp_name(Itaname_dict, ita_driver_id, menu_id):
    """
    [メソッド概要]
      
    [引数]
      Itaname_dict : ITAメニュー名管理データ
      ita_driver_id : ITAドライバーID
      menu_id : メニューID
    [戻り値]
      disp_name : string : 結合文字列
      (メニューグループID:メニューグループ名:メニューID:メニュー名)
    """

    for r in Itaname_dict:
        if r['ita_driver_id'] == ita_driver_id and r['menu_id'] == menu_id:
            disp_name = '%s:%s:%s:%s' % (r['menu_group_id'], r['menu_group_name'], r['menu_id'], r['menu_name'])
            return disp_name

    return None


def _check_update_auth(request, version):
    """
    [メソッド概要]
      更新権限チェック
    """

    hasUpdateAuthority = True

    # インストールドライバー取得
    rcnt = ActionType.objects.filter(driver_type_id=defs.ITA, disuse_flag='0').count()
    if rcnt <= 0:
        logger.user_log('LOSI27000', defs.ITA, request=request)
        raise Http404

    rset = DriverType.objects.filter(driver_type_id=defs.ITA, driver_major_version=version)
    drv_names = list(rset.values_list('name', flat=True))
    if len(drv_names) <= 0:
        logger.system_log('LOSM27000', defs.ITA, version, request=request)
        raise Http404

    # バージョンが1以上の場合は、ドライバー名にバージョン番号を付与
    drv_name = drv_names[0].capitalize()
    if version > 1:
        drv_name = '%s%s' % (drv_name, version)

    # ITAメニュー名称を取得
    module_name = '%sPermission' % (drv_name)

    # モジュール名からアクション設定モジュールを取得
    module = import_module('web_app.models.ITA_models')

    ItaPermission = getattr(module, module_name, None)
    if not ItaPermission:
        logger.user_log('LOSI27001', module_name, request=request)
        raise Http404

    if 1 not in request.user_config.group_id_list:
        ItaPerm_list = ItaPermission.objects.filter(group_id__in=request.user_config.group_id_list).values_list('permission_type_id', flat=True)
        if defs.ALLOWED_MENTENANCE not in ItaPerm_list:
            hasUpdateAuthority = False

    return hasUpdateAuthority


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_EVERY)
def index(request, version):
    """
    [メソッド概要]
      メッセージ解析ページの一覧画面（参照モード）
    """

    logger.logic_log('LOSI00001', '', request=request)

    data_list = []
    driver_id_names = {}

    # アクセス権限取得
    permission_type = request.user_config.get_menu_auth_type(MENU_ID)
    editable_user = True if permission_type == defs.ALLOWED_MENTENANCE else False

    try:
        # メッセージ解析情報取得
        data_list, driver_id_names, ita_name_list = _get_param_match_info(
            version,
            [defs.VIEW_ONLY, defs.ALLOWED_MENTENANCE],
            request.user_config.group_id_list,
            request
        )

        if editable_user:
            hasUpdateAuthority = _check_update_auth(request, version)
        else:
            hasUpdateAuthority = False

    except Http404:
        raise Http404

    except Exception as e:
        logger.logic_log('LOSI00005', traceback.format_exc())

    # 応答情報作成
    data = {
        'param_list' : data_list,
        'version' : version,
        'mainmenu_list' : request.user_config.get_menu_list(),
        'user_name' : request.user.user_name,
        'lang_mode' : request.user.get_lang_mode(),
        'hasUpdateAuthority' : hasUpdateAuthority,
    }

    return render(request, 'system/action_analysis_disp.html', data)


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def edit(request, version):
    """
    [メソッド概要]
      メッセージ解析の編集画面
    """

    logger.logic_log('LOSI00001', '', request=request)

    data_list = []
    driver_id_names = {}

    # アクセス権限取得
    permission_type = request.user_config.get_menu_auth_type(MENU_ID)
    editable_user = True if permission_type == defs.ALLOWED_MENTENANCE else False

    try:
        # メッセージ解析情報取得
        data_list, driver_id_names, ita_name_list = _get_param_match_info(
            version,
            [defs.ALLOWED_MENTENANCE,],
            request.user_config.group_id_list,
            request
        )
        logger.logic_log('LOSI00001', ita_name_list, request=request)
    except Http404:
        raise Http404

    except Exception as e:
        logger.logic_log('LOSI00005', traceback.format_exc())

    # 応答情報作成
    data = {
        'param_list' : data_list,
        'version' : version,
        'driver_id_names' : driver_id_names,
        'ita_name_list' : ita_name_list,
        'opelist_add' : defs.DABASE_OPECODE.OPELIST_ADD,
        'opelist_mod' : defs.DABASE_OPECODE.OPELIST_MOD,
        'mainmenu_list' : request.user_config.get_menu_list(),
        'user_name' : request.user.user_name,
        'lang_mode' : request.user.get_lang_mode(),
    }

    return render(request, 'system/action_analysis_edit.html', data)


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def modify(request, version):
    """
    [メソッド概要]
      メッセージ解析のデータ更新処理
    """

    # パラメーターチェック
    logger.logic_log('LOSI00001', 'None', request=request)

    msg = ''
    error_msg = {}
    now = datetime.datetime.now(pytz.timezone('UTC'))

    try:
        with transaction.atomic():
            json_str = json.loads(request.POST.get('json_str', '{}'))
            if 'json_str' not in json_str:
                msg = get_message('MOSJA27010', request.user.get_lang_mode(), showMsgId=False)
                logger.user_log('LOSM27001', 'json_str', request=request)
                raise Exception()

            # 更新前にレコードロック
            message_update_list = [
                rq['match_id']
                for rq in json_str['json_str']
                if int(rq['ope']) in (defs.DABASE_OPECODE.OPE_UPDATE, defs.DABASE_OPECODE.OPE_DELETE)
            ]

            ItaParameterMatchInfo = getattr(import_module('web_app.models.ITA_models'), 'ItaParameterMatchInfo')
            ItaParameterMatchInfo.objects.select_for_update().filter(pk__in=message_update_list)

            # バリデーションチェック
            error_flag, error_msg = _validate(json_str['json_str'], version, request)
            if error_flag:
                raise Exception('validation error.')

            # 挿入/更新/削除振り分け
            match_id_list_reg = []
            match_id_list_mod = []
            match_id_list_del = []
            sorted_data = sorted(json_str['json_str'], key=lambda x: x['match_id'])
            upd_data = list(filter(lambda x: int(x['ope']) == defs.DABASE_OPECODE.OPE_UPDATE, sorted_data))
            del_data = list(filter(lambda x: int(x['ope']) == defs.DABASE_OPECODE.OPE_DELETE, sorted_data))
            ins_data = list(filter(lambda x: int(x['ope']) == defs.DABASE_OPECODE.OPE_INSERT, sorted_data))

            # 削除処理
            logger.user_log('LOSI27004', 'web_app.models.ITA_models', request=request)

            match_id_list_del = [rq['match_id'] for rq in del_data]
            ItaParameterMatchInfo.objects.filter(pk__in=match_id_list_del).delete()
            logger.user_log('LOSI27005', 'web_app.models.ITA_models', request=request)

            # 更新処理
            logger.user_log('LOSI27002', 'web_app.models.ITA_models', request=request)
            for rq in upd_data:
                match_id_list_mod = ItaParameterMatchInfo.objects.filter(match_id=rq['match_id'])
                if len(match_id_list_mod) <= 0:
                    logger.logic_log('LOSM27001', rq['parameter_name'], request=request)
                    continue

                match_id_list_mod[0].ita_driver_id = rq['ita_driver_id']
                match_id_list_mod[0].menu_id=rq['menu_id']
                match_id_list_mod[0].parameter_name=rq['parameter_name']
                match_id_list_mod[0].order=rq['order']
                match_id_list_mod[0].conditional_name=rq['conditional_name']
                match_id_list_mod[0].extraction_method1=rq['extraction_method1']
                match_id_list_mod[0].extraction_method2=rq['extraction_method2']
                match_id_list_mod[0].last_update_timestamp = now
                match_id_list_mod[0].last_update_user = request.user.user_name
                match_id_list_mod[0].save(force_update=True)
            logger.user_log('LOSI27003', 'web_app.models.ITA_models', request=request)

            # 挿入処理
            logger.user_log('LOSI27006', 'web_app.models.ITA_models', request=request)
            for rq in ins_data:
                match_info = ItaParameterMatchInfo(
                    ita_driver_id=rq['ita_driver_id'],
                    menu_id=rq['menu_id'],
                    parameter_name=rq['parameter_name'],
                    order=rq['order'],
                    conditional_name=rq['conditional_name'],
                    extraction_method1=rq['extraction_method1'],
                    extraction_method2=rq['extraction_method2'],
                    last_update_timestamp=now,
                    last_update_user=request.user.user_name
                )
                match_id_list_reg.append(match_info)
            ItaParameterMatchInfo.objects.bulk_create(match_id_list_reg)
            logger.user_log('LOSI27007', 'web_app.models.ITA_models', request=request)

    except Http404:
        raise Http404

    # 応答情報作成
    except Exception as e:
        logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
        msg = get_message('MOSJA27311', request.user.get_lang_mode()) + '\\n' + str(e.args)
        response = {}
        response['status'] = 'failure'
        response['msg'] = msg
        response['error_msg'] = error_msg
        response_json = json.dumps(response)
        return HttpResponse(response_json, content_type="application/json")

    redirect_url = reverse('web_app:system:paramsheet', args=[version, ])
    response_json = '{"status": "success", "redirect_url": "%s"}' % redirect_url

    logger.logic_log('LOSI00002', 'None', request=request)
    return HttpResponse(response_json, content_type="application/json")


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def select(request):
    """
    [メソッド概要]
      メニューグループ:メニューのプルダウンリスト作成処理
    """

    logger.logic_log('LOSI00001', 'None', request=request)
    msg = ''

    try:
        ita_driver_id = request.POST.get('ita_driver_id', None)
        version = request.POST.get('version', None)

        # パラメーターチェック
        if ita_driver_id is None or version is None:
            msg = get_message('MOSJA27310', request.user.get_lang_mode())
            logger.user_log('LOSM27002', ita_driver_id, version, request=request)
            raise Exception()

        ita_driver_id = int(ita_driver_id)
        version = int(version)

        # リクエストデータの妥当性チェック
        if ita_driver_id <= 0:
            msg = get_message('MOSJA27310', request.user.get_lang_mode())
            logger.user_log('LOSM27003', ita_driver_id, request=request)
            raise Exception()

        # インストールドライバー取得
        rcnt = ActionType.objects.filter(driver_type_id=defs.ITA, disuse_flag='0').count()
        if rcnt <= 0:
            logger.user_log('LOSI27000', defs.ITA, request=request)
            raise Http404

        rset = DriverType.objects.filter(driver_type_id=defs.ITA, driver_major_version=version)
        drv_names = list(rset.values_list('name', flat=True))
        if len(drv_names) <= 0:
            logger.system_log('LOSM27000', defs.ITA, version, request=request)
            raise Http404

        # バージョンが1以上の場合は、ドライバー名にバージョン番号を付与
        drv_name = drv_names[0].capitalize()
        if version > 1:
            drv_name = '%s%s' % (drv_name, version)

        # ITAメニュー名称を取得
        module_name = '%sMenuName' % (drv_name)

        # モジュール名からアクション設定モジュールを取得
        module = import_module('web_app.models.ITA_models')

        ItaMenuName = getattr(module, module_name, None)
        if not ItaMenuName:
            logger.user_log('LOSI27001', module_name, request=request)
            raise Http404

        # データ取得処理
        menu_dict = ItaMenuName.objects.filter(ita_driver_id=ita_driver_id).values(
            'menu_group_id', 'menu_id', 'menu_group_name', 'menu_name')

        # データ加工処理
        menu_info = {}
        menu_ids = []

        for menu in menu_dict:
            value = '%s:%s:%s:%s' % (menu['menu_group_id'], menu['menu_group_name'], menu['menu_id'], menu['menu_name'])
            menu_info[menu['menu_id']] = value

    except Http404:
        raise Http404

    except Exception as e:
        # 異常
        logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
        if msg == '':
            msg = get_message('MOSJA27330', request.user.get_lang_mode())
        response = {}
        response['status'] = 'failure'
        response['msg'] = msg
        response_json = json.dumps(response)
        return HttpResponse(response_json, content_type="application/json")

    # 正常
    response = {}
    response['status'] = 'success'
    response['menu_info'] = menu_info
    response_json = json.dumps(response)

    logger.logic_log('LOSI00002', 'None', request=request)
    return HttpResponse(response_json, content_type="application/json")


def _validate(records, version, request=None):
    """
    入力チェック
    """
    error_flag = False
    error_msg = {}

    lang = request.user.get_lang_mode() if request else getattr(settings, 'LANGUAGE_CODE', 'JA')
    drv_ids = []
    match_ids = []
    match_info = {}

    # 登録中のITAドライバーIDを取得する
    drv_name = 'Ita'
    if version > 1:
        drv_name = '%s%s' % (drv_name, version)

    module_name = '%sDriver' % (drv_name)
    module = import_module('web_app.models.ITA_models')
    drv_module = getattr(module, module_name, None)
    if not drv_module:
        logger.user_log('LOSI27001', module_name, request=request)
        raise Http404

    drv_ids = list(drv_module.objects.all().values_list('ita_driver_id', flat=True))

    # 登録中のITAパラメータ抽出条件IDを取得する
    module_name = '%sParameterMatchInfo' % (drv_name)
    module = import_module('web_app.models.ITA_models')
    drv_module = getattr(module, module_name, None)
    if not drv_module:
        logger.user_log('LOSI27001', module_name, request=request)
        raise Http404

    match_ids = list(drv_module.objects.all().values_list('match_id', flat=True))

    # 入力データのチェック
    for r in records:
        # エラーメッセージ初期化
        error_msg[r['row_id']] = {
            'ita_driver_id' : '',
            'menu_id' : '',
            'parameter_name' : '',
            'order' : '',
            'conditional_name' : '',
            'extraction_method1' : '',
            'extraction_method2' : '',
        }

        # 削除操作であればチェックしない
        if int(r['ope']) == defs.DABASE_OPECODE.OPE_DELETE:
            continue

        # 入力値チェック
        data = {
            'ita_driver_id' : r['ita_driver_id'],
            'menu_id' : r['menu_id'],
            'parameter_name' : r['parameter_name'],
            'order' : r['order'],
            'conditional_name' : r['conditional_name'],
            'extraction_method1' : r['extraction_method1'],
            'extraction_method2' : r['extraction_method2'],
        }

        f = ItaParameterMatchInfoForm(data)
        if len(f.errors.items()):
            error_flag = True
            for content, validate_list in f.errors.items():
                error_msg[r['row_id']][content] = '\n'.join([get_message(v, lang) for v in validate_list])

        # 更新操作であればIDチェック
        if int(r['ope']) == defs.DABASE_OPECODE.OPE_UPDATE and int(r['match_id']) not in match_ids:
            logger.user_log('LOSI27008', r['row_id'], r['match_id'], request=request)
            error_flag = True
            error_msg[r['row_id']]['ita_driver_id'] += get_message('MOSJA27312', lang) + '\n'
            continue

        # 指定のドライバーID存在チェック
        if int(r['ita_driver_id']) not in drv_ids:
            logger.user_log('LOSI27009', r['row_id'], r['ita_driver_id'], request=request)
            error_flag = True
            error_msg[r['row_id']]['ita_driver_id'] += get_message('MOSJA27313', lang) + '\n'
            continue

        # 入力エラーがなければ重複チェック
        if r['ita_driver_id'] in match_info \
        and r['menu_id'] in match_info[r['ita_driver_id']] \
        and r['order'] in match_info[r['ita_driver_id']][r['menu_id']]:
            match_info[r['ita_driver_id']][r['menu_id']][r['order']] += 1
            logger.user_log(
                'LOSI27010',
                r['row_id'],
                r['ita_driver_id'],
                r['menu_id'],
                r['order'],
                match_info[r['ita_driver_id']][r['menu_id']][r['order']],
                request=request
            )
            error_flag = True
            error_msg[r['row_id']]['ita_driver_id'] += get_message('MOSJA27314', lang) + '\n'
            continue

        if r['ita_driver_id'] not in match_info:
            match_info[r['ita_driver_id']] = {}

        if r['menu_id'] not in match_info[r['ita_driver_id']]:
            match_info[r['ita_driver_id']][r['menu_id']] = {}

        if r['order'] not in match_info[r['ita_driver_id']][r['menu_id']]:
            match_info[r['ita_driver_id']][r['menu_id']][r['order']] = 1

    return error_flag, error_msg
