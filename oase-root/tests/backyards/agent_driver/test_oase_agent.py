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
from web_app.models.models import ActionType, DataObject, DriverType, RhdmResponseCorrelation

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
    RhdmResponseCorrelation.objects.filter(last_update_user='pytest').delete()


class DummyDriver:

    def __init__(self):

        self.ruletype = None
        self.request_type_id = None
        self.trace_id = None


class DummyDMController:

    def __init__(self):

        self.driver = None


def _dummy_send(*args, **kwargs):

    pass


def non_dummy(*args, **kwargs):
    return None


def rhdm_dummy(*args, **kwargs):

    STS_REGISTED     = 0
    STS_REGISTABLE   = 1
    STS_NOTACHIEVE   = 2
    STS_ACHIEVED     = 3
    STS_UNACHIEVABLE = 4
    now = datetime.datetime.now(pytz.timezone('UTC'))

    try:
        with transaction.atomic():
            # rhdmコリレーション情報
            #rcnt = RhdmResponseCorrelation.objects.filter(
            #    rule_type_id    = 1,
            #    request_type_id = 1,
            #    rule_name       = 'test_name'
            #).count()
            #
            #if rcnt > 0:
            #    RhdmResponseCorrelation.objects.filter(
            #        rule_type_id    = 1,
            #        request_type_id = 1,
            #        rule_name       = 'test_name'
            #    ).update(
            #        cond_large_group          = 'group02',
            #        cond_large_group_priority = 1,
            #        cond_small_group          = 'group20',
            #        cond_small_group_priority = 1,
            #        cond_count                = 3,
            #        cond_term                 = 100,
            #        current_count             = 1,
            #        start_time                = now,
            #        response_detail_id        = 1,
            #        status                    = STS_REGISTED,
            #        last_update_timestamp     = now,
            #        last_update_user          = 'administrator',
            #    )
            #
            #else:
            #    RhdmResponseCorrelation(
            #        rule_type_id              = 1,
            #        rule_name                 = 'test_name',
            #        request_type_id           = 1,
            #        cond_large_group          = 'group01',
            #        cond_large_group_priority = 1,
            #        cond_small_group          = 'group10',
            #        cond_small_group_priority = 1,
            #        cond_count                = 3,
            #        cond_term                 = 100,
            #        current_count             = 1,
            #        start_time                = now,
            #        response_detail_id        = 1,
            #        status                    = STS_REGISTED,
            #        last_update_timestamp     = now,
            #        last_update_user          = 'administrator',
            #    ).save(force_insert=True)

            RhdmResponseCorrelation(
                rule_type_id              = 1,
                rule_name                 = 'test_name',
                request_type_id           = 1,
                cond_large_group          = 'group01',
                cond_large_group_priority = 1,
                cond_small_group          = 'group10',
                cond_small_group_priority = 1,
                cond_count                = 3,
                cond_term                 = 100,
                current_count             = 1,
                start_time                = now,
                response_detail_id        = 1,
                status                    = STS_REGISTED,
                last_update_timestamp     = now,
                last_update_user          = 'administrator',
                ).save(force_insert=True)

    except Exception as e:
        print(e)


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


################################################
# テスト(コリレーション)
################################################
@pytest.mark.django_db
def test_make_rhdm_response_correlation_ok(django_db_setup_with_system_dmsettings, monkeypatch):
    """
    ルールマッチング結果コリレーション管理に登録するためのデータを作る
    正常系(空)
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
    parameterInfo = []
    preInfo = []
    id = '1'
    rulename = 'test_name'
    cond_count = '1'
    cond_term = '100'
    cond_group1 = 'X'
    cond_priority1 = '1'
    cond_group2 = 'X'
    cond_priority2 = '1'


    acts = {'parameterInfo':parameterInfo,
            'preInfo':preInfo,
            'id':id,
            'ruleName':rulename,
            'condCount':cond_count,
            'condTerm':cond_term,
            'condGroup1':cond_group1,
            'condPriority1':cond_priority1,
            'condGroup2':cond_group2,
            'condPriority2':cond_priority2}
    responseid = 1

    monkeypatch.setattr(classAgent, 'check_group_cond', non_dummy)

    # テスト
    result = True
    try:
        classAgent.make_rhdm_response_correlation(acts, responseid)
    except Exception as e:
        print(traceback.format_exc())
        result = False

    # テスト結果判定
    assert result

    del_test_data()


@pytest.mark.django_db
def test_check_group_cond_ok_digit(django_db_setup_with_system_dmsettings, monkeypatch):
    """
    グループ情報を持つルールのアクション情報をチェック
    正常系(グルーピングなし)
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

    resp_id = 1
    rule_name = 'test name'
    cond_cnt = 1
    cond_term = 100
    group1_name = 'X'
    priority1 = 1
    group2_name = 'X'
    priority2 = 1

    ret = classAgent.check_group_cond(
        resp_id,
        rule_name,
        cond_cnt,
        cond_term,
        group1_name,
        priority1,
        group2_name,
        priority2)
    assert len(ret) == 0

@pytest.mark.django_db
def test_check_group_cond_ok(django_db_setup_with_system_dmsettings, monkeypatch):
    """
    グループ情報を持つルールのアクション情報をチェック
    正常系(グルーピングあり)
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

    resp_id = 1
    rule_name = 'test name'
    cond_cnt = 1
    cond_term = 100
    group1_name = 'group01'
    priority1 = 1
    group2_name = 'group10'
    priority2 = 1

    now = datetime.datetime.now(pytz.timezone('UTC'))

    del_test_data()
    rhdm_dummy()

    # テスト判定
    ret = classAgent.check_group_cond(
        resp_id,
        rule_name,
        cond_cnt,
        cond_term,
        group1_name,
        priority1,
        group2_name,
        priority2)
    assert len(ret) == 9

    del_test_data()

@pytest.mark.django_db
def test_check_rhdm_response_correlation_ok(django_db_setup_with_system_dmsettings, monkeypatch):
    """
    マッチング結果コリレーション管理の状態をチェック
    正常系()
    """
    from backyards.agent_driver import oase_agent as ag
    classDrv = DummyDriver()
    classDMCtrl = DummyDMController()

    # テストデータ作成
    del_test_data()
    set_data_smtp()
    classDrv.ruletype = set_data_ruletype()
    classDMCtrl.driver = classDrv

    now = datetime.datetime.now(pytz.timezone('UTC'))

    rhdm_dummy()

    # テスト
    result = True
    try:
        ag.check_rhdm_response_correlation(now)
    except Exception as e:
        print(traceback.format_exc())
        result = False

    # テスト結果判定
    assert result

    del_test_data()
