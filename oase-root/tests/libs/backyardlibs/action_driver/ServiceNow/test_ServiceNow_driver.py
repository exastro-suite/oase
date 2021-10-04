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
from libs.backyardlibs.action_driver.ServiceNow.ServiceNow_core import ServiceNow1Core
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


def get_servicenow_driver():
    """
    ServiceNowDriverクラスを動的に読み込んで返す
    """
    return getattr(import_module('web_app.models.ServiceNow_models'), 'ServiceNowDriver')


def get_servicenow_manager():
    """
    ServiceNowManagerクラスを動的に読み込んで返す
    """
    return getattr(import_module('libs.backyardlibs.action_driver.ServiceNow.ServiceNow_driver'), 'ServiceNowManager')


def get_servicenow_action_history():
    """
    ServiceNowActionHistoryクラスを動的に読み込んで返す
    """
    return getattr(import_module('web_app.models.ServiceNow_models'), 'ServiceNowActionHistory')


################################################
# テスト用DB操作
################################################
def set_data_servicenow_driver(servicenow_disp_name):
    """
    ServiceNowへの確認機能のテストに必要なデータをDBに登録
    """
    ServiceNowDriver = get_servicenow_driver()
    cipher = AESCipher(settings.AES_KEY)
    now = datetime.datetime.now(pytz.timezone('UTC'))
    encrypted_password = cipher.encrypt('pytest')

    try:
        with transaction.atomic():

            # ServiceNowアクションマスタ
            ServiceNowDriver(
                servicenow_disp_name=servicenow_disp_name,
                hostname='pytest-host-name',
                protocol='https',
                port='443',
                username='pytest',
                password=encrypted_password,
                last_update_user='pytest',
                last_update_timestamp=now
            ).save(force_insert=True)

    except Exception as e:
        print(e)


def delete_data_param_information():
    """
    テストで使用したデータの削除
    """
    ServiceNowDriver = get_servicenow_driver()
    ServiceNowActionHistory = get_servicenow_action_history()

    RhdmResponseAction.objects.filter(last_update_user='pytest').delete()
    PreActionHistory.objects.filter(last_update_user='pytest').delete()
    ActionHistory.objects.filter(last_update_user='pytest').delete()
    EventsRequest.objects.filter(last_update_user='pytest').delete()
    ServiceNowDriver.objects.filter(last_update_user='pytest').delete()
    ServiceNowActionHistory.objects.filter(last_update_user='pytest',).delete()


def set_data_for_information(exec_order, servicenow_disp_name, trace_id, parm_info, flg=False):
    """
    テストで使用するデータの生成
    """
    ServiceNowDriver = get_servicenow_driver()
    rhdm_response_action = None
    pre_action_history = None
    servicenow_driver = None
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

            servicenow_driver = ServiceNowDriver(
                servicenow_disp_name=servicenow_disp_name,
                hostname='pytest-host-name',
                protocol='https',
                port='443',
                username='pytest',
                password=encrypted_password,
                count=1,
                proxy='test',
                last_update_timestamp=now,
                last_update_user='pytest',
            )
            servicenow_driver.save(force_insert=True)

            if flg:
                ServiceNowActionHistory = get_servicenow_action_history()
                servicenow_actionhistory = None
                servicenow_actionhistory = ServiceNowActionHistory(
                    action_his_id=action_history.action_history_id,
                    servicenow_disp_name=servicenow_disp_name,
                    sys_id='abcd1234',
                    short_description='aaa',
                    last_update_timestamp=now,
                    last_update_user='pytest',
                )
                servicenow_actionhistory.save(force_insert=True)

    except Exception as e:
        print(e)

    return rhdm_response_action, pre_action_history


@pytest.mark.django_db
def test_set_information():
    """
    ServiceNow情報登録 テスト
    """
    ServiceNowManager = get_servicenow_manager()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = "pytest"
    testServiceNow = ServiceNowManager(trace_id, response_id, last_update_user)

    ############################################
    # 正常終了パターン
    ############################################
    # テストデータ作成 OPERATON_ID
    servicenow_disp_name = 'ServiceNow176'
    parm_info = '{"ACTION_PARAMETER_INFO": ["SERVICENOW_NAME=ServiceNow176"]}'
    rhdm_res_act, pre_action_history = set_data_for_information(
        1, servicenow_disp_name, trace_id, parm_info)
    testServiceNow.aryActionParameter['SERVICENOW_NAME'] = 'ServiceNow176'

    status, detail = testServiceNow.set_information(rhdm_res_act, pre_action_history)
    assert status == 0
    assert detail == 0

    # テストデータ削除
    delete_data_param_information()

    ############################################
    # ServiceNow確認機能　失敗パターン
    ############################################
    # テストデータ作成
    servicenow_disp_name = 'dummy'
    parm_info = '{"ACTION_PARAMETER_INFO": ["SERVICENOW_NAME=ServiceNow176"]}'
    rhdm_res_act, pre_action_history = set_data_for_information(
        1, servicenow_disp_name, trace_id, parm_info)
    testServiceNow.aryActionParameter['SERVICENOW_NAME'] = 'ServiceNow176'

    status, detail = testServiceNow.set_information(rhdm_res_act, pre_action_history)
    assert status != 0
    assert detail != 0

    # テストデータ削除
    delete_data_param_information()


def test_set_action_parameters():
    """
    アクションパラメータ テスト
    """
    ServiceNowManager = get_servicenow_manager()
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
    # テストデータ作成 Operation_id用
    ACTION_PARAMETER_INFO = ['SERVICENOW_NAME=ServiceNow176', 'INCIDENT_STATUS=NEW']
    testServiceNow = ServiceNowManager(trace_id, response_id, last_update_user)
    testServiceNow.aryActionParameter['ACTION_PARAMETER_INFO'] = ACTION_PARAMETER_INFO
    testServiceNow.set_action_parameters(
        testServiceNow.aryActionParameter, exe_order, res_detail_id)

    ############################################
    # 異常終了パターン 1
    ############################################
    # テストデータ作成
    servicenow_disp_name = 'dummy'
    testServiceNow = ServiceNowManager(trace_id, response_id, last_update_user)

    try:
        with pytest.raises(OASEError):
            testServiceNow.set_action_parameters(
                testServiceNow.aryActionParameter, exe_order, res_detail_id)
            assert False
    except:
        assert False


@pytest.mark.django_db
def test_servicenow_action_history_insert():
    """
    ServiceNowアクション履歴登録メソッドのテスト
    insert処理
    """

    ServiceNowDriver = get_servicenow_driver()
    ServiceNowManager = get_servicenow_manager()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    servicenow_disp_name = 'servicenow_test'
    sys_id = 1
    short_desc = 'OASE Event Notify'
    exe_order = 1
    action_history_id = 1

    rhdm_res_act, pre_action_history = set_data_for_information(
        1, servicenow_disp_name, trace_id, '')

    testServiceNow = ServiceNowManager(trace_id, response_id, last_update_user)
    testServiceNow.action_history = ActionHistory.objects.all()[0]

    servicenowacthist = testServiceNow.servicenow_action_history_insert(
        servicenow_disp_name,
        sys_id,
        short_desc,
        exe_order,
        action_history_id
    )

    assert servicenowacthist == None

    delete_data_param_information()


@pytest.mark.django_db
def test_act_ok(monkeypatch):
    """
    ServiceNowアクションを実行メソッドのテスト
    正常系
    """
    ServiceNowDriver = get_servicenow_driver()
    ServiceNowManager = get_servicenow_manager()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    testServiceNow = ServiceNowManager(trace_id, response_id, last_update_user)

    servicenow_disp_name = 'ServiceNow176'
    parm_info = '{"ACTION_PARAMETER_INFO": ["SERVICENOW_NAME=ServiceNow176"]}'
    rhdm_res_act, pre_action_history = set_data_for_information(
        1, servicenow_disp_name, trace_id, parm_info)

    testServiceNow.aryActionParameter['SERVICENOW_NAME'] = 'ServiceNow176'
    testServiceNow.set_information(rhdm_res_act, pre_action_history)
    testServiceNow.servicenow_driver = ServiceNowDriver.objects.get(servicenow_disp_name=servicenow_disp_name)

    monkeypatch.setattr(testServiceNow, 'servicenow_action_history_insert', lambda a, b, c, d: (0))
    monkeypatch.setattr(ServiceNow1Core, 'create_incident', lambda a, b: True)
    status, detai = testServiceNow.act(rhdm_res_act)

    assert status == 2003

    delete_data_param_information()

@pytest.mark.django_db
def test_act_ng(monkeypatch):
    """
    ServiceNowアクションを実行メソッドのテスト
    異常系
    """
    ServiceNowDriver = get_servicenow_driver()
    ServiceNowManager = get_servicenow_manager()
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    servicenow_disp_name = 'dummy'
    testServiceNow = ServiceNowManager(trace_id, response_id, last_update_user)

    testServiceNow.aryActionParameter['SERVICENOW_NAME'] = 'ServiceNow176'
    parm_info = '{"ACTION_PARAMETER_INFO": ["SERVICENOW_NAME=ServiceNow176"]}'
    rhdm_res_act, pre_action_history = set_data_for_information(
        1, servicenow_disp_name, trace_id, parm_info)

    testServiceNow.set_information(rhdm_res_act, pre_action_history)
    testServiceNow.servicenow_driver = ServiceNowDriver.objects.get(servicenow_disp_name=servicenow_disp_name)

    monkeypatch.setattr(testServiceNow, 'servicenow_action_history_insert', lambda a, b, c, d: (0))
    monkeypatch.setattr(ServiceNow1Core, 'create_incident', lambda a, b: False)
    status, detai = testServiceNow.act(rhdm_res_act)

    assert status == ACTION_EXEC_ERROR

    delete_data_param_information()


@pytest.mark.django_db
def test_act_update_workflow_ok(monkeypatch):
    """
    ServiceNow Workflowアクションを実行メソッドのテスト
    正常系
    """

    ServiceNowDriver = get_servicenow_driver()
    ServiceNowManager = get_servicenow_manager()

    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    testServiceNow = ServiceNowManager(trace_id, response_id, last_update_user)

    servicenow_disp_name = 'ServiceNow176'
    parm_info = '{"ACTION_PARAMETER_INFO": ["SERVICENOW_NAME=ServiceNow176", "WORKFLOW_ID=0123456789abcdef"]}'
    rhdm_res_act, pre_action_history = set_data_for_information(
        1, servicenow_disp_name, trace_id, parm_info)

    testServiceNow.aryActionParameter['SERVICENOW_NAME'] = 'ServiceNow176'
    testServiceNow.set_information(rhdm_res_act, pre_action_history)
    testServiceNow.servicenow_driver = ServiceNowDriver.objects.get(servicenow_disp_name=servicenow_disp_name)

    monkeypatch.setattr(testServiceNow, 'servicenow_action_history_insert', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ServiceNow1Core, 'modify_workflow', lambda a, b, c, d: True)
    status, detai = testServiceNow.act_update_workflow(rhdm_res_act, True, False)

    assert status == PROCESSED

    delete_data_param_information()

@pytest.mark.django_db
def test_act_update_workflow_ng(monkeypatch):
    """
    ServiceNow Workflowアクションを実行メソッドのテスト
    異常系
    """

    ServiceNowDriver = get_servicenow_driver()
    ServiceNowManager = get_servicenow_manager()

    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    testServiceNow = ServiceNowManager(trace_id, response_id, last_update_user)

    servicenow_disp_name = 'ServiceNow176'
    parm_info = '{"ACTION_PARAMETER_INFO": ["SERVICENOW_NAME=ServiceNow176", "WORKFLOW_ID=0123456789abcdef"]}'
    rhdm_res_act, pre_action_history = set_data_for_information(
        1, servicenow_disp_name, trace_id, parm_info)

    testServiceNow.aryActionParameter['SERVICENOW_NAME'] = 'ServiceNow176'
    testServiceNow.set_information(rhdm_res_act, pre_action_history)
    testServiceNow.servicenow_driver = ServiceNowDriver.objects.get(servicenow_disp_name=servicenow_disp_name)

    monkeypatch.setattr(testServiceNow, 'servicenow_action_history_insert', lambda a, b, c, d, e: (0))
    monkeypatch.setattr(ServiceNow1Core, 'modify_workflow', lambda a, b, c, d: False)
    status, detai = testServiceNow.act_update_workflow(rhdm_res_act, False, False)

    assert status == SERVER_ERROR

    delete_data_param_information()


@pytest.mark.django_db
def test_act_approval_confirmation_ng(monkeypatch):
    """
    ServiceNow 承認確認メソッドのテスト
    異常系
    """

    ServiceNowDriver = get_servicenow_driver()
    ServiceNowManager = get_servicenow_manager()

    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1
    last_update_user = 'pytest'
    testServiceNow = ServiceNowManager(trace_id, response_id, last_update_user)

    servicenow_disp_name = 'ServiceNow176'
    parm_info = '{"ACTION_PARAMETER_INFO": ["SERVICENOW_NAME=ServiceNow176", "INCIDENT_STATUS=IN_PROGRESS", "WORK_NOTES=対処許可"]}'
    rhdm_res_act, pre_action_history = set_data_for_information(
        1, servicenow_disp_name, trace_id, parm_info)

    testServiceNow.aryActionParameter['SERVICENOW_NAME'] = 'ServiceNow176'
    testServiceNow.set_information(rhdm_res_act, pre_action_history)
    testServiceNow.servicenow_driver = ServiceNowDriver.objects.get(servicenow_disp_name=servicenow_disp_name)

    monkeypatch.setattr(ServiceNow1Core, 'get_incident', lambda a, b, c: True)
    status, detai = testServiceNow.act_approval_confirmation(rhdm_res_act, True, False)

    assert status == SERVER_ERROR

    delete_data_param_information()

