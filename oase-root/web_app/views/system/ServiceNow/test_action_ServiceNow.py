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
import datetime
import pytz

from importlib import import_module

from django.conf import settings
from django.db import transaction

from web_app.models.models import User
from web_app.views.system.ServiceNow.action_ServiceNow import ServiceNowDriverInfo

from libs.commonlibs.aes_cipher import AESCipher
from libs.commonlibs.define import *


module = import_module('web_app.models.ServiceNow_models')
ServiceNowDriver = getattr(module, 'ServiceNowDriver')


class DummyRequest():

    user = None


def set_test_data():

    now = datetime.datetime.now(pytz.timezone('UTC'))

    cipher = AESCipher(settings.AES_KEY)
    encrypted_password = cipher.encrypt('pytest')
    servicenow_driver = ServiceNowDriver(
        servicenow_driver_id=1,
        servicenow_disp_name='ServiceNow0001',
        hostname='pytest-host-name1',
        protocol='http',
        port='80',
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


def del_test_data():

    ServiceNowDriver.objects.all().delete()


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

    ############################################
    # 一覧取得テスト
    ############################################
    # 正常系
    def test_get_info_list(self):
        """
        get_info_list test
        """
        del_test_data()
        set_test_data()

        result = self.target.get_info_list([1, 2])

        assert len(result) >= 2
        assert (result[0]['servicenow_driver_id'] == 1 and result[0]['protocol'] == 'http') \
            or (result[0]['servicenow_driver_id'] == 2 and result[0]['protocol'] == 'https')
        assert (result[1]['servicenow_driver_id'] == 1 and result[1]['protocol'] == 'http') \
            or (result[1]['servicenow_driver_id'] == 2 and result[1]['protocol'] == 'https')

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

    ############################################
    # 異常系
    def test_modify_ng_ope_insert(self):

        # テストデータ初期化
        del_test_data()
        set_test_data()

        # テストデータ作成
        req = DummyRequest()
        req.user = User.objects.get(user_id=1)

        req_data = {}
        req_data['json_str'] = {
            'ope'                  : DABASE_OPECODE.OPE_INSERT,
            'password'             : '12345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567',
            'servicenow_disp_name' : '12345678901234567890123456789012345678901234567890123456789012345',
            'protocol'             : '123456789',
            'hostname'             : '123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789',
            'port'                 : 65536,
            'username'             : '12345678901234567890123456789012345678901234567890123456789012345',
            'proxy'                : '12345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567',
        }

        # テスト
        result = self.target.modify(req_data, req)

        assert result['status'] == 'failure'

        del_test_data()


    ############################################
    # 削除テスト
    ############################################
    # 正常系
    def test_modify_ok_ope_delete(self, monkeypatch):

        # テストデータ初期化
        del_test_data()
        set_test_data()

        # テストデータ作成
        req = DummyRequest()
        req.user = User.objects.get(user_id=1)

        req_data = {}
        req_data['json_str'] = {
            'ope'                  : DABASE_OPECODE.OPE_DELETE,
            'servicenow_driver_id' : 1,
        }
        # テスト
        monkeypatch.setattr(self.target, '_validate', lambda a, b, c:False)
        result = self.target.modify(req_data, req)

        assert result['status'] == 'success'

        del_test_data()

    # ############################################
    # # 異常系
    def test_modify_ng_ope_delete(self, monkeypatch):

        # テストデータ初期化
        del_test_data()
        set_test_data()

        # テストデータ作成
        req = DummyRequest()
        req.user = User.objects.get(user_id=1)

        req_data = {}
        req_data['json_str'] = {
            'ope'                  : DABASE_OPECODE.OPE_DELETE,
        }
        # テスト
        monkeypatch.setattr(self.target, '_validate', lambda a, b, c:False)
        result = self.target.modify(req_data, req)

        assert result['status'] == 'failure'

        del_test_data()

    ############################################
    # 変更テスト
    ############################################
    # 正常系
    def test_modity_ok_update(self,monkeypatch):

        # テストデータ初期化
        del_test_data()
        set_test_data()

        # テストデータ作成
        req = DummyRequest()
        req.user = User.objects.get(user_id=1)

        req_data = {}
        req_data['json_str'] = {
            'ope'                  : DABASE_OPECODE.OPE_UPDATE,
            'password'             : 'test_passwd',
            'servicenow_disp_name' : 'test_disp_name',
            'protocol'             : 'https',
            'hostname'             : 'test_host_name',
            'port'                 : 443,
            'username'             : 'test_user_name',
            'proxy'                : 'test_proxy',
            'servicenow_driver_id' : 1,
        }

        # テスト
        monkeypatch.setattr(self.target, '_validate', lambda a, b, c:False)
        result = self.target.modify(req_data, req)

        assert result['status'] == 'success'

        del_test_data()

    ############################################
    # 異常系
    def test_modify_ng_update(self,monkeypatch):

        # テストデータ初期化
        del_test_data()
        set_test_data()
        
        # テストデータ作成
        req = DummyRequest()
        req.user = User.objects.get(user_id=1)

        req_data = {}
        req_data['json_str'] = {
            'ope'                  : DABASE_OPECODE.OPE_UPDATE,
            'password'             : '12345678901234567890123456789012345678901234567890123456789012345',
            'servicenow_disp_name' : '12345678901234567890123456789012345678901234567890123456789012345',
            'protocol'             : '123456789',
            'hostname'             : '123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789',
            'port'                 : 65536,
            'username'             : '12345678901234567890123456789012345678901234567890123456789012345',
            'proxy'                : '12345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567',
            'servicenow_driver_id' : 1,
        }

        # テスト
        monkeypatch.setattr(self.target, '_validate', lambda a, b, c:False)
        with transaction.atomic():
            result = self.target.modify(req_data, req)
            assert result['status'] == 'failure'

        del_test_data()

    ############################################
    # 異常系
    def test_modity_ng_driverid_update(self,monkeypatch):

        # テストデータ初期化
        del_test_data()
        set_test_data()

        # テストデータ作成
        req = DummyRequest()
        req.user = User.objects.get(user_id=1)

        req_data = {}
        req_data['json_str'] = {
            'ope'                  : DABASE_OPECODE.OPE_UPDATE,
            'password'             : 'test_passwd',
            'servicenow_disp_name' : 'test_disp_name',
            'protocol'             : 'https',
            'hostname'             : 'test_host_name',
            'port'                 : 443,
            'username'             : 'test_user_name',
            'proxy'                : 'test_proxy',
            'servicenow_driver_id' : 0,
        }

        # テスト
        monkeypatch.setattr(self.target, '_validate', lambda a, b, c:False)
        self.target.modify(req_data, req)
        result = ServiceNowDriver.objects.all().values_list('servicenow_disp_name',flat=True)
        assert 'test_disp_name' not in result

        del_test_data()
