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

oase_mail.pyのテスト

"""

import pytest

from libs.webcommonlibs.oase_mail import *


@pytest.mark.django_db
def test_unknown_notify_ok(django_db_setup):
    """
    未知事象通知テスト
    ※正常系
    """

    addr_to = 'pytest@example.com'
    inquiry_url = ''
    login_url = ''
    notify_param = {
        'decision_table_name' : 'DecisionTable_pytest',
        'event_to_time' : '2020-01-01 00:00:00',
        'request_reception_time' : '2020-01-01 00:00:00',
        'event_info' : {'EVENTINFO':['pytest1', 'pytest2']},
        'trace_id' : 'TOS_dtname_pytest',
    }

    cls_mail = OASEMailUnknownEventNotify(addr_to, notify_param, inquiry_url, login_url)

    assert '未知事象通知' in cls_mail.subject
    assert notify_param['decision_table_name'] in cls_mail.mail_text


@pytest.mark.django_db
def test_unknown_notify_ok_noparam(django_db_setup):
    """
    未知事象通知テスト
    ※準正常系(パラメーターなし)
    """

    addr_to = 'pytest@example.com'
    inquiry_url = ''
    login_url = ''
    notify_param = {}

    cls_mail = OASEMailUnknownEventNotify(addr_to, notify_param, inquiry_url, login_url)

    assert '未知事象通知' in cls_mail.subject
    assert 'decision_table_name' in notify_param


