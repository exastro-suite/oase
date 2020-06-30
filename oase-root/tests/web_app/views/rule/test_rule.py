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
import requests

from django.urls import reverse
from django.http import Http404, HttpResponse
from django.test import Client, RequestFactory
from django.db import transaction
from django.conf import settings

from importlib import import_module

from libs.commonlibs.common import Common
from libs.webcommonlibs.user_config import UserConfig
from web_app.models.models import User, PasswordHistory, RuleType, DataObject
from web_app.views.rule import rule as rule_view


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
class TestRulePseudoRequest:
    """
    テストリクエストのテストクラス
    """

    ############################################################
    # テストデータ
    ############################################################
    def set_test_data(self):
        """
        テストデータの作成
        """

        # ルール種別
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

        # ルール条件
        DataObject(
            data_object_id = 99991,
            rule_type_id = 9999,
            conditional_name = 'pytest_cond1',
            label = 'label0',
            conditional_expression_id = 3,
            last_update_timestamp = datetime.datetime(2020, 6, 4, 12, 0, 0, tzinfo=datetime.timezone.utc),
            last_update_user = 'pytest'
        ).save(force_insert=True)

        DataObject(
            data_object_id = 99992,
            rule_type_id = 9999,
            conditional_name = 'pytest_cond2',
            label = 'label1',
            conditional_expression_id = 3,
            last_update_timestamp = datetime.datetime(2020, 6, 4, 12, 0, 0, tzinfo=datetime.timezone.utc),
            last_update_user = 'pytest'
        ).save(force_insert=True)


    def del_test_data(self):
        """
        テストデータの削除
        """

        RuleType.objects.filter(last_update_user='pytest').delete()
        DataObject.objects.filter(last_update_user='pytest').delete()


    ############################################################
    # ダミー関数
    ############################################################
    def dummy_post_ok(*args, **kwargs):
        """
        テストリクエストの結果応答(正常)
        """

        resp_json = {
            'result' : True,
            'msg'      : 'msg_pytest_OK',
            'trace_id' : 'TOS_pytest_OK',
        }

        resp_json = json.dumps(resp_json, ensure_ascii=False)

        return HttpResponse(resp_json)

    def dummy_post_ng(*args, **kwargs):
        """
        テストリクエストの結果応答(正常)
        """

        resp_json = {
            'result' : False,
            'msg'      : 'Unexpected error',
            'trace_id' : 'TOS_pytest_NG',
        }

        resp_json = json.dumps(resp_json, ensure_ascii=False)

        return HttpResponse(resp_json)

    def dummy_bulk_data(*args, **kwargs):
        """
        一括テストリクエストのテストデータ
        """

        bulk_data_list = [
            {'row':3, 'label0':'pytest1', 'label1':'pytest2'},
            {'row':4, 'label0':'pytest1', 'label1':'pytest2'},
        ]

        return bulk_data_list, '', []

    def dummy_pass(*args, **kwargs):
        """
        実態なし
        """

        pass


    ############################################################
    # テスト(単一テストリクエスト)
    ############################################################
    @pytest.mark.django_db
    def test_ok(self, monkeypatch):
        """
        単一テストリクエスト
        ※ 正常系
        """

        admin = get_adminstrator()
        self.del_test_data()
        self.set_test_data()

        monkeypatch.setattr(UserConfig, 'get_activerule_auth_type', lambda a, b, c:[9999,])
        monkeypatch.setattr(rule_view, '_validate_eventdatetime', self.dummy_pass)
        monkeypatch.setattr(rule_view, '_validate_eventinfo', self.dummy_pass)
        monkeypatch.setattr(requests, 'post', self.dummy_post_ok)

        json_data = {
            "decisiontable":"pytest_name",
            "requesttype":"2",
            "eventdatetime":"2020-01-01 00:00:00",
            "eventinfo":["pytest1", "pytest2"]
        }
        json_str = json.dumps(json_data)

        response = admin.post('/oase_web/rule/rule/pseudo_request/9999', {'json_str':json_str})
        resp_content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert resp_content['err_flg'] == 0

        self.del_test_data()


    @pytest.mark.django_db
    def test_ng(self, monkeypatch):
        """
        単一テストリクエスト
        ※ 異常系
        """

        admin = get_adminstrator()
        self.del_test_data()
        self.set_test_data()

        monkeypatch.setattr(UserConfig, 'get_activerule_auth_type', lambda a, b, c:[9999,])
        monkeypatch.setattr(rule_view, '_validate_eventdatetime', self.dummy_pass)
        monkeypatch.setattr(rule_view, '_validate_eventinfo', self.dummy_pass)
        monkeypatch.setattr(requests, 'post', self.dummy_post_ng)

        json_data = {
            "decisiontable":"pytest_name",
            "requesttype":"2",
            "eventdatetime":"2020-01-01 00:00:00",
            "eventinfo":["pytest1", "pytest2"]
        }
        json_str = json.dumps(json_data)

        response = admin.post('/oase_web/rule/rule/pseudo_request/9999', {'json_str':json_str})
        resp_content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert resp_content['err_flg'] > 0

        self.del_test_data()


    ############################################################
    # テスト(一括テストリクエスト)
    ############################################################
    @pytest.mark.django_db
    def test_bulk_ok(self, monkeypatch):
        """
        一括テストリクエスト
        ※ 正常系
        """

        admin = get_adminstrator()
        self.del_test_data()
        self.set_test_data()

        monkeypatch.setattr(rule_view, '_testrequest_upload', self.dummy_bulk_data)
        monkeypatch.setattr(UserConfig, 'get_activerule_auth_type', lambda a, b, c:[9999,])
        monkeypatch.setattr(rule_view, '_validate_eventdatetime', self.dummy_pass)
        monkeypatch.setattr(rule_view, '_validate_eventinfo', self.dummy_pass)
        monkeypatch.setattr(requests, 'post', self.dummy_post_ok)


        fpath = '%s/confs/frameworkconfs/settings.py.sample' % (settings.BASE_DIR)
        with open(fpath) as fp:
            response = admin.post('/oase_web/rule/rule/bulkpseudocall/9999/', {'testreqfile':fp})
            resp_content = json.loads(response.content.decode('utf-8'))


        assert response.status_code == 200
        assert resp_content['result'] == 'OK'

        self.del_test_data()


    @pytest.mark.django_db
    def test_bulk_ng(self, monkeypatch):
        """
        一括テストリクエスト
        ※ 異常系
        """

        admin = get_adminstrator()
        self.del_test_data()
        self.set_test_data()

        monkeypatch.setattr(rule_view, '_testrequest_upload', self.dummy_bulk_data)
        monkeypatch.setattr(UserConfig, 'get_activerule_auth_type', lambda a, b, c:[9999,])
        monkeypatch.setattr(rule_view, '_validate_eventdatetime', self.dummy_pass)
        monkeypatch.setattr(rule_view, '_validate_eventinfo', self.dummy_pass)
        monkeypatch.setattr(requests, 'post', self.dummy_post_ng)


        fpath = '%s/confs/frameworkconfs/settings.py.sample' % (settings.BASE_DIR)
        with open(fpath) as fp:
            response = admin.post('/oase_web/rule/rule/bulkpseudocall/9999/', {'testreqfile':fp})
            resp_content = json.loads(response.content.decode('utf-8'))


        assert response.status_code == 200
        assert resp_content['result'] == 'NG'

        self.del_test_data()



