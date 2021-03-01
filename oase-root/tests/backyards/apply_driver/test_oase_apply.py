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


"""


import pytest
import datetime
import pytz
import requests

from libs.commonlibs.define import *
from libs.commonlibs.dt_component import DecisionTableComponent

from backyards.apply_driver import oase_apply
from backyards.apply_driver.oase_apply import delete as apply_delete

from web_app.models.models import User, RuleType, AccessPermission



@pytest.mark.django_db
class TestOaseApplyDelete:
    """
    oase_apply.delete テストクラス
    """

    ############################################################
    # テストデータ
    ############################################################
    def set_test_data(self):
        """
        テストデータ作成
        """

        now = datetime.datetime.now(pytz.timezone('UTC'))

        User(
            user_id=999,
            user_name='unittest_apply',
            login_id='',
            mail_address='',
            password='',
            disp_mode_id=DISP_MODE.DEFAULT,
            lang_mode_id=LANG_MODE.JP,
            password_count=0,
            password_expire=now,
            last_update_user='unittest_apply',
            last_update_timestamp=now,
        ).save(force_insert=True)

        RuleType(
            rule_type_id = 9999,
            rule_type_name = 'pytest_name',
            summary = None,
            rule_table_name = 'pytest_table',
            generation_limit = 5,
            group_id = 'pytest_com',
            artifact_id = 'pytest_oase',
            container_id_prefix_staging = 'test',
            container_id_prefix_product = 'prod',
            current_container_id_staging = None,
            current_container_id_product = None,
            label_count = 1,
            unknown_event_notification = '1',
            mail_address = 'pytest@pytest.com',
            disuse_flag = '0',
            last_update_timestamp = now,
            last_update_user = 'unittest_apply'
        ).save(force_insert=True)

        AccessPermission(
            permission_id = 9999,
            group_id = 9999,
            menu_id = 9999,
            rule_type_id = 9999,
            permission_type_id = 3,
            last_update_timestamp = now,
            last_update_user = 'unittest_apply'
        ).save(force_insert=True)


    def del_test_data(self):
        """
        テストデータ削除
        """

        RuleType.objects.filter(last_update_user='unittest_apply').delete()
        User.objects.filter(last_update_user='unittest_apply').delete()
        AccessPermission.objects.filter(last_update_user='unittest_apply').delete()


    ############################################################
    # Dummy
    ############################################################
    def dummy(self):

        print('Dummy.')

    def dummy_dmsettings(self):

        print('DummyDMSettings.')

        return 'http', '8080', 'dummy_id', 'dummy_pass'


    ############################################################
    # テスト
    ############################################################
    @pytest.mark.django_db
    def test_ok(self, monkeypatch):
        """
        正常系
        """

        self.set_test_data()

        monkeypatch.setattr(oase_apply, 'disconnect', self.dummy)
        monkeypatch.setattr(oase_apply, 'get_dm_conf', self.dummy_dmsettings)
        monkeypatch.setattr(requests, 'delete', lambda a:204)
        monkeypatch.setattr(DecisionTableComponent, 'remove_mavenrepository', self.dummy)
        monkeypatch.setattr(DecisionTableComponent, 'remove_component', lambda a, b:None)

        req = {
            'user_id' : 999,
            'ruletypeid' : 9999,
        }

        result = apply_delete(req)

        assert result['result'] == 'OK'

        self.del_test_data()


