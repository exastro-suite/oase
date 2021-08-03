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
  DashBoard画面
"""


import pytest
import datetime
import pytz
import json

from web_app.models.models import EventsRequest
from web_app.views.top import dashboard 


################################################################
# テストデータ(既知ランキング、daily、円グラフ)
################################################################
@pytest.fixture()
def widget_data1():

    now = datetime.datetime.now(pytz.timezone('UTC'))

    ############################################
    # ランキング1位
    EventsRequest(
        request_id             = 9999,
        trace_id               = 'TOS_pytest9999',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = 'aaa',
        status                 = 3,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    EventsRequest(
        request_id             = 9998,
        trace_id               = 'TOS_pytest9998',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = 'aaa',
        status                 = 3,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    EventsRequest(
        request_id             = 9997,
        trace_id               = 'TOS_pytest9997',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = 'aaa',
        status                 = 3,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    EventsRequest(
        request_id             = 9996,
        trace_id               = 'TOS_pytest9996',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = 'aaa',
        status                 = 3,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    ############################################
    # ランキング2位
    EventsRequest(
        request_id             = 9995,
        trace_id               = 'TOS_pytest9995',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = 'bbb',
        status                 = 3,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    EventsRequest(
        request_id             = 9994,
        trace_id               = 'TOS_pytest9994',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = 'bbb',
        status                 = 3,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    EventsRequest(
        request_id             = 9993,
        trace_id               = 'TOS_pytest9993',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = 'bbb',
        status                 = 3,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    ############################################
    # ランキング3位
    EventsRequest(
        request_id             = 9992,
        trace_id               = 'TOS_pytest9992',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = 'ccc',
        status                 = 3,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    EventsRequest(
        request_id             = 9991,
        trace_id               = 'TOS_pytest9991',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = 'ccc',
        status                 = 3,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    ############################################
    # その他
    EventsRequest(
        request_id             = 9990,
        trace_id               = 'TOS_pytest9990',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = 'xyz',
        status                 = 3,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    yield

    EventsRequest.objects.filter(last_update_user='pytest_user').delete()


################################################################
# テスト(既知ランキング、daily、円グラフ)
################################################################
@pytest.mark.django_db
class TestPieGraphDateMatchgData(object):

    @pytest.mark.usefixtures('widget_data1')
    def test_ok(self):
        """
        正常系
        """

        cls_widget = dashboard.WidgetData()
        data = cls_widget.pie_graph_date_match_data(3, **{'language':'JA', 'req_rule_ids':[999,], 'count':3})

        assert len(data['data']) == 4
        assert 'aaa'    in data['data'] and data['data']['aaa'][0]    == 'known1'
        assert 'bbb'    in data['data'] and data['data']['bbb'][0]    == 'known2'
        assert 'ccc'    in data['data'] and data['data']['ccc'][0]    == 'known3'
        assert 'その他' in data['data'] and data['data']['その他'][0] == 'known6'


################################################################
# テストデータ(未知ランキング、daily、円グラフ)
################################################################
@pytest.fixture()
def widget_data2():

    now = datetime.datetime.now(pytz.timezone('UTC'))

    ############################################
    # ランキング1位
    EventsRequest(
        request_id             = 9999,
        trace_id               = 'TOS_pytest9999',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = 'aaa',
        status                 = 1000,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    EventsRequest(
        request_id             = 9998,
        trace_id               = 'TOS_pytest9998',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = 'aaa',
        status                 = 1000,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    EventsRequest(
        request_id             = 9997,
        trace_id               = 'TOS_pytest9997',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = 'aaa',
        status                 = 1000,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    EventsRequest(
        request_id             = 9996,
        trace_id               = 'TOS_pytest9996',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = 'aaa',
        status                 = 1000,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    ############################################
    # ランキング2位
    EventsRequest(
        request_id             = 9995,
        trace_id               = 'TOS_pytest9995',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = 'bbb',
        status                 = 1000,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    EventsRequest(
        request_id             = 9994,
        trace_id               = 'TOS_pytest9994',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = 'bbb',
        status                 = 1000,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    EventsRequest(
        request_id             = 9993,
        trace_id               = 'TOS_pytest9993',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = 'bbb',
        status                 = 1000,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    ############################################
    # ランキング3位
    EventsRequest(
        request_id             = 9992,
        trace_id               = 'TOS_pytest9992',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = 'ccc',
        status                 = 1000,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    EventsRequest(
        request_id             = 9991,
        trace_id               = 'TOS_pytest9991',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = 'ccc',
        status                 = 1000,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    ############################################
    # その他
    EventsRequest(
        request_id             = 9990,
        trace_id               = 'TOS_pytest9990',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = 'xyz',
        status                 = 1000,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    yield

    EventsRequest.objects.filter(last_update_user='pytest_user').delete()


################################################################
# テスト(未知ランキング、daily、円グラフ)
################################################################
@pytest.mark.django_db
class TestPieGraphDateUnmatchingData(object):

    @pytest.mark.usefixtures('widget_data2')
    def test_ok(self):
        """
        正常系
        """

        cls_widget = dashboard.WidgetData()
        data = cls_widget.pie_graph_date_unmatch_data(3, **{'language':'JA', 'req_rule_ids':[999,], 'count':3})

        assert len(data['data']) == 4
        assert 'aaa'    in data['data'] and data['data']['aaa'][0]    == 'unknown1'
        assert 'bbb'    in data['data'] and data['data']['bbb'][0]    == 'unknown2'
        assert 'ccc'    in data['data'] and data['data']['ccc'][0]    == 'unknown3'
        assert 'その他' in data['data'] and data['data']['その他'][0] == 'unknown6'


################################################################
# テストデータ(既知/未知、daily、円グラフ)
################################################################
@pytest.fixture()
def widget_data3():

    now = datetime.datetime.now(pytz.timezone('UTC'))

    ############################################
    # 取得対象データ
    ############################################
    # 既知
    EventsRequest(
        request_id             = 9999,
        trace_id               = 'TOS_pytest9999',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = '',
        status                 = 3,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    EventsRequest(
        request_id             = 9998,
        trace_id               = 'TOS_pytest9998',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = '',
        status                 = 4,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    ############################################
    # 未知
    EventsRequest(
        request_id             = 9997,
        trace_id               = 'TOS_pytest9997',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = '',
        status                 = 1000,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)


    ############################################
    # 対象外データ
    ############################################
    # 対象外ステータス
    EventsRequest(
        request_id             = 9996,
        trace_id               = 'TOS_pytest9996',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = '',
        status                 = 5,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    # 対象外リクエスト種別
    EventsRequest(
        request_id             = 9995,
        trace_id               = 'TOS_pytest9995',
        request_type_id        = 2,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = '',
        status                 = 3,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    # 対象外ルール
    EventsRequest(
        request_id             = 9994,
        trace_id               = 'TOS_pytest9994',
        request_type_id        = 1,
        rule_type_id           = 998,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now,
        event_info             = '',
        status                 = 3,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    # 対象外日時
    EventsRequest(
        request_id             = 9993,
        trace_id               = 'TOS_pytest9993',
        request_type_id        = 1,
        rule_type_id           = 998,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = now - datetime.timedelta(days=1),
        event_info             = '',
        status                 = 3,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    yield

    EventsRequest.objects.filter(last_update_user='pytest_user').delete()


################################################################
# テスト(既知/未知、daily、円グラフ)
################################################################
@pytest.mark.django_db
class TestPieGraphDateMatchingData(object):

    @pytest.mark.usefixtures('widget_data3')
    def test_ok(self):
        """
        正常系
        """

        cls_widget = dashboard.WidgetData()
        data = cls_widget.pie_graph_date_matching_data(3, **{'language':'JA', 'req_rule_ids':[999,]})

        assert len(data['data']) == 2
        assert data['data']['Match'][1]   == 2
        assert data['data']['Unmatch'][1] == 1


################################################################
# テストデータ(既知/未知、hourly、棒グラフ)
################################################################
@pytest.fixture()
def widget_data21():

    now = datetime.datetime.now(pytz.timezone('UTC'))
    today = datetime.datetime(now.year, now.month, now.day, 12, 0, 0)
    yesterday = pytz.timezone('UTC').localize(today - datetime.timedelta(days=1))

    ############################################
    # 取得対象データ
    ############################################
    # 既知
    EventsRequest(
        request_id             = 9999,
        trace_id               = 'TOS_pytest9999',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = yesterday,
        event_info             = '',
        status                 = 3,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    EventsRequest(
        request_id             = 9998,
        trace_id               = 'TOS_pytest9998',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = yesterday,
        event_info             = '',
        status                 = 4,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    ############################################
    # 未知
    EventsRequest(
        request_id             = 9997,
        trace_id               = 'TOS_pytest9997',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = yesterday,
        event_info             = '',
        status                 = 1000,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)


    ############################################
    # 対象外データ
    ############################################
    # 対象外ステータス
    EventsRequest(
        request_id             = 9996,
        trace_id               = 'TOS_pytest9996',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = yesterday,
        event_info             = '',
        status                 = 5,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    # 対象外リクエスト種別
    EventsRequest(
        request_id             = 9995,
        trace_id               = 'TOS_pytest9995',
        request_type_id        = 2,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = yesterday,
        event_info             = '',
        status                 = 3,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    # 対象外ルール
    EventsRequest(
        request_id             = 9994,
        trace_id               = 'TOS_pytest9994',
        request_type_id        = 1,
        rule_type_id           = 998,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = yesterday,
        event_info             = '',
        status                 = 3,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    # 対象外日時
    EventsRequest(
        request_id             = 9993,
        trace_id               = 'TOS_pytest9993',
        request_type_id        = 1,
        rule_type_id           = 998,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = yesterday - datetime.timedelta(days=31),
        event_info             = '',
        status                 = 3,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    yield

    EventsRequest.objects.filter(last_update_user='pytest_user').delete()


################################################################
# テスト(既知/未知、daily、円グラフ)
################################################################
@pytest.mark.django_db
class TestStackedGraphHourlyMatchingData(object):

    @pytest.mark.usefixtures('widget_data21')
    def test_ok(self):
        """
        正常系
        """

        param_info = {
            'language'     : 'JA',
            'date_range'   : 30,
            'req_rule_ids' : [999,],
        }

        cls_widget = dashboard.WidgetData()
        data = cls_widget.stacked_graph_hourly_matching_data(21, **param_info)

        assert len(data['data']) == 24
        for d in data['data']:
            if d[1] == '12':
                assert d[2] == 2
                assert d[3] == 1

            else:
                assert d[2] == 0
                assert d[3] == 0


################################################################
# テストデータ(既知/未知、monthly、棒グラフ)
################################################################
@pytest.fixture()
def widget_data22():

    now = datetime.datetime.now(pytz.timezone('UTC'))
    today = datetime.datetime(now.year, now.month, 15, 12, 0, 0)
    last_month = pytz.timezone('UTC').localize(today - datetime.timedelta(days=30))

    ############################################
    # 取得対象データ
    ############################################
    # 既知
    EventsRequest(
        request_id             = 9999,
        trace_id               = 'TOS_pytest9999',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = last_month,
        event_info             = '',
        status                 = 3,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    EventsRequest(
        request_id             = 9998,
        trace_id               = 'TOS_pytest9998',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = last_month,
        event_info             = '',
        status                 = 4,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    ############################################
    # 未知
    EventsRequest(
        request_id             = 9997,
        trace_id               = 'TOS_pytest9997',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = last_month,
        event_info             = '',
        status                 = 1000,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)


    ############################################
    # 対象外データ
    ############################################
    # 対象外ステータス
    EventsRequest(
        request_id             = 9996,
        trace_id               = 'TOS_pytest9996',
        request_type_id        = 1,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = last_month,
        event_info             = '',
        status                 = 5,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    # 対象外リクエスト種別
    EventsRequest(
        request_id             = 9995,
        trace_id               = 'TOS_pytest9995',
        request_type_id        = 2,
        rule_type_id           = 999,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = last_month,
        event_info             = '',
        status                 = 3,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    # 対象外ルール
    EventsRequest(
        request_id             = 9994,
        trace_id               = 'TOS_pytest9994',
        request_type_id        = 1,
        rule_type_id           = 998,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = last_month,
        event_info             = '',
        status                 = 3,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    # 対象外日時
    EventsRequest(
        request_id             = 9993,
        trace_id               = 'TOS_pytest9993',
        request_type_id        = 1,
        rule_type_id           = 998,
        request_reception_time = now,
        request_user           = 'pytest_user',
        request_server         = 'pytest_server',
        event_to_time          = last_month - datetime.timedelta(days=400),
        event_info             = '',
        status                 = 3,
        status_update_id       = 'pytest_user',
        retry_cnt              = 999,
        last_update_timestamp  = now,
        last_update_user       = 'pytest_user'
    ).save(force_insert=True)

    yield

    EventsRequest.objects.filter(last_update_user='pytest_user').delete()


################################################################
# テスト(既知/未知、daily、円グラフ)
################################################################
@pytest.mark.django_db
class TestStackedGraphMonthlyMatchingData(object):

    @pytest.mark.usefixtures('widget_data22')
    def test_ok(self):
        """
        正常系
        """

        param_info = {
            'language'     : 'JA',
            'date_range'   : 30,
            'req_rule_ids' : [999,],
        }

        cls_widget = dashboard.WidgetData()
        data = cls_widget.stacked_graph_monthly_matching_data(22, **param_info)

        cnt_known = 0
        cnt_unknown = 0
        assert len(data['data']) == 12
        for d in data['data']:
            cnt_known += d[2]
            cnt_unknown += d[3]

        assert cnt_known == 2
        assert cnt_unknown == 1


