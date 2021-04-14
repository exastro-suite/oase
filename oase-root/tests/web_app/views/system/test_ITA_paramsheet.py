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
  メッセージ解析 tests


"""


import pytest
import unittest
import datetime
import pytz
import json

from importlib import import_module
from mock import Mock

from django.urls import reverse
from django.http import Http404
from django.test import Client, RequestFactory

from libs.commonlibs.common import Common
from libs.commonlibs import define as defs
from web_app.models.models import ActionType, DriverType, User, PasswordHistory

from web_app.views.system.ITA_paramsheet import _get_param_match_info, _make_disp_name, _validate, modify as paramsheet_modify
from web_app.views.system.ITA_paramsheet import _get_param_item_info

def get_adminstrator():
    """
    サイトにログインしwebページをクロールできるシステム管理者を返す
    ユーザデータの加工、セッションの保存の後ログインをしている。
    """
    password = 'OaseTest@1'
    admin = User.objects.get(pk=1)
    admin.password = Common.oase_hash(password)
    admin.last_login = datetime.datetime.now(pytz.timezone('UTC'))
    admin.password_last_modified = datetime.datetime.now(pytz.timezone('UTC'))
    admin.save(force_update=True)

    PasswordHistory.objects.create(
        user_id=1,
        password=Common.oase_hash(password),
        last_update_timestamp=datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user=admin.user_name
    )

    client = Client()
    session = client.session
    session['cookie_age'] = (
        datetime.datetime.now(pytz.timezone('UTC')) +
        datetime.timedelta(minutes=30)
    ).strftime('%Y-%m-%d %H:%M:%S')
    session.save()

    _ = client.login(username='administrator', password=password)

    return client


@pytest.fixture(scope='function')
def ITAparamsheet_actiontype_data():
    """
    アクション種別設定データ作成(正常系テスト用)
    """

    ActionType(
        action_type_id = 999,
        driver_type_id = 1,
        disuse_flag = '0',
        last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user = 'pytest'
    ).save(force_insert=True)

    yield

    ActionType.objects.filter(action_type_id=999).delete()

@pytest.fixture(scope='function')
def ITAparamsheet_itadriver_data():
    """
    アクション設定データ作成(正常系テスト用)
    """

    module = import_module('web_app.models.ITA_models')
    ItaDriver = getattr(module, 'ItaDriver')

    ItaDriver(
        ita_driver_id = 999,
        ita_disp_name = 'ITA_1-3-0_pytest',
        hostname = 'host_pytest',
        username = 'pytest',
        password = 'pytest',
        protocol = 'https',
        port = 443,
        last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user = 'pytest'
    ).save(force_insert=True)

    yield

    ItaDriver.objects.filter(ita_driver_id=999).delete()

@pytest.fixture(scope='function')
def ITAparamsheet_itaparammatchinfo_data():
    """
    ITAパラメータ抽出条件データ作成(正常系テスト用)
    """

    module = import_module('web_app.models.ITA_models')
    ItaParameterMatchInfo = getattr(module, 'ItaParameterMatchInfo')

    ItaParameterMatchInfo(
        match_id = 999,
        ita_driver_id = 999,
        menu_id = 999,
        parameter_name = 'パラメーター名',
        order = 0,
        conditional_name = '条件名',
        extraction_method1 = '',
        extraction_method2 = '',
        last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user = 'pytest'
    ).save(force_insert=True)

    yield

    ItaParameterMatchInfo.objects.filter(match_id=999).delete()

@pytest.fixture(scope='function')
def ITAparamsheet_itamenuname_data():
    """
    ITAパラメータ抽出条件データ作成(正常系テスト用)
    """

    module = import_module('web_app.models.ITA_models')
    ItaMenuName = getattr(module, 'ItaMenuName')

    ItaMenuName(
        ita_menu_name_id = 999,
        ita_driver_id = 999,
        menu_group_id = 999,
        menu_id = 999,
        menu_group_name = 'group',
        menu_name = 'menu',
        last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user = 'pytest'
    ).save(force_insert=True)

    yield

    ItaMenuName.objects.filter(ita_menu_name_id=999).delete()

@pytest.fixture(scope='function')
def ITAparamsheet_itaparammatchinfo_data_forupdate():
    """
    ITAパラメータ抽出条件データ作成(正常系テスト用)
    """

    module = import_module('web_app.models.ITA_models')
    ItaParameterMatchInfo = getattr(module, 'ItaParameterMatchInfo')

    ItaParameterMatchInfo(
        match_id = 1,
        ita_driver_id = 1,
        menu_id = 999,
        parameter_name = 'パラメーター名',
        order = 0,
        conditional_name = '条件名',
        extraction_method1 = '',
        extraction_method2 = '',
        last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user = 'pytest'
    ).save(force_insert=True)

    ItaParameterMatchInfo(
        match_id = 2,
        ita_driver_id = 2,
        menu_id = 999,
        parameter_name = 'パラメーター名',
        order = 0,
        conditional_name = '条件名',
        extraction_method1 = '',
        extraction_method2 = '',
        last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user = 'pytest'
    ).save(force_insert=True)

    yield

    ItaParameterMatchInfo.objects.filter(menu_id = 999).delete()


@pytest.fixture(scope='function')
def ITAparamsheet_paraminfo_data():
    """
    ITAパラメーター項目情報データ作成(正常系テスト用)
    """

    module = import_module('web_app.models.ITA_models')
    ItaParameterItemInfo = getattr(module, 'ItaParameterItemInfo')

    ItaParameterItemInfo(
        ita_driver_id = 999,
        menu_id = 999,
        column_group = 'pytest_col_grp',
        item_name = 'pytest項目名',
        item_number = 99,
        ita_order = 1,
        last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user = 'pytest'
    ).save(force_insert=True)

    yield

    ItaParameterItemInfo.objects.filter(ita_driver_id=1, item_number=99).delete()


@pytest.fixture(scope='function')
def ITAparamsheet_permission_data():
    """
    ITAドライバーのアクセス権限データ作成
    """

    module = import_module('web_app.models.ITA_models')
    ItaPermission = getattr(module, 'ItaPermission')

    ItaPermission(
        ita_permission_id=1,
        ita_driver_id=999,
        group_id=999,
        permission_type_id=1,
        last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user = 'pytest'
    ).save(force_insert=True)

    ItaPermission(
        ita_permission_id=2,
        ita_driver_id=999,
        group_id=1,
        permission_type_id=1,
        last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user = 'pytest'
    ).save(force_insert=True)

    yield

    ItaPermission.objects.filter(last_update_user='pytest').delete()


@pytest.mark.django_db
class TestITAParamSheet(object):
    """
    web_app/views/system/ITA_paramsheet.pyのテストクラス
    （render後のtemplate実装内容含めた画面出力結果の確認）
    """

    ###########################################
    # 共通部分テスト
    ###########################################
    @pytest.mark.usefixtures(
        'ita_table',
        'ITAparamsheet_actiontype_data',
        'ITAparamsheet_itadriver_data',
        'ITAparamsheet_itaparammatchinfo_data',
        'ITAparamsheet_itamenuname_data',
        'ITAparamsheet_permission_data'
    )
    def test_get_param_match_info_ok(self):
        """
        ITAパラメータ抽出条件情報を取得
        ※ 正常系
        """

        data_list, drv_info, menu_info, item_info = _get_param_match_info(
            1,
            [defs.VIEW_ONLY, defs.ALLOWED_MENTENANCE],
            [999,]
        )

        assert len(data_list) > 0

    @pytest.mark.usefixtures(
        'ita_table',
        'ITAparamsheet_actiontype_data',
        'ITAparamsheet_itadriver_data',
        'ITAparamsheet_itaparammatchinfo_data',
        'ITAparamsheet_itamenuname_data'
    )
    def test_get_param_match_info_ng_ver(self):
        """
        ITAパラメータ抽出条件情報を取得
        ※ 異常系(バージョン不一致)
        """

        sts_code = 200

        try:
            data_list, drv_info, menu_info, item_info = _get_param_match_info(
                0,
                [defs.VIEW_ONLY, defs.ALLOWED_MENTENANCE],
                [1]
            )

        except Http404:
            sts_code = 404

        assert sts_code == 404

    @pytest.mark.usefixtures(
        'ita_table',
        'ITAparamsheet_actiontype_data',
        'ITAparamsheet_itadriver_data',
        'ITAparamsheet_itaparammatchinfo_data',
        'ITAparamsheet_itamenuname_data'
    )
    def test_make_disp_name_ok(self):
        """
        文字列結合処理
        ※ 正常系
        """

        module = import_module('web_app.models.ITA_models')
        ItaMenuName = getattr(module, 'ItaMenuName')

        Itaname_dict = ItaMenuName.objects.values('ita_driver_id', 'menu_group_id', 'menu_id', 'menu_group_name', 'menu_name')
        ita_driver_id = 999
        menu_id = 999

        disp_name = _make_disp_name(Itaname_dict, ita_driver_id, menu_id)

        assert len(disp_name) > 0

    @pytest.mark.usefixtures(
        'ita_table',
        'ITAparamsheet_actiontype_data',
        'ITAparamsheet_itadriver_data',
        'ITAparamsheet_itaparammatchinfo_data',
        'ITAparamsheet_itamenuname_data'
    )
    def test_make_disp_name_ng(self):
        """
        文字列結合処理
        ※ データが一致しない場合
        """

        module = import_module('web_app.models.ITA_models')
        ItaMenuName = getattr(module, 'ItaMenuName')

        Itaname_dict = ItaMenuName.objects.values('ita_driver_id', 'menu_group_id', 'menu_id', 'menu_group_name', 'menu_name')
        ita_driver_id = 1
        menu_id = 1

        disp_name = _make_disp_name(Itaname_dict, ita_driver_id, menu_id)

        assert disp_name == None

    @pytest.mark.usefixtures(
        'ita_table',
        'ITAparamsheet_actiontype_data',
        'ITAparamsheet_itadriver_data',
        'ITAparamsheet_itaparammatchinfo_data'
    )
    def test_validate_ok(self):
        """
        バリデーション
        ※ 正常系
        """

        json_str = (
            '{"json_str": ['
            '{"ope": "1",'
            ' "match_id": "999",'
            ' "ita_driver_id": "999",'
            ' "menu_id": "999",'
            ' "parameter_name": "ホスト名",'
            ' "order": "0",'
            ' "conditional_name": "メッセージ本文",'
            ' "extraction_method1": "(?<=(対象ノード|対象ホスト)= )[a-zA-Z0-9_-]+",'
            ' "extraction_method2": "",'
            ' "row_id": "1"}]}'
        )
        json_str = json.loads(json_str)

        records = json_str['json_str']
        version = 1
        request = None

        error_flag, error_msg = _validate(records, version, request)

        assert error_flag == False

    @pytest.mark.usefixtures(
        'ita_table',
        'ITAparamsheet_actiontype_data',
        'ITAparamsheet_itadriver_data',
        'ITAparamsheet_itaparammatchinfo_data'
    )
    def test_validate_ng_matchid(self):
        """
        バリデーション
        ※ 異常系(更新対象match_idなし)
        """

        json_str = (
            '{"json_str": ['
            '{"ope": "2",'
            ' "match_id": "998",'
            ' "ita_driver_id": "999",'
            ' "menu_id": "999",'
            ' "parameter_name": "ホスト名",'
            ' "order": "0",'
            ' "conditional_name": "メッセージ本文",'
            ' "extraction_method1": "(?<=(対象ノード|対象ホスト)= )[a-zA-Z0-9_-]+",'
            ' "extraction_method2": "",'
            ' "row_id": "1"}]}'
        )
        json_str = json.loads(json_str)

        records = json_str['json_str']
        version = 1
        request = None

        error_flag, error_msg = _validate(records, version, request)

        assert 'MOSJA27312' in error_msg['1']['ita_driver_id']

    @pytest.mark.usefixtures(
        'ita_table',
        'ITAparamsheet_actiontype_data',
        'ITAparamsheet_itadriver_data',
        'ITAparamsheet_itaparammatchinfo_data'
    )
    def test_validate_ng_driverid(self):
        """
        バリデーション
        ※ 異常系(指定driver_idなし)
        """

        json_str = (
            '{"json_str": ['
            '{"ope": "2",'
            ' "match_id": "999",'
            ' "ita_driver_id": "0",'
            ' "menu_id": "999",'
            ' "parameter_name": "ホスト名",'
            ' "order": "0",'
            ' "conditional_name": "メッセージ本文",'
            ' "extraction_method1": "(?<=(対象ノード|対象ホスト)= )[a-zA-Z0-9_-]+",'
            ' "extraction_method2": "",'
            ' "row_id": "1"}]}'
        )
        json_str = json.loads(json_str)

        records = json_str['json_str']
        version = 1
        request = None

        error_flag, error_msg = _validate(records, version, request)

        assert 'MOSJA27313' in error_msg['1']['ita_driver_id']

    @pytest.mark.usefixtures(
        'ita_table',
        'ITAparamsheet_actiontype_data',
        'ITAparamsheet_itadriver_data',
        'ITAparamsheet_itaparammatchinfo_data'
    )
    def test_validate_ng_duplicate(self):
        """
        バリデーション
        ※ 異常系(一意制約違反)
        """

        json_str = (
            '{"json_str": ['
            '{"ope": "1",'
            ' "match_id": "999",'
            ' "ita_driver_id": "999",'
            ' "menu_id": "999",'
            ' "parameter_name": "ホスト名",'
            ' "order": "0",'
            ' "conditional_name": "メッセージ本文",'
            ' "extraction_method1": "(?<=(対象ノード|対象ホスト)= )[a-zA-Z0-9_-]+",'
            ' "extraction_method2": "",'
            ' "row_id": "1"},'
            '{"ope": "1",'
            ' "match_id": "998",'
            ' "ita_driver_id": "999",'
            ' "menu_id": "999",'
            ' "parameter_name": "ホスト名",'
            ' "order": "0",'
            ' "conditional_name": "メッセージ本文",'
            ' "extraction_method1": "(?<=(対象ノード|対象ホスト)= )[a-zA-Z0-9_-]+",'
            ' "extraction_method2": "",'
            ' "row_id": "2"}'
            ']}'
        )
        json_str = json.loads(json_str)

        records = json_str['json_str']
        version = 1
        request = None

        error_flag, error_msg = _validate(records, version, request)

        assert 'MOSJA27314' in error_msg['2']['ita_driver_id']

    @pytest.mark.usefixtures(
        'ita_table',
        'ITAparamsheet_actiontype_data',
        'ITAparamsheet_itadriver_data',
        'ITAparamsheet_itaparammatchinfo_data'
    )
    def test_validate_ng_menuid_empty(self):
        """
        バリデーション
        ※ 異常系(menu_id)
        """

        json_str = (
            '{"json_str": ['
            '{"ope": "1",'
            ' "match_id": "999",'
            ' "ita_driver_id": "999",'
            ' "menu_id": "",'
            ' "parameter_name": "ホスト名",'
            ' "order": "0",'
            ' "conditional_name": "メッセージ本文",'
            ' "extraction_method1": "(?<=(対象ノード|対象ホスト)= )[a-zA-Z0-9_-]+",'
            ' "extraction_method2": "",'
            ' "row_id": "1"}]}'
        )
        json_str = json.loads(json_str)

        records = json_str['json_str']
        version = 1
        request = None

        error_flag, error_msg = _validate(records, version, request)

        assert 'MOSJA27317' in error_msg['1']['menu_id']

    @pytest.mark.usefixtures(
        'ita_table',
        'ITAparamsheet_actiontype_data',
        'ITAparamsheet_itadriver_data',
        'ITAparamsheet_itaparammatchinfo_data'
    )
    def test_validate_ng_parametername_empty(self):
        """
        バリデーション
        ※ 異常系(parameter_name)
        """

        json_str = (
            '{"json_str": ['
            '{"ope": "1",'
            ' "match_id": "999",'
            ' "ita_driver_id": "999",'
            ' "menu_id": "999",'
            ' "parameter_name": "",'
            ' "order": "0",'
            ' "conditional_name": "メッセージ本文",'
            ' "extraction_method1": "(?<=(対象ノード|対象ホスト)= )[a-zA-Z0-9_-]+",'
            ' "extraction_method2": "",'
            ' "row_id": "1"}]}'
        )
        json_str = json.loads(json_str)

        records = json_str['json_str']
        version = 1
        request = None

        error_flag, error_msg = _validate(records, version, request)

        assert 'MOSJA27318' in error_msg['1']['parameter_name']

    @pytest.mark.usefixtures(
        'ita_table',
        'ITAparamsheet_actiontype_data',
        'ITAparamsheet_itadriver_data',
        'ITAparamsheet_itaparammatchinfo_data'
    )
    def test_validate_ng_parametername_length(self):
        """
        バリデーション
        ※ 異常系(parameter_name文字列上限を超過)
        """

        param_name = (
            "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890"
            "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890"
            "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890"
        )

        json_str = (
            '{"json_str": ['
            '{"ope": "1",'
            ' "match_id": "999",'
            ' "ita_driver_id": "999",'
            ' "menu_id": "999",'
            ' "parameter_name": "%s",'
            ' "order": "0",'
            ' "conditional_name": "メッセージ本文",'
            ' "extraction_method1": "(?<=(対象ノード|対象ホスト)= )[a-zA-Z0-9_-]+",'
            ' "extraction_method2": "",'
            ' "row_id": "1"}]}'
        ) % (param_name)
        json_str = json.loads(json_str)

        records = json_str['json_str']
        version = 1
        request = None

        error_flag, error_msg = _validate(records, version, request)

        assert 'MOSJA27319' in error_msg['1']['parameter_name']

    @pytest.mark.usefixtures(
        'ita_table',
        'ITAparamsheet_actiontype_data',
        'ITAparamsheet_itadriver_data',
        'ITAparamsheet_itaparammatchinfo_data'
    )
    def test_validate_ng_order_empty(self):
        """
        バリデーション
        ※ 異常系(order)
        """

        json_str = (
            '{"json_str": ['
            '{"ope": "1",'
            ' "match_id": "999",'
            ' "ita_driver_id": "999",'
            ' "menu_id": "999",'
            ' "parameter_name": "ホスト名",'
            ' "order": "",'
            ' "conditional_name": "メッセージ本文",'
            ' "extraction_method1": "(?<=(対象ノード|対象ホスト)= )[a-zA-Z0-9_-]+",'
            ' "extraction_method2": "",'
            ' "row_id": "1"}]}'
        )
        json_str = json.loads(json_str)

        records = json_str['json_str']
        version = 1
        request = None

        error_flag, error_msg = _validate(records, version, request)

        assert 'MOSJA27320' in error_msg['1']['order']

    @pytest.mark.usefixtures(
        'ita_table',
        'ITAparamsheet_actiontype_data',
        'ITAparamsheet_itadriver_data',
        'ITAparamsheet_itaparammatchinfo_data'
    )
    def test_validate_ng_conditionalname_empty(self):
        """
        バリデーション
        ※ 異常系(conditional_name)
        """

        json_str = (
            '{"json_str": ['
            '{"ope": "1",'
            ' "match_id": "999",'
            ' "ita_driver_id": "999",'
            ' "menu_id": "999",'
            ' "parameter_name": "ホスト名",'
            ' "order": "0",'
            ' "conditional_name": "",'
            ' "extraction_method1": "(?<=(対象ノード|対象ホスト)= )[a-zA-Z0-9_-]+",'
            ' "extraction_method2": "",'
            ' "row_id": "1"}]}'
        )
        json_str = json.loads(json_str)

        records = json_str['json_str']
        version = 1
        request = None

        error_flag, error_msg = _validate(records, version, request)

        assert 'MOSJA27321' in error_msg['1']['conditional_name']

    @pytest.mark.usefixtures(
        'ita_table',
        'ITAparamsheet_actiontype_data',
        'ITAparamsheet_itadriver_data',
        'ITAparamsheet_itaparammatchinfo_data'
    )
    def test_validate_ng_conditionalname_length(self):
        """
        バリデーション
        ※ 異常系(conditional_name文字列上限を超過)
        """

        json_str = (
            '{"json_str": ['
            '{"ope": "1",'
            ' "match_id": "999",'
            ' "ita_driver_id": "999",'
            ' "menu_id": "999",'
            ' "parameter_name": "ホスト名",'
            ' "order": "0",'
            ' "conditional_name": "1234567890123456789012345678901234567890",'
            ' "extraction_method1": "(?<=(対象ノード|対象ホスト)= )[a-zA-Z0-9_-]+",'
            ' "extraction_method2": "",'
            ' "row_id": "1"}]}'
        )
        json_str = json.loads(json_str)

        records = json_str['json_str']
        version = 1
        request = None

        error_flag, error_msg = _validate(records, version, request)

        assert 'MOSJA27322' in error_msg['1']['conditional_name']

    @pytest.mark.usefixtures(
        'ita_table',
        'ITAparamsheet_actiontype_data',
        'ITAparamsheet_itadriver_data',
        'ITAparamsheet_itaparammatchinfo_data'
    )
    def test_validate_ng_method1_length(self):
        """
        バリデーション
        ※ 異常系(extraction_method1文字列上限を超過)
        """

        method_val = (
            "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890"
            "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890"
            "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890"
            "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890"
            "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890"
            "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890"
        )

        json_str = (
            '{"json_str": ['
            '{"ope": "1",'
            ' "match_id": "999",'
            ' "ita_driver_id": "999",'
            ' "menu_id": "999",'
            ' "parameter_name": "ホスト名",'
            ' "order": "0",'
            ' "conditional_name": "メッセージ本文",'
            ' "extraction_method1": "%s",'
            ' "extraction_method2": "",'
            ' "row_id": "1"}]}'
        ) % (method_val)
        json_str = json.loads(json_str)

        records = json_str['json_str']
        version = 1
        request = None

        error_flag, error_msg = _validate(records, version, request)

        assert 'MOSJA27323' in error_msg['1']['extraction_method1']

    @pytest.mark.usefixtures(
        'ita_table',
        'ITAparamsheet_actiontype_data',
        'ITAparamsheet_itadriver_data',
        'ITAparamsheet_itaparammatchinfo_data'
    )
    def test_validate_ng_method2_length(self):
        """
        バリデーション
        ※ 異常系(extraction_method2文字列上限を超過)
        """

        method_val = (
            "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890"
            "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890"
            "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890"
            "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890"
            "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890"
            "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890"
        )

        json_str = (
            '{"json_str": ['
            '{"ope": "1",'
            ' "match_id": "999",'
            ' "ita_driver_id": "999",'
            ' "menu_id": "999",'
            ' "parameter_name": "ホスト名",'
            ' "order": "0",'
            ' "conditional_name": "メッセージ本文",'
            ' "extraction_method1": "(?<=(対象ノード|対象ホスト)= )[a-zA-Z0-9_-]+",'
            ' "extraction_method2": "%s",'
            ' "row_id": "1"}]}'
        ) % (method_val)
        json_str = json.loads(json_str)

        records = json_str['json_str']
        version = 1
        request = None

        error_flag, error_msg = _validate(records, version, request)

        assert 'MOSJA27324' in error_msg['1']['extraction_method2']


    @pytest.mark.usefixtures(
        'ita_table',
        'ITAparamsheet_paraminfo_data'
    )
    def test_get_param_item_info_ok(self):
        """
        パラメーター項目情報を取得
        ※正常系
        """

        filter_info = {
            'ita_driver_id' : 999,
            'menu_id' : 999,
        }

        item_info = _get_param_item_info('ItaParameterItemInfo', filter_info)

        assert len(item_info[999][999]) >= 2


    ###########################################
    # 参照画面テスト
    ###########################################
    @pytest.mark.usefixtures('ita_table', 'ITAparamsheet_actiontype_data')
    def test_index_ok(self, admin):
        """
        参照画面表示
        ※ 正常系
        """

        response = admin.get(reverse('web_app:system:paramsheet', args=[1,]))
        content = response.content.decode('utf-8')

        assert response.status_code == 200

    @pytest.mark.usefixtures('ita_table')
    def test_index_ng(self, admin):
        """
        参照画面表示
        ※ 異常系
        """

        response = admin.get(reverse('web_app:system:paramsheet', args=[0,]))
        content = response.content.decode('utf-8')

        assert response.status_code == 404


    ###########################################
    # 編集画面テスト
    ###########################################
    @pytest.mark.usefixtures('ita_table', 'ITAparamsheet_actiontype_data')
    def test_edit_ok(self, admin):
        """
        編集画面表示
        ※ 正常系
        """

        response = admin.post(reverse('web_app:system:paramsheet_edit', args=[1,]))
        content = response.content.decode('utf-8')

        assert response.status_code == 200

    @pytest.mark.usefixtures('ita_table')
    def test_edit_ng(self, admin):
        """
        編集画面表示
        ※ 異常系
        """

        response = admin.post(reverse('web_app:system:paramsheet_edit', args=[0,]))
        content = response.content.decode('utf-8')

        assert response.status_code == 404


    ###########################################
    # 登録機能テスト
    ###########################################
    @pytest.mark.usefixtures('ita_table', 'ITAparamsheet_itaparammatchinfo_data')
    def test_modify_insert_ok(self, admin, monkeypatch):
        """
        抽出条件テーブル登録処理
        ※ 正常系
        """
        admin = get_adminstrator()

        # 登録処理
        json_str = {
            'json_str': [
                {
                    'ope': '1',
                    'match_id': '2',
                    'ita_driver_id': '1',
                    'menu_id': '1',
                    'parameter_name': 'ホスト名',
                    'order': '0',
                    'conditional_name': 'メッセージ本文',
                    'extraction_method1': '対象ノード=(\\w+)',
                    'extraction_method2': '対象ノード=',
                    'row_id': '2'
                },
                {
                    'ope': '1',
                    'match_id': '3',
                    'ita_driver_id': '1',
                    'menu_id': '1',
                    'parameter_name': 'プロセス',
                    'order': '1',
                    'conditional_name': 'メッセージ本文',
                    'extraction_method1': 'pid=\\d*',
                    'extraction_method2': 'pid=',
                    'row_id': '3'
                }
            ]
        }
        json_data = json.dumps(json_str)

        module = getattr(import_module('web_app.views.system'), 'ITA_paramsheet')
        monkeypatch.setattr(module, '_validate', lambda x, y, z: (False, {}))

        response = admin.post(reverse('web_app:system:paramsheet_modify', args=[1,]), {'json_str':json_data})
        assert response.status_code == 200

    @pytest.mark.usefixtures('ita_table', 'ITAparamsheet_itaparammatchinfo_data', 'ITAparamsheet_permission_data')
    def test_modify_insert_ng(self, admin, monkeypatch):
        """
        抽出条件テーブル登録処理
        ※ 異常系
        """
        admin = get_adminstrator()

        with pytest.raises(Exception):
            response = admin.post(path=reverse('web_app:system:paramsheet_modify', args=[0,]), content_type='application/json')
            assert False

        json_str = {
            'json_str': [
                {
                    'ope': '1',
                    'match_id': '2',
                    'ita_driver_id': '999',
                    'menu_id': '1',
                    'parameter_name': 'ホスト名',
                    'order': '0',
                    'conditional_name': 'メッセージ本文',
                    'extraction_method1': '対象ノード=(\\w+)',
                    'extraction_method2': '対象ノード=',
                    'row_id': '2'
                },
                {
                    'ope': '1',
                    'match_id': '3',
                    'ita_driver_id': '999',
                    'menu_id': '1',
                    'parameter_name': 'プロセス',
                    'order': '1',
                    'conditional_name': 'メッセージ本文',
                    'extraction_method1': 'pid=\\d*',
                    'extraction_method2': 'pid=',
                    'row_id': '3'
                }
            ]
        }
        json_data = json.dumps(json_str)

        response = admin.post(reverse('web_app:system:paramsheet_modify', args=[999,]), {'json_str':json_data})
        assert response.status_code == 404

        module = getattr(import_module('web_app.views.system'), 'ITA_paramsheet')
        monkeypatch.setattr(module, '_validate', lambda x, y, z: (True, {'xxx'}))

        with pytest.raises(Exception):
            response = admin.post(reverse('web_app:system:paramsheet_modify', args=[1,]), {'json_str':json_data})
            assert False


    ###########################################
    # 削除機能テスト
    ###########################################
    @pytest.mark.usefixtures('ita_table', 'ITAparamsheet_itaparammatchinfo_data')
    def test_modify_delete_ok(self, admin, monkeypatch):
        """
        抽出条件テーブル削除処理
        ※ 正常系
        """
        admin = get_adminstrator()

        # 削除処理
        json_str = {
            'json_str': [
                {
                    'ope': '3',
                    'match_id': '999',
                    'ita_driver_id': '999',
                    'menu_id': '999',
                    'parameter_name': 'ホスト名',
                    'order': '0',
                    'conditional_name': 'メッセージ本文',
                    'extraction_method1': '対象ノード=(\\w+)',
                    'extraction_method2': '対象ノード=',
                    'row_id': '2'
                }
            ]
        }
        json_data = json.dumps(json_str)

        module = getattr(import_module('web_app.views.system'), 'ITA_paramsheet')
        monkeypatch.setattr(module, '_validate', lambda x, y, z: (False, {}))

        response = admin.post(reverse('web_app:system:paramsheet_modify', args=[1,]), {'json_str':json_data})
        assert response.status_code == 200


    @pytest.mark.usefixtures('ita_table', 'ITAparamsheet_itaparammatchinfo_data', 'ITAparamsheet_permission_data')
    def test_modify_delete_ng(self, admin):
        """
        抽出条件テーブル削除処理
        ※ 異常系
        """
        admin = get_adminstrator()

        # 削除処理
        json_str = {
            'json_str': [
                {
                    'ope': '3',
                    'match_id': '999',
                    'ita_driver_id': '999',
                    'menu_id': '999',
                    'parameter_name': 'ホスト名',
                    'order': '0',
                    'conditional_name': 'メッセージ本文',
                    'extraction_method1': '対象ノード=(\\w+)',
                    'extraction_method2': '対象ノード=',
                    'row_id': '2'
                }
            ]
        }
        json_data = json.dumps(json_str)

        response = admin.post(reverse('web_app:system:paramsheet_modify', args=[999,]), {'json_str':json_data})
        assert response.status_code == 404


    ###########################################
    # 更新機能テスト
    ###########################################
    @pytest.mark.usefixtures('ita_table', 'ITAparamsheet_itaparammatchinfo_data_forupdate')
    def test_modify_update_ok(self, admin, monkeypatch):
        """
        抽出条件テーブル更新処理
        ※ 正常系
        """
        admin = get_adminstrator()

        # 更新処理
        json_str = {
            'json_str': [
                {
                    'ope': '2',
                    'match_id': '1',
                    'ita_driver_id': '1',
                    'menu_id': '999',
                    'parameter_name': 'ホスト名',
                    'order': '0',
                    'conditional_name': 'メッセージ本文',
                    'extraction_method1': '対象ノード=(\\w+)',
                    'extraction_method2': '対象ノード=',
                    'row_id': '2'
                },
                {
                    'ope': '2',
                    'match_id': '2',
                    'ita_driver_id': '2',
                    'menu_id': '999',
                    'parameter_name': 'プロセス',
                    'order': '1',
                    'conditional_name': 'メッセージ本文',
                    'extraction_method1': 'pid=\\d*',
                    'extraction_method2': 'pid=',
                    'row_id': '3'
                }
            ]
        }
        json_data = json.dumps(json_str)

        module = getattr(import_module('web_app.views.system'), 'ITA_paramsheet')
        monkeypatch.setattr(module, '_validate', lambda x, y, z: (False, {}))

        response = admin.post(reverse('web_app:system:paramsheet_modify', args=[1,]), {'json_str':json_data})
        assert response.status_code == 200


    @pytest.mark.usefixtures('ita_table', 'ITAparamsheet_itaparammatchinfo_data_forupdate', 'ITAparamsheet_permission_data')
    def test_modify_update_ng(self, admin):
        """
        抽出条件テーブル更新処理
        ※ 異常系
        """
        admin = get_adminstrator()

        # 更新処理
        json_str = {
            'json_str': [
                {
                    'ope': '2',
                    'match_id': '1',
                    'ita_driver_id': '999',
                    'menu_id': '999',
                    'parameter_name': 'ホスト名',
                    'order': '0',
                    'conditional_name': 'メッセージ本文',
                    'extraction_method1': '対象ノード=(\\w+)',
                    'extraction_method2': '対象ノード=',
                    'row_id': '2'
                },
                {
                    'ope': '2',
                    'match_id': '2',
                    'ita_driver_id': '999',
                    'menu_id': '999',
                    'parameter_name': 'プロセス',
                    'order': '1',
                    'conditional_name': 'メッセージ本文',
                    'extraction_method1': 'pid=\\d*',
                    'extraction_method2': 'pid=',
                    'row_id': '3'
                }
            ]
        }
        json_data = json.dumps(json_str)

        response = admin.post(reverse('web_app:system:paramsheet_modify', args=[999,]), {'json_str':json_data})
        assert response.status_code == 404

    ###########################################
    # 登録・更新・削除機能　複合テスト
    ###########################################
    @pytest.mark.usefixtures('ita_table', 'ITAparamsheet_itaparammatchinfo_data')
    def test_modify_crud_ok(self, admin, monkeypatch):
        """
        抽出条件テーブル登録・変更・削除処理
        ※ 正常系
        """
        admin = get_adminstrator()

        # 登録処理
        json_str = {
            'json_str': [
                {
                    'ope': '1',
                    'match_id': '3',
                    'ita_driver_id': '3',
                    'menu_id': '999',
                    'parameter_name': 'メッセージ',
                    'order': '0',
                    'conditional_name': 'メッセージ本文',
                    'extraction_method1': '対象ノード=(\\w+)',
                    'extraction_method2': '対象ノード=',
                    'row_id': '2'
                },
                {
                    'ope': '2',
                    'match_id': '1',
                    'ita_driver_id': '1',
                    'menu_id': '999',
                    'parameter_name': 'ホスト名',
                    'order': '0',
                    'conditional_name': 'メッセージ本文',
                    'extraction_method1': '対象ノード=(\\w+)',
                    'extraction_method2': '対象ノード=',
                    'row_id': '2'
                },
                {
                    'ope': '3',
                    'match_id': '2',
                    'ita_driver_id': '2',
                    'menu_id': '999',
                    'parameter_name': 'プロセス',
                    'order': '1',
                    'conditional_name': 'メッセージ本文',
                    'extraction_method1': 'pid=\\d*',
                    'extraction_method2': 'pid=',
                    'row_id': '3'
                }
            ]
        }
        json_data = json.dumps(json_str)

        module = getattr(import_module('web_app.views.system'), 'ITA_paramsheet')
        monkeypatch.setattr(module, '_validate', lambda x, y, z: (False, {}))

        response = admin.post(reverse('web_app:system:paramsheet_modify', args=[1,]), {'json_str':json_data})
        assert response.status_code == 200
