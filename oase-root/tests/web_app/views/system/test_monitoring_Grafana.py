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

monitoring_Grafana tests

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
from web_app.views.system.monitoring_Grafana.monitoring_Grafana import GrafanaAdapterInfo

from libs.commonlibs.aes_cipher import AESCipher
from libs.commonlibs.define import *

module = import_module('web_app.models.Grafana_monitoring_models')
GrafanaAdapter = getattr(module, 'GrafanaAdapter')
GrafanaMatchInfo = getattr(module, 'GrafanaMatchInfo')


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
def set_grafanaadapter_data():

    now = datetime.datetime.now(pytz.timezone('UTC'))

    cipher = AESCipher(settings.AES_KEY)
    encrypted_password = cipher.encrypt('pytest')
    pro_adapter = GrafanaAdapter(
        grafana_adapter_id=999,
        grafana_disp_name='adapter999',
        uri='aaa',
        username='pytest',
        password=encrypted_password,
        match_evtime='',
        match_instance='',
        rule_type_id=999,
        last_update_timestamp=now,
        last_update_user='pytest',
    )
    pro_adapter.save(force_insert=True)

    yield

    GrafanaAdapter.objects.filter(grafana_adapter_id=999).delete()


@pytest.fixture(scope='function')
def set_grafanamatchInfo_data():

    now = datetime.datetime.now(pytz.timezone('UTC'))

    pro_matchInfo = GrafanaMatchInfo(
        grafana_match_id=999,
        grafana_adapter_id=999,
        data_object_id=1,
        grafana_response_key='instance',
        last_update_timestamp=now,
        last_update_user='pytest',
    )
    pro_matchInfo.save(force_insert=True)

    yield

    GrafanaMatchInfo.objects.filter(grafana_match_id=999).delete()


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
class TestGrafanaAdapterInfo(object):

    def setup_method(self, method):

        # 動的インポート
        adp_id = 3
        mni_id = 1
        name = 'pytest'
        ver = 1
        icon_name = 'pytest'

        self.target = GrafanaAdapterInfo(adp_id, mni_id, name, ver, icon_name)


    @pytest.mark.usefixtures(
        'set_grafanaadapter_data',
        'set_ruletype_data',
        'set_grafanamatchInfo_data',
        'set_dataobject_data'
    )
    def test_ok(self):
        """
        正常系
        """

        adp = GrafanaAdapterInfo(999, 0, 'pytest', 1, 'pytest_icon')
        grafana_list = adp.get_info_list(DummyRequestOK())

        assert len(grafana_list) == 1
        assert grafana_list[0]['rule_type_id'] == 999


    @pytest.mark.usefixtures(
        'set_grafanaadapter_data',
        'set_ruletype_data',
        'set_grafanamatchInfo_data',
        'set_dataobject_data'
    )
    def test_ok_inactive(self):
        """
        正常系(廃止ルール)
        """

        adp = GrafanaAdapterInfo(999, 0, 'pytest', 1, 'pytest_icon')
        grafana_list = adp.get_info_list(DummyRequestInactive())

        assert len(grafana_list) == 1
        assert grafana_list[0]['rule_type_id'] == -1


    @pytest.mark.usefixtures(
        'set_grafanaadapter_data',
        'set_ruletype_data',
        'set_grafanamatchInfo_data',
        'set_dataobject_data'
    )
    def test_ng_rule_not_exists(self):
        """
        異常系(ルール種別なし)
        """

        try:
            adp = GrafanaAdapterInfo(999, 0, 'pytest', 1, 'pytest_icon')
            grafana_list = adp.get_info_list(None)

        except Exception as e:
            assert True
            return

        assert False


    @pytest.mark.usefixtures(
        'grafana_table',
        'set_grafanaadapter_data',
        'set_grafanamatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_update_ok(self):

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'         : 999,
            'grafana_disp_name'  : 'adapter998',
            'uri'                : 'aaa',
            'username'           : 'test_user_name',
            'password'           : 'test_passwd',
            'evtime'             : 'pytest.evtime',
            'instance'           : 'pytest.instance',
            'rule_type_id'       : '999',
            'match_list'         : {'1': 'instance'},
            'grafana_adapter_id' : '999'
        }

        result = self.target.update(json_str,request)
        assert result['status'] == 'success'


    @pytest.mark.usefixtures(
        'grafana_table',
        'set_grafanaadapter_data',
        'set_grafanamatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_update_none(self):

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'         : 998,
            'grafana_disp_name'  : 'adapter998',
            'uri'                : 'bbb',
            'username'           : 'test_user_name',
            'password'           : 'test_passwd',
            'evtime'             : 'pytest.evtime',
            'instance'           : 'pytest.instance',
            'rule_type_id'       : '999',
            'match_list'         : {'1': 'instance'},
            'grafana_adapter_id' : '998'
        }

        result = self.target.update(json_str,request)
        assert result['status'] == 'deleted'


    @pytest.mark.usefixtures(
        'grafana_table',
        'set_grafanaadapter_data',
        'set_grafanamatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_update_ng(self):

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'         : 999,
            'grafana_disp_name'  : 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
            'uri'                : 'aaa',
            'username'           : 'test_user_name',
            'password'           : 'test_passwd',
            'evtime'             : 'pytest.evtime',
            'instance'           : 'pytest.instance',
            'rule_type_id'       : '999',
            'match_list'         : {'1': 'instance'},
            'grafana_adapter_id' : '999'
        }

        result = self.target.update(json_str,request)
        assert result['status'] == 'failure'




    @pytest.mark.usefixtures(
        'grafana_table',
        'set_grafanaadapter_data',
        'set_grafanamatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_ok(self):

        error_msg  = {
            'grafana_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'query' : '',
            'rule_type_id':'',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'         : 999,
            'grafana_disp_name'  : 'adapter998',
            'uri'                : 'bbb',
            'username'           : 'test_user_name',
            'password'           : 'test_passwd',
            'evtime'             : 'pytest.evtime',
            'instance'           : 'pytest.instance',
            'rule_type_id'       : '999',
            'match_list'         : {'1': 'instance'},
            'grafana_adapter_id' : '0'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == False


    @pytest.mark.usefixtures(
        'grafana_table',
        'set_grafanaadapter_data',
        'set_grafanamatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_grafana_disp_name_none(self):

        error_msg  = {
            'grafana_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'evtime'   : '',
            'instance' : '',
            'rule_type_id':'',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'         : 999,
            'grafana_disp_name'  : '',
            'uri'                : 'bbb',
            'username'           : 'test_user_name',
            'password'           : 'test_passwd',
            'evtime'             : 'pytest.evtime',
            'instance'           : 'pytest.instance',
            'rule_type_id'       : '999',
            'match_list'         : {'1': 'instance'},
            'grafana_adapter_id' : '0'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True
        assert 'MOSJA26328' in error_msg['grafana_disp_name']


    @pytest.mark.usefixtures(
        'grafana_table',
        'set_grafanaadapter_data',
        'set_grafanamatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_grafana_disp_name_large(self):

        error_msg  = {
            'grafana_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'evtime'   : '',
            'instance' : '',
            'rule_type_id':'',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'         : 999,
            'grafana_disp_name'  : 'a' * 65,
            'uri'                : 'bbb',
            'username'           : 'test_user_name',
            'password'           : 'test_passwd',
            'evtime'             : 'pytest.evtime',
            'instance'           : 'pytest.instance',
            'rule_type_id'       : '999',
            'match_list'         : {'1': 'instance'},
            'grafana_adapter_id' : '0'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True
        assert 'MOSJA26329' in error_msg['grafana_disp_name']


    @pytest.mark.usefixtures(
        'grafana_table',
        'set_grafanaadapter_data',
        'set_grafanamatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_uri_none(self):

        error_msg  = {
            'grafana_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'evtime'   : '',
            'instance' : '',
            'rule_type_id':'',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'         : 999,
            'grafana_disp_name'  : 'aaa',
            'uri'                : '',
            'username'           : 'test_user_name',
            'password'           : 'test_passwd',
            'evtime'             : 'pytest.evtime',
            'instance'           : 'pytest.instance',
            'rule_type_id'       : '999',
            'match_list'         : {'1': 'instance'},
            'grafana_adapter_id' : '0'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True
        assert 'MOSJA26331' in error_msg['uri']


    @pytest.mark.usefixtures(
        'grafana_table',
        'set_grafanaadapter_data',
        'set_grafanamatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_uri_large(self):

        error_msg  = {
            'grafana_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'evtime'   : '',
            'instance' : '',
            'rule_type_id':'',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'         : 999,
            'grafana_disp_name'  : 'aaa',
            'uri'                : 'b' * 513,
            'username'           : 'test_user_name',
            'password'           : 'test_passwd',
            'evtime'             : 'pytest.evtime',
            'instance'           : 'pytest.instance',
            'rule_type_id'       : '999',
            'match_list'         : {'1': 'instance'},
            'grafana_adapter_id' : '0'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True
        assert 'MOSJA26332' in error_msg['uri']


    @pytest.mark.usefixtures(
        'grafana_table',
        'set_grafanaadapter_data',
        'set_grafanamatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_username_large(self):

        error_msg  = {
            'grafana_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'evtime'   : '',
            'instance' : '',
            'rule_type_id':'',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'         : 999,
            'grafana_disp_name'  : 'aaa',
            'uri'                : 'bbb',
            'username'           : 'a' * 65,
            'password'           : 'test_passwd',
            'evtime'             : 'pytest.evtime',
            'instance'           : 'pytest.instance',
            'rule_type_id'       : '999',
            'match_list'         : {'1': 'instance'},
            'grafana_adapter_id' : '0'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True
        assert 'MOSJA26335' in error_msg['username']


    @pytest.mark.usefixtures(
        'grafana_table',
        'set_grafanaadapter_data',
        'set_grafanamatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_password_add_large(self):

        error_msg  = {
            'grafana_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'evtime'   : '',
            'instance' : '',
            'rule_type_id':'',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'         : 999,
            'grafana_disp_name'  : 'aaa',
            'uri'                : 'bbb',
            'username'           : 'test_user_name',
            'password'           : 'a' * 65,
            'evtime'             : 'pytest.evtime',
            'instance'           : 'pytest.instance',
            'rule_type_id'       : '999',
            'match_list'         : {'1': 'instance'},
            'grafana_adapter_id' : '0'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True
        assert 'MOSJA26338' in error_msg['password']


    @pytest.mark.usefixtures(
        'grafana_table',
        'set_grafanaadapter_data',
        'set_grafanamatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_password_upd_large(self):

        error_msg  = {
            'grafana_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'evtime'   : '',
            'instance' : '',
            'rule_type_id':'',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'         : 999,
            'grafana_disp_name'  : 'aaa',
            'uri'                : 'bbb',
            'username'           : 'test_user_name',
            'password'           : 'a' * 65,
            'evtime'             : 'pytest.evtime',
            'instance'           : 'pytest.instance',
            'rule_type_id'       : '999',
            'match_list'         : {'1': 'instance'},
            'grafana_adapter_id' : '999'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'upd')
        assert error_flag == True
        assert 'MOSJA26338' in error_msg['password']


    @pytest.mark.usefixtures(
        'grafana_table',
        'set_grafanaadapter_data',
        'set_grafanamatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_evtime_none(self):

        error_msg  = {
            'grafana_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'evtime'   : '',
            'instance' : '',
            'rule_type_id':'',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'         : 999,
            'grafana_disp_name'  : 'aaa',
            'uri'                : 'bbb',
            'username'           : 'test_user_name',
            'password'           : 'test_passwd',
            'evtime'             : '',
            'instance'           : 'pytest.instance',
            'rule_type_id'       : '999',
            'match_list'         : {'1': 'instance'},
            'grafana_adapter_id' : '999'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True
        assert 'MOSJA26341' in error_msg['evtime']


    @pytest.mark.usefixtures(
        'grafana_table',
        'set_grafanaadapter_data',
        'set_grafanamatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_evtime_large(self):

        error_msg  = {
            'grafana_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'evtime'   : '',
            'instance' : '',
            'rule_type_id':'',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'         : 999,
            'grafana_disp_name'  : 'aaa',
            'uri'                : 'bbb',
            'username'           : 'test_user_name',
            'password'           : 'test_passwd',
            'evtime'             : 'a' * 129,
            'instance'           : 'pytest.instance',
            'rule_type_id'       : '999',
            'match_list'         : {'1': 'instance'},
            'grafana_adapter_id' : '999'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True
        assert 'MOSJA26342' in error_msg['evtime']


    @pytest.mark.usefixtures(
        'grafana_table',
        'set_grafanaadapter_data',
        'set_grafanamatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_instance_none(self):

        error_msg  = {
            'grafana_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'evtime'   : '',
            'instance' : '',
            'rule_type_id':'',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'         : 999,
            'grafana_disp_name'  : 'aaa',
            'uri'                : 'bbb',
            'username'           : 'test_user_name',
            'password'           : 'test_passwd',
            'evtime'             : 'pytest.evtime',
            'instance'           : '',
            'rule_type_id'       : '999',
            'match_list'         : {'1': 'instance'},
            'grafana_adapter_id' : '999'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True
        assert 'MOSJA26344' in error_msg['instance']


    @pytest.mark.usefixtures(
        'grafana_table',
        'set_grafanaadapter_data',
        'set_grafanamatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_instance_large(self):

        error_msg  = {
            'grafana_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'evtime'   : '',
            'instance' : '',
            'rule_type_id':'',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'         : 999,
            'grafana_disp_name'  : 'aaa',
            'uri'                : 'bbb',
            'username'           : 'test_user_name',
            'password'           : 'test_passwd',
            'evtime'             : 'pytest.evtime',
            'instance'           : 'a' * 129,
            'rule_type_id'       : '999',
            'match_list'         : {'1': 'instance'},
            'grafana_adapter_id' : '999'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True
        assert 'MOSJA26345' in error_msg['instance']


    @pytest.mark.usefixtures(
        'grafana_table',
        'set_grafanaadapter_data',
        'set_grafanamatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_rule_type_id_not(self):

        error_msg  = {
            'grafana_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'evtime'   : '',
            'instance' : '',
            'rule_type_id':'',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'         : 999,
            'grafana_disp_name'  : 'aaa',
            'uri'                : 'bbb',
            'username'           : 'test_user_name',
            'password'           : 'test_passwd',
            'evtime'             : 'pytest.evtime',
            'instance'           : 'pytest.instance',
            'rule_type_id'       : '998',
            'match_list'         : {'1': 'instance'},
            'grafana_adapter_id' : '999'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True
        assert 'MOSJA26340' in error_msg['rule_type_id']


    @pytest.mark.usefixtures(
        'grafana_table',
        'set_grafanaadapter_data',
        'set_grafanamatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_match_list_ng_nom(self):

        error_msg  = {
            'grafana_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'evtime'   : '',
            'instance' : '',
            'rule_type_id': '',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'         : 999,
            'grafana_disp_name'  : 'aaa',
            'uri'                : 'bbb',
            'username'           : 'test_user_name',
            'password'           : 'test_passwd',
            'evtime'             : 'pytest.evtime',
            'instance'           : 'pytest.instance',
            'rule_type_id'       : '999',
            'match_list'         : {'2': 'instance', '3': 'namespace'},
            'grafana_adapter_id' : '999'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True


    @pytest.mark.usefixtures(
        'grafana_table',
        'set_grafanaadapter_data',
        'set_grafanamatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_match_list_ng_large(self):

        error_msg  = {
            'grafana_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'evtime'   : '',
            'instance' : '',
            'rule_type_id': '',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'         : 999,
            'grafana_disp_name'  : 'aaa',
            'uri'                : 'bbb',
            'username'           : 'test_user_name',
            'password'           : 'test_passwd',
            'evtime'             : 'pytest.evtime',
            'instance'           : 'pytest.instance',
            'rule_type_id'       : '999',
            'match_list'         : {'1': 'a' * 129},
            'grafana_adapter_id' : '999'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True


    @pytest.mark.usefixtures(
        'grafana_table',
        'set_grafanaadapter_data',
        'set_grafanamatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_grafana_disp_name_ng_duplicate(self):

        error_msg  = {
            'grafana_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'evtime'   : '',
            'instance' : '',
            'rule_type_id': '',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'         : 999,
            'grafana_disp_name'  : 'adapter999',
            'uri'                : 'bbb',
            'username'           : 'test_user_name',
            'password'           : 'test_passwd',
            'evtime'             : 'pytest.evtime',
            'instance'           : 'pytest.instance',
            'rule_type_id'       : '999',
            'match_list'         : {'1': 'instance'},
            'grafana_adapter_id' : '0'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True
        assert 'MOSJA26315' in error_msg['grafana_disp_name']


    @pytest.mark.usefixtures(
        'grafana_table',
        'set_grafanaadapter_data',
        'set_grafanamatchInfo_data',
        'set_ruletype_data',
        'set_dataobject_data'
    )
    def test_validate_uri_ng_duplicate(self):

        error_msg  = {
            'grafana_disp_name' : '',
            'uri' : '',
            'username' : '',
            'password' : '',
            'evtime'   : '',
            'instance' : '',
            'rule_type_id': '',
        }

        request = DummyRequest()
        request.user = User.objects.get(user_id=1)

        json_str = {
            'adapter_id'         : 999,
            'grafana_disp_name'  : 'bbb',
            'uri'                : 'aaa',
            'username'           : 'test_user_name',
            'password'           : 'test_passwd',
            'evtime'             : 'pytest.evtime',
            'instance'           : 'pytest.instance',
            'rule_type_id'       : '999',
            'match_list'         : {'1': 'instance'},
            'grafana_adapter_id' : '0'
        }

        error_flag = self.target._validate(json_str, error_msg, request, 'add')
        assert error_flag == True
        assert 'MOSJA26316' in error_msg['uri']


