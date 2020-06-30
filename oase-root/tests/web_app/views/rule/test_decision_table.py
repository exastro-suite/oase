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

import datetime
import json
from importlib import import_module

import pytest
import pytz
from django.db import transaction
from django.http import Http404
from django.test import Client, RequestFactory
from django.urls import reverse
from libs.commonlibs.common import Common
from libs.commonlibs.dt_component import DecisionTableComponent
from web_app.models.models import Group, PasswordHistory, RuleType, User
from web_app.views.rule.decision_table import DecisionTableAuthByRule, _select
from libs.webcommonlibs.common import RequestToApply

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
        抽出条件テーブル変更処理
        ※ 正常系
        """
        admin = get_adminstrator()
        self.del_test_data()
        self.set_test_data()

        monkeypatch.setattr(DecisionTableAuthByRule, 'allow_update', lambda a, auth_val=None, rule_type_id=0:True)

        # 変更データ
        json_str = {"table_info":{"rule_type_name":"pytest","summary":""},"group_list":[],"notificationInfo":{"unknown_event_notification":"1","mail_address":"pytest@example.com"}}
        json_data = json.dumps(json_str)

        response = admin.post('/oase_web/rule/decision_table/modify/9999/', {'add_record':json_data})
        resp_content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert resp_content['status'] == 'success'

        self.del_test_data()


    @pytest.mark.django_db
    def test_modidy_detail_ng(self, monkeypatch):
        """
        抽出条件テーブル変更処理
        ※ 異常系(メールアドレス不正)
        """
        admin = get_adminstrator()
        self.del_test_data()
        self.set_test_data()

        monkeypatch.setattr(DecisionTableAuthByRule, 'allow_update', lambda a, auth_val=None, rule_type_id=0:True)

        # 変更データ
        json_str = {"table_info":{"rule_type_name":"pytest","summary":""},"group_list":[],"notificationInfo":{"unknown_event_notification":"1","mail_address":"aaaaaacom"}}
        json_data = json.dumps(json_str)

        assert response.status_code == 200
        assert resp_content['status'] == 'failure'

        self.del_test_data()


    @pytest.mark.django_db
    def test_modify_ok(self, monkeypatch):
        """
        抽出条件テーブル登録処理
        ※ 正常系
        """
        admin = get_adminstrator()
        self.del_test_data()
        self.set_test_data()

        sample = {'request': 'CREATE', 'table_info': {'rule_type_name': 'pytest', 'summary': '', 'rule_table_name': 'id00000000001'}, 'data_obj_info': [{'conditional_name': 'a', 'label': 'label0', 'conditional_expression_id': 1}], 'notificationInfo': {'unknown_event_notification': '1', 'mail_address': 'pytest@example.com'}, 'user_id': 1, 'label_count': 1, 'lang': 'JA'}

        monkeypatch.setattr(RequestToApply, 'operate', lambda sample, request=None:(True, {}))

        # 登録データ
        json_str = {"table_info":{"rule_type_name":"pytest","summary":""},"data_obj_info":[{"conditional_name":"a","conditional_expression_id":"1","row_id":"New1"}],"group_list":[],"notificationInfo":{"unknown_event_notification":"1","mail_address":"pytest@example.com"}}
        json_data = json.dumps(json_str)

        response = admin.post('/oase_web/rule/decision_table/modify', {'add_record':json_data})
        resp_content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        self.del_test_data()


    @pytest.mark.django_db
    def test_modify_ng(self, monkeypatch):
        """
        抽出条件テーブル登録処理
        ※ 異常系(メールアドレス不正)
        """
        admin = get_adminstrator()
        self.del_test_data()

        monkeypatch.setattr(RequestToApply, 'operate', lambda RequestToApply, b, request=None:True)

        # 登録データ
        json_str = {"table_info":{"rule_type_name":"pytest","summary":""},"data_obj_info":[{"conditional_name":"a","conditional_expression_id":"1","row_id":"New1"}],"group_list":[],"notificationInfo":{"unknown_event_notification":"1","mail_address":"pytestexamplecom"}}
        json_data = json.dumps(json_str)

        response = admin.post('/oase_web/rule/decision_table/modify', {'add_record':json_data})
        resp_content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert resp_content['status'] == 'failure'

        self.del_test_data()
