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
  トークン払い出し画面
"""


import pytest
import datetime
import pytz
import json

from django.urls import reverse
from django.test import Client

from libs.commonlibs.common import Common
from web_app.models.models import User, PasswordHistory
from web_app.models.models import TokenInfo, TokenPermission
from web_app.views.rule import token 


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


@pytest.fixture()
def tokeninfo_data():

    now = datetime.datetime.now(pytz.timezone('UTC'))

    # 権限なし
    TokenInfo(
        token_id = 99998,
        token_name = 'pytest_token_name',
        token_data = 'pytest_token_data',
        use_start_time = datetime.datetime.now(pytz.timezone('UTC')),
        use_end_time = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user = 'pytest_user'
    ).save(force_insert=True)

    # 正常
    TokenInfo(
        token_id = 99999,
        token_name = 'pytest_token_name',
        token_data = 'pytest_token_data',
        use_start_time = datetime.datetime.now(pytz.timezone('UTC')),
        use_end_time = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user = 'pytest_user'
    ).save(force_insert=True)

    yield

    TokenInfo.objects.filter(last_update_user='pytest_user').delete()


@pytest.fixture()
def tokenpermission_data():

    now = datetime.datetime.now(pytz.timezone('UTC'))

    # 権限なし
    TokenPermission(
        token_permission_id = 99998,
        token_id = 99998,
        group_id = 1,
        permission_type_id = 3,
        last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user = 'pytest_user'
    ).save(force_insert=True)

    # 正常
    TokenPermission(
        token_permission_id = 99999,
        token_id = 99999,
        group_id = 1,
        permission_type_id = 1,
        last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user = 'pytest_user'
    ).save(force_insert=True)

    yield

    TokenPermission.objects.filter(last_update_user='pytest_user').delete()


################################################################
# トークン削除テスト
################################################################
@pytest.mark.django_db
class TestDeleteToken(object):

    @pytest.mark.usefixtures('tokeninfo_data', 'tokenpermission_data')
    def test_ok(self):
        """
        正常系
        """

        admin = get_adminstrator()
        response = admin.get(reverse('web_app:rule:token_delete', args=[99999,]))
        response = json.loads(response.content)

        assert response['status'] == 'success'


    @pytest.mark.usefixtures('tokeninfo_data', 'tokenpermission_data')
    def test_ng_notexists(self):
        """
        異常系(指定IDのレコードなし)
        """

        admin = get_adminstrator()
        response = admin.get(reverse('web_app:rule:token_delete', args=[999,]))
        response = json.loads(response.content)

        assert 'error_msg' in response
        assert 'MOSJA37017' in response['error_msg']


    @pytest.mark.usefixtures('tokeninfo_data', 'tokenpermission_data')
    def test_ng_deny(self):
        """
        異常系(権限なし)
        """

        admin = get_adminstrator()
        response = admin.get(reverse('web_app:rule:token_delete', args=[99998,]))
        response = json.loads(response.content)

        assert 'error_msg' in response
        assert 'MOSJA37016' in response['error_msg']


