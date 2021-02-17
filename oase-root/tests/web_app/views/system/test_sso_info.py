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
  
sso_info tests

"""

import pytest
import unittest
import json
import datetime
import pytz

from django.urls import reverse
from django.test import Client
from web_app.templatetags.common import get_message
from web_app.models.models import System, Menu, SsoInfo, User, PasswordHistory
from libs.commonlibs import define as defs
from libs.commonlibs.common import Common
from importlib import import_module

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


@pytest.mark.django_db
class TestSsoInfoIndex(object):
    """
    web_app/views/system/sso_info.pyのテストクラス一覧表示
    """
    def test_index_ok(self, admin):
        """
        正常系
        """
        response = admin.get(reverse('web_app:system:sso_info'))
        content = response.content.decode('utf-8')
        assert response.status_code == 200
    def test_index_ng(self,admin):
        """
        異常系
        """
        with pytest.raises(Exception):
            response = admin.get(reverse('web_app:system:sso_info'))
            assert response.status_code == 404


class TestSsoInfoDelete(object):
    def set_test_data(self):
        """
        テストデータの作成
        """
        SsoInfo(
            provider_name = 'pytest',
            auth_type = 9999,
            logo = 'test_logo',
            visible_flag = '1',
            clientid = 5555,
            clientsecret = 6666,
            authorizationuri = 'ttt',
            accesstokenuri = 'ttt',
            resourceowneruri = 'ttt',
            scope = '',
            id = 1111,
            name = 'test',
            email = 'pytest@example.com',
            imageurl = 'test_log.pmg',
            proxy = 2222
        ).save(force_insert=True)

    @pytest.mark.django_db
    def test_delete_sso_ok(self, admin, monkeypatch):
        """
        テストデータの削除
        正常系
        """
        self.set_test_data()
        admin = get_adminstrator()

        # 削除処理
        json_str = {
            "providername":"pytest",
            "auth_type":9999,
            "visible_flag":1,
            "clientid":"0001",
            "clientsecret":"0000",
            "authorizationuri":"aaa",
            "resourceowneruri":"bbb",
            "id":"1234",
            "name":"test-user"
        }
        json_data = json.dumps(json_str)

        response = admin.post(reverse('web_app:system:delete_sso', args=[1,]), {'json_str':json_data})
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_delete_sso_ng(self, admin, monkeypatch):
        """
        テストデータの削除
        異常系
        """
        self.set_test_data()
        admin = get_adminstrator()
        response_data = {}
        # 削除処理
        json_str = {
            "providername":"pytest",
            "auth_type":9999,
            "visible_flag":1,
            "clientid":"0001",
            "clientsecret":"0000",
            "authorizationuri":"aaa",
            "resourceowneruri":"bbb",
            "id":"1234",
            "name":"test-user"
        }
        json_data = json.dumps(json_str)
        with pytest.raises(Exception):
            response = admin.post(reverse('web_app:system:delete_sso', args=["abc",]), {'json_str':json_data})
            assert response.status_code == 404


@pytest.mark.django_db
class TestModify:
    """
    modify テストクラス
    """

    def set_test_data(self):
        """
        テストデータの作成
        """

        SsoInfo(
            provider_name = 'pytest',
            auth_type = 9999,
            logo = 'test_logo',
            visible_flag = '1',
            clientid = 5555,
            clientsecret = 6666,
            authorizationuri = 'ttt',
            accesstokenuri = 'ttt',
            resourceowneruri = 'ttt',
            scope = '',
            id = 1111,
            name = 'test',
            email = 'pytest@example.com',
            imageurl = 'test_log.pmg',
            proxy = 2222
        ).save(force_insert=True)

    def del_test_data(self):
        """
        テストデータの削除
        """

        SsoInfo.objects.all().delete()


    @pytest.mark.django_db
    def test_modify_ok(self, admin):
        """
        新規登録
        正常系
        """
        admin = get_adminstrator()
        self.set_test_data()
        self.set_test_data()

        # 登録データ
        json_str = {"table_info":{"provider_name":"pytest",
                                  "auth_type":9999,
                                  "visible_flag":1,
                                  "clientid":"0001",
                                  "clientsecret":"0000",
                                  "authorizationuri":"aaa",
                                  "resourceowneruri":"bbb",
                                  "id":"1234",
                                  "name":"test-user"}}
        json_data = json.dumps(json_str)

        response = admin.post('/oase_web/system/sso_info', {'add_record':json_data})
        content = response.content.decode('utf-8')

        assert response.status_code == 200
        self.del_test_data()

    @pytest.mark.django_db
    def test_modify_ng(self, admin):
        """
        新規登録
        異常系
        """
        admin = get_adminstrator()
        self.set_test_data()
        self.set_test_data()

        # 登録データ
        json_str = {"table_info":{"provider_name":"pytest",
                                  "auth_type":9999,
                                  "visible_flag":0,
                                  "clientid":"0001",
                                  "clientsecret":"0000",
                                  "authorizationuri":"aaa",
                                  "resourceowneruri":"bbb",
                                  "id":"1234",
                                  "name":"test-user"}}
        json_data = json.dumps(json_str)

        with pytest.raises(Exception):
            response = admin.post('/oase_web/system/sso_info', {'add_record':json_data})

            assert response.status_code == 404

        self.del_test_data()

    @pytest.mark.django_db
    def test_modify_detail_ok(self, admin):
        """
        更新
        正常系
        """
        admin = get_adminstrator()

        # 変更データ
        json_str = {"table_info":{"provider_name":"pytest",
                                  "auth_type":9876,
                                  "visible_flag":1,
                                  "clientid":"0001",
                                  "clientsecret":"0000",
                                  "authorizationuri":"aaa",
                                  "resourceowneruri":"bbb",
                                  "id":"1234",
                                  "name":"test-user"}}
        json_data = json.dumps(json_str)

        response = admin.post(reverse('web_app:system:sso_modify_detail', args=[1,]), {'json_str':json_data})

        assert response.status_code == 200
        self.del_test_data()

    @pytest.mark.django_db
    def test_modify_detail_ok(self, admin):
        """
        更新
        異常系系
        """
        admin = get_adminstrator()

        # 変更データ
        json_str = {"table_info":{"provider_name":"pytest",
                                  "auth_type":9876,
                                  "visible_flag":1,
                                  "clientid":"0001",
                                  "clientsecret":"0000",
                                  "authorizationuri":"aaa",
                                  "resourceowneruri":"bbb",
                                  "id":"1234",
                                  "name":"test-user"}}
        json_data = json.dumps(json_str)

        with pytest.raises(Exception):
            response = admin.post(reverse('web_app:system:sso_modify_detail', args=[1,]), {'json_str':json_data})

            assert response.status_code == 404

        self.del_test_data()
