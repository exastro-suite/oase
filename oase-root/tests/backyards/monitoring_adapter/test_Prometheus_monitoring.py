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
from unittest.mock import patch

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


TEST_PROMETHEUS_ADAPTER_ID = 1234567

@pytest.fixture(scope='function')
def Prometheus_adapter_data():

    #動的インポート
    module = import_module('web_app.models.Prometheus_monitoring_models')
    PrometheusAdapter = getattr(module,'PrometheusAdapter')

    prometheus_adapter_list = []
    for index in range(1,4):
        prometheus_adapter = PrometheusAdapter(
                prometheus_adapter_id = TEST_PROMETHEUS_ADAPTER_ID + index,
                prometheus_disp_name  = 'unittest_prometheus_adapter' + str(index),
                uri                   = 'localhost',
                username              = 'unittest_user',
                password              = 'unittest_passwd',
                metric                = 'unittest_metric',
                label                 = 'unittest_label',
                rule_type_id          = 123456789 + index,
                last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
                last_update_user      = 'unittest_user'
        )
        prometheus_adapter.save(force_insert=True)
        prometheus_adapter_list.append(prometheus_adapter)
    yield

    for prometheus_adapter_item in prometheus_adapter_list:
        prometheus_adapter_item.delete()

@pytest.fixture(scope='function')
def Prometheus_monitoring_history_data():

    # 動的インポート
    module = import_module('web_app.models.Prometheus_monitoring_models')
    PrometheusMonitoringHistory = getattr(module, 'PrometheusMonitoringHistory')

    prometheus_monitoring_history_list = []
    for index in range(1, 5):
        prometheus_monitoring_history = PrometheusMonitoringHistory(
                prometheus_adapter_id     = TEST_PROMETHEUS_ADAPTER_ID + index,
                prometheus_lastchange     = datetime.datetime.now(pytz.timezone('UTC')),
                status                    = index,
                status_update_id          = gethostname(),
                last_update_timestamp     = datetime.datetime.now(pytz.timezone('UTC')),
                last_update_user          = 'unittest_user'
            )
        prometheus_monitoring_history.save(force_insert=True)
        prometheus_monitoring_history_list.append(prometheus_monitoring_history)
    yield

    for prometheus_monitoring_history_item in prometheus_monitoring_history_list:
        prometheus_monitoring_history_item.delete()

@pytest.mark.django_db
class TestPrometheusAdapterMainModules(object):

    @classmethod
    def setup_class(cls):
        print('TestPrometheusAdapterMainModules - start')

    @classmethod
    def teardown_class(cls):
        print('TestPrometheusAdapterMainModules - end')

    def setup_method(self, method):
        print('method_name: {}'.format(method.__name__))

        # 動的インポート
        module = import_module('backyards.monitoring_adapter.Prometheus_monitoring')
        PrometheusAdapterMainModules = getattr(module, 'PrometheusAdapterMainModules')

        self.target = PrometheusAdapterMainModules()

    def teardown_method(self, method):
        print('method_name: {}:'.format(method.__name__))
        del self.target


    ########################
    # TESTここから
    ########################

    @pytest.mark.usefixtures('prometheus_table')
    def test_execute_subprocess_1(self):

        expected_return = True
        expected_aryPCB_keys = [TEST_PROMETHEUS_ADAPTER_ID,]

        aryPCB = {}
        prometheus_adapter_id = TEST_PROMETHEUS_ADAPTER_ID
        actual_return = self.target.execute_subprocess(aryPCB, prometheus_adapter_id)

        assert expected_return == actual_return
        assert expected_aryPCB_keys == list(aryPCB)
        assert aryPCB[TEST_PROMETHEUS_ADAPTER_ID] is not None

    @pytest.mark.usefixtures('prometheus_table')
    def test_execute_subprocess_2(self):

        expected_return = False
        expected_aryPCB_keys = []

        with patch('subprocess.Popen.__init__') as popen_constructor:
            popen_constructor.side_effect = Exception()

            aryPCB = {}
            prometheus_adapter_id = TEST_PROMETHEUS_ADAPTER_ID
            actual_return = self.target.execute_subprocess(aryPCB, prometheus_adapter_id)

            assert expected_return == actual_return
            assert expected_aryPCB_keys == list(aryPCB)


    @pytest.mark.usefixtures('prometheus_table', 'Prometheus_adapter_data')
    def test_do_normal_1(self):

        expected_return = True
        expected_aryPCB_keys = [TEST_PROMETHEUS_ADAPTER_ID + i for i in range(1, 4)]

        aryPCB = {}
        actual_return = self.target.do_normal(aryPCB)

        assert expected_return == actual_return
        assert expected_aryPCB_keys == list(aryPCB)
        for j in range(1, 4):
            assert aryPCB[TEST_PROMETHEUS_ADAPTER_ID + j] is not None, 'loop %s' % str(j)

    @pytest.mark.usefixtures('prometheus_table', 'Prometheus_adapter_data')
    def test_do_normal_2(self):

        expected_return = False

        with patch('backyards.monitoring_adapter.Prometheus_monitoring.PrometheusAdapterMainModules.execute_subprocess') as mock_method:
            mock_method.side_effect = [True, True, False]

            aryPCB = {}
            actual_return = self.target.do_normal(aryPCB)

            assert expected_return == actual_return

    @pytest.mark.usefixtures('prometheus_table')
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

    @pytest.mark.usefixtures('prometheus_table')
    def test_observe_subprocess_2(self):

        expected = False

        aryPCB = {99: None,}
        actual = self.target.observe_subprocess(aryPCB)

        assert expected == actual


    @pytest.mark.usefixtures('prometheus_table', 'Prometheus_monitoring_history_data')
    def test_set_force_terminate_status(self):

        expected_status = [4, 2, 3, 4]
        expected_last_update_user = ['Prometheusアダプタプロシージャ', 'unittest_user', 'unittest_user', 'unittest_user']

        self.target.set_force_terminate_status()

        # 動的インポート
        module = import_module('web_app.models.Prometheus_monitoring_models')
        PrometheusMonitoringHistory = getattr(module, 'PrometheusMonitoringHistory')

        actual_data = PrometheusMonitoringHistory.objects.all().order_by('prometheus_monitoring_his_id')

        for i in range(0, 4):
            assert expected_status[i] == actual_data[i].status, 'loop=%s' % str(i)
            assert expected_last_update_user[i] == actual_data[i].last_update_user, 'loop=%s' % str(i)
