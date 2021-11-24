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

from importlib import import_module

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


################################################################
class ITAParameterSheetFactory():
    """
    [クラス概要]
        ITAパラメーターシートメニュー管理クラス
    """

    ############################################
    # 定数定義
    ############################################
    # バージョン別の接尾辞
    CLASS_SUFFIX_DICT = {
        '1.6.0' : '2',
        '1.6.1' : '2',
        '1.6.2' : '2',
        '1.6.3' : '2',
        '1.7.0' : '2',
        '1.7.1' : '2',
        '1.7.2' : '2',
        '1.8.0' : '2',
        '1.8.1' : '2',
        '1.8.2' : '2',
        '1.9.0' : '2',
    }

    # パラメーターシート用の基本名
    BASE_NAME_MODULE = 'libs.backyardlibs.exastro_collaboration.ITA.param_sheet'
    BASE_NAME_CLASS  = 'ITAParameterSheetMenuManager'


    @classmethod
    def create(cls, version):
        """
        [概要]
        コンストラクタ
        [引数]
        drv_info : dict : ITAアクション設定
        """

        logger.logic_log('LOSI00001', 'Create class for Parameter Sheet Menu Manager. ver=%s' % (version))

        try:
            suffix = '' if version not in cls.CLASS_SUFFIX_DICT else cls.CLASS_SUFFIX_DICT[version]
            module_name = '%s%s' % (cls.BASE_NAME_MODULE, suffix)
            class_name  = '%s%s' % (cls.BASE_NAME_CLASS,  suffix)

            param_sheet_module = import_module(module_name)
            param_sheet_class  = getattr(param_sheet_module, class_name)

        except Exception as e:
            logger.logic_log('LOSM00001', 'e: %s, Traceback: %s' % (e, traceback.format_exc()))
            return None


        return param_sheet_class


