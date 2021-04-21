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
  PrometheusFormat tests
"""


import pytest
import os
import datetime
import traceback
import pytz

from importlib import import_module

from libs.backyardlibs.monitoring_adapter.Prometheus import Prometheus_formatting as PromForm
from web_app.models.models import RuleType
from web_app.models.Prometheus_monitoring_models import PrometheusMatchInfo


################################################################
# テスト用データ
################################################################
# ルール種別データ
@pytest.fixture(scope='function')
def rule_type_data():

    RuleType(
        rule_type_id                 = 999,
        rule_type_name               = 'pytest_name',
        summary                      = 'pytest',
        rule_table_name              = 'pytest_table_name',
        generation_limit             = 3,
        group_id                     = 'pytest_group',
        artifact_id                  = 'pytest_artifact',
        container_id_prefix_staging  = 'pytest',
        container_id_prefix_product  = 'pytest',
        current_container_id_staging = 'pytest',
        current_container_id_product = 'pytest',
        label_count                  = 1,
        unknown_event_notification   = '0',
        mail_address                 = '',
        servicenow_driver_id         = 0,
        disuse_flag                  = '0',
        last_update_timestamp        = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user             = 'pytest'
    ).save(force_insert=True)

    yield

    RuleType.objects.filter(last_update_user='pytest').delete()


################################################
# ルール突合情報データ
@pytest.fixture(scope='function')
def match_info_data():

    PrometheusMatchInfo(
        prometheus_match_id     = 999,
        prometheus_adapter_id   = 999,
        data_object_id          = 1,
        prometheus_response_key = 999,
        last_update_timestamp   = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user        = 'pytest'
    ).save(force_insert=True)

    yield

    PrometheusMatchInfo.objects.filter(last_update_user='pytest').delete()


################################################################
# テスト
################################################################
# メイン処理
@pytest.mark.django_db
class TestMessageFormatting(object):

    @pytest.mark.usefixtures('rule_type_data', 'match_info_data')
    def test_ok(self, monkeypatch):
        """
        正常系
        """

        monkeypatch.setattr(PromForm, 'formatting_eventinfo', lambda a, b, c:True)

        result, form_data = PromForm.message_formatting([[1,1],], 999, 999)

        assert result == True


    def test_ng_msg_zero(self):
        """
        異常系(メッセージ0件)
        """

        result, form_data = PromForm.message_formatting([], 999, 999)

        assert result == False


    def test_ng_rule_none(self):
        """
        異常系(ルール種別なし)
        """

        result, form_data = PromForm.message_formatting([[1,1],], None, 999)

        assert result == False


    def test_ng_adapter_none(self):
        """
        異常系(ルール種別なし)
        """

        result, form_data = PromForm.message_formatting([[1,1],], 999, None)

        assert result == False


    @pytest.mark.usefixtures('rule_type_data')
    def test_ng_rule_not_exists(self):
        """
        異常系(ルール種別レコードなし)
        """

        result, form_data = PromForm.message_formatting([[1,1],], 998, 999)

        assert result == False


    @pytest.mark.usefixtures('rule_type_data', 'match_info_data')
    def test_ng_unmatch_event(self, monkeypatch):
        """
        異常系(イベント情報アンマッチ)
        """

        monkeypatch.setattr(PromForm, 'formatting_eventinfo', lambda a, b, c:False)

        result, form_data = PromForm.message_formatting([[1,1],], 999, 999)

        assert result == False


