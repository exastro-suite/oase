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
  エージェントドライバ 実行処理


"""


import pytest
import os
import django
import configparser
import datetime
import traceback
import pytz

from libs.backyardlibs.action_driver.ITA.ITA_core import ITA1Core
from libs.commonlibs.aes_cipher import AESCipher
from libs.commonlibs.define import *
from importlib import import_module

from django.conf import settings
from django.db import transaction
from mock import Mock

# 環境変数設定
oase_root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..')
os.environ['OASE_ROOT_DIR'] = oase_root_dir
os.environ['RUN_INTERVAL']  = '3600'
os.environ['PYTHON_MODULE'] = '/usr/bin/python3'
os.environ['LOG_LEVEL']     = "TRACE"
os.environ['LOG_DIR']       = oase_root_dir + "/logs/backyardlogs/exastro_collaboration/"

# 動的インポート
module = import_module('web_app.models.models')
User = getattr(module, 'User')

module2 = import_module('web_app.models.ITA_models')
ItaDriver = getattr(module2, 'ItaDriver')
ItaMenuName = getattr(module2, 'ItaMenuName')


def set_exastro_ITA_collaboration_data():
    '''
    テストデータ作成
    '''
    now = datetime.datetime.now(pytz.timezone('UTC'))
    user = User(
        user_id=999,
        user_name='unittest_procedure',
        login_id='',
        mail_address='',
        password='',
        disp_mode_id=DISP_MODE.DEFAULT,
        lang_mode_id=LANG_MODE.JP,
        password_count=0,
        password_expire=datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user='unittest_user',
        last_update_timestamp=datetime.datetime.now(pytz.timezone('UTC')),
    )
    user.save(force_insert=True)

    cipher = AESCipher(settings.AES_KEY)
    encrypted_password = cipher.encrypt('pytest')
    ita_driver = ItaDriver(
        ita_driver_id=99,
        ita_disp_name='Action43',
        protocol='https',
        hostname='pytest-host-name',
        port='443',
        username='pytest',
        password=encrypted_password,
        last_update_user='pytest',
        last_update_timestamp=now,
    )
    ita_driver.save(force_insert=True)

    ItaMenuName(
        ita_menu_name_id=1,
        ita_driver_id=99,
        menu_group_id=1,
        menu_id=1,
        menu_group_name="デフォルトテストメニューグループ名",
        menu_name="デフォルトテストメニュー名",
        last_update_timestamp=datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user="デフォルトシステム最終更新者",
    ).save(force_insert=True)

    return now, user.user_id


def del_exastro_ITA_collaboration_data():
    '''
    テストデータ作成
    '''

    User.objects.all().delete()
    ItaDriver.objects.all().delete()
    ItaMenuName.objects.all().delete()


@pytest.mark.django_db
# @pytest.mark.usefixtures('prepare_data')
class TestITAParameterSheetMenuManager(object):

    @classmethod
    def setup_class(cls):
        print('TestITAParameterSheetMenuManager - start')

    @classmethod
    def teardown_class(cls):
        print('TestITAParameterSheetMenuManager - end')

    def setup_method(self, method):
        print('method_name: {}'.format(method.__name__))

        # 動的インポート
        module = import_module('backyards.exastro_collaboration.exastro_ITA_collaboration')
        ITAParameterSheetMenuManager = getattr(module, 'ITAParameterSheetMenuManager')

        now, user_id = set_exastro_ITA_collaboration_data()
        rset = ItaDriver.objects.all().values('ita_driver_id', 'hostname', 'username', 'password', 'protocol', 'port')

        for rs in rset:
            self.target = ITAParameterSheetMenuManager(rs, user_id, now)

    def teardown_method(self, method):
        print('method_name: {}:'.format(method.__name__))
        del self.target
        del_exastro_ITA_collaboration_data()


    def get_configs(self):
        configs = {
            'Protocol': 'https',
            'Host': 'pytest-host-name',
            'PortNo': '443',
            'user': u'pytest',
            'password': u'pytest',
            'menuID': '',
        }
        return configs


    ########################
    # TESTここから
    ########################

    def test_get_menu_list_OK(self, monkeypatch):
        """
        パラメーターシートメニューの情報リストを取得(正常系)
        """

        patch_return = [[None, '', '1', 'OASEメニュー1', 'パラメータシート(ホスト/オペレーション含む)', '1', 'ホスト用', '', '', 'OASE_MenuGroup(Host)', 'OASE_MenuGroup(Ref)', '', None, None, '2020/04/10 15:02:08', 'T_20200410150208611888', 'システム管理者'], [None, '', '2', 'OASEメニュー2', 'パラメータシート(ホスト/オペレーション含む)', '2', 'ホスト 用', '', '', 'テストメニュー（Host）', 'testメニュー （Ref）', '', 'テスト', None, '2020/04/16 17:35:02', 'T_20200416173502336962', 'システム管理者']]

        monkeypatch.setattr(ITA1Core, 'select_create_menu_info_list', lambda x, y, z: (True, patch_return))
        monkeypatch.setattr(ITA1Core, 'select_menu_list', lambda a, b, menu_names=[], group_names=[], range_start=0, range_end=0: (True, patch_return))

        flg, get_data = self.target.get_menu_list()

        assert flg == True
        assert get_data == patch_return


    def test_get_menu_list_NG(self, monkeypatch):
        """
        パラメーターシートメニューの情報リストを取得(正常系)
        """

        patch_return = []
        ita_core = ITA1Core('TOS_Backyard_ParameterSheetMenuManager', 0, 0, 0)
        monkeypatch.setattr(ITA1Core, 'select_create_menu_info_list', lambda x, y, z: (False, patch_return))

        flg, get_data = self.target.get_menu_list()

        assert flg == False
        assert get_data == patch_return

    def test_save_menu_list(self):
        """
        パラメーターシートメニューの情報リストを保存
        """

        # テストケース1(追加・変更パターン)
        test_menu_list = [[None, '', '1', '1', 'OASE_MenuGroup(Host)', '1:OASE_MenuGroup(Host)', 'OASEメニュー', '要', 'サービス提供中', '1', 'する', 'しない', None, None, None, None, '2020/04/10 15:04:12', 'T_20200410150412624059', 'メニュー作成機能'], [None, '', '3', '3', '追加メニューグループ（Host）', '3:追加メニューグループ（Host）', '追加メニュー', '要', 'サービス提供中', '1', 'する', 'しない', None, None, None, None, '2020/04/16 17:36:07', 'T_20200416173607725733', 'メニュー作成機能']]

        self.target.save_menu_info(test_menu_list)
        assert ItaMenuName.objects.count() == 2

        # テストケース2(削除パターン)
        test_menu_list2 = [[None, '', '3', '3', '追加メニューグループ（Host）', '3:追加メニューグループ（Host）', '追加メニュー', '要', 'サービス提供中', '1', 'する', 'しない', None, None, None, None, '2020/04/16 17:36:07', 'T_20200416173607725733', 'メニュー作成機能']]

        self.target.save_menu_info(test_menu_list2)
        assert ItaMenuName.objects.count() == 1

        # テストケース3(ITAのデータとOASEのデータに差異がないパターン)
        self.target.save_menu_info(test_menu_list2)
        assert ItaMenuName.objects.count() == 1

        del_exastro_ITA_collaboration_data()
