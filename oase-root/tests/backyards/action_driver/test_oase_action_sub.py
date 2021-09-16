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
  アクションドライバ アクション実行処理（子プロセス）
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
from web_app.models.models import ActionType, EventsRequest, RhdmResponseAction, ActionHistory


oase_root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..')
os.environ['OASE_ROOT_DIR'] = oase_root_dir
os.environ['RUN_INTERVAL']  = '10'
os.environ['PYTHON_MODULE'] = '/usr/bin/python3'
os.environ['LOG_LEVEL']     = "TRACE"
os.environ['LOG_DIR']       = oase_root_dir + "/logs/backyardlogs/oase_action"


from backyards.action_driver.oase_action_sub import ActionDriverSubModules
from backyards.action_driver import oase_action_sub as chld_proc

################################################
# テスト用DB操作(exastro_request用)
################################################
def set_data_exastro_request():
    """
    Exastroシリーズの実行ステータス取得のテストに必要なデータをDBに登録
    """

    now = datetime.datetime.now(pytz.timezone('UTC'))

    try:
        with transaction.atomic():

            # アクション履歴
            ActionHistory(
                action_history_id=999,
                response_id=999,
                trace_id='TOS_pytest999',
                rule_type_id=999,
                rule_type_name='pytest_ruletable',
                rule_name='pytest',
                execution_order=1,
                action_start_time=now,
                action_type_id=1,
                status=2005,
                status_detail=0,
                status_update_id='pytest_id',
                retry_flag=False,
                retry_status=None,
                retry_status_detail=None,
                action_retry_count=0,
                last_act_user='administrator',
                last_update_timestamp=now,
                last_update_user='pytest_user',
            ).save(force_insert=True)

            # ルールマッチング情報
            RhdmResponseAction(
                response_detail_id = 999,
                response_id = 999,
                rule_name = 'pytest_rule_name',
                execution_order = 1,
                action_type_id = 1,
                action_parameter_info = '',
                action_pre_info = '',
                action_retry_interval = 1,
                action_retry_count = 1,
                action_stop_interval = 0,
                action_stop_count = 0,
                last_update_timestamp = now,
                last_update_user = 'pytest_user'
            ).save(force_insert=True)

            RhdmResponseAction(
                response_detail_id = 998,
                response_id = 999,
                rule_name = 'pytest_rule_name',
                execution_order = 2,
                action_type_id = 1,
                action_parameter_info = '',
                action_pre_info = '',
                action_retry_interval = 1,
                action_retry_count = 1,
                action_stop_interval = 0,
                action_stop_count = 0,
                last_update_timestamp = now,
                last_update_user = 'pytest_user'
            ).save(force_insert=True)


    except Exception as e:
        print(e)

def set_data_exastro_request_ng():
    """
    Exastroシリーズの実行ステータス取得のテストに必要なデータをDBに登録
    異常系データ
    """

    now = datetime.datetime.now(pytz.timezone('UTC'))

    try:
        with transaction.atomic():

            # アクション履歴
            ActionHistory(
                action_history_id=999,
                response_id=998,
                trace_id='TOS_pytest999',
                rule_type_id=999,
                rule_type_name='pytest_ruletable',
                rule_name='pytest',
                execution_order=1,
                action_start_time=now,
                action_type_id=1,
                status=2005,
                status_detail=0,
                status_update_id='pytest_id',
                retry_flag=False,
                retry_status=None,
                retry_status_detail=None,
                action_retry_count=0,
                last_act_user='administrator',
                last_update_timestamp=now,
                last_update_user='pytest_user',
            ).save(force_insert=True)

            # ルールマッチング情報
            RhdmResponseAction(
                response_detail_id = 999,
                response_id = 999,
                rule_name = 'pytest_rule_name',
                execution_order = 1,
                action_type_id = 1,
                action_parameter_info = '',
                action_pre_info = '',
                action_retry_interval = 1,
                action_retry_count = 1,
                action_stop_interval = 0,
                action_stop_count = 0,
                last_update_timestamp = now,
                last_update_user = 'pytest_user'
            ).save(force_insert=True)

    except Exception as e:
        print(e)


################################################
# テスト用DB操作(抑止回数/抑止間隔)
################################################
def set_data_action_stop(action_stop_interval, action_stop_count, exec_order):
    """
    抑止回数/抑止間隔のテストに必要なデータをDBに登録
    """

    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    rhdm_response_action = None
    action_history = None

    try:
        with transaction.atomic():

            # アクション種別
            action_type = ActionType(
                driver_type_id=1,
                disuse_flag='0',
                last_update_timestamp=now,
                last_update_user='administrator'
            )
            action_type.save(force_insert=True)

            # イベントリクエスト
            events_request = EventsRequest(
                trace_id=trace_id,
                request_type_id=1,
                rule_type_id=1,
                request_reception_time=now,
                request_user='pytest_user',
                request_server='pytest_server',
                event_to_time=now,
                event_info='{"EVENT_INFO":["1"]}',
                status='3',
                status_update_id='pytest_id',
                retry_cnt=0,
                last_update_timestamp=now,
                last_update_user='administrator'
            )
            events_request.save(force_insert=True)

            # ルールマッチング結果詳細
            rhdm_response_action = RhdmResponseAction(
                response_id=1,
                rule_name='pytest_rule',
                execution_order=exec_order,
                action_type_id=action_type.pk,
                action_parameter_info='{"ACTION_PARAMETER_INFO": ["SERVER_LIST=localhost", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1"]}',
                action_pre_info='',
                action_retry_interval=1,
                action_retry_count=1,
                action_stop_interval=action_stop_interval,
                action_stop_count=action_stop_count,
                last_update_timestamp=now,
                last_update_user='administrator',
            )
            rhdm_response_action.save(force_insert=True)

            # アクション履歴
            action_history = ActionHistory(
                response_id=rhdm_response_action.response_id,
                trace_id=trace_id,
                rule_type_id=events_request.rule_type_id,
                rule_type_name='pytest_ruletable',
                rule_name=rhdm_response_action.rule_name,
                execution_order=rhdm_response_action.execution_order,
                action_start_time=now,
                action_type_id=rhdm_response_action.action_type_id,
                status=2,
                status_detail=0,
                status_update_id='pytest_id',
                retry_flag=False,
                retry_status=None,
                retry_status_detail=None,
                action_retry_count=0,
                last_act_user='administrator',
                last_update_timestamp=now,
                last_update_user='administrator',
            )
            action_history.save(force_insert=True)

    except Exception as e:
        print(e)

    return trace_id, rhdm_response_action, action_history


def delete_data_action_stop():
    """
    テストで使用したデータの削除
    テーブル初期化
    """
    module = import_module('web_app.models.ITA_models')
    ItaDriver = getattr(module, 'ItaDriver')

    EventsRequest.objects.all().delete()
    RhdmResponseAction.objects.all().delete()
    ActionHistory.objects.all().delete()
    ItaDriver.objects.all().delete()
    ActionType.objects.all().delete()


@pytest.fixture()
def setup_data_action():
    """
    テストデータのリセット
    """

    delete_data_action_stop()

    module = import_module('web_app.models.ITA_models')
    ItaDriver = getattr(module, 'ItaDriver')

    encryptpassword = AESCipher(settings.AES_KEY).encrypt('pytest')
    ita_driver = ItaDriver(
        ita_disp_name='ITA176',
        protocol='https',
        hostname='pytest-host-name',
        port='443',
        username='pytest',
        password=encryptpassword,
        last_update_timestamp=datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user='pytest',
    ).save(force_insert=True)

    yield

    delete_data_action_stop()


@pytest.mark.django_db
def test_is_prevented(setup_data_action):
    """
    抑止判定テスト
    """
    ############################################
    # 回数なし、間隔なしのテスト
    ############################################
    # テストデータ作成
    trace_id, rhdm_res_act, act_his = set_data_action_stop(0, 0, 1)

    # 抑止判定テスト
    act_sub = ActionDriverSubModules(rhdm_res_act.response_id, trace_id, 0)
    act_sub.action_history = act_his
    result1 = act_sub._prevent_by_interval_and_times(rhdm_res_act)

    # 抑止しないこと
    assert result1 == "both_none"

    ############################################
    # 回数あり、間隔ありのテスト(WAITパターン)
    ############################################
    # テストデータ作成
    trace_id, rhdm_res_act, act_his = set_data_action_stop(10, 10, 2)

    # 抑止判定テスト
    act_sub = ActionDriverSubModules(rhdm_res_act.response_id, trace_id, 0)
    act_sub.action_history = act_his
    result1 = act_sub._prevent_by_interval_and_times(rhdm_res_act)
    result2 = act_sub._is_prevented(rhdm_res_act, trace_id, act_his.pk)

    assert result1 == "both_existence"
    assert result2 == WAITING


@pytest.mark.django_db
def test_regist_exastro(ita_table, setup_data_action, monkeypatch):
    """
    regist_exastro()テスト
    """
    # テストデータ作成
    trace_id, rhdm_res_act, act_his = set_data_action_stop(0, 0, 1)
    act_sub = ActionDriverSubModules(rhdm_res_act.response_id, trace_id, 0)
    act_sub.action_history = act_his

    ITAManager = getattr(import_module('libs.backyardlibs.action_driver.ITA.ITA_driver'), 'ITAManager')
    monkeypatch.setattr(ITAManager, 'act_with_menuid', lambda a, b, c, d : (ACTION_HISTORY_STATUS.EXASTRO_REQUEST, ACTION_HISTORY_STATUS.DETAIL_STS.NONE))
    # 正常系
    result = act_sub.regist_exastro(trace_id, act_his.pk)
    assert result

    # 異常系 第2引数に不正な値を渡す
    result = act_sub.regist_exastro(trace_id, 'a')
    assert result == False


################################################################
# check_exastro_requestテスト
################################################################
@pytest.mark.django_db
def test_exastro_request_ok(ita_table, setup_data_action, monkeypatch):
    """
    exastro_request()テスト
    正常系
    """

    # テストデータ作成
    set_data_exastro_request()
    act_sub = ActionDriverSubModules(999, 'TOS_pytest999', 0)

    act_sub.driver_type_info = {
        1 : {
            'exastro' : '1',
            'name'    : 'ITA',
        },
    }

    ITAManager = getattr(import_module('libs.backyardlibs.action_driver.ITA.ITA_driver'), 'ITAManager')
    monkeypatch.setattr(ITAManager, 'set_information', lambda a, b, c:True)
    monkeypatch.setattr(ITAManager, 'get_last_info',   lambda a, b, c:(3,0))
    monkeypatch.setattr(chld_proc,  'update_action_history', lambda a, b, c, d, retry:True)

    # 正常系
    result = act_sub.check_exastro_request('TOS_pytest999', 999)

    assert result == True


@pytest.mark.django_db
def test_exastro_request_ng_acthistory_not_exists(ita_table, setup_data_action):
    """
    exastro_request()テスト
    アクション履歴なし
    """

    # テストデータ作成
    set_data_exastro_request()
    act_sub = ActionDriverSubModules(999, 'TOS_pytest999', 0)

    act_sub.driver_type_info = {
        1 : {
            'exastro' : '1',
            'name'    : 'ITA',
        },
    }

    ITAManager = getattr(import_module('libs.backyardlibs.action_driver.ITA.ITA_driver'), 'ITAManager')

    # テスト
    result = act_sub.check_exastro_request('TOS_pytest999', 998)

    assert result == False


@pytest.mark.django_db
def test_exastro_request_ng_not_exastro(ita_table, setup_data_action):
    """
    exastro_request()テスト
    exastroシリーズ外
    """

    # テストデータ作成
    set_data_exastro_request()
    act_sub = ActionDriverSubModules(999, 'TOS_pytest999', 0)

    act_sub.driver_type_info = {
        1 : {
            'exastro' : 'X',
            'name'    : 'ITA',
        },
    }

    ITAManager = getattr(import_module('libs.backyardlibs.action_driver.ITA.ITA_driver'), 'ITAManager')

    # テスト
    result = act_sub.check_exastro_request('TOS_pytest999', 999)

    assert result == False


@pytest.mark.django_db
def test_exastro_request_ng_ita_result_is_none(ita_table, setup_data_action, monkeypatch):
    """
    exastro_request()テスト
    ITA実行結果取得エラー
    """

    # テストデータ作成
    set_data_exastro_request()
    act_sub = ActionDriverSubModules(999, 'TOS_pytest999', 0)

    act_sub.driver_type_info = {
        1 : {
            'exastro' : '1',
            'name'    : 'ITA',
        },
    }

    ITAManager = getattr(import_module('libs.backyardlibs.action_driver.ITA.ITA_driver'), 'ITAManager')
    monkeypatch.setattr(ITAManager, 'set_information', lambda a, b, c:True)
    monkeypatch.setattr(ITAManager, 'get_last_info',   lambda a, b, c:(None,None))

    # テスト
    result = act_sub.check_exastro_request('TOS_pytest999', 999)

    assert result == False


@pytest.mark.django_db
def test_exastro_request_ng_respact_not_exists(ita_table, setup_data_action, monkeypatch):
    """
    exastro_request()テスト
    ITA実行結果取得エラー
    """

    # テストデータ作成
    set_data_exastro_request_ng()
    act_sub = ActionDriverSubModules(999, 'TOS_pytest999', 0)

    act_sub.driver_type_info = {
        1 : {
            'exastro' : '1',
            'name'    : 'ITA',
        },
    }

    ITAManager = getattr(import_module('libs.backyardlibs.action_driver.ITA.ITA_driver'), 'ITAManager')

    # テスト
    result = act_sub.check_exastro_request('TOS_pytest999', 999)

    assert result == False



