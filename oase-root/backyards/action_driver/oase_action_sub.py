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
アクションドライバ アクション実行処理（子プロセス）
"""

import os
import sys
import json
import re
import fasteners
from time import sleep
import pytz
import datetime
import django
import traceback
import ast
from collections import OrderedDict
from abc import ABCMeta, abstractmethod
import abc
from socket import gethostname

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

#################################################
# デバック用
if settings.DEBUG and getattr(settings, 'ENABLE_NOSERVICE_BACKYARDS', False):
    oase_root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..')
    os.environ['OASE_ROOT_DIR'] = oase_root_dir 
    os.environ['RUN_INTERVAL']  = '10'
    os.environ['PYTHON_MODULE'] = '/usr/bin/python3'
    os.environ['LOG_LEVEL']     = "TRACE"
    os.environ['LOG_DIR']       = oase_root_dir + "/logs/backyardlogs/oase_action"
#################################################
# 環境変数取得
try:
    root_dir_path = os.environ['OASE_ROOT_DIR']
    run_interval  = os.environ['RUN_INTERVAL']
    python_module = os.environ['PYTHON_MODULE']
    log_dir       = os.environ['LOG_DIR']
    log_level     = os.environ['LOG_LEVEL']
except Exception as ex:
    print(str(ex))
    sys.exit(2)

# ロガー初期化
from libs.commonlibs.oase_logger import OaseLogger
logger = OaseLogger.get_instance()

#################################################
# 負荷テスト設定
ENABLE_LOAD_TEST = getattr(settings, 'ENABLE_LOAD_TEST', False)
if ENABLE_LOAD_TEST:
    import time
    import logging
    loadtest_logger = logging.getLogger('oase_action_sub')


from web_app.models.models import User
from web_app.models.models import RhdmResponse
from web_app.models.models import RhdmResponseAction
from web_app.models.models import ActionHistory
from web_app.models.models import System
from web_app.models.models import EventsRequest
from web_app.models.models import RuleType
from web_app.models.models import DataObject
from web_app.models.models import ActionType
from web_app.models.models import PreActionHistory
from web_app.models.models import DriverType
from web_app.templatetags.common import get_message

from libs.commonlibs.common import Common
from libs.commonlibs.define import *

from libs.backyardlibs.oase_action_common_libs import ActionDriverCommonModules as ActCommon
from libs.backyardlibs.oase_action_common_libs import ConstantModules as Cstobj
from libs.backyardlibs.oase_action_common_libs import TimeConversion 

from libs.webcommonlibs.oase_exception import OASEError

from importlib import import_module

from collections import defaultdict

#-----------------------------------------------
# todo db操作系外だし　ライブラリに移動するか？
#-----------------------------------------------

def update_action_history(action_history, status, detail, user, retry=False, countup=0):
    """
    [概要]
      アクション履歴更新メゾット
    """

    logger.logic_log('LOSI00001', 'status: %s' % (status))
    try:
        with transaction.atomic():
            if retry:
                action_history.retry_status = status
                action_history.retry_status_detail = detail
            else:
                action_history.status = status
                action_history.status_detail = detail

            action_history.action_retry_count = action_history.action_retry_count + countup
            action_history.status_update_id = gethostname()
            action_history.last_update_user = user
            action_history.last_update_timestamp = ActCommon.getStringNowDateTime()
            action_history.save(force_update=True)

    except Exception as e:
        logger.system_log('LOSE01104', self.trace_id, traceback.format_exc())
        return False 

    logger.logic_log('LOSI00002', 'None')
    return True


def update_pre_action_history(action_history_pre, status, user, retry=False):
    """
    [概要]
      アクション履歴更新メゾット
    """

    logger.logic_log('LOSI00001','status: %s' % (status))
    try:
        with transaction.atomic():
            action_history_pre.status = status
            action_history_pre.last_update_user = user
            action_history_pre.last_update_timestamp = ActCommon.getStringNowDateTime()
            action_history_pre.save(force_update=True)

    except Exception as e:
        logger.system_log('LOSE01104', self.trace_id, traceback.format_exc())

    logger.logic_log('LOSI00002', 'None')


class ActionDriverMainModules:
    """
    [クラス概要]
        アクションドライバメイン処理クラス
    """
    def __init__(self):
        """
        [概要]
          コンストラクタ
        """
        self.last_update_user = User.objects.get(user_id=Cstobj.DB_OASE_USER).user_name
        self.hostname = gethostname()

    def OASE_T_RHDM_RESPONSE_update(self,rhdm_response):
        """
        [概要]
          ルールマッチング結果管理更新メゾット
        """
        logger.logic_log('LOSI00001', 'None')

        try:
            with transaction.atomic():
                    rhdm_response.status_update_id = self.hostname
                    rhdm_response.last_update_user = self.last_update_user
                    rhdm_response.last_update_timestamp = ActCommon.getStringNowDateTime()
                    rhdm_response.save(force_update=True)
            return True 

        except Exception as ex:
            logger.logic_log('LOSM01001', traceback.format_exc())
            return False


    def UpdateActionHistoryToRetry(self, action_history):
        """
        [概要]
          再実行させるようにアクション履歴を更新する
        """

        logger.logic_log('LOSI00001', 'action_history_id: %s' % (action_history.pk))
        try:
            with transaction.atomic():
                action_history.retry_status = PROCESSING
                action_history.retry_status_detail = 0
                action_history.retry_flag = False
                action_history.status_update_id = gethostname()
                action_history.last_update_user = self.last_update_user
                action_history.last_update_timestamp = ActCommon.getStringNowDateTime()
                action_history.save(force_update=True)

                logger.logic_log('LOSI00002', 'None')

                return True

        except Exception as e:
            logger.logic_log('LOSM01001', traceback.format_exc())
            return False


class ActionDriverSubModules:
    """
    [クラス概要]
        アクションドライバメイン処理クラス
    """

    def __init__(self, response_id=0, trace_id='', resume_order=0):
        """
        [概要]
          コンストラクタ
        """

        # クラス生成
        self.action_history = None
        self.action_history_pre = None
        self.response_id = response_id
        self.trace_id = trace_id
        self.resume_order = resume_order
        self.save_resume = 0
        self.save_resume_time = None
        self.user_objects = User.objects.get(user_id=Cstobj.DB_OASE_USER)
        self.user = self.user_objects.user_name
        self.load_drivers()
        self.preact_manager = None
        self.driver_manager = None

    def load_drivers(self):
        """動的にインストール済みのドライバーを読み込む"""

        self.action_type_list = []
        self.driver_type_info = {}

        # 有効なアクション種別を取得
        driver_type_list = []
        act_types = ActionType.objects.filter(disuse_flag='0').values_list('action_type_id', 'driver_type_id')
        for act_type_id, drv_type_id in act_types:
            self.action_type_list.append(act_type_id)
            driver_type_list.append(drv_type_id)

        # 有効なアクション種別からドライバー情報を取得
        drv_types = []
        if len(driver_type_list) > 0:
            drv_types = DriverType.objects.filter(driver_type_id__in=driver_type_list).values('driver_type_id', 'name', 'driver_major_version', 'exastro_flag')

        # アクション種別とドライバー情報を紐付ける
        for act_type_id, drv_type_id in act_types:
            for dt in drv_types:
                if drv_type_id != dt['driver_type_id']:
                    continue

                self.driver_type_info[act_type_id] = {
                    'id'      : dt['driver_type_id'],
                    'name'    : dt['name'],
                    'ver'     : dt['driver_major_version'],
                    'exastro' : dt['exastro_flag'],
                }

                break

            # 予期せぬドライバーがインストール状態
            else:
                logger.system_log('LOSM01010', self.trace_id, act_type_id, drv_type_id)


    def reset_variables(self):
        """
        [概要]
          メンバ変数、ドライバーを初期化する 
        """

        if self.preact_manager is not None:
            self.preact_manager.reset_variables()

        # driverは都度作り直す。(todo 再利用できるようにすると効率が良い)
        self.driver_manager = None

        self.save_resume_time = None


    def insert_action_history(self, rhdm_res_act, status, detail):
        """
        [概要]
          アクション履歴登録メゾット
        """
        logger.logic_log('LOSI00001', 'trace_id: %s, response_id: %s, status: %s, detail: %s' % (self.trace_id, rhdm_res_act.response_id, status, detail))

        try:
            with transaction.atomic():
                rcnt = ActionHistory.objects.filter(response_id=rhdm_res_act.response_id, execution_order=rhdm_res_act.execution_order).count()
                if rcnt > 0:
                    action_history = ActionHistory.objects.get(response_id=rhdm_res_act.response_id, execution_order=rhdm_res_act.execution_order)
                    action_history.status = status
                    action_history.status_detail = detail
                    action_history.status_update_id = gethostname()
                    action_history.last_update_timestamp = ActCommon.getStringNowDateTime()
                    action_history.last_update_user = self.user
                    action_history.save(force_update=True)

                else:
                    rhdm_res = RhdmResponse.objects.get(response_id=rhdm_res_act.response_id)
                    events_request = EventsRequest.objects.get(trace_id=rhdm_res.trace_id)
                    rule_type = RuleType.objects.get(pk=events_request.rule_type_id)

                    action_history = ActionHistory(
                        response_id           = rhdm_res_act.response_id,
                        trace_id              = self.trace_id,
                        rule_type_id          = events_request.rule_type_id,
                        rule_type_name        = rule_type.rule_type_name,
                        rule_name             = rhdm_res_act.rule_name,
                        execution_order       = rhdm_res_act.execution_order,
                        action_start_time     = ActCommon.getStringNowDateTime(True),
                        action_type_id        = rhdm_res_act.action_type_id,
                        status                = status,
                        status_detail         = detail,
                        status_update_id      = gethostname(),
                        action_retry_count    = 0,
                        last_act_user         = self.user,
                        last_update_timestamp = ActCommon.getStringNowDateTime(),
                        last_update_user      = self.user,
                    )
                    action_history.save(force_insert=True)

        except Exception as e:
            logger.system_log('LOSE01102', self.trace_id, traceback.format_exc())
            return None

        logger.logic_log('LOSI00002', 'action_history_id: %s' % (str(action_history.pk)))

        return action_history


    def insert_pre_action_history(self, status):
        """
        [概要]
          アクション履歴登録メゾット
        """
        logger.logic_log('LOSI00001', 'trace_id: %s, action_history_id: %s, status: %s' % (self.trace_id, self.action_history.action_history_id, status))

        try:
            with transaction.atomic():
                action_history_pre = PreActionHistory(
                    action_history_id     = self.action_history.action_history_id,
                    trace_id              = self.trace_id,
                    status                = status,
                    last_update_timestamp = ActCommon.getStringNowDateTime(),
                    last_update_user      = self.user,
                )
                action_history_pre.save(force_insert=True)

        except Exception as e:
            logger.system_log('LOSE01102', self.trace_id, traceback.format_exc())
            return None 

        logger.logic_log('LOSI00002', 'trace_id: %s, preact_history_id: %s' % (self.trace_id, action_history_pre.preact_history_id))

        return action_history_pre


    def should_approved(self):
        """
        事前実行メールチェック
        承認必要ならTrue、不要ならFalse
        """
        return True if self.preact_manager and self.preact_manager.aryActionParameter else False



    def preact(self, rhdm_res_act, retry=False):
        """
        事前実行メール処理 
        """
        logger.logic_log('LOSI01121', self.trace_id, self.response_id, rhdm_res_act.execution_order)
        ActCommon.SaveActionLog(self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01044')

        # メール送信
        ActionStatus, DetailStatus = self.preact_manager.act(rhdm_res_act, retry=retry, pre_flag=True)

        # 正常終了
        if ActionStatus == PROCESSED:
            update_pre_action_history(self.action_history_pre, PROCESSED, self.user)
            update_action_history(self.action_history, PENDING, ACTION_HISTORY_STATUS.DETAIL_STS.NONE, self.user, retry=retry)
            ActCommon.SaveActionLog(self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01045')
            logger.logic_log('LOSI01122', self.trace_id, self.response_id, rhdm_res_act.execution_order)
            self.save_resume = rhdm_res_act.execution_order
            return PENDING

        # 異常終了
        else:
            logger.logic_log('LOSI01123', self.trace_id, self.response_id, rhdm_res_act.execution_order)
            update_action_history(self.action_history, ActionStatus, DetailStatus, self.user, retry=retry)
            return ActionStatus


    def has_driver(self, rhdm_res_act, retry=False):
        """ドライバー存在チェック"""
        if not rhdm_res_act.action_type_id in self.action_type_list:
            update_action_history(self.action_history, NO_DRIVER, ACTION_HISTORY_STATUS.DETAIL_STS.DRV_UNINSTALL, self.user, retry=retry)

            logger.logic_log('LOSI01119', rhdm_res_act.action_type_id, self.trace_id)
            ActCommon.SaveActionLog(self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01046')
            return False
        else:
            return True

    def set_driver_manager(self, action_type_id):
        """driver_managerをセットする"""

        driver_name = self.driver_type_info[action_type_id]['name'] if action_type_id in self.driver_type_info else ''
        module_name = 'libs.backyardlibs.action_driver.%s.%s_driver' % (driver_name, driver_name)
        class_name  = '%sManager' % (driver_name)

        try:
            drv_module = import_module(module_name)
            drv_class  = getattr(drv_module, class_name)
            self.driver_manager = drv_class(self.trace_id, self.response_id, self.user)

        except ModuleNotFoundError:
            logger.logic_log('LOSM01012', self.trace_id, module_name)

        except AttributeError:
            logger.logic_log('LOSM01013', self.trace_id, module_name, class_name)

        except Exception as e:
            logger.logic_log('LOSM01011', self.trace_id, traceback.format_exc())


    def MainLoop(self):
        """
        [概要]
          ルールマッチング結果管理から未処理アクション情報を取得し子プロセスを起動するメゾット
        """
        logger.logic_log('LOSI00001', 'None')
        ActionStatus = PROCESSED

        rhdm_res = RhdmResponse.objects.get(pk=self.response_id)

        # 実行順からのデータ取得
        rhdm_res_act_list = RhdmResponseAction.objects.filter(
            response_id=self.response_id,
            execution_order__gte=self.resume_order
        ).order_by('execution_order')

        logger.logic_log('LOSI01101', str(len(rhdm_res_act_list)), self.trace_id)

        if len(rhdm_res_act_list) == 0:
            logger.system_log('LOSE01105', self.trace_id, 'OASE_T_RHDM_RESPONSE_ACTION', self.response_id)
            return ACTION_DATA_ERROR

        # 実行順に処理
        for rhdm_res_act in rhdm_res_act_list:
            try:
                # 処理再開の場合(承認 or リトライ or 待機中)、実行ログを出力
                if self.resume_order == rhdm_res_act.execution_order:
                    # リトライ状態のチェック
                    ret_sts = self._is_retry(rhdm_res_act)
                    
                    # リトライ不可の場合は、リトライ状態を継続
                    if ret_sts == False:
                        self.save_resume = rhdm_res_act.execution_order
                        return ACTION_HISTORY_STATUS.RETRY 
                    
                    # 実行ログを出力
                    self.logging_resume_log(
                        ret_sts,
                        rhdm_res_act.execution_order,
                        rhdm_res.status
                    )

                # アクション履歴作成 メンバ変数にセット
                self.action_history = self.insert_action_history(
                    rhdm_res_act,
                    PROCESSING,
                    ACTION_HISTORY_STATUS.DETAIL_STS.NONE
                )
                if self.action_history is None:
                    return ACTION_DATA_ERROR

                # ドライバー存在チェック & セット
                self.reset_variables()
                if self.has_driver(rhdm_res_act):
                    self.set_driver_manager(rhdm_res_act.action_type_id)
                else:
                    return ACTION_DATA_ERROR

                logger.logic_log('LOSI01102', str(rhdm_res_act.execution_order), self.trace_id)

                # 事前アクション情報を登録
                ret = self.set_pre_action_information(rhdm_res_act)
                if ret != True:
                    ActCommon.SaveActionLog(self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01048')
                    return ACTION_DATA_ERROR

                # 事前アクションを実施
                if self.should_approved():
                    self.action_history_pre = self.insert_pre_action_history(PROCESSING)
                    if not self.action_history_pre:
                        update_action_history(
                            self.action_history,
                            ACTION_DATA_ERROR,
                            ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_VAL, 
                            self.user
                        )
                        return ACTION_DATA_ERROR

                    return self.preact(rhdm_res_act)


                logger.logic_log('LOSI01104', str(rhdm_res_act.execution_order), self.trace_id)
                ActCommon.SaveActionLog(self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01023')

                # 抑止回数・間隔の確認
                prevent_flg = self._prevent_by_interval_and_times(rhdm_res_act)
                if prevent_flg == "both_existence":
                    # 抑止判定チェック
                    prevent_status = self._is_prevented(
                        rhdm_res_act,
                        trace_id,
                        self.action_history.pk,
                    )

                    if prevent_status == WAITING:
                        # 先行ルールのアクション結果がわかるまで待機
                        # 再開アクション順を登録
                        self.save_resume = rhdm_res_act.execution_order
                        ActCommon.SaveActionLog(
                            self.response_id,
                            rhdm_res_act.execution_order,
                            self.trace_id,
                            'MOSJA01060',
                        )
                        return WAITING 

                    elif prevent_status == PREVENT:
                        #抑止したことをアクション履歴に保存
                        update_action_history(
                            self.action_history,
                            ACTION_HISTORY_STATUS.PREVENT,
                            ACTION_HISTORY_STATUS.DETAIL_STS.NONE,
                            self.user,
                        )

                        # todo msgId確認
                        ActCommon.SaveActionLog(
                            self.response_id,
                            rhdm_res_act.execution_order,
                            self.trace_id,
                            'MOSJA01024'
                        )
                        continue

                # アクション情報を登録
                status, detail = self.driver_manager.set_information(rhdm_res_act, self.action_history)
                if status > 0:
                    status = self.check_retry_status(status, rhdm_res_act, revision=1)
                    self.action_history.action_retry_count += 1
                    update_action_history(self.action_history, status, detail, self.user)
                    if status == ACTION_HISTORY_STATUS.RETRY:
                        self.update_resume_data(rhdm_res_act.execution_order, rhdm_res_act.action_retry_interval)
                        ActCommon.SaveActionLog(self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01057', interval=rhdm_res_act.action_retry_interval, ret_count=self.action_history.action_retry_count)

                    return status

                # アクション実行
                ActionStatus = self.act(rhdm_res_act)

                # 正常終了
                if ActionStatus == PROCESSED:
                    ActCommon.SaveActionLog(self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01038')

                # リトライによる処理継続
                elif ActionStatus == ACTION_HISTORY_STATUS.RETRY:
                    self.update_resume_data(rhdm_res_act.execution_order, rhdm_res_act.action_retry_interval)
                    ActCommon.SaveActionLog(self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01057', interval=rhdm_res_act.action_retry_interval, ret_count=self.action_history.action_retry_count)
                    return ACTION_HISTORY_STATUS.RETRY

            except Exception as e:
                logger.system_log('LOSE01119', traceback.format_exc())
                self.insert_action_history(rhdm_res_act, SERVER_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.NONE)
                return SERVER_ERROR

        logger.logic_log('LOSI00002', 'ActionStatus {}'.format(ActionStatus))

        return ActionStatus

    def logging_resume_log(self, retry_sts, order, rhdm_res_status):
        """
        処理再開(承認,リトライ,待機中)の実行ログを出力
        [引数]
        retry_sts: リトライ可能か不可能かのステータス
        order: ルール実行順
        rhdm_res_status: メッセージのステータス
        """
        msgid = ''

        if retry_sts == True:
            # リトライ可能
            msgid = 'MOSJA01058'

        elif rhdm_res_status == WAITING:
            # 待機中なら処理を再開するログ
            msgid = 'MOSJA01061'

        elif retry_sts == None:
            # リトライでも待機中でもない場合は承認再開とする
            msgid = 'MOSJA01049'

        if not msgid:
            ActCommon.SaveActionLog(
                self.response_id,
                order,
                self.trace_id,
                msgid,
            )


    def update_resume_data(self, execution_order, action_retry_interval):
        """
        再実行に使うデータをアップデートする
        """
        self.save_resume = execution_order
        self.save_resume_time = self.make_datetime(action_retry_interval * -1, str_flg=False)



    def check_retry_status(self, status, rhdm_res_act, revision=0):
        """
        [概要]
          アクション状態からリトライ可否を判定する
        [引数]
          status : アクション状態
          rhdm_res_act : アクション情報
          revision : リトライ回数の補正値
        [戻り値]
          int : 判定による遷移先status
        """

        logger.logic_log('LOSI01007', self.trace_id, status, self.action_history.action_retry_count, rhdm_res_act.action_retry_count - revision)

        # リトライ無効ステータスの場合は何も処理をしない
        if status in ACTION_HISTORY_STATUS.DISABLE_RETRY_LIST:
            return status

        # リトライ上限に達している場合はエラー
        if self.action_history.action_retry_count >= rhdm_res_act.action_retry_count - revision:
            return status

        # リトライ状態に遷移
        return ACTION_HISTORY_STATUS.RETRY


    def _is_retry(self, rhdm_res_act):
        """
        リトライ可能か調べる。
        None : リトライ対象外, True : 可能, False : 不可
        """

        # アクション履歴検索
        act_his_list = ActionHistory.objects.filter(
            response_id     = rhdm_res_act.response_id,
            execution_order = rhdm_res_act.execution_order
        ).values('status', 'action_start_time')

        # 対象レコードなし
        if len(act_his_list) <= 0:
            logger.system_log('LOSM01016', self.trace_id, rhdm_res_act.response_id, rhdm_res_act.execution_order)
            return None

        # 状態チェック
        if act_his_list[0]['status'] != ACTION_HISTORY_STATUS.RETRY:
            logger.logic_log('LOSI01008', self.trace_id, rhdm_res_act.response_id, rhdm_res_act.execution_order)
            return None

        # リトライ間隔未満
        start_time = self.make_datetime(rhdm_res_act.action_retry_interval, str_flg=False)
        if act_his_list[0]['action_start_time'] > start_time:
            logger.logic_log('LOSI01009', self.trace_id, rhdm_res_act.response_id, rhdm_res_act.execution_order, rhdm_res_act.action_retry_interval, act_his_list[0]['action_start_time'])
            return False

        return True
        
        
    def _prevent_by_interval_and_times(self, rhdm_res_act):
        """
        アクション抑止情報（回数と間隔）を確認し、
        それぞれの組み合わせ毎に異なるステータスを発行する
        
        返却値
        both_none      ： 回数・間隔ともに0の場合
        count_none     ： 回数が0、間隔は0でない場合   
        interval_none  ： 回数が0ではく、間隔は0の場合  
        both_existence ： 回数・間隔ともに0でない場合
        """

        logger.logic_log('LOSI00001', 'trace_id: {}'.format(self.trace_id))

        if not (rhdm_res_act.action_stop_count or rhdm_res_act.action_stop_interval):
            prevent_flg = "both_none"

        elif not rhdm_res_act.action_stop_count:
            prevent_flg = "count_none"

        elif not rhdm_res_act.action_stop_interval:
            prevent_flg = "interval_none"

        else:
            prevent_flg =  "both_existence"

        logger.logic_log('LOSI00002', 'prevent_flg: {}, trace_id: {}'.format(prevent_flg, self.trace_id))
        return prevent_flg


    def _is_prevented(self, rhdm_res_act, trace_id, act_his_pk):
        """
        抑止すべきか調べる。
        True : 抑止する, False : 抑止しない
        """
        logger.logic_log('LOSI00001', 'trace_id: {}'.format(self.trace_id))
        # ルール種別IDを取得 
        rule_type_id = EventsRequest.objects.get(trace_id=trace_id).rule_type_id

        # アクション抑止間隔からアクション履歴を検索する日時を求める
        time_from = self.action_history.last_update_timestamp - datetime.timedelta(seconds=rhdm_res_act.action_stop_interval)
        
        # 抑止対象となるアクション履歴を検索 承認待ちと、停止されたデータは除外
        history_status_list = ActionHistory.objects.filter(
            rule_type_id = rule_type_id,
            rule_name = rhdm_res_act.rule_name,
            last_update_timestamp__gt = time_from,
            pk__lt = act_his_pk,
        ).exclude(
            status__in = [ACTION_HISTORY_STATUS.PENDING, ACTION_HISTORY_STATUS.STOP]
        ).values_list('status', flat=True)


        # 成否が出ていないものがあれば待機中
        for s in history_status_list:
            if s in (
                     ACTION_HISTORY_STATUS.RETRY,
                     ACTION_HISTORY_STATUS.EXASTRO_REQUEST,
                     ACTION_HISTORY_STATUS.PROCESSING,
                ):
                logger.logic_log('LOSI01124', self.trace_id, act_his_pk)
                return WAITING 

        # 抑止判定
        history_count = history_status_list.count()
        result = PREVENT if 0 < history_count <= rhdm_res_act.action_stop_count else False
        
        logger.logic_log('LOSI00002', 'trace_id: {}, return: {}'.format(self.trace_id, result))
        return result 


    def act(self, rhdm_res_act):
        """アクション実行"""

        status = ACTION_EXEC_ERROR
        detail = ACTION_HISTORY_STATUS.DETAIL_STS.NONE

        try:
            retry_flag = True if self.action_history.action_retry_count > 0 else False
            status, detail = self.driver_manager.act(rhdm_res_act, retry_flag)

            status = self.check_retry_status(status, rhdm_res_act, revision=1)
            if status == ACTION_HISTORY_STATUS.RETRY:
                self.action_history.action_retry_count += 1

            update_action_history(self.action_history, status, detail, self.user)

        except Exception as e:
            logger.system_log('LOSE01119', traceback.format_exc())
            status = self.check_retry_status(ACTION_EXEC_ERROR, rhdm_res_act, revision=1)
            self.action_history.action_retry_count += 1
            update_action_history(self.action_history, status, detail, self.user)

        return status


    def retry(self, action_history_id):
        """
        [概要]
            アクションを再実行
        [引数]
        update_user : str 再実行者の名前
        """
        logger.logic_log('LOSI00001', 'None')

        status = SERVER_ERROR
        detail = ACTION_HISTORY_STATUS.DETAIL_STS.NONE

        try:
            # 再実行したいアクション履歴を取得
            self.action_history = ActionHistory.objects.get(action_history_id=action_history_id)
            execution_order = self.action_history.execution_order

            # 再実行したいルールマッチング結果詳細を取得
            rhdm_res_act = RhdmResponseAction.objects.get(
                response_id = self.response_id,
                execution_order = execution_order,
            )

            # 再実行したい事前アクション履歴を取得
            rset = PreActionHistory.objects.filter(action_history_id=action_history_id)
            if len(rset) > 0:
                self.action_history_pre = rset[0]

        except ActionHistory.DoesNotExist:
            logger.system_log('LOSE01120', action_history_id)
            return ACTION_DATA_ERROR

        except RhdmResponseAction.DoesNotExist:
            logger.system_log('LOSE01121', self.response_id, execution_order)
            return ACTION_DATA_ERROR

        try:
            # ドライバー存在チェック
            self.reset_variables()
            if self.has_driver(rhdm_res_act, retry=True):
                self.set_driver_manager(rhdm_res_act.action_type_id)
            else:
                return ACTION_DATA_ERROR

            # 事前アクションを実施
            ret = self.set_pre_action_information(rhdm_res_act, retry=True)
            if ret != True:
                return ACTION_DATA_ERROR

            # 事前アクションを実施
            if self.should_approved():
                update_action_history(self.action_history, PROCESSING, ACTION_HISTORY_STATUS.DETAIL_STS.NONE, self.user, retry=True)
                if self.action_history_pre:
                    update_pre_action_history(self.action_history_pre, PROCESSING, self.user)
                else:
                    self.action_history_pre = self.insert_pre_action_history(PROCESSING)

                return self.preact(rhdm_res_act, retry=True)

            # アクション情報を解析
            logger.logic_log('LOSI01102', str(execution_order), self.trace_id)
            status, detail = self.driver_manager.set_information(rhdm_res_act, self.action_history)
            if status > 0:
                update_action_history(self.action_history, ACTION_DATA_ERROR, detail, self.user, retry=True)
                return ACTION_DATA_ERROR

            # アクション実行
            logger.logic_log('LOSI01104', str(execution_order), self.trace_id)
            ActCommon.SaveActionLog(self.response_id, execution_order, self.trace_id, 'MOSJA01042')
            status = self.act_retry(rhdm_res_act)

            # 正常終了の場合
            if status == PROCESSED:
                ActCommon.SaveActionLog(self.response_id, execution_order, self.trace_id, 'MOSJA01043')

        except Exception as e:
            status = SERVER_ERROR
            detail = ACTION_HISTORY_STATUS.DETAIL_STS.NONE
            logger.system_log('LOSE01119', traceback.format_exc())
            update_action_history(self.action_history, status, detail, self.user, retry=True)

        logger.logic_log('LOSI00002', status)
        return status


    def act_retry(self, rhdm_res_act):
        """アクション実行（再実行）"""

        status, detail = self.driver_manager.retry(rhdm_res_act, retry=True)
        update_action_history(self.action_history, status, detail, self.user, retry=True)

        return status


    def make_datetime(self,seconds,str_flg=True):
        """
        [概要]
          現在時間に指定秒数を加算した日時を求める
        """
        logger.logic_log('LOSI00001', 'seconds: %s' % (seconds))

        make_seconds = seconds * -1
        time = datetime.datetime.now(pytz.timezone('UTC'))
        if seconds != 0:
            time += datetime.timedelta(seconds=make_seconds)

        if not str_flg:
            logger.logic_log('LOSI00002', time)
            return time

        string = '{}-{}-{} {}:{}:{}'.format( '%04d' % time.year, 
                                             '%02d' % time.month, 
                                             '%02d' % time.day, 
                                             '%02d' % time.hour, 
                                             '%02d' % time.minute, 
                                             '%02d' % time.second)

        logger.logic_log('LOSI00002', 'None')

        return string


    def set_pre_action_information(self, rhdm_res_act, retry=False):
        """
        [概要]
          事前アクション情報登録
        """

        logger.logic_log('LOSI00001', 'trace_id: %s, pre_info: %s' % (self.trace_id, rhdm_res_act.action_pre_info))

        pre_info = rhdm_res_act.action_pre_info

        # 情報登録の要否確認
        if not self.is_preaction(pre_info, rhdm_res_act.execution_order):
            # 事前アクションがないなら何もしない
            return True
        elif self.has_preacted(rhdm_res_act.execution_order):
            # 事前アクションが存在しても実行済みなら何もしない
            return True

        ActCommon.SaveActionLog(self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01047')

        # アクション情報解析
        pre_info = ast.literal_eval(pre_info)
        if not pre_info or not isinstance(pre_info, dict):
            ActCommon.SaveActionLog(self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01048')
            logger.logic_log('LOSM01100', self.trace_id, self.response_id, rhdm_res_act.execution_order, type(pre_info), pre_info)
            return False

        try:
            # メールドライバーの確認
            for k, v in self.driver_type_info.items():
                if v['name'] != 'mail':
                    continue

                drv_module = import_module('libs.backyardlibs.action_driver.%s.%s_driver' % (v['name'], v['name']))
                drv_class  = getattr(drv_module, '%sManager' % (v['name']))
                self.preact_manager = drv_class(self.trace_id, self.response_id, self.user)
                break

            else:
                ActCommon.SaveActionLog(self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01052')
                logger.logic_log('LOSM01014', self.trace_id)
                update_action_history(self.action_history, NO_DRIVER, ACTION_HISTORY_STATUS.DETAIL_STS.DRV_UNINSTALL, self.user, retry)
                return False

            # 事前メールの情報登録
            self.preact_manager.set_action_parameters(pre_info, rhdm_res_act.execution_order, rhdm_res_act.response_detail_id, pre_flg=True)
            self.preact_manager.set_driver(rhdm_res_act.execution_order)
            self.preact_manager.set_mailtemplate(rhdm_res_act.execution_order, pre_flag=True)

            # アクション履歴をmail_managerにも登録
            self.preact_manager.action_history = self.action_history

        except OASEError as e:
            logger.logic_log('LOSM01011', self.trace_id, traceback.format_exc())
            ActCommon.SaveActionLog(self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01048')
            if e.arg_dict and isinstance(e.arg_dict, dict) and 'sts' in e.arg_dict and 'detail' in e.arg_dict:
                update_action_history(self.action_history, e.arg_dict['sts'], e.arg_dict['detail'], self.user, retry)

            else:
                update_action_history(self.action_history, ACTION_DATA_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.NONE, self.user, retry)

            return False

        except Exception as e:
            logger.logic_log('LOSM01011', self.trace_id, traceback.format_exc())
            ActCommon.SaveActionLog(self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01048')
            update_action_history(self.action_history, ACTION_DATA_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.NONE, self.user, retry)
            return False

        logger.logic_log('LOSI00002', 'return: True')
        return True

    def is_preaction(self, pre_info, exe_order):
        """
        事前アクションがあるか調べる。あればTrue, なければFalse
        
        """
        if not pre_info or pre_info in ['x', 'X']:
            logger.logic_log('LOSI01118', self.trace_id, self.response_id, exe_order)
            return False
        else:
            return True


    def has_preacted(self, exe_order):
        """
        事前アクションをやったか調べる
        [戻り値]
        bool: True 実行済み, False 未実行
        """
        if 0 < self.resume_order < exe_order:
            self.action_history_pre = None

        elif self.resume_order == exe_order:
            acthist = ActionHistory.objects.filter(response_id=self.response_id, execution_order=exe_order)
            if len(acthist) > 0:
                self.action_history = acthist[0]
                acthist_id = self.action_history.action_history_id

                acthist_pre = PreActionHistory.objects.filter(action_history_id=acthist_id)
                if len(acthist_pre) > 0:
                    self.action_history_pre = acthist_pre[0]

        if self.action_history_pre:
            if self.action_history_pre.status == PROCESSED:
                logger.logic_log('LOSI01120', self.trace_id, self.response_id, exe_order)
                return True

        return False


    def update_status(self, ActionStatus):
        """
        [概要]
          ルールマッチング結果のステータス更新
        """

        logger.logic_log('LOSI00001', 'ActionStatus: %s' % ActionStatus)

        try:
            with transaction.atomic():
                rhdm_response = RhdmResponse.objects.select_for_update().get(response_id=self.response_id)
                rhdm_response.resume_order = self.save_resume
                rhdm_response.resume_timestamp = self.save_resume_time
                rhdm_response.status_update_id = gethostname()
                rhdm_response.status = ActionStatus
                rhdm_response.last_update_user = self.user
                rhdm_response.last_update_timestamp = ActCommon.getStringNowDateTime()
                rhdm_response.save(force_update=True)

        except Exception as e:
            logger.system_log('LOSE01117', self.trace_id, traceback.format_exc())
            return False

        logger.logic_log('LOSI00002', 'None')

        return True


    def check_exastro_request(self, trace_id, act_his_id):
        """
        [概要]
          Exastroシリーズの実行ステータス取得
        """

        logger.logic_log('LOSI00001', 'trace_id: %s, act_his_id: %s' % (trace_id, act_his_id))

        act_his_list = ActionHistory.objects.filter(action_history_id = act_his_id).filter(
            Q(status__in=ACTION_HISTORY_STATUS.EXASTRO_CHECK_LIST)
            |Q(retry_status__in=ACTION_HISTORY_STATUS.EXASTRO_CHECK_LIST)
        )

        if len(act_his_list) <= 0:
            logger.system_log('LOSE01120', act_his_id)
            return False

        act_his = act_his_list[0]
        act_type = act_his.action_type_id

        # アクション種別がexastroシリーズかチェック
        if (act_type not in self.driver_type_info
                or self.driver_type_info[act_type]['exastro'] != '1'):
            logger.logic_log('LOSE01126', trace_id, self.action_type_list)
            ActCommon.SaveActionLog(act_his.response_id, act_his.execution_order, act_his.trace_id, 'MOSJA01053')
            return False

        # action_type_idとexastroで対象ドライバーを絞り込む
        try:
            status, detail = None, None
            rhdm_res_act = RhdmResponseAction.objects.get(
                response_id=act_his.response_id,
                execution_order=act_his.execution_order,
            )

            self.set_driver_manager(act_type)
            self.driver_manager.set_information(rhdm_res_act, act_his)
            status, detail = self.driver_manager.get_last_info(act_his_id, rhdm_res_act.execution_order)

            if status is None or detail is None:
                ActCommon.SaveActionLog(
                    act_his.response_id, act_his.execution_order, trace_id, 'MOSJA01055', status=status, detail=detail
                )
                return False

            # アクション履歴のステータス更新
            retry_flag = True if act_his.retry_status is not None else False
            update_action_history(act_his, status, detail, self.user, retry=retry_flag)

            # アクション履歴ログ管理更新
            ActCommon.SaveActionLog(
                act_his.response_id,
                act_his.execution_order,
                trace_id,
                'MOSJA01054',
                status=get_message(
                    ACTION_HISTORY_STATUS.STATUS_DESCRIPTION[status],
                    self.user_objects.get_lang_mode(),
                    showMsgId=False
                )
            )

        except RhdmResponseAction.DoesNotExist:
            logger.system_log('LOSE01121', act_his.response_id, act_his.execution_order)
            return False

        except Exception as e:
            logger.system_log('LOSE01104', trace_id, traceback.format_exc())
            return False

        logger.logic_log('LOSI00002', 'getResult = %s, trace_id = %s' % ('True', trace_id))
        return True

    def regist_exastro(self, trace_id, act_his_id):
        """
        Exastroシリーズのデータ登録状況に応じた処理
        """
        logger.logic_log('LOSI00001', 'trace_id: %s, act_his_id: %s' % (trace_id, act_his_id))

        try:
            act_his = ActionHistory.objects.get(action_history_id = act_his_id)

            # アクション種別がexastroシリーズかチェック
            if (act_his.action_type_id not in self.driver_type_info
                    or self.driver_type_info[act_his.action_type_id]['exastro'] != '1'):
                logger.logic_log('LOSE01126', trace_id, self.action_type_list)
                ActCommon.SaveActionLog(act_his.response_id, act_his.execution_order, act_his.trace_id, 'MOSJA01069')
                return False

            status, detail = None, None
            rhdm_res_act = RhdmResponseAction.objects.get(
                response_id=act_his.response_id,
                execution_order=act_his.execution_order,
            )

            self.set_driver_manager(act_his.action_type_id)
            self.driver_manager.set_information(rhdm_res_act, act_his)
            status, detail = self.driver_manager.act_with_menuid(act_his_id, rhdm_res_act.execution_order)

            retry_flag = True if act_his.retry_status is not None else False
            update_action_history(act_his, status, detail, self.user, retry=retry_flag)
            ActCommon.SaveActionLog(act_his.response_id, act_his.execution_order, trace_id, 'MOSJA01068')

        except ActionHistory.DoesNotExist:
            logger.system_log('LOSE01120', act_his_id)
            return False
        except RhdmResponseAction.DoesNotExist:
            logger.system_log('LOSE01121', act_his.response_id, act_his.execution_order)
            return False
        except Exception as e:
            logger.system_log('LOSE01104', trace_id, traceback.format_exc())
            return False

        logger.logic_log('LOSI00002', 'return = True, trace_id = %s' % (trace_id))
        return True


if __name__ == '__main__':

    exec_type = ''
    response_id = 0
    trace_id = ''
    resume_order = 0

    # 起動パラメータ
    args = sys.argv

    # 引数異常
    argc = len(args)
    if argc < 5 or argc > 6:
        logger.system_log('LOSE01118', args)
        sys.exit(2)

    # 引数の共通部分設定
    if argc >= 5:
        exec_type = args[1]
        response_id = int(args[2])
        trace_id = args[3]
        resume_order = int(args[4])

    if len(trace_id) == 0:
        logger.system_log('LOSE01131', trace_id)
        sys.exit(2)

    # 引数の個数に合わせて個別設定
    if argc >= 6:
        action_history_id = int(args[5])

    if ENABLE_LOAD_TEST:
        start_time = time.time()
        loadtest_logger.warn('処理開始 TraceID[%s]' % (trace_id))

    logger.logic_log('LOSI01114', exec_type, str(response_id), trace_id, resume_order)
    try:
        ADobj = ActionDriverSubModules(response_id, trace_id, resume_order)

        if exec_type == 'retry':
            status = ADobj.retry(action_history_id)

        elif exec_type == 'exastro':
            ret = ADobj.check_exastro_request(trace_id, action_history_id)
            if not ret:
                raise Exception(ret)

        elif exec_type == 'normal':
            ActionStatus = ADobj.MainLoop()
            # ルールマッチング結果のステータス更新
            ret = ADobj.update_status(ActionStatus)

        elif exec_type == 'regist_exastro':
            status = ADobj.regist_exastro(trace_id, action_history_id)

    except Exception as e:
        logger.system_log('LOSE01119', traceback.format_exc())

    if ENABLE_LOAD_TEST:
        elapsed_time = time.time() - start_time
        loadtest_logger.warn('処理終了 所要時間[%s] TraceID[%s]' % (elapsed_time, trace_id))

    logger.logic_log('LOSI01115', str(response_id), trace_id)
    logger.logic_log('LOSI00002', 'None')

    sys.exit(0)

