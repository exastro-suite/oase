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
  Exastro連携メイン処理
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
    os.environ['RUN_INTERVAL']  = '3600'
    os.environ['PYTHON_MODULE'] = '/usr/bin/python3'
    os.environ['LOG_LEVEL']     = "TRACE"
    os.environ['LOG_DIR']       = oase_root_dir + "/logs/backyardlogs/exastro_collaboration/"
#################################################

# 環境変数取得
try:
    root_dir_path = os.environ['OASE_ROOT_DIR']
    run_interval  = '3600' # os.environ['RUN_INTERVAL']
    python_module = os.environ['PYTHON_MODULE']
    log_dir       = os.environ['LOG_DIR']
    log_level     = os.environ['LOG_LEVEL']
except Exception as e:
    print(str(e))
    sys.exit(2)

# ロガー初期化
from libs.commonlibs.oase_logger import OaseLogger
logger = OaseLogger.get_instance()

from libs.commonlibs import define as defs
from web_app.models.models import User


#-------------------
# STATUS
#-------------------
DB_OASE_USER = 1 # -2140000006

class ITAParameterSheetMenuManager:
    """
    [クラス概要]
        ITAパラメーターシートメニュー管理クラス
    """

    def __init__(self):
        """
        [概要]
        コンストラクタ
        """

        pass

    def get_menu_list(self):
        """
        [概要]
        パラメーターシートメニューの情報リストを取得
        """

        pass

    def save_menu_info(self):
        """
        [概要]
        パラメーターシートメニューの情報を保存
        """

        pass

    def execute(self):
        """
        [概要]
        ITAからパラメーターシートメニューの情報を取得して保存
        """

        pass


if __name__ == '__main__':

    try:
        # ドライバー設定情報取得
        rset = []

        # アクション先ごとに情報を取得
        for rs in rset:
            # パラメーターシート用メニュー情報を取得
            cls = ITAParameterSheetMenuManager()
            cls.execute()

    except Exception as e:
        logger.system_log('LOSM25012')
        logger.logic_log('LOSM00001', 'e: %s, Traceback: %s' % (e, traceback.format_exc()))
        sys.exit(2)

    sys.exit(0)
