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
  監視アダプタ 監視実行処理（子プロセス）
"""

import os
import sys
import json
import re
import pytz
import datetime
import django
import traceback

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
from django.db import transaction
from django.db.models import Q

#################################################
# デバック用
if settings.DEBUG and getattr(settings, 'ENABLE_NOSERVICE_BACKYARDS', False):
    oase_root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..')
    os.environ['OASE_ROOT_DIR'] = oase_root_dir 
    os.environ['RUN_INTERVAL']  = '3'
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
from web_app.models.models import System
from web_app.models.models import RuleType
from web_app.models.models import MonitoringType
from web_app.models.models import AdapterType
from web_app.models.ZABBIX_monitoring_models import ZabbixAdapter
from web_app.models.ZABBIX_monitoring_models import ZabbixMonitoringHistory
from web_app.templatetags.common import get_message

from libs.backyardlibs.monitoring_adapter.ZABBIX.manage_trigger import ManageTrigger
from libs.backyardlibs.monitoring_adapter.ZABBIX.ZABBIX_api import ZabbixApi
from libs.backyardlibs.monitoring_adapter.ZABBIX.ZABBIX_formatting import message_formatting
from libs.backyardlibs.monitoring_adapter.ZABBIX.ZABBIX_request import send_request
from libs.commonlibs.common import Common
from libs.commonlibs.define import *


#-------------------
# STATUS
#-------------------
PROCESSING   = 1
PROCESSED    = 2
SERVER_ERROR = 3

DB_OASE_USER = -2140000005

class ZabbixAdapterSubModules:
    """
    [クラス概要]
        アクションドライバメイン処理クラス
    """

    def __init__(self, zabbix_adapter_id=0):
        """
        [概要]
          コンストラクタ
        """

        # クラス生成
        self.monitoring_history = None
        self.zabbix_adapter_id = zabbix_adapter_id
        self.zabbix_adapter = None
        self.monitoring_history = None
        self.user_objects = User.objects.get(user_id=DB_OASE_USER)
        self.user = self.user_objects.user_name


    def insert_monitoring_history(self, zabbix_lastchange, status):
        """
        [概要]
          ZABBIX監視履歴登録メゾット
        """
        logger.logic_log('LOSI00001', 'zabbix_adapter_id: %s, zabbix_lastchange: %s, status: %s' % (self.zabbix_adapter_id, zabbix_lastchange, status))

        monitoring_history = None
        monitoring_history_id = -1
        try:
            with transaction.atomic():

                monitoring_history = ZabbixMonitoringHistory(
                    zabbix_adapter_id     = self.zabbix_adapter_id,
                    zabbix_lastchange     = zabbix_lastchange,
                    status                = status,
                    status_update_id      = gethostname(),
                    last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
                    last_update_user      = self.user,
                )
                monitoring_history.save(force_insert=True)

                monitoring_history_id = monitoring_history.pk

        except Exception as e:
            logger.system_log('LOSM25013')
            logger.logic_log('LOSM00001', 'Traceback: %s' % (traceback.format_exc()))
            monitoring_history = None

        logger.logic_log('LOSI00002', 'monitoring_history_id: %s' % (str(monitoring_history_id)))

        return monitoring_history


    def update_monitoring_history(self, status, last_monitoring_time):
        """
        [概要]
          ZABBIX監視履歴更新メゾット
        """

        logger.logic_log('LOSI00001', 'status: %s' % (status))
        try:
            with transaction.atomic():
                self.monitoring_history.status = status
                self.monitoring_history.zabbix_lastchange = last_monitoring_time
                self.monitoring_history.status_update_id = gethostname()
                self.monitoring_history.last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC'))
                self.monitoring_history.last_update_user = self.user
                self.monitoring_history.save(force_update=True)

        except Exception as e:
            raise

        logger.logic_log('LOSI00002', 'None')
        return True


    def execute(self, zabbix_adapter, zabbix_lastchange):
        """
        [概要]
          監視実行
        """

        logger.logic_log('LOSI00001', zabbix_adapter.zabbix_adapter_id)

        result = True
        api_response = []
        last_monitoring_time = 0
        try:
            zabbix_api = ZabbixApi(zabbix_adapter)
            # TODO last_monitoring_timeを返却してもらう予定 現状(2020/01/10) 0で実施する
            api_response = zabbix_api.get_active_triggers(zabbix_lastchange)
            zabbix_api.logout()

        except TypeError as e:
            result = False
            logger.system_log('LOSM25014')
            logger.logic_log('LOSM00001', 'e: %s' % (e))

        except Exception as e:
            result = False
            logger.system_log('LOSM25014')
            logger.logic_log('LOSM00001', 'e: %s, Traceback: %s' % (e, traceback.format_exc()))

        logger.logic_log('LOSI00002', 'None')

        return result, api_response, last_monitoring_time


    def do_workflow(self):
        """
        [概要]
          
        """
        logger.logic_log('LOSI00001', 'None')

        zabbix_adapter = None
        latest_monitoring_history = None
        zabbix_lastchange = 0

        # 事前情報取得
        try:
            zabbix_adapter = ZabbixAdapter.objects.get(pk=self.zabbix_adapter_id)

            latest_monitoring_history = ZabbixMonitoringHistory.objects.filter(zabbix_adapter_id=self.zabbix_adapter_id, status=PROCESSED).order_by('zabbix_lastchange').reverse().first()

        except Exception as e:
            logger.logic_log('LOSM00001', 'Traceback: %s' % (traceback.format_exc()))

        if latest_monitoring_history != None:
            zabbix_lastchange = latest_monitoring_history.zabbix_lastchange

        # 監視履歴作成 メンバ変数にセット
        try:
            self.monitoring_history = self.insert_monitoring_history(zabbix_lastchange, PROCESSING)
            if self.monitoring_history is None:
                return False

        except Exception as e:
            logger.system_log('LOSM25013')
            logger.logic_log('LOSM00001', 'Traceback: %s' % (traceback.format_exc()))
            return False

        runnable = True
        error_occurred = False
        try:
            # 監視実行
            result_flag, result_data, last_monitoring_time = self.execute(zabbix_adapter, zabbix_lastchange)

            if not result_flag:
                error_occurred = True
                runnable = False

            # トリガー比較
            difference = []
            with transaction.atomic():
                if runnable:
                    triggerManager = ManageTrigger(self.zabbix_adapter_id, self.user)
                    confirm_list = [(int(record['triggerid']), int(record['lastchange'])) for record in result_data]
                    flag_array = triggerManager.main(confirm_list)

                    index = 0
                    for flag in flag_array:
                        if flag:
                            difference.append(result_data[index])

                        index = index + 1

                    if len(difference) <= 0:
                        runnable = False

                # メッセージ整形
                if runnable:
                    formatting_result, form_data = message_formatting(difference, zabbix_adapter.rule_type_id, self.zabbix_adapter_id)

                    if not formatting_result:
                        error_occurred = True
                        runnable = False

                    if len(form_data) <= 0:
                        runnable = False

                # OASEへ本番リクエスト
                if runnable:
                    send_result = send_request(form_data)

                    if not send_result:
                        error_occurred = True
                        runnable = False

        except Exception as e:
            error_occurred = True
            logger.system_log('LOSM25014')
            logger.logic_log('LOSM00001', 'Traceback: %s' % (traceback.format_exc()))

        # 結果により監視履歴更新
        status = 'success'
        try:
            # 正常終了
            if not error_occurred:
                self.update_monitoring_history(PROCESSED, last_monitoring_time)

            # 異常終了
            else:
                status = 'error'
                self.update_monitoring_history(SERVER_ERROR, last_monitoring_time)

        except Exception as e:
            status = 'error'
            logger.system_log('LOSM25011')
            logger.logic_log('LOSM00001', 'Traceback: %s' % (traceback.format_exc()))

        logger.logic_log('LOSI00002', 'Monitoring status: %s.' % status)

        return True


if __name__ == '__main__':

    zabbix_adapter_id = 0

    # 起動パラメータ
    args = sys.argv

    # 引数の共通部分設定
    if len(args) == 2:
        zabbix_adapter_id = int(args[1])
    else:
        logger.system_log('LOSE25000')
        logger.logic_log('LOSE00002', 'args: %s' % (args))
        sys.exit(2)

    if ENABLE_LOAD_TEST:
        start_time = time.time()
        loadtest_logger.warn('処理開始 ZabbixAdapterID[%s]' % (zabbix_adapter_id))

    logger.logic_log('LOSI25002', str(zabbix_adapter_id))
    try:
        zabbix_sub_module = ZabbixAdapterSubModules(zabbix_adapter_id)

        zabbix_sub_module.do_workflow()

    except Exception as e:
        logger.system_log('LOSM25014')
        logger.logic_log('LOSM00001', 'zabbix_adapter_id: %s, Traceback: %s' % (str(zabbix_adapter_id), traceback.format_exc()))

    if ENABLE_LOAD_TEST:
        elapsed_time = time.time() - start_time
        loadtest_logger.warn('処理終了 所要時間[%s] ZabbixAdapterID[%s]' % (elapsed_time, zabbix_adapter_id))

    logger.logic_log('LOSI25003', str(zabbix_adapter_id))

    sys.exit(0)

