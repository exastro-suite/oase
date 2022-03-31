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

from libs.backyardlibs.exastro_collaboration.ITA.param_sheet import ITAParameterSheetMenuManager
from libs.backyardlibs.oase_action_common_libs import ConstantModules as Cstobj
from libs.backyardlibs.action_driver.ITA.ITA_core import ITA1Core
from libs.commonlibs import define as defs
from libs.commonlibs.aes_cipher import AESCipher
from web_app.models.ITA_models import ItaMenuName, ItaParameterItemInfo


class ITAParameterSheetMenuManager2(ITAParameterSheetMenuManager):
    """
    [クラス概要]
        ITAパラメーターシートメニュー管理クラス
    """

    def __init__(self, drv_info, user_name, now=None):
        """
        [概要]
        コンストラクタ
        [引数]
        drv_info : dict : ITAアクション設定
        """

        super(ITAParameterSheetMenuManager2, self).__init__(drv_info, user_name, now)


    def get_hostgroup_flg(self, param_menu_list):
        """
        [概要]
        ホストグループフラグ情報を取得
        [引数]
        param_menu_list : list : パラメーターシートメニューの情報リスト
        [戻り値]
        flg       : bool : True=成功、False=失敗
        ret_info  : dict : パラメーターシートメニューの情報リスト、ホストグループフラグ情報、メニュー項目リスト
        """

        ret_info = {
            'menu_list' : [],
            'use_info'  : {},
        }

        logger.logic_log(
            'LOSI00001',
            'Start ITAParameterSheetMenuManager.get_hostgroup_flg. DriverID=%s' % (self.drv_id)
        )

        # 取得件数0件
        if len(param_menu_list) <= 0:
            return True, ret_info

        # メニュー管理取得用の条件を作成
        menu_names = []
        group_names = []
        use_info = {}
        for menu in param_menu_list:
            menu_name = ''
            group_name = ''
            hostgroup_flg = 0
            vertical_flg = False
            priority = 0

            if menu[Cstobj.FCMI_MENU_NAME]:
                menu_name = menu[Cstobj.FCMI_MENU_NAME]

            if menu[Cstobj.FCMI_USE] in ['ホストグループ用', 'For HostGroup']:
                hostgroup_flg = 1

            elif menu[Cstobj.FCMI_USE] == '':
                hostgroup_flg = -1

            if menu[Cstobj.FCMI_MENUGROUP_FOR_VERTICAL_2]:
                group_name = menu[Cstobj.FCMI_MENUGROUP_FOR_HOSTGROUP]
                vertical_flg = True
                priority = 3

            elif menu[Cstobj.FCMI_MENUGROUP_FOR_HOSTGROUP]:
                group_name = menu[Cstobj.FCMI_MENUGROUP_FOR_HOSTGROUP]
                priority = 2

            elif menu[Cstobj.FCMI_MENUGROUP_FOR_HOST]:
                group_name = menu[Cstobj.FCMI_MENUGROUP_FOR_HOST]
                priority = 1

            if menu_name and group_name:
                menu_names.append(menu_name)
                group_names.append(group_name)
                use_info[(group_name, menu_name)] = {
                    'hostgroup_flg' : hostgroup_flg,
                    'vertical_flg' : vertical_flg,
                    'priority' : priority,
                }

        # メニューグループ管理取得
        group_ids = []
        self.ita_config['menuID'] = '2100000204'
        flg, menu_list = self.ita_core.select_menugroup_list(
            self.ita_config,
            group_names=group_names,
            range_start=1
        )

        logger.logic_log('LOSI28004', 'menu_group', flg, self.drv_id, len(menu_list))

        # メニューグループ管理取得エラー
        if not flg:
            return False, ret_info

        # メニュー管理取得用の条件を作成
        group_ids = []
        for menu in menu_list:
            if menu[Cstobj.AMGL_MENU_GROUP_ID]:
                group_ids.append(menu[Cstobj.AMGL_MENU_GROUP_ID])

        # メニュー管理取得
        self.ita_config['menuID'] = '2100000205'
        flg, menu_list = self.ita_core.select_menu_list(
            self.ita_config,
            menu_names=menu_names,
            group_names=group_ids,
            range_start=1
        )

        logger.logic_log('LOSI28004', 'menu', flg, self.drv_id, len(menu_list))

        # メニュー管理取得エラー
        if not flg:
            return False, ret_info

        logger.logic_log(
            'LOSI00002',
            'End ITAParameterSheetMenuManager.get_hostgroup_flg. DriverID=%s, result=%s, count=%s' % (
                self.drv_id, flg, len(menu_list)
            )
        )

        ret_info['menu_list'] = menu_list
        ret_info['use_info'] = use_info
        return flg, ret_info



