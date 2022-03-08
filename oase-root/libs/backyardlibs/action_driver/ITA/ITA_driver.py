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
アクションドライバ アクション実行処理（ITA）

"""

import os
import sys
import json
import re
import django
import traceback
import ast
import datetime
import pytz

# OASE モジュール importパス追加
my_path = os.path.dirname(os.path.abspath(__file__))
tmp_path = my_path.split('oase-root')
root_dir_path = tmp_path[0] + 'oase-root'
sys.path.append(root_dir_path)

# OASE モジュール import
# #LOCAL_PATCH#
os.environ['DJANGO_SETTINGS_MODULE'] = 'confs.frameworkconfs.settings'
django.setup()

from django.conf import settings
from django.urls import reverse
from django.db import transaction
from django.db.models import Q

from web_app.models.models import EventsRequest
from web_app.models.models import DataObject

from web_app.models.ITA_models import ItaActionHistory
from web_app.models.ITA_models import ItaDriver
from web_app.models.ITA_models import ItaActionSystem
from web_app.models.ITA_models import ItaParameterMatchInfo
from web_app.models.ITA_models import ItaParametaCommitInfo, ItaMenuName
from web_app.models.ITA_models import ItaParameterItemInfo

from libs.commonlibs.oase_logger import OaseLogger
from libs.commonlibs.aes_cipher import AESCipher
from libs.commonlibs.define import *
from libs.commonlibs.common import Common

from libs.backyardlibs.oase_action_common_libs import ActionDriverCommonModules, ConstantModules as Cstobj
from libs.backyardlibs.action_driver.ITA.ITA_core import ITA1Core
from libs.backyardlibs.action_driver.common.action_abstract import AbstractManager

from libs.webcommonlibs.oase_exception import OASEError

from collections import defaultdict

logger = OaseLogger.get_instance()
Comobj = ActionDriverCommonModules()


class ITAManager(AbstractManager):
    """
    [クラス概要]
        アクションドライバメイン処理クラス
    """

    ACTIONPARAM_KEYS = [
        'ITA_NAME',
        'SYMPHONY_CLASS_ID',
        'CONDUCTOR_CLASS_ID',
        'OPERATION_ID',
        'SERVER_LIST',
        'MENU_ID',
        'CONVERT_FLG',
        'HOSTGROUP_NAME',
        'HOST_NAME',
        'MENU',
        'OPERATION_NAME',
        'SYMPHONY_NAME',
        'CONDUCTOR_NAME'
    ]

    def __init__(self, trace_id, response_id, last_update_user):
        self.trace_id = trace_id
        self.response_id = response_id
        self.action_history = None
        self.aryActionParameter = {}
        self.last_update_user = last_update_user
        self.symphony_class_id = None
        self.conductor_class_id = None

        self.ITAobj = None
        self.ary_ita_config = {}
        self.ary_movement_list = {}
        self.ary_action_server_id_name = {}
        self.listActionServer = []
        self.ita_driver = None  # model


    def ita_action_history_insert(self, aryAnzActionParameter, SymphonyInstanceNO,
            OperationID,SymphonyWorkflowURL, exe_order, conductor_instance_id, conductor_url, parameter_item_info=''):
        """
        [概要]
        ITAアクション履歴登録メゾット
        """
        logger.logic_log('LOSI00001',
            'trace_id: %s, aryAnzActionParameter: %s, ActionHistoryID: %s, SymphonyInstanceNO: %s, OperationID: %s, SymphonyWorkflowURL: %s, conductor_instance_id: %s, conductor_url: %s' %
            (self.trace_id, aryAnzActionParameter, self.action_history.pk, SymphonyInstanceNO, OperationID, SymphonyWorkflowURL, conductor_instance_id, conductor_url))

        symphony_class_id = self.symphony_class_id
        conductor_class_id = self.conductor_class_id

        try:
            with transaction.atomic():
                rcnt = ItaActionHistory.objects.filter(action_his_id=self.action_history.pk).count()
                if rcnt > 0:
                    itaacthist = ItaActionHistory.objects.get(action_his_id=self.action_history.pk)
                    itaacthist.ita_disp_name = aryAnzActionParameter['ITA_NAME']
                    itaacthist.symphony_instance_no = SymphonyInstanceNO
                    itaacthist.symphony_class_id = symphony_class_id
                    itaacthist.operation_id = OperationID
                    itaacthist.symphony_workflow_confirm_url = SymphonyWorkflowURL
                    itaacthist.conductor_instance_no = conductor_instance_id
                    itaacthist.conductor_class_id = conductor_class_id
                    itaacthist.conductor_workflow_confirm_url = conductor_url
                    itaacthist.last_update_timestamp = Comobj.getStringNowDateTime()
                    itaacthist.last_update_user = self.last_update_user
                    itaacthist.save(force_update=True)
                else:
                    itaacthist = ItaActionHistory(
                        action_his_id=self.action_history.pk,
                        ita_disp_name=aryAnzActionParameter['ITA_NAME'],
                        symphony_instance_no=SymphonyInstanceNO,
                        symphony_class_id=symphony_class_id,
                        operation_id=OperationID,
                        symphony_workflow_confirm_url=SymphonyWorkflowURL,
                        parameter_item_info=parameter_item_info,
                        conductor_instance_no=conductor_instance_id,
                        conductor_class_id=conductor_class_id,
                        conductor_workflow_confirm_url=conductor_url,
                        last_update_timestamp=Comobj.getStringNowDateTime(),
                        last_update_user=self.last_update_user,
                    )
                    itaacthist.save(force_insert=True)

        except Exception as e:
            logger.system_log('LOSE01101', self.trace_id, traceback.format_exc())
            ActionDriverCommonModules.SaveActionLog(self.response_id, exe_order, self.trace_id, 'MOSJA01036')
            return None

        logger.logic_log('LOSI00002', 'ItaActionHistory pk: %s' % itaacthist.pk)
        return itaacthist

    def reset_variables(self):
        """
        [概要]
          メンバ変数を初期化する
        """
        self.ary_movement_list = {}
        self.ary_action_server_id_name = {}
        self.listActionServer = []
        self.aryActionParameter = {}

    def act(self, rhdm_res_act, retry=False):
        """
        [概要]
            ITAアクションを実行
        """
        logger.logic_log('LOSI00001', 'self.trace_id: %s' % (self.trace_id,))
        ActionStatus = ACTION_EXEC_ERROR
        DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.NONE

        list_operation_id = []
        symphony_instance_id = None
        symphony_url = ''
        server_list = ''
        operation_id = None
        menu_id = None
        convert_flg = None
        dt_host_name = None
        hostgroup_name = None
        conductor_instance_id = None
        conductor_url = ''
        event_info_list = []
        instance_check = True
        no_host_flg = False
        server_str = ''
        operation_name = ''

        param_info = json.loads(rhdm_res_act.action_parameter_info)

        status, detail = self.check_ita_master(rhdm_res_act.execution_order)
        if status > 0:
            raise OASEError('', 'LOSE01129', log_params=[self.trace_id], msg_params={
                'sts': status, 'detail': detail})

        key1 = 'ACTION_PARAMETER_INFO'
        if key1 not in param_info:
            ActionDriverCommonModules.SaveActionLog(
                self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01005')
            raise OASEError('', 'LOSE01114', log_params=[self.trace_id, 'OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key1], msg_params={
                            'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_SRVLIST_KEY})

        # OPERATION_ID/SERVER_LIST/MENU_ID/MENU サーチ
        key_operation_id = 'OPERATION_ID'
        key_server_list = 'SERVER_LIST'
        key_menu_id = 'MENU_ID'
        key_convert_flg = 'CONVERT_FLG'
        key_hostgroup_name = 'HOSTGROUP_NAME'
        key_dt_host_name = 'HOST_NAME'
        key_menu = 'MENU'
        key_operation_name = 'OPERATION_NAME'
        check_info = self.analysis_parameters(param_info[key1])

        # MENUのパターン
        if key_menu in check_info:
            server_list_flg = False
            if len(check_info[key_menu]) == 0:
                ActionDriverCommonModules.SaveActionLog(
                    self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01117')
                raise OASEError(
                    '',
                    'LOSE01143',
                    log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_menu, self.trace_id],
                    msg_params={'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL}
                )

            if key_server_list in check_info:
                server_str = check_info[key_server_list]
                if not server_str:
                    ActionDriverCommonModules.SaveActionLog(
                        self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01064')
                    raise OASEError(
                        '',
                        'LOSE01130',
                        log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_server_list, self.trace_id],
                        msg_params={'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL}
                    )

            if key_hostgroup_name in check_info:
                hostgroup_name = check_info[key_hostgroup_name]
                if not hostgroup_name:
                    ActionDriverCommonModules.SaveActionLog(
                        self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01121')
                    raise OASEError(
                        '',
                        'LOSE01139',
                        log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_hostgroup_name, self.trace_id],
                        msg_params={'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL}
                    )

            if key_dt_host_name in check_info:
                dt_host_name = check_info[key_dt_host_name]
                if not dt_host_name:
                    ActionDriverCommonModules.SaveActionLog(
                        self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01122')
                    raise OASEError(
                        '',
                        'LOSE01140',
                        log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_dt_host_name, self.trace_id],
                        msg_params={'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL}
                    )

            if key_operation_id in check_info:
                operation_id = check_info[key_operation_id]
                if not operation_id:
                    ActionDriverCommonModules.SaveActionLog(
                        self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01059')

                    raise OASEError(
                        '',
                        'LOSE01128',
                        log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_convert_flg, self.trace_id],
                        msg_params={'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL}
                    )

            elif key_operation_name in check_info:
                operation_name = check_info[key_operation_name]
                if not operation_name:
                    ActionDriverCommonModules.SaveActionLog(
                        self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01118')

                    raise OASEError(
                        '',
                        'LOSE01144',
                        log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_operation_name, self.trace_id],
                        msg_params={'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL}
                    )

                event_str = ''
                event_list = []
                event_info = EventsRequest.objects.get(trace_id=self.trace_id).event_info
                event_list = ast.literal_eval(event_info)['EVENT_INFO']
                for event_data in event_list:
                    event_str = event_str + event_data
                hash_str = Common.sha256_hash_str(event_str)
                operation_name = operation_name + hash_str

            params = param_info[key1]
            ke = check_info.keys()
            flg = False
            fidx = 0
            tidx = len(params)
            for i, para in enumerate(params):
                for k in ke:
                    if para.startswith(k + '='):
                        if k == 'MENU':
                            fidx = i
                            flg = True
                        elif flg == True:
                            tidx = i
                            break

            parameters = (',').join(params[fidx:tidx])
            check_info[key_menu] = ('=').join(parameters.split('=')[1:])

            menu_str = check_info[key_menu]
            menu_dict = ast.literal_eval(menu_str)

            menu_id_list = []
            for menu in menu_dict:
                menu_id_list.append(menu['ID'])

            hg_flg_info = {}
            rset = ItaMenuName.objects.filter(ita_driver_id=self.ita_driver.ita_driver_id, menu_id__in=menu_id_list)
            rset = rset.values('menu_id', 'hostgroup_flag')
            for r in rset:
                hg_flg_info[r['menu_id']] = r['hostgroup_flag']

            for menu_id in menu_id_list:
                menu_id = int(menu_id)
                if menu_id not in hg_flg_info:
                    ActionDriverCommonModules.SaveActionLog(
                        self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01123')

                    logger.system_log(
                        'LOSM01101', self.trace_id, self.response_id, rhdm_res_act.execution_order, menu_id
                    )
                    return ACTION_EXEC_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_PARAM_FAIL

            target_host_name = {}
            server_list = []

            for menu_id in menu_id_list:
                if menu_id not in target_host_name:
                    target_host_name[str(menu_id)] = {
                        'H': [],
                        'HG': [],
                    }

            if server_str:
                server_list = server_str.split(':')

            if hostgroup_name:
                target_host_name = self.set_host_data(target_host_name, 'HG', hostgroup_name)

            if dt_host_name:
                target_host_name = self.set_host_data(target_host_name, 'H', dt_host_name)

            commitinfo_list = ItaParametaCommitInfo.objects.filter(
                response_id=self.response_id,
                commit_order=rhdm_res_act.execution_order
            ).order_by('ita_order')

            if len(commitinfo_list) == 0:
                commitinfo_list = []
                if not server_list:
                    server_list_flg = True
                    server_list.append("HostName")

                server_name = (',').join(server_list[:])
                for menu in menu_dict:
                    menu_id = menu['ID']
                    values = menu['VALUES']
                    key = values.keys()
                    for i, ke in enumerate(key):

                        # カラムが空白の場合はDBにコミットしない
                        if not ke:
                            continue

                        val = values[ke]

                        # 値が空白の場合はDBにコミットしない
                        if not val:
                            continue

                        count = ke.count('/')

                        try:
                            if count > 0:
                                tmp = ke.rsplit('/', 1)
                                column_group = tmp[0]
                                column       = tmp[1]

                                ita_order = ItaParameterItemInfo.objects.get(
                                    ita_driver_id=self.ita_driver.ita_driver_id,
                                    menu_id=int(menu_id),
                                    column_group=column_group,
                                    item_name=column
                                ).ita_order

                            else:
                                ita_order = ItaParameterItemInfo.objects.get(
                                    ita_driver_id=self.ita_driver.ita_driver_id,
                                    menu_id=int(menu_id),
                                    item_name=ke
                                ).ita_order

                        except ItaParameterItemInfo.DoesNotExist:
                            logger.system_log('LOSE01148', self.trace_id)
                            ActionDriverCommonModules.SaveActionLog(
                                self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01124')
                            return ACTION_EXEC_ERROR, DetailStatus

                        except Exception as e:
                            logger.system_log('LOSE01147', self.trace_id, traceback.format_exc())
                            ActionDriverCommonModules.SaveActionLog(
                                self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01125')
                            return ACTION_EXEC_ERROR, DetailStatus

                        if i == 0:
                            itaparcom = ItaParametaCommitInfo(
                                response_id = self.response_id,
                                commit_order = rhdm_res_act.execution_order,
                                menu_id = int(menu_id),
                                ita_order = 0,
                                parameter_value = server_name,
                                last_update_timestamp = Comobj.getStringNowDateTime(),
                                last_update_user = self.last_update_user,
                            )
                            commitinfo_list.append(itaparcom)

                            itaparcom = ItaParametaCommitInfo(
                                response_id = self.response_id,
                                commit_order = rhdm_res_act.execution_order,
                                menu_id = int(menu_id),
                                ita_order = ita_order + 1,
                                parameter_value = val,
                                last_update_timestamp = Comobj.getStringNowDateTime(),
                                last_update_user = self.last_update_user,
                            )
                            commitinfo_list.append(itaparcom)

                        else:
                            itaparcom = ItaParametaCommitInfo(
                                response_id = self.response_id,
                                commit_order = rhdm_res_act.execution_order,
                                menu_id = int(menu_id),
                                ita_order = ita_order + 1,
                                parameter_value = val,
                                last_update_timestamp = Comobj.getStringNowDateTime(),
                                last_update_user = self.last_update_user,
                            )
                            commitinfo_list.append(itaparcom)

                try:
                    ItaParametaCommitInfo.objects.bulk_create(commitinfo_list)

                except Exception as e:
                    logger.system_log('LOSE01133', self.trace_id, traceback.format_exc())
                    ActionDriverCommonModules.SaveActionLog(
                        self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01071')
                    return ACTION_EXEC_ERROR, DetailStatus

            parameter_list = {}

            commitinfo_list = ItaParametaCommitInfo.objects.filter(response_id=self.response_id, commit_order=rhdm_res_act.execution_order).order_by('ita_order')
            for commit_info in commitinfo_list:
                if commit_info.menu_id not in parameter_list:
                    parameter_list[commit_info.menu_id] = {'host_name':'', 'param_list':[]}

                if commit_info.ita_order == 0:
                    parameter_list[commit_info.menu_id]['host_name'] = commit_info.parameter_value
                else:
                    parameter_list[commit_info.menu_id]['param_list'].append(commit_info.parameter_value)

            # ホスト情報の有無をチェック
            for k, v in parameter_list.items():

                # ホスト情報を必要としないパラメーターシートはチェック対象外
                if hg_flg_info[k] < 0:
                    continue

                if not v['host_name']:
                    logger.system_log('LOSE01136', self.trace_id, traceback.format_exc())
                    return ACTION_EXEC_ERROR, DetailStatus

            operation_data = []
            if retry:
                if operation_id:
                    ret, operation_data = self.ITAobj.select_operation_id(
                        self.ary_ita_config, operation_id)

                    if ret != 0:
                        ActionDriverCommonModules.SaveActionLog(
                            self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01126')

                        logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                        DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL

                        return ACTION_EXEC_ERROR, DetailStatus

                elif operation_name:
                    ret = self.ITAobj._select_c_operation_list_by_operation_name(
                        operation_name, operation_data, False)
                    if ret == Cstobj.RET_DATA_ERROR:
                        ActionDriverCommonModules.SaveActionLog(
                            self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01056')

                        ret, operation_data = self.ITAobj.insert_operation_name(
                            self.ary_ita_config, operation_name)

                        if ret > 0:
                            logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                            DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL

                            return ACTION_EXEC_ERROR, DetailStatus

                    elif ret == Cstobj.RET_REST_ERROR:
                        logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                        DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL

                        return ACTION_EXEC_ERROR, DetailStatus

                else:
                    operation_name = '%s%s' % (self.trace_id, rhdm_res_act.execution_order)
                    ret = self.ITAobj._select_c_operation_list_by_operation_name(operation_name, operation_data, False)

                    if ret == Cstobj.RET_DATA_ERROR:
                        ActionDriverCommonModules.SaveActionLog(
                            self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01056')

                        operation_name = ''
                        ret, operation_name = self.ITAobj.insert_operation(self.ary_ita_config)
                        if ret != True:
                            logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                            DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL

                            return ACTION_EXEC_ERROR, DetailStatus

                        ret, operation_data = self.ITAobj.select_operation(
                            self.ary_ita_config, operation_name)
                        if ret != True:
                            logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                            DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL

                            return ACTION_EXEC_ERROR, DetailStatus

                    elif ret == Cstobj.RET_REST_ERROR:
                        logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                        DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL

                        return ACTION_EXEC_ERROR, DetailStatus

            else:
                if operation_id:
                    ret, operation_data = self.ITAobj.select_operation_id(
                        self.ary_ita_config, operation_id)

                    if ret != 0:
                        ActionDriverCommonModules.SaveActionLog(
                            self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01126')

                        logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                        DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL

                        return ACTION_EXEC_ERROR, DetailStatus

                elif operation_name:
                    ret = self.ITAobj._select_c_operation_list_by_operation_name(
                        operation_name, operation_data, False)
                    if ret == Cstobj.RET_DATA_ERROR:
                        ActionDriverCommonModules.SaveActionLog(
                            self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01056')

                        ret, operation_data = self.ITAobj.insert_operation_name(
                            self.ary_ita_config, operation_name)

                        if ret > 0:
                            logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                            DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL

                            return ACTION_EXEC_ERROR, DetailStatus

                    elif ret == Cstobj.RET_REST_ERROR:
                        logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                        DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL

                        return ACTION_EXEC_ERROR, DetailStatus

                else:
                    # オペレーションID登録
                    ret, operation_name = self.ITAobj.insert_operation(self.ary_ita_config)
                    if ret != True:
                        logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                        DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL

                        return ACTION_EXEC_ERROR, DetailStatus

                    # オペレーション検索
                    ret, operation_data = self.ITAobj.select_operation(self.ary_ita_config, operation_name)
                    if ret != True:
                        logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                        DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL

                        return ACTION_EXEC_ERROR, DetailStatus

            # パラメータシート登録情報作成
            operation_id = operation_data[0][Cstobj.COL_OPERATION_NO_IDBH]
            operation_name = operation_data[0][Cstobj.COL_OPERATION_NAME]
            exec_schedule_date = '%s_%s:%s' % (
                operation_data[0][Cstobj.COL_OPERATION_DATE],
                operation_data[0][Cstobj.COL_OPERATION_NO_IDBH],
                operation_data[0][Cstobj.COL_OPERATION_NAME])

            if server_list_flg:
                server_list = []

            for menu_id in menu_id_list:
                menu_id = int(menu_id)
                host_name = ''
                param_list = []

                if not parameter_list[menu_id]['host_name'] and hg_flg_info[menu_id] >= 0:
                    logger.system_log(
                        'LOSE01138', self.trace_id, self.response_id, rhdm_res_act.execution_order, menu_id
                    )
                    return ACTION_EXEC_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_PARAM_FAIL

                set_host = []
                target_id = str(menu_id)
                if target_id in target_host_name.keys():
                    for h in target_host_name[target_id]['HG']:
                        host_name_tmp = '[HG]%s' % (h) if hg_flg_info[menu_id] > 0 else h

                        set_host.append(host_name_tmp)

                    for h in target_host_name[target_id]['H']:
                        host_name_tmp = '[H]%s' % (h) if hg_flg_info[menu_id] > 0 else h
                        set_host.append(host_name_tmp)

                if len(set_host) == 0 and menu_id in parameter_list and parameter_list[menu_id]['host_name']:
                    for server in server_list:
                        host_name_tmp = '[H]%s' % (h) if hg_flg_info[menu_id] > 0 else server
                        set_host.append(host_name_tmp)

                if len(set_host) == 0 and hg_flg_info[menu_id] < 0:
                    set_host.append('')


                param_list = parameter_list[menu_id]['param_list']

                if len(set_host) == 0:
                    # Error
                    logger.system_log(
                        'LOSM01101', self.trace_id, self.response_id, rhdm_res_act.execution_order, menu_id
                    )
                    return ACTION_EXEC_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_PARAM_FAIL

                for sh in set_host:
                    host_name = sh
                    # 検索結果によりあったら、update なかったら、insert
                    ret_select, ary_result = self.ITAobj.select_c_parameter_sheet(
                        self.ary_ita_config, host_name, operation_name, str(menu_id).zfill(10))

                    if ret_select is None:
                        DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_PARAM_FAIL
                        return ACTION_EXEC_ERROR, DetailStatus

                    if ret_select > 0:
                        col_revision = 3 if self.ita_driver.version in ['1.6.0', '1.6.1', '1.6.2', '1.6.3', '1.7.0', '1.7.1', '1.7.2', '1.8.0', '1.8.1', '1.8.2', '1.9.0'] else 2
                        ret = self.ITAobj.update_c_parameter_sheet(
                            self.ary_ita_config, host_name, operation_name, exec_schedule_date, param_list, str(menu_id).zfill(10), ary_result, col_revision)
                    elif ret_select == 0:
                        ret = self.ITAobj.insert_c_parameter_sheet(
                            host_name, operation_id, operation_name, exec_schedule_date, param_list, str(menu_id).zfill(10))

                    if ret == Cstobj.RET_REST_ERROR:
                        logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                        DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_PARAM_FAIL

                        return ACTION_EXEC_ERROR, DetailStatus

                ActionDriverCommonModules.SaveActionLog(
                    self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01067')

            # 連携項目整形
            parameter_item_info = self.make_parameter_item_info_menu(menu_id_list, rhdm_res_act, target_host_name)

            # ITAアクション履歴登録
            ret = self.ita_action_history_insert(
                self.aryActionParameter,
                symphony_instance_id,
                operation_id,
                symphony_url,
                rhdm_res_act.execution_order,
                conductor_instance_id,
                conductor_url,
                parameter_item_info
            )
            # 履歴の保存に失敗した場合は、異常終了とする
            if ret == None:
                return ACTION_EXEC_ERROR, DetailStatus

            return ACTION_HISTORY_STATUS.ITA_REGISTERING_SUBSTITUTION_VALUE, DetailStatus

        # SERVER_LISTのパターン
        elif key_server_list in check_info:
            if len(check_info[key_server_list]) == 0:
                ActionDriverCommonModules.SaveActionLog(
                    self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01064')
                raise OASEError('', 'LOSE01130', log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_server_list, self.trace_id], msg_params={
                                'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL})

            if key_operation_id in check_info:
                operation_id = check_info[key_operation_id]
                if not operation_id:
                    ActionDriverCommonModules.SaveActionLog(
                        self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01059')

                    raise OASEError(
                        '',
                        'LOSE01128',
                        log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_convert_flg, self.trace_id],
                        msg_params={'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL}
                    )

                row_data = []
                ret = self.ITAobj.select_c_operation_list(
                    self.ary_ita_config, operation_id, row_data, False)

                if ret != 0:
                    ActionDriverCommonModules.SaveActionLog(
                        self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01126')

                    raise OASEError(
                        '',
                        'LOSE01128',
                        log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_operation_id, self.trace_id],
                        msg_params={'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL}
                    )

                operation_name = row_data[0][Cstobj.COL_OPERATION_NAME]

                ret = self.ITAobj.insert_working_host(
                    self.ary_ita_config,
                    self.ary_movement_list,
                    self.ary_action_server_id_name,
                    operation_id,
                    operation_name)

                if ret > 0:
                    DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL
                    return ACTION_EXEC_ERROR, DetailStatus

            elif key_operation_name in check_info:
                operation_name = check_info[key_operation_name]
                if not operation_name:
                    ActionDriverCommonModules.SaveActionLog(
                        self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01118')

                    raise OASEError(
                        '',
                        'LOSE01144',
                        log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_operation_name, self.trace_id],
                        msg_params={'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL}
                    )

                event_str = ''
                event_list = []
                event_info = EventsRequest.objects.get(trace_id=self.trace_id).event_info
                event_list = ast.literal_eval(event_info)['EVENT_INFO']
                for event_data in event_list:
                    event_str = event_str + event_data
                hash_str = Common.sha256_hash_str(event_str)
                operation_name = operation_name + hash_str

                row_data = []
                ret, operation_id = self.ITAobj.select_ope_name_ita_master(
                    self.ary_ita_config, operation_name, False)

                if operation_id == 0:
                    ret, row_data = self.ITAobj.insert_operation_name(
                        self.ary_ita_config, operation_name)

                    if ret > 0:
                        DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL
                        return ACTION_EXEC_ERROR, DetailStatus

                    operation_id = row_data[0][Cstobj.COL_OPERATION_NO_IDBH]

                ret = self.ITAobj.insert_working_host(
                    self.ary_ita_config,
                    self.ary_movement_list,
                    self.ary_action_server_id_name,
                    operation_id,
                    operation_name)

                if ret > 0:
                    DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL
                    return ACTION_EXEC_ERROR, DetailStatus

            else:
                if retry:
                    # 再実行の際、登録前にエラーになっていた場合は登録処理から行う。
                    operation_data = []
                    operation_name = '%s%s' % (self.trace_id, rhdm_res_act.execution_order)
                    ret = self.ITAobj._select_c_operation_list_by_operation_name(
                        operation_name, operation_data, False)

                    if ret == Cstobj.RET_DATA_ERROR:
                        ActionDriverCommonModules.SaveActionLog(
                            self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01056')
                        ret = self.ITAobj.insert_ita_master(
                            self.ary_ita_config, self.ary_movement_list, self.ary_action_server_id_name, list_operation_id)
                        if ret > 0:
                            DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL
                        operation_id = list_operation_id[0]
                    elif ret == 0:
                        operation_id = operation_data[0][Cstobj.COL_OPERATION_NO_IDBH]

                else:
                    ret = self.ITAobj.insert_ita_master(
                        self.ary_ita_config, self.ary_movement_list, self.ary_action_server_id_name, list_operation_id)
                    if ret > 0:
                        DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL
                    operation_id = list_operation_id[0]

        # MENU_IDのパターン
        elif key_menu_id in check_info:
            if len(check_info[key_menu_id]) == 0:
                ActionDriverCommonModules.SaveActionLog(
                    self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01070')
                raise OASEError('', 'LOSE01132', log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_menu_id, self.trace_id], msg_params={
                                'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL})

            if len(check_info[key_convert_flg]) == 0 or not check_info[key_convert_flg] or (check_info[key_convert_flg].upper() != 'TRUE' and check_info[key_convert_flg].upper() != 'FALSE'):
                raise OASEError('', 'LOSE01134', log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_convert_flg, self.trace_id], msg_params={
                                'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL})

            if key_hostgroup_name in check_info:
                hostgroup_name = check_info[key_hostgroup_name]
                if not hostgroup_name:
                    raise OASEError('', 'LOSE01139', log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_convert_flg, self.trace_id], msg_params={
                                    'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL})

            if key_dt_host_name in check_info:
                dt_host_name = check_info[key_dt_host_name]
                if not dt_host_name:
                    raise OASEError('', 'LOSE01140', log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_convert_flg, self.trace_id], msg_params={
                                    'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL})

            if key_operation_id in check_info:
                operation_id = check_info[key_operation_id]
                if not operation_id:
                    ActionDriverCommonModules.SaveActionLog(
                        self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01059')

                    raise OASEError(
                        '',
                        'LOSE01128',
                        log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_convert_flg, self.trace_id],
                        msg_params={'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL}
                    )

            elif key_operation_name in check_info:
                operation_name = check_info[key_operation_name]
                if not operation_name:
                    ActionDriverCommonModules.SaveActionLog(
                        self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01118')

                    raise OASEError(
                        '',
                        'LOSE01144',
                        log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_operation_name, self.trace_id],
                        msg_params={'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL}
                    )

                event_str = ''
                event_list = []
                event_info = EventsRequest.objects.get(trace_id=self.trace_id).event_info
                event_list = ast.literal_eval(event_info)['EVENT_INFO']
                for event_data in event_list:
                    event_str = event_str + event_data
                hash_str = Common.sha256_hash_str(event_str)
                operation_name = operation_name + hash_str

            menu_id = check_info[key_menu_id]
            convert_flg = check_info[key_convert_flg]

            menu_id_list = menu_id.split(':')
            if len(menu_id_list) != 1 and convert_flg.upper() == 'TRUE':
                raise OASEError('', 'LOSE01137', log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_convert_flg, self.trace_id], msg_params={
                                'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL})


            hg_flg_info = {}
            rset = ItaMenuName.objects.filter(ita_driver_id=self.ita_driver.ita_driver_id, menu_id__in=menu_id_list)
            rset = rset.values('menu_id', 'hostgroup_flag')
            for r in rset:
                hg_flg_info[r['menu_id']] = r['hostgroup_flag']

            for menu_id in menu_id_list:
                menu_id = int(menu_id)
                if menu_id not in hg_flg_info:
                    logger.system_log(
                        'LOSM01101', self.trace_id, self.response_id, rhdm_res_act.execution_order, menu_id
                    )
                    return ACTION_EXEC_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_PARAM_FAIL


            target_host_name = {}

            for menu_id in menu_id_list:
                if menu_id not in target_host_name:
                    target_host_name[menu_id] = {
                        'H': [],
                        'HG': [],
                    }

            if hostgroup_name:
                target_host_name = self.set_host_data(target_host_name, 'HG', hostgroup_name)

            if dt_host_name:
                target_host_name = self.set_host_data(target_host_name, 'H', dt_host_name)

            host_name = None
            events_request = EventsRequest.objects.get(trace_id=self.trace_id)
            if convert_flg.upper() == 'FALSE':
                commitinfo_list = ItaParametaCommitInfo.objects.filter(response_id=self.response_id, commit_order=rhdm_res_act.execution_order).order_by('ita_order')
                if len(commitinfo_list) == 0:
                    commitinfo_list = []
                    for menu_id in menu_id_list:
                        ita_param_matchinfo_list = list(ItaParameterMatchInfo.objects.filter(
                            ita_driver_id=self.ita_driver.ita_driver_id, menu_id=menu_id).order_by('match_id'))
                        events_request = EventsRequest.objects.get(trace_id=self.trace_id)
                        data_object_list = list(DataObject.objects.filter(rule_type_id=events_request.rule_type_id).order_by('data_object_id'))

                        for match in ita_param_matchinfo_list:
                            label_list = []
                            for obj in data_object_list:

                                if match.conditional_name == obj.conditional_name and not obj.label in label_list:
                                    label_list.append(obj.label)
                                    number = int(obj.label[5:])
                                    message = ast.literal_eval(events_request.event_info)['EVENT_INFO'][number]

                                    parameter_value = ''

                                    pattern = match.extraction_method1
                                    m = re.search(pattern, message)
                                    if m is None:
                                        continue
                                    elif match.extraction_method2 == '':
                                        parameter_value = m.group(0).strip()
                                    elif match.extraction_method2 != '':
                                        value = m.group(0).split(match.extraction_method2)
                                        parameter_value = value[1].strip()

                                    itaparcom = ItaParametaCommitInfo(
                                        response_id = self.response_id,
                                        commit_order = rhdm_res_act.execution_order,
                                        menu_id = int(menu_id),
                                        ita_order = match.order,
                                        parameter_value = parameter_value,
                                        last_update_timestamp = Comobj.getStringNowDateTime(),
                                        last_update_user = self.last_update_user,
                                    )
                                    commitinfo_list.append(itaparcom)

                    try:
                        ItaParametaCommitInfo.objects.bulk_create(commitinfo_list)
                    except Exception as e:
                        logger.system_log('LOSE01133', self.trace_id, traceback.format_exc())
                        ActionDriverCommonModules.SaveActionLog(
                            self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01071')
                        return ACTION_EXEC_ERROR, DetailStatus

                parameter_list = {}

                commitinfo_list = ItaParametaCommitInfo.objects.filter(response_id=self.response_id, commit_order=rhdm_res_act.execution_order).order_by('ita_order')
                for commit_info in commitinfo_list:
                    if commit_info.menu_id not in parameter_list:
                        parameter_list[commit_info.menu_id] = {'host_name':'', 'param_list':[]}

                    if commit_info.ita_order == 0:
                        parameter_list[commit_info.menu_id]['host_name'] = commit_info.parameter_value
                    else:
                        parameter_list[commit_info.menu_id]['param_list'].append(commit_info.parameter_value)

            elif convert_flg.upper() == 'TRUE':
                menu_id = int(menu_id_list[0])
                parameter_list = {}
                commitinfo_list = []

                event_info_list = ast.literal_eval(events_request.event_info)['EVENT_INFO']
                if len(event_info_list) == 0:
                    logger.system_log('LOSE01135', self.trace_id, traceback.format_exc())
                    return ACTION_EXEC_ERROR, DetailStatus

                for i, v in enumerate(event_info_list):
                    if menu_id not in parameter_list:
                        parameter_list[menu_id] = {'host_name':'', 'param_list':[]}

                    no_host_flg = True if hg_flg_info[menu_id] < 0 else False

                    if i == 0 and no_host_flg == False:
                        parameter_list[menu_id]['host_name'] = event_info_list[0]
                    else:
                        parameter_list[menu_id]['param_list'].append(event_info_list[i])
                        itaparcom = ItaParametaCommitInfo(
                            response_id           = self.response_id,
                            commit_order          = rhdm_res_act.execution_order,
                            menu_id               = int(menu_id),
                            ita_order             = i + 1,
                            parameter_value       = event_info_list[i],
                            last_update_timestamp = Comobj.getStringNowDateTime(),
                            last_update_user      = self.last_update_user
                        )
                        commitinfo_list.append(itaparcom)

                if len(commitinfo_list) > 0:
                    try:
                        ItaParametaCommitInfo.objects.bulk_create(commitinfo_list)

                    except Exception as e:
                        logger.system_log('LOSE01133', self.trace_id, traceback.format_exc())
                        ActionDriverCommonModules.SaveActionLog(
                            self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01071')

                        return ACTION_EXEC_ERROR, DetailStatus


            # ホスト情報の有無をチェック
            for k, v in parameter_list.items():

                # ホスト情報を必要としないパラメーターシートはチェック対象外
                if hg_flg_info[k] < 0:
                    continue

                if not v['host_name']:
                    logger.system_log('LOSE01136', self.trace_id, traceback.format_exc())
                    return ACTION_EXEC_ERROR, DetailStatus

            operation_data = []
            if retry:
                if operation_id:
                    ret, operation_data = self.ITAobj.select_operation_id(
                        self.ary_ita_config, operation_id)

                    if ret != 0:
                        ActionDriverCommonModules.SaveActionLog(
                            self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01126')

                        logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                        DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL

                        return ACTION_EXEC_ERROR, DetailStatus

                elif operation_name:
                    ret = self.ITAobj._select_c_operation_list_by_operation_name(
                        operation_name, operation_data, False)

                    if ret == Cstobj.RET_DATA_ERROR:
                        ActionDriverCommonModules.SaveActionLog(
                            self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01056')

                        ret, operation_data = self.ITAobj.insert_operation_name(
                            self.ary_ita_config, operation_name)

                        if ret > 0:
                            logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                            DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL

                            return ACTION_EXEC_ERROR, DetailStatus

                    elif ret == Cstobj.RET_REST_ERROR:
                        logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                        DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL

                        return ACTION_EXEC_ERROR, DetailStatus

                else:
                    operation_name = '%s%s' % (self.trace_id, rhdm_res_act.execution_order)
                    ret = self.ITAobj._select_c_operation_list_by_operation_name(operation_name, operation_data, False)
                    if ret == Cstobj.RET_DATA_ERROR:
                        ActionDriverCommonModules.SaveActionLog(
                            self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01056')

                        operation_name = ''
                        ret, operation_name = self.ITAobj.insert_operation(self.ary_ita_config)
                        if ret != True:
                            logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                            DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL

                            return ACTION_EXEC_ERROR, DetailStatus

                        ret, operation_data = self.ITAobj.select_operation(
                            self.ary_ita_config, operation_name)
                        if ret != True:
                            logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                            DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL

                            return ACTION_EXEC_ERROR, DetailStatus
                    elif ret == Cstobj.RET_REST_ERROR:
                        logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                        DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL

                        return ACTION_EXEC_ERROR, DetailStatus

            else:
                if operation_id:
                    ret, operation_data = self.ITAobj.select_operation_id(
                        self.ary_ita_config, operation_id)

                    if ret != 0:
                        ActionDriverCommonModules.SaveActionLog(
                            self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01126')

                        logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                        DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL

                        return ACTION_EXEC_ERROR, DetailStatus

                elif operation_name:
                    ret = self.ITAobj._select_c_operation_list_by_operation_name(
                        operation_name, operation_data, False)

                    if ret == Cstobj.RET_DATA_ERROR:
                        ActionDriverCommonModules.SaveActionLog(
                            self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01056')

                        ret, operation_data = self.ITAobj.insert_operation_name(
                            self.ary_ita_config, operation_name)

                        if ret > 0:
                            logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                            DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL

                            return ACTION_EXEC_ERROR, DetailStatus

                    elif ret == Cstobj.RET_REST_ERROR:
                        logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                        DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL

                        return ACTION_EXEC_ERROR, DetailStatus

                else:
                    # オペレーションID登録
                    ret, operation_name = self.ITAobj.insert_operation(self.ary_ita_config)
                    if ret != True:
                        logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                        DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL

                        return ACTION_EXEC_ERROR, DetailStatus

                    # オペレーション検索
                    ret, operation_data = self.ITAobj.select_operation(self.ary_ita_config, operation_name)
                    if ret != True:
                        logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                        DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL

                        return ACTION_EXEC_ERROR, DetailStatus

            # パラメータシート登録情報作成
            operation_id = operation_data[0][Cstobj.COL_OPERATION_NO_IDBH]
            operation_name = operation_data[0][Cstobj.COL_OPERATION_NAME]
            exec_schedule_date = '%s_%s:%s' % (
                operation_data[0][Cstobj.COL_OPERATION_DATE],
                operation_data[0][Cstobj.COL_OPERATION_NO_IDBH],
                operation_data[0][Cstobj.COL_OPERATION_NAME])

            for menu_id in menu_id_list:
                menu_id = int(menu_id)
                host_name = ''
                param_list = []

                if not parameter_list[menu_id]['host_name'] and hg_flg_info[menu_id] >= 0:
                    logger.system_log(
                        'LOSE01138', self.trace_id, self.response_id, rhdm_res_act.execution_order, menu_id
                    )
                    return ACTION_EXEC_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_PARAM_FAIL

                set_host = []
                target_id = str(menu_id)
                if target_id in target_host_name.keys():
                    for h in target_host_name[target_id]['HG']:
                        host_name_tmp = '[HG]%s' % (h) if hg_flg_info[menu_id] > 0 else h

                        set_host.append(host_name_tmp)

                    for h in target_host_name[target_id]['H']:
                        host_name_tmp = '[H]%s' % (h) if hg_flg_info[menu_id] > 0 else h
                        set_host.append(host_name_tmp)

                if len(set_host) == 0 and menu_id in parameter_list and parameter_list[menu_id]['host_name']:
                    h = parameter_list[menu_id]['host_name']
                    host_name_tmp = '[H]%s' % (h) if hg_flg_info[menu_id] > 0 else h
                    set_host.append(host_name_tmp)

                if len(set_host) == 0 and hg_flg_info[menu_id] < 0:
                    set_host.append('')


                param_list = parameter_list[menu_id]['param_list']

                if len(set_host) == 0:
                    # Error
                    logger.system_log(
                        'LOSM01101', self.trace_id, self.response_id, rhdm_res_act.execution_order, menu_id
                    )
                    return ACTION_EXEC_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_PARAM_FAIL

                for sh in set_host:
                    host_name = sh
                    # 検索結果によりあったら、update なかったら、insert
                    ret_select, ary_result = self.ITAobj.select_c_parameter_sheet(
                        self.ary_ita_config, host_name, operation_name, str(menu_id).zfill(10))
                    if ret_select is None:
                        DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_PARAM_FAIL
                        return ACTION_EXEC_ERROR, DetailStatus

                    if ret_select > 0:
                        col_revision = 3 if self.ita_driver.version in ['1.6.0', '1.6.1', '1.6.2', '1.6.3', '1.7.0', '1.7.1', '1.7.2', '1.8.0', '1.8.1', '1.8.2', '1.9.0'] else 2
                        ret = self.ITAobj.update_c_parameter_sheet(
                            self.ary_ita_config, host_name, operation_name, exec_schedule_date, param_list, str(menu_id).zfill(10), ary_result, col_revision)
                    elif ret_select == 0:
                        ret = self.ITAobj.insert_c_parameter_sheet(
                            host_name, operation_id, operation_name, exec_schedule_date, param_list, str(menu_id).zfill(10))

                    if ret == Cstobj.RET_REST_ERROR:
                        logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                        DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_PARAM_FAIL

                        return ACTION_EXEC_ERROR, DetailStatus

                ActionDriverCommonModules.SaveActionLog(
                    self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01067')

            # 連携項目整形
            parameter_item_info = self.make_parameter_item_info(menu_id_list, rhdm_res_act, target_host_name, event_info_list, convert_flg, no_host_flg)

            # ITAアクション履歴登録
            ret = self.ita_action_history_insert(
                self.aryActionParameter,
                symphony_instance_id,
                operation_id,
                symphony_url,
                rhdm_res_act.execution_order,
                conductor_instance_id,
                conductor_url,
                parameter_item_info
            )
            # 履歴の保存に失敗した場合は、異常終了とする
            if ret == None:
                return ACTION_EXEC_ERROR, DetailStatus

            return ACTION_HISTORY_STATUS.ITA_REGISTERING_SUBSTITUTION_VALUE, DetailStatus

        # OPERATION_IDのパターン
        elif key_operation_id in check_info:
            if len(check_info[key_operation_id]) == 0:
                ActionDriverCommonModules.SaveActionLog(
                    self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01059')
                raise OASEError('', 'LOSE01128', log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_operation_id, self.trace_id], msg_params={
                                'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL})

            operation_id = check_info[key_operation_id]

        # OPERATION_NAMEのパターン
        elif key_operation_name in check_info:
            if len(check_info[key_operation_name]) == 0:
                ActionDriverCommonModules.SaveActionLog(
                    self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01118')
                raise OASEError(
                    '',
                    'LOSE01144',
                    log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_operation_name, self.trace_id],
                    msg_params={'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL}
                )

            operation_name = check_info[key_operation_name]

        if operation_id:
            ret = self.ITAobj.select_ope_ita_master(
                self.ary_ita_config, operation_id)
        else:
            ret, operation_id = self.ITAobj.select_ope_name_ita_master(
                self.ary_ita_config, operation_name)

        if ret == Cstobj.RET_DATA_ERROR:
            if key_operation_id in check_info:
                raise OASEError(
                    '',
                    'LOSE01128',
                    log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_operation_id, self.trace_id],
                    msg_params={'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL}
                )
            else:
                raise OASEError(
                    '',
                    'LOSE01128',
                    log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_operation_name, self.trace_id],
                    msg_params={'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL}
                )

        if 'SYMPHONY_CLASS_ID' in self.aryActionParameter or 'SYMPHONY_NAME' in self.aryActionParameter:
            code, symphony_instance_id, symphony_url = self.ITAobj.symphony_execute(
                self.ary_ita_config, operation_id)

            if symphony_instance_id == '':
                instance_check = False
                symphony_instance_id = None
            else:
                ActionDriverCommonModules.SaveActionLog(self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01028')
        else:
            code, conductor_instance_id, conductor_url = self.ITAobj.conductor_execute(
                self.ary_ita_config, operation_id)
            if conductor_instance_id == '':
                instance_check = False
                conductor_instance_id = None
            else:
                ActionDriverCommonModules.SaveActionLog(self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01076')

        if code == 0 and instance_check != False:
            ActionStatus = PROCESSED

        else:
            DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_SYMP_FAIL

        logger.logic_log('LOSI01105', ActionStatus, rhdm_res_act.execution_order, self.trace_id)

        # ITAアクション履歴登録
        logger.logic_log('LOSI01104', str(rhdm_res_act.execution_order), self.trace_id)
        ret = self.ita_action_history_insert(
            self.aryActionParameter,
            symphony_instance_id,
            operation_id,
            symphony_url,
            rhdm_res_act.execution_order,
            conductor_instance_id,
            conductor_url
        )
        # 履歴の保存に失敗した場合は、異常終了とする
        if ret == None:
            return ACTION_EXEC_ERROR, DetailStatus

        # SymphonyまたはConductorに失敗した場合は異常終了する。
        if ActionStatus != PROCESSED:
            logger.system_log('LOSE01110', ActionStatus, self.trace_id)
            ActionDriverCommonModules.SaveActionLog(self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01080')
            return ACTION_EXEC_ERROR, DetailStatus

        logger.logic_log('LOSI00002', 'return: PROCESSED')
        return ACTION_HISTORY_STATUS.EXASTRO_REQUEST, DetailStatus

    def make_parameter_item_info(self, menu_id_list, rhdm_res_act, target_host_name, event_info_list, convert_flg, no_host_flg):
        """
        [概要]
        """

        menu_name = ItaMenuName.objects.filter(ita_driver_id=self.ita_driver.ita_driver_id, menu_id__in=menu_id_list)
        menu_name = menu_name.values('menu_id', 'menu_name')

        param_item_info = ItaParameterItemInfo.objects.filter(
            ita_driver_id=self.ita_driver.ita_driver_id, menu_id__in=menu_id_list).order_by('menu_id','ita_order','item_number')
        param_item_info = param_item_info.values('menu_id', 'item_name', 'ita_order')

        param_commit_info = ItaParametaCommitInfo.objects.filter(
            response_id=self.response_id, commit_order=rhdm_res_act.execution_order).order_by('menu_id','ita_order')
        param_commit_info = param_commit_info.values('menu_id', 'parameter_value', 'ita_order')

        parameter_item_info = ''

        if convert_flg.upper() == 'FALSE':
            for i,mn in enumerate(menu_name):
                if i == 0:
                    parameter_item_info = str(mn['menu_id']) + ":" + mn['menu_name']
                else:
                    parameter_item_info = parameter_item_info + ", " + str(mn['menu_id']) + ":" + mn['menu_name']

                host_flg = False

                for j,pii in enumerate(param_item_info):
                    menu_id_prev = 0
                    for k,pci in enumerate(param_commit_info):
                        if mn['menu_id'] == pii['menu_id'] and mn['menu_id'] == pci['menu_id']:
                            if menu_id_prev != pci['menu_id'] and \
                               host_flg == False and \
                               (len(target_host_name[str(mn['menu_id'])]['HG']) > 0 or \
                               len(target_host_name[str(mn['menu_id'])]['H']) > 0):
                                if target_host_name.get(str(mn['menu_id'])) != None:
                                    if len(target_host_name[str(mn['menu_id'])]['HG']) > 0 and \
                                       len(target_host_name[str(mn['menu_id'])]['H']) > 0:
                                        hg_hostname = ",".join(target_host_name[str(mn['menu_id'])]['HG'])
                                        h_hostname = ",".join(target_host_name[str(mn['menu_id'])]['H'])
                                        # TODO 多言語化対応
                                        parameter_item_info = parameter_item_info + "[ホスト名/ホストグループ名:"
                                        parameter_item_info = parameter_item_info + hg_hostname
                                        parameter_item_info = parameter_item_info + "," + h_hostname
                                        host_flg = True
                                    elif len(target_host_name[str(mn['menu_id'])]['HG']) > 0:
                                        hg_hostname = ",".join(target_host_name[str(mn['menu_id'])]['HG'])
                                        # TODO 多言語化対応
                                        parameter_item_info = parameter_item_info + "[ホスト名/ホストグループ名:"
                                        parameter_item_info = parameter_item_info + hg_hostname
                                        host_flg = True
                                    elif len(target_host_name[str(mn['menu_id'])]['H']) > 0:
                                        h_hostname = ",".join(target_host_name[str(mn['menu_id'])]['H'])
                                        # TODO 多言語化対応
                                        parameter_item_info = parameter_item_info + "[ホスト名/ホストグループ名:"
                                        parameter_item_info = parameter_item_info + h_hostname
                                        host_flg = True
                                elif pci['ita_order'] == 0 and host_flg == False:
                                    # TODO 多言語化対応
                                    parameter_item_info = parameter_item_info + "[ホスト名:"
                                    parameter_item_info = parameter_item_info + pci['parameter_value']
                                    host_flg = True
                            elif pci['ita_order'] == 0 and host_flg == False:
                                # TODO 多言語化対応
                                parameter_item_info = parameter_item_info + "[ホスト名:"
                                parameter_item_info = parameter_item_info + pci['parameter_value']
                                host_flg = True
                            elif (pii['ita_order'] + 1) == pci['ita_order']:
                                parameter_item_info = parameter_item_info + ", "
                                parameter_item_info = parameter_item_info + pii['item_name']
                                parameter_item_info = parameter_item_info + ":"
                                parameter_item_info = parameter_item_info + pci['parameter_value']

                        menu_id_prev = pci['menu_id']

                    if j == len(param_item_info) - 1:
                        parameter_item_info = parameter_item_info + "]"

        else:
            for i,mn in enumerate(menu_name):
                if i == 0:
                    parameter_item_info = str(mn['menu_id']) + ":" + mn['menu_name']
                for j,pii in enumerate(param_item_info):
                    if j == 0 and no_host_flg == False:
                        # TODO 多言語化対応
                        parameter_item_info = parameter_item_info + "[ホスト名:"
                        parameter_item_info = parameter_item_info + event_info_list[j]
                        parameter_item_info = parameter_item_info + ", "
                        parameter_item_info = parameter_item_info + pii['item_name']
                        parameter_item_info = parameter_item_info + ":"
                        parameter_item_info = parameter_item_info + event_info_list[j+1]
                    elif j == 0 and no_host_flg == True:
                        parameter_item_info = parameter_item_info + "["
                        parameter_item_info = parameter_item_info + pii['item_name']
                        parameter_item_info = parameter_item_info + ":"
                        parameter_item_info = parameter_item_info + event_info_list[j]
                    elif no_host_flg == True:
                        parameter_item_info = parameter_item_info + ", "
                        parameter_item_info = parameter_item_info + pii['item_name']
                        parameter_item_info = parameter_item_info + ":"
                        parameter_item_info = parameter_item_info + event_info_list[j]
                    else:
                        parameter_item_info = parameter_item_info + ", "
                        parameter_item_info = parameter_item_info + pii['item_name']
                        parameter_item_info = parameter_item_info + ":"
                        parameter_item_info = parameter_item_info + event_info_list[j+1]

                    if j == len(param_item_info) - 1:
                        parameter_item_info = parameter_item_info + "]"

        return parameter_item_info


    def make_parameter_item_info_menu(self, menu_id_list, rhdm_res_act, target_host_name):
        """
        [概要]
        """

        menu_name = ItaMenuName.objects.filter(ita_driver_id=self.ita_driver.ita_driver_id, menu_id__in=menu_id_list)
        menu_name = menu_name.values('menu_id', 'menu_name')

        param_item_info = ItaParameterItemInfo.objects.filter(
            ita_driver_id=self.ita_driver.ita_driver_id, menu_id__in=menu_id_list).order_by('menu_id','ita_order','item_number')
        param_item_info = param_item_info.values('menu_id', 'item_name', 'ita_order')

        param_commit_info = ItaParametaCommitInfo.objects.filter(
            response_id=self.response_id, commit_order=rhdm_res_act.execution_order).order_by('menu_id','ita_order')
        param_commit_info = param_commit_info.values('menu_id', 'parameter_value', 'ita_order')

        parameter_item_info = ''

        for i,mn in enumerate(menu_name):
            if i == 0:
                parameter_item_info = str(mn['menu_id']) + ":" + mn['menu_name']
            else:
                parameter_item_info = parameter_item_info + ", " + str(mn['menu_id']) + ":" + mn['menu_name']

            host_flg = False

            for j,pii in enumerate(param_item_info):
                menu_id_prev = 0
                for k,pci in enumerate(param_commit_info):
                    if mn['menu_id'] == pii['menu_id'] and mn['menu_id'] == pci['menu_id']:
                        if menu_id_prev != pci['menu_id'] and \
                           host_flg == False and \
                           (len(target_host_name[str(mn['menu_id'])]['HG']) > 0 or \
                           len(target_host_name[str(mn['menu_id'])]['H']) > 0):
                            if target_host_name.get(str(mn['menu_id'])) != None:
                                if len(target_host_name[str(mn['menu_id'])]['HG']) > 0 and \
                                   len(target_host_name[str(mn['menu_id'])]['H']) > 0:
                                    hg_hostname = ",".join(target_host_name[str(mn['menu_id'])]['HG'])
                                    h_hostname = ",".join(target_host_name[str(mn['menu_id'])]['H'])
                                    # TODO 多言語化対応
                                    parameter_item_info = parameter_item_info + "[ホスト名/ホストグループ名:"
                                    parameter_item_info = parameter_item_info + hg_hostname
                                    parameter_item_info = parameter_item_info + "," + h_hostname
                                    host_flg = True
                                elif len(target_host_name[str(mn['menu_id'])]['HG']) > 0:
                                    hg_hostname = ",".join(target_host_name[str(mn['menu_id'])]['HG'])
                                    # TODO 多言語化対応
                                    parameter_item_info = parameter_item_info + "[ホスト名/ホストグループ名:"
                                    parameter_item_info = parameter_item_info + hg_hostname
                                    host_flg = True
                                elif len(target_host_name[str(mn['menu_id'])]['H']) > 0:
                                    h_hostname = ",".join(target_host_name[str(mn['menu_id'])]['H'])
                                    # TODO 多言語化対応
                                    parameter_item_info = parameter_item_info + "[ホスト名/ホストグループ名:"
                                    parameter_item_info = parameter_item_info + h_hostname
                                    host_flg = True
                            elif pci['ita_order'] == 0 and host_flg == False:
                                # TODO 多言語化対応
                                parameter_item_info = parameter_item_info + "[ホスト名:"
                                parameter_item_info = parameter_item_info + pci['parameter_value']
                                host_flg = True
                        elif pci['ita_order'] == 0 and host_flg == False:
                            # TODO 多言語化対応
                            parameter_item_info = parameter_item_info + "[ホスト名:"
                            parameter_item_info = parameter_item_info + pci['parameter_value']
                            host_flg = True
                        elif (pii['ita_order'] + 1) == pci['ita_order']:
                            parameter_item_info = parameter_item_info + ", "
                            parameter_item_info = parameter_item_info + pii['item_name']
                            parameter_item_info = parameter_item_info + ":"
                            parameter_item_info = parameter_item_info + pci['parameter_value']

                    menu_id_prev = pci['menu_id']

                if j == len(param_item_info) - 1:
                    parameter_item_info = parameter_item_info + "]"

        return parameter_item_info


    def act_with_menuid(self, act_his_id, exec_order, limit_dt):
        """
        [概要]
        """
        logger.logic_log('LOSI00001', 'self.trace_id: %s, act_his_id: %s, exec_order: %s' % (self.trace_id, act_his_id, exec_order))
        symphony_instance_id = None
        operation_id = None
        operation_name = ''
        symphony_url = ''
        restapi_error_info = ''
        conductor_instance_id = None
        conductor_url = ''
        symphony_class_id = None
        conductor_class_id = None
        ActionStatus = ACTION_EXEC_ERROR
        instance_check = True
        DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.NONE

        self.ITAobj = ITA1Core(
            self.trace_id,
            self.symphony_class_id,
            self.response_id,
            exec_order,
            self.conductor_class_id)
        self.set_ary_ita_config()

        if 'SYMPHONY_CLASS_ID' in self.aryActionParameter:
            self.symphony_class_id = self.aryActionParameter['SYMPHONY_CLASS_ID']

        elif 'CONDUCTOR_CLASS_ID' in self.aryActionParameter:
            self.conductor_class_id = self.aryActionParameter['CONDUCTOR_CLASS_ID']

        elif 'SYMPHONY_NAME' in self.aryActionParameter:
            symphony_name = self.aryActionParameter['SYMPHONY_NAME']
            ret, self.symphony_class_id = self.ITAobj.select_symphony(self.ary_ita_config, symphony_name)

            if ret > 0:
                logger.system_log('LOSE01145', self.trace_id, ret, symphony_name)
                return ACTION_EXEC_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_VAL

        else:
            conductor_name = self.aryActionParameter['CONDUCTOR_NAME']
            ret, self.conductor_class_id = self.ITAobj.select_conductor(self.ary_ita_config, conductor_name)

            if ret > 0:
                logger.system_log('LOSE01146', self.trace_id, ret, conductor_name)
                return ACTION_EXEC_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_VAL

        self.ITAobj = ITA1Core(
            self.trace_id,
            self.symphony_class_id,
            self.response_id,
            exec_order,
            self.conductor_class_id)

        if 'SYMPHONY_CLASS_ID' in self.aryActionParameter or 'SYMPHONY_NAME' in self.aryActionParameter:
            code = self.ITAobj.select_symphony_movement_master(self.ary_ita_config, self.ary_movement_list)
        else:
            code = self.ITAobj.select_conductor_movement_master(self.ary_ita_config, self.ary_movement_list)

        if code > 0:
            logger.system_log('LOSE01107', self.trace_id, code)
            return ACTION_EXEC_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_VAL

        if 'OPERATION_ID' in self.aryActionParameter:
            operation_id = self.aryActionParameter['OPERATION_ID']

            row_data = []
            ret = self.ITAobj.select_c_operation_list(
                self.ary_ita_config, operation_id, row_data)

            if ret != 0:
                logger.system_log('LOSE01149', self.trace_id, ret, operation_id)
                return ACTION_EXEC_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_VAL

            operation_name = row_data[0][Cstobj.COL_OPERATION_NAME]

        elif 'OPERATION_NAME' in self.aryActionParameter:
            operation_name = self.aryActionParameter['OPERATION_NAME']

            event_str = ''
            event_list = []
            event_info = EventsRequest.objects.get(trace_id=self.trace_id).event_info
            event_list = ast.literal_eval(event_info)['EVENT_INFO']
            for event_data in event_list:
                event_str = event_str + event_data
            hash_str = Common.sha256_hash_str(event_str)
            operation_name = operation_name + hash_str

        else:
            operation_name = '%s%s' % (self.trace_id, exec_order)

        operation_list = []
        ret = self.ITAobj._select_c_operation_list_by_operation_name(operation_name, operation_list)
        if ret > 0:
            logger.system_log('LOSE01011', self.trace_id, 'C_PATTERN_PER_ORCH', self.response_id, exec_order)
            logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, ret))

            ActionDriverCommonModules.SaveActionLog(self.response_id, exec_order, self.trace_id, 'MOSJA01040')
            return ACTION_EXEC_ERROR, DetailStatus

        operation_id = operation_list[0][Cstobj.COL_OPERATION_NO_IDBH]

        operation_id_name = operation_id + ":" + operation_name

        # オーケストレーターID別のムーブメントIDリストを作成
        orch_move_list = {}
        for movement_id, value in self.ary_movement_list.items():
            if value['ORCHESTRATOR_ID'] not in orch_move_list:
                orch_move_list[value['ORCHESTRATOR_ID']] = []

            orch_move_list[value['ORCHESTRATOR_ID']].append(movement_id)

        # オーケストレーターID別の変数カウントを取得
        var_count = {}
        move_info = {}
        for orch_id, movement_ids in orch_move_list.items():
            menu_id, target_table, target_col = self.orchestrator_id_to_menu_movement(orch_id)
            if not menu_id or not target_table:
                logger.logic_log('LOSI00002', 'orchestrator_id: %s, menu_id: %s, target_table: %s' % (orch_id, menu_id, target_table))
                return ACTION_EXEC_ERROR, DetailStatus

            if orch_id not in var_count:
                var_count[orch_id] = 0
                move_info[orch_id] = []

            ret = self.ITAobj.select_e_movent_list(self.ary_ita_config, movement_ids, orch_id, menu_id, target_table, target_col, var_count, move_info)
            if ret > 0:
                logger.system_log('LOSE01011', self.trace_id, 'C_PATTERN_PER_ORCH', self.response_id, exec_order)
                logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, ret))

                ActionDriverCommonModules.SaveActionLog(self.response_id, exec_order, self.trace_id, 'MOSJA01040')
                return ACTION_EXEC_ERROR, DetailStatus

        # 代入値登録のタイムリミットを算出
        limit_sec = 30
        try:
            limit_sec = int(ItaActionSystem.objects.filter(config_id='SUBSTITUTION_TIME').value)

        except Exception as e:
            logger.logic_log('LOSI00005', traceback.format_exc())

        limit_now = datetime.datetime.now(pytz.timezone('UTC'))
        limit_dt += datetime.timedelta(seconds=limit_sec)


        # 変数カウントのあるパラメーターシートに対して取得要求
        total_count = 0
        subst_count = 0
        if self.ita_driver.version in ['1.7.0', '1.7.1', '1.7.2', '1.8.0', '1.8.1', '1.8.2', '1.9.0']:
            total_count = ItaParametaCommitInfo.objects.filter(response_id=self.response_id, ita_order__gt=0).count()

        for orch_id, num in var_count.items():
            total_count += num

            if num <= 0 and self.ita_driver.version not in ['1.7.0', '1.7.1', '1.7.2', '1.8.0', '1.8.1', '1.8.2', '1.9.0']:
                continue

            menu_id, target_table, target_col = self.orchestrator_id_to_menu_id(orch_id)
            if not menu_id or not target_table:
                logger.logic_log('LOSI00002', 'orchestrator_id: %s, menu_id: %s, target_table: %s' % (orch_id, menu_id, target_table))
                return ACTION_EXEC_ERROR, DetailStatus

            movement_names = [] if orch_id not in move_info else move_info[orch_id]
            ret = self.ITAobj.select_substitution_value_mng(self.ary_ita_config, operation_id_name, movement_names, menu_id, target_table, target_col)
            if ret is None or (isinstance(ret, list) and len(ret) <= 0):
                logger.logic_log('LOSI00002', 'orchestrator_id: %s, menu_id: %s, target_table: %s' % (orch_id, menu_id, target_table))

                # タイムリミットを超過していた場合は異常終了
                if limit_now > limit_dt:
                    logger.logic_log('LOSM01306', self.trace_id, 'XXX', 'XXX', limit_sec, limit_dt)
                    ActionDriverCommonModules.SaveActionLog(self.response_id, exec_order, self.trace_id, 'MOSJA01081')
                    return ACTION_HISTORY_STATUS.ACTION_EXEC_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_PARAM_FAIL

                return ACTION_HISTORY_STATUS.ITA_REGISTERING_SUBSTITUTION_VALUE, ACTION_HISTORY_STATUS.DETAIL_STS.NONE

            subst_count += ret


        # ITA側が変数を必要としない(変数カウント0)場合
        if total_count == 0:
            logger.logic_log('LOSI00002', 'trace_id: %s, subst_count: %s, total_count: %s' % (self.trace_id, subst_count, total_count))
            return ACTION_HISTORY_STATUS.ACTION_EXEC_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_PARAM_FAIL


        # 代入値登録が未完了の場合
        if subst_count < total_count:

            # タイムリミットを超過していた場合は異常終了
            if limit_now > limit_dt:
                logger.logic_log('LOSM01306', self.trace_id, subst_count, total_count, limit_sec, limit_dt)
                ActionDriverCommonModules.SaveActionLog(self.response_id, exec_order, self.trace_id, 'MOSJA01081')
                return ACTION_HISTORY_STATUS.ACTION_EXEC_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_PARAM_FAIL

            logger.logic_log('LOSI00002', 'trace_id: %s, subst_count: %s, total_count: %s' % (self.trace_id, subst_count, total_count))
            return ACTION_HISTORY_STATUS.ITA_REGISTERING_SUBSTITUTION_VALUE, ACTION_HISTORY_STATUS.DETAIL_STS.NONE

        if 'SYMPHONY_CLASS_ID' in self.aryActionParameter or 'SYMPHONY_NAME' in self.aryActionParameter:
            # Symphony実行()
            code, symphony_instance_id, symphony_url = self.ITAobj.symphony_execute(
                self.ary_ita_config, operation_id)
            if symphony_instance_id == '':
                instance_check = False
                symphony_instance_id = None
            else:
                ActionDriverCommonModules.SaveActionLog(self.response_id, exec_order, self.trace_id, 'MOSJA01028')
        else:
            # Conductor実行()
            code, conductor_instance_id, conductor_url = self.ITAobj.conductor_execute(
                self.ary_ita_config, operation_id)
            if conductor_instance_id == '':
                instance_check = False
                conductor_instance_id = None
            else:
                ActionDriverCommonModules.SaveActionLog(self.response_id, exec_order, self.trace_id, 'MOSJA01076')

        if code == 0 and instance_check != False:
            ActionStatus = PROCESSED

        # ITAアクション履歴登録
        logger.logic_log('LOSI01104', str(exec_order), self.trace_id)
        ret = self.ita_action_history_insert(
            self.aryActionParameter,
            symphony_instance_id,
            operation_id,
            symphony_url,
            exec_order,
            conductor_instance_id,
            conductor_url
        )
        # 履歴の保存に失敗した場合は、異常終了とする
        if ret == None:
            return ACTION_EXEC_ERROR, DetailStatus

        # SymphonyまたはConductorに失敗した場合は異常終了する。
        if ActionStatus != PROCESSED:
            logger.system_log('LOSE01110', ActionStatus, self.trace_id)
            ActionDriverCommonModules.SaveActionLog(self.response_id, exec_order, self.trace_id, 'MOSJA01080')
            return ACTION_EXEC_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_SYMP_FAIL

        logger.logic_log('LOSI00002', 'return: PROCESSED')
        return ACTION_HISTORY_STATUS.EXASTRO_REQUEST, ACTION_HISTORY_STATUS.DETAIL_STS.NONE

    def orchestrator_id_to_menu_movement(self, orchestra_id):
        """
        [概要]
        オーケストレータIDからMovement一覧メニューID、および、変数カウンタのカラム番号を取得
        """
        menu_id = ""
        target_table = ""
        target_col = 0

        if orchestra_id == '3':
                menu_id = '2100020103'
                target_table = 'E_ANSIBLE_LNS_PATTERN'
                target_col = Cstobj.EAP_LEGACY_VAR_COUNT
        elif orchestra_id == '4':
                menu_id = '2100020203'
                target_table = 'E_ANSIBLE_PNS_PATTERN'
                target_col = Cstobj.EAP_PIONEER_VAR_COUNT
        elif orchestra_id == '5':
                menu_id = '2100020306'
                target_table = 'E_ANSIBLE_LRL_PATTERN'
                target_col = Cstobj.EAP_LEGACYROLE_VAR_COUNT
        elif orchestra_id == '10':
                menu_id = '2100080004'
                target_table = 'E_TERRAFORM_PATTERN'
                target_col = 0

        if self.ita_driver.version in ['1.7.0', '1.7.1', '1.7.2', '1.8.0', '1.8.1', '1.8.2', '1.9.0']:
            target_col = 0

        return menu_id, target_table, target_col

    def orchestrator_id_to_menu_id(self, orchestra_id):
        """
        [概要]
        オーケストレータIDからメニューIDを取得
        """
        menu_id = ""
        target_table = ""
        target_col = 0

        if orchestra_id == '3':
                menu_id = '2100020109'
                target_table = 'B_ANSIBLE_LNS_VARS_ASSIGN_RIC'
                target_col = 5
        elif orchestra_id == '4':
                menu_id = '2100020210'
                target_table = 'B_ANSIBLE_PNS_VARS_ASSIGN_RIC'
                target_col = 5
        elif orchestra_id == '5':
                menu_id = '2100020311'
                target_table = 'B_ANSIBLE_LRL_VARS_ASSIGN_RIC'
                target_col = 5
        elif orchestra_id == '10':
                menu_id = '2100080008'
                target_table = 'B_TERRAFORM_VARS_ASSIGN_RIC'
                target_col = 4

        return menu_id, target_table, target_col

    def set_ary_ita_config(self):
        """
        ary_ita_configの設定
        """
        cipher = AESCipher(settings.AES_KEY)
        password = cipher.decrypt(self.ita_driver.password)

        self.ary_ita_config['Protocol'] = self.ita_driver.protocol
        self.ary_ita_config['Host'] = self.ita_driver.hostname
        self.ary_ita_config['PortNo'] = self.ita_driver.port
        self.ary_ita_config['user'] = self.ita_driver.username
        self.ary_ita_config['password'] = password
        self.ary_ita_config['menuID'] = '2100000303'

    def get_last_info(self, action_his_id, execution_order):
        """
        [概要]
        ITAアクション結果を取得
        """

        self.ITAobj = ITA1Core(
            self.trace_id,
            self.symphony_class_id,
            self.response_id,
            execution_order,
            self.conductor_class_id)
        self.set_ary_ita_config()

        # ITAアクション オブジェクト生成
        if 'SYMPHONY_CLASS_ID' in self.aryActionParameter:
            self.symphony_class_id = self.aryActionParameter['SYMPHONY_CLASS_ID']

        elif 'CONDUCTOR_CLASS_ID' in self.aryActionParameter:
            self.conductor_class_id = self.aryActionParameter['CONDUCTOR_CLASS_ID']

        elif 'SYMPHONY_NAME' in self.aryActionParameter:
            symphony_name = self.aryActionParameter['SYMPHONY_NAME']
            ret, self.symphony_class_id = self.ITAobj.select_symphony(self.ary_ita_config, symphony_name)

            if ret > 0:
                logger.system_log('LOSE01145', self.trace_id, ret, symphony_name)
                return ACTION_EXEC_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_VAL

        else:
            conductor_name = self.aryActionParameter['CONDUCTOR_NAME']
            ret, self.conductor_class_id = self.ITAobj.select_conductor(self.ary_ita_config, conductor_name)

            if ret > 0:
                logger.system_log('LOSE01146', self.trace_id, ret, conductor_name)
                return ACTION_EXEC_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_VAL

        self.ITAobj = ITA1Core(
            self.trace_id,
            self.symphony_class_id,
            self.response_id,
            execution_order,
            self.conductor_class_id)

        logger.logic_log('LOSI00001', 'self.trace_id: %s, action_his_id: %s' % (self.trace_id, action_his_id))

        action_status = ACTION_EXEC_ERROR
        detail_status = ACTION_HISTORY_STATUS.DETAIL_STS.NONE

        try:
            ita_act_his = ItaActionHistory.objects.get(action_his_id=action_his_id)
        except ItaActionHistory.DoesNotExist:
            logger.logic_log('LOSE01127', self.trace_id, action_his_id)
            return action_status, detail_status

        if 'SYMPHONY_CLASS_ID' in self.aryActionParameter or 'SYMPHONY_NAME' in self.aryActionParameter:
            status_id = self.ITAobj.get_last_info(
                self.ary_ita_config,
                ita_act_his.symphony_instance_no,
                ita_act_his.operation_id,
            )
        else:
            status_id = self.ITAobj.get_last_info_conductor(
                self.ary_ita_config,
                ita_act_his.conductor_instance_no,
                ita_act_his.operation_id,
            )
        # SymphonyインスタンスまたはConductorインスタンスの実行時ステータスIDを変換する
        if status_id == 1:
            action_status = ACTION_HISTORY_STATUS.ITA_UNPROCESS
            detail_status = ACTION_HISTORY_STATUS.DETAIL_STS.ITAUNPROC
        elif status_id == 2:
            action_status = ACTION_HISTORY_STATUS.ITA_UNPROCESS
            detail_status = ACTION_HISTORY_STATUS.DETAIL_STS.ITAUNPROC_RESERVE
        elif status_id == 3:
            action_status = ACTION_HISTORY_STATUS.ITA_PROCESSING
            detail_status = ACTION_HISTORY_STATUS.DETAIL_STS.ITAPROC
        elif status_id == 4:
            action_status = ACTION_HISTORY_STATUS.ITA_PROCESSING
            detail_status = ACTION_HISTORY_STATUS.DETAIL_STS.ITAPROC_LATE
        elif status_id == 5:
            action_status = ACTION_HISTORY_STATUS.PROCESSED
            detail_status = ACTION_HISTORY_STATUS.DETAIL_STS.NONE
        elif status_id == 6:
            action_status = ACTION_HISTORY_STATUS.ITA_CANCEL
            detail_status = ACTION_HISTORY_STATUS.DETAIL_STS.ITACANCEL_STOP
        elif status_id == 7:
            action_status = ACTION_HISTORY_STATUS.ITA_ERROR
            detail_status = ACTION_HISTORY_STATUS.DETAIL_STS.ITAERR
        elif status_id == 8:
            action_status = ACTION_HISTORY_STATUS.ITA_ERROR
            detail_status = ACTION_HISTORY_STATUS.DETAIL_STS.ITAERR_UNEXPECT
        elif status_id == 9:
            action_status = ACTION_HISTORY_STATUS.ITA_CANCEL
            detail_status = ACTION_HISTORY_STATUS.DETAIL_STS.ITACANCEL
        else:
            action_status = ACTION_HISTORY_STATUS.ITA_FAIL
            detail_status = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL

        logger.logic_log('LOSI00002', 'return: (%s, %s)' % (action_status, detail_status))
        return action_status, detail_status

    def retry(self, rhdm_res_act, retry=True):
        """
        再実行
        """
        # todo itaは通常実行と再実行が変わるかもしれない
        ActionStatus, detail = self.act(rhdm_res_act, retry=retry)
        return ActionStatus, detail

    def set_information(self, rhdm_res_act, action_history):
        """
        [概要]
          ITA情報登録
        """
        logger.logic_log('LOSI00001', 'action_type_id: %s' % (rhdm_res_act.action_type_id))

        self.action_history = action_history

        param_info = json.loads(rhdm_res_act.action_parameter_info)

        try:
            # アクションサーバリストセット
            self.set_action_server_list(
                param_info, rhdm_res_act.execution_order, rhdm_res_act.response_detail_id)
            # アクションパラメータセット
            self.set_action_parameters(
                param_info, rhdm_res_act.execution_order, rhdm_res_act.response_detail_id)

            # アクションパラメーターチェック
            err_info = self.check_action_parameters()
            if err_info:
                ActionDriverCommonModules.SaveActionLog(
                    self.response_id,
                    rhdm_res_act.execution_order,
                    self.trace_id,
                    err_info['msg_id'],
                    **({'key': err_info['key']})
                )

                raise OASEError(
                    '',
                    'LOSE01114',
                    log_params=[self.trace_id, 'OASE_T_RHDM_RESPONSE_ACTION',
                                rhdm_res_act.response_detail_id, err_info['key']],
                    msg_params={'sts': ACTION_DATA_ERROR,
                                'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_VAL}
                )

            # ドライバーセット
            self.set_driver(rhdm_res_act.execution_order)

        except OASEError as e:
            if e.log_id:
                if e.arg_list and isinstance(e.arg_list, list):
                    logger.system_log(e.log_id, *(e.arg_list))
                else:
                    logger.system_log(e.log_id)

            logger.system_log('LOSE01106', self.trace_id, ACTION_DATA_ERROR)

            if e.arg_dict and isinstance(e.arg_dict, dict) \
                    and 'sts' in e.arg_dict and 'detail' in e.arg_dict:
                return e.arg_dict['sts'], e.arg_dict['detail']

        except Exception as e:
            logger.system_log(*e.args)
            logger.system_log('LOSE01106', self.trace_id, ACTION_DATA_ERROR)
            return ACTION_DATA_ERROR, 0

        logger.logic_log('LOSI00002', 'return: True')
        return 0, 0

    def check_ita_master(self, execution_order):
        """
        [概要]
        
        """

        self.ITAobj = ITA1Core(
            self.trace_id,
            self.symphony_class_id,
            self.response_id,
            execution_order,
            self.conductor_class_id )
        self.set_ary_ita_config()

        # ITAアクション オブジェクト生成
        if 'SYMPHONY_CLASS_ID' in self.aryActionParameter:
            self.symphony_class_id = self.aryActionParameter['SYMPHONY_CLASS_ID']

        elif 'CONDUCTOR_CLASS_ID' in self.aryActionParameter:
            self.conductor_class_id = self.aryActionParameter['CONDUCTOR_CLASS_ID']

        elif 'SYMPHONY_NAME' in self.aryActionParameter:
            symphony_name = self.aryActionParameter['SYMPHONY_NAME']
            ret, self.symphony_class_id = self.ITAobj.select_symphony(self.ary_ita_config, symphony_name)

            if ret > 0:
                logger.system_log('LOSE01145', self.trace_id, ret, symphony_name)
                return ACTION_DATA_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_VAL

        else:
            conductor_name = self.aryActionParameter['CONDUCTOR_NAME']
            ret, self.conductor_class_id = self.ITAobj.select_conductor(self.ary_ita_config, conductor_name)

            if ret > 0:
                logger.system_log('LOSE01146', self.trace_id, ret, conductor_name)
                return ACTION_DATA_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_VAL

        self.ITAobj = ITA1Core(
            self.trace_id,
            self.symphony_class_id,
            self.response_id,
            execution_order,
            self.conductor_class_id )

        if 'SYMPHONY_CLASS_ID' in self.aryActionParameter or 'SYMPHONY_NAME' in self.aryActionParameter:
            code = self.ITAobj.select_ita_master(self.ary_ita_config, self.listActionServer, self.ary_movement_list, self.ary_action_server_id_name)
        else:
            code = self.ITAobj.select_ita_master_conductor(self.ary_ita_config, self.listActionServer, self.ary_movement_list, self.ary_action_server_id_name)

        if code > 0:
            logger.system_log('LOSE01107', self.trace_id, code)
            return ACTION_DATA_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_VAL

        return 0, 0

    def set_driver(self, exe_order):
        """
        ITAドライバをセット
        """
        disp_name = self.aryActionParameter['ITA_NAME']
        try:
            self.ita_driver = ItaDriver.objects.get(ita_disp_name=disp_name)
        except ItaDriver.DoesNotExist:
            ActionDriverCommonModules.SaveActionLog(self.response_id, exe_order, self.trace_id, 'MOSJA01013')
            raise OASEError('', 'LOSE01115', log_params=['OASE_T_ITA_DRIVER', 'ITA_NAME', self.trace_id], msg_params={'sts':ACTION_DATA_ERROR, 'detail':ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_VAL})

    def set_action_server_list(self, aryActionParameter, exe_order, response_detail_id):
        """
        [概要]
        アクションサーバーリストをメンバ変数にセットする
        """
        logger.logic_log('LOSI00001', 'aryActionParameter: %s' %
                        aryActionParameter)
        ActionDriverCommonModules.SaveActionLog(
            self.response_id, exe_order, self.trace_id, 'MOSJA01001')

        key1 = 'ACTION_PARAMETER_INFO'
        if key1 not in aryActionParameter:
            ActionDriverCommonModules.SaveActionLog(
                self.response_id, exe_order, self.trace_id, 'MOSJA01005')
            raise OASEError('', 'LOSE01114', log_params=[self.trace_id, 'OASE_T_RHDM_RESPONSE_ACTION', response_detail_id, key1], msg_params={
                            'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_SRVLIST_KEY})

        # SERVER_LIST サーチ
        key_server_list = 'SERVER_LIST'
        check_info = self.analysis_parameters(aryActionParameter[key1])

        for key, val in check_info.items():
            if key != key_server_list:
                continue

            server_list = val.split(':') if val else []
            if len(server_list) == 0:
                ActionDriverCommonModules.SaveActionLog(
                    self.response_id, exe_order, self.trace_id, 'MOSJA01002')
                raise OASEError('', 'LOSE01113', log_params=['OASE_T_RHDM_RESPONSE_ACTION', response_detail_id, key_server_list, self.trace_id], msg_params={
                                'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_SRVLIST_VAL})

            # 一意のホストリストにする
            self.listActionServer.extend(server_list)


    def set_action_parameters(self, aryActionParameter, exe_order, res_detail_id):
        """
        [概要]
          ITAパラメータ解析
        """
        logger.logic_log('LOSI00001', 'aryActionParameter: %s' % (aryActionParameter))
        ActionDriverCommonModules.SaveActionLog(self.response_id, exe_order, self.trace_id, 'MOSJA01004')

        key1 = 'ACTION_PARAMETER_INFO'
        if key1 not in aryActionParameter:
            ActionDriverCommonModules.SaveActionLog(self.response_id, exe_order, self.trace_id, 'MOSJA01005')
            raise OASEError('', 'LOSE01114', log_params=[self.trace_id, 'OASE_T_RHDM_RESPONSE_ACTION', res_detail_id, key1], msg_params={'sts':ACTION_DATA_ERROR, 'detail':ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_KEY})

        # アクションパラメータ サーチ
        check_info = self.analysis_parameters(aryActionParameter[key1])
        for key, val in check_info.items():
            if val:
                self.aryActionParameter[key] = val

    def set_host_data(self, target_host_name, key, name_data):
        """
        [概要]
        ホストグループ名/ホスト名の正常性チェック  
        """
        name_splited = name_data.split('|')
        for rec in name_splited:
            name_splited_c = rec.split(':')
            if len(name_splited_c) < 2:
                continue
            if name_splited_c[0] not in target_host_name:
                continue

            name_splited_c2 = name_splited_c[1].split('&')

            name_splited_c3 = []
            for rec2 in name_splited_c2:
                if len(rec2) <= 0:
                    continue
                name_splited_c3.append(rec2)

            if len(name_splited_c3) > 0:
                target_host_name[name_splited_c[0]][key] = name_splited_c3

        return target_host_name

    def check_action_parameters(self):
        """
        [概要]
          ITAパラメータの正常性チェック
        [戻り値]
          dict : エラー情報(正常時は空白)
        """

        ret_info = {}

        # 必須キー(ITA_NAME)チェック
        if 'ITA_NAME' not in self.aryActionParameter or not self.aryActionParameter['ITA_NAME']:
            ret_info = {'msg_id':'MOSJA01006', 'key':'ITA_NAME'}
            return ret_info

        # 排他キー(SYMPHONY_CLASS_ID, SYMPHONY_NAME, CONDUCTOR_CLASS_ID, CONDUCTOR_NAME)チェック
        key_exists_count = 0
        matual_exclusive_keys = ['SYMPHONY_CLASS_ID', 'SYMPHONY_NAME', 'CONDUCTOR_CLASS_ID', 'CONDUCTOR_NAME']
        for exkey in matual_exclusive_keys:
            if exkey in self.aryActionParameter:
                key_exists_count += 1

        # キーが排他的ではない
        if key_exists_count > 1:
            ret_info = {'msg_id':'MOSJA01062', 'key':['SYMPHONY_CLASS_ID', 'SYMPHONY_NAME', 'CONDUCTOR_CLASS_ID', 'CONDUCTOR_NAME']}
            return ret_info

        # いずれのキーも存在しない
        elif key_exists_count < 1:
            ret_info = {'msg_id':'MOSJA01063', 'key':['SYMPHONY_CLASS_ID', 'SYMPHONY_NAME', 'CONDUCTOR_CLASS_ID', 'CONDUCTOR_NAME']}
            return ret_info

        # キーは存在するが値が不完全
        if (('SYMPHONY_CLASS_ID'  in self.aryActionParameter and not self.aryActionParameter['SYMPHONY_CLASS_ID']) \
        or  ('SYMPHONY_NAME'      in self.aryActionParameter and not self.aryActionParameter['SYMPHONY_NAME']) \
        or  ('CONDUCTOR_CLASS_ID' in self.aryActionParameter and not self.aryActionParameter['CONDUCTOR_CLASS_ID']) \
        or  ('CONDUCTOR_NAME'     in self.aryActionParameter and not self.aryActionParameter['CONDUCTOR_NAME'])):
            ret_info = {'msg_id':'MOSJA01063', 'key':['SYMPHONY_CLASS_ID', 'SYMPHONY_NAME', 'CONDUCTOR_CLASS_ID', 'CONDUCTOR_NAME']}
            return ret_info

        # キー(OPERATION_ID, OPERATION_NAME, SERVER_LIST, MENU_ID, MENU)の有無をチェック
        key_exists_count = 0
        key_menu = ['OPERATION_ID', 'OPERATION_NAME', 'SERVER_LIST', 'MENU_ID','MENU']
        for key in key_menu:
            if key in self.aryActionParameter:
                key_exists_count += 1

        # いずれのキーも存在しない
        if key_exists_count < 1:
            ret_info = {'msg_id':'MOSJA01063', 'key':['OPERATION_ID', 'OPERATION_NAME', 'SERVER_LIST', 'MENU_ID','MENU']}
            return ret_info

        # キーは存在するが値が不完全
        if (('OPERATION_ID'   in self.aryActionParameter and not self.aryActionParameter['OPERATION_ID']) \
        or  ('OPERATION_NAME' in self.aryActionParameter and not self.aryActionParameter['OPERATION_NAME']) \
        or  ('SERVER_LIST'    in self.aryActionParameter and not self.aryActionParameter['SERVER_LIST']) \
        or  ('MENU_ID'        in self.aryActionParameter and not self.aryActionParameter['MENU_ID']) \
        or  ('MENU'           in self.aryActionParameter and not self.aryActionParameter['MENU'])):
            ret_info = {'msg_id':'MOSJA01063', 'key':['OPERATION_ID', 'OPERATION_NAME', 'SERVER_LIST', 'MENU_ID','MENU']}
            return ret_info

        # 排他キー(OPERATION_ID, SERVER_LIST, MENU_ID)チェック
        key_exists_count = 0
        matual_exclusive_keys = ['SERVER_LIST', 'MENU_ID']
        for exkey in matual_exclusive_keys:
            if exkey in self.aryActionParameter:
                key_exists_count += 1

        # キーが排他的ではない
        if key_exists_count > 1:
            ret_info = {'msg_id':'MOSJA01062', 'key':['SERVER_LIST', 'MENU_ID']}
            return ret_info

        # 排他キー(MENU_ID, MENU)チェック
        key_exists_count = 0
        matual_exclusive_keys = ['MENU_ID', 'MENU']
        for exkey in matual_exclusive_keys:
            if exkey in self.aryActionParameter:
                key_exists_count += 1

        # キーが排他的ではない
        if key_exists_count > 1:
            ret_info = {'msg_id':'MOSJA01062', 'key':['MENU_ID', 'MENU']}
            return ret_info

        return ret_info


    @classmethod
    def analysis_parameters(cls, param_list):

        check_info = {}

        for string in param_list:
            for key in cls.ACTIONPARAM_KEYS:
                ret = Comobj.KeyValueStringFind(key, string)
                if ret is not None:
                    check_info[key] = ret

        return check_info

    @classmethod
    def has_action_master(cls):
        """
        [概要]
          アクションマスタの登録確認
        """

        if ItaDriver.objects.all().count():
            return True

        return False

    def is_exastro_suite(self):
        """
        [概要]
        エグザストロシリーズか否か。
        [戻り値]
        True : bool
        """
        return True
