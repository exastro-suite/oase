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
  エージェントドライバ 実行処理


"""


import pytest
import os
import django
import configparser
import datetime
import traceback
import pytz
from django.db import transaction

from libs.commonlibs.define import *
from libs.webcommonlibs.events_request import EventsRequestCommon
from web_app.models.models import EventsRequest

oase_root_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '../..')
os.environ['OASE_ROOT_DIR'] = oase_root_dir
os.environ['RUN_INTERVAL'] = '10'
os.environ['PYTHON_MODULE'] = '/usr/bin/python3'
os.environ['LOG_LEVEL'] = "NORMAL"


################################################
# テスト用DB操作
################################################
def set_data_replace_reserv_var():
    """
    置換処理のテストに必要なデータをDBに登録
    """

    now = datetime.datetime.now(pytz.timezone('UTC'))

    trace_id             = EventsRequestCommon.generate_trace_id(now)
    rhdm_response_action = None
    action_history       = None

    try:
        with transaction.atomic():

            # イベントリクエスト
            events_request = EventsRequest(
                trace_id               = trace_id,
                request_type_id        = 1,
                rule_type_id           = 1,
                request_reception_time = now,
                request_user           = 'pytest_user',
                request_server         = 'pytest_server',
                event_to_time          = now,
                event_info             = '{"EVENT_INFO":["置換テスト"]}',
                status                 = '1',
                status_update_id       = 'pytest_id',
                retry_cnt              = 0,
                last_update_timestamp  = now,
                last_update_user       = 'administrator'
            )
            events_request.save(force_insert=True)

    except Exception as e:
        print(e)

    return events_request


@pytest.mark.django_db
def test_agent(django_db_setup_with_system_dmsettings):
    """
    置換処理テスト
    """
    from backyards.agent_driver import oase_agent as ag
    classAgent = ag.Agent()

    # テストデータ作成
    events_request  = set_data_replace_reserv_var()
    conditional_name = ['条件1',]
    act_lists = ['ITA_NAME=ITA176, SYMPHONY_CLASS_ID={{ VAR_条件1 }}, OPERATION_ID={{ VAR_条件2 }}']

    result = classAgent.replace_reserv_var(
        events_request, conditional_name, act_lists)

    # テスト結果判定
    assert 'VAR_条件1' not in result[0] and 'VAR_条件2' in result[0]
