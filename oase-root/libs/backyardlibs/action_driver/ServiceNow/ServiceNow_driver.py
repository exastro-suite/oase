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
  アクションドライバ アクション実行処理（ServiceNow）


"""

import os
import sys
import json
import django
import traceback

# OASE モジュール importパス追加
my_path = os.path.dirname(os.path.abspath(__file__))
tmp_path = my_path.split('oase-root')
root_dir_path = tmp_path[0] + 'oase-root'
sys.path.append(root_dir_path)

# OASE モジュール import
# #LOCAL_PATCH#
os.environ['DJANGO_SETTINGS_MODULE'] = 'confs.frameworkconfs.settings'
django.setup()

from django.db import transaction

# ロガー初期化
from libs.commonlibs.oase_logger import OaseLogger
logger = OaseLogger.get_instance()


from libs.backyardlibs.action_driver.common.action_abstract import AbstractManager
from libs.webcommonlibs.oase_exception import OASEError
from libs.backyardlibs.action_driver.ServiceNow.ServiceNow_core import ServiceNow1Core
from libs.backyardlibs.oase_action_common_libs import ActionDriverCommonModules
from libs.commonlibs.define import *
from libs.commonlibs.aes_cipher import AESCipher
from web_app.models.models import ActionHistory
from web_app.models.ServiceNow_models import *


Comobj = ActionDriverCommonModules()


class ServiceNowManager(AbstractManager):
    """
    [クラス概要]
        アクションドライバメイン処理クラス
    """

    ############################################
    # 定数
    ############################################
    # アクション情報キーリスト
    ACTIONPARAM_KEYS = [
        'SERVICENOW_NAME',
        'INCIDENT_STATUS',
    ]

    # アクション情報の必須キーリスト
    ACTIONPARAM_KEYS_REQUIRE = [
        'SERVICENOW_NAME',
        'INCIDENT_STATUS',
    ]


    ############################################
    # メソッド
    ############################################
    def __init__(self, trace_id, response_id, last_update_user):

        self.servicenow_driver = None
        self.action_history = None

        self.trace_id = trace_id
        self.response_id = response_id
        self.last_update_user = last_update_user

        self.aryActionParameter = {}

        self.core = ServiceNow1Core(trace_id)


    def servicenow_action_history_insert(self, servicenow_name, sys_id, short_desc, exe_order, action_history_id):
        """
        [概要]
          ServiceNowアクション履歴登録メゾット
        """

        logger.logic_log(
            'LOSI00001',
            'servicenow_name: % s, short_desc: % s, exe_order: % s, action_history_id: % s' % (
                servicenow_name, short_desc, exe_order, action_history_id))

        try:
            with transaction.atomic():
                ServiceNowActionHistory(
                    action_his_id=action_history_id,
                    servicenow_disp_name=servicenow_name,
                    sys_id=sys_id,
                    short_description=short_desc,
                    last_update_timestamp=Comobj.getStringNowDateTime(),
                    last_update_user=self.last_update_user,
                ).save(force_insert=True)

        except Exception as e:
            logger.system_log('LOSE01141', self.trace_id, traceback.format_exc())
            ActionDriverCommonModules.SaveActionLog(
                self.response_id, exe_order, self.trace_id, 'MOSJA01085'
            )

        logger.logic_log('LOSI00002', 'None')


    def reset_variables(self):
        """
        [概要]
          メンバ変数を初期化する 
        """

        self.servicenow_driver = None
        self.aryActionParameter = {}


    def set_information(self, rhdm_res_act, action_history):
        """
        [概要]
          ServiceNow情報をインスタンス変数にセット
        """

        logger.logic_log('LOSI00001', 'action_type_id: %s' %
                         (rhdm_res_act.action_type_id))

        self.action_history = action_history

        try:
            # アクションパラメータ解析
            param_info = json.loads(rhdm_res_act.action_parameter_info)
            self.set_action_parameters(
                param_info, rhdm_res_act.execution_order,
                rhdm_res_act.response_detail_id
            )
            self.set_driver(rhdm_res_act.execution_order)

        except OASEError as e:
            if e.log_id:
                if e.arg_list and isinstance(e.arg_list, list):
                    logger.system_log(e.log_id, *(e.arg_list))
                else:
                    logger.system_log(e.log_id)

            if e.arg_dict and isinstance(e.arg_dict, dict) \
                    and 'sts' in e.arg_dict and 'detail' in e.arg_dict:
                return e.arg_dict['sts'], e.arg_dict['detail']

        except Exception as e:
            logger.system_log(*e.args)
            return ACTION_DATA_ERROR, 0

        logger.logic_log('LOSI00002', 'return: True')
        return 0, 0


    def set_driver(self, exe_order):
        """
        [概要]
          ServiceNowドライバーmodelをセット
        """

        disp_name = self.aryActionParameter['SERVICENOW_NAME']

        try:
            self.servicenow_driver = ServiceNowDriver.objects.get(servicenow_disp_name=disp_name)

        except ServiceNowDriver.DoesNotExist:
            ActionDriverCommonModules.SaveActionLog(
                self.response_id, exe_order, self.trace_id, 'MOSJA01086')

            raise OASEError(
                '',
                'LOSE01115',
                log_params=['OASE_T_SERVICENOW_DRIVER', 'SERVICENOW_NAME', self.trace_id],
                msg_params={
                    'sts': ACTION_DATA_ERROR,
                    'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_VAL
                }
            )


    def set_action_parameters(self, param_list, exe_order, response_detail_id, pre_flg=False, post_flg=False):
        """
        [概要]
          ServiceNowパラメータ解析
        """

        logger.logic_log('LOSI00001', 'param_list: %s' % (param_list))

        ActionDriverCommonModules.SaveActionLog(
            self.response_id, exe_order, self.trace_id, 'MOSJA01004'
        )

        # アクションパラメータ情報の存在チェック
        key1 = 'ACTION_PARAMETER_INFO'
        if key1 not in param_list:
            ActionDriverCommonModules.SaveActionLog(
                self.response_id, exe_order, self.trace_id, 'MOSJA01005'
            )

            raise OASEError(
                '',
                'LOSE01114',
                log_params=[
                    self.trace_id,
                    'OASE_T_RHDM_RESPONSE_ACTION',
                    response_detail_id,
                    key1
                ],
                msg_params={
                    'sts': ACTION_DATA_ERROR,
                    'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_KEY
                }
            )

        # アクションパラメータ情報のキー値チェック
        check_info = self.analysis_parameters(param_list[key1])
        for key, val in check_info.items():

            # 必須キーが記述されていない場合はデータ異常
            if val is None:
                ActionDriverCommonModules.SaveActionLog(
                    self.response_id, exe_order, self.trace_id, 'MOSJA01006', **{'key': key}
                )

                raise OASEError(
                    '',
                    'LOSE01114',
                    log_params=[
                        self.trace_id, 'OASE_T_RHDM_RESPONSE_ACTION',
                        response_detail_id, key
                    ],
                    msg_params={
                        'sts': ACTION_DATA_ERROR,
                        'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_KEY
                    }
                )

            # 必須キーの値が空の場合はデータ異常
            if val == '' and key in self.ACTIONPARAM_KEYS_REQUIRE:
                ActionDriverCommonModules.SaveActionLog(
                    self.response_id, exe_order, self.trace_id, 'MOSJA01006', **{'key': key}
                )
                raise OASEError(
                    '',
                    'LOSE01114',
                    log_params=[
                        self.trace_id, 'OASE_T_RHDM_RESPONSE_ACTION',
                        response_detail_id, key
                    ],
                    msg_params={
                        'sts': ACTION_DATA_ERROR,
                        'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_VAL
                    }
                )

            self.aryActionParameter[key] = val


    @classmethod
    def analysis_parameters(cls, param_list):
        """
        [概要]
          アクション情報キーに指定された値を返す
        [引数]
          param_list : list : アクション情報に記述されたキー値ペアのリスト
        [戻り値]
          check_info : dict : アクション情報に記述された値、記述がなければNoneを返す
        """

        check_info = {}
        for key in cls.ACTIONPARAM_KEYS:
            check_info[key] = None

        for string in param_list:
            for key in cls.ACTIONPARAM_KEYS:
                ret = Comobj.KeyValueStringFind(key, string)
                if ret is not None:
                    check_info[key] = ret

        return check_info


    def get_act_ptrn(self):
        """
        [概要]
          アクション情報の値により呼び出す関数を取得する
        """

        if 'INCIDENT_STATUS' not in self.aryActionParameter:

            return None

        if self.aryActionParameter['INCIDENT_STATUS'] == 'OPEN':

            return self.act_open_incident

        if self.aryActionParameter['INCIDENT_STATUS'] == 'CLOSE':

            return self.act_close_incident

        return None


    def act(self, rhdm_res_act, retry=False, pre_flag=False):
        """
        [概要]
            ServiceNowアクションを実行
        """

        logger.logic_log(
            'LOSI00001', 
            'self.trace_id: %s, aryActionParameter: %s' % (self.trace_id, self.aryActionParameter)
        )


        status = ACTION_EXEC_ERROR
        detail = ACTION_HISTORY_STATUS.DETAIL_STS.NONE


        act_func = self.get_act_ptrn()
        if act_func:
            status, detail = act_func(rhdm_res_act, retry, pre_flag)


        logger.logic_log('LOSI00002', 'sts:%s, detail:%s' % (status, detail))

        return status, detail


    def act_open_incident(self, rhdm_res_act, retry, pre_flag):
        """
        [概要]
            ServiceNowアクションを実行
            インシデント新規作成
        """

        logger.logic_log(
            'LOSI00001', 
            'self.trace_id: %s, aryActionParameter: %s' % (self.trace_id, self.aryActionParameter)
        )


        # リクエスト送信
        result, sys_id = self.core.create_incident(self.servicenow_driver)

        # リクエスト結果判定
        status = PROCESSED if result else ACTION_EXEC_ERROR

        logger.logic_log(
            'LOSI01108', 
            status, str(rhdm_res_act.execution_order), self.trace_id
        )

        # 初回実行の場合は履歴情報を登録
        if not retry:
            # ServiceNowアクション履歴登録
            logger.logic_log(
                'LOSI01125',
                str(rhdm_res_act.execution_order), self.trace_id
            )

            self.servicenow_action_history_insert(
                self.servicenow_driver.servicenow_disp_name,
                sys_id,
                'OASE Event Notify',
                rhdm_res_act.execution_order,
                self.action_history.pk,
            )

        # リクエストに失敗した場合は異常終了する。
        if status != PROCESSED:
            logger.system_log('LOSE01142', status, self.trace_id, 'incident')
            ActionDriverCommonModules.SaveActionLog(
                self.response_id,
                rhdm_res_act.execution_order,
                self.trace_id,
                'MOSJA01087'
            )

            return ACTION_EXEC_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_SEND_FAIL

        logger.logic_log('LOSI00002', 'return: PROCESSED')
        return PROCESSED, ACTION_HISTORY_STATUS.DETAIL_STS.NONE


    def retry(self, rhdm_res_act, retry=True):
        """
        [概要]
          再実行
        """

        status, detail = self.act(rhdm_res_act, retry=retry)
        return status, detail


    def act_close_incident(self, rhdm_res_act, retry, pre_flag):
        """
        [概要]
          アクション実行後処理
        """

        logger.logic_log(
            'LOSI00001', 
            'self.trace_id:%s, aryActionParameter:%s' % (self.trace_id, self.aryActionParameter)
        )

        status = PROCESSED
        detail = ACTION_HISTORY_STATUS.DETAIL_STS.NONE

        # sys_id取得
        sys_id = None
        try:
            act_his = ActionHistory.objects.filter(
                trace_id             = self.trace_id,
                action_type_id       = ACTION_TYPE_ID.SERVICENOW,
                execution_order__lt  = rhdm_res_act.execution_order
            ).order_by('-execution_order')[0]

            sys_id = ServiceNowActionHistory.objects.get(action_his_id=act_his.action_history_id).sys_id

        except ServiceNowActionHistory.DoesNotExist:
            logger.logic_log('LOSM01501', self.trace_id, act_his.action_history_id)
            ActionDriverCommonModules.SaveActionLog(
                self.response_id,
                rhdm_res_act.execution_order,
                self.trace_id,
                'MOSJA01106'
            )

            status = SERVER_ERROR
            detail = ACTION_HISTORY_STATUS.DETAIL_STS.NONE

        except Exception as e:
            logger.logic_log('LOSM01501', self.trace_id, None)
            ActionDriverCommonModules.SaveActionLog(
                self.response_id,
                rhdm_res_act.execution_order,
                self.trace_id,
                'MOSJA01106'
            )

            status = SERVER_ERROR
            detail = ACTION_HISTORY_STATUS.DETAIL_STS.NONE

        if not sys_id:
            logger.logic_log('LOSI01126', self.trace_id, self.action_history.pk)
            return status, detail


        # アクション種別取得
        str_resolver = 'Unknown'
        if rhdm_res_act.action_type_id == ACTION_TYPE_ID.ITA:
            str_resolver = 'Exastro IT Automation'

        elif rhdm_res_act.action_type_id == ACTION_TYPE_ID.MAIL:
            str_resolver = 'Mail'

        elif rhdm_res_act.action_type_id == ACTION_TYPE_ID.SERVICENOW:
            str_resolver = 'ServiceNow'


        # インシデントクローズ
        data = {
            'state'       : '7',  # 7:Close
            'close_notes' : 'Resolved by %s. Closed by %s' % (str_resolver, self.last_update_user),
            'close_code'  : 'Closed/Resolved by Caller',
        }

        result = self.core.modify_incident(self.servicenow_driver, sys_id, data)
        if not result:
            status = SERVER_ERROR
            detail = ACTION_HISTORY_STATUS.DETAIL_STS.NONE
            ActionDriverCommonModules.SaveActionLog(
                self.response_id,
                rhdm_res_act.execution_order,
                self.trace_id,
                'MOSJA01087'
            )

        logger.logic_log(
            'LOSI00002', 
            'self.trace_id:%s, sts:%s, detail:%s' % (self.trace_id, status, detail)
        )

        return status, detail


    @classmethod
    def has_action_master(cls):
        """
        [概要]
          アクションマスタの登録確認
        """

        if ServiceNowDriver.objects.all().count():
            return True

        return False


