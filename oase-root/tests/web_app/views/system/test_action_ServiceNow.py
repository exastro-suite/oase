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
  
action_ServiceNow tests

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

from web_app.models.models import User, Group, UserGroup
from web_app.views.system.ServiceNow.action_ServiceNow import ServiceNowDriverInfo

from libs.commonlibs.aes_cipher import AESCipher
from libs.commonlibs.define import *
from importlib import import_module


module = import_module('web_app.models.ServiceNow_models')
ServiceNowDriver = getattr(module, 'ServiceNowDriver')


class DummyRequest():

    user = None


def set_test_data():

    now = datetime.datetime.now(pytz.timezone('UTC'))
    group = Group(
        group_id=1,
        group_name='単体テストチーム',
        summary='単体テスト用権限',
        ad_data_flag='0',
        last_update_timestamp=now,
        last_update_user='pytest',
    )
    group.save()

    group = Group(
        group_id=2,
        group_name='結合テストチーム',
        summary='結合テスト用権限',
        ad_data_flag='0',
        last_update_timestamp=now,
        last_update_user='pytest',
    )
    group.save()

    cipher = AESCipher(settings.AES_KEY)
    encrypted_password = cipher.encrypt('pytest')
    servicenow_driver = ServiceNowDriver(
        servicenow_driver_id=1,
        servicenow_disp_name='ServiceNow0001',
        hostname='pytest-host-name1',
        protocol='https',
        port='443',
        username='pytest',
        password=encrypted_password,
        count=0,
        proxy='',
        last_update_user='pytest',
        last_update_timestamp=now,
    )
    servicenow_driver.save(force_insert=True)

    servicenow_driver = ServiceNowDriver(
        servicenow_driver_id=2,
        servicenow_disp_name='ServiceNow0002',
        hostname='pytest-host-name2',
        protocol='https',
        port='443',
        username='pytest',
        password=encrypted_password,
        count=0,
        proxy='',
        last_update_user='pytest',
        last_update_timestamp=now,
    )
    servicenow_driver.save(force_insert=True)

    user_group = UserGroup(
        user_group_id=1,
        user_id=1,
        group_id=1,
        ad_data_flag='0',
        last_update_timestamp=datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user='test_user',
    )
    user_group.save(force_insert=True)

    user_group = UserGroup(
        user_group_id=2,
        user_id=1,
        group_id=998,
        ad_data_flag='0',
        last_update_timestamp=datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user='test_user',
    )
    user_group.save(force_insert=True)


def del_test_data():
    Group.objects.all().delete()
    ServiceNowDriver.objects.all().delete()
    UserGroup.objects.all().delete()


@pytest.mark.django_db
class TestServiceNowDriverInfo(object):

    @classmethod
    def setup_class(cls):
        print('TestServiceNowDriverInfo - start')

    @classmethod
    def teardown_class(cls):
        print('TestServiceNowDriverInfo - end')

    def setup_method(self, method):
        print('method_name: {}'.format(method.__name__))

        # 動的インポート
        drv_id = 1
        act_id = 1
        name = 'pytest'
        ver = 1
        icon_name = 'test'

        self.target = ServiceNowDriverInfo(drv_id, act_id, name, ver, icon_name)

    def teardown_method(self, method):
        print('method_name: {}:'.format(method.__name__))
        del self.target

    ########################
    # TESTここから
    ########################

    def test_get_info_list(self):
        """
        get_info_list test
        """
        del_test_data()
        set_test_data()

        result = self.target.get_info_list([1, 2])

        assert len(result) > 0

        del_test_data()


    ############################################
    # 新規追加テスト
    ############################################
    # 正常系
    def test_modify_ok_ope_insert(self, monkeypatch):

        # テストデータ初期化
        del_test_data()
        set_test_data()

        # テストデータ作成
        req = DummyRequest()
        req.user = User.objects.get(user_id=1)

        req_data = {}
        req_data['json_str'] = {
            'ope'                  : DABASE_OPECODE.OPE_INSERT,
            'password'             : 'test_passwd',
            'servicenow_disp_name' : 'test_disp_name',
            'protocol'             : 'https',
            'hostname'             : 'test_host_name',
            'port'                 : 443,
            'username'             : 'test_user_name',
            'proxy'                : 'test_proxy',
        }

        # テスト
        monkeypatch.setattr(self.target, '_validate', lambda a, b, c:False)
        result = self.target.modify(req_data, req)

        assert result['status'] == 'success'

        del_test_data()

