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
python test 旧版
todo TestCaseで書かれているテストをpytest形式に直す。
    @pytest.mark.skip()がつけられているテストを直す。testの要否も確認する。
"""

from django.test import TestCase
from django.urls import reverse
from django.test import Client

from datetime import timedelta
from web_app.models.models import * 
import sys
import pytz
import pytest

from web_app.serializers.user import UserSerializer


@pytest.mark.django_db
def test_sample(django_db_setup):

    u1 = User.objects.get(pk=1)
    assert u1.user_name == 'システム管理者'

#--------------------------------
# ModelTest
#--------------------------------
@pytest.mark.django_db
class TestGroupModel:

    def test_default_group(self, django_db_setup):
        """初期groupの存在チェック"""

        g = Group.objects.get(pk=1)
        assert g.group_name == 'システム管理者'


# user.py
@pytest.mark.django_db
def test_default_user(self, django_db_setup):
    """
    default_userの存在チェック
    """

    u1 = User.objects.get(pk=1)
    assert is_sameuser(u1, 'administrator', 'システム管理者')

    u2140000000 = User.objects.get(pk=-2140000000)
    assert is_sameuser(u2140000000, 'oase_admin', 'OASE')

    u2140000001 = User.objects.get(pk=-2140000001)
    assert is_sameuser(u2140000001, 'oase_action_driver', 'アクションドライバープロシージャ')

    u2140000002 = User.objects.get(pk=-2140000002)
    assert is_sameuser(u2140000002, 'oase_agent', 'OASEエージェントプロシージャ')

    u2140000003 = User.objects.get(pk=-2140000003)
    assert is_sameuser(u2140000003, 'oase_apply', 'OASEルール適用プロシージャ')

    u2140000004 = User.objects.get(pk=-2140000004)
    assert is_sameuser(u2140000004, 'oase_ad_linkage', 'OASE_AD連携プロシージャ')


def is_sameuser(user, login_id, user_name):
    """
    userモデルが期待したログインidとユーザ名かどうかチェックする
    """
    if user.login_id == login_id and user.user_name == user_name:
        return True
    return False



@pytest.mark.django_db
def test_default_user(admin):
    """
    システム管理者グループのUserGroupの初期値チェック
    """

    ug_list = UserGroup.objects.filter(pk__gte=-2140000004, pk__lte=1)

    assert len(ug_list) == 6
    for ug in ug_list:
        assert ug.group_id == 1


#--------------------------------
# ViewTest
#--------------------------------
def add_user(login_id, user_name='test_user', password='abc123!#', mail_address='sample@a.a', lang_mode_id=1, disp_mode_id=1):
    """ユーザ追加"""

    admin = User.objects.get(pk=1)
    
    user = User.objects.create(
        login_id = login_id,
        user_name = user_name,
        password = password, 
        mail_address = mail_address, 
        lang_mode_id = lang_mode_id,
        disp_mode_id = disp_mode_id,
        last_update_user = admin.user_name,
    )
    return user

# login.py
@pytest.mark.django_db
def test_login_url(admin):
    """ログイン画面が存在するかテスト"""
    response = admin.get(reverse('web_app:top:login'))
    assert response.status_code == 200

# index.py
@pytest.mark.django_db
def test_index_url(admin):
    """indexページ表示テスト"""
    response = admin.get(reverse('web_app:top:index'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_logout_url(admin):
    """
    logoutページ表示テスト
    ログアウト処理後ログイン画面にリダイレクトされる
    """
    response = admin.get(reverse('web_app:top:logout'), follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [('/oase_web/top/login?logout=true', 302)]

# user.py
@pytest.mark.django_db
def test_default_list(admin):
    """
    初期の表示ユーザは1件
    """
    response = admin.get(reverse('web_app:system:user'))
    assert len(response.context['user_list']) ==  1


@pytest.mark.django_db
def test_user_order_desc(admin):
    """ユーザは降順で表示される"""
    tester1 = add_user(login_id='tester1')
    tester2 = add_user(login_id='tester2')

    response = admin.get(reverse('web_app:system:user'))
    user_list = response.context['user_list']

    assert user_list[1]['login_id'] == 'tester1'
    assert user_list[2]['login_id'] == 'tester2'


# group.py
@pytest.mark.django_db
def test_default_list(admin):
    """
    初期の表示グループは1件
    """
    response = admin.get(reverse('web_app:system:group'))
    assert len(response.context['group_list']) == 1


# personal_config.py
@pytest.mark.django_db
def test_personal_config(admin):
    response = admin.get(reverse('web_app:user:personal_config'))
    assert response.status_code == 200


# login.py
@pytest.mark.django_db
def test_pass_ch_top(admin):
    response = admin.get(reverse('web_app:top:pass_ch'))
    assert response.status_code == 200

#--------------------------------
# SerializersTests
#--------------------------------
@pytest.mark.django_db
def test_user(admin):
    
    json_data = {
        'user_name' : 'test',
        'login_id' : 'test',
        'mail_address' : 'test',
        'lang_mode_id' : '1',
        'disp_mode_id' : '1',
    }

    serializer = UserSerializer(data=json_data)
    result = serializer.is_valid()

    print(serializer.errors)
    assert result == False

