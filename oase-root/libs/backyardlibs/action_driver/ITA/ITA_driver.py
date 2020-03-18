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
from web_app.models.ITA_models import ItaParameterMatchInfo
from web_app.models.ITA_models import ItaParametaCommitInfo

from libs.commonlibs.oase_logger import OaseLogger
from libs.commonlibs.aes_cipher import AESCipher
from libs.commonlibs.define import *

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
        'OPERATION_ID',
        'SERVER_LIST',
        'MENU_ID',
    ]

    def __init__(self, trace_id, response_id, last_update_user):
        self.trace_id = trace_id
        self.response_id = response_id
        self.action_history = None
        self.aryActionParameter = {}
        self.last_update_user = last_update_user

        self.ITAobj = None
        self.ary_ita_config = {}
        self.ary_movement_list = {}
        self.ary_action_server_id_name = {}
        self.listActionServer = []
        self.ita_driver = None  # model


    def ita_action_history_insert(self,aryAnzActionParameter,SymphonyInstanceNO,
            OperationID,SymphonyWorkflowURL, exe_order):
        """
        [概要]
        ITAアクション履歴登録メゾット
        """
        logger.logic_log('LOSI00001', 'trace_id: %s, aryAnzActionParameter: %s, ActionHistoryID: %s, SymphonyInstanceNO: %s, OperationID: %s, SymphonyWorkflowURL: %s' % (self.trace_id, aryAnzActionParameter, self.action_history.pk, SymphonyInstanceNO, OperationID, SymphonyWorkflowURL))

        try:
            with transaction.atomic():
                rcnt = ItaActionHistory.objects.filter(action_his_id=self.action_history.pk).count()
                if rcnt > 0:
                    itaacthist = ItaActionHistory.objects.get(action_his_id=self.action_history.pk)
                    itaacthist.ita_disp_name = aryAnzActionParameter['ITA_NAME']
                    itaacthist.symphony_instance_no = SymphonyInstanceNO
                    itaacthist.symphony_class_id = aryAnzActionParameter['SYMPHONY_CLASS_ID']
                    itaacthist.operation_id = OperationID
                    itaacthist.symphony_workflow_confirm_url = SymphonyWorkflowURL
                    itaacthist.last_update_timestamp = Comobj.getStringNowDateTime()
                    itaacthist.last_update_user = self.last_update_user
                    itaacthist.save(force_update=True)
                else:
                    itaacthist = ItaActionHistory(
                        action_his_id=self.action_history.pk,
                        ita_disp_name=aryAnzActionParameter['ITA_NAME'],
                        symphony_instance_no=SymphonyInstanceNO,
                        symphony_class_id=aryAnzActionParameter['SYMPHONY_CLASS_ID'],
                        operation_id=OperationID,
                        symphony_workflow_confirm_url=SymphonyWorkflowURL,
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


    def ita_parameta_commitinfo_insert(self, execution_order, order, parameter_value):
        """
        [概要]
        ITAパラメータ実行管理登録メゾット
        """
        logger.logic_log('LOSI00001', 'execution_order: %s, order: %s, parameter_value: %s' % (
            execution_order, order, parameter_value))

        try:
            with transaction.atomic():
                itaparcom = ItaParametaCommitInfo(
                    response_id = self.response_id,
                    commit_order = execution_order,
                    ita_order = order,
                    parameter_value = parameter_value,
                    last_update_timestamp = Comobj.getStringNowDateTime(),
                    last_update_user = self.last_update_user,
                )
                itaparcom.save(force_insert=True)

        except Exception as e:
            logger.system_log('LOSE01133', self.trace_id, traceback.format_exc())
            ActionDriverCommonModules.SaveActionLog(self.response_id, execution_order, self.trace_id, 'MOSJA01071')
            return None

        logger.logic_log('LOSI00002', 'ItaParametaCommitInfo pk: %s' % itaparcom.pk)
        return itaparcom


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
        symphony_instance_id = 0
        symphony_url = ''
        server_list = ''
        operation_id = None
        menu_id = None

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

        # OPERATION_ID/SERVER_LIST サーチ
        key_operation_id = 'OPERATION_ID'
        key_server_list = 'SERVER_LIST'
        key_menu_id = 'MENU_ID'
        check_info = self.analysis_parameters(param_info[key1])

        if key_operation_id in check_info:
            if len(check_info[key_operation_id]) == 0:
                ActionDriverCommonModules.SaveActionLog(
                    self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01059')
                raise OASEError('', 'LOSE01128', log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_operation_id, self.trace_id], msg_params={
                                'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL})

            operation_id = check_info[key_operation_id]

        elif key_server_list in check_info:
            if len(check_info[key_server_list]) == 0:
                ActionDriverCommonModules.SaveActionLog(
                    self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01064')
                raise OASEError('', 'LOSE01130', log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_server_list, self.trace_id], msg_params={
                                'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL})

            server_list = check_info[key_server_list]

        elif key_menu_id in check_info:
            if len(check_info[key_menu_id]) == 0:
                ActionDriverCommonModules.SaveActionLog(
                    self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01070')
                raise OASEError('', 'LOSE01132', log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_server_list, self.trace_id], msg_params={
                                'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL})

            menu_id = check_info[key_menu_id]

        # MENU_IDのパターン
        if menu_id:
            # 抽出条件
            ita_param_matchinfo_list = list(ItaParameterMatchInfo.objects.filter(menu_id=menu_id).order_by('match_id'))

            # イベント情報抽出
            events_request = EventsRequest.objects.get(trace_id=self.trace_id)

            # 条件名
            data_object_list = list(DataObject.objects.filter(
                rule_type_id=events_request.rule_type_id).order_by('data_object_id'))

            # イベント情報
            for match in ita_param_matchinfo_list:
                label_list = []
                for obj in data_object_list:
                    if match.conditional_name == obj.conditional_name and not obj.label in label_list:
                        label_list.append(obj.label)
                        number = int(obj.label[5:])
                        message = ast.literal_eval(events_request.event_info)['EVENT_INFO'][number]

                        pattern = match.extraction_method1
                        m = re.search(pattern, message)

                        if m is None:
                            continue
                        elif match.extraction_method2 == '':
                            parameter_value = m.group(0).strip()
                        elif match.extraction_method2 != '':
                            value = m.group(0).split(match.extraction_method2)
                            parameter_value = value[1].strip()

                        ret = self.ita_parameta_commitinfo_insert(
                            rhdm_res_act.execution_order, match.order, parameter_value)

                        if ret is None:
                            return ACTION_EXEC_ERROR, DetailStatus

            return PROCESSED, DetailStatus

        # パラメータシート登録パターン
        if not operation_id and not server_list:
            operation_data = []
            if retry:
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

            # パラメータシート登録
            parameter_list = []
            events_request = EventsRequest.objects.get(trace_id=self.trace_id)
            host_name = ast.literal_eval(events_request.event_info)['EVENT_INFO'][0]
            operation_id = operation_data[0][Cstobj.COL_OPERATION_NO_IDBH]
            operation_name = operation_data[0][Cstobj.COL_OPERATION_NAME]
            exec_schedule_date = '%s_%s:%s' % (
                operation_data[0][Cstobj.COL_OPERATION_DATE],
                operation_data[0][Cstobj.COL_OPERATION_NO_IDBH],
                operation_data[0][Cstobj.COL_OPERATION_NAME])
            parameter_list.append(ast.literal_eval(events_request.event_info)['EVENT_INFO'][1])

            ret = self.ITAobj.insert_c_parameter_sheet(
                host_name, operation_id, operation_name, exec_schedule_date, parameter_list)
            if ret == Cstobj.RET_REST_ERROR:
                logger.system_log('LOSE01110', ActionStatus, self.trace_id)
                DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_PARAM_FAIL

                return ACTION_EXEC_ERROR, DetailStatus

            ActionDriverCommonModules.SaveActionLog(
                self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01067')

            return ACTION_HISTORY_STATUS.ITA_REGISTERING_SUBSTITUTION_VALUE, DetailStatus

        # SERVER_LISTのパターン
        if server_list:
            if retry:
                # 再実行の際、登録前にエラーになっていた場合は登録処理から行う。
                ret = self.ITAobj.select_ope_ita_master(
                    self.ary_ita_config, operation_id)
                if ret == Cstobj.RET_DATA_ERROR:
                    ActionDriverCommonModules.SaveActionLog(
                        self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01056')
                    ret = self.ITAobj.insert_ita_master(
                        self.ary_ita_config, self.ary_movement_list, self.ary_action_server_id_name, list_operation_id)

            else:
                ret = self.ITAobj.insert_ita_master(
                    self.ary_ita_config, self.ary_movement_list, self.ary_action_server_id_name, list_operation_id)
                if ret > 0:
                    DetailStatus = ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_OPEID_FAIL
            operation_id = list_operation_id[0]

        ret = self.ITAobj.select_ope_ita_master(
            self.ary_ita_config, operation_id)
        if ret == Cstobj.RET_DATA_ERROR:
            raise OASEError('', 'LOSE01128', log_params=['OASE_T_RHDM_RESPONSE_ACTION', rhdm_res_act.response_detail_id, key_operation_id, self.trace_id], msg_params={
                            'sts': ACTION_DATA_ERROR, 'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_OPEID_VAL})

        code, symphony_instance_id, symphony_url = self.ITAobj.symphony_execute(
            self.ary_ita_config, operation_id)
        if code == 0:
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
            rhdm_res_act.execution_order
        )

        # Symphonyに失敗した場合は異常終了する。
        if ActionStatus != PROCESSED:
            logger.system_log('LOSE01110', ActionStatus, self.trace_id)
            ActionDriverCommonModules.SaveActionLog(self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01040')
            return ACTION_EXEC_ERROR, DetailStatus

        logger.logic_log('LOSI00002', 'return: PROCESSED')
        return ACTION_HISTORY_STATUS.EXASTRO_REQUEST, DetailStatus

    def act_with_menuid(self, act_his_id, exec_order):
        """
        [概要]
        """
        logger.logic_log('LOSI00001', 'self.trace_id: %s, act_his_id: %s, exec_order: %s' % (self.trace_id, act_his_id, exec_order))
        symphony_instance_id = 0
        operation_id = 0
        symphony_url = ''

        self.ITAobj = ITA1Core(self.trace_id, self.aryActionParameter['SYMPHONY_CLASS_ID'], self.response_id, exec_order)
        self.set_ary_ita_config()

        code = self.ITAobj.select_symphony_movement_master(self.ary_ita_config, self.ary_movement_list)

        if code > 0:
            logger.system_log('LOSE01107', self.trace_id, code)
            return ACTION_DATA_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_VAL

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

        for movement_id, value in self.ary_movement_list.items():
            menu_id, target_table = self.orchestrator_id_to_menu_id(value['ORCHESTRATOR_ID'])

            if not menu_id or not target_table:
                logger.logic_log('LOSI00002', 'orchestrator_id: %s, menu_id: %s, target_table: %s' % (value['ORCHESTRATOR_ID'], menu_id, target_table))

                return ACTION_EXEC_ERROR, DetailStatus

            if not self.ITAobj.select_substitution_value_mng(self.ary_ita_config, operation_id_name, menu_id, target_table):
                logger.logic_log('LOSI00002', 'orchestrator_id: %s, menu_id: %s, target_table: %s' % (value['ORCHESTRATOR_ID'], menu_id, target_table))

                return ITA_REGISTERING_SUBSTITUTION_VALUE, ACTION_HISTORY_STATUS.DETAIL_STS.NONE

        # Symphony実行()
        code, symphony_instance_id, symphony_url = self.ITAobj.symphony_execute(self.ary_ita_config, operation_id)

        # ITAアクション履歴登録
        logger.logic_log('LOSI01104', str(exec_order), self.trace_id)
        ret = self.ita_action_history_insert(
            self.aryActionParameter,
            symphony_instance_id,
            operation_id,
            symphony_url,
            exec_order
        )

        logger.logic_log('LOSI00002', 'return: PROCESSED')
        return ACTION_HISTORY_STATUS.EXASTRO_REQUEST, ACTION_HISTORY_STATUS.DETAIL_STS.NONE

    def orchestrator_id_to_menu_id(self, orchestra_id):
        """
        [概要]
        オーケストレータIDからメニューIDを取得
        """
        menu_id = ""
        target_table = ""

        if orchestra_id == '3':
                menu_id = '2100020108'
                target_table = 'B_ANSIBLE_LNS_PHO_LINK'
        elif orchestra_id == '4':
                menu_id = '2100020209'
                target_table = 'B_ANSIBLE_PNS_PHO_LINK'
        else:
                menu_id = '2100020310'
                target_table = 'B_ANSIBLE_LRL_PHO_LINK'

        return menu_id, target_table

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
        # ITAアクション オブジェクト生成
        self.ITAobj = ITA1Core(self.trace_id, self.aryActionParameter['SYMPHONY_CLASS_ID'], self.response_id, execution_order)
        self.set_ary_ita_config()

        logger.logic_log('LOSI00001', 'self.trace_id: %s, action_his_id: %s' % (self.trace_id, action_his_id))

        action_status = ACTION_EXEC_ERROR
        detail_status = ACTION_HISTORY_STATUS.DETAIL_STS.NONE

        try:
            ita_act_his = ItaActionHistory.objects.get(action_his_id=action_his_id)
        except ItaActionHistory.DoesNotExist:
            logger.logic_log('LOSE01127', self.trace_id, action_his_id)
            return action_status, detail_status

        status_id = self.ITAobj.get_last_info(
            self.ary_ita_config,
            ita_act_his.symphony_instance_no,
            ita_act_his.operation_id,
        )
        # Symphonyインスタンスの実行時ステータスIDを変換する
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
        # ITAアクション オブジェクト生成
        self.ITAobj = ITA1Core(
            self.trace_id,
            self.aryActionParameter['SYMPHONY_CLASS_ID'],
            self.response_id,
            execution_order)
        self.set_ary_ita_config()

        code = self.ITAobj.select_ita_master(self.ary_ita_config, self.listActionServer, self.ary_movement_list, self.ary_action_server_id_name)

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

        # ITA_NAME/SYMPHONY_CLASS_ID/OPERATION_ID/SERVER_LIST サーチ
        check_info = self.analysis_parameters(aryActionParameter[key1])
        for key, val in check_info.items():
            if val:
                self.aryActionParameter[key] = val


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

        # 必須キー(SYMPHONY_CLASS_ID)チェック
        if 'SYMPHONY_CLASS_ID' not in self.aryActionParameter or not self.aryActionParameter['SYMPHONY_CLASS_ID']:
            ret_info = {'msg_id':'MOSJA01006', 'key':'SYMPHONY_CLASS_ID'}
            return ret_info

        # 排他キー(OPERATION_ID, SERVER_LIST)チェック
        # キーが排他的ではない
        if 'OPERATION_ID' in self.aryActionParameter and 'SERVER_LIST' in self.aryActionParameter:
            ret_info = {'msg_id':'MOSJA01062', 'key':['OPERATION_ID', 'SERVER_LIST']}
            return ret_info

        # いずれのキーも存在しない、もしくは、キーは存在するが値が不完全
        elif (('OPERATION_ID' in self.aryActionParameter and not self.aryActionParameter['OPERATION_ID']) \
        or   ('SERVER_LIST'  in self.aryActionParameter and not self.aryActionParameter['SERVER_LIST'])):
            ret_info = {'msg_id':'MOSJA01063', 'key':['OPERATION_ID', 'SERVER_LIST']}
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
