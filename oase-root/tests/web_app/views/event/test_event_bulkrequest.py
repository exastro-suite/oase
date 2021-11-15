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
import datetime
import json
import pytz
import requests

from django.test import Client
from django.db import transaction
from django.conf import settings

from importlib import import_module

from web_app.views.event import event as event_view
from web_app.models.models import RuleType, DataObject


@pytest.mark.django_db
class TestEvent_BulkEventsRequest:
    """
    イベントリクエスト(単一)のテストクラス
    """

    ############################################################
    # テストデータ
    ############################################################
    def set_test_data(self):
        """
        テストデータの作成
        """

        # ルール種別
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
            label_count = 2,
            unknown_event_notification = '1',
            mail_address = 'pytest@pytest.com',
            disuse_flag = '0',
            last_update_timestamp = datetime.datetime(2020, 6, 4, 12, 0, 0, tzinfo=datetime.timezone.utc),
            last_update_user = 'pytest'
        ).save(force_insert=True)

        # ルール条件
        DataObject(
            data_object_id = 99991,
            rule_type_id = 9999,
            conditional_name = 'pytest_cond1',
            label = 'label0',
            conditional_expression_id = 3,
            last_update_timestamp = datetime.datetime(2020, 6, 4, 12, 0, 0, tzinfo=datetime.timezone.utc),
            last_update_user = 'pytest'
        ).save(force_insert=True)

        DataObject(
            data_object_id = 99992,
            rule_type_id = 9999,
            conditional_name = 'pytest_cond2',
            label = 'label1',
            conditional_expression_id = 3,
            last_update_timestamp = datetime.datetime(2020, 6, 4, 12, 0, 0, tzinfo=datetime.timezone.utc),
            last_update_user = 'pytest'
        ).save(force_insert=True)


    def del_test_data(self):
        """
        テストデータの削除
        """

        RuleType.objects.filter(last_update_user='pytest').delete()
        DataObject.objects.filter(last_update_user='pytest').delete()


    ############################################################
    # ダミー関数
    ############################################################
    def dummy_none(*args, **kwargs):
        """
        実態なし
        """

        return None

    def dummy_pass(*args, **kwargs):
        """
        実態なし
        """

        pass


    ############################################################
    # テスト
    ############################################################
    @pytest.mark.django_db
    def test_ok(self, monkeypatch):
        """
        一括リクエスト
        ※ 正常系
        """

        client = Client()
        self.del_test_data()
        self.set_test_data()

        # 一括リクエスト廃止に伴い、テストも廃止
        assert True

        """
        json_data = {
            "request" : [
                {
                    "decisiontable":"pytest_name",
                    "requesttype":"2",
                    "eventdatetime":"2020-01-01 00:00:00",
                    "eventinfo":["pytest1", "pytest2"]
                }
            ]
        }
        json_str = json.dumps(json_data)

        monkeypatch.setattr(event_view, '_rabbitMQ_conf', self.dummy_pass)
        monkeypatch.setattr(event_view, '_produce', self.dummy_pass)


        response = client.post(
            '/oase_web/event/event/bulk_eventsrequest', data=json_str, content_type='application/json'
        )
        resp_content = json.loads(response.content.decode('utf-8'))


        assert response.status_code == 200
        assert resp_content['result'] == True
        """

        self.del_test_data()


    @pytest.mark.django_db
    def test_ng_getmethod(self, monkeypatch):
        """
        GETメソッドリクエスト
        ※ 異常系(メソッド不正)
        """

        client = Client()
        self.del_test_data()
        self.set_test_data()

        # 一括リクエスト廃止に伴い、テストも廃止
        assert True

        """
        json_data = {
            "request" : [
                {
                    "decisiontable":"pytest_name",
                    "requesttype":"2",
                    "eventdatetime":"2020-01-01 00:00:00",
                    "eventinfo":["pytest1", "pytest2"]
                }
            ]
        }
        json_str = json.dumps(json_data)

        monkeypatch.setattr(event_view, '_rabbitMQ_conf', self.dummy_pass)
        monkeypatch.setattr(event_view, '_produce', self.dummy_pass)


        response = client.get('/oase_web/event/event/bulk_eventsrequest')
        resp_content = json.loads(response.content.decode('utf-8'))


        assert response.status_code == 200
        assert resp_content['result'] == False
        """

        self.del_test_data()


