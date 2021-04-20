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
  PrometheusAPI tests
"""


import pytest
import os
import datetime
import traceback
import pytz

from importlib import import_module

from libs.backyardlibs.monitoring_adapter.Prometheus.Prometheus_api import PrometheusApi as PromAPI


################################################################
# テスト用ダミークラス
################################################################
# Prometheusアダプター管理クラス
class DummyPromAdapter(object):

    uri    = ''
    metric = ''


################################################################
# テスト
################################################################
# メトリクス取得処理
@pytest.mark.django_db
class TestPrometheusApi_GetActiveTriggers(object):

    def test_ok(self, monkeypatch):
        """
        正常系
        """

        monkeypatch.setattr(PromAPI, '_request',   lambda a, b, c:{})
        monkeypatch.setattr(PromAPI, '_has_error', lambda a, b: False)

        now = datetime.datetime.now(pytz.timezone('UTC'))
        now = now.strftime('%Y-%m-%dT%H:%M:%S.000Z')

        prom = DummyPromAdapter()
        prom_api = PromAPI(prom)

        resp = prom_api.get_active_triggers(now, now)

        assert resp == {}


    def test_ng_errresp(self, monkeypatch):
        """
        異常系(Prometheusから異常ステータス応答)
        """

        monkeypatch.setattr(PromAPI, '_request',   lambda a, b, c:{})
        monkeypatch.setattr(PromAPI, '_has_error', lambda a, b: True)

        now = datetime.datetime.now(pytz.timezone('UTC'))
        now = now.strftime('%Y-%m-%dT%H:%M:%S.000Z')

        prom = DummyPromAdapter()
        prom_api = PromAPI(prom)

        try:
            resp = prom_api.get_active_triggers(now, now)

        except Exception as e:
            assert True

        else:
            assert False


