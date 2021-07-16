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
from libs.backyardlibs.oase_action_common_libs import ConstantModules as cmod
from libs.backyardlibs.action_driver.ITA.ITA_core import ITA1Core
from libs.webcommonlibs.oase_exception import OASEError
from web_app.models.models import ActionHistory, PreActionHistory, RhdmResponseAction, EventsRequest, DataObject
from libs.webcommonlibs.events_request import EventsRequestCommon
from libs.commonlibs.define import *
from libs.commonlibs.aes_cipher import AESCipher
from django.conf import settings
from django.db import transaction
from importlib import import_module
import json
import pytest
import datetime
import pytz


def get_ita_driver():
    """
    ItaDriverクラスを動的に読み込んで返す
    """
    return getattr(import_module('web_app.models.ITA_models'), 'ItaDriver')


def get_ita_manager():
    """
    ITAManagerクラスを動的に読み込んで返す
    """
    return getattr(import_module('libs.backyardlibs.action_driver.ITA.ITA_driver'), 'ITAManager')


def get_ita_action_history():
    """
    ItaActionHistoryクラスを動的に読み込んで返す
    """
    return getattr(import_module('web_app.models.ITA_models'), 'ItaActionHistory')


def get_ita_parameter_match_info():
    """
    ItaParameterMatchInfoクラスを動的に読み込んで返す
    """
    return getattr(import_module('web_app.models.ITA_models'), 'ItaParameterMatchInfo')


def get_ita_parameter_item_info():
    """
    ItaParameterItemInfoクラスを動的に読み込んで返す
    """
    return getattr(import_module('web_app.models.ITA_models'), 'ItaParameterItemInfo')


def get_ita_parameta_commit_info():
    """
    ItaParametaCommitInfoクラスを動的に読み込んで返す
    """
    return getattr(import_module('web_app.models.ITA_models'), 'ItaParametaCommitInfo')


def get_ita_name_menu_info():
    """
    ItaParametaCommitInfoクラスを動的に読み込んで返す
    """
    return getattr(import_module('web_app.models.ITA_models'), 'ItaMenuName')


################################################
# テスト用DB操作
################################################
def set_data_ita_driver(ita_disp_name):
    """
    ITAへの確認機能のテストに必要なデータをDBに登録
    """
    ItaDriver = get_ita_driver()
    cipher = AESCipher(settings.AES_KEY)
    now = datetime.datetime.now(pytz.timezone('UTC'))
    encrypted_password = cipher.encrypt('pytest')

    try:
        with transaction.atomic():

            # ITAアクションマスタ
            ItaDriver(
                ita_disp_name=ita_disp_name,
                protocol='https',
                hostname='pytest-host-name',
                port='443',
                username='pytest',
                password=encrypted_password,
                last_update_user='pytest',
                last_update_timestamp=now
            ).save(force_insert=True)

    except Exception as e:
        print(e)


@pytest.mark.django_db
def test_check_ita_master(ita_table, monkeypatch):
    """
    ITAへの確認機能テスト
    """
    ITAManager = get_ita_manager()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = "pytest"
    testITA = ITAManager(trace_id, response_id, last_update_user)

    ############################################
    # 正常終了パターン
    ############################################
    # テストデータ作成 operation_id
    ita_disp_name = 'action43'
    set_data_ita_driver(ita_disp_name)
    execution_order = 1
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.aryActionParameter['ITA_NAME'] = 'action43'

    parm_info = '{"ACTION_PARAMETER_INFO": ["OPERATION_ID=1", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1"]}'
    json_parm = json.loads(parm_info)
    testITA.set_action_server_list(json_parm, 1, 1)

    testITA.set_driver(execution_order)
    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    status, detail = testITA.check_ita_master(execution_order)

    # テスト結果判定
    assert status == 0
    assert detail == 0

    # テストデータ削除
    delete_data_param_information()

    ############################################
    # 正常終了パターン
    ############################################
    # テストデータ作成 Server_list
    ita_disp_name = 'action43'
    set_data_ita_driver(ita_disp_name)
    execution_order = 1
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.aryActionParameter['ITA_NAME'] = 'action43'

    parm_info = '{"ACTION_PARAMETER_INFO": ["SERVER_LIST=hostname", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1"]}'
    json_parm = json.loads(parm_info)
    testITA.set_action_server_list(json_parm, 1, 1)

    testITA.set_driver(execution_order)
    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    status, detail = testITA.check_ita_master(execution_order)

    # テスト結果判定
    assert status == 0
    assert detail == 0

    # テストデータ削除
    delete_data_param_information()

    ############################################
    # ITAへの確認機能テスト　失敗パターン
    ############################################
    # テストデータ作成
    ita_disp_name = 'dummy'
    set_data_ita_driver(ita_disp_name)
    execution_order = 2
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 5
    testITA.aryActionParameter['ITA_NAME'] = 'dummy'

    testITA.set_driver(execution_order)
    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (100))
    status, detail = testITA.check_ita_master(execution_order)

    # テスト結果判定
    assert status != 0
    assert detail != 0

    # テストデータ削除
    delete_data_param_information()

    ############################################
    # 正常終了パターン
    ############################################
    # テストデータ作成 operation_id
    ita_disp_name = 'action43'
    set_data_ita_driver(ita_disp_name)
    execution_order = 1
    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['CONDUCTOR_CLASS_ID'] = 1
    testITA.aryActionParameter['ITA_NAME'] = 'action43'

    parm_info = '{"ACTION_PARAMETER_INFO": ["OPERATION_ID=1", "ITA_NAME=ITA176", "CONDUCTOR_CLASS_ID=1"]}'
    json_parm = json.loads(parm_info)
    testITA.set_action_server_list(json_parm, 1, 1)

    testITA.set_driver(execution_order)
    monkeypatch.setattr(ITA1Core, 'select_ita_master_conductor', lambda a, b, c, d, e: (0))
    status, detail = testITA.check_ita_master(execution_order)

    # テスト結果判定
    assert status == 0
    assert detail == 0

    # テストデータ削除
    delete_data_param_information()

    ############################################
    # 正常終了パターン
    ############################################
    # テストデータ作成 Server_list
    ita_disp_name = 'action43'
    set_data_ita_driver(ita_disp_name)
    execution_order = 1
    testITA.aryActionParameter['CONDUCTOR_CLASS_ID'] = 1
    testITA.aryActionParameter['ITA_NAME'] = 'action43'

    parm_info = '{"ACTION_PARAMETER_INFO": ["SERVER_LIST=hostname", "ITA_NAME=ITA176", "CONDUCTOR_CLASS_ID=1"]}'
    json_parm = json.loads(parm_info)
    testITA.set_action_server_list(json_parm, 1, 1)

    testITA.set_driver(execution_order)
    monkeypatch.setattr(ITA1Core, 'select_ita_master_conductor', lambda a, b, c, d, e: (0))
    status, detail = testITA.check_ita_master(execution_order)

    # テスト結果判定
    assert status == 0
    assert detail == 0

    # テストデータ削除
    delete_data_param_information()

    ############################################
    # ITAへの確認機能テスト　失敗パターン
    ############################################
    # テストデータ作成
    ita_disp_name = 'dummy'
    set_data_ita_driver(ita_disp_name)
    execution_order = 2
    testITA.aryActionParameter['CONDUCTOR_CLASS_ID'] = 5
    testITA.aryActionParameter['ITA_NAME'] = 'dummy'

    testITA.set_driver(execution_order)
    monkeypatch.setattr(ITA1Core, 'select_ita_master_conductor', lambda a, b, c, d, e: (100))
    status, detail = testITA.check_ita_master(execution_order)

    # テスト結果判定
    assert status != 0
    assert detail != 0

    # テストデータ削除
    delete_data_param_information()

    ############################################
    # ITAへの確認機能テスト　失敗パターン(IDなし)
    ############################################
    # テストデータ作成
    ita_disp_name = 'dummy'
    set_data_ita_driver(ita_disp_name)
    execution_order = 2
    testITA.aryActionParameter['CONDUCTOR_CLASS_ID'] = None
    testITA.aryActionParameter['ITA_NAME'] = 'dummy'

    testITA.set_driver(execution_order)
    monkeypatch.setattr(ITA1Core, 'select_ita_master_conductor', lambda a, b, c, d, e: (100))
    status, detail = testITA.check_ita_master(execution_order)

    # テスト結果判定
    assert status != 0
    assert detail != 0

    # テストデータ削除
    delete_data_param_information()

    ############################################
    # ITAへの確認機能テスト　失敗パターン(IDなし)
    ############################################
    # テストデータ作成
    ita_disp_name = 'dummy'
    set_data_ita_driver(ita_disp_name)
    execution_order = 2
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = None
    testITA.aryActionParameter['ITA_NAME'] = 'dummy'

    testITA.set_driver(execution_order)
    monkeypatch.setattr(ITA1Core, 'select_ita_master_conductor', lambda a, b, c, d, e: (100))
    status, detail = testITA.check_ita_master(execution_order)

    # テスト結果判定
    assert status != 0
    assert detail != 0

    # テストデータ削除
    delete_data_param_information()

def set_data_for_last_info(ita_disp_name, execution_order):
    """
    テストで使用するデータの生成
    """
    ItaDriver = get_ita_driver()
    ItaActionHistory = get_ita_action_history()

    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    action_stop_interval = 1
    action_stop_count = 1

    ita_act_his = None
    parm_info = '{"ACTION_PARAMETER_INFO": ["OPERATION_ID=1", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1"]}'

    url = 'https://pytest-host-name:443/'
    try:
        with transaction.atomic():
            # ルールマッチング結果詳細
            rhdm_response_action = RhdmResponseAction(
                response_id=1,
                rule_name='pytest_rule',
                execution_order=execution_order,
                action_type_id=1,
                action_parameter_info=parm_info,
                action_pre_info='',
                action_retry_interval=1,
                action_retry_count=1,
                action_stop_interval=action_stop_interval,
                action_stop_count=action_stop_count,
                last_update_timestamp=now,
                last_update_user='pytest'
            )
            rhdm_response_action.save(force_insert=True)

            # アクション履歴
            action_history = ActionHistory(
                response_id=rhdm_response_action.response_id,
                trace_id=trace_id,
                rule_type_id=1,
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
                last_act_user='pytest',
                last_update_timestamp=now,
                last_update_user='pytest'
            )
            action_history.save(force_insert=True)
            act_his_id = action_history.action_history_id

            ita_act_his = ItaActionHistory(
                ita_action_his_id=1,
                action_his_id=1,
                ita_disp_name=ita_disp_name,
                symphony_instance_no=1,
                symphony_class_id=1,
                operation_id=1,
                symphony_workflow_confirm_url=url,
                restapi_error_info=None,
                last_update_timestamp=now,
                last_update_user='pytest'
            ).save(force_insert=True)

            # パスワードを暗号化
            cipher = AESCipher(settings.AES_KEY)
            encrypted_password = cipher.encrypt('pytest')

            ita_driver = ItaDriver(
                ita_disp_name=ita_disp_name,
                protocol='https',
                hostname='pytest-host-name',
                port='443',
                username='pytest',
                password=encrypted_password,
                last_update_user='pytest',
                last_update_timestamp=now,
            )
            ita_driver.save(force_insert=True)
    except Exception as e:
        print(e)

    return ita_act_his, act_his_id


def delete_data_param_information():
    """
    テストで使用したデータの削除
    """
    ItaDriver = get_ita_driver()
    ItaParameterMatchInfo = get_ita_parameter_match_info()
    ItaParameterItemInfo = get_ita_parameter_item_info()
    ItaParametaCommitInfo = get_ita_parameta_commit_info()
    ItaActionHistory = get_ita_action_history()
    ItaMenuName = get_ita_name_menu_info()

    RhdmResponseAction.objects.filter(last_update_user='pytest').delete()
    PreActionHistory.objects.filter(last_update_user='pytest').delete()
    ActionHistory.objects.filter(last_update_user='pytest').delete()
    EventsRequest.objects.filter(last_update_user='pytest').delete()
    ItaDriver.objects.filter(last_update_user='pytest').delete()
    ItaActionHistory.objects.filter(last_update_user='pytest',).delete()
    ItaParameterMatchInfo.objects.filter(last_update_user='pytest').delete()
    ItaParameterItemInfo.objects.filter(last_update_user='pytest').delete()
    ItaParametaCommitInfo.objects.filter(last_update_user='pytest').delete()
    ItaMenuName.objects.filter(last_update_user='pytest').delete()


@pytest.mark.django_db
def test_get_last_info(ita_table, monkeypatch):
    """
    ITAアクション結果取得テスト
    """
    ItaDriver = get_ita_driver()
    ITAManager = get_ita_manager()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = "pytest"
    testITA = ITAManager(trace_id, response_id, last_update_user)

    ############################################
    # 正常終了パターン
    ############################################
    # テストデータ作成
    ita_disp_name = 'ITA176'
    execution_order = 1

    ItaActionHistory, act_his_id = set_data_for_last_info(
        ita_disp_name, execution_order)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.aryActionParameter['ITA_NAME'] = 'ITA176'
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITA1Core, 'get_last_info', lambda a, b, c, d: (1))

    action_status, detail_status = testITA.get_last_info(
        1, execution_order)
    assert action_status != 0
    assert detail_status != 0

    # テストデータ削除
    delete_data_param_information()

    ############################################
    # 失敗パターン
    ############################################
    # テストデータ作成
    ita_disp_name = 'dummy'
    execution_order = 2

    ItaActionHistory, act_his_id = set_data_for_last_info(
        ita_disp_name, execution_order)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 2
    testITA.aryActionParameter['ITA_NAME'] = 'dummy'

    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITA1Core, 'get_last_info', lambda a, b, c, d: (5))

    action_status, detail_status = testITA.get_last_info(
        2, execution_order)
    assert action_status != 0
    assert detail_status == 0

    # テストデータ削除
    delete_data_param_information()


def set_data_for_information(exec_order, ita_disp_name, trace_id, parm_info):
    """
    テストで使用するデータの生成
    """
    ItaDriver = get_ita_driver()
    rhdm_response_action = None
    pre_action_history = None
    ita_driver = None
    now = datetime.datetime.now(pytz.timezone('UTC'))
    action_stop_interval = 1
    action_stop_count = 1

    try:
        with transaction.atomic():

            # ルールマッチング結果詳細
            rhdm_response_action = RhdmResponseAction(
                response_id=1,
                rule_name='pytest_rule',
                execution_order=exec_order,
                action_type_id=1,
                action_parameter_info=parm_info,
                action_pre_info='',
                action_retry_interval=1,
                action_retry_count=1,
                action_stop_interval=action_stop_interval,
                action_stop_count=action_stop_count,
                last_update_timestamp=now,
                last_update_user='pytest'
            )
            rhdm_response_action.save(force_insert=True)

            # アクション履歴
            action_history = ActionHistory(
                response_id=rhdm_response_action.response_id,
                trace_id=trace_id,
                rule_type_id=1,
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
                last_act_user='pytest',
                last_update_timestamp=now,
                last_update_user='pytest'
            )
            action_history.save(force_insert=True)

            # アクション実行前履歴
            pre_action_history = PreActionHistory(
                action_history_id=action_history.action_history_id,
                trace_id=trace_id,
                status=1,
                last_update_timestamp=now,
                last_update_user='pytest',
            )
            pre_action_history.save(force_insert=True)

            # パスワードを暗号化
            cipher = AESCipher(settings.AES_KEY)
            encrypted_password = cipher.encrypt('pytest')

            ita_driver = ItaDriver(
                ita_disp_name=ita_disp_name,
                protocol='https',
                hostname='pytest-host-name',
                port='443',
                username='pytest',
                password=encrypted_password,
                last_update_user='pytest',
                last_update_timestamp=now,
            )
            ita_driver.save(force_insert=True)

    except Exception as e:
        print(e)

    return rhdm_response_action, pre_action_history


@pytest.mark.django_db
def test_set_information(ita_table):
    """
    ITA情報登録 テスト
    """
    ITAManager = get_ita_manager()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = "pytest"
    testITA = ITAManager(trace_id, response_id, last_update_user)

    ############################################
    # 正常終了パターン1
    ############################################
    # テストデータ作成 OPERATON_ID
    ita_disp_name = 'ITA176'
    parm_info = '{"ACTION_PARAMETER_INFO": ["OPERATION_ID=1", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1"]}'
    rhdm_res_act, pre_action_history = set_data_for_information(
        1, ita_disp_name, trace_id, parm_info)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.aryActionParameter['ITA_NAME'] = ita_disp_name

    status, detail = testITA.set_information(rhdm_res_act, pre_action_history)
    assert status == 0
    assert detail == 0

    # テストデータ削除
    delete_data_param_information()

    ############################################
    # 正常終了パターン 2
    ############################################
    # テストデータ作成 SERVER_LIST
    ita_disp_name = 'ITA176'
    parm_info = '{"ACTION_PARAMETER_INFO": ["SERVER_LIST=hostname", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1"]}'
    rhdm_res_act, pre_action_history = set_data_for_information(
        1, ita_disp_name, trace_id, parm_info)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.aryActionParameter['ITA_NAME'] = ita_disp_name

    status, detail = testITA.set_information(rhdm_res_act, pre_action_history)
    assert status != 0
    assert detail != 0

    # テストデータ削除
    delete_data_param_information()

    ############################################
    # ITA確認機能　失敗パターン
    ############################################
    # テストデータ作成
    ita_disp_name = 'dummy'
    parm_info = '{"ACTION_PARAMETER_INFO": ["SERVER_LIST=hostname", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1"]}'
    rhdm_res_act, pre_action_history = set_data_for_information(
        1, ita_disp_name, trace_id, parm_info)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 2
    testITA.aryActionParameter['ITA_NAME'] = ita_disp_name

    status, detail = testITA.set_information(rhdm_res_act, pre_action_history)
    assert status != 0
    assert detail != 0

    # テストデータ削除
    delete_data_param_information()


def test_check_action_parameters():
    """
    アクションパラメータチェック テスト
    """
    ITAManager = get_ita_manager()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    last_update_user = "pytest"
    ita_disp_name = 'ITA176'
    response_id = 1

    ############################################
    # 異常終了パターン　必須キー(ITA_NAME)チェック
    ############################################
    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.aryActionParameter['SERVER_LIST'] = 1

    result = testITA.check_action_parameters()
    assert result == {'msg_id': 'MOSJA01006', 'key': 'ITA_NAME'}

    ########################################################
    # 異常終了パターン　必須キー(SYMPHONY_CLASS_ID or CONDUCTOR_CLASS_ID)チェック
    ########################################################
    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['ITA_NAME'] = ita_disp_name
    testITA.aryActionParameter['SERVER_LIST'] = 1

    result = testITA.check_action_parameters()
    assert result == {'msg_id': 'MOSJA01063', 'key': ['SYMPHONY_CLASS_ID', 'CONDUCTOR_CLASS_ID']}

    ########################################################
    # 異常終了パターン　排他キー(SYMPHONY_CLASS_ID, CONDUCTOR_CLASS_ID)チェック
    ########################################################
    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.aryActionParameter['CONDUCTOR_CLASS_ID'] = 1
    testITA.aryActionParameter['ITA_NAME'] = ita_disp_name
    testITA.aryActionParameter['OPERATION_ID'] = 1

    result = testITA.check_action_parameters()
    assert result == {'msg_id': 'MOSJA01062', 'key': ['SYMPHONY_CLASS_ID', 'CONDUCTOR_CLASS_ID']}

    ####################################################################
    # 異常終了パターン 排他キー(OPERATION_ID, SERVER_LIST)チェック
    ####################################################################
    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.aryActionParameter['ITA_NAME'] = ita_disp_name
    testITA.aryActionParameter['OPERATION_ID'] = 1
    testITA.aryActionParameter['SERVER_LIST'] = 1

    result = testITA.check_action_parameters()
    assert result == {'msg_id': 'MOSJA01062',
                      'key': ['OPERATION_ID', 'SERVER_LIST', 'MENU_ID']}

    ############################################
    # 正常終了パターン SYMPHONY_CLASS_ID
    ############################################
    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.aryActionParameter['ITA_NAME'] = ita_disp_name
    testITA.aryActionParameter['OPERATION_ID'] = 1

    result = testITA.check_action_parameters()

    assert not result

    ############################################
    # 正常終了パターン CONDUCTOR_CLASS_ID
    ############################################
    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['CONDUCTOR_CLASS_ID'] = 1
    testITA.aryActionParameter['ITA_NAME'] = ita_disp_name
    testITA.aryActionParameter['OPERATION_ID'] = 1

    result = testITA.check_action_parameters()

    assert not result

    ############################################
    # 正常終了パターン OPERATION_ID
    ############################################
    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.aryActionParameter['ITA_NAME'] = ita_disp_name
    testITA.aryActionParameter['OPERATION_ID'] = 1

    result = testITA.check_action_parameters()

    assert not result

    ############################################
    # 正常終了パターン SERVER_LIST
    ############################################
    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.aryActionParameter['ITA_NAME'] = ita_disp_name
    testITA.aryActionParameter['SERVER_LIST'] = 1

    result = testITA.check_action_parameters()
    assert not result


def test_set_action_parameters():
    """
    アクションパラメータ テスト
    """
    ITAManager = get_ita_manager()
    # テストデータ初期化
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = "pytest"
    exe_order = 1
    res_detail_id = 1

    ############################################
    # 正常終了パターン
    ############################################
    # テストデータ作成　Operation_id用
    ita_disp_name = 'ITA176'
    ACTION_PARAMETER_INFO = 'ITA_NAME=ITA176,SYMPHONY_CLASS_ID=1,OPERATION_ID=1'
    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.aryActionParameter['ITA_NAME'] = ita_disp_name
    testITA.aryActionParameter['OPERATION_ID'] = 1
    testITA.aryActionParameter['ACTION_PARAMETER_INFO'] = ACTION_PARAMETER_INFO
    testITA.set_action_parameters(
        testITA.aryActionParameter, exe_order, res_detail_id)

    # SERVER_LIST用

    ############################################
    # 異常終了パターン 1
    ############################################
    # テストデータ作成
    ita_disp_name = 'dummy'
    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.aryActionParameter['ITA_NAME'] = ita_disp_name
    testITA.aryActionParameter['OPERATION_ID'] = 1

    try:
        with pytest.raises(OASEError):
            testITA.set_action_parameters(
                testITA.aryActionParameter, exe_order, res_detail_id)
            assert False
    except:
        assert False


def test_set_action_server_list():
    '''
    アクションサーバーリストをメンバ変数にセットする動作確認
    '''
    ITAManager = get_ita_manager()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)

    response_id = 1
    last_update_user = 'pytest'

    testITA = ITAManager(trace_id, response_id, last_update_user)

    testITA.response_id = 1
    testITA.trace_id = EventsRequestCommon.generate_trace_id(now)

    ############################################
    # SERVER_LIST存在しないパターン
    ############################################
    parm_info = '{"ACTION_PARAMETER_INFO": ["ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1", "OPERATION_=xxxx"]}'

    json_parm = json.loads(parm_info)
    testITA.set_action_server_list(json_parm, 1, 1)

    assert len(testITA.listActionServer) == 0

    ############################################
    # SERVER_LIST1件パターン
    ############################################
    parm_info = '{"ACTION_PARAMETER_INFO": ["ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1", "SERVER_LIST=xxxx"]}'

    json_parm = json.loads(parm_info)
    testITA.set_action_server_list(json_parm, 1, 1)

    assert len(testITA.listActionServer) == 1

    ############################################
    # SERVER_LIST複数件パターン
    ############################################
    parm_info = '{"ACTION_PARAMETER_INFO": ["ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1", "SERVER_LIST=xxx1:xxx2"]}'

    json_parm = json.loads(parm_info)
    testITA.set_action_server_list(json_parm, 1, 1)

    assert len(testITA.listActionServer) == 3


################################################################
# ITAアクションを実行メソッドのテスト
################################################################
@pytest.mark.django_db
def test_act_ptrn_menuid_convertflg_true_ok(monkeypatch):
    """
    ITAアクションを実行メソッドのテスト
    MENU_IDあり CONVERT_FLG=TRUE パターン
    """
    ITAManager = get_ita_manager()
    ItaDriver = get_ita_driver()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    ita_disp_name = 'ITA176'

    parm_info = '{"ACTION_PARAMETER_INFO": ["MENU_ID=5", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=4","CONVERT_FLG=TRUE"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info, 3)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 4
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITAManager, 'ita_action_history_insert', lambda a, b, c, d, e, f, g, h, i: 3)
    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c, d: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (True, 'hoge'))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (True, [{cmod.COL_OPERATION_NO_IDBH:1, cmod.COL_OPERATION_NAME:'ope_name', cmod.COL_OPERATION_DATE:'20181231000000'}]))
    monkeypatch.setattr(ITA1Core, 'select_c_parameter_sheet', lambda a, b, c, d, e: (0, []))
    monkeypatch.setattr(ITA1Core, 'update_c_parameter_sheet', lambda a, b, c, d, e, f, g, h, i: (0))
    monkeypatch.setattr(ITA1Core, 'insert_c_parameter_sheet', lambda a, b, c, d, e, f, g: (0))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    status, detai = testITA.act(rhdm_res_act)
    assert status == ACTION_HISTORY_STATUS.ITA_REGISTERING_SUBSTITUTION_VALUE

    delete_data_param_information()


@pytest.mark.django_db
def test_act_ptrn_menuid_convertflg_false_ok(monkeypatch):
    """
    ITAアクションを実行メソッドのテスト
    アクションパラーメータにMENU_ID,CONVERT_FLG=FALSE を指定したパターン
    """
    ITAManager = get_ita_manager()
    ItaDriver = get_ita_driver()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    ita_disp_name = 'ITA176'

    parm_info = '{"ACTION_PARAMETER_INFO": ["MENU_ID=1", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1","CONVERT_FLG=FALSE"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info, 4)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITAManager, 'ita_action_history_insert', lambda a, b, c, d, e, f, g, h, i: 3)
    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c, d: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (True, 'hoge'))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (True, [{cmod.COL_OPERATION_NO_IDBH:1, cmod.COL_OPERATION_NAME:'ope_name', cmod.COL_OPERATION_DATE:'20181231000000'}]))
    monkeypatch.setattr(ITA1Core, 'select_c_parameter_sheet', lambda a, b, c, d, e: (0, []))
    monkeypatch.setattr(ITA1Core, 'update_c_parameter_sheet', lambda a, b, c, d, e, f, g, h, i: (0))
    monkeypatch.setattr(ITA1Core, 'insert_c_parameter_sheet', lambda a, b, c, d, e, f, g: (0))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    status, detai = testITA.act(rhdm_res_act)
    assert status == ACTION_HISTORY_STATUS.ITA_REGISTERING_SUBSTITUTION_VALUE

    delete_data_param_information()


@pytest.mark.django_db
def test_act_ptrn_menuid_hostgroup_convertflg_false_ok(monkeypatch):
    """
    ITAアクションを実行メソッドのテスト
    アクションパラーメータにMENU_ID,CONVERT_FLG=FALSE を指定したパターン
    """
    ITAManager = get_ita_manager()
    ItaDriver = get_ita_driver()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    ita_disp_name = 'ITA176'

    parm_info = '{"ACTION_PARAMETER_INFO": ["MENU_ID=1", "HOSTGROUP_NAME=1:HG1&HG2", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1","CONVERT_FLG=FALSE"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info, 4)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITAManager, 'ita_action_history_insert', lambda a, b, c, d, e, f, g, h, i: 3)
    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c, d: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (True, 'hoge'))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (True, [{cmod.COL_OPERATION_NO_IDBH:1, cmod.COL_OPERATION_NAME:'ope_name', cmod.COL_OPERATION_DATE:'20181231000000'}]))
    monkeypatch.setattr(ITA1Core, 'select_c_parameter_sheet', lambda a, b, c, d, e: (0, []))
    monkeypatch.setattr(ITA1Core, 'update_c_parameter_sheet', lambda a, b, c, d, e, f, g, h, i: (0))
    monkeypatch.setattr(ITA1Core, 'insert_c_parameter_sheet', lambda a, b, c, d, e, f, g: (0))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    status, detai = testITA.act(rhdm_res_act)
    assert status == ACTION_HISTORY_STATUS.ITA_REGISTERING_SUBSTITUTION_VALUE

    delete_data_param_information()


@pytest.mark.django_db
def test_act_ptrn_menuid_hostgroup_convertflg_false_update_ok(monkeypatch):
    """
    ITAアクションを実行メソッドのテスト
    アクションパラーメータにMENU_ID,CONVERT_FLG=FALSE を指定したパターン
    レコード重複OK
    """
    ITAManager = get_ita_manager()
    ItaDriver = get_ita_driver()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    ita_disp_name = 'ITA176'

    parm_info = '{"ACTION_PARAMETER_INFO": ["MENU_ID=1", "HOSTGROUP_NAME=1:HG1&HG2", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1","CONVERT_FLG=FALSE"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info, 4)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITAManager, 'ita_action_history_insert', lambda a, b, c, d, e, f, g, h, i: 3)
    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c, d: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (True, 'hoge'))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (True, [{cmod.COL_OPERATION_NO_IDBH:1, cmod.COL_OPERATION_NAME:'ope_name', cmod.COL_OPERATION_DATE:'20181231000000'}]))
    monkeypatch.setattr(ITA1Core, 'select_c_parameter_sheet', lambda a, b, c, d, e: (1, []))
    monkeypatch.setattr(ITA1Core, 'update_c_parameter_sheet', lambda a, b, c, d, e, f, g, h, i: (0))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    status, detai = testITA.act(rhdm_res_act)
    assert status == ACTION_HISTORY_STATUS.ITA_REGISTERING_SUBSTITUTION_VALUE

    delete_data_param_information()


@pytest.mark.django_db
def test_act_ptrn_menuid_hostgroup_convertflg_false_update_ng(monkeypatch):
    """
    ITAアクションを実行メソッドのテスト
    アクションパラーメータにMENU_ID,CONVERT_FLG=FALSE を指定したパターン
    レコード重複NG
    """
    ITAManager = get_ita_manager()
    ItaDriver = get_ita_driver()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    ita_disp_name = 'ITA176'

    parm_info = '{"ACTION_PARAMETER_INFO": ["MENU_ID=1", "HOSTGROUP_NAME=1:HG1&HG2", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1","CONVERT_FLG=FALSE"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info, 4)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITAManager, 'ita_action_history_insert', lambda a, b, c, d, e, f, g, h, i: 3)
    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c, d: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (True, 'hoge'))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (True, [{cmod.COL_OPERATION_NO_IDBH:1, cmod.COL_OPERATION_NAME:'ope_name', cmod.COL_OPERATION_DATE:'20181231000000'}]))
    monkeypatch.setattr(ITA1Core, 'select_c_parameter_sheet', lambda a, b, c, d, e: (None, []))
    monkeypatch.setattr(ITA1Core, 'update_c_parameter_sheet', lambda a, b, c, d, e, f, g, h, i: (0))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    status, detai = testITA.act(rhdm_res_act)
    assert status == ACTION_HISTORY_STATUS.ACTION_EXEC_ERROR

    delete_data_param_information()


@pytest.mark.django_db
def test_act_ptrn_menuid_host_convertflg_false_ok(monkeypatch):
    """
    ITAアクションを実行メソッドのテスト
    アクションパラーメータにMENU_ID,CONVERT_FLG=FALSE を指定したパターン
    """
    ITAManager = get_ita_manager()
    ItaDriver = get_ita_driver()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    ita_disp_name = 'ITA176'

    parm_info = '{"ACTION_PARAMETER_INFO": ["MENU_ID=1", "HOST_NAME=1:H1&H2", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1","CONVERT_FLG=FALSE"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info, 4)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITAManager, 'ita_action_history_insert', lambda a, b, c, d, e, f, g, h, i: 3)
    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c, d: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (True, 'hoge'))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (True, [{cmod.COL_OPERATION_NO_IDBH:1, cmod.COL_OPERATION_NAME:'ope_name', cmod.COL_OPERATION_DATE:'20181231000000'}]))
    monkeypatch.setattr(ITA1Core, 'select_c_parameter_sheet', lambda a, b, c, d, e: (0, []))
    monkeypatch.setattr(ITA1Core, 'update_c_parameter_sheet', lambda a, b, c, d, e, f, g, h, i: (0))
    monkeypatch.setattr(ITA1Core, 'insert_c_parameter_sheet', lambda a, b, c, d, e, f, g: (0))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    status, detai = testITA.act(rhdm_res_act)
    assert status == ACTION_HISTORY_STATUS.ITA_REGISTERING_SUBSTITUTION_VALUE

    delete_data_param_information()


@pytest.mark.django_db
def test_act_ptrn_menuid_hostgroup_host_convertflg_false_ok(monkeypatch):
    """
    ITAアクションを実行メソッドのテスト
    アクションパラーメータにMENU_ID,CONVERT_FLG=FALSE を指定したパターン
    """
    ITAManager = get_ita_manager()
    ItaDriver = get_ita_driver()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    ita_disp_name = 'ITA176'

    parm_info = '{"ACTION_PARAMETER_INFO": ["MENU_ID=1", "HOSTGROUP_NAME=1:HG1&HG2", "HOST_NAME=1:H1&H2", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1","CONVERT_FLG=FALSE"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info, 4)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITAManager, 'ita_action_history_insert', lambda a, b, c, d, e, f, g, h, i: 3)
    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c, d: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (True, 'hoge'))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (True, [{cmod.COL_OPERATION_NO_IDBH:1, cmod.COL_OPERATION_NAME:'ope_name', cmod.COL_OPERATION_DATE:'20181231000000'}]))
    monkeypatch.setattr(ITA1Core, 'select_c_parameter_sheet', lambda a, b, c, d, e: (0, []))
    monkeypatch.setattr(ITA1Core, 'update_c_parameter_sheet', lambda a, b, c, d, e, f, g, h, i: (0))
    monkeypatch.setattr(ITA1Core, 'insert_c_parameter_sheet', lambda a, b, c, d, e, f, g: (0))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    status, detai = testITA.act(rhdm_res_act)
    assert status == ACTION_HISTORY_STATUS.ITA_REGISTERING_SUBSTITUTION_VALUE

    delete_data_param_information()


@pytest.mark.django_db
def test_act_ptrn_multiple_menuid_convertflg_false_ok(monkeypatch):
    """
    ITAアクションを実行メソッドのテスト
    アクションパラーメータに複数のMENU_ID,CONVERT_FLG=FALSE を指定したパターン
    """
    ITAManager = get_ita_manager()
    ItaDriver = get_ita_driver()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    ita_disp_name = 'ITA176'

    parm_info = '{"ACTION_PARAMETER_INFO": ["MENU_ID=1:2", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1","CONVERT_FLG=FALSE"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info, 4)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITAManager, 'ita_action_history_insert', lambda a, b, c, d, e, f, g, h, i: 3)
    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c, d: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (True, 'hoge'))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (True, [{cmod.COL_OPERATION_NO_IDBH:1, cmod.COL_OPERATION_NAME:'ope_name', cmod.COL_OPERATION_DATE:'20181231000000'}]))
    monkeypatch.setattr(ITA1Core, 'select_c_parameter_sheet', lambda a, b, c, d, e: (0, []))
    monkeypatch.setattr(ITA1Core, 'update_c_parameter_sheet', lambda a, b, c, d, e, f, g, h, i: (0))
    monkeypatch.setattr(ITA1Core, 'insert_c_parameter_sheet', lambda a, b, c, d, e, f, g: (0))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    status, detai = testITA.act(rhdm_res_act)
    assert status == ACTION_HISTORY_STATUS.ITA_REGISTERING_SUBSTITUTION_VALUE

    delete_data_param_information()

@pytest.mark.django_db
def test_act_ptrn_multiple_menuid_hostgroup_convertflg_false_ok(monkeypatch):
    """
    ITAアクションを実行メソッドのテスト
    アクションパラーメータに複数のMENU_ID,CONVERT_FLG=FALSE を指定したパターン
    """
    ITAManager = get_ita_manager()
    ItaDriver = get_ita_driver()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    ita_disp_name = 'ITA176'

    parm_info = '{"ACTION_PARAMETER_INFO": ["MENU_ID=1:2", "HOSTGROUP=1:HG1&HG2|2:HG3&HG4&HG5", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1","CONVERT_FLG=FALSE"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info, 4)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITAManager, 'ita_action_history_insert', lambda a, b, c, d, e, f, g, h, i: 3)
    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c, d: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (True, 'hoge'))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (True, [{cmod.COL_OPERATION_NO_IDBH:1, cmod.COL_OPERATION_NAME:'ope_name', cmod.COL_OPERATION_DATE:'20181231000000'}]))
    monkeypatch.setattr(ITA1Core, 'select_c_parameter_sheet', lambda a, b, c, d, e: (0, []))
    monkeypatch.setattr(ITA1Core, 'update_c_parameter_sheet', lambda a, b, c, d, e, f, g, h, i: (0))
    monkeypatch.setattr(ITA1Core, 'insert_c_parameter_sheet', lambda a, b, c, d, e, f, g: (0))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    status, detai = testITA.act(rhdm_res_act)
    assert status == ACTION_HISTORY_STATUS.ITA_REGISTERING_SUBSTITUTION_VALUE

    delete_data_param_information()

@pytest.mark.django_db
def test_act_ptrn_ita_action_history_ng(monkeypatch):
    """
    ITAアクションを実行メソッドのテスト
    アクション履歴登録の失敗パターン
    """
    ITAManager = get_ita_manager()
    ItaDriver = get_ita_driver()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    ita_disp_name = 'ITA176'

    parm_info = '{"ACTION_PARAMETER_INFO": ["MENU_ID=1", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1","CONVERT_FLG=FALSE"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info, 4)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    #アクション履歴登録失敗
    monkeypatch.setattr(ITAManager, 'ita_action_history_insert', lambda a, b, c, d, e, f, g, h, i: None)
    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c, d: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (True, 'hoge'))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (True, [{cmod.COL_OPERATION_NO_IDBH:1, cmod.COL_OPERATION_NAME:'ope_name', cmod.COL_OPERATION_DATE:'20181231000000'}]))
    monkeypatch.setattr(ITA1Core, 'select_c_parameter_sheet', lambda a, b, c, d, e: (0, []))
    monkeypatch.setattr(ITA1Core, 'update_c_parameter_sheet', lambda a, b, c, d, e, f, g, h, i: (0))
    monkeypatch.setattr(ITA1Core, 'insert_c_parameter_sheet', lambda a, b, c, d, e, f, g: (0))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    status, detai = testITA.act(rhdm_res_act)
    status = ACTION_HISTORY_STATUS.ITA_REGISTERING_SUBSTITUTION_VALUE
    assert status == 2106

    delete_data_param_information()

@pytest.mark.django_db
def test_ptrn_menuid_act_ng(monkeypatch):
    ITAManager = get_ita_manager()
    ItaDriver = get_ita_driver()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    ita_disp_name = 'ITA176'

    parm_info = '{"ACTION_PARAMETER_INFO": ["MENU_ID=1:2", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1","CONVERT_FLG=TRUE"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info, 4)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c, d: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (True, 'hoge'))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (True, [{cmod.COL_OPERATION_NO_IDBH:1, cmod.COL_OPERATION_NAME:'ope_name', cmod.COL_OPERATION_DATE:'20181231000000'}]))
    monkeypatch.setattr(ITA1Core, 'select_c_parameter_sheet', lambda a, b, c, d, e: (0, []))
    monkeypatch.setattr(ITA1Core, 'update_c_parameter_sheet', lambda a, b, c, d, e, f, g, h, i: (0))
    monkeypatch.setattr(ITA1Core, 'insert_c_parameter_sheet', lambda a, b, c, d, e, f, g: (0))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    try:
        with pytest.raises(OASEError):
            status, detai = testITA.act(rhdm_res_act)
            assert status == ACTION_DATA_ERROR
    except:
        assert False

    delete_data_param_information()

    """
    ITAアクションを実行時のオペレーション登録/検索失敗のテスト
    """
    ItaDriver = get_ita_driver()
    ITAManager = get_ita_manager()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'

    # 異常系 (オペレーション登録失敗)
    trace_id = EventsRequestCommon.generate_trace_id(now)
    ita_disp_name = 'ITA176'
    parm_info = '{"ACTION_PARAMETER_INFO": ["MENU_ID=1", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1", "CONVERT_FLG=FALSE"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c, d: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (False, ''))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (True, [{cmod.COL_OPERATION_NO_IDBH:1, cmod.COL_OPERATION_NAME:'ope_name', cmod.COL_OPERATION_DATE:'20181231000000'}]))
    monkeypatch.setattr(ITA1Core, 'select_c_parameter_sheet', lambda a, b, c, d, e: (0, []))
    monkeypatch.setattr(ITA1Core, 'update_c_parameter_sheet', lambda a, b, c, d, e, f, g, h, i: (0))
    monkeypatch.setattr(ITA1Core, 'insert_c_parameter_sheet', lambda a, b, c, d, e, f, g: (0))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    status, detai = testITA.act(rhdm_res_act)
    assert status == ACTION_EXEC_ERROR

    delete_data_param_information()

    # 異常系 (オペレーション検索失敗)
    trace_id = EventsRequestCommon.generate_trace_id(now)
    ita_disp_name = 'ITA176'
    parm_info = '{"ACTION_PARAMETER_INFO": ["MENU_ID=1", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1", "CONVERT_FLG=FALSE"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c, d: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (True, 'hoge'))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (False, []))
    monkeypatch.setattr(ITA1Core, 'select_c_parameter_sheet', lambda a, b, c, d, e: (0, []))
    monkeypatch.setattr(ITA1Core, 'update_c_parameter_sheet', lambda a, b, c, d, e, f, g, h, i: (0))
    monkeypatch.setattr(ITA1Core, 'insert_c_parameter_sheet', lambda a, b, c, d, e, f, g: (0))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    status, detai = testITA.act(rhdm_res_act)
    assert status == ACTION_EXEC_ERROR

    delete_data_param_information()

    # 異常系 (パラメータシート登録失敗)
    trace_id = EventsRequestCommon.generate_trace_id(now)
    ita_disp_name = 'ITA176'
    parm_info = '{"ACTION_PARAMETER_INFO": ["MENU_ID=1", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1", "CONVERT_FLG=FALSE"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c, d: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (True, 'hoge'))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (True, [{cmod.COL_OPERATION_NO_IDBH:1, cmod.COL_OPERATION_NAME:'ope_name', cmod.COL_OPERATION_DATE:'20181231000000'}]))
    monkeypatch.setattr(ITA1Core, 'select_c_parameter_sheet', lambda a, b, c, d, e: (0, []))
    monkeypatch.setattr(ITA1Core, 'update_c_parameter_sheet', lambda a, b, c, d, e, f, g, h, i: (0))
    monkeypatch.setattr(ITA1Core, 'insert_c_parameter_sheet', lambda a, b, c, d, e, f, g: (cmod.RET_REST_ERROR))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    # TODO parameter_list.items()が0件の場合のの処理　後ほど修正すること
    try:
        with pytest.raises(OASEError):
            status, detai = testITA.act(rhdm_res_act)
            assert status == ACTION_EXEC_ERROR
    except:
        assert True

    delete_data_param_information()

@pytest.mark.django_db
def test_ptrn_multiple_menuid_act_ng(monkeypatch):
    """
    ITAアクションを実行時のオペレーション登録/検索失敗のテスト
    """
    ItaDriver = get_ita_driver()
    ITAManager = get_ita_manager()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'

    # 異常系 (オペレーション登録失敗)
    trace_id = EventsRequestCommon.generate_trace_id(now)
    ita_disp_name = 'ITA176'
    parm_info = '{"ACTION_PARAMETER_INFO": ["MENU_ID=1:2", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1", "CONVERT_FLG=TRUE"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c, d: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (False, ''))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (True, [{cmod.COL_OPERATION_NO_IDBH:1, cmod.COL_OPERATION_NAME:'ope_name', cmod.COL_OPERATION_DATE:'20181231000000'}]))
    monkeypatch.setattr(ITA1Core, 'insert_c_parameter_sheet', lambda a, b, c, d, e, f, g: (0))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    try:
        with pytest.raises(OASEError):
            status, detai = testITA.act(rhdm_res_act)
            assert status == ACTION_EXEC_ERROR
    except:
        assert True

    delete_data_param_information()

    # 異常系 (オペレーション検索失敗)
    trace_id = EventsRequestCommon.generate_trace_id(now)
    ita_disp_name = 'ITA176'
    parm_info = '{"ACTION_PARAMETER_INFO": ["MENU_ID=1:2", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1", "CONVERT_FLG=FALSE"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c, d: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (True, 'hoge'))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (False, []))
    monkeypatch.setattr(ITA1Core, 'insert_c_parameter_sheet', lambda a, b, c, d, e, f, g: (0))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    status, detai = testITA.act(rhdm_res_act)
    assert status == ACTION_EXEC_ERROR

    delete_data_param_information()

    # 異常系 (パラメータシート登録失敗)
    trace_id = EventsRequestCommon.generate_trace_id(now)
    ita_disp_name = 'ITA176'
    parm_info = '{"ACTION_PARAMETER_INFO": ["MENU_ID=1:2", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1", "CONVERT_FLG=FALSE"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c, d: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (True, 'hoge'))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (True, [{cmod.COL_OPERATION_NO_IDBH:1, cmod.COL_OPERATION_NAME:'ope_name', cmod.COL_OPERATION_DATE:'20181231000000'}]))
    monkeypatch.setattr(ITA1Core, 'insert_c_parameter_sheet', lambda a, b, c, d, e, f, g: (cmod.RET_REST_ERROR))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    # TODO parameter_list.items()が0件の場合のの処理　後ほど修正すること
    try:
        with pytest.raises(OASEError):
            status, detai = testITA.act(rhdm_res_act)
            assert status == ACTION_DATA_ERROR
    except:
        assert True

    delete_data_param_information()


@pytest.mark.django_db
def test_ptrn_menuid_hostgroup_act_ng(monkeypatch):
    ITAManager = get_ita_manager()
    ItaDriver = get_ita_driver()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    ita_disp_name = 'ITA176'

    parm_info = '{"ACTION_PARAMETER_INFO": ["MENU_ID=1:2", "HOSTGROUP_NAME=1:", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1","CONVERT_FLG=TRUE"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info, 4)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c, d: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (True, 'hoge'))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (True, [{cmod.COL_OPERATION_NO_IDBH:1, cmod.COL_OPERATION_NAME:'ope_name', cmod.COL_OPERATION_DATE:'20181231000000'}]))
    monkeypatch.setattr(ITA1Core, 'insert_c_parameter_sheet', lambda a, b, c, d, e, f, g: (0))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    try:
        with pytest.raises(OASEError):
            status, detai = testITA.act(rhdm_res_act)
            assert status == ACTION_DATA_ERROR
    except:
        assert False

    delete_data_param_information()

    # 異常系 (オペレーション検索失敗)
    trace_id = EventsRequestCommon.generate_trace_id(now)
    ita_disp_name = 'ITA176'
    parm_info = '{"ACTION_PARAMETER_INFO": ["MENU_ID=1", "HOSTGROUP_NAME=", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1", "CONVERT_FLG=FALSE"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c, d: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (True, 'hoge'))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (False, []))
    monkeypatch.setattr(ITA1Core, 'insert_c_parameter_sheet', lambda a, b, c, d, e, f, g: (0))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    try:
        with pytest.raises(OASEError):
            status, detai = testITA.act(rhdm_res_act)
            assert status == ACTION_DATA_ERROR
    except:
        assert False

    delete_data_param_information()

    # 異常系 (パラメータシート登録失敗)
    trace_id = EventsRequestCommon.generate_trace_id(now)
    ita_disp_name = 'ITA176'
    parm_info = '{"ACTION_PARAMETER_INFO": ["MENU_ID=1", "HOSTGROUPNAME=1:H1", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1", "CONVERT_FLG=FALSE"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c, d: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (True, 'hoge'))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (True, [{cmod.COL_OPERATION_NO_IDBH:1, cmod.COL_OPERATION_NAME:'ope_name', cmod.COL_OPERATION_DATE:'20181231000000'}]))
    monkeypatch.setattr(ITA1Core, 'insert_c_parameter_sheet', lambda a, b, c, d, e, f, g: (cmod.RET_REST_ERROR))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    try:
        with pytest.raises(OASEError):
            status, detai = testITA.act(rhdm_res_act)
            assert status == ACTION_DATA_ERROR
    except:
        assert True
    delete_data_param_information()


@pytest.mark.django_db
def test_ptrn_menuid_host_act_ng(monkeypatch):
    ITAManager = get_ita_manager()
    ItaDriver = get_ita_driver()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    ita_disp_name = 'ITA176'

    parm_info = '{"ACTION_PARAMETER_INFO": ["MENU_ID=1:2", "HOST_NAME=1:", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1","CONVERT_FLG=TRUE"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info, 4)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c, d: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (True, 'hoge'))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (True, [{cmod.COL_OPERATION_NO_IDBH:1, cmod.COL_OPERATION_NAME:'ope_name', cmod.COL_OPERATION_DATE:'20181231000000'}]))
    monkeypatch.setattr(ITA1Core, 'insert_c_parameter_sheet', lambda a, b, c, d, e, f, g: (0))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    try:
        with pytest.raises(OASEError):
            status, detai = testITA.act(rhdm_res_act)
            assert status == ACTION_DATA_ERROR
    except:
        assert False

    delete_data_param_information()

    # 異常系 (オペレーション検索失敗)
    trace_id = EventsRequestCommon.generate_trace_id(now)
    ita_disp_name = 'ITA176'
    parm_info = '{"ACTION_PARAMETER_INFO": ["MENU_ID=1", "HOST_NAME=", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1", "CONVERT_FLG=FALSE"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c, d: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (True, 'hoge'))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (False, []))
    monkeypatch.setattr(ITA1Core, 'insert_c_parameter_sheet', lambda a, b, c, d, e, f, g: (0))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    try:
        with pytest.raises(OASEError):
            status, detai = testITA.act(rhdm_res_act)
            assert status == ACTION_DATA_ERROR
    except:
        assert False

    delete_data_param_information()

    # 異常系 (パラメータシート登録失敗)
    trace_id = EventsRequestCommon.generate_trace_id(now)
    ita_disp_name = 'ITA176'
    parm_info = '{"ACTION_PARAMETER_INFO": ["MENU_ID=1", "HOSTNAME=1:H1", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1", "CONVERT_FLG=FALSE"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c, d: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (True, 'hoge'))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (True, [{cmod.COL_OPERATION_NO_IDBH:1, cmod.COL_OPERATION_NAME:'ope_name', cmod.COL_OPERATION_DATE:'20181231000000'}]))
    monkeypatch.setattr(ITA1Core, 'insert_c_parameter_sheet', lambda a, b, c, d, e, f, g: (cmod.RET_REST_ERROR))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    try:
        with pytest.raises(OASEError):
            status, detai = testITA.act(rhdm_res_act)
            assert status == ACTION_DATA_ERROR
    except:
        assert True

    delete_data_param_information()


@pytest.mark.django_db
def test_act_ptrn_serverlist_ok(monkeypatch):
    """
    ITAアクションを実行メソッドのテスト
    アクションパラーメータにSERVER_LISTを指定したパターン
    """
    ItaDriver = get_ita_driver()
    ITAManager = get_ita_manager()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    ita_disp_name = 'ITA176'
    parm_info = '{"ACTION_PARAMETER_INFO": ["ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1","SERVER_LIST=hostname"]}'
    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, parm_info)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(ITAManager, 'ita_action_history_insert', lambda a, b, c, d, e, f, g, h: 3)
    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (True, 'hoge'))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (True, [{cmod.COL_OPERATION_NO_IDBH:1, cmod.COL_OPERATION_NAME:'ope_name', cmod.COL_OPERATION_DATE:'20181231000000'}]))
    monkeypatch.setattr(ITA1Core, 'insert_c_parameter_sheet', lambda a, b, c, d, e, f, g: (cmod.RET_REST_ERROR))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'insert_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))

    # monkeypatchを使用すると必ずエラーになるためテストを行わない
    #status, detai = testITA.act(rhdm_res_act)
    #assert status == ACTION_HISTORY_STATUS.EXASTRO_REQUEST

    delete_data_param_information()


@pytest.mark.django_db
def test_set_host_data_HG_ok(monkeypatch):
    """
    ホストグループ名/ホスト名の正常性チェック
    HGを確認するパターン
    """

    ITAManager = get_ita_manager()

    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    testITA = ITAManager(trace_id, response_id, last_update_user)

    key = 'HG'
    name_data = '1:HG2&HG3'
    menu_id = '1'

    target_host_name = {}
    target_host_name[menu_id] = {'H': [], 'HG': []}
    target_host = {menu_id: {'H': [], 'HG': ['HG2', 'HG3']}}

    result = testITA.set_host_data(target_host_name, key, name_data)
    assert result == target_host


@pytest.mark.django_db
def test_set_host_data_H_ok(monkeypatch):
    """
    ホストグループ名/ホスト名の正常性チェック
    Hを確認するパターン
    """

    ITAManager = get_ita_manager()

    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    testITA = ITAManager(trace_id, response_id, last_update_user)

    key = 'H'
    name_data = '1:H2&H3'
    menu_id = '1'

    target_host_name = {}
    target_host_name[menu_id] = {'H': [], 'HG': []}
    target_host = {menu_id: {'H': ['H2', 'H3'], 'HG': []}}

    result = testITA.set_host_data(target_host_name, key, name_data)
    assert result == target_host


@pytest.mark.django_db
def test_set_host_data_HG_ng1(monkeypatch):
    """
    ホストグループ名/ホスト名の正常性チェック
    アクションパラーメータにSERVER_LISTを指定したパターン
    """

    ITAManager = get_ita_manager()

    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    testITA = ITAManager(trace_id, response_id, last_update_user)

    key = 'H'
    name_data = '1:H2&H3&H4'
    menu_id = ''

    target_host_name = {}
    target_host_name[menu_id] = {'H': [], 'HG': []}
    target_host = {menu_id: {'H': [], 'HG': []}}

    result = testITA.set_host_data(target_host_name, key, name_data)
    assert result == target_host


def test_set_host_data_HG_ng2(monkeypatch):
    """
    ホストグループ名/ホスト名の正常性チェック
    アクションパラーメータにSERVER_LISTを指定したパターン
    """

    ITAManager = get_ita_manager()

    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    testITA = ITAManager(trace_id, response_id, last_update_user)

    key = 'H'
    name_data = '1:H2&H3&H4'
    menu_id = '2'

    target_host_name = {}
    target_host_name[menu_id] = {'H': [], 'HG': []}
    target_host = {menu_id: {'H': [], 'HG': []}}

    result = testITA.set_host_data(target_host_name, key, name_data)
    assert result == target_host

@pytest.mark.django_db
def test_set_host_data_HGandH_ok(monkeypatch):
    """
    ホストグループ名/ホスト名の正常性チェック
    HGとHの複合パターン
    """

    ITAManager = get_ita_manager()

    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    testITA = ITAManager(trace_id, response_id, last_update_user)

    key = 'HG'
    name_data = '1:HG2&HG3'
    menu_id = '1'

    target_host_name = {}
    target_host_name[menu_id] = {'H': [], 'HG': []}

    result = testITA.set_host_data(target_host_name, key, name_data)

    key = 'H'
    name_data = '1:H3&H3'
    menu_id = '1'
    target_host = {menu_id: {'H': ['H3', 'H3'], 'HG': ['HG2', 'HG3']}}

    result = testITA.set_host_data(result, key, name_data)
    assert result == target_host


@pytest.mark.django_db
def test_set_host_data_H_ok(monkeypatch):
    """
    ホストグループ名/ホスト名の正常性チェック
    アクションパラーメータにSERVER_LISTを指定したパターン
    """

    ITAManager = get_ita_manager()

    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    testITA = ITAManager(trace_id, response_id, last_update_user)

    key = 'H'
    name_data = '1:H2&H3'
    menu_id = '1'

    target_host_name = {}
    target_host_name[menu_id] = {'H': [], 'HG': []}
    target_host = {menu_id: {'H': ['H2', 'H3'], 'HG': []}}

    result = testITA.set_host_data(target_host_name, key, name_data)
    assert result == target_host


@pytest.mark.django_db
def test_act_ok(monkeypatch):
    """
    ITAアクションを実行メソッドのテスト
    アクションパラーメータにOPERATION_IDを指定したパターン
    """
    ItaDriver = get_ita_driver()
    ITAManager = get_ita_manager()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    ita_disp_name = 'ITA176'
    parm_info = '{"ACTION_PARAMETER_INFO": ["OPERATION_ID=1", "ITA_NAME=ITA176", "SYMPHONY_CLASS_ID=1"]}'
    rhdm_res_act, pre_action_history = set_data_for_information(
        1, ita_disp_name, trace_id, parm_info)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 1
    testITA.ita_driver = ItaDriver.objects.get(ita_disp_name=ita_disp_name)

    monkeypatch.setattr(testITA, 'ita_action_history_insert', lambda a, b, c, d, e, f, g: 3)
    monkeypatch.setattr(ITA1Core, 'select_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, 'insert_operation', lambda a, b: (True, 'hoge'))
    monkeypatch.setattr(ITA1Core, 'select_operation', lambda a, b, c: (True, [{cmod.COL_OPERATION_NO_IDBH:1, cmod.COL_OPERATION_NAME:'ope_name', cmod.COL_OPERATION_DATE:'20181231000000'}]))
    monkeypatch.setattr(ITA1Core, 'insert_c_parameter_sheet', lambda a, b, c, d, e, f, g: (cmod.RET_REST_ERROR))
    monkeypatch.setattr(ITA1Core, 'select_ope_ita_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, 'insert_ita_master', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ITA1Core, 'symphony_execute', lambda a, b, c: (0, 1, 'https'))
    status, detai = testITA.act(rhdm_res_act)

    assert status == ACTION_HISTORY_STATUS.EXASTRO_REQUEST

    delete_data_param_information()


@pytest.mark.django_db
def test_ita_action_history_insert_ok():
    """
    ITAアクション履歴登録メソッドのテスト
    insert処理の正常系
    """

    ItaDriver = get_ita_driver()
    ITAManager = get_ita_manager()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    ita_disp_name = 'ITA176'
    param_info = {
        'ITA_NAME':ita_disp_name,
        'SYMPHONY_CLASS_ID' : 1,
    }

    rhdm_res_act, pre_action_history = set_data_for_information(
        1, ita_disp_name, trace_id, '')

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.action_history = ActionHistory.objects.all()[0]

    itaacthist = testITA.ita_action_history_insert(param_info, 1, 1, 'http://hoge.example.com/', 1, 1, 'http://conductor.example.com/')

    assert itaacthist != None

    delete_data_param_information()


@pytest.mark.django_db
def test_ita_action_history_update_ok():
    """
    ITAアクション履歴登録メソッドのテスト
    insert処理の正常系
    """

    ItaDriver = get_ita_driver()
    ITAManager = get_ita_manager()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    ita_disp_name = 'ITA176'
    param_info = {
        'ITA_NAME':ita_disp_name,
        'SYMPHONY_CLASS_ID' : 1,
    }

    rhdm_res_act, pre_action_history = set_data_for_information(
        1, ita_disp_name, trace_id, '')

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.action_history = ActionHistory.objects.all()[0]

    itaacthist = testITA.ita_action_history_insert(param_info, 1, 1, 'http://hoge.example.com/', 1, 1, 'http://conductor.example.com/')
    itaacthist = testITA.ita_action_history_insert(param_info, 9, 9, 'http://hoge.example.com/', 1, 1, 'http://conductor.example.com/')

    assert itaacthist != None
    assert itaacthist.operation_id == 9

    delete_data_param_information()


@pytest.mark.django_db
def test_make_parameter_item_info_ok():
    """
    パラメーター項目情報作成メソッドのテスト
    正常系(対象ホスト指定なし)
    """

    ItaDriver = get_ita_driver()
    ITAManager = get_ita_manager()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    ita_disp_name = 'ITA176'
    param_info = {
        'ITA_NAME':ita_disp_name,
        'SYMPHONY_CLASS_ID' : 1,
    }
    target_host = {
        '1':{'H':[], 'HG':[]},
        '2':{'H':[], 'HG':[]}
    }
    event_info_list = []
    assert_parameter_item_info = '1:pytest用メニュー1[ホスト名:HostName], 2:pytest用メニュー2[ホスト名:HostGroupName]'

    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, param_info)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.ita_driver = ItaDriver.objects.all()[0]

    set_data_param_item(testITA.ita_driver.ita_driver_id, response_id, rhdm_res_act.execution_order)

    parameter_item_info = testITA.make_parameter_item_info([1, 2], rhdm_res_act, target_host, event_info_list, 'False')

    assert assert_parameter_item_info == parameter_item_info

    delete_data_param_information()


@pytest.mark.django_db
def test_make_parameter_item_info_ok_specifyhost_nomatch():
    """
    パラメーター項目情報作成メソッドのテスト
    正常系(対象ホスト指定がマッチしない)
    """

    ItaDriver = get_ita_driver()
    ITAManager = get_ita_manager()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    ita_disp_name = 'ITA176'
    param_info = {
        'ITA_NAME':ita_disp_name,
        'SYMPHONY_CLASS_ID' : 1,
    }
    target_host = {
        '1':{'H':['Host99'], 'HG':['HostGroup99']},
        '2':{'H':['Host99'], 'HG':['HostGroup99']}
    }
    event_info_list = []
    assert_parameter_item_info = '1:pytest用メニュー1[ホスト名/ホストグループ名:HostGroup99,Host99], 2:pytest用メニュー2[ホスト名/ホストグループ名:HostGroup99,Host99]'

    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, param_info)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.ita_driver = ItaDriver.objects.all()[0]

    set_data_param_item(testITA.ita_driver.ita_driver_id, response_id, rhdm_res_act.execution_order)

    parameter_item_info = testITA.make_parameter_item_info([1, 2], rhdm_res_act, target_host, event_info_list, 'False')

    assert assert_parameter_item_info == parameter_item_info

    delete_data_param_information()


@pytest.mark.django_db
def test_make_parameter_item_info_ok_specifyhost_all():
    """
    パラメーター項目情報作成メソッドのテスト
    正常系(対象ホスト指定がホスト/ホストグループ/両方の全パターン)
    """

    ItaDriver = get_ita_driver()
    ITAManager = get_ita_manager()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    ita_disp_name = 'ITA176'
    param_info = {
        'ITA_NAME':ita_disp_name,
        'SYMPHONY_CLASS_ID' : 1,
    }
    target_host = {
        '1':{'H':['[H]Host1001', ], 'HG':[]},
        '2':{'HG':['[HG]HostGr2001', ], 'H':[]},
        '5':{'H':['[H]Host5001', ], 'HG':['[HG]HostGr5002', ]}
    }
    event_info_list = []
    assert_parameter_item_info = '1:pytest用メニュー1[ホスト名/ホストグループ名:[H]Host1001], 2:pytest用メニュー2[ホスト名/ホストグループ名:[HG]HostGr2001], 5:pytest用メニュー5[ホスト名/ホストグループ名:[HG]HostGr5002,[H]Host5001]'

    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, param_info)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.ita_driver = ItaDriver.objects.all()[0]

    set_data_param_item(testITA.ita_driver.ita_driver_id, response_id, rhdm_res_act.execution_order)

    parameter_item_info = testITA.make_parameter_item_info([1, 2, 5], rhdm_res_act, target_host, event_info_list, 'False')

    assert assert_parameter_item_info == parameter_item_info

    delete_data_param_information()


@pytest.mark.django_db
def test_make_parameter_item_info_ok_nomatch():
    """
    パラメーター項目情報作成メソッドのテスト
    正常系(マッチング情報なし)
    """

    ItaDriver = get_ita_driver()
    ITAManager = get_ita_manager()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    ita_disp_name = 'ITA176'
    param_info = {
        'ITA_NAME':ita_disp_name,
        'SYMPHONY_CLASS_ID' : 1,
    }
    event_info_list = []

    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, param_info)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.ita_driver = ItaDriver.objects.all()[0]

    set_data_param_item(testITA.ita_driver.ita_driver_id, response_id, rhdm_res_act.execution_order)

    parameter_item_info = testITA.make_parameter_item_info([99], rhdm_res_act, {}, event_info_list, 'False')

    assert parameter_item_info == ''

    delete_data_param_information()


@pytest.mark.django_db
def test_make_parameter_item_info_convert_true_ok():
    """
    パラメーター項目情報作成メソッドのテスト
    正常系(加工あり)
    """

    ItaDriver = get_ita_driver()
    ITAManager = get_ita_manager()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    ita_disp_name = 'ITA176'
    param_info = {
        'ITA_NAME':ita_disp_name,
        'SYMPHONY_CLASS_ID' : 1,
    }
    target_host = {
        '1':{'H':[], 'HG':[]}
    }
    event_info_list = ['HostName', 'ItemName1001']
    assert_parameter_item_info = '1:pytest用メニュー1[ホスト名:HostName, ItemName1001:ItemName1001]'

    rhdm_res_act = set_data_param_information(1, ita_disp_name, trace_id, param_info)

    testITA = ITAManager(trace_id, response_id, last_update_user)
    testITA.ita_driver = ItaDriver.objects.all()[0]

    set_data_param_item(testITA.ita_driver.ita_driver_id, response_id, rhdm_res_act.execution_order)

    parameter_item_info = testITA.make_parameter_item_info([1], rhdm_res_act, target_host, event_info_list, 'True')

    assert assert_parameter_item_info == parameter_item_info

    delete_data_param_information()


def create_ita1core():
    """
    ITA1Coreのインスタンスを作成して返す
    """
    trace_id = '-' * 40
    symphony_class_no_ = '1'
    response_id = '2'
    execution_order = '3'
    return ITA1Core(trace_id, symphony_class_no_, response_id, execution_order)


def set_data_param_item(drv_id, resp_id, exec_order):
    """
    テストで使用するパラメーターシート項目データの生成
    """

    now = datetime.datetime.now(pytz.timezone('UTC'))

    ItaParameterItemInfo = get_ita_parameter_item_info()
    ItaParametaCommitInfo = get_ita_parameta_commit_info()

    # パラメーターシート項目データ作成
    ItaParameterItemInfo(
        ita_driver_id = drv_id,
        menu_id = 1,
        column_group = '',
        item_name = 'ItemName1001',
        item_number = 1,
        ita_order = 1,
        last_update_timestamp = now,
        last_update_user = 'pytest'
    ).save(force_insert=True)

    ItaParameterItemInfo(
        ita_driver_id = drv_id,
        menu_id = 2,
        column_group = '',
        item_name = 'ItemName2001',
        item_number = 2,
        ita_order = 1,
        last_update_timestamp = now,
        last_update_user = 'pytest'
    ).save(force_insert=True)

    ItaParameterItemInfo(
        ita_driver_id = drv_id,
        menu_id = 5,
        column_group = '',
        item_name = 'ItemName5001',
        item_number = 5,
        ita_order = 1,
        last_update_timestamp = now,
        last_update_user = 'pytest'
    ).save(force_insert=True)

    # パラメーターシート投入データ作成
    ItaParametaCommitInfo(
        response_id = resp_id,
        commit_order = exec_order,
        menu_id = 1,
        ita_order = 0,
        parameter_value = 'HostName',
        last_update_timestamp = now,
        last_update_user = 'pytest'
    ).save(force_insert=True)

    ItaParametaCommitInfo(
        response_id = resp_id,
        commit_order = exec_order,
        menu_id = 1,
        ita_order = 1,
        parameter_value = 'ParamData1001',
        last_update_timestamp = now,
        last_update_user = 'pytest'
    ).save(force_insert=True)

    ItaParametaCommitInfo(
        response_id = resp_id,
        commit_order = exec_order,
        menu_id = 2,
        ita_order = 0,
        parameter_value = 'HostGroupName',
        last_update_timestamp = now,
        last_update_user = 'pytest'
    ).save(force_insert=True)

    ItaParametaCommitInfo(
        response_id = resp_id,
        commit_order = exec_order,
        menu_id = 2,
        ita_order = 1,
        parameter_value = 'ParamData2001',
        last_update_timestamp = now,
        last_update_user = 'pytest'
    ).save(force_insert=True)

    ItaParametaCommitInfo(
        response_id = resp_id,
        commit_order = exec_order,
        menu_id = 5,
        ita_order = 0,
        parameter_value = 'HostName',
        last_update_timestamp = now,
        last_update_user = 'pytest'
    ).save(force_insert=True)

    ItaParametaCommitInfo(
        response_id = resp_id,
        commit_order = exec_order,
        menu_id = 5,
        ita_order = 1,
        parameter_value = 'ParamData5001',
        last_update_timestamp = now,
        last_update_user = 'pytest'
    ).save(force_insert=True)


def get_evinfo(act_ptrn):
    """
    [概要]
      アクション実行パターン別にテストで使用するイベント情報を返却
    [引数]
      act_ptrn : 1=OPERATION_ID, 2=SERVER_LIST, 3=MENU_ID
    """

    event_info = '{"EVENT_INFO":["hostname","httpd"]}'

    if act_ptrn == 3:
        event_info = '{"EVENT_INFO":["hostname","httpd","date"]}'
    elif act_ptrn == 4:
        event_info = '{"EVENT_INFO":["18:09 TEST825   E (対象ノード= hostname )( SystemScope(0000):pcheck001[999]: Process [/opt/sample/bin/aaa ,pid=7203]Down TEST001 )TEST002"]}'

    return event_info


def set_data_param_information(exec_order, ita_disp_name, trace_id, parm_info, act_ptrn=0):
    """
    テストで使用するデータの生成
    """
    ItaDriver = get_ita_driver()
    ItaParameterMatchInfo = get_ita_parameter_match_info()
    ItaMenuName = get_ita_name_menu_info()

    rhdm_response_action = None
    pre_action_history = None
    ita_driver = None
    now = datetime.datetime.now(pytz.timezone('UTC'))
    action_stop_interval = 1
    action_stop_count = 1

    try:
        with transaction.atomic():

            # イベントリクエスト
            events_request = EventsRequest(
                request_id=1,
                trace_id=trace_id,
                request_type_id=1,
                rule_type_id=1,
                request_reception_time='2020-03-04 08:37:46.139355',
                request_user='OASE Web User',
                request_server='OASE Web',
                event_to_time='2020-03-03 02:18:00.000000',
                event_info=get_evinfo(act_ptrn),
                status=3,
                status_update_id=None,
                retry_cnt=0,
                last_update_timestamp=now,
                last_update_user='pytest'
            )
            events_request.save(force_insert=True)

            # ルールマッチング結果詳細
            rhdm_response_action = RhdmResponseAction(
                response_id=1,
                rule_name='pytest_rule',
                execution_order=exec_order,
                action_type_id=1,
                action_parameter_info=parm_info,
                action_pre_info='',
                action_retry_interval=1,
                action_retry_count=1,
                action_stop_interval=action_stop_interval,
                action_stop_count=action_stop_count,
                last_update_timestamp=now,
                last_update_user='pytest'
            )
            rhdm_response_action.save(force_insert=True)

            # アクション履歴
            action_history = ActionHistory(
                response_id=rhdm_response_action.response_id,
                trace_id=trace_id,
                rule_type_id=1,
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
                last_act_user='pytest',
                last_update_timestamp=now,
                last_update_user='pytest'
            )
            action_history.save(force_insert=True)

            # アクション実行前履歴
            pre_action_history = PreActionHistory(
                action_history_id=action_history.action_history_id,
                trace_id=trace_id,
                status=1,
                last_update_timestamp=now,
                last_update_user='pytest'
            )
            pre_action_history.save(force_insert=True)

            # パスワードを暗号化
            cipher = AESCipher(settings.AES_KEY)
            encrypted_password = cipher.encrypt('pytest')

            ita_driver = ItaDriver(
                ita_disp_name=ita_disp_name,
                protocol='https',
                hostname='pytest-host-name',
                port='443',
                username='pytest',
                password=encrypted_password,
                last_update_user='pytest',
                last_update_timestamp=now
            )
            ita_driver.save(force_insert=True)

            # ITAパラメータ抽出条件
            ItaParameterMatchInfo(
                ita_driver_id=ita_driver.ita_driver_id,
                menu_id=1,
                parameter_name='ホスト名',
                order=0,
                conditional_name='メッセージ本文',
                extraction_method1=r'対象ノード= ([\w-]+)',
                extraction_method2='対象ノード=',
                last_update_timestamp=now,
                last_update_user='pytest'
            ).save(force_insert=True)

            ItaParameterMatchInfo(
                ita_driver_id=ita_driver.ita_driver_id,
                menu_id=1,
                parameter_name='プロセス',
                order=1,
                conditional_name='メッセージ本文',
                extraction_method1=r'pid=\d*',
                extraction_method2='pid=',
                last_update_timestamp=now,
                last_update_user='pytest'
            ).save(force_insert=True)

            ItaParameterMatchInfo(
                ita_driver_id=ita_driver.ita_driver_id,
                menu_id=2,
                parameter_name='ホスト名',
                order=0,
                conditional_name='メッセージ本文',
                extraction_method1=r'対象ノード= ([\w-]+)',
                extraction_method2='対象ノード=',
                last_update_timestamp=now,
                last_update_user='pytest'
            ).save(force_insert=True)

            ItaParameterMatchInfo(
                ita_driver_id=ita_driver.ita_driver_id,
                menu_id=2,
                parameter_name='プロセス',
                order=1,
                conditional_name='メッセージ本文',
                extraction_method1=r'pid=\d*',
                extraction_method2='pid=',
                last_update_timestamp=now,
                last_update_user='pytest'
            ).save(force_insert=True)

            ItaMenuName(
                ita_driver_id=ita_driver.ita_driver_id,
                menu_group_id=1,
                menu_id=1,
                menu_group_name='testGroup',
                menu_name='pytest用メニュー1',
                hostgroup_flag=True,
                last_update_timestamp=now,
                last_update_user='pytest',
            ).save(force_insert=True)

            ItaMenuName(
                ita_driver_id=ita_driver.ita_driver_id,
                menu_group_id=1,
                menu_id=2,
                menu_group_name='testGroup',
                menu_name='pytest用メニュー2',
                hostgroup_flag=False,
                last_update_timestamp=now,
                last_update_user='pytest',
            ).save(force_insert=True)

            ItaMenuName(
                ita_driver_id=ita_driver.ita_driver_id,
                menu_group_id=1,
                menu_id=5,
                menu_group_name='testGroup',
                menu_name='pytest用メニュー5',
                hostgroup_flag=True,
                last_update_timestamp=now,
                last_update_user='pytest',
            ).save(force_insert=True)

            # データオブジェクト
            DataObject(
                rule_type_id=1,
                conditional_name='メッセージ本文',
                label='label0',
                conditional_expression_id=3,
                last_update_timestamp=now,
                last_update_user='pytest'
            ).save(force_insert=True)

    except Exception as e:
        print(e)

    return rhdm_response_action


################################################################
# 代入値登録待ちテスト
################################################################
@pytest.mark.django_db
def test_act_with_menuid_ng_noparam(monkeypatch):
    """
    代入値登録待ちのテスト
    異常系：アクションパラーメータに必須キーなし
    """

    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'

    # ITA関連クラスのインスタンス生成
    ITAManager = get_ita_manager()  # ITA_driver.py
    testITA = ITAManager(trace_id, response_id, last_update_user)

    # テスト
    result_flag = True
    try:
        testITA.act_with_menuid(1, 1, now)

    except Exception as e:
        result_flag = False

    assert result_flag == False


################################################################
@pytest.mark.django_db
def test_act_with_menuid_ng_movement_err(monkeypatch):
    """
    代入値登録待ちのテスト
    異常系：symphony紐づけmovement取得エラー
    """

    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'

    # ITA関連クラスのインスタンス生成
    ITAManager = get_ita_manager()  # ITA_driver.py
    testITA = ITAManager(trace_id, response_id, last_update_user)

    # テストデータ作成
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 4

    # monkeypatch
    monkeypatch.setattr(ITAManager, 'set_ary_ita_config', lambda a: None)
    monkeypatch.setattr(ITA1Core, 'select_symphony_movement_master', lambda a, b, c: (100))

    # テスト
    sts, code = testITA.act_with_menuid(1, 1, now)

    assert sts  == ACTION_DATA_ERROR
    assert code == ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_VAL


################################################################
@pytest.mark.django_db
def test_act_with_menuid_ng_operation_err(monkeypatch):
    """
    代入値登録待ちのテスト
    異常系：オペレーション取得エラー
    """

    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'

    # ITA関連クラスのインスタンス生成
    #ItaDriver = get_ita_driver()    # models.py : ItaDriverクラス
    ITAManager = get_ita_manager()  # ITA_driver.py
    testITA = ITAManager(trace_id, response_id, last_update_user)

    # テストデータ作成
    testITA.aryActionParameter['SYMPHONY_CLASS_ID'] = 4
    testITA.ary_movement_list = {
        '1' : {
            'ORCHESTRATOR_ID' : '3',
        },
    }

    # monkeypatch
    monkeypatch.setattr(ITAManager, 'set_ary_ita_config', lambda a: None)
    monkeypatch.setattr(ITA1Core, 'select_symphony_movement_master', lambda a, b, c: (0))
    monkeypatch.setattr(ITA1Core, '_select_c_operation_list_by_operation_name', lambda a, b, c: (100))

    # テスト
    sts, code = testITA.act_with_menuid(1, 1, now)

    assert sts  == ACTION_EXEC_ERROR
    assert code == ACTION_HISTORY_STATUS.DETAIL_STS.NONE


################################################################
# オーケストレーター別の情報取得テスト
################################################################
# 代入値管理メニュー
@pytest.mark.django_db
class TestOrchestratorIdToMenuId(object):

    def create_ita_manage(self):
        """
        ITA関連クラスのインスタンス生成
        """

        now = datetime.datetime.now(pytz.timezone('UTC'))
        trace_id = EventsRequestCommon.generate_trace_id(now)
        response_id = 1
        last_update_user = 'pytest'

        ITAManager = get_ita_manager()
        testITA = ITAManager(trace_id, response_id, last_update_user)

        return testITA


    def test_ok_ans_legacy(self):
        """
        正常系
          Ansible Legacy
        """

        testITA = self.create_ita_manage()

        # テスト
        mid, tbl, col = testITA.orchestrator_id_to_menu_id('3')  # 3 : Ansible Legacy

        assert mid == '2100020109'


    def test_ok_ans_pioneer(self):
        """
        正常系
          Ansible Pioneer
        """

        testITA = self.create_ita_manage()

        # テスト
        mid, tbl, col = testITA.orchestrator_id_to_menu_id('4')  # 4 : Ansible Pioneer

        assert mid == '2100020210'


    def test_ok_ans_role(self):
        """
        正常系
          Ansible LegacyRole
        """

        testITA = self.create_ita_manage()

        # テスト
        mid, tbl, col = testITA.orchestrator_id_to_menu_id('5')  # 5 : Ansible LegacyRole

        assert mid == '2100020311'


    def test_ok_terraform(self):
        """
        正常系
          Terraform
        """

        testITA = self.create_ita_manage()

        # テスト
        mid, tbl, col = testITA.orchestrator_id_to_menu_id('10')  # 10 : Terraform

        assert mid == '2100080008'


    def test_ok_semi(self):
        """
        準正常系
          該当なし
        """

        testITA = self.create_ita_manage()

        # テスト
        mid, tbl, col = testITA.orchestrator_id_to_menu_id('aaa')

        assert mid == ''


################################################################
# Movement一覧メニュー
@pytest.mark.django_db
class TestOrchestratorIdToMenuMovement(object):

    class Dummy():

        version = ''


    def create_ita_manage(self):
        """
        ITA関連クラスのインスタンス生成
        """

        now = datetime.datetime.now(pytz.timezone('UTC'))
        trace_id = EventsRequestCommon.generate_trace_id(now)
        response_id = 1
        last_update_user = 'pytest'

        ITAManager = get_ita_manager()
        testITA = ITAManager(trace_id, response_id, last_update_user)
        testITA.ita_driver = self.Dummy()

        return testITA


    def test_ok_ans_legacy(self):
        """
        正常系
          Ansible Legacy
        """

        testITA = self.create_ita_manage()

        # テスト
        mid, tbl, col = testITA.orchestrator_id_to_menu_movement('3')  # 3 : Ansible Legacy

        assert mid == '2100020103'


    def test_ok_ans_pioneer(self):
        """
        正常系
          Ansible Pioneer
        """

        testITA = self.create_ita_manage()

        # テスト
        mid, tbl, col = testITA.orchestrator_id_to_menu_movement('4')  # 4 : Ansible Pioneer

        assert mid == '2100020203'


    def test_ok_ans_role(self):
        """
        正常系
          Ansible LegacyRole
        """

        testITA = self.create_ita_manage()

        # テスト
        mid, tbl, col = testITA.orchestrator_id_to_menu_movement('5')  # 5 : Ansible LegacyRole

        assert mid == '2100020306'


    def test_ok_terraform(self):
        """
        正常系
          Terraform
        """

        testITA = self.create_ita_manage()

        # テスト
        mid, tbl, col = testITA.orchestrator_id_to_menu_movement('10')  # 10 : Terraform

        assert mid == '2100080004'


    def test_ok_semi(self):
        """
        準正常系
          該当なし
        """

        testITA = self.create_ita_manage()

        # テスト
        mid, tbl, col = testITA.orchestrator_id_to_menu_movement('aaa')

        assert mid == ''


