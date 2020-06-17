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
def ITAparamsheet_drivertype_data():
    """
    アクション種別設定データ作成(正常系テスト用)
    """

    DriverType(
        driver_type_id = 999,
        name = 'ITA',
        version = '1',
        driver_major_version = 1,
        exastro_flag = '1',
        icon_name = 'pytest',
        last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user = 'pytest'
    ).save(force_insert=True)

    yield

    DriverType.objects.filter(driver_type_id=999).delete()

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


@pytest.mark.django_db
class TestITAParamSheet_Select2(object):
    """
    web_app/views/system/ITA_paramsheet.pyの select2 テストクラス
    （render後のtemplate実装内容含めた画面出力結果の確認）
    """

    ###########################################
    # 登録機能テスト
    ###########################################
    @pytest.mark.usefixtures(
        'ita_table',
        'ITAparamsheet_itadriver_data',
        'ITAparamsheet_actiontype_data'
    )
    def test_ok(self, admin):
        """
        抽出条件テーブル登録処理
        ※ 正常系
        """
        admin = get_adminstrator()

        # 登録処理
        json_str = {
            'version' : '1',
            'ita_driver_id' : '999',
            'menu_id' : '1'
        }

        response = admin.post(reverse('web_app:system:paramsheet_select2'), json_str)

        assert response.status_code == 200


    @pytest.mark.usefixtures('ita_table')
    def test_ng_notexists_menu_id(self, admin):
        """
        抽出条件テーブル登録処理
        ※ 異常系(menu_idなし)
        """
        admin = get_adminstrator()

        # 登録処理
        json_str = {
            'version' : '1',
            'ita_driver_id' : '999',
        }

        response = admin.post(reverse('web_app:system:paramsheet_select2'), json_str)
        content = json.loads(response.content)

        assert response.status_code == 200
        assert content['status'] == 'failure'


