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

from django.urls import reverse
from django.http import Http404, HttpResponse
from django.test import Client, RequestFactory
from django.db import transaction
from django.conf import settings

from importlib import import_module

from libs.commonlibs.common import Common
from libs.webcommonlibs.user_config import UserConfig
from web_app.models.models import RuleType, DataObject


@pytest.mark.django_db
class TestEvent_EventsRequest:
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
            label_count = 1,
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
    # テスト
    ############################################################
    @pytest.mark.django_db
    def test_ok_stg(self):
        """
        ステージング向けリクエスト
        ※ 正常系
        """

        client = Client()
        self.del_test_data()
        self.set_test_data()

        json_data = {
            "decisiontable":"pytest_name",
            "requesttype":"2",
            "eventdatetime":"2020-01-01 00:00:00",
            "eventinfo":["pytest1", "pytest2"]
        }
        json_str = json.dumps(json_data)


        response = client.post('/oase_web/event/event/eventsrequest', data=json_str, content_type='application/json')
        resp_content = json.loads(response.content.decode('utf-8'))


        assert response.status_code == 200
        assert resp_content['result'] == True

        self.del_test_data()


    @pytest.mark.django_db
    def test_ng_getmethod(self):
        """
        GETメソッドリクエスト
        ※ 異常系(メソッド不正)
        """

        client = Client()
        self.del_test_data()
        self.set_test_data()

        json_data = {
            "decisiontable":"pytest_name",
            "requesttype":"2",
            "eventdatetime":"2020-01-01 00:00:00",
            "eventinfo":["pytest1", "pytest2"]
        }
        json_str = json.dumps(json_data)


        response = client.get('/oase_web/event/event/eventsrequest')
        resp_content = json.loads(response.content.decode('utf-8'))


        assert response.status_code == 200
        assert resp_content['result'] == False

        self.del_test_data()


    @pytest.mark.django_db
    def test_ng_nojson(self):
        """
        非JSON形式のリクエスト
        ※ 異常系(非JSON形式)
        """

        client = Client()
        self.del_test_data()
        self.set_test_data()

        json_data = {
            "decisiontable":"pytest_name",
            "requesttype":"2",
            "eventdatetime":"2020-01-01 00:00:00",
            "eventinfo":["pytest1", "pytest2"]
        }
        json_str = json.dumps(json_data)


        response = client.post('/oase_web/event/event/eventsrequest', {'json_str':json_str})
        resp_content = json.loads(response.content.decode('utf-8'))


        assert response.status_code == 200
        assert resp_content['result'] == False

        self.del_test_data()


    @pytest.mark.django_db
    def test_ng_err_reqtype(self):
        """
        種別不明なリクエスト
        ※ 異常系(リクエスト種別不明)
        """

        client = Client()
        self.del_test_data()
        self.set_test_data()

        json_data = {
            "decisiontable":"pytest_name",
            "requesttype":"9999",
            "eventdatetime":"2020-01-01 00:00:00",
            "eventinfo":["pytest1", "pytest2"]
        }
        json_str = json.dumps(json_data)


        response = client.post('/oase_web/event/event/eventsrequest', data=json_str, content_type='application/json')
        resp_content = json.loads(response.content.decode('utf-8'))


        assert response.status_code == 200
        assert resp_content['result'] == False

        self.del_test_data()



