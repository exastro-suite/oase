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
  イベントタイマーを管理する

[引数]


[戻り値]


"""




import pytz
import time
import datetime
import subprocess
import glob
import os
import traceback
import socket
import threading
from importlib import import_module
from itertools import zip_longest
from threading import Event, Thread

from django.conf import settings

from libs.commonlibs.oase_logger import OaseLogger


logger = OaseLogger.get_instance() # ロガー初期化
EVTIMER_LOCK = threading.Lock()


class OASEEventTimer(object):

    """
    [クラス概要]
      イベントタイマー管理クラス
    """

    _ipaddr = None
    _instance = None

    CONFIG_INFO = {
        'AD_LINKAGE_TIMER' : {
            'command'   : '%s/backyards/ad_collaboration/ad_collaboration.py' % (settings.BASE_DIR),
            'classpath' : 'backyards.ad_collaboration.ad_collaboration',
            'classname' : 'AdCollabExecutor',
            'exemethod' : 'execute',
        },
    }


    def __new__(cls):

        raise Exception('既にインスタンスが生成されています')


    @classmethod
    def __internal_new__(cls):

        return super().__new__(cls)


    @classmethod
    def get_instance(cls):
        """
        [メソッド概要]
          シングルトンのインスタンス生成処理
        """

        # 自サーバーIPアドレス取得
        host = socket.gethostname()
        cls._ipaddr = socket.gethostbyname(host)

        # イベントサーバーでない場合は、インスタンスを生成しない
        if not getattr(settings, 'EVTIMER_SERVER', None):
            logger.system_log('LOSE13001', 'EVTIMER_SERVER')
            return None

        ev_server = settings.EVTIMER_SERVER['location'].split(':')[0]
        if cls._ipaddr != ev_server:
            logger.logic_log('LOSI13006', cls._ipaddr, ev_server)
            return None

        # インスタンス生成
        if not cls._instance:
            cls._instance = cls.__internal_new__()

        return cls._instance


    def initialize(self):
        """
        [メソッド概要]
          初期化処理
        """

        self.python_path    = ''
        self.cron_path      = ''
        self.cron_file      = ''
        self.event_info     = {}
        self.last_timestamp = None
        self.event          = None
        self.thrd           = None

        # cron設定
        if settings.EVTIMER_SERVER['type'] == 'cron':
            self.python_path = os.environ.get('PYTHON_MODULE', '/bin/python')
            self.cron_path   = '%s/temp/cron/' % (settings.BASE_DIR)
            self.cron_file   = 'cron.txt'

        # タイマー設定(作成中)
        elif settings.EVTIMER_SERVER['type'] == 'timer':
            self.event_info = {}
            self.last_timestamp = None

            self.event = Event()
            self.thrd = Thread(target=self.event_scheduler)
            self.thrd.start()


    def regist_timer(self, config_id, hour_list, minute_list):
        """
        [メソッド概要]
          イベントタイマー登録処理
        """

        # システム設定IDから実行するコマンドを取得
        if config_id not in self.CONFIG_INFO:
            logger.logic_log('LOSM13016', config_id)
            return False

        if config_id not in self.event_info:
            if len(hour_list) > 0:
                self.event_info[config_id] = {
                    'hour_list'   : hour_list,
                    'minute_list' : minute_list,
                }

        else:
            if len(hour_list) <= 0:
                self.event_info.pop(config_id)

            else:
                self.event_info[config_id]['hour_list']   = hour_list
                self.event_info[config_id]['minute_list'] = minute_list

        return True


    def regist_cron(self, config_id, month_list, day_list, hour_list, minute_list):
        """
        [メソッド概要]
          cron登録処理
        """

        logger.logic_log('LOSI00001', 'config_id=%s, month=%s, day=%s, hour=%s, minute=%s' % (config_id, month_list, day_list, hour_list, minute_list))

        # システム設定IDから実行するコマンドを取得
        if config_id not in self.CONFIG_INFO:
            logger.logic_log('LOSM13016', config_id)
            return False

        try:
            command_file = self.CONFIG_INFO[config_id]['command']

            # ロックを取得
            with EVTIMER_LOCK:

                # 現在のcronをバックアップ
                os.makedirs(self.cron_path, exist_ok=True)
                now = datetime.datetime.now(pytz.timezone('UTC'))
                now_str = now.strftime('%Y%m%d%H%M%S%f')
                bk_filename = '%scron_%s.txt' % (self.cron_path, now_str)

                cron_cmd = []
                cron_cmd.append('crontab')
                cron_cmd.append('-l')

                with open(bk_filename, 'w') as fp:
                    proc = subprocess.Popen(cron_cmd, stdout=fp, stderr=subprocess.PIPE)

                logger.logic_log('LOSI13007', bk_filename)

                # 既存のバックアップファイルを削除
                file_list = glob.glob('%scron_[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].txt' % (self.cron_path))
                for f in file_list:
                    file_dt = f.split('/')[-1]
                    file_dt = file_dt[5:25]
                    file_dt = datetime.datetime.strptime(file_dt, '%Y%m%d%H%M%S%f')
                    file_dt = pytz.timezone('UTC').localize(file_dt, is_dst=None)
                    if file_dt < now:
                        logger.logic_log('LOSI13008', f)
                        os.remove(f)

                # 現在のcronを読込
                current_cron_lines = []
                with open(bk_filename, 'r') as fp:
                    fline = fp.readline()
                    while fline:
                        if command_file not in fline:
                            current_cron_lines.append(fline)
                        fline = fp.readline()

                # コマンド編集
                for mo, da, ho, mi in zip_longest(month_list, day_list, hour_list, minute_list, fillvalue='*'):
                    command_txt = '%s %s %s %s * %s %s 1> /dev/null 2>&1\n' % (mi, ho, da, mo, self.python_path, command_file)
                    current_cron_lines.append(command_txt)

                logger.logic_log('LOSI13009', current_cron_lines)

                # cron編集
                cr_filename = '%s%s' % (self.cron_path, self.cron_file)
                with open(cr_filename, 'w') as fp:
                    fp.writelines(current_cron_lines)

                # cron設定
                cron_cmd = []
                cron_cmd.append('crontab')
                cron_cmd.append(cr_filename)

                proc = subprocess.Popen(cron_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        except Exception as e:
            logger.logic_log('LOSM00001', traceback.format_exc())
            return False


        logger.logic_log('LOSI00002', 'success')

        return True


    def event_scheduler(self):
        """
        [メソッド概要]
          イベントスケジュール処理(作成中)
        """

        if self.event is None:
            return

        while self.event_info:
            now = datetime.datetime.now(pytz.timezone('UTC'))
            if not self.last_timestamp:
                self.last_timestamp = now

            for k, v in self.event_info:
                if k not in self.CONFIG_INFO:
                    continue

                for h, m in zip(v['hour_list'], v['minute_list']):
                    evtime = datetime.datetime(self.last_timestamp.year, self.last_timestamp.month, self.last_timestamp.day, h, m, 0)
                    if evtime < now and self.last_timestamp < evtime:
                        try:
                            ev_module = import_module(self.CONFIG_INFO[k]['classpath'])
                            ev_cls    = getattr(ev_module, self.CONFIG_INFO[k]['classname'])
                            ev_method = getattr(ev_cls, self.CONFIG_INFO[k]['exemethod'])
                            ev_method()

                        except Exception as e:
                            pass

            self.last_timestamp = now


