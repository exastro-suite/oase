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
  
action_ita tests

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

from web_app.models.models import ActionType, DriverType, Group, User, UserGroup, PasswordHistory
from web_app.views.system.ITA.action_ITA import ITADriverInfo

from libs.commonlibs.aes_cipher import AESCipher
from libs.commonlibs.define import *
from importlib import import_module


module = import_module('web_app.models.ITA_models')
ItaDriver = getattr(module, 'ItaDriver')
ItaPermission = getattr(module, 'ItaPermission')


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
    ita_driver = ItaDriver(
        ita_driver_id=1,
        ita_disp_name='Action43',
        version='1.5.0',
        protocol='https',
        hostname='pytest-host-name',
        port='443',
        username='pytest',
        password=encrypted_password,
        last_update_user='pytest',
        last_update_timestamp=now,
    )
    ita_driver.save(force_insert=True)

    ita_driver = ItaDriver(
        ita_driver_id=2,
        ita_disp_name='Action44',
        version='1.5.0',
        protocol='https',
        hostname='pytest-host-name2',
        port='443',
        username='pytest',
        password=encrypted_password,
        last_update_user='pytest',
        last_update_timestamp=now,
    )
    ita_driver.save(force_insert=True)

    itapermission = ItaPermission(
        ita_permission_id=1,
        ita_driver_id=1,
        group_id=998,
        permission_type_id=1,
        last_update_timestamp=now,
        last_update_user='pytest',
    )
    itapermission.save(force_insert=True)

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
    ItaDriver.objects.all().delete()
    ItaPermission.objects.all().delete()
    UserGroup.objects.all().delete()


@pytest.mark.django_db
class TestITADriverInfo(object):

    @classmethod
    def setup_class(cls):
        print('TestITADriverInfo - start')

    @classmethod
    def teardown_class(cls):
        print('TestITADriverInfo - end')

    def setup_method(self, method):
        print('method_name: {}'.format(method.__name__))

        # 動的インポート
        drv_id = 1
        act_id = 1
        name = 'pytest'
        ver = 1
        icon_name = 'test'

        self.target = ITADriverInfo(drv_id, act_id, name, ver, icon_name)

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

    def test_get_group_list(self):
        """
        get_group_list test
        """

        del_test_data()
        set_test_data()

        result = self.target.get_group_list()

        assert result.count() == 1

        del_test_data()

    def test_get_editable_driver_ids(self):
        """
        get_editable_driver_ids test
        """
        del_test_data()
        set_test_data()

        arg1 = ItaDriver.objects.all()
        arg2 = [1,]

        result = self.target.get_driver_ids(arg1, arg2, [ALLOWED_MENTENANCE,])

        assert len(result) > 0

        del_test_data()

    def test_get_permission(self):
        """
        get_permission test
        """

        arg1 = ItaDriver.objects.all()

        del_test_data()
        set_test_data()
        permission = self.target.get_permission(arg1)

        assert len(permission) > 0

        del_test_data()

    def test__chk_permission(self):
        """
        _chk_permission test
        """

        group_id_list = [1, 2]
        ita_driver_id = 1
        response = {"status": "success",}

        result = self.target._chk_permission(group_id_list, ita_driver_id, response)

        assert result['status'] == "success"

