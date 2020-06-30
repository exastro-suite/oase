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

common.pyのテスト

"""
from libs.webcommonlibs.events_request import EventsRequestCommon


def test_generate_trace_id_ok():
    """
    トレースID生成テスト
    ※正常系
    """

    trace_id = EventsRequestCommon.generate_trace_id()

    assert len(trace_id) == 55


def test_check_events_request_key_ok():
    """
    トレースID生成テスト
    ※正常系
    """

    req = {
        'decisiontable' : 'pytest_table',
        'requesttype' : 0,
        'eventdatetime' : '2020-01-01 00:00:00',
        'eventinfo' : []
    }

    result = EventsRequestCommon.check_events_request_key(req)

    assert result == EventsRequestCommon.REQUEST_OK


def test_check_events_request_key_ng_keyerr_ruletype():
    """
    トレースID生成テスト
    ※異常系(キーなし'decisiontable')
    """

    req = {
        'requesttype' : 0,
        'eventdatetime' : '2020-01-01 00:00:00',
        'eventinfo' : []
    }

    result = EventsRequestCommon.check_events_request_key(req)

    assert result == EventsRequestCommon.REQUEST_ERR_RULETYPE_KEY


def test_check_events_request_key_ng_keyerr_reqtype():
    """
    トレースID生成テスト
    ※異常系(キーなし'requesttype')
    """

    req = {
        'decisiontable' : 'pytest_table',
        'eventdatetime' : '2020-01-01 00:00:00',
        'eventinfo' : []
    }

    result = EventsRequestCommon.check_events_request_key(req)

    assert result == EventsRequestCommon.REQUEST_ERR_REQTYPE_KEY


def test_check_events_request_key_ng_keyerr_evtime():
    """
    トレースID生成テスト
    ※異常系(キーなし'eventdatetime')
    """

    req = {
        'decisiontable' : 'pytest_table',
        'requesttype' : 0,
        'eventinfo' : []
    }

    result = EventsRequestCommon.check_events_request_key(req)

    assert result == EventsRequestCommon.REQUEST_ERR_DATETIME_KEY


def test_check_events_request_key_ng_keyerr_evinfo():
    """
    トレースID生成テスト
    ※異常系(キーなし'eventinfo')
    """

    req = {
        'decisiontable' : 'pytest_table',
        'requesttype' : 0,
        'eventdatetime' : '2020-01-01 00:00:00',
    }

    result = EventsRequestCommon.check_events_request_key(req)

    assert result == EventsRequestCommon.REQUEST_ERR_EVINFO_KEY


def test_check_events_request_len_ok():
    """
    イベント情報チェック
    ※正常系
    """

    req = {
        'eventinfo' : ['pytest1', 'pytest2']
    }

    result = EventsRequestCommon.check_events_request_len(req, 2)

    assert result == EventsRequestCommon.REQUEST_OK


def test_check_events_request_len_ng_lenzero():
    """
    イベント情報チェック
    ※異常系(データなし)
    """

    req = {
        'eventinfo' : []
    }

    result = EventsRequestCommon.check_events_request_len(req, 0)

    assert result == EventsRequestCommon.REQUEST_ERR_EVINFO_LENGTH


def test_check_events_request_len_ng_notlist():
    """
    イベント情報チェック
    ※異常系(データなし)
    """

    req = {
        'eventinfo' : 'pytest1'
    }

    result = EventsRequestCommon.check_events_request_len(req, 1)

    assert result == EventsRequestCommon.REQUEST_ERR_EVINFO_TYPE


def test_check_events_request_len_ng_errlen():
    """
    イベント情報チェック
    ※異常系(データなし)
    """

    req = {
        'eventinfo' : ['pytest1', 'pytest2']
    }

    result = EventsRequestCommon.check_events_request_len(req, 1)

    assert result == EventsRequestCommon.REQUEST_ERR_EVINFO_LENGTH


