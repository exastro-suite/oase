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

ServiceNow_common.pyのテスト

"""

import pytest
import os
import django
import configparser
import datetime
import traceback
import pytz
import traceback

from unittest.mock import MagicMock, patch
from importlib import import_module
from django.conf import settings
from django.db import transaction

from libs.commonlibs.aes_cipher import AESCipher
from libs.commonlibs.ServiceNow.ServiceNow_common import *

################################################
# テスト用DB操作
################################################

def set_data_servicenow_driver(servicenow_disp_name):
    """
    ServiceNowへの確認機能のテストに必要なデータをDBに登録
    """
    module = import_module('web_app.models.ServiceNow_models')
    ServiceNowDriver = getattr(module, 'ServiceNowDriver')
    ServiceNowActionHistory = getattr(module, 'ServiceNowActionHistory')

    # パスワードを暗号化
    cipher = AESCipher(settings.AES_KEY)

    now = datetime.datetime.now(pytz.timezone('UTC'))
    encrypted_password = cipher.encrypt('pytest')

    try:
        with transaction.atomic():

            # ServiceNowアクションマスタ
            ServiceNowDriver(
                servicenow_disp_name=servicenow_disp_name,
                protocol='https',
                hostname='pytest-host-name',
                port=443,
                username='pytest',
                password=encrypted_password,
                count=0,
                proxy='http://proxy.example.com:8080',
                last_update_user='pytest',
                last_update_timestamp=now
            ).save(force_insert=True)

            ServiceNowActionHistory(
                servicenow_action_his_id=1,
                action_his_id=1,
                servicenow_disp_name=servicenow_disp_name,
                short_description='OASE Event Notify',
                last_update_timestamp=now,
                last_update_user='pytest'
            ).save(force_insert=True)

    except Exception as e:
        print(e)


def delete_data_for_servicenow_driver():
    """
    テストで使用したデータの削除
    """
    module = import_module('web_app.models.ServiceNow_models')
    ItaDriver = getattr(module, 'ServiceNowDriver')
    ItaActionHistory = getattr(module, 'ServiceNowActionHistory')

    ServiceNowDriver.objects.filter(last_update_user='pytest',).delete()
    ServiceNowActionHistory.objects.filter(last_update_user='pytest',).delete()


################################################################
# アクションパラメータのバリデーションチェック処理テスト
################################################################
# SERVICENOW_NAMEテスト
@pytest.mark.django_db
def test_servicenow_name_check_ok(servicenow_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    SERVICENOW_NAMEの正常系(DBからドライバー名取得)
    """

    # テストデータ初期化
    delete_data_for_servicenow_driver()
    servicenow_disp_name = 'test_servicenow'

    # テストデータ設定
    check_info = {'SERVICENOW_NAME':servicenow_disp_name}
    act_info = {"driver_name": 'ServiceNow'}
    set_data_servicenow_driver(servicenow_disp_name)

    # テスト実施
    message_list = []
    servicenow_name_check(check_info, act_info, message_list)
    assert len(message_list) == 0

    # テストデータ削除
    delete_data_for_servicenow_driver()


@pytest.mark.django_db
def test_servicenow_name_check_ok_already(servicenow_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    SERVICENOW_NAMEの正常系(ドライバー名取得済み)
    """

    # テストデータ初期化
    delete_data_for_servicenow_driver()
    servicenow_disp_name = 'test_servicenow'

    # テストデータ設定
    check_info = {'SERVICENOW_NAME':servicenow_disp_name}
    act_info = {"driver_name": 'ServiceNow', 'test_servicenow':True}
    set_data_servicenow_driver(servicenow_disp_name)

    # テスト実施
    message_list = []
    servicenow_name_check(check_info, act_info, message_list)
    assert len(message_list) == 0

    # テストデータ削除
    delete_data_for_servicenow_driver()


@pytest.mark.django_db
def test_servicenow_name_check_ng_nokey(servicenow_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    SERVICENOW_NAMEの異常系(キーなし)
    """

    # テストデータ初期化
    delete_data_for_servicenow_driver()
    servicenow_disp_name = 'test_servicenow'

    # テストデータ設定
    check_info = {}
    act_info = {"driver_name": 'ServiceNow'}
    set_data_servicenow_driver(servicenow_disp_name)

    # テスト実施
    message_list = []
    servicenow_name_check(check_info, act_info, message_list)
    assert len(message_list) == 1 and message_list[0]['id'] == 'MOSJA03113'

    # テストデータ削除
    delete_data_for_servicenow_driver()


@pytest.mark.django_db
def test_servicenow_name_check_ng_notexists(servicenow_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    SERVICENOW_NAMEの異常系(存在しない値)
    """

    # テストデータ初期化
    delete_data_for_servicenow_driver()
    servicenow_disp_name = 'test_servicenow'

    # テストデータ設定
    check_info = {'SERVICENOW_NAME':'action00'}
    act_info = {"driver_name": 'ServiceNow'}
    set_data_servicenow_driver(servicenow_disp_name)

    # テスト実施
    message_list = []
    servicenow_name_check(check_info, act_info, message_list)
    assert len(message_list) == 1 and message_list[0]['id'] == 'MOSJA03148'

    # テストデータ削除
    delete_data_for_servicenow_driver()


@pytest.mark.django_db
def test_get_history_data_ok(servicenow_table):
    """
    ServiceNowアクション履歴の取得処理テスト
    ACTION_HIS_IDの正常系
    """

    # テストデータ初期化
    delete_data_for_servicenow_driver()
    servicenow_disp_name = 'test_servicenow'
    set_data_servicenow_driver(servicenow_disp_name)
    action_his_id = 1
    result = get_history_data(action_his_id)

    assert len(result) > 0
    assert result['MOSJA13088'] == servicenow_disp_name
    assert result['MOSJA13089'] == 'OASE Event Notify'

    # テストデータ削除
    delete_data_for_servicenow_driver()


@pytest.mark.django_db
def test_get_history_data_ng_notexists(servicenow_table):
    """
    ServiceNowアクション履歴の取得処理テスト
    ACTION_HIS_IDの異常系(存在しない値)
    """

    # テストデータ初期化
    delete_data_for_servicenow_driver()
    servicenow_disp_name = 'test_servicenow'
    set_data_servicenow_driver(servicenow_disp_name)
    action_his_id = 2
    result = get_history_data(action_his_id)

    assert len(result) == 0


@pytest.mark.django_db
def test_incident_status_check_ok_open(servicenow_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    INCIDENT_STATUS(OPEN)の正常系
    """

    # テストデータ初期化
    delete_data_for_servicenow_driver()
    servicenow_disp_name = 'test_servicenow'

    # テストデータ設定
    incident_status = 'OPEN'
    check_info = {'SERVICENOW_NAME':servicenow_disp_name, 'INCIDENT_STATUS':'OPEN'}
    set_data_servicenow_driver(servicenow_disp_name)

    # テスト実施
    message_list = []
    incident_status_check(incident_status, check_info, message_list)
    assert len(message_list) == 0

    # テストデータ削除
    delete_data_for_servicenow_driver()


@pytest.mark.django_db
def test_incident_status_check_ok_close(servicenow_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    INCIDENT_STATUS(CLOSE)の正常系
    """

    # テストデータ初期化
    delete_data_for_servicenow_driver()
    servicenow_disp_name = 'test_servicenow'

    # テストデータ設定
    incident_status = 'CLOSE'
    check_info = {'SERVICENOW_NAME':servicenow_disp_name, 'INCIDENT_STATUS':'CLOSE'}
    set_data_servicenow_driver(servicenow_disp_name)

    # テスト実施
    message_list = []
    incident_status_check(incident_status, check_info, message_list)
    assert len(message_list) == 0

    # テストデータ削除
    delete_data_for_servicenow_driver()


@pytest.mark.django_db
def test_incident_status_check_ng_no_value(servicenow_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    INCIDENT_STATUSの異常系(値なし)
    """

    # テストデータ初期化
    delete_data_for_servicenow_driver()
    servicenow_disp_name = 'test_servicenow'

    # テストデータ設定
    incident_status = ''
    check_info = {'SERVICENOW_NAME':servicenow_disp_name, 'INCIDENT_STATUS':''}
    set_data_servicenow_driver(servicenow_disp_name)

    # テスト実施
    message_list = []
    incident_status_check(incident_status, check_info, message_list)
    assert len(message_list) == 1 and message_list[0]['id'] == 'MOSJA03161'

    # テストデータ削除
    delete_data_for_servicenow_driver()


@pytest.mark.django_db
def test_incident_status_check_ng_notexists(servicenow_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    INCIDENT_STATUSの異常系(値間違え)
    """

    # テストデータ初期化
    delete_data_for_servicenow_driver()
    servicenow_disp_name = 'test_servicenow'

    # テストデータ設定
    incident_status = 'STOP'
    check_info = {'SERVICENOW_NAME':servicenow_disp_name, 'INCIDENT_STATUS':'STOP'}
    set_data_servicenow_driver(servicenow_disp_name)

    # テスト実施
    message_list = []
    incident_status_check(incident_status, check_info, message_list)
    assert len(message_list) == 1 and message_list[0]['id'] == 'MOSJA03162'

    # テストデータ削除
    delete_data_for_servicenow_driver()


@pytest.mark.django_db
def test_workflow_id_check_ok(servicenow_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    WORKFLOW_IDの正常系
    """

    # テストデータ初期化
    delete_data_for_servicenow_driver()
    servicenow_disp_name = 'test_servicenow'

    # テストデータ設定
    workflow_id = '1234567890abcdef'
    check_info = {'SERVICENOW_NAME':servicenow_disp_name, 'WORKFLOW_ID':'1234567890abcdef'}
    conditions = {'条件1', '条件2'}
    set_data_servicenow_driver(servicenow_disp_name)

    # テスト実施
    message_list = []
    workflow_id_check(workflow_id, check_info, conditions, message_list)
    assert len(message_list) == 0

    # テストデータ削除
    delete_data_for_servicenow_driver()


@pytest.mark.django_db
def test_workflow_id_check_ng_no_value(servicenow_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    WORKFLOW_IDの異常系(値なし)
    """

    # テストデータ初期化
    delete_data_for_servicenow_driver()
    servicenow_disp_name = 'test_servicenow'

    # テストデータ設定
    workflow_id = ''
    check_info = {'SERVICENOW_NAME':servicenow_disp_name, 'WORKFLOW_ID':''}
    conditions = {'条件1', '条件2'}
    set_data_servicenow_driver(servicenow_disp_name)

    # テスト実施
    message_list = []
    workflow_id_check(workflow_id, check_info, conditions, message_list)
    assert len(message_list) == 1 and message_list[0]['id'] == 'MOSJA03163'

    # テストデータ削除
    delete_data_for_servicenow_driver()


@pytest.mark.django_db
def test_workflow_id_check_ng_reserved(servicenow_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    WORKFLOW_IDの異常系(存在しない予約変数)
    """

    # テストデータ初期化
    delete_data_for_servicenow_driver()
    servicenow_disp_name = 'test_servicenow'

    # テストデータ設定
    workflow_id = '{{ VAR_条件0 }}'
    check_info = {'SERVICENOW_NAME':servicenow_disp_name, 'WORKFLOW_ID':'{{ VAR_条件0 }}'}
    conditions = {'条件1', '条件2'}
    set_data_servicenow_driver(servicenow_disp_name)

    # テスト実施
    message_list = []
    workflow_id_check(workflow_id, check_info, conditions, message_list)
    assert len(message_list) == 1 and message_list[0]['id'] == 'MOSJA03137'

    # テストデータ削除
    delete_data_for_servicenow_driver()

