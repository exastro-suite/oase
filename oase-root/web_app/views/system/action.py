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
    "アクション設定"アイテムの画面コントローラ

"""


import json
import requests
import traceback

from importlib import import_module

from django.shortcuts import render
from django.http import HttpResponse
from django.db import transaction

from libs.commonlibs import define as defs
from libs.commonlibs.oase_logger import OaseLogger
from libs.webcommonlibs.decorator import *

from web_app.models.models import ActionType, DriverType
from web_app.templatetags.common import get_message

class ActionDriverSupportTool():

    @classmethod
    def get_driver_info(cls, driver_info):

        drv_module = import_module(driver_info['module'])
        drv_class  = getattr(drv_module, driver_info['class'])

        clazz = drv_class(driver_info['drv_id'], driver_info['act_id'], driver_info['name'], driver_info['ver'], driver_info['icon_name'])

        clazz_info = {}
        clazz_info['name'] = clazz.get_driver_name()
        clazz_info['driver_id'] = clazz.get_driver_id()
        clazz_info['driver_template_file'] = clazz.get_template_file()
        clazz_info['info_list'] = clazz.get_info_list()
        clazz_info['define'] = clazz.get_define()
        clazz_info['icon_name'] = clazz.get_icon_name()

        return clazz_info

    @classmethod
    def get_driver_data_modify(cls, driver_info):

        drv_module = import_module(driver_info['module'])
        drv_class  = getattr(drv_module, driver_info['class'])

        clazz = drv_class(driver_info['drv_id'], driver_info['act_id'], driver_info['name'], driver_info['ver'], driver_info['icon_name'])

        clazz_info = {}
        clazz_info['driver_id'] = clazz.get_driver_id()
        clazz_info['driver_data_modify_function'] = clazz.modify # function object
        clazz_info['driver_record_lock_function'] = clazz.record_lock # function object

        return clazz_info


MENU_ID = 2141002007

logger = OaseLogger.get_instance() # ロガー初期化

################################################
@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_EVERY)
def action(request):

    logger.logic_log('LOSI00001', 'None', request=request)

    #メンテナンス権限チェック
    permission_type = request.user_config.get_menu_auth_type(MENU_ID)
    editable_user = True if permission_type == defs.ALLOWED_MENTENANCE else False

    use_drivers = _get_available_drivers()

    msg = ''
    driver_list = []
    try:
        for ud in use_drivers:
            driver_info = ActionDriverSupportTool.get_driver_info(ud)

            driver_list.append(driver_info)

    except Exception as e:
        logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
        msg = get_message('MOSJA27008', request.user.get_lang_mode())

    data = {
        'msg'          : msg,
        'driver_list'  : driver_list,
        'editable_user': editable_user,
        'mainmenu_list': request.user_config.get_menu_list(),
        'opelist_add'  : defs.DABASE_OPECODE.OPELIST_ADD,
        'opelist_mod'  : defs.DABASE_OPECODE.OPELIST_MOD,
        'user_name'    : request.user.user_name,
        'lang_mode'    : request.user.get_lang_mode(),
    }

    logger.logic_log('LOSI00002', 'data=%s' % data, request=request)

    return render(request, 'system/action.html', data)


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
def modify(request):

    logger.logic_log('LOSI00001', 'None', request=request)

    use_drivers = _get_available_drivers()
    logger.logic_log('LOSI07001', use_drivers, request=request)

    # 成功時レスポンスデータ
    redirect_url = '/oase_web/system/action'
    response = {
            "status": "success",
            "redirect_url": redirect_url,
        }

    msg = ''
    try:
        if request and request.method != 'POST':
            logger.logic_log('LOSM04004', request=request)
            msg = get_message('MOSJA27010', request.user.get_lang_mode())
            return HttpResponseServerError(msg)

        json_str = request.POST.get('json_str', '{}')
        json_str = json.loads(json_str)
        if 'json_str' not in json_str:
            msg = get_message('MOSJA27010', request.user.get_lang_mode())
            logger.user_log('LOSM04000', 'json_str', request=request)
            raise Exception()

        with transaction.atomic():

            for ud in use_drivers:
                # 必要情報取得
                driver_info = ActionDriverSupportTool.get_driver_data_modify(ud)

                if str(driver_info['driver_id']) != json_str['json_str']["driver_id"]:
                    continue

                record_lock_function = driver_info['driver_record_lock_function']
                modify_func = driver_info['driver_data_modify_function']

                # 関連TBLにロックかける
                record_lock_function(json_str, request)
                # 更新 or 追加 or 削除処理
                each_driver_response = modify_func(json_str, request)

                if each_driver_response['status'] != 'success':
                    response['status'] = 'failure'
                    response['error_msg'] = each_driver_response.get('error_msg', {})

            # 最終的にfailure扱いであればロールバック
            if response['status'] == 'failure':
                transaction.rollback()

    except Exception as e:
        logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
        if not msg:
            msg = get_message('MOSJA27009', request.user.get_lang_mode())
        response['status'] = 'failure'
        response['msg'] = msg              # alertで出すメッセージ
        #response['error_msg'] = error_msg  # エラー詳細(エラーアイコンで出す)

    response_json = json.dumps(response)
    logger.logic_log('LOSI00002', 'status=%s' % response['status'], request=request)

    return HttpResponse(response_json, content_type="application/json")

def _get_available_drivers():

    driver_cls_list = []

    # インストール済みドライバーを取得
    driver_type_list = []
    act_types = ActionType.objects.filter(disuse_flag=str(defs.ENABLE)).values('action_type_id', 'driver_type_id')
    for at in act_types:
        driver_type_list.append(at['driver_type_id'])

    drv_types = []
    if len(driver_type_list) > 0:
        drv_types = DriverType.objects.filter(driver_type_id__in=driver_type_list).values('driver_type_id', 'name', 'driver_major_version', 'icon_name')

    for at in act_types:
        for dt in drv_types:
            if at['driver_type_id'] != dt['driver_type_id']:
                continue

            module_name = 'web_app.views.system.%s.action_%s' % (dt['name'], dt['name'])
            class_name  = '%sDriverInfo' % (dt['name'])

            drv_info = {}
            drv_info['module'] = module_name
            drv_info['class']  = class_name
            drv_info['drv_id'] = dt['driver_type_id']
            drv_info['act_id'] = at['action_type_id']
            drv_info['name']   = dt['name']
            drv_info['ver']    = dt['driver_major_version']
            drv_info['icon_name'] = dt['icon_name']

            driver_cls_list.append(drv_info)


    return driver_cls_list


