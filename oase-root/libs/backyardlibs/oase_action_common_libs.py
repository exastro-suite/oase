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

"""
import json
import os
import sys
import re
import pytz
import datetime
from socket import gethostname
import traceback

# import検索パス追加
my_path = os.path.dirname(os.path.abspath(__file__))
tmp_path = my_path.split('oase-root')
root_dir_path = tmp_path[0] + 'oase-root'
sys.path.append(root_dir_path)

# oaseログモジュールのimport
from    web_app.models.models              import ActionLog
from    libs.commonlibs.oase_logger        import OaseLogger
logger = OaseLogger.get_instance() # ロガー初期化


class ConstantModules:
    """
    [クラス概要]
        アクションドライバ コンスタント定義クラス
    """
    ## OASE DB USER
    DB_OASE_USER                      =  -2140000001
    ## module result code
    # deprecate 以下3つのステータスはITA_DBを使っていたもので廃止予定
    RET_REST_ERROR                    =  100  # REST Access Error
    RET_DATA_ERROR                    =  101  # DBの登録データが異常
    RET_REST_MULTI_UPDATE             =  102  # 追越し更新

    ## テーブルカラム位置
    ## 共通
    COL_FUNCTION_NAME                 =  0
    COL_DISUSE_FLAG                   =  1

    ## C_MOVEMENT_CLASS_MNG
    CMCM_MOVEMENT_CLASS_NO            =  2
    CMCM_ORCHESTRATOR_ID              =  3
    CMCM_PATTERN_ID                   =  4
    CMCM_MOVEMENT_SEQ                 =  5
    CMCM_NEXT_PENDING_FLAG            =  6
    CMCM_DESCRIPTION                  =  7
    CMCM_SYMPHONY_CLASS_NO            =  8
    CMCM_NOTE                         =  9
    CMCM_LAST_UPDATE_TIMESTAMP        = 10
    CMCM_UPDATE_LAST_UPDATE_TIMESTAMP = 11
    CMCM_LAST_UPDATE_USER             = 12

    ## C_STM_LIST
    CSL_SYSTEM_ID                     =  2
    CSL_HARDAWRE_TYPE_ID              =  3
    CSL_HOSTNAME                      =  4
    CSL_IP_ADDRESS                    =  5

    ## C_OPERATION_LIST
    COL_OPERATION_NO_UAPK             =  2
    COL_OPERATION_NO_IDBH             =  3
    COL_OPERATION_NAME                =  4
    COL_OPERATION_DATE                =  5
    COL_NOTE                          =  6
    COL_LAST_UPDATE_TIMESTAMP         =  7
    COL_UPDATE_LAST_UPDATE_TIMESTAMP  =  8
    COL_LAST_UPDATE_USER              =  9
    TBL_COL_MAX                       =  COL_LAST_UPDATE_USER + 1

    ## C_PARAMETER_SHEET
    COL_HOSTNAME                      =  3
    COL_OPERATION_ID                  =  4
    COL_OPERATION_NAME_PARAM          =  5
    COL_SCHEDULE_TIMESTAMP_ID_NAME    =  9
    COL_PARAMETER                     =  10
    TBL_CPS_MAX                       =  COL_PARAMETER + 1

    ## C_PATTERN_PER_ORCH
    CPPO_PATTERN_ID                   =  2
    CPPO_PATTERN_NAME                 =  3
    CPPO_ITA_EXT_STM_ID               =  4

    ## B_ANSIBLE_xxx_PHO_LINK
    BAPL_PHO_LINK_ID                  =  2
    BAPL_OPERATION_NO_UAPK            =  3
    BAPL_PATTERN_ID                   =  4
    BAPL_SYSTEM_ID                    =  5
    BAPL_NOTE                         =  6
    BAPL_LAST_UPDATE_TIMESTAMP        =  7
    BAPL_UPDATE_LAST_UPDATE_TIMESTAMP =  8
    BAPL_LAST_UPDATE_USER             =  9
    TBL_BAPL_MAX                      =  BAPL_LAST_UPDATE_USER + 1

    #OASE_T_RHDM_RESPONSE
    OTRR_RESPONSE_ID                  = 2
    OTRR_REQUEST_TYPE_ID              = 5
    OTRR_STATUS                       = 6
    OTRR_UPDATE_STATUS_ID             = 7

    #OASE_T_RHDM_RESPONSE_ACTION
    OTRRA_RESPONSE_ID                 = 3
    OTRRA_EXECUTION_ORDER             = 5

    #OASE_T_ACTION_HISTORY
    OTAH_RESPONSE_ID                  = 3
    OTAH_RULE_NAME                    = 5
    OTAH_EXECUTION_ORDER              = 6
    OTAH_ACTION_START_TIME            = 7
    OTAH_ACTION_TYPE_ID               = 8
    OTAH_STATUS                       = 10

    #OASE_T_ITA_DRIVER
    OTID_ITA_DISP_NAME                = 3

    #OASE_T_MAIL_DRIVER
    OTMD_MAIL_DISP_NAME               = 3

    #OASE_T_MAIL_TEMPLATE
    OTMT_MAIL_TEMPLATE_NAME           = 3

    #トレースIDがない場合の設定値
    UnsetTraceID                      = '----------------------------------------'

class ActionDriverCommonModules:
    """
    [クラス概要]
        アクションドライバ共通処理クラス
    """
    def getStringNowDate(self):
        """
        [概要]
          現在日付を文字列で取得するメソット
        """
        now = datetime.datetime.now(pytz.timezone('UTC'))
        return now.strftime("%Y/%m/%d")


    @classmethod
    def getStringNowDateTime(cls, convert_flg=False):
        """
        [概要]
          現在日時を文字列で取得するメソット
        """
        now = datetime.datetime.now(pytz.timezone('UTC'))
        if convert_flg:
            return now.strftime("%Y-%m-%d %H:%M:%S.%f")

        return now


    def KeyValueStringFind(self,pattern,string):
        """
        [概要]
          Key Value型文字列からValueを抜き出すメソット
        """
        string_tmp = string.split('=')
        if len(string_tmp) < 2:
            return None

        key = string_tmp[0]
        if key != pattern:
            return None

        val = '='.join(string_tmp[1:])
        return val

    @classmethod
    def back_trace(self):
        """
        [概要]
          Key Value型文字列からValueを抜き出すメソット
        """
        exc_type, exc_value, exc_traceback = sys.exc_info()
        stack_trace = traceback.format_exception(exc_type, exc_value, exc_traceback)
        edit_trace = ''
        for line in stack_trace:
            edit_trace = edit_trace  + line
        return edit_trace

    @staticmethod
    def SaveActionLog(resp_id, exe_order, trace_id, msg_id, **kwargs):
        """
        [概要]
          アクション履歴ログを保存する
        """

        now = datetime.datetime.now(pytz.timezone('UTC'))
        msg_params = None
        if kwargs:
            msg_params = '%s' % (kwargs)

        try:
            ActionLog(
                response_id           = resp_id,
                execution_order       = exe_order,
                trace_id              = trace_id,
                message_id            = msg_id,
                message_params        = msg_params,
                last_update_timestamp = now
            ).save(force_insert=True)

        except Exception as ex:
            logger.system_log('LOSM01007', resp_id, exe_order, trace_id, msg_id, msg_params)

# libs/webcommonlibs/common.py から引用
class TimeConversion:
    @classmethod
    def get_time_conversion(cls, naive, tz):
        """
        [概要]
        時刻変換処理を行う
        [戻り値]
        変換した時刻
        """

        return naive.astimezone(pytz.timezone(tz)).strftime('%Y-%m-%d %H:%M:%S')


    @classmethod
    def get_time_conversion_utc(cls, naive, tz):
        """
        [概要]
        時刻変換処理を行う
        [戻り値]
        utc_dt : 変換した時刻(UTC)
        """

        tz_ex   = pytz.timezone(tz)
        naive   = naive.replace('/', '-')
        user_dt = datetime.datetime.strptime(naive, '%Y-%m-%d %H:%M:%S')
        cou_dt  = tz_ex.localize(user_dt, is_dst=None)
        utc_dt  = cou_dt.astimezone(pytz.utc)

        return utc_dt

