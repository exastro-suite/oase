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
import requests
import json
import datetime
import pytz

from django.db import transaction
from django.conf import settings

from libs.commonlibs.define import *
from unittest.mock import MagicMock, patch
from libs.commonlibs.aes_cipher import AESCipher
from libs.backyardlibs.action_driver.ServiceNow.ServiceNow_core import ServiceNow1Core
from web_app.models.models import EventsRequest, RuleType


def create_servicenow1core():
    """
    ServiceNow1Coreのインスタンスを作成して返す
    """
    TraceID = '1'
    return ServiceNow1Core(TraceID)

def method_dummy_true(*args, **kwargs):
    """正常系用"""
    return True

def method_dummy_false(*args, **kwargs):
    """異常系用"""
    return False

def create_data():
    """
    テストに必要なデータをDBに登録
    """

    events_request = None

    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = '1'

    try:
        with transaction.atomic():

            # ルール種別
            RuleType(
                rule_type_id = 999,
                rule_type_name = 'pytest',
                summary = 'pytest_summary',
                rule_table_name = 'pytest_table',
                generation_limit = 5,
                group_id = 0,
                artifact_id = 'pytest_art',
                container_id_prefix_staging = 'pytest_stg',
                container_id_prefix_product = 'pytest_prd',
                current_container_id_staging = 'pytest_stg999',
                current_container_id_product = 'pytest_prd999',
                label_count = 1,
                unknown_event_notification = 2,
                mail_address = '',
                servicenow_driver_id = 1,
                disuse_flag = '0',
                last_update_timestamp = now,
                last_update_user = 'pytest_user'
            ).save(force_insert=True)

            # イベントリクエスト
            events_request = EventsRequest(
                trace_id=trace_id,
                request_type_id=PRODUCTION,
                rule_type_id=999,
                request_reception_time=now,
                request_user='pytest_user',
                request_server='pytest_server',
                event_to_time=now,
                event_info='{"EVENT_INFO":["1"]}',
                status=RULE_UNMATCH,
                status_update_id='pytest_id',
                retry_cnt=0,
                last_update_timestamp=now,
                last_update_user='administrator'
            )
            events_request.save(force_insert=True)

    except Exception as e:
        print(e)

    return trace_id, events_request


def test_send_post_request_ok(monkeypatch):
    """
    POSTリクエスト送信のテスト
    正常系
    """
    class DummyTrue:
        """正常系用 response.status_codeを置き換えるクラス"""
        status_code = 201

    def post_dummy_true(*args, **kwargs):
        """正常系用 request.postの戻り値"""
        return DummyTrue()

    now = datetime.datetime.now(pytz.timezone('UTC'))

    url = 'https://pytest-host-name:443/test.html'
    user = 'test_user'
    passwd = 'password'
    ary_data = {}
    ary_data['short_description'] = 'OASE Event Notify'
    ary_data['description'] = {
        'trace_id'      : 1,
        'decisiontable' : 'name',
        'eventdatetime' : now,
        'eventinfo'     : ['1'],
    }
    str_para_json_encoded = json.dumps(ary_data, default=str)

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    proxies = {
        'http' : '8080',
        'https': '443',
    }
    core = create_servicenow1core()

    monkeypatch.setattr(requests, 'post', post_dummy_true)
    result = core.send_post_request(url, user, passwd, str_para_json_encoded.encode('utf-8'), headers, proxies)
    assert(result)

def test_send_post_request_ng(monkeypatch):
    """
    POSTリクエスト送信のテスト
    異常系
    """
    class DummyFalse:
        """異常系用 response.status_codeを置き換えるクラス"""
        status_code = 0

    def post_dummy_false(*args, **kwargs):
        """異常系用 request.postの戻り値"""
        return DummyFalse()

    now = datetime.datetime.now(pytz.timezone('UTC'))

    url = 'https://pytest-host-name:443/test.html'
    user = 'test_user'
    passwd = 'password'
    ary_data = {}
    ary_data['short_description'] = 'OASE Event Notify'
    ary_data['description'] = {
        'trace_id'      : 1,
        'decisiontable' : 'name',
        'eventdatetime' : now,
        'eventinfo'     : ['1'],
    }
    str_para_json_encoded = json.dumps(ary_data, default=str)

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    proxies = {
        'http' : '8080',
        'https': '443',
    }
    core = create_servicenow1core()

    monkeypatch.setattr(requests, 'post', post_dummy_false)
    result = core.send_post_request(url, user, passwd, str_para_json_encoded.encode('utf-8'), headers, proxies)
    assert result != 201

@pytest.mark.django_db
def test_create_incident_ok(monkeypatch):
    """
    インシデント管理に追加のテスト
    """
    class DummyData:
        servicenow_driver_id = 1
        protocol = 'localhost'
        hostname = 'test_host'
        port = 443
        proxy = '2222'
        username = 'test_name'
        password = AESCipher(settings.AES_KEY).encrypt('pytest')

    drv = DummyData()
    core = create_servicenow1core()
    trace_id, eve_req = create_data()

    monkeypatch.setattr(ServiceNow1Core, 'send_post_request', method_dummy_true)
    result = core.create_incident(drv)
    assert(result)

@pytest.mark.django_db
def test_create_incident_ng(monkeypatch):
    """
    インシデント管理に追加のテスト
    """
    class DummyData:
        servicenow_driver_id = 1
        protocol = 'localhost'
        hostname = 'test_host'
        port = 443
        proxy = '2222'
        username = 'test_name'
        password = AESCipher(settings.AES_KEY).encrypt('pytest')

    drv = DummyData()
    core = create_servicenow1core()
    trace_id, eve_req = create_data()

    monkeypatch.setattr(ServiceNow1Core, 'send_post_request', method_dummy_false)
    result = core.create_incident(drv)
    assert result == False
