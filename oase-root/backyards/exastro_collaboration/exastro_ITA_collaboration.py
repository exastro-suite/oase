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
import traceback
import django
import datetime
import fcntl


# OASE モジュール importパス追加
my_path       = os.path.dirname(os.path.abspath(__file__))
tmp_path      = my_path.split('oase-root')
root_dir_path = tmp_path[0] + 'oase-root'
sys.path.append(root_dir_path)

# 排他制御ファイル名
exclusive_file = tmp_path[0] + 'oase-root/temp/exclusive/ita_collaboration.lock'

# OASE モジュール import
# #LOCAL_PATCH#
os.environ['DJANGO_SETTINGS_MODULE'] = 'confs.frameworkconfs.settings'
django.setup()

from django.conf import settings

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

from libs.backyardlibs.exastro_collaboration.ITA.factory import ITAParameterSheetFactory
from web_app.models.models import User
from web_app.models.ITA_models import ItaDriver


#-------------------
# STATUS
#-------------------
DB_OASE_USER = -2140000006


#-------------------
# MAIN
#-------------------
if __name__ == '__main__':

    with open(exclusive_file, "w") as f:

        # 排他ロックを獲得する。
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB )

        except IOError:
            sys.exit(0)

        try:
            logger.logic_log('LOSI00001', 'Start ITA collaboration.')

            now = datetime.datetime.now()
            user_name = User.objects.get(user_id=DB_OASE_USER).user_name

            # ドライバー設定情報取得
            rset = ItaDriver.objects.all().values('ita_driver_id', 'version', 'hostname', 'username', 'password', 'protocol', 'port')
            logger.logic_log('LOSI28001', [rs['ita_driver_id'] for rs in rset])

            # アクション先ごとに情報を取得
            for rs in rset:
                # パラメーターシート用メニュー情報を取得
                cls = ITAParameterSheetFactory.create(rs['version'])
                if cls:
                    cls = cls(rs, user_name, now)
                    cls.execute()

            logger.logic_log('LOSI00002', 'End ITA collaboration.')

        except Exception as e:
            logger.system_log('LOSM28001', 'main')
            logger.logic_log('LOSM00001', 'e: %s, Traceback: %s' % (e, traceback.format_exc()))
            fcntl.flock(f, fcntl.LOCK_UN)
            sys.exit(2)

        fcntl.flock(f, fcntl.LOCK_UN)

    sys.exit(0)
