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
  アクション履歴の表示処理

[引数]
  HTTPリクエスト

[戻り値]
  HTTPレスポンス

"""

import os
import traceback
import json
import pytz
import datetime
import urllib.parse
import ast
import re
from importlib import import_module

from django.shortcuts             import render, redirect
from django.http                  import HttpResponse
from django.db                    import transaction
from django.views.decorators.http import require_POST
from django.conf import settings

from libs.commonlibs              import define as defs
from libs.webcommonlibs.decorator import *
from libs.webcommonlibs.common    import TimeConversion
from libs.webcommonlibs.oase_exception import OASEError
from libs.commonlibs.oase_logger  import OaseLogger
from web_app.models.models        import ActionHistory, PreActionHistory
from web_app.models.models        import ActionType
from web_app.models.models        import ActionLog
from web_app.models.models        import RuleType
from web_app.models.models        import EventsRequest
from web_app.models.models        import RhdmResponse, RhdmResponseAction
from web_app.models.models        import DriverType

from web_app.templatetags.common import get_message


MENU_ID = 2141001003
#ロガー初期化
logger = OaseLogger.get_instance()

################################################
@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_EVERY)
def action_history(request):
    """
    [メソッド概要]
    アクション履歴画面の一覧表示
    """

    logger.logic_log('LOSI00001', 'none', request=request)
    msg = ''
    ita_flg = False
    mail_flg = False
    servicenow_flg = False
    filter_info = {
        'tblname'  : None,
        'rulename' : None,
    }

    try:
        # アクション画面のルール別アクセス権限を取得
        permission_info = request.user_config.get_rule_auth_type(MENU_ID)

        # アクセス可能なルール種別IDを取得
        rule_ids_view = permission_info[defs.VIEW_ONLY]
        rule_ids_admin = permission_info[defs.ALLOWED_MENTENANCE]
        rule_ids_all = rule_ids_view + rule_ids_admin 

        # アクション種別管理
        action_type_list    = ActionType.objects.all()

        # アクションステータス管理
        action_status_dict  = defs.ACTION_STATUS

        # ドライバ種別を取得
        driver_type_list = DriverType.objects.all()

        # ドライバインストール確認
        for act_type in action_type_list:
            if act_type.driver_type_id == 1 and act_type.disuse_flag == '0':
                ita_flg = True
            elif act_type.driver_type_id == 2 and act_type.disuse_flag == '0':
                mail_flg = True
            elif act_type.driver_type_id == 3 and act_type.disuse_flag == '0':
                servicenow_flg = True

        # アクション履歴を取得
        action_history_list = ActionHistory.objects.filter(rule_type_id__in=rule_ids_all).order_by('-pk') if len(rule_ids_all) > 0 else []

        # 表示用データ整備
        for act in action_history_list:
            # ルール種別の削除フラグを確認
            act.disuse_flag = RuleType.objects.get(rule_type_id=act.rule_type_id).disuse_flag

            # アイコン表示用文字列セット
            status = act.status
            if act.retry_status is not None:
                status = act.retry_status

            if status in defs.ACTION_HISTORY_STATUS.ICON_INFO:
                #承認中のものが削除された場合は処理済みとして取り扱う
                if act.disuse_flag != '0' and status == 6:
                    act.class_info = defs.ACTION_HISTORY_STATUS.ICON_INFO[8]
                else:
                    act.class_info = defs.ACTION_HISTORY_STATUS.ICON_INFO[status]
            else:
                act.class_info = {'status':'attention','name':'owf-attention','description':'MOSJA13063'}

        # フィルター情報を取得
        filter_info['tblname']  = request.GET.get('tblname')
        filter_info['rulename'] = request.GET.get('rulename')

    except Exception as e:
        msg = get_message('MOSJA13000', request.user.get_lang_mode())
        logger.logic_log('LOSM05000', 'traceback: %s' % traceback.format_exc(), request=request)

    data = {
        'message'             : msg,
        'action_type_list'    : action_type_list,
        'action_history_data' : action_history_list,
        'action_status_dict'  : action_status_dict,
        'action_info_dict'    : '',
        'request_info_dict'   : '',
        'action_log_list'     : '',
        'can_update'          : rule_ids_admin,
        'driver_type_list'    : driver_type_list,
        'ita_flg'             : ita_flg,
        'mail_flg'            : mail_flg,
        'servicenow_flg'      : servicenow_flg,
        'filter_info'         : filter_info,
    }

    data.update(request.user_config.get_templates_data(request))

    logger.logic_log('LOSI00002', 'none', request=request)
    return render(request, 'rule/action_history.html', data)


################################################
@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_EVERY)
def search_history(request):
    """
    [メソッド概要]
    アクション履歴画面の検索による一覧表示
    """

    logger.logic_log('LOSI00001', 'none', request=request)

    # 初期化
    msg                            = ''
    act_par_info_list              = []
    event_to_time_start            = ''
    event_to_time_end              = ''
    event_serial_number            = ''
    event_info                     = ''
    action_parameter_info          = ''
    action_start_time_start        = ''
    action_start_time_end          = ''
    history_serial_number          = ''
    rule_type_name                 = ''
    rule_name                      = ''
    ita_disp_name                  = ''
    symphony_instance_no           = ''
    symphony_class_id              = ''
    conductor_instance_no          = ''
    conductor_class_id             = ''
    operation_id                   = ''
    symphony_workflow_confirm_url  = ''
    conductor_workflow_confirm_url = ''
    restapi_error_info             = ''
    parameter_item_info            = ''
    mail_template_name             = ''
    mail_address                   = ''
    servicenow_disp_name           = ''
    ita_flg                        = False
    mail_flg                       = False
    servicenow_flg                 = False
    time_zone = settings.TIME_ZONE

    try:
        # アクション画面のルール別アクセス権限を取得
        permission_info = request.user_config.get_rule_auth_type(MENU_ID)

        # アクセス可能なルール種別IDを取得
        rule_ids_view = permission_info[defs.VIEW_ONLY]
        rule_ids_admin = permission_info[defs.ALLOWED_MENTENANCE]
        rule_ids_all = rule_ids_view + rule_ids_admin

        # アクション種別管理
        action_type_list    = ActionType.objects.all()

        # アクションステータス管理
        action_status_dict  = defs.ACTION_STATUS

        # ドライバ種別を取得
        driver_type_list = DriverType.objects.all()

        # ドライバインストール確認
        for act_type in action_type_list:
            if act_type.driver_type_id == 1 and act_type.disuse_flag == '0':
                ita_flg = True
            elif act_type.driver_type_id == 2 and act_type.disuse_flag == '0':
                mail_flg = True
            elif act_type.driver_type_id == 3 and act_type.disuse_flag == '0':
                servicenow_flg = True

        search_record = request.POST.get('search_record',"{}")
        search_record = json.loads(search_record)
        request_info  = search_record['request_info']
        action_info  = search_record['action_shared_info']
        action_type  = search_record['action_type']

        if request_info['request_event_start'] != '':
            event_to_time_start = TimeConversion.get_time_conversion_utc(
                request_info['request_event_start'], time_zone)
        else:
            event_to_time_start = '2000-01-01 00:00'

        if request_info['request_event_end'] != '':
            event_to_time_end = TimeConversion.get_time_conversion_utc(
                request_info['request_event_end'], time_zone)
        else:
            event_to_time_end = '2999-12-31 23:59'

        event_serial_number = request_info['request_trace_id']
        event_info          = request_info['request_infomation']

        if action_info['action_start'] != '':
            action_start_time_start = TimeConversion.get_time_conversion_utc(
                action_info['action_start'], time_zone)
        else:
            action_start_time_start = '2000-01-01 00:00'

        if action_info['action_end'] != '':
            action_start_time_end = TimeConversion.get_time_conversion_utc(
                action_info['action_end'], time_zone)
        else:
            action_start_time_end = '2999-12-31 23:59'

        history_serial_number = action_info['action_trace_id']
        rule_type_name = action_info['action_decision_table']
        rule_name = action_info['action_rule']
        action_parameter_info = action_info['action_parameter']

        # リクエスト管理
        evn_req_list = EventsRequest.objects.filter(
            event_to_time__gte=event_to_time_start,
            event_to_time__lte=event_to_time_end,
            trace_id__contains=event_serial_number,
            event_info__contains=event_info).order_by('-pk').values_list('trace_id', flat=True)

        # アクションパラメータ情報
        act_par_info_list = RhdmResponseAction.objects.filter(
            action_parameter_info__contains=action_parameter_info).order_by(
                '-pk').values_list('response_id', flat=True)

        if action_type['action_type'] == 'it-automation':
            # ITA
            action_ita_info = search_record['action_ita_info']
            ita_disp_name = action_ita_info['action_ita_name']
            symphony_instance_no = action_ita_info['action_symphony_instance']
            symphony_class_id = action_ita_info['action_symphony_class_id']
            conductor_instance_no = action_ita_info['action_conductor_instance']
            conductor_class_id = action_ita_info['action_conductor_class_id']
            operation_id = action_ita_info['action_ita_operation_id']
            symphony_workflow_confirm_url = action_ita_info['action_symphony_work_url']
            conductor_workflow_confirm_url = action_ita_info['action_conductor_work_url']
            restapi_error_info = action_ita_info['action_ita_restapi_info']
            parameter_item_info = action_ita_info['action_ita_cooperation']

            print(ita_disp_name)
            module = import_module('web_app.models.ITA_models')
            ItaActionHistory = getattr(module, 'ItaActionHistory')
            ita_act_his_list = ItaActionHistory.objects.filter(
                ita_disp_name__contains=ita_disp_name,
                symphony_workflow_confirm_url__contains=symphony_workflow_confirm_url,
                conductor_workflow_confirm_url__contains=conductor_workflow_confirm_url,
                parameter_item_info__contains=parameter_item_info).order_by('-pk').values_list('action_his_id', flat=True)

            if symphony_instance_no != '':
                ita_act_his_list = ItaActionHistory.objects.filter(
                    symphony_instance_no=symphony_instance_no).order_by('-pk').values_list('action_his_id', flat=True)

            if symphony_class_id != '':
                ita_act_his_list = ItaActionHistory.objects.filter(
                    symphony_class_id=symphony_class_id).order_by('-pk').values_list('action_his_id', flat=True)

            if conductor_instance_no != '':
                ita_act_his_list = ItaActionHistory.objects.filter(
                    conductor_instance_no=conductor_instance_no).order_by('-pk').values_list('action_his_id', flat=True)

            if conductor_class_id != '':
                ita_act_his_list = ItaActionHistory.objects.filter(
                    conductor_class_id=conductor_class_id).order_by('-pk').values_list('action_his_id', flat=True)

            if operation_id != '':
                ita_act_his_list = ItaActionHistory.objects.filter(
                    operation_id=operation_id).order_by('-pk').values_list('action_his_id', flat=True)

            if restapi_error_info != '':
                ita_act_his_list = ItaActionHistory.objects.filter(
                    restapi_error_info__contains=restapi_error_info
                ).order_by('-pk').values_list('action_his_id', flat=True)

            # アクション履歴
            action_history_list = ActionHistory.objects.filter(
                action_history_id__in=ita_act_his_list,
                trace_id__in=evn_req_list,
                action_start_time__gte=action_start_time_start,
                action_start_time__lte=action_start_time_end,
                trace_id__contains=history_serial_number,
                rule_type_name__contains=rule_type_name,
                rule_name__contains=rule_name,
                response_id__in=act_par_info_list).order_by('-pk') if len(rule_ids_all) > 0 else []

        elif action_type['action_type'] == 'mail':
            # mail
            action_mail_info = search_record['action_mail_info']
            mail_template_name = action_mail_info['action_mail_template']
            mail_address = action_mail_info['action_mail_destination']

            module = import_module('web_app.models.mail_models')
            MailActionHistory = getattr(module, 'MailActionHistory')
            mail_act_his_list = MailActionHistory.objects.filter(
                mail_template_name__contains=mail_template_name,
                mail_address__contains=mail_address).order_by('-pk').values_list('action_his_id', flat=True)

            # アクション履歴
            action_history_list = ActionHistory.objects.filter(
                action_history_id__in=mail_act_his_list,
                trace_id__in=evn_req_list,
                action_start_time__gte=action_start_time_start,
                action_start_time__lte=action_start_time_end,
                trace_id__contains=history_serial_number,
                rule_type_name__contains=rule_type_name,
                rule_name__contains=rule_name,
                response_id__in=act_par_info_list).order_by('-pk') if len(rule_ids_all) > 0 else []

        elif action_type['action_type'] == 'servicenow':
            # ServiceNow
            action_servicenow_info = search_record['action_servicenow_info']
            servicenow_disp_name = action_servicenow_info['action_servicenow_template']

            module = import_module('web_app.models.ServiceNow_models')
            ServiceNowActionHistory = getattr(module, 'ServiceNowActionHistory')
            ser_act_his_list = ServiceNowActionHistory.objects.filter(
                servicenow_disp_name__contains=servicenow_disp_name
            ).order_by('-pk').values_list('action_his_id', flat=True)

            # アクション履歴
            action_history_list = ActionHistory.objects.filter(
                action_history_id__in=ser_act_his_list,
                trace_id__in=evn_req_list,
                action_start_time__gte=action_start_time_start,
                action_start_time__lte=action_start_time_end,
                trace_id__contains=history_serial_number,
                rule_type_name__contains=rule_type_name,
                rule_name__contains=rule_name,
                response_id__in=act_par_info_list).order_by('-pk') if len(rule_ids_all) > 0 else []

        else:
            # アクション履歴
            action_history_list = ActionHistory.objects.filter(
                trace_id__in=evn_req_list,
                action_start_time__gte=action_start_time_start,
                action_start_time__lte=action_start_time_end,
                trace_id__contains=history_serial_number,
                rule_type_name__contains=rule_type_name,
                rule_name__contains=rule_name,
                response_id__in=act_par_info_list).order_by('-pk') if len(rule_ids_all) > 0 else []

        # 表示用データ整備
        for act in action_history_list:
            # ルール種別の削除フラグを確認
            act.disuse_flag = RuleType.objects.get(rule_type_id=act.rule_type_id).disuse_flag

            # アイコン表示用文字列セット
            status = act.status
            if act.retry_status is not None:
                status = act.retry_status

            if status in defs.ACTION_HISTORY_STATUS.ICON_INFO:
                #承認中のものが削除された場合は処理済みとして取り扱う
                if act.disuse_flag != '0' and status == 6:
                    act.class_info = defs.ACTION_HISTORY_STATUS.ICON_INFO[8]
                else:
                    act.class_info = defs.ACTION_HISTORY_STATUS.ICON_INFO[status]
            else:
                act.class_info = {'status':'attention','name':'owf-attention','description':'MOSJA13063'}

    except Exception as e:
        msg = get_message('MOSJA13000', request.user.get_lang_mode())
        logger.logic_log('LOSM05000', 'traceback: %s' % traceback.format_exc(), request=request)

    data = {
        'message'             : msg,
        'action_type_list'    : action_type_list,
        'action_history_data' : action_history_list,
        'action_status_dict'  : action_status_dict,
        'action_info_dict'    : '',
        'request_info_dict'   : '',
        'action_log_list'     : '',
        'can_update'          : rule_ids_admin,
        'driver_type_list'    : driver_type_list,
        'ita_flg'             : ita_flg,
        'mail_flg'            : mail_flg,
        'servicenow_flg'      : servicenow_flg,
    }

    data.update(request.user_config.get_templates_data(request))

    logger.logic_log('LOSI00002', 'none', request=request)
    return render(request, 'rule/action_history.html', data)


################################################
# 詳細画面
################################################
def dataobject(request, response_id, execution_order ):
    """
    [メソッド概要]
    アクション履歴画面の一覧表示
    """
    msg = ''
    req_shape_dic = {}
    act_shape_dic = {}
    log_message = []
    logger.logic_log('LOSI00001', 'response_id: %s, execution_order: %s' % (response_id, execution_order), request=request)
    lang = request.user.get_lang_mode()
    time_zone = settings.TIME_ZONE

    try:
        # ルール別アクセス権限チェック
        act_history_info = ActionHistory.objects.get(response_id=response_id, execution_order=execution_order)
        user_auth = request.user_config.get_menu_auth_type(MENU_ID, rule_type_id=act_history_info.rule_type_id)
        if user_auth not in defs.MENU_CATEGORY.ALLOW_EVERY:
            logger.user_log('LOSI13003', request.path, user_auth, defs.MENU_CATEGORY.ALLOW_EVERY)
            if 'HTTP_X_REQUESTED_WITH' in request.META and request.META['HTTP_X_REQUESTED_WITH'] == 'XMLHttpRequest':
                return HttpResponse(status=400)
            else:
                return HttpResponseRedirect(reverse('web_app:top:notpermitted'))


        # ログデータ取得
        err_flag, req_dic, act_dic, action_history_log_list = get_logdata(request, response_id, execution_order, act_history_info=act_history_info)
        if err_flag:
            logger.system_log('LOSM08001', 'req_dic: %s, act_dic: %s, action_history_log_list: %s' % (req_dic, act_dic, len(action_history_log_list)), request=request)
            msg = get_message('MOSJA13000', lang)
            raise Exception()


        #[リクエスト情報]
        req_shape_dic[get_message('MOSJA13002', lang, showMsgId=False)] = req_dic['req_time_stamp']
        req_shape_dic[get_message('MOSJA13003', lang, showMsgId=False)] = req_dic['req_trace_id']
        req_shape_dic[get_message('MOSJA13004', lang, showMsgId=False)] = req_dic['event_info']

        #[アクション情報]
        act_shape_dic[get_message('MOSJA13006', lang, showMsgId=False)] = act_dic['act_time_stamp']
        act_shape_dic[get_message('MOSJA13003', lang, showMsgId=False)] = act_dic['act_trace_id']
        act_shape_dic[get_message('MOSJA13007', lang, showMsgId=False)] = act_dic['rule_type_name']
        act_shape_dic[get_message('MOSJA13008', lang, showMsgId=False)] = act_dic['rule_name']
        act_shape_dic[get_message('MOSJA13010', lang, showMsgId=False)] = act_dic['action_parameter_info']

        # 各ドライバーのアクションの詳細を取得
        func = _get_get_history_data_func(act_history_info.action_type_id)
        history_data = func(act_history_info.pk)

        # ドライバー固有のアクション情報
        for k,v in history_data.items():
            act_shape_dic[get_message(k, lang, showMsgId=False)] = v

        #[ログ]    
        for log in action_history_log_list :
            msg_params = log.message_params
            if not msg_params:
                message    = get_message(log.message_id, lang)

            else:
                msg_params = ast.literal_eval(msg_params)
                message    = get_message(log.message_id, lang, **(msg_params))

            time_stamp = TimeConversion.get_time_conversion(log.last_update_timestamp, time_zone, request=request)
            message='[' + time_stamp +']'+ message
            log_message.append(message)

        data = {
            'message'             : msg,
            'action_info_dict'    : act_shape_dic,
            'request_info_dict'   : req_shape_dic,
            'action_log_list'     : log_message,
        }

        data.update(request.user_config.get_templates_data(request))

        logger.logic_log('LOSI00002', 'success', request=request)
        return render(request, 'rule/action_history_data.html', data)


    except Exception as e:
        logger.logic_log('LOSI00005', 'response_id: %s, execution_order: %s, trace: %s' % (response_id, execution_order, traceback.format_exc()), request=request)
        if not msg:
            msg = get_message('MOSJA13000', lang)

        data = {
            'message'             : msg,
            'action_info_dict'    : '',
            'request_info_dict'   : '',
            'action_log_list'     : '',
        }

        data.update(request.user_config.get_templates_data(request))

        response_json = json.dumps(data)
        return HttpResponse(response_json, content_type="application/json")

################################################
# ダウンロード処理
################################################
def download(request, response_id, execution_order):
    """
    [メソッド概要]
      アクションログダウンロード処理
    """
    logger.logic_log('LOSI00001', 'response_id: %s, execution_order: %s' % (response_id, execution_order), request=request)

    try:
        err_flag    = False
        log_message = ''
        log_txt     = ''
        lang = request.user.get_lang_mode()
        time_zone = settings.TIME_ZONE

        # ルール別アクセス権限チェック
        act_history_info = ActionHistory.objects.get(response_id=response_id, execution_order=execution_order)
        user_auth = request.user_config.get_menu_auth_type(MENU_ID, rule_type_id=act_history_info.rule_type_id)
        if user_auth not in defs.MENU_CATEGORY.ALLOW_EVERY:
            logger.user_log('LOSI13003', request.path, user_auth, defs.MENU_CATEGORY.ALLOW_EVERY)
            if 'HTTP_X_REQUESTED_WITH' in request.META and request.META['HTTP_X_REQUESTED_WITH'] == 'XMLHttpRequest':
                return HttpResponse(status=400)
            else:
                return HttpResponseRedirect(reverse('web_app:top:notpermitted'))

        # ログデータ取得
        err_flag, req_dic, act_dic, action_history_log_list = get_logdata(request, response_id, execution_order, act_history_info=act_history_info)

        if err_flag:
            logger.system_log('LOSM08001', 'req_dic: %s, act_dic: %s, action_history_log_list: %s' % (req_dic, act_dic, len(action_history_log_list)), request=request)
            return HttpResponse(request, status=500)

        # リクエスト情報整形
        log_message += '[' + get_message('MOSJA13001', lang, showMsgId=False) + ']' + '\n' \
                    + get_message('MOSJA13002', lang, showMsgId=False) + ':' + req_dic['req_time_stamp'] + '\n'  \
                    + get_message('MOSJA13003', lang, showMsgId=False) + ':' + req_dic['req_trace_id'] + '\n' \
                    + get_message('MOSJA13004', lang, showMsgId=False) + ':' + req_dic['event_info'] + '\n' \
                    + '\n'

        # アクション情報整形
        log_message += '[' + get_message('MOSJA13005', lang, showMsgId=False) + ']' + '\n' \
                    + get_message('MOSJA13006', lang, showMsgId=False) + ':' + act_dic['act_time_stamp'] + '\n'  \
                    + get_message('MOSJA13003', lang, showMsgId=False) + ':' + act_dic['act_trace_id'] + '\n'  \
                    + get_message('MOSJA13007', lang, showMsgId=False) + ':' + act_dic['rule_type_name'] + '\n'  \
                    + get_message('MOSJA13008', lang, showMsgId=False) + ':' + act_dic['rule_name'] + '\n'  \
                    + get_message('MOSJA13010', lang, showMsgId=False) + ':' + act_dic['action_parameter_info'] + '\n'  \

        # 各ドライバーのアクションの詳細を取得
        func = _get_get_history_data_func(act_history_info.action_type_id)
        history_data = func(act_history_info.pk)

        # ドライバー固有のアクション情報追記
        for k,v in history_data.items():
            if not v:
                v = ''
            log_message += get_message(k, lang, showMsgId=False) + ':' + str(v) + '\n'

        else:
            log_message += '\n'

        # action_history_listをループしながらテキストにいれる。
        if len(action_history_log_list) > 0:
            log_message += '[' + get_message('MOSJA13011', lang, showMsgId=False) + ']' + '\n'

        for action_log in action_history_log_list:
            msg_params = action_log.message_params
            if not msg_params:
                message = get_message(action_log.message_id, request.user.get_lang_mode())
            else:
                msg_params = ast.literal_eval(msg_params)
                message    = get_message(action_log.message_id, request.user.get_lang_mode(), **(msg_params))

            time_stamp = TimeConversion.get_time_conversion(action_log.last_update_timestamp, time_zone, request=request)
            log_message += '[%s] %s\n' % (time_stamp, message)

        # ダウンロード
        rule_name = act_dic['rule_type_name']
        act_type = act_dic['action_type_id']
        act_list = ActionType.objects.all()
        num = act_type-1
        act_typ = str(act_list[num])
        action_type =act_typ.split('(')[0]
        act_time = act_dic['act_time_stamp']
        action_time = (act_time.translate(str.maketrans({'-':'', '_':'' ,  ':':'' ,' ':''})))
        file_name   = 'Action_log_%s_%s_%s.txt' %(rule_name, action_type, action_time)

        response = HttpResponse(log_message, content_type='text/plain')
        response['Content-Disposition'] = "attachment; filename*=UTF-8''%s" % (urllib.parse.quote(file_name))

        logger.logic_log('LOSI00002', 'success', request=request)
        return response

    except Exception as e:
        logger.logic_log('LOSI00005', 'response_id: %s, execution_order: %s, trace: %s' % (response_id, execution_order, traceback.format_exc()), request=request)
        return HttpResponse(request, status=500)


################################################
# データ取得
################################################
def get_logdata(request, response_id, execution_order, act_history_info=None):
    """
    [メソッド概要]
      ログデータ取得処理
    [戻り値]
    err_flag: エラーフラグ
    req_dic： リクエスト情報
    act_dic： アクション情報
    action_history_log_list： アクションログ履歴
    """

    logger.logic_log('LOSI00001', 'response_id: %s, execution_order: %s' % (response_id, execution_order), request=request)

    try:
        err_flag = True
        req_dic = {}
        act_dic = {}
        action_history_log_list = []
        time_zone = settings.TIME_ZONE

        # requestからレスポンスIDとアクション実行順判定
        if not response_id or not execution_order:
            # 上記がNoneならエラー
            logger.system_log('LOSM08002',response_id, execution_order, request=request)
            return err_flag, req_dic, act_dic, action_history_log_list

        # アクション情報取得
        act_info = RhdmResponseAction.objects.get(response_id=response_id, execution_order=execution_order)
        if act_history_info is None:
            act_history_info = ActionHistory.objects.get(response_id=response_id, execution_order=execution_order)

        # リクエスト情報取得
        req_info         = EventsRequest.objects.get(trace_id=act_history_info.trace_id)

        # 日時の整形
        act_time_stamp   = TimeConversion.get_time_conversion(act_history_info.action_start_time, time_zone, request=request)
        req_time_stamp   = TimeConversion.get_time_conversion(req_info.event_to_time, time_zone, request=request)

        # リクエスト情報取得
        req_dic['req_time_stamp'] = req_time_stamp
        req_dic['req_trace_id']   = req_info.trace_id
        req_dic['event_info']     = req_info.event_info

        # アクション情報取得
        act_dic['act_time_stamp']        = act_time_stamp
        act_dic['act_trace_id']          = act_history_info.trace_id
        act_dic['rule_type_name']        = act_history_info.rule_type_name
        act_dic['action_type_id']        = act_history_info.action_type_id
        act_dic['rule_name']             = act_info.rule_name
        act_dic['action_parameter_info'] = act_info.action_parameter_info

        # アクションログ取得
        action_history_log_list = list(ActionLog.objects.filter(response_id=response_id, execution_order=execution_order).order_by('action_log_id'))


        err_flag = False
        logger.logic_log('LOSI00002', 'req_dic: %s, act_dic: %s, action_history_log_list: %s' % (req_dic, act_dic, len(action_history_log_list)), request=request)
        return err_flag, req_dic, act_dic, action_history_log_list

    except Exception as e:
        logger.logic_log('LOSI00005', 'response_id: %s, execution_order: %s, trace: %s' % (response_id, execution_order, traceback.format_exc()), request=request)
        return err_flag, req_dic, act_dic, action_history_log_list


def _validate_permission(request, act_his, msgid):
    """
     ルール別アクセス権限をチェック
     act_his : ActionHistoryオブジェクト
     msgid : 権限不正だった場合のmsgid
    """
    rule_ids = []
    for chk_auth in defs.MENU_CATEGORY.ALLOW_ADMIN:
        rule_ids.extend(request.user_config.get_rule_auth_type(MENU_ID, chk_auth))

    if act_his.rule_type_id not in rule_ids:
        raise OASEError(msgid, 'LOSI08003', msg_params={'rule_type_name':act_his.rule_type_name}, log_params=[act_his.rule_type_id, rule_ids])


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def retry(request):
    """
    アクションを再実行する
    """
    logger.logic_log('LOSI00001', 'none', request=request)
    now = datetime.datetime.now(pytz.timezone('UTC'))
    msg = ''
    action_history_id = 0 
    try:
        with transaction.atomic():
            action_history_id = request.POST.get('act_his_id', None)

            # ルール種別管理を確認し、削除フラグが立っている場合は処理を中断する！
            if _chk_disuse_flag(action_history_id) == False:
                raise OASEError('MOSJA13082', '')

            if action_history_id is None:
                msg = get_message('MOSJA13022', request.user.get_lang_mode(), showMsgId=False)

            act_his = ActionHistory.objects.select_for_update().get(action_history_id=action_history_id)

            # ルール別アクセス権限をチェック
            _validate_permission(request, act_his, 'MOSJA13017')

            # アクション履歴の再実行状態を更新
            if act_his.status != defs.PROCESSING or act_his.retry_status != defs.PROCESSING or act_his.retry_flag != True:
                act_his.retry_flag = True
                act_his.retry_status = defs.PROCESSING
                act_his.action_start_time = now 
                act_his.last_act_user = request.user.user_name
                act_his.last_update_timestamp = now
                act_his.save(force_update=True)

            else:
                # 実行中の場合
                msg = get_message('MOSJA13013', request.user.get_lang_mode(), showMsgId=False)

    except OASEError as e:
        if e.log_id:
            if e.arg_list and isinstance(e.arg_list, list):
                logger.logic_log(e.log_id, *(e.arg_list), request=request)
            else:
                logger.logic_log(e.log_id, request=request)

        if e.msg_id:
            if e.arg_dict and isinstance(e.arg_dict, dict):
                msg = get_message(e.msg_id, request.user.get_lang_mode(), **(e.arg_dict))
            else:
                msg = get_message(e.msg_id, request.user.get_lang_mode())
    except ActionHistory.DoesNotExist:
        logger.logic_log('LOSI08001', action_history_id, request=request)
    except Exception as e:
        logger.logic_log('LOSI00005', 'Fail to retry an action. trace: %s' % (traceback.format_exc()), request=request)

    data = {'message' : msg}

    response_json = json.dumps(data)
    return HttpResponse(response_json, content_type="application/json")


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def resume(request):
    """
    アクションを再開する
    """
    logger.logic_log('LOSI00001', 'none', request=request)
    now = datetime.datetime.now(pytz.timezone('UTC'))
    msg = ''
    action_history_id = 0 
    try:
        with transaction.atomic():
            action_history_id = request.POST.get('act_his_id', None)
            if action_history_id is None:
                msg = get_message('MOSJA13022', request.user.get_lang_mode(), showMsgId=False)

            # ルール種別管理を確認し、削除フラグが立っている場合は処理を中断する！
            if _chk_disuse_flag(action_history_id) == False:
                raise OASEError('MOSJA13082', '')

            # 再開対象のアクション履歴を抽出
            act_his = ActionHistory.objects.select_for_update().get(action_history_id=action_history_id)

            # ルール別アクセス権限をチェック
            _validate_permission(request, act_his, 'MOSJA13018')

            # アクション履歴の状態をチェック
            if act_his.status != defs.PENDING and act_his.retry_status != defs.PENDING:
                raise OASEError('MOSJA13016', '')

            # 再開のみの場合
            if act_his.retry_status != defs.PENDING:

                # 再開対象のルールマッチング結果を取得
                response_id = act_his.response_id
                rhdm_resp = RhdmResponse.objects.select_for_update().get(response_id=response_id)
                if rhdm_resp.status != defs.PENDING and act_his.retry_status != defs.PENDING:
                    raise OASEError('MOSJA13016', '')

                # アクション履歴の状態を未処理に遷移
                act_his.status = defs.PROCESSING
                act_his.last_act_user = request.user.user_name
                act_his.action_start_time = now
                act_his.last_update_timestamp = now
                act_his.save(force_update=True)

                # ルールマッチング結果の状態を未処理に遷移
                rhdm_resp.status = defs.UNPROCESS
                rhdm_resp.last_update_user = request.user.user_name
                rhdm_resp.last_update_timestamp = now
                rhdm_resp.save(force_update=True)

            # 再開、かつ、再実行の場合
            else:
                act_his.retry_flag = True
                act_his.retry_status = defs.PROCESSING
                act_his.last_act_user = request.user.user_name
                act_his.action_start_time = now
                act_his.last_update_timestamp = now
                act_his.save(force_update=True)


    except OASEError as e:
        if e.log_id:
            if e.arg_list and isinstance(e.arg_list, list):
                logger.logic_log(e.log_id, *(e.arg_list), request=request)
            else:
                logger.logic_log(e.log_id, request=request)

        if e.msg_id:
            if e.arg_dict and isinstance(e.arg_dict, dict):
                msg = get_message(e.msg_id, request.user.get_lang_mode(), **(e.arg_dict))
            else:
                msg = get_message(e.msg_id, request.user.get_lang_mode())
    except ActionHistory.DoesNotExist:
        logger.logic_log('LOSI08001', action_history_id, request=request)
    except RhdmResponse.DoesNotExist:
        logger.logic_log('LOSI08002', action_history_id, request=request)
    except Exception as e:
        logger.logic_log('LOSI00005', 'Fail to retry an action. trace: %s' % (traceback.format_exc()), request=request)

    data = {'message' : msg}

    response_json = json.dumps(data)
    return HttpResponse(response_json, content_type="application/json")

@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def stop(request):
    """
    保留中のアクションを停止する
    """
    logger.logic_log('LOSI00001', 'none', request=request)
    now = datetime.datetime.now(pytz.timezone('UTC'))
    msg = ''
    action_history_id = 0 
    try:
        with transaction.atomic():
            action_history_id = request.POST.get('act_his_id', None)
            if action_history_id is None:
                msg = get_message('MOSJA13022', request.user.get_lang_mode(), showMsgId=False)

            # ルール種別管理を確認し、削除フラグが立っている場合は処理を中断する！
            if _chk_disuse_flag(action_history_id) == False:
                raise OASEError('MOSJA13082', '')

            # 再開対象のアクション履歴を抽出
            act_his = ActionHistory.objects.select_for_update().get(action_history_id=action_history_id)

            # ルール別アクセス権限をチェック
            _validate_permission(request, act_his, 'MOSJA13021')

            # 停止対象のルールマッチング結果を取得
            response_id = act_his.response_id
            rhdm_resp = RhdmResponse.objects.select_for_update().get(response_id=response_id)
            if not(rhdm_resp.status == defs.PENDING and act_his.status == defs.PENDING):
                raise OASEError('MOSJA13016', '')

            # 停止にする
            act_his.status = defs.STOP
            act_his.last_act_user = request.user.user_name
            act_his.last_update_timestamp = now
            act_his.save(force_update=True)

            # ルールマッチング結果の状態を処理済みに遷移
            rhdm_resp.status = defs.PROCESSED
            rhdm_resp.last_update_user = request.user.user_name
            rhdm_resp.last_update_timestamp = now
            rhdm_resp.save(force_update=True)

            # アクションログに実行中断のログを残す
            ActionLog(
                response_id = rhdm_resp.response_id,
                execution_order = act_his.execution_order,
                trace_id = rhdm_resp.trace_id,
                message_id = 'MOSJA01050',
                message_params = None,
                last_update_timestamp = now,
            ).save(force_insert=True)

    except OASEError as e:
        if e.log_id:
            if e.arg_list and isinstance(e.arg_list, list):
                logger.logic_log(e.log_id, *(e.arg_list), request=request)
            else:
                logger.logic_log(e.log_id, request=request)

        if e.msg_id:
            if e.arg_dict and isinstance(e.arg_dict, dict):
                msg = get_message(e.msg_id, request.user.get_lang_mode(), **(e.arg_dict))
            else:
                msg = get_message(e.msg_id, request.user.get_lang_mode())
    except ActionHistory.DoesNotExist:
        logger.logic_log('LOSI08001', action_history_id, request=request)
    except RhdmResponse.DoesNotExist:
        logger.logic_log('LOSI08002', action_history_id, request=request)
    except Exception as e:
        logger.logic_log('LOSI00005', 'Fail to retry an action. trace: %s' % (traceback.format_exc()), request=request)

    data = {'message' : msg}

    response_json = json.dumps(data)
    return HttpResponse(response_json, content_type="application/json")


def _get_get_history_data_func(action_type_id):
    """
    [概要]
    インストール済みドライバーのget_history_data()を動的に取得
    [引数]
    action_type_id: int
    [戻り値]
    action_type_idに対応したget_history_data()
    エラーの場合は引き数1つ戻り値{}のメソッドを返す
    """
    method = lambda action_history_id: {}
    try:
        driver_type_id = ActionType.objects.values_list('driver_type_id', flat=True).get(disuse_flag=str(defs.ENABLE), action_type_id=action_type_id)
        drv_type = DriverType.objects.get(driver_type_id=driver_type_id)

        module_name = 'libs.commonlibs.{0}.{0}_common'.format(drv_type.name)
        drv_module = import_module(module_name)
        method = getattr(drv_module, 'get_history_data')

    except ActionType.DoesNotExist:
        logger.logic_log('LOSI08004', action_type_id)
    except DriverType.DoesNotExist:
        logger.logic_log('LOSI08005', driver_type_id)
    except ImportError as e:
        logger.system_log('LOSM08003', e)
    except AttributeError as e:
        logger.system_log('LOSM08004', e)
    finally:
        return method


def _chk_disuse_flag(action_history_id):
    """
    [概要]
    action_history_idに紐づいたルール種別の削除フラグを確認する
    [引数]
    action_type_id: int
    [戻り値]
    True/False
    Falseの場合は後続処理を中断する
    """
    rule_id = ActionHistory.objects.get(action_history_id=action_history_id).rule_type_id
    disuse_flag = RuleType.objects.get(rule_type_id=rule_id).disuse_flag
    if disuse_flag == "0":
        return True
    else:
        return False
