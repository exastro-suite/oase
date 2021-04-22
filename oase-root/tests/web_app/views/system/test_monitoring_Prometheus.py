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

monitoring_Prometheus tests

"""

import pytest
import unittest
import datetime
import pytz
import json

from importlib import import_module
from mock import Mock

from django.conf import settings
from django.db import transaction

from django.urls import reverse
from django.http import Http404
from django.test import Client, RequestFactory

from libs.commonlibs.common import Common
from libs.commonlibs import define as defs

from web_app.models.models import User, RuleType, DataObject, PasswordHistory
from web_app.views.system.monitoring_Prometheus.monitoring_Prometheus import PrometheusAdapterInfo

from libs.commonlibs.aes_cipher import AESCipher
from libs.commonlibs.define import *

module = import_module('web_app.models.Prometheus_monitoring_models')
PrometheusAdapter = getattr(module, 'PrometheusAdapter')
PrometheusMatchInfo = getattr(module, 'PrometheusMatchInfo')


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


class DummyRequest():

    user = None


@pytest.fixture(scope='function')
def set_prometheusadapter_data():

    now = datetime.datetime.now(pytz.timezone('UTC'))

    cipher = AESCipher(settings.AES_KEY)
    encrypted_password = cipher.encrypt('pytest')
    pro_adapter = PrometheusAdapter(
        prometheus_adapter_id=999,
        prometheus_disp_name='adapter999',
        uri='aaa',
        username='pytest',
        password=encrypted_password,
        metric='query',
        label='',
        rule_type_id=999,
        last_update_timestamp=now,
        last_update_user='pytest',
    )
    pro_adapter.save(force_insert=True)

    yield

    PrometheusAdapter.objects.filter(prometheus_adapter_id=999).delete()


@pytest.fixture(scope='function')
def set_prometheusmatchInfo_data():

    now = datetime.datetime.now(pytz.timezone('UTC'))

    pro_matchInfo = PrometheusMatchInfo(
        prometheus_match_id=999,
        prometheus_adapter_id=999,
        data_object_id=1,
        prometheus_response_key='instance',
        last_update_timestamp=now,
        last_update_user='pytest',
    )
    pro_matchInfo.save(force_insert=True)

    yield

    PrometheusMatchInfo.objects.filter(prometheus_match_id=999).delete()


@pytest.fixture(scope='function')
def set_ruletype_data():

    now = datetime.datetime.now(pytz.timezone('UTC'))

    rule_type = RuleType(
        rule_type_id=999,
        rule_type_name='pytest',
        summary='summary',
        rule_table_name='id00000000001',
        generation_limit=3,
        group_id='com.oase',
        artifact_id='id00000000001',
        container_id_prefix_staging='testid00000000001',
        container_id_prefix_product='prodid00000000001',
        current_container_id_staging='testid00000000002',
        current_container_id_product='testid00000000002',
        label_count=1,
        unknown_event_notification='0',
        mail_address='',
        servicenow_driver_id=0,
        disuse_flag='0',
        last_update_timestamp=now,
        last_update_user='pytest',
    )
    rule_type.save(force_insert=True)

    yield

    RuleType.objects.filter(rule_type_id=999).delete()


@pytest.fixture(scope='function')
def set_dataobject_data():

    now = datetime.datetime.now(pytz.timezone('UTC'))

    data_object = DataObject(
        data_object_id=999,
        rule_type_id=999,
        conditional_name='pytest',
        label='label0',
        conditional_expression_id=1,
        last_update_timestamp=now,
        last_update_user='pytest',
    )
    data_object.save(force_insert=True)

    yield

    DataObject.objects.filter(data_object_id=999).delete()


class DummyConfigOK(object):

    def get_rule_auth_type(self, menu):

        return {1:[999,], 2:[999,], 3:[]}

    def get_activerule_auth_type(self, menu):

        return {1:[999,], 2:[999,], 3:[]}


class DummyRequestOK(object):

    user_config = DummyConfigOK()


class DummyConfigInactive(object):

    def get_rule_auth_type(self, menu):

        return {1:[999,], 2:[999,], 3:[]}

    def get_activerule_auth_type(self, menu):

        return {1:[], 2:[], 3:[]}


class DummyRequestInactive(object):

    user_config = DummyConfigInactive()


@pytest.mark.django_db
class TestPrometheusAdapterInfo(object):

    def setup_method(self, method):

        # 動的インポート
        adp_id = 2
        mni_id = 1
        name = 'pytest'
        ver = 1
        icon_name = 'pytest'

        self.target = PrometheusAdapterInfo(adp_id, mni_id, name, ver, icon_name)


    @pytest.mark.usefixtures(
        'set_prometheusadapter_data',
        'set_ruletype_data',
        'set_prometheusmatchInfo_data',
        'set_dataobject_data'
    )
    def test_ok(self):
        """
        正常系
        """

        adp = PrometheusAdapterInfo(999, 0, 'pytest', 1, 'pytest_icon')
        prom_list = adp.get_info_list(DummyRequestOK())

        assert len(prom_list) == 1
        assert prom_list[0]['rule_type_id'] == 999


    @pytest.mark.usefixtures(
        'set_prometheusadapter_data',
        'set_ruletype_data',
        'set_prometheusmatchInfo_data',
        'set_dataobject_data'
    )
    def test_ok_inactive(self):
        """
        正常系(廃止ルール)
        """

        adp = PrometheusAdapterInfo(999, 0, 'pytest', 1, 'pytest_icon')
        prom_list = adp.get_info_list(DummyRequestInactive())

        assert len(prom_list) == 1
        assert prom_list[0]['rule_type_id'] == -1


    @pytest.mark.usefixtures(
        'set_prometheusadapter_data',
        'set_ruletype_data',
        'set_prometheusmatchInfo_data',
        'set_dataobject_data'
    )
    def test_ng_rule_not_exists(self):
        """
        異常系(ルール種別なし)
        """

        try:
            adp = PrometheusAdapterInfo(999, 0, 'pytest', 1, 'pytest_icon')
            prom_list = adp.get_info_list(None)

        except Exception as e:
            assert True
            return

        assert False


    @pytest.mark.usefixtures(
        'prometheus_table',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_create_ok(self):

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'            : 999,
            'prometheus_disp_name'  : 'test_disp_name',
            'uri'                   : 'aaa',
            'username'              : 'test_user_name',
            'password'              : 'test_passwd',
            'query'                 : 'pytest',
            'rule_type_id'          : '999',
            'match_list'            : {'1': 'instance'},
            'prometheus_adapter_id' : '0'
        }

        result = self.target.create(json_str,request)
        assert result['status'] == 'success'


    @pytest.mark.usefixtures(
        'prometheus_table',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_create_ng(self):

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'            : 999,
            'prometheus_disp_name'  : 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
            'uri'                   : 'aaa',
            'username'              : 'test_user_name',
            'password'              : 'test_passwd',
            'query'                 : 'pytest',
            'rule_type_id'          : '999',
            'match_list'            : {'1': 'instance'},
            'prometheus_adapter_id' : '0'
        }

        result = self.target.create(json_str,request)
        assert result['status'] == 'failure'


    @pytest.mark.usefixtures(
        'prometheus_table',
        'set_prometheusadapter_data',
        'set_prometheusmatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_update_ok(self):

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'            : 999,
            'prometheus_disp_name'  : 'adapter998',
            'uri'                   : 'aaa',
            'username'              : 'test_user_name',
            'password'              : 'test_passwd',
            'query'                 : 'pytest',
            'rule_type_id'          : '999',
            'match_list'            : {'1': 'instance'},
            'prometheus_adapter_id' : '999'
        }

        result = self.target.update(json_str,request)
        assert result['status'] == 'success'


    @pytest.mark.usefixtures(
        'prometheus_table',
        'set_prometheusadapter_data',
        'set_prometheusmatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_update_none(self):

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'            : 998,
            'prometheus_disp_name'  : 'adapter998',
            'uri'                   : 'bbb',
            'username'              : 'test_user_name',
            'password'              : 'test_passwd',
            'query'                 : 'pytest',
            'rule_type_id'          : '999',
            'match_list'            : {'1': 'instance'},
            'prometheus_adapter_id' : '998'
        }

        result = self.target.update(json_str,request)
        assert result['status'] == 'deleted'


    @pytest.mark.usefixtures(
        'prometheus_table',
        'set_prometheusadapter_data',
        'set_prometheusmatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_update_ng(self):

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'            : 999,
            'prometheus_disp_name'  : 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
            'uri'                   : 'aaa',
            'username'              : 'test_user_name',
            'password'              : 'test_passwd',
            'query'                 : 'pytest',
            'rule_type_id'          : '999',
            'match_list'            : {'1': 'instance'},
            'prometheus_adapter_id' : '999'
        }

        result = self.target.update(json_str,request)
        assert result['status'] == 'failure'


    @pytest.mark.usefixtures(
        'prometheus_table',
        'set_prometheusadapter_data',
        'set_prometheusmatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_delete_ok(self):

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'record_id' : 999,
        }

        result = self.target.delete(json_str,request)
        assert result['status'] == 'success'


    @pytest.mark.usefixtures(
        'prometheus_table',
        'set_prometheusadapter_data',
        'set_prometheusmatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_delete_none(self):

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'record_id' : 998,
        }

        result = self.target.delete(json_str,request)
        assert result['status'] == 'deleted'


    @pytest.mark.usefixtures(
        'prometheus_table',
        'set_prometheusadapter_data',
        'set_prometheusmatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_delete_ng(self):

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'record_id' : 'a',
        }

        result = self.target.delete(json_str,request)
        assert result['status'] == 'failure'


    @pytest.mark.usefixtures(
        'prometheus_table',
        'set_prometheusadapter_data',
        'set_prometheusmatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_ok(self):

        error_msg  = {
            'prometheus_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'query' : '',
            'rule_type_id':'',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'            : 999,
            'prometheus_disp_name'  : 'adapter998',
            'uri'                   : 'bbb',
            'username'              : 'test_user_name',
            'password'              : 'test_passwd',
            'query'                 : 'pytest',
            'rule_type_id'          : '999',
            'match_list'            : {'1': 'instance'},
            'prometheus_adapter_id' : '0'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == False


    @pytest.mark.usefixtures(
        'prometheus_table',
        'set_prometheusadapter_data',
        'set_prometheusmatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_prometheus_disp_name_none(self):

        error_msg  = {
            'prometheus_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'query' : '',
            'rule_type_id':'',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'            : 999,
            'prometheus_disp_name'  : '',
            'uri'                   : 'bbb',
            'username'              : 'test_user_name',
            'password'              : 'test_passwd',
            'query'                 : 'pytest',
            'rule_type_id'          : '999',
            'match_list'            : {'1': 'instance'},
            'prometheus_adapter_id' : '0'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True
        assert error_msg['prometheus_disp_name'] == '必須項目(名前)が入力されていません。入力してください。 (MOSJA26221)\n'


    @pytest.mark.usefixtures(
        'prometheus_table',
        'set_prometheusadapter_data',
        'set_prometheusmatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_prometheus_disp_name_large(self):

        error_msg  = {
            'prometheus_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'query' : '',
            'rule_type_id':'',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'            : 999,
            'prometheus_disp_name'  : 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
            'uri'                   : 'bbb',
            'username'              : 'test_user_name',
            'password'              : 'test_passwd',
            'query'                 : 'pytest',
            'rule_type_id'          : '999',
            'match_list'            : {'1': 'instance'},
            'prometheus_adapter_id' : '0'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True
        assert error_msg['prometheus_disp_name'] == '名前は64文字以内で入力してください。 (MOSJA26222)\n'


    @pytest.mark.usefixtures(
        'prometheus_table',
        'set_prometheusadapter_data',
        'set_prometheusmatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_uri_none(self):

        error_msg  = {
            'prometheus_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'query' : '',
            'rule_type_id':'',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'            : 999,
            'prometheus_disp_name'  : 'aaa',
            'uri'                   : '',
            'username'              : 'test_user_name',
            'password'              : 'test_passwd',
            'query'                 : 'pytest',
            'rule_type_id'          : '999',
            'match_list'            : {'1': 'instance'},
            'prometheus_adapter_id' : '0'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True
        assert error_msg['uri'] == '必須項目(URL)が入力されていません。入力してください。 (MOSJA26224)\n'


    @pytest.mark.usefixtures(
        'prometheus_table',
        'set_prometheusadapter_data',
        'set_prometheusmatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_uri_large(self):

        error_msg  = {
            'prometheus_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'query' : '',
            'rule_type_id':'',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'            : 999,
            'prometheus_disp_name'  : 'aaa',
            'uri'                   : 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
            'username'              : 'test_user_name',
            'password'              : 'test_passwd',
            'query'                 : 'pytest',
            'rule_type_id'          : '999',
            'match_list'            : {'1': 'instance'},
            'prometheus_adapter_id' : '0'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True
        assert error_msg['uri'] == 'URIは512文字以内で入力してください。 (MOSJA26225)\n'


    @pytest.mark.usefixtures(
        'prometheus_table',
        'set_prometheusadapter_data',
        'set_prometheusmatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_username_large(self):

        error_msg  = {
            'prometheus_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'query' : '',
            'rule_type_id':'',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'            : 999,
            'prometheus_disp_name'  : 'aaa',
            'uri'                   : 'bbb',
            'username'              : 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
            'password'              : 'test_passwd',
            'query'                 : 'pytest',
            'rule_type_id'          : '999',
            'match_list'            : {'1': 'instance'},
            'prometheus_adapter_id' : '0'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True
        assert error_msg['username'] == 'ユーザ名は64文字以内で入力してください。 (MOSJA26228)\n'


    @pytest.mark.usefixtures(
        'prometheus_table',
        'set_prometheusadapter_data',
        'set_prometheusmatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_password_add_large(self):

        error_msg  = {
            'prometheus_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'query' : '',
            'rule_type_id':'',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'            : 999,
            'prometheus_disp_name'  : 'aaa',
            'uri'                   : 'bbb',
            'username'              : 'test_user_name',
            'password'              : 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
            'query'                 : 'pytest',
            'rule_type_id'          : '999',
            'match_list'            : {'1': 'instance'},
            'prometheus_adapter_id' : '0'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True
        assert error_msg['password'] == 'パスワードは64文字以内で入力してください。 (MOSJA26231)\n'


    @pytest.mark.usefixtures(
        'prometheus_table',
        'set_prometheusadapter_data',
        'set_prometheusmatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_password_upd_large(self):

        error_msg  = {
            'prometheus_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'query' : '',
            'rule_type_id':'',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'            : 999,
            'prometheus_disp_name'  : 'aaa',
            'uri'                   : 'bbb',
            'username'              : 'test_user_name',
            'password'              : 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
            'query'                 : 'pytest',
            'rule_type_id'          : '999',
            'match_list'            : {'1': 'instance'},
            'prometheus_adapter_id' : '999'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'upd')
        assert error_flag == True
        assert error_msg['password'] == 'パスワードは64文字以内で入力してください。 (MOSJA26231)\n'


    @pytest.mark.usefixtures(
        'prometheus_table',
        'set_prometheusadapter_data',
        'set_prometheusmatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_query_large(self):

        error_msg  = {
            'prometheus_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'query' : '',
            'rule_type_id':'',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'            : 999,
            'prometheus_disp_name'  : 'aaa',
            'uri'                   : 'bbb',
            'username'              : 'test_user_name',
            'password'              : 'test_passwd',
            'query'                 : 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
            'rule_type_id'          : '999',
            'match_list'            : {'1': 'instance'},
            'prometheus_adapter_id' : '999'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True
        assert error_msg['query'] == 'クエリは128文字以内で入力してください。 (MOSJA26242)\n'


    @pytest.mark.usefixtures(
        'prometheus_table',
        'set_prometheusadapter_data',
        'set_prometheusmatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_rule_type_id_not(self):

        error_msg  = {
            'prometheus_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'query' : '',
            'rule_type_id':'',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'            : 999,
            'prometheus_disp_name'  : 'aaa',
            'uri'                   : 'bbb',
            'username'              : 'test_user_name',
            'password'              : 'test_passwd',
            'query'                 : 'pytest',
            'rule_type_id'          : '998',
            'match_list'            : {'1': 'instance'},
            'prometheus_adapter_id' : '999'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True
        assert error_msg['rule_type_id'] == 'ディシジョンテーブル名が存在しません。ディシジョンテーブル画面からファイルをダウンロードし、ルールの設定を行ってください。 (MOSJA26233)\n'


    @pytest.mark.usefixtures(
        'prometheus_table',
        'set_prometheusadapter_data',
        'set_prometheusmatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_match_list_ng_nom(self):

        error_msg  = {
            'prometheus_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'query' : '',
            'rule_type_id': '',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'            : 999,
            'prometheus_disp_name'  : 'aaa',
            'uri'                   : 'bbb',
            'username'              : 'test_user_name',
            'password'              : 'test_passwd',
            'query'                 : 'pytest',
            'rule_type_id'          : '999',
            'match_list'            : {'2': 'instance', '3': 'namespace'},
            'prometheus_adapter_id' : '999'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True


    @pytest.mark.usefixtures(
        'prometheus_table',
        'set_prometheusadapter_data',
        'set_prometheusmatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_match_list_ng_large(self):

        error_msg  = {
            'prometheus_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'query' : '',
            'rule_type_id': '',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'            : 999,
            'prometheus_disp_name'  : 'aaa',
            'uri'                   : 'bbb',
            'username'              : 'test_user_name',
            'password'              : 'test_passwd',
            'query'                 : 'pytest',
            'rule_type_id'          : '999',
            'match_list'            : {'1': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'},
            'prometheus_adapter_id' : '999'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True


    @pytest.mark.usefixtures(
        'prometheus_table',
        'set_prometheusadapter_data',
        'set_prometheusmatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_match_list_ng_nouse(self):

        error_msg  = {
            'prometheus_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'query' : '',
            'rule_type_id': '',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'            : 999,
            'prometheus_disp_name'  : 'aaa',
            'uri'                   : 'bbb',
            'username'              : 'test_user_name',
            'password'              : 'test_passwd',
            'query'                 : 'pytest',
            'rule_type_id'          : '999',
            'match_list'            : {'1': 'aaa'},
            'prometheus_adapter_id' : '999'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True


    @pytest.mark.usefixtures(
        'prometheus_table',
        'set_prometheusadapter_data',
        'set_prometheusmatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_prometheus_disp_name_ng_duplicate(self):

        error_msg  = {
            'prometheus_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'query' : '',
            'rule_type_id': '',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'            : 999,
            'prometheus_disp_name'  : 'adapter999',
            'uri'                   : 'bbb',
            'username'              : 'test_user_name',
            'password'              : 'test_passwd',
            'query'                 : 'pytest',
            'rule_type_id'          : '999',
            'match_list'            : {'1': 'instance'},
            'prometheus_adapter_id' : '0'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True
        assert error_msg['prometheus_disp_name'] == '他のPrometheusアダプタ名と重複しています。修正してください。 (MOSJA26217)\n'


    @pytest.mark.usefixtures(
        'prometheus_table',
        'set_prometheusadapter_data',
        'set_prometheusmatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_uri_ng_duplicate(self):

        error_msg  = {
            'prometheus_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'query' : '',
            'rule_type_id': '',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'            : 999,
            'prometheus_disp_name'  : 'bbb',
            'uri'                   : 'aaa',
            'username'              : 'test_user_name',
            'password'              : 'test_passwd',
            'query'                 : 'pytest',
            'rule_type_id'          : '999',
            'match_list'            : {'1': 'instance'},
            'prometheus_adapter_id' : '0'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True
        assert error_msg['uri'] == 'URIとディシジョンテーブル名の組み合わせが重複しています。URI、またはディシジョンテーブル名を変更してください。 (MOSJA26218)\n'


