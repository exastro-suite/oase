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
  ServiceNowドライバーのライブラリ

"""
import traceback
from web_app.models.ServiceNow_models import ServiceNowDriver
from web_app.models.ServiceNow_models import ServiceNowActionHistory
from libs.backyardlibs.action_driver.ServiceNow.ServiceNow_driver import ServiceNowManager
from libs.commonlibs.oase_logger import OaseLogger
from libs.commonlibs.common import DriverCommon
logger = OaseLogger.get_instance()


def check_dt_action_params(params, act_info, conditions, *args, **kwargs):
    """
    アクションパラメータのチェックをする。
    エラーメッセージのリストを返す。
    """
    message_list = []
    count = 0

    for param in params:
        param = param.strip()

    # パラメーター情報取得
    check_info = ServiceNowManager.analysis_parameters(params)

    # SERVICENOW_NAME チェック
    message_list = servicenow_name_check(check_info, act_info, message_list)

    # INCIDENT_STATUS チェック
    if check_info['INCIDENT_STATUS'] or check_info['INCIDENT_STATUS'] == '':
        count = count + 1
        incident_status = check_info['INCIDENT_STATUS']
        message_list = incident_status_check(incident_status, check_info, message_list)

    # WORKFLOW_ID チェック
    if check_info['WORKFLOW_ID'] or check_info['WORKFLOW_ID'] == '':
        count = count + 1
        workflow_id = check_info['WORKFLOW_ID']
        message_list = workflow_id_check(workflow_id, check_info, conditions, message_list)

    # WORK_NOTES チェック
    if check_info['WORK_NOTES'] or check_info['WORK_NOTES'] == '':
        count = count + 1
        work_notes = check_info['WORK_NOTES']
        message_list = work_notes_check(work_notes, check_info, conditions, message_list)

    # INCIDENT_STATUS,WORKFLOW_IDどちらも記述がない場合
    if count == 0:
        message_list.append({'id': 'MOSJA03164', 'param': None})

    return message_list


def servicenow_name_check(check_info, act_info, message_list):
    """
    [概要]
    SERVICENOW_NAMEのバリデーションチェックを行う
    [引数]
    check_info   : チェック情報
    act_info     : アクション情報
    message_list : メッセージリスト
    [戻り値]
    message_list : メッセージリスト
    """

    if 'SERVICENOW_NAME' not in check_info:
        logger.logic_log('LOSM00036', check_info)
        message_list.append({'id': 'MOSJA03113', 'param': 'SERVICENOW_NAME'})

    else:
        # SERVICENOW_NAME の値が登録済みのドライバー名であるかチェック
        servicenow_name = check_info['SERVICENOW_NAME']
        if servicenow_name not in act_info:
            rcnt = ServiceNowDriver.objects.filter(servicenow_disp_name=servicenow_name).count()
            act_info[servicenow_name] = True if rcnt > 0 else False

        if not act_info[servicenow_name]:
            logger.logic_log('LOSM00037', check_info)
            message_list.append({'id': 'MOSJA03148', 'param': None})

    return message_list


def incident_status_check(incident_status, check_info, message_list):
    """
    [概要]
    INCIDENT_STATUSのバリデーションチェックを行う
    [引数]
    incident_status : INCIDENT_STATUS
    check_info      : チェック情報
    message_list    : メッセージリスト
    [戻り値]
    message_list    : メッセージリスト
    """

    if incident_status == '':
        logger.logic_log('LOSM00041', check_info)
        message_list.append({'id': 'MOSJA03161', 'param': None})

    else:
        # INCIDENT_STATUS の値が「OPEN」または「CLOSE」であるかチェック
        if incident_status not in ['OPEN', 'CLOSE', 'IN PROGRESS', 'RESOLVED']:
            logger.logic_log('LOSM00040', check_info)
            message_list.append({'id': 'MOSJA03162', 'param': None})

    return message_list


def workflow_id_check(workflow_id, check_info, conditions, message_list):
    """
    [概要]
    WORKFLOW_IDのバリデーションチェックを行う
    [引数]
    workflow_id  : WORKFLOW_ID
    check_info   : チェック情報
    conditions   : 条件名
    message_list : メッセージリスト
    [戻り値]
    message_list : メッセージリスト
    """

    if workflow_id == '':
        logger.logic_log('LOSM00044', check_info)
        message_list.append({'id': 'MOSJA03163', 'param': 'WORKFLOW_ID'})

    elif workflow_id and not DriverCommon.has_right_reserved_value(conditions, workflow_id):
        logger.logic_log('LOSM00023', workflow_id)
        message_list.append({'id': 'MOSJA03137', 'param': 'WORKFLOW_ID'})

    return message_list


def work_notes_check(work_notes, check_info, conditions, message_list):
    """
    [概要]
    WORK_NOTESのバリデーションチェックを行う
    [引数]
    work_notes   : WORK_NOTES
    check_info   : チェック情報
    conditions   : 条件名
    message_list : メッセージリスト
    [戻り値]
    message_list : メッセージリスト
    """

    if work_notes == '':
        logger.logic_log('LOSM00045', check_info)
        message_list.append({'id': 'MOSJA03165', 'param': 'WORK_NOTES'})

    elif work_notes and not DriverCommon.has_right_reserved_value(conditions, work_notes):
        logger.logic_log('LOSM00023', work_notes)
        message_list.append({'id': 'MOSJA03137', 'param': 'WORK_NOTES'})

    return message_list


def get_history_data(action_his_id):
    """
    [概要]
    action_his_idのServiceNowアクション履歴を取得する
    [引数]
    action_his_id: int
    [戻り値]
    result: dict アクション情報に表示したい情報
    """

    result = {}
    try:
        history = ServiceNowActionHistory.objects.get(action_his_id=action_his_id)
        result['MOSJA13088'] = history.servicenow_disp_name
        result['MOSJA13126'] = history.sys_id
        result['MOSJA13089'] = history.short_description

    except ItaActionHistory.DoesNotExist:
        logger.system_log('LOSE00001', action_his_id, traceback.format_exc())

    finally:
        return result

