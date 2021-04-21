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
  PrometheusManageTrigger tests
"""


import pytest
import os
import datetime
import traceback
import pytz

from importlib import import_module

from libs.backyardlibs.monitoring_adapter.Prometheus.manage_trigger import ManageTrigger
from web_app.models.Prometheus_monitoring_models import PrometheusTriggerHistory


################################################################
# テスト用データ
################################################################
# メトリクス取得履歴データ
@pytest.fixture(scope='function')
def prom_trig_history_data():

    PrometheusTriggerHistory(
        prometheus_trigger_his_id = 999,
        prometheus_adapter_id     = 999,
        trigger_id                = 999,
        lastchange                = 1,
        last_update_timestamp     = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user          = 'pytest'
    ).save(force_insert=True)

    PrometheusTriggerHistory(
        prometheus_trigger_his_id = 998,
        prometheus_adapter_id     = 999,
        trigger_id                = 998,
        lastchange                = 1,
        last_update_timestamp     = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user          = 'pytest'
    ).save(force_insert=True)

    PrometheusTriggerHistory(
        prometheus_trigger_his_id = 997,
        prometheus_adapter_id     = 999,
        trigger_id                = 997,
        lastchange                = 1,
        last_update_timestamp     = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user          = 'pytest'
    ).save(force_insert=True)

    yield

    PrometheusTriggerHistory.objects.filter(last_update_user='pytest').delete()


################################################################
# テスト
################################################################
# メイン処理
@pytest.mark.django_db
class TestManageTrigger_Main(object):

    @pytest.mark.usefixtures('prom_trig_history_data')
    def test_ok(self, monkeypatch):
        """
        正常系
        """

        test_data = [
            [1000, 1],  # 新規登録
            [ 999, 1],  # 変更なし
            [ 998, 2],  # 変更あり
        ]

        monkeypatch.setattr(ManageTrigger, 'create', lambda a, b, c, d:None)
        monkeypatch.setattr(ManageTrigger, 'update', lambda a, b, c, d:None)
        monkeypatch.setattr(ManageTrigger, 'delete_resolved_records', lambda a, b, c:None)

        trig = ManageTrigger(999, 'pytest')

        resp = trig.main(test_data)

        assert len(resp) == 3
        assert resp[0] == True   # 新規登録
        assert resp[1] == False  # 変更なし
        assert resp[2] == True   # 変更あり


