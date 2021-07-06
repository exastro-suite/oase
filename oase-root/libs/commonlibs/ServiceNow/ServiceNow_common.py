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

    for param in params:
        param = param.strip()

    # パラメーター情報取得
    check_info = ServiceNowManager.analysis_parameters(params)

    # SERVICENOW_NAME チェック
    message_list = servicenow_name_check(check_info, act_info, message_list)
    # INCIDENT_STATUS チェック
    message_list = incident_status_check(check_info, act_info, message_list)

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


def incident_status_check(check_info, act_info, message_list):
    """
    [概要]
    INCIDENT_STATUSのバリデーションチェックを行う
    [引数]
    check_info   : チェック情報
    act_info     : アクション情報
    message_list : メッセージリスト
    [戻り値]
    message_list : メッセージリスト
    """

    incident_status = check_info['INCIDENT_STATUS']

    if incident_status is None:
        logger.logic_log('LOSM00039', check_info)
        message_list.append({'id': 'MOSJA03113', 'param': 'INCIDENT_STATUS'})

    elif incident_status == '':
        logger.logic_log('LOSM00041', check_info)
        message_list.append({'id': 'MOSJA03161', 'param': None})

    else:
        # INCIDENT_STATUS の値が「OPEN」または「CLOSE」であるかチェック
        if incident_status not in ['OPEN', 'CLOSE']:
            logger.logic_log('LOSM00040', check_info)
            message_list.append({'id': 'MOSJA03162', 'param': None})

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

