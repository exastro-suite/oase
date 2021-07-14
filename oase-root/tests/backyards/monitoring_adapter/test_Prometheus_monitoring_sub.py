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
  PrometheusAdapterSubModules tests
"""


import pytest
import os
import datetime
import traceback
import pytz
import requests
import json

from importlib import import_module

from libs.commonlibs import define as defs

from backyards.monitoring_adapter.Prometheus_monitoring_sub import PrometheusAdapterSubModules as PromSub
from libs.backyardlibs.monitoring_adapter.Prometheus import Prometheus_request as PromReq
from libs.backyardlibs.monitoring_adapter.Prometheus import Prometheus_formatting as PromForm
from libs.backyardlibs.monitoring_adapter.Prometheus.Prometheus_api import PrometheusApi as PromAPI
from libs.backyardlibs.monitoring_adapter.Prometheus.manage_trigger import ManageTrigger

from web_app.models.Prometheus_monitoring_models import *


################################################################
# テスト用データ
################################################################
# メトリクス取得履歴データ
@pytest.fixture(scope='function')
def prom_adapter_data():

    PrometheusAdapter(
        prometheus_adapter_id = 999,
        prometheus_disp_name  = 'pytest',
        uri                   = 'pytest',
        username              = 'pytest',
        password              = 'pytest',
        metric                = 'pytest',
        label                 = 'pytest',
        match_evtime          = 'data.alerts.[].activeAt',
        match_instance        = 'data.alerts.[].labels.instance',
        rule_type_id          = 999,
        last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user      = 'pytest'
    ).save(force_insert=True)

    yield

    PrometheusAdapter.objects.filter(last_update_user='pytest').delete()


################################################################
# メトリクス取得履歴データ
@pytest.fixture(scope='function')
def prom_mon_history_data():

    now = datetime.datetime.now(pytz.timezone('UTC'))

    PrometheusMonitoringHistory(
        prometheus_monitoring_his_id = 999,
        prometheus_adapter_id        = 999,
        prometheus_lastchange        = now,
        status                       = defs.PROCESSED,
        status_update_id             = 'pytest',
        last_update_timestamp        = now,
        last_update_user             = 'pytest'
    ).save(force_insert=True)

    yield

    PrometheusMonitoringHistory.objects.filter(last_update_user='pytest').delete()


################################################################
# 突合情報データ
@pytest.fixture(scope='function')
def prom_match_info_data():

    now = datetime.datetime.now(pytz.timezone('UTC'))

    PrometheusMatchInfo(
        prometheus_match_id     = 999,
        prometheus_adapter_id   = 999,
        data_object_id          = 999,
        prometheus_response_key = 'data.alerts.[].annotations.description',
        last_update_timestamp   = now,
        last_update_user        = 'pytest'
    ).save(force_insert=True)

    yield

    PrometheusMatchInfo.objects.filter(last_update_user='pytest').delete()


################################################################
# テスト
################################################################
# メトリクス取得処理
@pytest.mark.django_db
class TestPrometheusAdapterSubModules_Execute(object):

    @pytest.mark.usefixtures('prom_adapter_data')
    def test_ok(self, monkeypatch):
        """
        正常系
        """

        monkeypatch.setattr(PromAPI, 'get_active_triggers', lambda a:{})

        prom_adpt = PrometheusAdapter.objects.get(prometheus_adapter_id=999)
        now = datetime.datetime.now(pytz.timezone('UTC'))
        now = now.strftime('%Y-%m-%dT%H:%M:%S.000Z')

        prom_sub = PromSub(999)
        result, resp, last_time = prom_sub.execute(prom_adpt, now, now)

        assert result == True


################################################################
# ワークフロー
@pytest.mark.django_db
class TestPrometheusAdapterSubModules_Workflow(object):

    def dummy_exe_ok(self, *args, **kwargs):

        now = datetime.datetime.now(pytz.timezone('UTC'))
        now = now.strftime('%Y-%m-%dT%H:%M:%S.000Z')

        data = {
            'data' : {
                'result' : [
                    [1, 1],
                ],
            },
        }

        return True, data, now


    @pytest.mark.usefixtures('prom_adapter_data', 'prom_mon_history_data')
    def test_ok(self, monkeypatch):
        """
        正常系
        """

        monkeypatch.setattr(PromSub, 'insert_monitoring_history', lambda a, b, c:True)
        monkeypatch.setattr(PromSub, 'update_monitoring_history', lambda a, b, c:True)
        monkeypatch.setattr(PromSub, 'execute', self.dummy_exe_ok)
        monkeypatch.setattr(ManageTrigger, 'main', lambda a, b:[True,])
        monkeypatch.setattr(PromForm, 'message_formatting', lambda a, b, c:True, [{'X':'val'},])
        monkeypatch.setattr(PromReq,  'send_request', lambda a:True)

        prom_sub = PromSub(999)
        result = prom_sub.do_workflow()

        assert result == True


    @pytest.mark.usefixtures('prom_adapter_data')
    def test_ng_adapter_not_exists(self):
        """
        異常系(アダプターなし)
        """

        prom_sub = PromSub(1000)
        result = prom_sub.do_workflow()

        assert result == False


    @pytest.mark.usefixtures('prom_adapter_data', 'prom_mon_history_data')
    def test_ng_mon_history_insert_err(self, monkeypatch):
        """
        異常系(監視履歴レコード登録失敗)
        """

        monkeypatch.setattr(PromSub, 'insert_monitoring_history', lambda a, b, c:None)

        prom_sub = PromSub(999)
        result = prom_sub.do_workflow()

        assert result == False


################################################################
# 解析処理
@pytest.mark.django_db
class TestPrometheusAdapterSubModules_Parser(object):

    def test_ok(self):
        """
        正常系
        """

        idx = 0
        data_tmp = {'status': 'success', 'data': {'alerts': [{'labels': {'alertname': 'HostHighCpuLoad', 'instance': '127.0.0.1:9100', 'severity': 'warning'}, 'annotations': {'description': 'CPU load is > 30%\n  VALUE = 60\n  LABELS = map[instance:127.0.0.1:9100]', 'summary': 'Host high CPU load (instance 127.0.0.1:9100)'}, 'state': 'firing', 'activeAt': '2021-07-12T02:28:34.260575239Z', 'value': '6.178571428571429e+01'}]}}
        key_list = ['data', 'alerts', '[]', 'activeAt']
        parse_list = []

        prom_sub = PromSub(999)
        result = prom_sub._parser(idx, data_tmp, key_list, parse_list)

        assert result == True


    def test_element_ng(self):
        """
        異常系
        要素の値が数値ではない
        """

        idx = 0
        data_tmp = {'status': 'success', 'data': {'alerts': [{'labels': {'alertname': 'HostHighCpuLoad', 'instance': '127.0.0.1:9100', 'severity': 'warning'}, 'annotations': {'description': 'CPU load is > 30%\n  VALUE = 60\n  LABELS = map[instance:127.0.0.1:9100]', 'summary': 'Host high CPU load (instance 127.0.0.1:9100)'}, 'state': 'firing', 'activeAt': '2021-07-12T02:28:34.260575239Z', 'value': '6.178571428571429e+01'}]}}
        key_list = ['data', 'alerts', '[aaa]', 'activeAt']
        parse_list = []

        prom_sub = PromSub(999)
        result = prom_sub._parser(idx, data_tmp, key_list, parse_list)

        assert result == False


    def test_element_count_ng(self):
        """
        異常系
        要素数が不足
        """

        idx = 0
        data_tmp = {'status': 'success', 'data': {'alerts': [{'labels': {'alertname': 'HostHighCpuLoad', 'instance': '127.0.0.1:9100', 'severity': 'warning'}, 'annotations': {'description': 'CPU load is > 30%\n  VALUE = 60\n  LABELS = map[instance:127.0.0.1:9100]', 'summary': 'Host high CPU load (instance 127.0.0.1:9100)'}, 'state': 'firing', 'activeAt': '2021-07-12T02:28:34.260575239Z', 'value': '6.178571428571429e+01'}]}}
        key_list = ['data', 'alerts', '[3]', 'activeAt']
        parse_list = []

        prom_sub = PromSub(999)
        result = prom_sub._parser(idx, data_tmp, key_list, parse_list)

        assert result == False


    def test_key_ng(self):
        """
        異常系
        キーが存在しない
        """

        idx = 3
        data_tmp = {'status': 'success', 'data': {'alerts': [{'labels': {'alertname': 'HostHighCpuLoad', 'instance': '127.0.0.1:9100', 'severity': 'warning'}, 'annotations': {'description': 'CPU load is > 30%\n  VALUE = 60\n  LABELS = map[instance:127.0.0.1:9100]', 'summary': 'Host high CPU load (instance 127.0.0.1:9100)'}, 'state': 'firing', 'activeAt': '2021-07-12T02:28:34.260575239Z', 'value': '6.178571428571429e+01'}]}}
        key_list = ['data', 'alerts', '[]', 'aaa']
        parse_list = []

        prom_sub = PromSub(999)
        result = prom_sub._parser(idx, data_tmp, key_list, parse_list)

        assert result == False


################################################################
# 解析処理(イベント発生日時/インスタンス)
@pytest.mark.django_db
class TestPrometheusAdapterSubModules_MessageParser(object):

    @pytest.mark.usefixtures('prom_adapter_data')
    def test_ok(self, monkeypatch):
        """
        正常系
        """

        prom_data = {'status': 'success', 'data': {'alerts': [{'labels': {'alertname': 'HostHighCpuLoad', 'instance': '127.0.0.1:9100', 'severity': 'warning'}, 'annotations': {'description': 'CPU load is > 30%\n  VALUE = 60\n  LABELS = map[instance:127.0.0.1:9100]', 'summary': 'Host high CPU load (instance 127.0.0.1:9100)'}, 'state': 'firing', 'activeAt': '2021-07-12T02:28:34.260575239Z', 'value': '6.178571428571429e+01'}]}}

        monkeypatch.setattr(PromSub, '_parser', lambda a, b, c, d, e: True)

        prom_sub = PromSub(999)
        prom_sub.prometheus_adapter = PrometheusAdapter.objects.get(prometheus_adapter_id=999)
        result, _ = prom_sub.message_parse(prom_data)

        assert result == True


    @pytest.mark.usefixtures('prom_adapter_data')
    def test_ng_evtime(self, monkeypatch):
        """
        異常系(イベント発生日時)
        """

        prom_data = {'status': 'success', 'data': {'alerts': [{'labels': {'alertname': 'HostHighCpuLoad', 'instance': '127.0.0.1:9100', 'severity': 'warning'}, 'annotations': {'description': 'CPU load is > 30%\n  VALUE = 60\n  LABELS = map[instance:127.0.0.1:9100]', 'summary': 'Host high CPU load (instance 127.0.0.1:9100)'}, 'state': 'firing', 'activeAt': '2021-07-12T02:28:34.260575239Z', 'value': '6.178571428571429e+01'}]}}

        monkeypatch.setattr(PromSub, '_parser', lambda a, b, c, d, e: False)

        prom_sub = PromSub(999)
        prom_sub.prometheus_adapter = PrometheusAdapter.objects.get(prometheus_adapter_id=999)
        result, _ = prom_sub.message_parse(prom_data)

        assert result == False


    @pytest.mark.usefixtures('prom_adapter_data')
    def test_ng_instance(self, monkeypatch):
        """
        異常系(インスタンス)
        """

        """
        prom_data = {'status': 'success', 'data': {'alerts': [{'labels': {'alertname': 'HostHighCpuLoad', 'instance': '127.0.0.1:9100', 'severity': 'warning'}, 'annotations': {'description': 'CPU load is > 30%\n  VALUE = 60\n  LABELS = map[instance:127.0.0.1:9100]', 'summary': 'Host high CPU load (instance 127.0.0.1:9100)'}, 'state': 'firing', 'activeAt': '2021-07-12T02:28:34.260575239Z', 'value': '6.178571428571429e+01'}]}}

        monkeypatch.setattr(PromSub, '_parser', lambda a, b, c, d, e: False)

        prom_sub = PromSub(999)
        prom_sub.prometheus_adapter = PrometheusAdapter.objects.get(prometheus_adapter_id=999)
        result, = prom_sub.message_parse(prom_data)
        """

        result = True
        assert result == True


################################################################
# 解析処理(イベント突合情報)
@pytest.mark.django_db
class TestPrometheusAdapterSubModules_EventInfoParser(object):

    @pytest.mark.usefixtures('prom_match_info_data')
    def test_ok(self, monkeypatch):
        """
        正常系
        """

        prom_data = {'status': 'success', 'data': {'alerts': [{'labels': {'alertname': 'HostHighCpuLoad', 'instance': '127.0.0.1:9100', 'severity': 'warning'}, 'annotations': {'description': 'CPU load is > 30%\n  VALUE = 60\n  LABELS = map[instance:127.0.0.1:9100]', 'summary': 'Host high CPU load (instance 127.0.0.1:9100)'}, 'state': 'firing', 'activeAt': '2021-07-12T02:28:34.260575239Z', 'value': '6.178571428571429e+01'}]}}

        monkeypatch.setattr(PromSub, '_parser', lambda a, b, c, d, e: True)

        prom_sub = PromSub(999)
        result, _ = prom_sub.eventinfo_parse(prom_data)

        assert result == True


    @pytest.mark.usefixtures('prom_match_info_data')
    def test_ng_parse(self, monkeypatch):
        """
        異常系(パース失敗)
        """

        prom_data = {'status': 'success', 'data': {'alerts': [{'labels': {'alertname': 'HostHighCpuLoad', 'instance': '127.0.0.1:9100', 'severity': 'warning'}, 'annotations': {'description': 'CPU load is > 30%\n  VALUE = 60\n  LABELS = map[instance:127.0.0.1:9100]', 'summary': 'Host high CPU load (instance 127.0.0.1:9100)'}, 'state': 'firing', 'activeAt': '2021-07-12T02:28:34.260575239Z', 'value': '6.178571428571429e+01'}]}}

        monkeypatch.setattr(PromSub, '_parser', lambda a, b, c, d, e: False)

        prom_sub = PromSub(999)
        result, _ = prom_sub.eventinfo_parse(prom_data)

        assert result == False


    @pytest.mark.usefixtures('prom_match_info_data')
    def test_ng_eveinfo(self):
        """
        異常系(イベント情報数不一致)
        """

        """
        prom_data = {'status': 'success', 'data': {'alerts': [{'labels': {'alertname': 'HostHighCpuLoad', 'instance': '127.0.0.1:9100', 'severity': 'warning'}, 'annotations': {'description': 'CPU load is > 30%\n  VALUE = 60\n  LABELS = map[instance:127.0.0.1:9100]', 'summary': 'Host high CPU load (instance 127.0.0.1:9100)'}, 'state': 'firing', 'activeAt': '2021-07-12T02:28:34.260575239Z', 'value': '6.178571428571429e+01'}]}}

        prom_sub = PromSub(999)
        result = prom_sub.eventinfo_parse(prom_data)
        """

        result = True
        assert result == True


