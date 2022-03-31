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
import ast
import re
from web_app.models.ITA_models import ItaDriver
from web_app.models.ITA_models import ItaActionHistory
from web_app.models.ITA_models import ItaParameterItemInfo
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
    coexist = 0
    operation_id_check_flg = 0
    server_list_flg = False
    menu_flg = False
    server_host_check = 0
    hostgroup_flg = False
    hostname_flg = False
    action_check = 0
    operation_flg = False

    # パラメーター情報取得
    check_info = ITAManager.analysis_parameters(params)

    # ITA_NAME チェック
    message_list = ita_name_check(check_info, act_info, message_list)

    # 重複チェック
    if 'SYMPHONY_CLASS_ID' in check_info and 'CONDUCTOR_CLASS_ID' in check_info:
        logger.logic_log('LOSM00035', check_info)
        message_list.append(
            {'id': 'MOSJA03139', 'param': 'SYMPHONY_CLASS_ID, CONDUCTOR_CLASS_ID'})
    elif 'SYMPHONY_CLASS_ID' in check_info and 'SYMPHONY_NAME' in check_info:
        logger.logic_log('LOSM00047', check_info)
        message_list.append(
            {'id': 'MOSJA03139', 'param': 'SYMPHONY_CLASS_ID, SYMPHONY_NAME'})
    elif 'CONDUCTOR_CLASS_ID' in check_info and 'CONDUCTOR_NAME' in check_info:
        logger.logic_log('LOSM00048', check_info)
        message_list.append(
            {'id': 'MOSJA03139', 'param': 'CONDUCTOR_CLASS_ID, CONDUCTOR_NAME'})
    elif 'SYMPHONY_CLASS_ID' in check_info and 'CONDUCTOR_NAME' in check_info:
        logger.logic_log('LOSM00049', check_info)
        message_list.append(
            {'id': 'MOSJA03139', 'param': 'SYMPHONY_CLASS_ID, CONDUCTOR_NAME'})
    elif 'CONDUCTOR_CLASS_ID' in check_info and 'SYMPHONY_NAME' in check_info:
        logger.logic_log('LOSM00050', check_info)
        message_list.append(
            {'id': 'MOSJA03139', 'param': 'CONDUCTOR_CLASS_ID, SYMPHONY_NAME'})
    elif 'SYMPHONY_NAME' in check_info and 'CONDUCTOR_NAME' in check_info:
        logger.logic_log('LOSM00051', check_info)
        message_list.append(
            {'id': 'MOSJA03139', 'param': 'SYMPHONY_NAME, CONDUCTOR_NAME'})
    elif 'SYMPHONY_CLASS_ID' in check_info:
        # SYMPHONY_CLASS_ID チェック
        message_list = symphony_class_id_check(check_info, conditions, message_list)
    elif 'CONDUCTOR_CLASS_ID' in check_info:
        # CONDUCTOR_CLASS_ID チェック
        message_list = conductor_class_id_check(check_info, conditions, message_list)
    elif 'SYMPHONY_NAME' in check_info:
        # SYMPHONY_NAME チェック
        message_list = symphony_name_check(check_info, conditions, message_list)
    elif 'CONDUCTOR_NAME' in check_info:
        # CONDUCTOR_NAME チェック
        message_list = conductor_name_check(check_info, conditions, message_list)
    else:
        # どちらも記述がない場合
        message_list.append({'id': 'MOSJA03108', 'param': None})

    # 重複チェック
    if 'OPERATION_ID' in check_info and 'OPERATION_NAME' in check_info:
        logger.logic_log('LOSM00035', check_info)
        message_list.append(
            {'id': 'MOSJA03139', 'param': 'OPERATION_ID, OPERATION_NAME'})

    # OPERATION_ID チェック
    elif 'OPERATION_ID' in check_info:
        operation_id = check_info['OPERATION_ID']
        operation_id_check_flg = operation_id_check_flg + 1
        action_check = action_check + 1
        operation_flg = True
        message_list = operation_id_check(operation_id, check_info, conditions, message_list)

    # OPERATION_NAME チェック
    elif 'OPERATION_NAME' in check_info:
        operation_name = check_info['OPERATION_NAME']
        action_check = action_check + 1
        operation_flg = True
        message_list = operation_name_check(operation_name, check_info, conditions, message_list)

    # SERVER_LIST チェック
    if 'SERVER_LIST' in check_info:
        server_list = check_info['SERVER_LIST']
        exclusive = exclusive + 1
        action_check = action_check + 1
        operation_id_check_flg = operation_id_check_flg + 1
        server_host_check = server_host_check + 1
        server_list_flg = True
        message_list = server_list_check(server_list, check_info, conditions, message_list)

    # MENU_ID チェック
    if 'MENU_ID' in check_info:
        menu_id = check_info['MENU_ID']
        exclusive = exclusive + 1
        coexist = coexist + 1
        operation_id_check_flg = operation_id_check_flg + 1
        action_check = action_check + 1
        message_list = menu_id_check(menu_id, check_info, conditions, message_list)

    # MENU チェック
    if 'MENU' in check_info:

        ke = check_info.keys()
        flg = False
        fidx = 0
        tidx = len(params)
        for i, para in enumerate(params):
            # if (para.startswith(ke + '=') and flg = True):
            for k in ke:
                if para.startswith(k + '='):
                    if k == 'MENU':
                        fidx = i
                        flg = True
                    elif flg == True:
                        tidx = i
                        break

        parameters = (',').join(params[fidx:tidx])
        check_info['MENU'] = ('=').join(parameters.split('=')[1:])

        flg = act_info[check_info['ITA_NAME']] if 'ITA_NAME' in check_info and check_info['ITA_NAME'] in act_info else False
        coexist = coexist + 1
        action_check = action_check + 1
        menu_flg = True

        if not server_list_flg:
            operation_id_check_flg = operation_id_check_flg + 1

        search = re.search("{{ VAR_", check_info['MENU'])

        if search is None:
            messsage_list = into_parameter_check(check_info, flg, message_list)

    # HOSTGROUP_NAME チェック
    if 'HOSTGROUP_NAME' in check_info:
        server_host_check = server_host_check + 1
        hostgroup_flg = True
        hostgroup_list = check_info['HOSTGROUP_NAME']
        message_list = hostgroup_list_check(hostgroup_list, check_info, message_list)

    # HOST_NAME チェック
    if 'HOST_NAME' in check_info:
        if not hostgroup_flg:
            server_host_check = server_host_check + 1
        hostname_flg = True
        hostname_list = check_info['HOST_NAME']
        message_list = hostname_list_check(hostname_list, check_info, message_list)

    # OPERATION_ID OPERATION_NAME SERVER_LIST MENU MENU_ID 記述チェック
    if action_check == 0:
        logger.logic_log('LOSM00060', check_info)
        message_list.append(
            {'id': 'MOSJA03182', 'param': 'OPERATION_ID, OPERATION_NAME, SERVER_LIST, MENU, MENU_ID'})

    elif operation_flg == True and action_check == 1:
        if hostgroup_flg == True or hostname_flg == True:
            logger.logic_log('LOSM00061', check_info)
            message_list.append(
            {'id': 'MOSJA03183', 'param': 'HOSTGROUP_NAME, HOST_NAME'})

    # SERVER_LIST MENU_ID 共存チェック
    if exclusive > 1:
        logger.logic_log('LOSM00024', check_info)
        message_list.append(
            {'id': 'MOSJA03139', 'param': 'SERVER_LIST, MENU_ID'})

    # MENU_ID MENU 共存チェック
    if coexist > 1:
        logger.logic_log('LOSM00056', check_info)
        message_list.append(
            {'id': 'MOSJA03139', 'param': 'MENU_ID, MENU'})

    # OPERATION_ID 共存チェック
    if operation_id_check_flg > 1:
        logger.logic_log('LOSM00057', check_info)
        message_list.append(
            {'id': 'MOSJA03179', 'param': 'SERVER_LIST, MENU, MENU_ID'})

    # MENU と SERVER_LIST,HOSTGROUP_NAME,HOST_NAMEチェック
    if menu_flg and server_host_check > 1:
        logger.logic_log('LOSM00058', check_info)
        message_list.append(
            {'id': 'MOSJA03180', 'param': 'SERVER_LIST, HOSTGROUP_NAME, HOST_NAME'})

    elif menu_flg and server_host_check < 1:
        logger.logic_log('LOSM00059', check_info)
        message_list.append(
            {'id': 'MOSJA03181', 'param': 'SERVER_LIST, HOSTGROUP_NAME, HOST_NAME'})

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


def symphony_name_check(check_info, conditions, message_list):
    """
    [概要]
    SYMPHONY_NAMEのバリデーションチェックを行う
    [引数]
    check_info        : チェック情報
    conditions        : 条件名
    message_list      : メッセージリスト
    [戻り値]
    message_list      : メッセージリスト
    """

    if 'SYMPHONY_NAME' not in check_info:
        logger.logic_log('LOSM00052', check_info)
        message_list.append({'id': 'MOSJA03113', 'param': 'SYMPHONY_NAME'})

    elif check_info['SYMPHONY_NAME'] == '':
        logger.logic_log('LOSM00053', check_info)
        message_list.append({'id': 'MOSJA03176', 'param': None})

    elif not DriverCommon.has_right_reserved_value(conditions, check_info['SYMPHONY_NAME']):
        logger.logic_log('LOSM00023', check_info['SYMPHONY_NAME'])
        message_list.append({'id': 'MOSJA03137', 'param': 'SYMPHONY_NAME'})

    return message_list


def conductor_class_id_check(check_info, conditions, message_list):
    """
    [概要]
    CONDUCTOR_CLASS_IDのバリデーションチェックを行う
    [引数]
    check_info        : チェック情報
    conditions        : 条件名
    message_list      : メッセージリスト
    [戻り値]
    message_list      : メッセージリスト
    """

    if 'CONDUCTOR_CLASS_ID' not in check_info:
        logger.logic_log('LOSM00033', check_info)
        message_list.append({'id': 'MOSJA03113', 'param': 'CONDUCTOR_CLASS_ID'})

    elif check_info['CONDUCTOR_CLASS_ID'] == '':
        logger.logic_log('LOSM00034', check_info)
        message_list.append({'id': 'MOSJA03207', 'param': None})

    elif not DriverCommon.has_right_reserved_value(conditions, check_info['CONDUCTOR_CLASS_ID']):
        logger.logic_log('LOSM00023', check_info['CONDUCTOR_CLASS_ID'])
        message_list.append({'id': 'MOSJA03137', 'param': 'CONDUCTOR_CLASS_ID'})

    return message_list


def conductor_name_check(check_info, conditions, message_list):
    """
    [概要]
    CONDUCTOR_NAMEのバリデーションチェックを行う
    [引数]
    check_info        : チェック情報
    conditions        : 条件名
    message_list      : メッセージリスト
    [戻り値]
    message_list      : メッセージリスト
    """

    if 'CONDUCTOR_NAME' not in check_info:
        logger.logic_log('LOSM00054', check_info)
        message_list.append({'id': 'MOSJA03113', 'param': 'CONDUCTOR_NAME'})

    elif check_info['CONDUCTOR_NAME'] == '':
        logger.logic_log('LOSM00034', check_info)
        message_list.append({'id': 'MOSJA03177', 'param': None})

    elif not DriverCommon.has_right_reserved_value(conditions, check_info['CONDUCTOR_NAME']):
        logger.logic_log('LOSM00023', check_info['CONDUCTOR_NAME'])
        message_list.append({'id': 'MOSJA03137', 'param': 'CONDUCTOR_NAME'})

    return message_list


def operation_id_check(operation_id, check_info, conditions, message_list):
    """
    [概要]
    OPERATION_IDのバリデーションチェックを行う
    [引数]
    operation_id : OPERATION_ID
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


def operation_name_check(operation_name, check_info, conditions, message_list):
    """
    [概要]
    OPERATION_NAMEのバリデーションチェックを行う
    [引数]
    operation_name : OPERATION_NAME
    check_info     : チェック情報
    conditions     : 条件名
    message_list   : メッセージリスト
    [戻り値]
    message_list   : メッセージリスト
    """

    if operation_name == '':
        logger.logic_log('LOSM00055', check_info)
        message_list.append({'id': 'MOSJA03178', 'param': None})

    elif operation_name and not DriverCommon.has_right_reserved_value(conditions, operation_name):
        logger.logic_log('LOSM00023', operation_name)
        message_list.append({'id': 'MOSJA03137', 'param': 'OPERATION_NAME'})

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


def hostgroup_list_check(hostgroup_list, check_info, message_list):
    """
    [概要]
    HOSTGROUP_NAMEのバリデーションチェックを行う
    [引数]
    hostgroup_list : HOSTGROUP_NAME
    check_info     : チェック情報
    message_list   : メッセージリスト
    [戻り値]
    message_list   : メッセージリスト
    """

    if hostgroup_list == '':
        logger.logic_log('LOSM00031', check_info)
        message_list.append({'id': 'MOSJA03146', 'param': None})

    return message_list


def hostname_list_check(hostname_list, check_info, message_list):
    """
    [概要]
    HOST_NAMEのバリデーションチェックを行う
    [引数]
    hostname_list : HOST_NAME
    check_info    : チェック情報
    message_list  : メッセージリスト
    [戻り値]
    message_list  : メッセージリスト
    """

    if hostname_list == '':
        logger.logic_log('LOSM00032', check_info)
        message_list.append({'id': 'MOSJA03147', 'param': None})

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

    if 'CONVERT_FLG' not in check_info:
        logger.logic_log('LOSM00028', check_info)
        message_list.append({'id': 'MOSJA03143', 'param': None})

    elif check_info['CONVERT_FLG'] == '':
        logger.logic_log('LOSM00029', check_info)
        message_list.append({'id': 'MOSJA03144', 'param': None})

    menu_id_list = menu_id.split(':')
    if len(menu_id_list) != 1 and check_info['CONVERT_FLG'].upper() == 'TRUE':
        logger.logic_log('LOSM00030', check_info)
        message_list.append({'id': 'MOSJA03145', 'param': None})

    return message_list


def into_parameter_check(check_info, valid_flg, message_list):
    """
    [概要]
    MENUのバリデーションチェックを行う
    [引数]
    check_info   : チェック情報
    valid_flg    : バリデーションフラグ
    message_list : メッセージリスト
    [戻り値]
    message_list : メッセージリスト
    """

    # フォーマットチェック、辞書に変換
    menu = check_info['MENU']
    menu = ast.literal_eval(menu)

    menuid_list = []
    menu_val_info = {}
    for value in menu:
        menu_id = None
        if 'ID' not in value:
            logger.logic_log('LOSM00047', check_info)
            message_list.append({'id': 'MOSJA03171', 'param': None})

        else:
            if value['ID'] == '':
                logger.logic_log('LOSM00048', check_info)
                message_list.append({'id': 'MOSJA03171', 'param': None})

            else:
                menu_id = int(value['ID'])
                menuid_list.append(menu_id)

        if 'VALUES' not in value:
            logger.logic_log('LOSM00050', check_info)
            message_list.append({'id': 'MOSJA03172', 'param': None})

        else:
            if len(value['VALUES']) <= 0:
                logger.logic_log('LOSM00049', check_info)
                message_list.append({'id': 'MOSJA03173', 'param': None})

            elif menu_id is not None:
                if menu_id not in menu_val_info:
                    menu_val_info[menu_id] = {
                        'COL_GROUP' : '',
                        'COL_NAME'  : '',
                    }

                if isinstance(value['VALUES'], dict):
                    for k, v in value['VALUES'].items():
                        col_list = k.split('/')
                        menu_val_info[menu_id]['COL_GROUP'] = ('/').join(col_list[0:-1]) if len(col_list) >= 2 else ''
                        menu_val_info[menu_id]['COL_NAME'] = col_list[-1]
                else:
                    for value in value['VALUES']:
                        for k, v in value.items():
                            col_list = k.split('/')
                            menu_val_info[menu_id]['COL_GROUP'] = ('/').join(col_list[0:-1]) if len(col_list) >= 2 else ''
                            menu_val_info[menu_id]['COL_NAME'] = col_list[-1]

    # DBに存在しないメニューIDを指定したらエラー
    rset = []
    if valid_flg and len(menuid_list) > 0:
        db_menu_ids = []
        db_col_info = {}

        if 'ITA_NAME' in check_info:
            ita_name = check_info['ITA_NAME']
            drv_id = ItaDriver.objects.get(ita_disp_name=ita_name).ita_driver_id
            rset = ItaParameterItemInfo.objects.filter(ita_driver_id=drv_id, menu_id__in=menuid_list).values('menu_id', 'column_group', 'item_name')
            for rs in rset:
                if rs['menu_id'] not in db_menu_ids:
                    db_menu_ids.append(rs['menu_id'])
                if rs['menu_id'] not in db_col_info:
                    db_col_info[rs['menu_id']] = []

                col_name = '%s/%s' % (rs['column_group'], rs['item_name']) if rs['column_group'] else rs['item_name']
                db_col_info[rs['menu_id']].append(col_name)

            if len(menuid_list) != len(db_menu_ids):
                tmp_list = list(set(menuid_list) - set(db_menu_ids))
                logger.logic_log('LOSM00051', check_info)
                message_list.append({'id': 'MOSJA03174', 'param': tmp_list})

            for mid in menuid_list:
                if mid not in db_col_info:
                    continue

                col_name = ''
                if mid in menu_val_info:
                    col_name = '%s/%s' % (menu_val_info[mid]['COL_GROUP'], menu_val_info[mid]['COL_NAME']) if menu_val_info[mid]['COL_GROUP'] else menu_val_info[mid]['COL_NAME']

                if col_name not in db_col_info[mid]:
                    logger.logic_log('LOSM00052', check_info)
                    message_list.append({'id': 'MOSJA03175', 'param': None})
        else:
            logger.logic_log('LOSM00004', check_info)


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
        if history.symphony_instance_no:
            result['MOSJA13024'] = history.symphony_instance_no
            result['MOSJA13025'] = history.symphony_class_id
            result['MOSJA13026'] = history.operation_id
            result['MOSJA13027'] = history.symphony_workflow_confirm_url
            result['MOSJA13028'] = history.restapi_error_info
            result['MOSJA13084'] = history.parameter_item_info  # MOSJA13084:連携項目
        else:
            result['MOSJA13085'] = history.conductor_instance_no
            result['MOSJA13086'] = history.conductor_class_id
            result['MOSJA13026'] = history.operation_id
            result['MOSJA13087'] = history.conductor_workflow_confirm_url
            result['MOSJA13028'] = history.restapi_error_info
            result['MOSJA13084'] = history.parameter_item_info  # MOSJA13084:連携項目

    except ItaActionHistory.DoesNotExist:
        logger.system_log('LOSE00001', action_his_id, traceback.format_exc())

    finally:
        return result
