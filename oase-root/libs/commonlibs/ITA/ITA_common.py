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
  ITAドライバーのライブラリ

"""
import traceback
from web_app.models.ITA_models import ItaDriver
from web_app.models.ITA_models import ItaActionHistory
from libs.backyardlibs.action_driver.ITA.ITA_driver import ITAManager
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

    # 初期化
    operation_id = None
    server_list = None
    menu_id = None
    exclusive = 0

    # パラメーター情報取得
    check_info = ITAManager.analysis_parameters(params)

    # ITA_NAME チェック
    message_list = ita_name_check(check_info, act_info, message_list)

    # SYMPHONY_CLASS_ID チェック
    message_list = symphony_class_id_check(check_info, conditions, message_list)

    # OPERATION_ID チェック
    if 'OPERATION_ID' in check_info:
        operation_id = check_info['OPERATION_ID']
        exclusive = exclusive + 1
        message_list = operation_id_check(operation_id, check_info, conditions, message_list)

    # SERVER_LIST チェック
    if 'SERVER_LIST' in check_info:
        server_list = check_info['SERVER_LIST']
        exclusive = exclusive + 1
        message_list = server_list_check(server_list, check_info, conditions, message_list)

    # MENU_ID チェック
    if 'MENU_ID' in check_info:
        menu_id = check_info['MENU_ID']
        exclusive = exclusive + 1
        message_list = menu_id_check(menu_id, check_info, conditions, message_list)

    # OPERATION_ID SERVER_LIST MENU_ID 共存チェック
    if exclusive > 1:
        logger.logic_log('LOSM00024', check_info)
        message_list.append(
            {'id': 'MOSJA03139', 'param': 'OPERATION_ID, SERVER_LIST, MENU_ID'})

    return message_list


def ita_name_check(check_info, act_info, message_list):
    """
    [概要]
    ITA_NAMEのバリデーションチェックを行う
    [引数]
    check_info   : チェック情報
    act_info     : アクション情報
    message_list : メッセージリスト
    [戻り値]
    message_list : メッセージリスト
    """

    if 'ITA_NAME' not in check_info:
        logger.logic_log('LOSM00004', check_info)
        message_list.append({'id': 'MOSJA03113', 'param': 'ITA_NAME'})

    else:
        # ITA_NAME の値が登録済みのドライバー名であるかチェック
        ita_name = check_info['ITA_NAME']
        if ita_name not in act_info:
            rcnt = ItaDriver.objects.filter(ita_disp_name=ita_name).count()
            act_info[ita_name] = True if rcnt > 0 else False

        if not act_info[ita_name]:
            logger.logic_log('LOSM00005', check_info)
            message_list.append({'id': 'MOSJA03115', 'param': None})

    return message_list


def symphony_class_id_check(check_info, conditions, message_list):
    """
    [概要]
    SYMPHONY_CLASS_IDのバリデーションチェックを行う
    [引数]
    check_info        : チェック情報
    conditions        : 条件名
    message_list      : メッセージリスト
    [戻り値]
    message_list      : メッセージリスト
    """

    if 'SYMPHONY_CLASS_ID' not in check_info:
        logger.logic_log('LOSM00006', check_info)
        message_list.append({'id': 'MOSJA03113', 'param': 'SYMPHONY_CLASS_ID'})

    elif check_info['SYMPHONY_CLASS_ID'] == '':
        logger.logic_log('LOSM00007', check_info)
        message_list.append({'id': 'MOSJA03116', 'param': None})

    elif not DriverCommon.has_right_reserved_value(conditions, check_info['SYMPHONY_CLASS_ID']):
        logger.logic_log('LOSM00023', check_info['SYMPHONY_CLASS_ID'])
        message_list.append({'id': 'MOSJA03137', 'param': 'SYMPHONY_CLASS_ID'})

    return message_list


def operation_id_check(operation_id, check_info, conditions, message_list):
    """
    [概要]
    OPERATION_IDのバリデーションチェックを行う
    [引数]
    operation_id : SYMPHONY_CLASS_ID
    check_info   : チェック情報
    conditions   : 条件名
    message_list : メッセージリスト
    [戻り値]
    message_list : メッセージリスト
    """

    if operation_id == '':
        logger.logic_log('LOSM00025', check_info)
        message_list.append({'id': 'MOSJA03140', 'param': None})

    elif operation_id and not DriverCommon.has_right_reserved_value(conditions, operation_id):
        logger.logic_log('LOSM00023', operation_id)
        message_list.append({'id': 'MOSJA03137', 'param': 'OPERATION_ID'})

    return message_list


def server_list_check(server_list, check_info, conditions, message_list):
    """
    [概要]
    SERVER_LISTのバリデーションチェックを行う
    [引数]
    server_list  : SERVER_LIST
    check_info   : チェック情報
    conditions   : 条件名
    message_list : メッセージリスト
    [戻り値]
    message_list : メッセージリスト
    """

    if server_list == '':
        logger.logic_log('LOSM00026', check_info)
        message_list.append({'id': 'MOSJA03141', 'param': None})

    elif server_list and not DriverCommon.has_right_reserved_value(conditions, server_list):
        logger.logic_log('LOSM00023', server_list)
        message_list.append({'id': 'MOSJA03137', 'param': 'SERVER_LIST'})

    return message_list


def menu_id_check(menu_id, check_info, conditions, message_list):
    """
    [概要]
    MENU_IDのバリデーションチェックを行う
    [引数]
    menu_id      : MENU_ID
    check_info   : チェック情報
    conditions   : 条件名
    message_list : メッセージリスト
    [戻り値]
    message_list : メッセージリスト
    """

    if menu_id == '':
        logger.logic_log('LOSM00027', check_info)
        message_list.append({'id': 'MOSJA03142', 'param': None})

    elif menu_id and not DriverCommon.has_right_reserved_value(conditions, menu_id):
        logger.logic_log('LOSM00023', menu_id)
        message_list.append({'id': 'MOSJA03137', 'param': 'MENU_ID'})

    return message_list


def get_history_data(action_his_id):
    """
    [概要]
    action_his_idのITAアクション履歴を取得する
    [引数]
    action_his_id: int
    [戻り値]
    result: dict アクション情報に表示したい情報
    """

    result = {}
    try:
        history = ItaActionHistory.objects.get(action_his_id=action_his_id)
        result['MOSJA13023'] = history.ita_disp_name
        result['MOSJA13024'] = history.symphony_instance_no
        result['MOSJA13025'] = history.symphony_class_id
        result['MOSJA13026'] = history.operation_id
        result['MOSJA13027'] = history.symphony_workflow_confirm_url
        result['MOSJA13028'] = history.restapi_error_info

    except ItaActionHistory.DoesNotExist:
        logger.system_log('LOSE00001', action_his_id, traceback.format_exc())

    finally:
        return result
