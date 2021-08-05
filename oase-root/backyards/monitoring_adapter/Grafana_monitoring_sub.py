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
    os.environ['LOG_DIR']       = oase_root_dir + "/logs/backyardlogs/oase_monitoring"
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
from web_app.models.Grafana_monitoring_models import GrafanaAdapter
from web_app.models.Grafana_monitoring_models import GrafanaMonitoringHistory, GrafanaMatchInfo
from web_app.templatetags.common import get_message

from libs.backyardlibs.monitoring_adapter.Grafana.manage_trigger import ManageTrigger
from libs.backyardlibs.monitoring_adapter.Grafana.Grafana_api import GrafanaApi
from libs.backyardlibs.monitoring_adapter.Grafana.Grafana_formatting import message_formatting
from libs.backyardlibs.monitoring_adapter.Grafana.Grafana_request import send_request
from libs.commonlibs.common import Common
from libs.commonlibs.define import *


#-------------------
# STATUS
#-------------------
PROCESSING   = 1
PROCESSED    = 2
SERVER_ERROR = 3

DB_OASE_USER = -2140000007

class GrafanaAdapterSubModules:
    """
    [クラス概要]
        Grafanaアダプタメイン処理クラス
    """

    def __init__(self, grafana_adapter_id=0):
        """
        [概要]
          コンストラクタ
        """

        # クラス生成
        self.grafana_adapter_id = grafana_adapter_id
        self.grafana_adapter = None
        self.monitoring_history = None
        self.user_objects = User.objects.get(user_id=DB_OASE_USER)
        self.user = self.user_objects.user_name


    def insert_monitoring_history(self, grafana_lastchange, status):
        """
        [概要]
          Grafana監視履歴登録メゾット
        """
        logger.logic_log(
            'LOSI00001', 'grafana_adapter_id: %s, grafana_lastchange: %s, status: %s' %
            (self.grafana_adapter_id, grafana_lastchange, status))

        monitoring_history = None
        monitoring_history_id = -1
        try:
            with transaction.atomic():

                monitoring_history = GrafanaMonitoringHistory(
                    grafana_adapter_id    = self.grafana_adapter_id,
                    grafana_lastchange    = grafana_lastchange,
                    status                = status,
                    status_update_id      = gethostname(),
                    last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
                    last_update_user      = self.user,
                )
                monitoring_history.save(force_insert=True)

                monitoring_history_id = monitoring_history.pk

        except Exception as e:
            logger.system_log('LOSM30023', 'OASE_T_GRAFANA_MONITORING_HISTORY')
            logger.logic_log('LOSM00001', 'Traceback: %s' % (traceback.format_exc()))
            monitoring_history = None

        logger.logic_log('LOSI00002', 'monitoring_history_id: %s' % (str(monitoring_history_id)))

        return monitoring_history


    def update_monitoring_history(self, status, last_monitoring_time):
        """
        [概要]
          Grafana監視履歴更新メゾット
        """

        logger.logic_log('LOSI00001', 'status: %s' % (status))
        try:
            with transaction.atomic():
                self.monitoring_history.status = status
                self.monitoring_history.grafana_lastchange = last_monitoring_time
                self.monitoring_history.status_update_id = gethostname()
                self.monitoring_history.last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC'))
                self.monitoring_history.last_update_user = self.user
                self.monitoring_history.save(force_update=True)

        except Exception as e:
            raise

        logger.logic_log('LOSI00002', 'None')
        return True


    def execute(self, grafana_adapter, from_dt, to_dt):
        """
        [概要]
          監視実行
        """

        logger.logic_log('LOSI00001', grafana_adapter.grafana_adapter_id)

        result = True
        api_response = []
        last_monitoring_time = to_dt
        try:
            grafana_api = GrafanaApi(grafana_adapter)
            # TODO last_monitoring_timeを返却してもらう予定 現状(2020/01/10) 0で実施する
            api_response = grafana_api.get_active_triggers()
            #grafana_api.logout()

        except TypeError as e:
            result = False
            logger.system_log('LOSM30024', 'Grafana')
            logger.logic_log('LOSM00001', 'e: %s' % (e))

        except Exception as e:
            result = False
            logger.system_log('LOSM30024', 'Grafana')
            logger.logic_log('LOSM00001', 'e: %s, Traceback: %s' % (e, traceback.format_exc()))

        logger.logic_log('LOSI00002', 'None')

        return result, api_response, last_monitoring_time


    def _parser(self, idx, data_tmp, key_list, parse_list):

        while idx < len(key_list):
            k = key_list[idx]
            l = len(k)

            # 配列走査する場合
            if l == 2 and k.startswith('[') and k.endswith(']'):
                idx = idx + 1
                for dt in data_tmp:
                    result = self._parser(idx, dt, key_list, parse_list)
                    if not result:
                        return False

                else:
                    break

            # 配列型の添え字の場合
            elif l > 2 and k.startswith('[') and k.endswith(']'):
                # 要素の値が数値ではない
                if k[1 : l - 1].isdigit() == False:
                    logger.system_log('LOSM30018', 'element:%s' % (k[1 : l - 1]))
                    return False

                i = int(k[1 : l - 1])

                # 抽出データが配列型ではない、もしくは、要素数が不足
                if isinstance(data_tmp, list) == False or i >= len(data_tmp):
                    logger.system_log('LOSM30017', 'data_tmp:%s, index:%s, records:%s' % (data_tmp, i, len(data_tmp)))
                    return False

                data_tmp = data_tmp[i]
                idx = idx + 1

            # 辞書型のキーの場合
            if not (k.startswith('[') and k.endswith(']')):

                # 抽出データが辞書型ではない、もしくは、キーが存在しない
                if isinstance(data_tmp,  dict) == False or k not in data_tmp:
                    logger.system_log('LOSM30016', 'data_tmp:%s, key:%s' % (data_tmp, k))
                    return False

                data_tmp = data_tmp[k]
                idx = idx + 1

        if idx >= len(key_list):
            parse_list.append(data_tmp)

        return True


    def message_parse(self, pull_data):
        """
        [概要]
          取得データをパースして、インスタンスとイベント発生日時を取得
        """

        def convert_epoch_time(val):

            ret_val = val

            try:
                ret_val = int(val)

            except Exception as e:
                val = val.replace('-', '/')
                val = val.replace('T', ' ')
                val = val.replace('Z', '')
                val = (val.split('+'))[0]
                val = (val.split('.'))[0]
                dt_tmp = datetime.datetime.strptime(val, '%Y/%m/%d %H:%M:%S').replace(tzinfo=pytz.timezone('UTC'))
                ret_val = dt_tmp.timestamp()

            return ret_val


        logger.logic_log('LOSI00001', 'grafana_adapter_id:%s, msg_count:%s' % (self.grafana_adapter_id, len(pull_data)))

        confirm_list = []

        evtime_list   = []
        instance_list = []

        # イベント発生日時のパース
        evtime_list_tmp = []
        evtime_parse_list = self.grafana_adapter.match_evtime.split('.')
        result = self._parser(0, pull_data, evtime_parse_list, evtime_list_tmp)
        if not result:
            logger.system_log('LOSM30019')
            return False, []

        # イベント発生日時をエポックタイムに変換
        for et in evtime_list_tmp:
            val = convert_epoch_time(et)
            evtime_list.append(val)

        # インスタンスのパース
        instance_parse_list = self.grafana_adapter.match_instance.split('.')
        result = self._parser(0, pull_data, instance_parse_list, instance_list)
        if not result:
            logger.system_log('LOSM30020')
            return False, []

        # インスタンスとイベント発生日時のタプルリストを生成
        if len(evtime_list) > 0 and len(evtime_list) == len(instance_list):
            confirm_list = list(zip(instance_list, evtime_list))

        return True, confirm_list


    def eventinfo_parse(self, pull_data):
        """
        [概要]
          取得データをパースして、イベント情報を取得
        """

        logger.logic_log('LOSI00001', 'grafana_adapter_id:%s, msg_count:%s' % (self.grafana_adapter_id, len(pull_data)))

        evinfo_list = []

        evinfo_tmp_list = []
        check_ev_len_list = []

        # grafana_response_key取得
        key_list = list(GrafanaMatchInfo.objects.filter(grafana_adapter_id=self.grafana_adapter_id).order_by(
            'grafana_match_id').values_list('grafana_response_key', flat=True))

        # ルール条件ごとのイベント情報をパース
        for k in key_list:
            keys = k.split('.')
            tmp_list = []
            result = self._parser(0, pull_data, keys, tmp_list)
            if not result:
                logger.system_log('LOSM30021')
                return False, []

            check_ev_len_list.append(len(tmp_list))
            evinfo_tmp_list.append(tmp_list)

        # ルール条件数とパースされたイベント情報数が同一であること
        ev_len = 0
        for cel in check_ev_len_list:
            ev_len = cel
            if cel != check_ev_len_list[0]:
                return False, []

        # ルールごとのイベント情報に整列
        for i in range(ev_len):
            tmp_list = []
            for et in evinfo_tmp_list:
                tmp_list.append(et[i])

            evinfo_list.append(tmp_list)


        return True, evinfo_list


    def do_workflow(self):
        """
        [概要]
          
        """
        logger.logic_log('LOSI00001', 'None')

        grafana_adapter = None
        latest_monitoring_history = None
        now = datetime.datetime.now(pytz.timezone('UTC'))
        grafana_lastchange = now

        # 事前情報取得
        try:
            grafana_adapter = GrafanaAdapter.objects.get(pk=self.grafana_adapter_id)
            self.grafana_adapter = grafana_adapter

            latest_monitoring_history = GrafanaMonitoringHistory.objects.filter(
                grafana_adapter_id=self.grafana_adapter_id, status=PROCESSED
            ).order_by('grafana_lastchange').reverse().first()

        except GrafanaAdapter.DoesNotExist:
            logger.logic_log('LOSM30025', 'OASE_T_GRAFANA_ADAPTER', self.grafana_adapter_id)
            return False

        except Exception as e:
            logger.logic_log('LOSM00001', 'Traceback: %s' % (traceback.format_exc()))

        if latest_monitoring_history != None:
            grafana_lastchange = latest_monitoring_history.grafana_lastchange

        # 監視履歴作成 メンバ変数にセット
        try:
            self.monitoring_history = self.insert_monitoring_history(grafana_lastchange, PROCESSING)
            if self.monitoring_history is None:
                return False

        except Exception as e:
            logger.system_log('LOSM30023', 'OASE_T_GRAFANA_MONITORING_HISTORY')
            logger.logic_log('LOSM00001', 'Traceback: %s' % (traceback.format_exc()))
            return False

        runnable = True
        error_occurred = False
        last_monitoring_time = now.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        try:
            # 監視実行
            from_dt = grafana_lastchange.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            to_dt   = now.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            result_flag, result_data, last_monitoring_time = self.execute(grafana_adapter, from_dt, to_dt)

            if not result_flag:
                error_occurred = True
                runnable = False

            # トリガー比較
            difference = []
            with transaction.atomic():
                if runnable:
                    triggerManager = ManageTrigger(self.grafana_adapter_id, self.user)

                    runnable, confirm_list = self.message_parse(result_data)
                    if not runnable:
                        raise Exception()

                    flag_array = triggerManager.main(confirm_list)

                    runnable, evinfo_list = self.eventinfo_parse(result_data)
                    if not runnable:
                        raise Exception()

                    if len(flag_array) == len(evinfo_list):
                        index = 0
                        for flg, ev in zip(flag_array, evinfo_list):
                            if flg:
                                difference.append(
                                    {
                                        'instance' : confirm_list[index][0],
                                        'evtime'   : confirm_list[index][1],
                                        'evinfo'   : ev,
                                    }
                                )

                            index = index + 1

                    if len(difference) <= 0:
                        runnable = False

                # メッセージ整形
                if runnable:
                    formatting_result, form_data = message_formatting(
                        difference, grafana_adapter.rule_type_id, self.grafana_adapter_id)

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
            logger.system_log('LOSM30024', 'Grafana')
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
            logger.system_log('LOSM30022', 'OASE_T_GRAFANA_MONITORING_HISTORY')
            logger.logic_log('LOSM00001', 'Traceback: %s' % (traceback.format_exc()))

        logger.logic_log('LOSI00002', 'Monitoring status: %s.' % status)

        return True


if __name__ == '__main__':

    grafana_adapter_id = 0

    # 起動パラメータ
    args = sys.argv

    # 引数の共通部分設定
    if len(args) == 2:
        grafana_adapter_id = int(args[1])
    else:
        logger.system_log('LOSE30000')
        logger.logic_log('LOSE00002', 'args: %s' % (args))
        sys.exit(2)

    if ENABLE_LOAD_TEST:
        start_time = time.time()
        loadtest_logger.warn('処理開始 GrafanaAdapterID[%s]' % (grafana_adapter_id))

    logger.logic_log('LOSI30005', 'Grafana', str(grafana_adapter_id))
    try:
        grafana_sub_module = GrafanaAdapterSubModules(grafana_adapter_id)

        grafana_sub_module.do_workflow()

    except Exception as e:
        logger.system_log('LOSM30024', 'Grafana')
        logger.logic_log(
            'LOSM00001', 'grafana_adapter_id: %s, Traceback: %s' %
            (str(grafana_adapter_id), traceback.format_exc()))

    if ENABLE_LOAD_TEST:
        elapsed_time = time.time() - start_time
        loadtest_logger.warn('処理終了 所要時間[%s] GrafanaAdapterID[%s]' % (elapsed_time, grafana_adapter_id))

    logger.logic_log('LOSI30006', 'Grafana', str(grafana_adapter_id))

    sys.exit(0)

