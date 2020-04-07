
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

ITA_common.pyのテスト

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
from libs.commonlibs.ITA.ITA_common import *

################################################
# テスト用DB操作
################################################


def set_data_ita_driver(ita_disp_name):
    """
    ITAへの確認機能のテストに必要なデータをDBに登録
    """
    module = import_module('web_app.models.ITA_models')
    ItaDriver = getattr(module, 'ItaDriver')
    ItaActionHistory = getattr(module, 'ItaActionHistory')

    # パスワードを暗号化
    cipher = AESCipher(settings.AES_KEY)

    now = datetime.datetime.now(pytz.timezone('UTC'))
    encrypted_password = cipher.encrypt('pytest')
    url = 'https://pytest-host-name:443/'

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

            ItaActionHistory(
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

    except Exception as e:
        print(e)


def delete_data_for_ita_driver():
    """
    テストで使用したデータの削除
    """
    module = import_module('web_app.models.ITA_models')
    ItaDriver = getattr(module, 'ItaDriver')
    ItaActionHistory = getattr(module, 'ItaActionHistory')

    ItaDriver.objects.filter(last_update_user='pytest',).delete()
    ItaActionHistory.objects.filter(last_update_user='pytest',).delete()


################################################################
# アクションパラメータのバリデーションチェック処理テスト
################################################################
# ITA_NAMEテスト
@pytest.mark.django_db
def test_ita_name_check_ok(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    ITA_NAMEの正常系(DBからドライバー名取得)
    """

    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    # テストデータ設定
    check_info = {'ITA_NAME':ita_disp_name, 'SYMPHONY_CLASS_ID':'1', 'OPERATION_ID':'1'}
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    # テスト実施
    message_list = []
    ita_name_check(check_info, act_info, message_list)
    assert len(message_list) == 0

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_ita_name_check_ok_already(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    ITA_NAMEの正常系(ドライバー名取得済み)
    """

    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    # テストデータ設定
    check_info = {'ITA_NAME':ita_disp_name, 'SYMPHONY_CLASS_ID':'1', 'OPERATION_ID':'1'}
    act_info = {"driver_name": 'ITA', 'action43':True}
    set_data_ita_driver(ita_disp_name)

    # テスト実施
    message_list = []
    ita_name_check(check_info, act_info, message_list)
    assert len(message_list) == 0

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_ita_name_check_ng_nokey(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    ITA_NAMEの異常系(キーなし)
    """

    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    # テストデータ設定
    check_info = {'SYMPHONY_CLASS_ID':'1', 'OPERATION_ID':'1'}
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    # テスト実施
    message_list = []
    ita_name_check(check_info, act_info, message_list)
    assert len(message_list) == 1 and message_list[0]['id'] == 'MOSJA03113'

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_ita_name_check_ng_notexists(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    ITA_NAMEの異常系(存在しない値)
    """

    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    # テストデータ設定
    check_info = {'ITA_NAME':'action00', 'SYMPHONY_CLASS_ID':'1', 'OPERATION_ID':'1'}
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    # テスト実施
    message_list = []
    ita_name_check(check_info, act_info, message_list)
    assert len(message_list) == 1 and message_list[0]['id'] == 'MOSJA03115'

    # テストデータ削除
    delete_data_for_ita_driver()


################################################
# SYMPHONY_CLASS_IDテスト
@pytest.mark.django_db
def test_symphony_class_id_check_ok(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    SYMPHONY_CLASS_IDの正常系
    """

    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    # テストデータ設定
    check_info = {'ITA_NAME':ita_disp_name, 'SYMPHONY_CLASS_ID':'1', 'OPERATION_ID':'1'}
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    # テスト実施
    message_list = []
    symphony_class_id_check(check_info, conditions, message_list)
    assert len(message_list) == 0

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_symphony_class_id_check_ng_nokey(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    SYMPHONY_CLASS_IDの異常系(キーなし)
    """

    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    # テストデータ設定
    check_info = {'ITA_NAME':ita_disp_name, 'OPERATION_ID':'1'}
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    # テスト実施
    message_list = []
    symphony_class_id_check(check_info, conditions, message_list)
    assert len(message_list) == 1 and message_list[0]['id'] == 'MOSJA03113'

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_symphony_class_id_check_ng_noval(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    SYMPHONY_CLASS_IDの異常系(値なし)
    """

    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    # テストデータ設定
    check_info = {'ITA_NAME':ita_disp_name, 'SYMPHONY_CLASS_ID':'', 'OPERATION_ID':'1'}
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    # テスト実施
    message_list = []
    symphony_class_id_check(check_info, conditions, message_list)
    assert len(message_list) == 1 and message_list[0]['id'] == 'MOSJA03116'

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_symphony_class_id_check_ng_reserved(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    SYMPHONY_CLASS_IDの異常系(存在しない予約変数)
    """

    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    # テストデータ設定
    check_info = {'ITA_NAME':ita_disp_name, 'SYMPHONY_CLASS_ID':'{{ VAR_条件0 }}', 'OPERATION_ID':'1'}
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    # テスト実施
    message_list = []
    symphony_class_id_check(check_info, conditions, message_list)
    assert len(message_list) == 1 and message_list[0]['id'] == 'MOSJA03137'

    # テストデータ削除
    delete_data_for_ita_driver()


################################################
# OPERATION_IDテスト
@pytest.mark.django_db
def test_operation_id_check_ok(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    OPERATION_ID使用時の正常系
    """

    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    # テストデータ設定
    check_info = {'ITA_NAME':ita_disp_name, 'SYMPHONY_CLASS_ID':'1', 'OPERATION_ID':'1'}
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    # テスト実施
    message_list = []
    operation_id_check(check_info['OPERATION_ID'], check_info, conditions, message_list)
    assert len(message_list) == 0

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_operation_id_check_ng_noval(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    OPERATION_IDの異常系(値なし)
    """

    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    # テストデータ設定
    check_info = {'ITA_NAME':ita_disp_name, 'SYMPHONY_CLASS_ID':'1', 'OPERATION_ID':''}
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    # テスト実施
    message_list = []
    operation_id_check(check_info['OPERATION_ID'], check_info, conditions, message_list)
    assert len(message_list) == 1 and message_list[0]['id'] == 'MOSJA03140'

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_operation_id_check_ng_reserved(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    OPERATION_IDの異常系(存在しない予約変数)
    """

    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    # テストデータ設定
    check_info = {'ITA_NAME':ita_disp_name, 'SYMPHONY_CLASS_ID':'1', 'OPERATION_ID':'{{ VAR_条件0 }}'}
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    # テスト実施
    message_list = []
    operation_id_check(check_info['OPERATION_ID'], check_info, conditions, message_list)
    assert len(message_list) == 1 and message_list[0]['id'] == 'MOSJA03137'

    # テストデータ削除
    delete_data_for_ita_driver()


################################################
# SERVER_LISTテスト
@pytest.mark.django_db
def test_server_list_check_ok(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    SERVER_LIST使用時の正常系
    """

    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    # テストデータ設定
    check_info = {'ITA_NAME':ita_disp_name, 'SYMPHONY_CLASS_ID':'1', 'SERVER_LIST':'mas-pj-dev'}
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    # テスト実施
    message_list = []
    server_list_check(check_info['SERVER_LIST'], check_info, conditions, message_list)
    assert len(message_list) == 0

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_server_list_check_ng_noval(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    SERVER_LISTの異常系(値なし)
    """

    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    # テストデータ設定
    check_info = {'ITA_NAME':ita_disp_name, 'SYMPHONY_CLASS_ID':'1', 'SERVER_LIST':''}
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    # テスト実施
    message_list = []
    server_list_check(check_info['SERVER_LIST'], check_info, conditions, message_list)
    assert len(message_list) == 1 and message_list[0]['id'] == 'MOSJA03141'

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_server_list_check_ng_reserved(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    SERVER_LISTの異常系(存在しない予約変数)
    """

    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    # テストデータ設定
    check_info = {'ITA_NAME':ita_disp_name, 'SYMPHONY_CLASS_ID':'1', 'SERVER_LIST':'{{ VAR_条件0 }}'}
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    # テスト実施
    message_list = []
    server_list_check(check_info['SERVER_LIST'], check_info, conditions, message_list)
    assert len(message_list) == 1 and message_list[0]['id'] == 'MOSJA03137'

    # テストデータ削除
    delete_data_for_ita_driver()


################################################
# MENU_IDテスト
@pytest.mark.django_db
def test_menu_id_check_ok(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    MENU_ID使用時の正常系
    """

    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    # テストデータ設定
    check_info = {'ITA_NAME':ita_disp_name, 'SYMPHONY_CLASS_ID':'1', 'MENU_ID':'1', 'CONVERT_FLG':True}
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    # テスト実施
    message_list = []
    menu_id_check(check_info['MENU_ID'], check_info, conditions, message_list)
    assert len(message_list) == 0

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_menu_id_check_ng_menu_id_noval(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    MENU_IDの異常系(値なし)
    """

    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    # テストデータ設定
    check_info = {'ITA_NAME':ita_disp_name, 'SYMPHONY_CLASS_ID':'1', 'MENU_ID':'', 'CONVERT_FLG':True}
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    # テスト実施
    message_list = []
    menu_id_check(check_info['MENU_ID'], check_info, conditions, message_list)
    assert len(message_list) == 1 and message_list[0]['id'] == 'MOSJA03142'

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_menu_id_check_ng_menu_id_reserved(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    MENU_IDの異常系(存在しない予約変数)
    """

    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    # テストデータ設定
    check_info = {'ITA_NAME':ita_disp_name, 'SYMPHONY_CLASS_ID':'1', 'MENU_ID':'{{ VAR_条件0 }}', 'CONVERT_FLG':True}
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    # テスト実施
    message_list = []
    menu_id_check(check_info['MENU_ID'], check_info, conditions, message_list)
    assert len(message_list) == 1 and message_list[0]['id'] == 'MOSJA03137'

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_menu_id_check_ng_convert_flg_nokey(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    MENU_IDの異常系(キーなし)
    """

    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    # テストデータ設定
    check_info = {'ITA_NAME':ita_disp_name, 'SYMPHONY_CLASS_ID':'1', 'MENU_ID':'1'}
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    # テスト実施
    message_list = []
    menu_id_check(check_info['MENU_ID'], check_info, conditions, message_list)
    assert len(message_list) == 1 and message_list[0]['id'] == 'MOSJA03143'

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_menu_id_check_ng_convert_flg_noval(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    MENU_IDの異常系(値なし)
    """

    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    # テストデータ設定
    check_info = {'ITA_NAME':ita_disp_name, 'SYMPHONY_CLASS_ID':'1', 'MENU_ID':'1', 'CONVERT_FLG':''}
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    # テスト実施
    message_list = []
    menu_id_check(check_info['MENU_ID'], check_info, conditions, message_list)
    assert len(message_list) == 1 and message_list[0]['id'] == 'MOSJA03144'

    # テストデータ削除
    delete_data_for_ita_driver()


################################################################
# アクションパラメータ全体のバリデーションチェック処理テスト
################################################################
@pytest.mark.django_db
def test_menu_id_check_ng_reserved(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    MENU_IDの異常系(存在しない予約変数)
    """

    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    # テストデータ設定
    check_info = {'ITA_NAME':ita_disp_name, 'SYMPHONY_CLASS_ID':'1', 'MENU_ID':'{{ VAR_条件0 }}'}
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    # テスト実施
    message_list = []
    server_list_check(check_info['MENU_ID'], check_info, conditions, message_list)
    assert len(message_list) == 1 and message_list[0]['id'] == 'MOSJA03137'

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_check_dt_act_params_ope_id_ok(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    OPERATION_IDの正常系
    """
    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    ############################################
    # 正常テスト(OPERATION_ID版)
    ############################################
    param_list = ['ITA_NAME=action43', 'SYMPHONY_CLASS_ID=1', 'OPERATION_ID=1']
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    message_list = check_dt_action_params(param_list, act_info, conditions)
    assert len(message_list) == 0

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_check_dt_act_params_ope_id_reserved_ok(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    OPERATION_ID・予約変数使用時の正常系
    """
    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    ############################################
    # 正常テスト(OPERATION_ID版 予約変数使用)
    ############################################
    param_list = ['ITA_NAME=action43',
                  'SYMPHONY_CLASS_ID={{ VAR_条件1 }}', 'OPERATION_ID={{ VAR_条件2 }}']
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    message_list = check_dt_action_params(param_list, act_info, conditions)
    assert len(message_list) == 0

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_check_dt_act_params_server_list_ok(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    SERVER_LISTの正常系
    """
    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    ############################################
    # 正常テスト(SERVER_LIST版)
    ############################################
    param_list = ['ITA_NAME=action43',
                  'SYMPHONY_CLASS_ID=1', 'SERVER_LIST=mas-pj-dev']
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    message_list = check_dt_action_params(param_list, act_info, conditions)
    assert len(message_list) == 0

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_check_dt_act_params_server_list_reserved_ok(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    SERVER_LIST・予約変数使用時の正常系
    """
    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    ############################################
    # 正常テスト(SERVER_LIST版 予約変数使用)
    ############################################
    param_list = ['ITA_NAME=action43',
                  'SYMPHONY_CLASS_ID={{ VAR_条件1 }}', 'SERVER_LIST={{ VAR_条件2 }}']
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    message_list = check_dt_action_params(param_list, act_info, conditions)
    assert len(message_list) == 0

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_check_dt_act_params_ita_name_ng_nokey(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    ITA_NAMEの異常系(キーなし)
    """
    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    ############################################
    # 異常テスト(ITA_NAMEのキーなし)
    ############################################
    expected_msg = {'id': 'MOSJA03113', 'param': 'ITA_NAME'}
    param_list = ['SYMPHONY_CLASS_ID=1', 'SERVER_LIST=mas-pj-dev']
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    message_list = check_dt_action_params(param_list, act_info, conditions)
    assert len(message_list) == 1
    assert message_list[0] == expected_msg

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_check_dt_act_params_ita_name_ng_notexists(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    ITA_NAMEの異常系(存在しない値)
    """
    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    ############################################
    # 異常テスト(ITA_NAMEの値差異)
    ############################################
    expected_msg = {'id': 'MOSJA03115', 'param': None}
    act_info = {"driver_name": 'ITA'}
    param_list = ['ITA_NAME=action44',
                  'SYMPHONY_CLASS_ID=1', 'SERVER_LIST=mas-pj-dev']
    set_data_ita_driver(ita_disp_name)

    message_list = check_dt_action_params(param_list, act_info, conditions)
    assert len(message_list) == 1
    assert message_list[0] == expected_msg

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_check_dt_act_params_symphony_class_id_ng_nokey(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    SYMPHONY_CLASS_IDの異常系(キーなし)
    """
    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}
    ############################################
    # 異常テスト(SYMPHONY_CLASS_IDのキーなし)
    ############################################
    expected_msg = {'id': 'MOSJA03113', 'param': 'SYMPHONY_CLASS_ID'}
    param_list = ['ITA_NAME=action43', 'SERVER_LIST=mas-pj-dev']
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    message_list = check_dt_action_params(param_list, act_info, conditions)
    assert len(message_list) == 1
    assert message_list[0] == expected_msg

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_check_dt_act_params_symphony_class_id_ng_noval(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    SYMPHONY_CLASS_IDの異常系(値なし)
    """
    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}
    ############################################
    # 異常テスト(SYMPHONY_CLASS_IDの値なし)
    ############################################
    expected_msg = {'id': 'MOSJA03116', 'param': None}
    param_list = ['ITA_NAME=action43',
                  'SYMPHONY_CLASS_ID=', 'SERVER_LIST=mas-pj-dev']
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    message_list = check_dt_action_params(param_list, act_info, conditions)
    assert len(message_list) == 1
    assert message_list[0] == expected_msg

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_check_dt_act_params_symphony_class_id_ng_reserved(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    SYMPHONY_CLASS_IDの異常系(予約変数誤り)
    """
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}
    ############################################
    # 異常テスト(SYMPHONY_CLASS_IDの予約変数誤り)
    ############################################
    expected_msg = {'id': 'MOSJA03137', 'param': 'SYMPHONY_CLASS_ID'}
    param_list = ['ITA_NAME=action43',
                  'SYMPHONY_CLASS_ID={{ VAR_条件1  }}', 'SERVER_LIST=mas-pj-dev']
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    message_list = check_dt_action_params(param_list, act_info, conditions)
    assert len(message_list) == 1
    assert message_list[0] == expected_msg

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_check_dt_action_params(ita_table):
    """
    アクションパラメータのバリデーションチェック処理テスト
    """

    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    conditions = {'条件1', '条件2'}

    ############################################
    # 異常テスト(OPERATION_IDとSERVER_LISTが共存)
    ############################################
    expected_msg = {'id': 'MOSJA03139', 'param': 'OPERATION_ID, SERVER_LIST, MENU_ID'}
    param_list = ['ITA_NAME=action43', 'SYMPHONY_CLASS_ID=1',
                  'OPERATION_ID=1', 'SERVER_LIST=mas-pj-dev']
    act_info = {"driver_name": 'ITA'}
    set_data_ita_driver(ita_disp_name)

    message_list = check_dt_action_params(param_list, act_info, conditions)
    assert len(message_list) == 1
    assert message_list[0] == expected_msg

    # テストデータ削除
    delete_data_for_ita_driver()

    ############################################
    # 正常テスト(OPERATION_IDとSERVER_LISTが存在しない)
    ############################################
    expected_msg = {'id': 'MOSJA03113', 'param': 'OPERATION_ID or SERVER_LIST'}
    param_list = ['ITA_NAME=action43', 'SYMPHONY_CLASS_ID=1']
    set_data_ita_driver(ita_disp_name)

    message_list = check_dt_action_params(param_list, act_info, conditions)
    assert len(message_list) == 0

    # テストデータ削除
    delete_data_for_ita_driver()

    ############################################
    # 異常テスト(SYMPHONY_CLASS_IDの予約変数誤り)
    ############################################
    expected_msg = {'id': 'MOSJA03137', 'param': 'OPERATION_ID'}
    param_list = ['ITA_NAME=action43',
                  'SYMPHONY_CLASS_ID=1', 'OPERATION_ID={{ VAR条件2 }}']
    set_data_ita_driver(ita_disp_name)

    message_list = check_dt_action_params(param_list, act_info, conditions)
    assert len(message_list) == 1
    assert message_list[0] == expected_msg

    # テストデータ削除
    delete_data_for_ita_driver()

    ############################################
    # 異常テスト(SERVER_LISTの予約変数誤り)
    ############################################
    expected_msg = {'id': 'MOSJA03137', 'param': 'SERVER_LIST'}
    param_list = ['ITA_NAME=action43',
                  'SYMPHONY_CLASS_ID=1', 'SERVER_LIST={{ VA_条件1 }}']
    set_data_ita_driver(ita_disp_name)

    message_list = check_dt_action_params(param_list, act_info, conditions)
    assert len(message_list) == 1
    assert message_list[0] == expected_msg

    # テストデータ削除
    delete_data_for_ita_driver()


@pytest.mark.django_db
def test_get_history_data_ok(ita_table):
    """
    ITAアクション履歴の取得処理テスト
    ACTION_HIS_IDの正常系
    """

    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    set_data_ita_driver(ita_disp_name)
    action_his_id = 1
    result = get_history_data(action_his_id)

    assert len(result) > 0
    assert result['MOSJA13023'] == ita_disp_name
    assert result['MOSJA13024'] == 1
    assert result['MOSJA13025'] == 1
    assert result['MOSJA13026'] == 1
    assert result['MOSJA13027'] == 'https://pytest-host-name:443/'
    assert result['MOSJA13028'] == None

    # テストデータ削除
    delete_data_for_ita_driver()

@pytest.mark.django_db
def test_get_history_data_ng_notexists(ita_table):
    """
    ITAアクション履歴の取得処理テスト
    ACTION_HIS_IDの異常系(存在しない値)
    """

    # テストデータ初期化
    delete_data_for_ita_driver()
    ita_disp_name = 'action43'
    set_data_ita_driver(ita_disp_name)
    action_his_id = 2
    result = get_history_data(action_his_id)

    assert len(result) == 0
