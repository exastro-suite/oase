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
  Prometheusアダプタメイン処理
"""


import os
import sys
import json
import subprocess
import traceback
import django
import datetime
import pytz
from time import sleep
from subprocess import Popen
from socket import gethostname

# OASE モジュール importパス追加
my_path       = os.path.dirname(os.path.abspath(__file__))
tmp_path      = my_path.split('oase-root')
root_dir_path = tmp_path[0] + 'oase-root'
sys.path.append(root_dir_path)

# OASE モジュール import
# #LOCAL_PATCH#
os.environ['DJANGO_SETTINGS_MODULE'] = 'confs.frameworkconfs.settings'
django.setup()

from django.conf import settings
from django.db import transaction

#################################################
# デバック用
if settings.DEBUG and getattr(settings, 'ENABLE_NOSERVICE_BACKYARDS', False):
    oase_root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..')
    os.environ['OASE_ROOT_DIR'] = oase_root_dir 
    os.environ['RUN_INTERVAL']  = '3'
    os.environ['PYTHON_MODULE'] = '/usr/bin/python3'
    os.environ['LOG_LEVEL']     = "TRACE"
    os.environ['LOG_DIR']       = oase_root_dir + "/logs/backyardlogs/oase_monitoring/"
#################################################

# 環境変数取得
try:
    root_dir_path = os.environ['OASE_ROOT_DIR']
    run_interval  = os.environ['RUN_INTERVAL']
    python_module = os.environ['PYTHON_MODULE']
    log_dir       = os.environ['LOG_DIR']
    log_level     = os.environ['LOG_LEVEL']
except Exception as e:
    print(str(e))
    sys.exit(2)

# ロガー初期化
from libs.commonlibs.oase_logger import OaseLogger
logger = OaseLogger.get_instance()

from web_app.models.models import User
from web_app.models.Prometheus_monitoring_models import PrometheusAdapter
from web_app.models.Prometheus_monitoring_models import PrometheusMonitoringHistory

from libs.commonlibs.common import Common
from libs.commonlibs.define import *

#-------------------
# STATUS
#-------------------
FORCE_PROCESSED = 4

DB_OASE_USER = -2140000007


class PrometheusAdapterMainModules:
    """
    [クラス概要]
        Prometheusアダプタメイン処理クラス
    """
    def __init__(self):
        """
        [概要]
          コンストラクタ
        """
        logger.logic_log('LOSI00001', 'None')

        self.last_update_user = User.objects.get(user_id=DB_OASE_USER).user_name
        self.hostname  = gethostname()

        logger.logic_log('LOSI00002', 'None')


    def execute_subprocess(self, aryPCB, prometheus_adapter_id):
        """
        [概要]
          Prometheus情報を取得する子プロセスを起動するメソッド
        """
        logger.logic_log('LOSI00001', 'aryPCB: %s, prometheus_adapter_id: %s' % (aryPCB, prometheus_adapter_id))

        try:
            file_path = os.path.dirname(os.path.abspath(__file__)) + '/Prometheus_monitoring_sub.py'
            args = [os.environ['PYTHON_MODULE'], file_path , str(prometheus_adapter_id)]

            proc = Popen(args, stderr=subprocess.PIPE, shell=False)
            aryPCB[prometheus_adapter_id] = proc

        except Exception as e:
            logger.system_log('LOSM30000')
            logger.logic_log('LOSM00001', 'prometheus_adapter_id: %s, Traceback: %s' % (prometheus_adapter_id, traceback.format_exc()))
            return False

        logger.logic_log('LOSI00002', 'None')
        return True


    def do_normal(self, aryPCB):
        """
        Prometheusアダプタ通常実行
        """
        # Prometheusアダプタ設定情報を取得
        prometheus_adapter_list = PrometheusAdapter.objects.all()

        if len(prometheus_adapter_list) > 0:
            for prometheus_adapter in prometheus_adapter_list:

                # 子プロセス起動
                prometheus_adapter_id = prometheus_adapter.prometheus_adapter_id
                ret = self.execute_subprocess(aryPCB, prometheus_adapter_id)
                if ret != True:
                    return False

        return True


    def observe_subprocess(self, aryPCB):
        """
        [概要]
          子プロセス終了状況確認
        """
        logger.logic_log('LOSI00001', 'aryPCB: %s' % aryPCB)

        try:
            for prometheus_adapter_id in list(aryPCB):
                if aryPCB[prometheus_adapter_id].poll() != None:
                    aryPCB[prometheus_adapter_id].wait()
                    aryPCB.pop(prometheus_adapter_id)

        except Exception as e:
            logger.system_log('LOSM30001')
            logger.logic_log('LOSM00001', 'Traceback: %s' % (traceback.format_exc()))
            return False

        logger.logic_log('LOSI00002', 'None')
        return True


    def set_force_terminate_status(self):
        """
        [概要]
          Prometheus監視履歴管理のステータスが処理中のまま
          子プロセスが終了しているレコードのステータスを
          強制処理済みに設定する。
        """

        logger.logic_log('LOSI00001', 'None')

        try:
            with transaction.atomic():

                # 監視結果管理:処理中データ取得
                prometheus_monitoring_history_list = PrometheusMonitoringHistory.objects.filter(
                    status = 1,
                    status_update_id = self.hostname,
                )

                if len(prometheus_monitoring_history_list) > 0:
                    for prometheus_res in prometheus_monitoring_history_list:
                        prometheus_adapter_id = prometheus_res.prometheus_adapter_id

                        logger.logic_log('LOSI30000', prometheus_adapter_id)

                        # ステータスを強制処理済みに更新
                        prometheus_res.status = FORCE_PROCESSED
                        prometheus_res.last_update_user = self.last_update_user
                        prometheus_res.last_update_datetime = datetime.datetime.now(pytz.timezone('UTC'))
                        prometheus_res.save(force_update=True)

        except Exception as e:
            logger.system_log('LOSM30002')
            logger.logic_log('LOSM00001', 'Traceback: %s' % (traceback.format_exc()))

        logger.logic_log('LOSI00002', 'None')


if __name__ == '__main__':

    aryPCB = {}
    try:
        prometheus_main_module = PrometheusAdapterMainModules()

        ret = prometheus_main_module.do_normal(aryPCB)

        while(True):
            # 子プロセス起動状況確認
            ret = prometheus_main_module.observe_subprocess(aryPCB)

            # 処理中プロセスの数を確認
            if len(aryPCB) == 0:
                break

            # 処理中プロセスがある場合はsleep
            sleep(int(run_interval))

        prometheus_main_module.set_force_terminate_status()

    except Exception as e:
        logger.system_log('LOSM30003')
        logger.logic_log('LOSM00001', 'e: %s, Traceback: %s' % (e, traceback.format_exc()))
        sys.exit(2)

    sys.exit(0)
