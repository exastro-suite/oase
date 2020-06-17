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

import pytest
import datetime
import json
import pytz

from django.urls import reverse
from django.http import Http404
from django.test import Client, RequestFactory
from django.db import transaction
from importlib import import_module

from libs.commonlibs.common import Common
from web_app.models.models import Group, PasswordHistory, RuleType, User
from web_app.views.rule.decision_table import _select, DecisionTableAuthByRule


@pytest.mark.django_db
class TestDecisionTableSelect:
    """
    decision_table._select テストクラス
    """

    def set_test_data(self):
        """
        テストデータの作成
        """

        RuleType(
            rule_type_id = 9999,
            rule_type_name = 'pytest_name',
            summary = None,
            rule_table_name = 'pytest_table',
            generation_limit = 5,
            group_id = 'pytest_com',
            artifact_id = 'pytest_oase',
            container_id_prefix_staging = 'test',
            container_id_prefix_product = 'prod',
            current_container_id_staging = None,
            current_container_id_product = None,
            label_count = 1,
            unknown_event_notification = '1',
            mail_address = 'pytest@pytest.com',
            disuse_flag = '0',
            last_update_timestamp = datetime.datetime(2020, 6, 4, 12, 0, 0, tzinfo=datetime.timezone.utc),
            last_update_user = 'pytest'
        ).save(force_insert=True)


    def del_test_data(self):
        """
        テストデータの削除
        """

        RuleType.objects.all().delete()


    def test_ok(self):
        """
        正常系
        """

        self.del_test_data()
        self.set_test_data()

        filter_info = {
            'rule_type_id': {'LIST': [9999, ]},
            'rule_type_name': {'LIKE': 'pytest_'},
            'label_count': {'END': '1'},
            'generation_limit': {'START': '4'},
            'last_update_timestamp': {'FROM': '2020-06-03', 'TO': '2020-06-05', }
        }

        table_list = _select(filter_info)

        assert len(table_list) == 1

        self.del_test_data()


# やることリスト
#   DecisionTableAuthByRuleモック化
#   バリデーションチェックモック化
#   RuleType,Groupに予めデータ挿入 済
#   リクエストデータ準備（rule_type_idは同じ）
#   レスポンスを投げる
#   assert response_data['status'] == 'success'
#   データ削除　済


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
class TestModifyDetail:
    """
    modify_detail テストクラス
    """

    def set_test_data(self):
        """
        テストデータの作成
        """

        RuleType(
            rule_type_id = 9999,
            rule_type_name = 'pytest_name',
            summary = None,
            rule_table_name = 'pytest_table',
            generation_limit = 5,
            group_id = 'pytest_com',
            artifact_id = 'pytest_oase',
            container_id_prefix_staging = 'test',
            container_id_prefix_product = 'prod',
            current_container_id_staging = None,
            current_container_id_product = None,
            label_count = 1,
            unknown_event_notification = '1',
            mail_address = 'pytest@pytest.com',
            disuse_flag = '0',
            last_update_timestamp = datetime.datetime(2020, 6, 4, 12, 0, 0, tzinfo=datetime.timezone.utc),
            last_update_user = 'pytest',
        ).save(force_insert=True)

        Group(
            group_id = 1,
            group_name = 'pytest管理者',
            summary = '',
            ad_data_flag = '0',
            last_update_timestamp = datetime.datetime(2020, 6, 4, 12, 0, 0, tzinfo=datetime.timezone.utc),
            last_update_user = 'pytest',
        ).save(force_insert=True)


    def del_test_data(self):
        """
        テストデータの削除
        """

        RuleType.objects.all().delete()
        Group.objects.all().delete()

    @pytest.mark.django_db
    def test_modidy_detail_ok(self, monkeypatch):
        """
        抽出条件テーブル登録処理
        ※ 正常系
        """
        admin = get_adminstrator()
        self.del_test_data
        self.set_test_data

        # 変更データ
        json_str = {"table_info":{"rule_type_name":"pytest","summary":""},"group_list":[],"notificationInfo":{"notification-flag":"1","mail_address":"aaa@aaa.com"}}
        json_data = json.dumps(json_str)

        response = admin.post('/oase_web/rule/decision_table/modify/15/', {'json_str':json_data})

        assert response.status_code == 200

        self.del_test_data


    def test_modidy_detail_ng(self):
        """
        抽出条件テーブル登録処理
        ※ 異常系
        """
        admin = get_adminstrator()
        self.del_test_data
        self.set_test_data

        # 変更データ
        json_str = {"table_info":{"rule_type_name":"pytest","summary":""},"group_list":[],"notificationInfo":{"notification-flag":"1","mail_address":"aaaaaacom"}}
        json_data = json.dumps(json_str)

        response = admin.post('/oase_web/rule/decision_table/modify/15/', {'json_str':json_data})
        assert response.status_code != 200

        self.del_test_data
