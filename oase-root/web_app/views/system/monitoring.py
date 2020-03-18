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
    "監視アダプタ"アイテムの画面コントローラ

"""


import json
import requests
import traceback

from importlib import import_module

from django.shortcuts import render
from django.http import HttpResponse
from django.db import transaction
from django.views.decorators.http import require_POST

from libs.commonlibs import define as defs
from libs.commonlibs.oase_logger import OaseLogger
logger = OaseLogger.get_instance() # ロガー初期化
from libs.webcommonlibs.decorator import *

from web_app.models.models import MonitoringType, AdapterType, RuleType, DataObject
from web_app.templatetags.common import get_message

from web_app.views.rule.decision_table import DecisionTableAuthByRule


class MonitoringAdapterSupportTool():

    @classmethod
    def get_adapter_disp_info(cls, adapter_cls_info, request):

        adapter_module = import_module(adapter_cls_info['module'])
        adapter_class  = getattr(adapter_module, adapter_cls_info['class'])

        adapter = adapter_class(adapter_cls_info['adp_id'], adapter_cls_info['mni_id'], adapter_cls_info['name'], adapter_cls_info['ver'], adapter_cls_info['icon_name'])

        adapter_disp_info = {}
        adapter_disp_info['name'] = adapter.get_adapter_name()
        adapter_disp_info['adapter_id'] = adapter.get_adapter_id()
        adapter_disp_info['adapter_template_file'] = adapter.get_template_file()
        adapter_disp_info['info_list'] = adapter.get_info_list(request)
        adapter_disp_info['define'] = adapter.get_define()
        adapter_disp_info['icon_name'] = adapter.get_icon_name()
        adapter_disp_info['zabbix_items'] = adapter.get_zabbix_items()

        return adapter_disp_info

    @classmethod
    def get_adapter_data_modify(cls, adapter_cls_info):

        adapter_module = import_module(adapter_cls_info['module'])
        adapter_class  = getattr(adapter_module, adapter_cls_info['class'])

        class_ = adapter_class(adapter_cls_info['adp_id'], adapter_cls_info['mni_id'], adapter_cls_info['name'], adapter_cls_info['ver'], adapter_cls_info['icon_name'])

        adapter_modify_info = {
            'adapter_id' : adapter_cls_info['adp_id'],
            'adapter_data_create_function' : class_.create, # function object
            'adapter_data_delete_function' : class_.delete, # function object
            'adapter_data_update_function' : class_.update, # function object
            'adapter_record_lock_function' : class_.record_lock, # function object
        }

        return adapter_modify_info

    @classmethod
    def get_adapter_modify_data(cls, adapter_cls_info):
        """
        adapterクラスを返す
        """
        adapter_module = import_module(adapter_cls_info['module'])
        adapter_class  = getattr(adapter_module, adapter_cls_info['class'])

        result = adapter_class(
            adapter_cls_info['adp_id'],
            adapter_cls_info['mni_id'],
            adapter_cls_info['name'],
            adapter_cls_info['ver'],
            adapter_cls_info['icon_name'],
        )

        return result


MENU_ID = 2141002006


################################################
@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_EVERY)
def monitoring(request):

    logger.logic_log('LOSI00001', 'None', request=request)

    #メンテナンス権限チェック
    permission_type = request.user_config.get_menu_auth_type(MENU_ID)
    editable_user = True if permission_type == defs.ALLOWED_MENTENANCE else False

    use_adapters = _get_available_adapters()

    msg = ''
    adapter_list = []
    rule_type_data_obj_dict = {}
    rule_type_list = []
    try:
        # アダプタ情報取得
        for ua in use_adapters.values():
            adapter_disp_info = MonitoringAdapterSupportTool.get_adapter_disp_info(ua, request)

            adapter_list.append(adapter_disp_info)
            
        # ルール取得
        rule_type_data_obj_dict = get_rule_type_data_obj_dict(request)
        rule_type_list = rule_type_data_obj_dict.values()

    except Exception as e:
        logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
        msg = get_message('MOSJA26008', request.user.get_lang_mode())

    data = {
        'msg'           : msg,
        'adapter_list'  : adapter_list,
        'rule_type_list': rule_type_list,
        'rule_type_data_obj_dict': rule_type_data_obj_dict,
        'editable_user' : editable_user,
        'mainmenu_list' : request.user_config.get_menu_list(),
        'user_name'     : request.user.user_name,
        'lang_mode'     : request.user.get_lang_mode(),
    }

    logger.logic_log('LOSI00002', 'data=%s' % data, request=request)

    return render(request, 'system/monitoring.html', data)


def get_json_str(request):
    """
    requestデータからjson_strを取得する。
    [引数]
    request: request情報
    [戻り値]
    json_str: dict requestから取得したjson_str
    """

    json_str = request.POST.get('json_str', '{}')
    json_str = json.loads(json_str)
    if 'json_str' not in json_str:
        logger.user_log('LOSM04000', 'json_str', request=request)
        raise Exception

    return json_str


def get_adapter_id(json_str):
    """
    json_strからadapter_idを取得する
    [引数]
    json_str: dict get_json_str()で取得したjson_str
    [戻り値]
    adapter_id: int
    """
    # adapter_id チェック 
    adapter_id = json_str['json_str'].get('adapter_id')
    if adapter_id == None:
        logger.user_log('LOSM04000', 'adapter_id')
        raise Exception

    return adapter_id


################################################
@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
def create(request):

    logger.logic_log('LOSI00001', 'None', request=request)
    lang = request.user.get_lang_mode()
    json_str = None
    adapter_id = None

    # リクエスト情報取得
    try:
        json_str = get_json_str(request)
        adapter_id = get_adapter_id(json_str)
    except Exception as e:
        logger.logic_log('LOSM04008', request=request)
        response = {
            'status': 'failure',
            'msg': get_message('MOSJA26009', lang),
        }
        response_json = json.dumps(response)
        return HttpResponse(response_json, content_type="application/json")

    # 指定されたadapterのクラス情報取得
    use_adapters = _get_available_adapters()
    adapter_class = MonitoringAdapterSupportTool.get_adapter_modify_data(use_adapters[adapter_id])

    # 更新 
    result = _modify(request, json_str, adapter_class.create)

    logger.logic_log('LOSI00002', result, request=request)
    return result


################################################
@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def update(request):

    logger.logic_log('LOSI00001', 'None', request=request)
    lang = request.user.get_lang_mode()
    json_str = None
    adapter_id = None

    # リクエスト情報取得
    try:
        json_str = get_json_str(request)
        adapter_id = get_adapter_id(json_str)
    except Exception as e:
        logger.logic_log('LOSM04008', request=request)
        response = {
            'status': 'failure',
            'msg': get_message('MOSJA26009', lang),
        }
        response_json = json.dumps(response)
        return HttpResponse(response_json, content_type="application/json")

    # 指定されたadapterのクラス情報取得
    use_adapters = _get_available_adapters()
    adapter_class = MonitoringAdapterSupportTool.get_adapter_modify_data(use_adapters[adapter_id])

    # 更新 
    result = _modify(request, json_str, adapter_class.update)

    logger.logic_log('LOSI00002', result, request=request)
    return result


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def delete(request):

    logger.logic_log('LOSI00001', 'None', request=request)
    lang = request.user.get_lang_mode()
    json_str = None
    adapter_id = None

    # リクエスト情報取得
    try:
        json_str = get_json_str(request)
        adapter_id = get_adapter_id(json_str)
    except Exception as e:
        logger.logic_log('LOSM04008', request=request)
        response = {
            'status': 'failure',
            'msg': get_message('MOSJA26009', lang),
        }
        response_json = json.dumps(response)
        return HttpResponse(response_json, content_type="application/json")

    # 指定されたadapterのクラス情報取得
    use_adapters = _get_available_adapters()
    adapter_class = MonitoringAdapterSupportTool.get_adapter_modify_data(use_adapters[adapter_id])

    # 削除
    result = _modify(request, json_str, adapter_class.delete)

    logger.logic_log('LOSI00002', result, request=request)
    return result

################################################
def _modify(request, json_str, modify_func):

    logger.logic_log('LOSI00001', 'None', request=request)
    lang = request.user.get_lang_mode()

    # 成功時レスポンスデータ
    redirect_url = '/oase_web/system/monitoring'
    response = {
            "status": "success",
            "msg": "",
            "redirect_url": redirect_url,
        }
    try:
        with transaction.atomic():

            # 更新 or 追加 or 削除処理
            adapter_response = modify_func(json_str['json_str'], request)

            if adapter_response['status'] != 'success':
                response['status'] = adapter_response.get('status', "failure")
                response['msg'] = adapter_response.get('msg', "")

                transaction.rollback()

    except Exception as e:
        logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
        if not response['msg']:
            response['msg'] = get_message('MOSJA26010', lang)
        if not response['status'] or response['status'] == 'success':
            response['status'] = 'failure'

    response_json = json.dumps(response)
    logger.logic_log('LOSI00002', 'status=%s' % response['status'], request=request)

    return HttpResponse(response_json, content_type="application/json")


def _get_available_adapters():

    adapter_cls_dict = {}

    # インストール済みドライバーを取得
    adapter_type_list = []
    mni_types = MonitoringType.objects.filter(disuse_flag=str(defs.ENABLE)).values('monitoring_type_id', 'adapter_type_id')
    for mt in mni_types:
        adapter_type_list.append(mt['adapter_type_id'])

    adp_types = []
    if len(adapter_type_list) > 0:
        adp_types = AdapterType.objects.filter(adapter_type_id__in=adapter_type_list).values('adapter_type_id', 'name', 'adapter_major_version', 'icon_name')

    for mt in mni_types:
        for at in adp_types:
            if mt['adapter_type_id'] != at['adapter_type_id']:
                continue

            module_name = 'web_app.views.system.monitoring_%s.monitoring_%s' % (at['name'], at['name'])
            class_name  = '%sAdapterInfo' % (at['name'])

            adp_cls_info = {}
            adp_cls_info['module'] = module_name
            adp_cls_info['class']  = class_name
            adp_cls_info['adp_id'] = at['adapter_type_id']
            adp_cls_info['mni_id'] = mt['monitoring_type_id']
            adp_cls_info['name']   = at['name']
            adp_cls_info['ver']    = at['adapter_major_version']
            adp_cls_info['icon_name'] = at['icon_name']

            adapter_cls_dict[at['adapter_type_id']] = adp_cls_info

    logger.logic_log('LOSI07001', adapter_cls_dict)
    return adapter_cls_dict


def get_rule_type_data_obj_dict(request):
    """
    [メソッド概要]
      更新権限ありルール種別取得
      また紐づくDataObjectも辞書形式で取得する
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    rule_type_dict = {}

    try:
        # ログインしているユーザが表示/更新できるルールIDを取得
        dt_rule_ids_disp = request.user_config.get_rule_auth_type(MENU_ID)[defs.VIEW_ONLY]
        dt_rule_ids_edit = request.user_config.get_rule_auth_type(MENU_ID)[defs.ALLOWED_MENTENANCE]
        dt_rule_ids_disp = dt_rule_ids_disp + dt_rule_ids_edit
        dt_rule_ids_active = request.user_config.get_activerule_auth_type(MENU_ID)[defs.VIEW_ONLY]
        dt_rule_ids_active = dt_rule_ids_active + request.user_config.get_activerule_auth_type(MENU_ID)[defs.ALLOWED_MENTENANCE]
        # データオブジェクト取得
        data_obj_list = list(DataObject.objects.filter(rule_type_id__in=dt_rule_ids_disp).values('rule_type_id', 'data_object_id', 'conditional_name'))

        # ルール種別IDとルール種別名を辞書形式で保存
        rule_type_list = RuleType.objects.filter(rule_type_id__in=dt_rule_ids_disp)

        # TODO 後でログIDふり直す
        log_msg = 'dt_rule_ids_disp: %s, dt_rule_ids_edit: %s' % (dt_rule_ids_disp, dt_rule_ids_edit)
        logger.logic_log('LOSI11000', log_msg, request=request)

        for rule_type in rule_type_list:
            rule_type_dict[rule_type.rule_type_id] = {
                    'rule_type_id' : rule_type.rule_type_id,
                    'rule_type_name' : rule_type.rule_type_name,
                    'data_obj' : {data_obj['data_object_id']: data_obj['conditional_name']
                                    for data_obj in data_obj_list
                                    if data_obj['rule_type_id'] == rule_type.rule_type_id},
                    'editable' : True if rule_type.rule_type_id in dt_rule_ids_edit else False,
                    'active' : True if rule_type.rule_type_id in dt_rule_ids_active else False,
                }

    except Exception as e:
        # ここでの例外は大外で拾う
        raise

    logger.logic_log('LOSI00002', 'rule_type=%s' % rule_type_dict.keys(), request=request)

    return rule_type_dict
