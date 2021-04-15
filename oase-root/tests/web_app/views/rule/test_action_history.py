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

from django.urls import reverse
from django.http import Http404
from django.test import Client, RequestFactory

from libs.commonlibs.common import Common
from libs.commonlibs import define as defs
from web_app.models.models import User, PasswordHistory
from web_app.models.models import DriverType, ActionType, ActionHistory, RuleType

from web_app.views.rule import action_history as mod_act_hist


################################################################
# テストデータ
################################################################
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
def actiontype_data():
    """
    アクション種別設定データ作成
    """

    ActionType(
        action_type_id        = 997,
        driver_type_id        = 3,
        disuse_flag           = '0',
        last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user      = 'pytest'
    ).save(force_insert=True)

    ActionType(
        action_type_id        = 998,
        driver_type_id        = 2,
        disuse_flag           = '0',
        last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user      = 'pytest'
    ).save(force_insert=True)

    ActionType(
        action_type_id        = 999,
        driver_type_id        = 1,
        disuse_flag           = '0',
        last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user      = 'pytest'
    ).save(force_insert=True)

    yield

    ActionType.objects.filter(last_update_user='pytest').delete()


@pytest.fixture(scope='function')
def actionhistory_data():
    """
    アクション履歴データ作成
    """

    now = datetime.datetime.now(pytz.timezone('UTC'))

    ActionHistory(
        action_history_id     = 999,
        response_id           = 999,
        trace_id              = 'TOS_pytest',
        rule_type_id          = 999,
        rule_type_name        = 'RuleType_pytest',
        rule_name             = 'Rule_pytest',
        execution_order       = 999,
        action_start_time     = now,
        action_type_id        = 1,
        status                = 3,
        status_detail         = 0,
        status_update_id      = 'StatusID_pytest',
        retry_flag            = False,
        retry_status          = None,
        retry_status_detail   = None,
        action_retry_count    = None,
        last_act_user         = 'pytest',
        last_update_timestamp = now,
        last_update_user      = 'pytest'
    ).save(force_insert=True)

    ActionHistory(
        action_history_id     = 998,
        response_id           = 998,
        trace_id              = 'TOS_pytest',
        rule_type_id          = 998,
        rule_type_name        = 'RuleType_pytest',
        rule_name             = 'Rule_pytest',
        execution_order       = 998,
        action_start_time     = now,
        action_type_id        = 2,
        status                = 6,
        status_detail         = 0,
        status_update_id      = 'StatusID_pytest',
        retry_flag            = False,
        retry_status          = None,
        retry_status_detail   = None,
        action_retry_count    = None,
        last_act_user         = 'pytest',
        last_update_timestamp = now,
        last_update_user      = 'pytest'
    ).save(force_insert=True)

    ActionHistory(
        action_history_id     = 997,
        response_id           = 997,
        trace_id              = 'TOS_pytest',
        rule_type_id          = 997,
        rule_type_name        = 'RuleType_pytest',
        rule_name             = 'Rule_pytest',
        execution_order       = 997,
        action_start_time     = now,
        action_type_id        = 3,
        status                = 3,
        status_detail         = 0,
        status_update_id      = 'StatusID_pytest',
        retry_flag            = False,
        retry_status          = 3,
        retry_status_detail   = 0,
        action_retry_count    = 1,
        last_act_user         = 'pytest',
        last_update_timestamp = now,
        last_update_user      = 'pytest'
    ).save(force_insert=True)

    ActionHistory(
        action_history_id     = -999,
        response_id           = -999,
        trace_id              = 'TOS_pytest',
        rule_type_id          = -999,
        rule_type_name        = 'RuleType_pytest',
        rule_name             = 'Rule_pytest',
        execution_order       = -999,
        action_start_time     = now,
        action_type_id        = 1,
        status                = 3,
        status_detail         = 0,
        status_update_id      = 'StatusID_pytest',
        retry_flag            = False,
        retry_status          = None,
        retry_status_detail   = None,
        action_retry_count    = None,
        last_act_user         = 'pytest',
        last_update_timestamp = now,
        last_update_user      = 'pytest'
    ).save(force_insert=True)

    yield

    ActionHistory.objects.filter(last_update_user='pytest').delete()


@pytest.fixture(scope='function')
def ruletype_data():
    """
    ルール種別データ作成
    """

    now = datetime.datetime.now(pytz.timezone('UTC'))

    RuleType(
        rule_type_id                 = 999,
        rule_type_name               = 'RuleType999_pytest',
        summary                      = 'Summary_pytest',
        rule_table_name              = 'RuleTable999_pytest',
        generation_limit             = 5,
        group_id                     = 999,
        artifact_id                  = 'Artifact_pytest',
        container_id_prefix_staging  = 'PrefixStg_pytest',
        container_id_prefix_product  = 'PrefixPrd_pytest',
        current_container_id_staging = 'Stg_pytest',
        current_container_id_product = 'Prd_pytest',
        label_count                  = 1,
        unknown_event_notification   = '0',
        mail_address                 = None,
        servicenow_driver_id         = None,
        disuse_flag                  = '0',
        last_update_timestamp        = now,
        last_update_user             = 'pytest'
    ).save(force_insert=True)

    RuleType(
        rule_type_id                 = -999,
        rule_type_name               = 'RuleType-999_pytest',
        summary                      = 'Summary_pytest',
        rule_table_name              = 'RuleTable-999_pytest',
        generation_limit             = 5,
        group_id                     = -999,
        artifact_id                  = 'Artifact_pytest',
        container_id_prefix_staging  = 'PrefixStg_pytest',
        container_id_prefix_product  = 'PrefixPrd_pytest',
        current_container_id_staging = 'Stg_pytest',
        current_container_id_product = 'Prd_pytest',
        label_count                  = 1,
        unknown_event_notification   = '0',
        mail_address                 = None,
        servicenow_driver_id         = None,
        disuse_flag                  = '1',
        last_update_timestamp        = now,
        last_update_user             = 'pytest'
    ).save(force_insert=True)

    yield

    RuleType.objects.filter(last_update_user='pytest').delete()


################################################################
# アクション履歴一覧テスト
################################################################
@pytest.mark.django_db
class TestActionHistory(object):

    @pytest.mark.usefixtures('actiontype_data', 'actionhistory_data', 'ruletype_data')
    def test_ok(self):
        """
        アクション履歴一覧
        ※ 正常系
        """

        admin = get_adminstrator()
        response = admin.get(reverse('web_app:rule:action_history'))

        assert response.status_code == 200


################################################################
# アクション履歴検索テスト
################################################################
@pytest.mark.django_db
class TestSearchHistory(object):

    @pytest.mark.usefixtures('actiontype_data', 'actionhistory_data', 'ruletype_data')
    def test_ok_nothing(self):
        """
        アクション履歴検索
        ※ 正常系(無条件)
        """

        req_data = {}
        req_data['search_record'] = {}
        req_data['search_record']['request_info'] = {
            'request_event_start' : '',
            'request_event_end'   : '',
            'request_trace_id'    : '',
            'request_infomation'  : '',
        }

        req_data['search_record']['action_type'] = ''

        req_data['search_record']['action_shared_info'] = {
            'action_start'          : '',
            'action_end'            : '',
            'action_trace_id'       : '',
            'action_decision_table' : '',
            'action_rule'           : '',
            'action_parameter'      : '',
        }

        req_data['search_record']['action_ita_info'] = {
            'action_ita_name'           : '',
            'action_symphony_instance'  : '',
            'action_symphony_class_id'  : '',
            'action_conductor_instance' : '',
            'action_conductor_class_id' : '',
            'action_ita_operation_id'   : '',
            'action_symphony_work_url'  : '',
            'action_conductor_work_url' : '',
            'action_ita_restapi_info'   : '',
            'action_ita_cooperation'    : '',
        }

        req_data['search_record']['action_mail_info'] = {
            'action_mail_template'    : '',
            'action_mail_destination' : '',
        }

        req_data['search_record']['action_servicenow_info'] = {
            'action_servicenow_template' : '',
        }

        admin = get_adminstrator()
        response = admin.post(reverse('web_app:rule:action_history'), req_data)

        assert response.status_code == 200


################################################################
# ドライバー別履歴メソッド取得関数テスト
################################################################
@pytest.mark.django_db
class TestGetGetHistoryDataFunc(object):

    @pytest.mark.usefixtures('actiontype_data')
    def test_ok_ita(self):
        """
        ※ 正常系(ITA)
        """

        result = mod_act_hist._get_get_history_data_func(999)

        assert 'get_history_data' in str(result)


    @pytest.mark.usefixtures('actiontype_data')
    def test_ok_mail(self):
        """
        ※ 正常系(mail)
        """

        result = mod_act_hist._get_get_history_data_func(998)

        assert 'get_history_data' in str(result)


    @pytest.mark.usefixtures('actiontype_data')
    def test_ok_servicenow(self):
        """
        ※ 正常系(ServiceNow)
        """

        result = mod_act_hist._get_get_history_data_func(997)

        assert 'get_history_data' in str(result)


    @pytest.mark.usefixtures('actiontype_data')
    def test_ng_actiontype_doesnotexists(self):
        """
        ※ 異常系(ActionType.DoesNotExist)
        """

        result = mod_act_hist._get_get_history_data_func(-999)

        assert 'lambda' in str(result)


################################################################
# 削除フラグチェック関数テスト
################################################################
@pytest.mark.django_db
class TestChkDisuseFlag(object):

    @pytest.mark.usefixtures('actionhistory_data', 'ruletype_data')
    def test_true(self):
        """
        削除フラグチェック
        ※ 有効
        """

        result = mod_act_hist._chk_disuse_flag(999)

        assert result == True


    @pytest.mark.usefixtures('actionhistory_data', 'ruletype_data')
    def test_false(self):
        """
        削除フラグチェック
        ※ 有効
        """

        result = mod_act_hist._chk_disuse_flag(-999)

        assert result == False



