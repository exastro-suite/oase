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

import pytest
import unittest

import datetime
import os
import pytz
import subprocess
import time
from importlib import import_module
from socket import gethostname

from libs.commonlibs import define as defs
from web_app.models.models import User


# 環境変数設定
oase_root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..')
os.environ['OASE_ROOT_DIR'] = oase_root_dir
os.environ['RUN_INTERVAL']  = '3'
os.environ['PYTHON_MODULE'] = '/usr/bin/python3'
os.environ['LOG_LEVEL']     = "TRACE"
os.environ['LOG_DIR']       = oase_root_dir + "/logs/backyardlogs/oase_monitoring/"

TEST_ZABBIX_ADAPTER_ID = 1234567

# @pytest.mark.django_db
# @pytest.fixture(scope='class')
# def prepare_data(django_db_blocker):

#     with django_db_blocker.unblock():
#         user = User(
#             user_id      = -2140000005,
#             user_name    = 'unittest_procedure',
#             login_id     = '',
#             mail_address = '',
#             password     = '',
#             disp_mode_id = defs.DISP_MODE.DEFAULT,
#             lang_mode_id = defs.LANG_MODE.JP,
#             password_count = 0,
#             password_expire = datetime.datetime.now(pytz.timezone('UTC')),
#             last_update_user = 'unittest_user',
#             last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
#         )
#         user.save(force_insert=True)

#     yield

#     with django_db_blocker.unblock():
#         user.delete()

@pytest.fixture(scope='function')
def ZABBIX_adapter_data():

    # 動的インポート
    module = import_module('web_app.models.ZABBIX_monitoring_models')
    ZabbixAdapter = getattr(module, 'ZabbixAdapter')

    zabbix_adapter_list = []
    for index in range(1, 4):
        zabbix_adapter = ZabbixAdapter(
                zabbix_adapter_id   = TEST_ZABBIX_ADAPTER_ID + index,
                zabbix_disp_name    = 'unittest_zabbix_adapter' + str(index),
                hostname            = 'localhost',
                username            = 'unittest_user',
                password            = 'unittest_passwd',
                protocol            = 'http',
                port                = '80',
                rule_type_id        = 123456789 + index,
                last_update_user    = 'unittest_user',
                last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
            )
        zabbix_adapter.save(force_insert=True)
        zabbix_adapter_list.append(zabbix_adapter)

    yield

    for zabbix_adapter_item in zabbix_adapter_list:
        zabbix_adapter_item.delete()

@pytest.fixture(scope='function')
def ZABBIX_monitoring_history_data():

    # 動的インポート
    module = import_module('web_app.models.ZABBIX_monitoring_models')
    ZabbixMonitoringHistory = getattr(module, 'ZabbixMonitoringHistory')

    zabbix_monitoring_history_list = []
    for index in range(1, 5):
        zabbix_monitoring_history = ZabbixMonitoringHistory(
                zabbix_adapter_id     = TEST_ZABBIX_ADAPTER_ID + index,
                zabbix_lastchange     = index,
                status                = index,
                status_update_id      = gethostname(),
                last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
                last_update_user      = 'unittest_user',
            )
        zabbix_monitoring_history.save(force_insert=True)
        zabbix_monitoring_history_list.append(zabbix_monitoring_history)

    yield

    for zabbix_monitoring_history_item in zabbix_monitoring_history_list:
        zabbix_monitoring_history_item.delete()


@pytest.mark.django_db
# @pytest.mark.usefixtures('prepare_data')
class TestZabbixAdapterMainModules(object):

    @classmethod
    def setup_class(cls):
        print('TestZabbixAdapterMainModules - start')

    @classmethod
    def teardown_class(cls):
        print('TestZabbixAdapterMainModules - end')

    def setup_method(self, method):
        print('method_name: {}'.format(method.__name__))

        # 動的インポート
        module = import_module('backyards.monitoring_adapter.ZABBIX_monitoring')
        ZabbixAdapterMainModules = getattr(module, 'ZabbixAdapterMainModules')

        self.target = ZabbixAdapterMainModules()

    def teardown_method(self, method):
        print('method_name: {}:'.format(method.__name__))
        del self.target


    ########################
    # TESTここから
    ########################

    @pytest.mark.usefixtures('zabbix_table')
    def test_execute_subprocess_1(self):

        expected_return = True
        expected_aryPCB_keys = [TEST_ZABBIX_ADAPTER_ID,]

        aryPCB = {}
        zabbix_adapter_id = TEST_ZABBIX_ADAPTER_ID
        actual_return = self.target.execute_subprocess(aryPCB, zabbix_adapter_id)

        assert expected_return == actual_return
        assert expected_aryPCB_keys == list(aryPCB)
        assert aryPCB[TEST_ZABBIX_ADAPTER_ID] is not None

    @pytest.mark.usefixtures('zabbix_table')
    def test_execute_subprocess_2(self):

        expected_return = False
        expected_aryPCB_keys = []

        with unittest.mock.patch('subprocess.Popen.__init__') as popen_constructor:
            popen_constructor.side_effect = Exception()

            aryPCB = {}
            zabbix_adapter_id = TEST_ZABBIX_ADAPTER_ID
            actual_return = self.target.execute_subprocess(aryPCB, zabbix_adapter_id)

            assert expected_return == actual_return
            assert expected_aryPCB_keys == list(aryPCB)

    @pytest.mark.usefixtures('zabbix_table', 'ZABBIX_adapter_data')
    def test_do_normal_1(self):

        expected_return = True
        expected_aryPCB_keys = [TEST_ZABBIX_ADAPTER_ID + i for i in range(1, 4)]

        aryPCB = {}
        actual_return = self.target.do_normal(aryPCB)

        assert expected_return == actual_return
        assert expected_aryPCB_keys == list(aryPCB)
        for j in range(1, 4):
            assert aryPCB[TEST_ZABBIX_ADAPTER_ID + j] is not None, 'loop %s' % str(j)

    @pytest.mark.usefixtures('zabbix_table', 'ZABBIX_adapter_data')
    def test_do_normal_2(self):

        expected_return = False

        with unittest.mock.patch('backyards.monitoring_adapter.ZABBIX_monitoring.ZabbixAdapterMainModules.execute_subprocess') as mock_method:
            mock_method.side_effect = [True, True, False]

            aryPCB = {}
            actual_return = self.target.do_normal(aryPCB)

            assert expected_return == actual_return

    @pytest.mark.usefixtures('zabbix_table')
    def test_observe_subprocess_1(self):

        expected_return = True
        expected_aryPCB_keys = []

        aryPCB = {}
        args = ['/bin/echo', 'unittest']
        for i in (100, 200, 300):
            proc = subprocess.Popen(args, stderr=subprocess.PIPE, shell=False)
            aryPCB[i] = proc

        time.sleep(1) # サーバ負荷によってはエラーになるかも？要改善？
        actual_return = self.target.observe_subprocess(aryPCB)

        assert expected_return == actual_return
        assert expected_aryPCB_keys == list(aryPCB)

    @pytest.mark.usefixtures('zabbix_table')
    def test_observe_subprocess_2(self):

        expected = False

        aryPCB = {99: None,}
        actual = self.target.observe_subprocess(aryPCB)

        assert expected == actual


    @pytest.mark.usefixtures('zabbix_table', 'ZABBIX_monitoring_history_data')
    def test_set_force_terminate_status(self):

        expected_status = [4, 2, 3, 4]
        # expected_last_update_user = ['unittest_procedure', 'unittest_user', 'unittest_user', 'unittest_user']
        expected_last_update_user = ['ZABBIXアダプタプロシージャ', 'unittest_user', 'unittest_user', 'unittest_user']

        self.target.set_force_terminate_status()

        # 動的インポート
        module = import_module('web_app.models.ZABBIX_monitoring_models')
        ZabbixMonitoringHistory = getattr(module, 'ZabbixMonitoringHistory')

        actual_data = ZabbixMonitoringHistory.objects.all().order_by('zabbix_monitoring_his_id')

        for i in range(0, 4):
            assert expected_status[i] == actual_data[i].status, 'loop=%s' % str(i)
            assert expected_last_update_user[i] == actual_data[i].last_update_user, 'loop=%s' % str(i)
