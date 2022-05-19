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
    loadtest_logger = logging.getLogger('load_zabbix_monitor')

from web_app.models.models import User
from web_app.models.models import System
from web_app.models.models import RuleType
from web_app.models.models import MonitoringType
from web_app.models.models import AdapterType
from web_app.models.Mail_monitoring_models import MailAdapter
from web_app.models.Mail_monitoring_models import MailMonitoringHistory
from web_app.templatetags.common import get_message

from libs.backyardlibs.monitoring_adapter.Mail.manage_trigger import ManageTrigger
from libs.backyardlibs.monitoring_adapter.Mail.Mail_api import MailApi
from libs.backyardlibs.monitoring_adapter.Mail.Mail_formatting import message_formatting
from libs.backyardlibs.monitoring_adapter.Mail.Mail_request import send_request
from libs.commonlibs.common import Common
from libs.commonlibs.define import *


#-------------------
# STATUS
#-------------------
PROCESSING   = 1
PROCESSED    = 2
SERVER_ERROR = 3

DB_OASE_USER = -2140000011


class MailAdapterSubModules:
    """
    [クラス概要]
        監視アダプタメイン処理クラス
    """

    def __init__(self, mail_adapter_id=0):
        """
        [概要]
          コンストラクタ
        """

        # クラス生成
        self.monitoring_history = None
        self.mail_adapter_id = mail_adapter_id
        self.mail_adapter = None
        self.monitoring_history = None
        self.user_objects = User.objects.get(user_id=DB_OASE_USER)
        self.user = self.user_objects.user_name


    def insert_monitoring_history(self, mail_lastchange, status):
        """
        [概要]
          Mail監視履歴登録メゾット
        """
        logger.logic_log('LOSI00001', 'mail_adapter_id: %s, mail_lastchange: %s, status: %s' % (self.mail_adapter_id, mail_lastchange, status))

        monitoring_history = None
        monitoring_history_id = -1
        try:
            monitoring_history = MailMonitoringHistory(
                mail_adapter_id       = self.mail_adapter_id,
                mail_lastchange       = mail_lastchange,
                status                = status,
                status_update_id      = gethostname(),
                last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
                last_update_user      = self.user,
            )
            monitoring_history.save(force_insert=True)

            monitoring_history_id = monitoring_history.pk

        except Exception as e:
            # ログ追加
            logger.system_log('LOSM41005', self.mail_adapter_id)
            logger.logic_log('LOSM00001', 'mail_adapter_id: %s, Traceback: %s' % (self.mail_adapter_id, traceback.format_exc()))
            monitoring_history = None

        logger.logic_log('LOSI00002', 'mail_adapter_id: %s, monitoring_history_id: %s' % (self.mail_adapter_id, str(monitoring_history_id)))

        return monitoring_history


    def update_monitoring_history(self, status, last_monitoring_time):
        """
        [概要]
          Mail監視履歴更新メゾット
        """

        logger.logic_log('LOSI00001', 'mail_adapter_id: %s, status: %s' % (self.mail_adapter_id, status))
        try:
            self.monitoring_history.status = status
            self.monitoring_history.mail_lastchange = last_monitoring_time
            self.monitoring_history.status_update_id = gethostname()
            self.monitoring_history.last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC'))
            self.monitoring_history.last_update_user = self.user
            self.monitoring_history.save(force_update=True)

        except Exception as e:
            raise

        logger.logic_log('LOSI00002', 'mail_adapter_id: %s' % (self.mail_adapter_id))
        return True


    def execute(self, mail_adapter, from_dt, to_dt):
        """
        [概要]
          監視実行
        """

        logger.logic_log('LOSI00001', 'mail_adapter_id: %s' % (self.mail_adapter_id))

        result = True
        api_response = []
        last_monitoring_time = to_dt
        try:
            mail_api = MailApi(mail_adapter)
            api_response = mail_api.get_active_triggers(from_dt)

        except TypeError as e:
            result = False
            # ログ追加
            logger.system_log('LOSM41006', self.mail_adapter_id)
            logger.logic_log('LOSM00001', 'mail_adapter_id: %s, e: %s' % (self.mail_adapter_id, e))

        except Exception as e:
            result = False
            # ログ追加
            logger.system_log('LOSM41006', self.mail_adapter_id)
            logger.logic_log('LOSM00001', 'mail_adapter_id: %s, e: %s, Traceback: %s' % (self.mail_adapter_id, e, traceback.format_exc()))

        logger.logic_log('LOSI00002', 'mail_adapter_id: %s' % (self.mail_adapter_id))

        return result, api_response, last_monitoring_time


    def do_workflow(self):
        """
        [概要]
          
        """
        logger.logic_log('LOSI00001', 'None')

        mail_adapter = None
        latest_monitoring_history = None
        now = datetime.datetime.now(pytz.timezone('UTC'))
        mail_lastchange = now

        # 事前情報取得
        try:
            mail_adapter = MailAdapter.objects.get(pk=self.mail_adapter_id)
            self.mail_adapter = mail_adapter

            latest_monitoring_history = MailMonitoringHistory.objects.filter(
                mail_adapter_id=self.mail_adapter_id, status=PROCESSED
            ).order_by('mail_lastchange').reverse().first()

        except MailAdapter.DoesNotExist:
            # ログ追加
            logger.logic_log('LOSM30025', 'OASE_T_MAIL_ADAPTER', self.mail_adapter_id)
            return False

        except Exception as e:
            logger.logic_log('LOSM00001', 'Traceback: %s' % (traceback.format_exc()))

        if latest_monitoring_history != None:
            mail_lastchange = latest_monitoring_history.mail_lastchange

        # 監視履歴作成 メンバ変数にセット
        try:
            self.monitoring_history = self.insert_monitoring_history(mail_lastchange, PROCESSING)
            if self.monitoring_history is None:
                return False

        except Exception as e:
            # ログ追加
            logger.system_log('LOSM30023', 'OASE_T_MAIL_MONITORING_HISTORY')
            logger.logic_log('LOSM00001', 'Traceback: %s' % (traceback.format_exc()))
            return False

        runnable = True
        error_occurred = False
        last_monitoring_time = now.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        try:
            # 監視実行
            from_dt = mail_lastchange.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            to_dt   = now.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            result_flag, result_data, last_monitoring_time = self.execute(mail_adapter, mail_lastchange, to_dt)

            if not result_flag:
                error_occurred = True
                runnable = False

            # トリガー比較
            difference = []
            with transaction.atomic():
                if runnable:
                    triggerManager = ManageTrigger(self.mail_adapter_id, self.user)
                    confirm_list = [(record['message_id'], record['lastchange']) for record in result_data]
                    flag_array = triggerManager.main(confirm_list)

                    index = 0
                    for i, flag in enumerate(flag_array):
                        if flag:
                            difference.append(result_data[i])

                    if len(difference) <= 0:
                        runnable = False

                # メッセージ整形
                if runnable:
                    formatting_result, form_data = message_formatting(
                        difference, mail_adapter.rule_type_id, self.mail_adapter_id)

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
            logger.system_log('LOSM30024', 'Mail')
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
            # ログ追加
            logger.system_log('LOSM30022', 'OASE_T_MAIL_MONITORING_HISTORY')
            logger.logic_log('LOSM00001', 'Traceback: %s' % (traceback.format_exc()))

        logger.logic_log('LOSI00002', 'Monitoring status: %s.' % status)

        return True


if __name__ == '__main__':

    mail_adapter_id = 0

    # 起動パラメータ
    args = sys.argv

    # 引数の共通部分設定
    if len(args) == 2:
        mail_adapter_id = int(args[1])
    else:
        # ログ追加
        logger.system_log('LOSE30000')
        logger.logic_log('LOSE00002', 'args: %s' % (args))
        sys.exit(2)

    if ENABLE_LOAD_TEST:
        start_time = time.time()
        loadtest_logger.warn('処理開始 MailAdapterID[%s]' % (mail_adapter_id))

    # ログ追加
    logger.logic_log('LOSI30005', 'Mail', str(mail_adapter_id))
    try:
        mail_sub_module = MailAdapterSubModules(mail_adapter_id)

        mail_sub_module.do_workflow()

    except Exception as e:
        # ログ追加
        logger.system_log('LOSM30024', 'Mail')
        logger.logic_log(
            'LOSM00001', 'mail_adapter_id: %s, Traceback: %s' %
            (str(mail_adapter_id), traceback.format_exc()))

    if ENABLE_LOAD_TEST:
        elapsed_time = time.time() - start_time
        loadtest_logger.warn('処理終了 所要時間[%s] MailAdapterID[%s]' % (elapsed_time, mail_adapter_id))

    # ログ追加
    logger.logic_log('LOSI30006', 'Mail', str(mail_adapter_id))

    sys.exit(0)
