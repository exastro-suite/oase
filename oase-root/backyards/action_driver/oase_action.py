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
アクションドライバメイン処理（親プロセス）
"""
import os
import sys
from time import sleep
from subprocess import Popen
import traceback
import django
from socket import gethostname

# OASE モジュール importパス追加
my_path = os.path.dirname(os.path.abspath(__file__))
tmp_path = my_path.split('oase-root')
root_dir_path = tmp_path[0] + 'oase-root'
sys.path.append(root_dir_path)

# OASE モジュール import
os.environ['DJANGO_SETTINGS_MODULE'] = 'confs.frameworkconfs.settings'
django.setup()

from django.conf import settings
from django.db import transaction
from django.db.models import Q

from web_app.models.models import User
from web_app.models.models import RhdmResponse
from web_app.models.models import RhdmResponseAction
from web_app.models.models import ActionHistory
from libs.commonlibs.common import Common
from libs.commonlibs.define import *
from libs.commonlibs.oase_logger import OaseLogger
from libs.backyardlibs.oase_action_common_libs import ActionDriverCommonModules as ActCommon
from libs.backyardlibs.oase_action_common_libs import ConstantModules as Cstobj

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
logger = OaseLogger.get_instance()


class ActionDriverMainModules:
    """
    [クラス概要]
        アクションドライバメイン処理クラス
    """

    def __init__(self, log_file_path):
        """
        [概要]
          コンストラクタ
        """
        logger.logic_log('LOSI00001', 'log_file_path: %s' % log_file_path)

        # クラス生成
        self.LogFilePath = log_file_path
        self.last_update_user = User.objects.get(user_id=Cstobj.DB_OASE_USER).user_name
        self.hostname = gethostname()

    def OASE_T_RHDM_RESPONSE_update(self, rhdm_response):
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

    def ExecuteSubProcess(self, aryPCB, exec_type, ResponseID, TraceID, resume_order, action_history_id=0):
        """
        [概要]
          ルールマッチング結果を処理する子プロセスと
          再実行要求を処理する子プロセスを起動するメソッド

        """
        logger.logic_log(
            'LOSI00001', 'aryPCB: %s, ExecType: %s, ResponseID: %s, TraceID: %s, Resume: %s, ActHistID: %s' %
            (aryPCB, exec_type, ResponseID, TraceID, resume_order, action_history_id))

        try:
            devnull = open(os.devnull, "wb")
            logfile = open(self.LogFilePath, "ab")
            file_path = os.path.dirname(os.path.abspath(__file__)) + '/oase_action_sub.py'
            args = [os.environ['PYTHON_MODULE'], file_path, exec_type, str(ResponseID), TraceID, str(resume_order)]

            # アクション履歴IDが指定されていたら再実行用の引数を追加
            if action_history_id > 0:
                args.append(str(action_history_id))

            proc = Popen(args, stderr=logfile, shell=False)

            aryPCB[TraceID] = proc
            devnull.close()
            logfile.close()

            logger.logic_log('LOSI00002', 'None')
            return True

        except Exception as e:
            logger.logic_log('LOSM01002', TraceID, traceback.format_exc())
            return False

    def chkSubProcessTerminate(self, aryPCB):
        """
        [概要]
          子プロセス終了状況確認
        """
        logger.logic_log('LOSI00001', 'aryPCB: %s' % aryPCB)

        try:
            if len(aryPCB) == 0:
                return False
            for TraceID in list(aryPCB):
                if aryPCB[TraceID].poll() != None:
                    aryPCB[TraceID].wait()
                    aryPCB.pop(TraceID)

            logger.logic_log('LOSI00002', 'None')
            return True

        except Exception as ex:
            logger.logic_log('LOSM01003', TraceID, traceback.format_exc())
            return False

    def do_normal(self, aryPCB):
        """
        アクション通常実行
        """
        # ルールマッチング結果管理:未処理データをレスポンス受信日時の昇順で取得
        now = ActCommon.getStringNowDateTime()
        rhdm_response_list = RhdmResponse.objects.filter(request_type_id=PRODUCTION).filter(
            Q(status=UNPROCESS)
            | Q(status=WAITING)
            | Q(status=ACTION_HISTORY_STATUS.RETRY, resume_timestamp__isnull=False, resume_timestamp__lte=now)
        ).order_by('request_reception_time')

        logger.logic_log('LOSI01000', str(len(rhdm_response_list)), None)

        if len(rhdm_response_list) > 0:
            for rhdm_res in rhdm_response_list:
                trace_id = rhdm_res.trace_id
                response_id = rhdm_res.response_id
                resume_order = rhdm_res.resume_order

                logger.logic_log('LOSI01001', trace_id)

                # 待機中以外はステータスを処理中に更新
                if rhdm_res.status != WAITING:
                    rhdm_res.status = PROCESSING
                result = self.OASE_T_RHDM_RESPONSE_update(rhdm_res)

                if not result:
                    logger.logic_log('LOSM01005', trace_id)
                    return False

                # 子プロセス起動
                ret = self.ExecuteSubProcess(aryPCB, 'normal', response_id, trace_id, resume_order)
                if not ret:
                    logger.logic_log('LOSM01006', trace_id)
                    return False

        return True

    def do_retry(self, aryPCB):
        """
        再実行
        """
        act_his_list = ActionHistory.objects.filter(retry_flag=True)
        if len(act_his_list) > 0:
            for act_his in act_his_list:
                trace_id = act_his.trace_id

                result = self.UpdateActionHistoryToRetry(act_his)
                if not result:
                    logger.logic_log('LOSM01005', trace_id)
                    return False

                # 子プロセス起動
                ret = self.ExecuteSubProcess(
                    aryPCB,
                    'retry',
                    act_his.response_id,
                    trace_id,
                    act_his.execution_order,
                    act_his.pk
                )
                if not ret:
                    logger.logic_log('LOSM01006', trace_id)
                    return False

        return True

    def do_exastro(self, aryPCB):
        """
        Exastro実行中
        """
        # アクション履歴管理:Exastroリクエスト/Exastro実行中/Exastro未実行状態をアクション履歴IDの昇順で取得
        act_his_list = ActionHistory.objects.filter(
            Q(status__in=ACTION_HISTORY_STATUS.EXASTRO_CHECK_LIST)
            | Q(retry_status__in=ACTION_HISTORY_STATUS.EXASTRO_CHECK_LIST),
        ).order_by('action_history_id').values('action_history_id', 'trace_id', 'response_id', 'execution_order')

        logger.logic_log('LOSI01100', str(len(act_his_list)), None)

        for act_his in act_his_list:
            act_his_id   = act_his['action_history_id']
            trace_id     = act_his['trace_id']
            response_id  = act_his['response_id']
            resume_order = act_his['execution_order']

            # 子プロセス起動
            ret = self.ExecuteSubProcess(aryPCB, 'exastro', response_id, trace_id, resume_order, act_his_id)
            if not ret:
                logger.logic_log('LOSM01006', trace_id)
                return False

        return True

    def regist_exastro(self, arypcb):
        """
        exastroにデータの登録確認をする。登録状況に応じてアクションする。
        """
        # アクション履歴管理:Exastroリクエスト/Exastro実行中/Exastro未実行状態をアクション履歴IDの昇順で取得
        act_his_list = ActionHistory.objects.filter(
            Q(status__in=ACTION_HISTORY_STATUS.EXASTRO_REGIST_LIST)
            | Q(retry_status__in=ACTION_HISTORY_STATUS.EXASTRO_REGIST_LIST),
        ).order_by('action_history_id').values('action_history_id', 'trace_id', 'response_id', 'execution_order')

        logger.logic_log('LOSI01100', str(len(act_his_list)), None)

        for act_his in act_his_list:
            act_his_id = act_his['action_history_id']
            trace_id = act_his['trace_id']
            response_id = act_his['response_id']
            resume_order = act_his['execution_order']

            ret = self.ExecuteSubProcess(arypcb, 'regist_exastro', response_id, trace_id, resume_order, act_his_id)
            if not ret:
                logger.logic_log('LOSM01006', trace_id)
                return False

        return True

    def MainLoop(self, aryPCB):
        """
        [概要]
          ルールマッチング結果管理から未処理アクション情報を取得し子プロセスを起動するメゾット
        """
        logger.logic_log('LOSI00001', 'aryPCB: %s' % aryPCB)

        # 通常実行
        result = self.do_normal(aryPCB)
        if not result:
            logger.logic_log('LOSM01008')
            return False

        # アクション再実行
        result = self.do_retry(aryPCB)
        if not result:
            logger.logic_log('LOSM01009')
            return False

        # exastroの実行結果取得
        result = self.do_exastro(aryPCB)
        if not result:
            logger.logic_log('LOSM01015')
            return False

        # exastroの"代入値管理登録中"ステータスの更新
        result = self.regist_exastro(aryPCB)
        if not result:
            logger.logic_log('LOSM01017')
            return False

        logger.logic_log('LOSI00002', 'None')

        return True

    def chkAbnomalEndChildProcs(self):
        """
        [概要]
          ルールマッチング結果管理のステータスが処理中のまま
          子プロセスが終了しているレコードのステータスを
          強制処理済みに設定する。
        """

        logger.logic_log('LOSI00001', 'None')

        # ルールマッチング結果管理:処理中データ取得
        TraceID = '-' * 40
        rhdm_response_list = RhdmResponse.objects.filter(
            status=PROCESSING,
            status_update_id=self.hostname,
        )

        logger.logic_log('LOSI01000', str(len(rhdm_response_list)), TraceID)

        if len(rhdm_response_list) > 0:
            for rhdm_res in rhdm_response_list:
                TraceID = rhdm_res.trace_id

                logger.logic_log('LOSI01001', TraceID)

                # ステータスを強制処理済みに更新
                rhdm_res.status = FORCE_PROCESSED
                result = self.OASE_T_RHDM_RESPONSE_update(rhdm_res)
                # 多重更新を判定しない
                if result == False:
                    logger.logic_log('LOSM01005', TraceID)
                    # エラーでも先に進む
                else:
                    logger.logic_log('LOSI00002', 'None')


if __name__ == '__main__':

    # 実行ファイル名取得
    filename, ext = os.path.splitext(os.path.basename(__file__))
    # ログファイルのパスを生成
    log_file_path = log_dir + '/' + filename + '_err.log'

    ADobj = ActionDriverMainModules(log_file_path)
    aryPCB = {}

    logger.logic_log('LOSI01003', Cstobj.UnsetTraceID)

    # ルールマッチング結果管理からアクションを取得し子プロセス起動
    ret = ADobj.MainLoop(aryPCB)

    while(True):
        # 子プロセス起動状況確認
        ret = ADobj.chkSubProcessTerminate(aryPCB)

        # 処理中プロセスの数を確認
        if len(aryPCB) == 0:
            logger.logic_log('LOSI01004', Cstobj.UnsetTraceID)
            break

        # 処理中プロセスがある場合はsleep
        sleep(int(run_interval))

    logger.logic_log('LOSI01005', Cstobj.UnsetTraceID)

    ADobj.chkAbnomalEndChildProcs()

    logger.logic_log('LOSI01006', Cstobj.UnsetTraceID)

    sys.exit(0)
