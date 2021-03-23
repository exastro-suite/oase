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
  ServiceNow通知テスト
"""

import pytest
import os
import datetime
import pytz

from importlib import import_module
from django.db import transaction
from django.conf import settings

from libs.commonlibs.define import *
from libs.commonlibs.aes_cipher import AESCipher
from libs.webcommonlibs.events_request import EventsRequestCommon
from web_app.models.models import RuleType, EventsRequest

from backyards.servicenow_notification.ServiceNow_notification import *


oase_root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..')
os.environ['OASE_ROOT_DIR'] = oase_root_dir
os.environ['RUN_INTERVAL']  = '10'
os.environ['PYTHON_MODULE'] = '/usr/bin/python3'
os.environ['LOG_LEVEL']     = "TRACE"
os.environ['LOG_DIR']       = oase_root_dir + "/logs/backyardlogs/oase_action"


################################################
# テストデータ
################################################
def create_data():
    """
    テストに必要なデータをDBに登録
    """

    events_request = None

    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)

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
                disuse_flag = '0',
                last_update_timestamp = now,
                last_update_user = 'pytest_user'
            ).save(force_insert=True)

            # イベントリクエスト
            events_request = EventsRequest(
                trace_id=trace_id,
                request_type_id=PRODUCTION,
                rule_type_id=1,
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


def delete_data():
    """
    テストで使用したデータの削除
    テーブル初期化
    """
    module = import_module('web_app.models.ServiceNow_models')
    ServiceNowDriver = getattr(module, 'ServiceNowDriver')

    ServiceNowDriver.objects.all().delete()
    EventsRequest.objects.all().delete()
    RuleType.objects.all().delete()


@pytest.fixture()
def setup_data():
    """
    テストデータのリセット
    """

    delete_data()

    now = datetime.datetime.now(pytz.timezone('UTC'))
    module = import_module('web_app.models.ServiceNow_models')
    ServiceNowDriver = getattr(module, 'ServiceNowDriver')

    encryptpassword = AESCipher(settings.AES_KEY).encrypt('pytest')
    ServiceNowDriver(
        servicenow_driver_id=1,
        servicenow_disp_name='ServiceNow0001',
        hostname='pytest-host-name1',
        protocol='http',
        port='80',
        username='pytest',
        password=encryptpassword,
        count=0,
        proxy='',
        last_update_user='pytest',
        last_update_timestamp=now,
    ).save(force_insert=True)

    yield

    delete_data()


################################################
# テスト(イベントリクエスト更新)
################################################
@pytest.mark.django_db
def test_events_request_update_ok(setup_data):
    """
    正常系
    """

    # テストデータ作成
    trace_id, eve_req = create_data()

    # テスト
    result = events_request_update(
        eve_req.request_id,
        REQUEST_HISTORY_STATUS.RULE_ALREADY_LINKED,
        'pytest_user'
    )

    assert result == True


@pytest.mark.django_db
def test_events_request_update_ng(setup_data):
    """
    異常系
    """

    # テストデータ作成
    trace_id, eve_req = create_data()

    # テスト
    result = events_request_update(
        'pytest_err',
        REQUEST_HISTORY_STATUS.RULE_ALREADY_LINKED,
        'pytest_user'
    )

    assert result == False


