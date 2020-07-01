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
from libs.webcommonlibs.oase_mail import OASEMailSMTP
from web_app.models.models import EventsRequest, RuleType, System

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


def set_data_ruletype(notify_type='1', maddr='pytest@example.com'):
    """
    テストデータの作成
    """

    # ルール種別
    ruletype = RuleType(
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
        unknown_event_notification = notify_type,
        mail_address = maddr,
        disuse_flag = '0',
        last_update_timestamp = datetime.datetime(2020, 6, 4, 12, 0, 0, tzinfo=datetime.timezone.utc),
        last_update_user = 'pytest'
    )

    ruletype.save(force_insert=True)

    return ruletype


def set_data_smtp():
    """
    テストデータの作成
    """

    # メール送信
    rcnt = System.objects.filter(config_id='OASE_MAIL_SMTP').count()
    if rcnt <= 0:
        System(
            item_id = 9999,
            config_name = 'OASEメールSMTP',
            category = 'OASE_MAIL',
            config_id = 'OASE_MAIL_SMTP',
            value = '{}',
            maintenance_flag = 0,
            last_update_timestamp = datetime.datetime(2020, 6, 4, 12, 0, 0, tzinfo=datetime.timezone.utc),
            last_update_user = 'pytest'
        ).save(force_insert=True)


def del_test_data():
    """
    テストデータの削除
    """

    RuleType.objects.filter(last_update_user='pytest').delete()
    System.objects.filter(last_update_user='pytest').delete()


class DummyDriver:

    def __init__(self):

        self.ruletype = None


class DummyDMController:

    def __init__(self):

        self.driver = None


def _dummy_send(*args, **kwargs):

    pass


################################################
# テスト
################################################
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


################################################
# テスト(未知事象通知)
################################################
@pytest.mark.django_db
def test_notify_unknown_event_ok(django_db_setup_with_system_dmsettings, monkeypatch):
    """
    未知事象通知テスト
    正常系
    """

    from backyards.agent_driver import oase_agent as ag
    classAgent = ag.Agent()
    classDrv = DummyDriver()
    classDMCtrl = DummyDMController()

    # テストデータ作成
    del_test_data()
    set_data_smtp()
    classDrv.ruletype = set_data_ruletype()
    classDMCtrl.driver = classDrv
    classAgent.dmctl = classDMCtrl

    notify_param = {
        'decision_table_name' : classDrv.ruletype.rule_type_name,
        'event_to_time' : 'ett_2020-01-01 00:00:00',
        'request_reception_time' : 'rrt_2020-01-01 00:00:00',
        'event_info' : 'EventInfo_pytest',
        'trace_id' : 'TOS_pytest_unknown_event',
    }

    monkeypatch.setattr(OASEMailSMTP, 'send_mail', _dummy_send)

    # テスト
    result = True
    try:
        classAgent._notify_unknown_event(
            1,
            notify_param
        )

    except Exception as e:
        print(traceback.format_exc())
        result = False

    # テスト結果判定
    assert result

    del_test_data()


@pytest.mark.django_db
def test_notify_unknown_event_ok_reqtype(django_db_setup_with_system_dmsettings, monkeypatch):
    """
    未知事象通知テスト
    準正常系(非プロダクション)
    """

    from backyards.agent_driver import oase_agent as ag
    classAgent = ag.Agent()
    classDrv = DummyDriver()
    classDMCtrl = DummyDMController()

    # テストデータ作成
    del_test_data()
    set_data_smtp()
    classDrv.ruletype = set_data_ruletype()
    classDMCtrl.driver = classDrv
    classAgent.dmctl = classDMCtrl

    notify_param = {
        'decision_table_name' : classDrv.ruletype.rule_type_name,
        'event_to_time' : 'ett_2020-01-01 00:00:00',
        'request_reception_time' : 'rrt_2020-01-01 00:00:00',
        'event_info' : 'EventInfo_pytest',
        'trace_id' : 'TOS_pytest_unknown_event',
    }

    monkeypatch.setattr(OASEMailSMTP, 'send_mail', _dummy_send)

    # テスト
    result = True
    try:
        classAgent._notify_unknown_event(
            2,
            notify_param
        )

    except Exception as e:
        print(traceback.format_exc())
        result = False

    # テスト結果判定
    assert result

    del_test_data()


@pytest.mark.django_db
def test_notify_unknown_event_ok_notifytype(django_db_setup_with_system_dmsettings, monkeypatch):
    """
    未知事象通知テスト
    準正常系(通知種別対象外)
    """

    from backyards.agent_driver import oase_agent as ag
    classAgent = ag.Agent()
    classDrv = DummyDriver()
    classDMCtrl = DummyDMController()

    # テストデータ作成
    del_test_data()
    set_data_smtp()
    classDrv.ruletype = set_data_ruletype(notify_type='9')
    classDMCtrl.driver = classDrv
    classAgent.dmctl = classDMCtrl

    notify_param = {
        'decision_table_name' : classDrv.ruletype.rule_type_name,
        'event_to_time' : 'ett_2020-01-01 00:00:00',
        'request_reception_time' : 'rrt_2020-01-01 00:00:00',
        'event_info' : 'EventInfo_pytest',
        'trace_id' : 'TOS_pytest_unknown_event',
    }

    monkeypatch.setattr(OASEMailSMTP, 'send_mail', _dummy_send)

    # テスト
    result = True
    try:
        classAgent._notify_unknown_event(
            1,
            notify_param
        )

    except Exception as e:
        print(traceback.format_exc())
        result = False

    # テスト結果判定
    assert result

    del_test_data()


@pytest.mark.django_db
def test_notify_unknown_event_ok_noaddr(django_db_setup_with_system_dmsettings, monkeypatch):
    """
    未知事象通知テスト
    準正常系(通知先なし)
    """

    from backyards.agent_driver import oase_agent as ag
    classAgent = ag.Agent()
    classDrv = DummyDriver()
    classDMCtrl = DummyDMController()

    # テストデータ作成
    del_test_data()
    set_data_smtp()
    classDrv.ruletype = set_data_ruletype(maddr='')
    classDMCtrl.driver = classDrv
    classAgent.dmctl = classDMCtrl

    notify_param = {
        'decision_table_name' : classDrv.ruletype.rule_type_name,
        'event_to_time' : 'ett_2020-01-01 00:00:00',
        'request_reception_time' : 'rrt_2020-01-01 00:00:00',
        'event_info' : 'EventInfo_pytest',
        'trace_id' : 'TOS_pytest_unknown_event',
    }

    monkeypatch.setattr(OASEMailSMTP, 'send_mail', _dummy_send)

    # テスト
    result = True
    try:
        classAgent._notify_unknown_event(
            1,
            notify_param
        )

    except Exception as e:
        print(traceback.format_exc())
        result = False

    # テスト結果判定
    assert result

    del_test_data()


@pytest.mark.django_db
def test_notify_unknown_event_ng_noparam(django_db_setup_with_system_dmsettings, monkeypatch):
    """
    未知事象通知テスト
    異常系
    """

    from backyards.agent_driver import oase_agent as ag
    classAgent = ag.Agent()
    classDrv = DummyDriver()
    classDMCtrl = DummyDMController()

    # テストデータ作成
    del_test_data()
    set_data_smtp()
    classDrv.ruletype = set_data_ruletype()
    classDMCtrl.driver = classDrv
    classAgent.dmctl = classDMCtrl

    notify_param = {}

    monkeypatch.setattr(OASEMailSMTP, 'send_mail', _dummy_send)

    # テスト
    result = True
    try:
        classAgent._notify_unknown_event(
            1,
            notify_param
        )

    except Exception as e:
        print(traceback.format_exc())
        result = False

    # テスト結果判定
    assert result

    del_test_data()


