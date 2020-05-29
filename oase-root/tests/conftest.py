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
import os
import configparser
import datetime
import pytz
from importlib import import_module

from django.db import connection
from django.core.management import call_command
from django.test import Client

from libs.commonlibs.common import Common
from web_app.models.models import User, PasswordHistory


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


def create_tables(conf_file_path):
    """
    コンフィグファイルからテーブルを作成する

    [引数]
    conf_file_path: 各ドライバーやアダプターのconfファイルパス
    """

    config = configparser.ConfigParser()
    config.read(conf_file_path)
    if config:
        icnt = 1
        while True:
            sec_key = 'models'
            opt_sql_key = 'query' + str(icnt)

            if not config.has_section(sec_key) or not config.has_option(sec_key, opt_sql_key):
                break

            query = config.get(sec_key, opt_sql_key)
            with connection.cursor() as cursor:
                cursor.execute(query)
                cursor.close()

            icnt += 1


def delete_records(tables):
    """
    テーブルのレコードを全件削除する
    [引数]
    tables: レコードを削除したいテーブル名のリスト
    """

    for table in tables:
        query = 'DELETE FROM {};'.format(table)
        with connection.cursor() as cursor:
            cursor.execute(query)
            cursor.close()


@pytest.fixture()
def zabbix_table(django_db_blocker):
    """
    セットアップ：
        ZABBIX.confを使ってzabbixアダプター関連のテーブルを追加する
    ティアダウン：
        zabbixアダプター関連のレコードを全削除

    """

    oase_path = os.path.dirname(os.path.abspath(__file__)).split('oase-root')
    conf_filepath = oase_path[0] + 'tool/conf/ZABBIX.conf'

    create_tables(conf_filepath)

    yield

    module = import_module('web_app.models.ZABBIX_monitoring_models')
    getattr(module, 'ZabbixAdapter').objects.all().delete()
    getattr(module, 'ZabbixMatchInfo').objects.all().delete()
    getattr(module, 'ZabbixMonitoringHistory').objects.all().delete()
    getattr(module, 'ZabbixTriggerHistory').objects.all().delete()


@pytest.fixture()
def ita_table(django_db_blocker):
    """
    セットアップ：
        ITA.confを使ってitaアダプター関連のテーブルを追加する
    ティアダウン：
        itaアダプター関連のレコードを全削除
    """
    oase_path = os.path.dirname(os.path.abspath(__file__)).split('oase-root')
    conf_filepath = oase_path[0] + 'tool/conf/ITA.conf'

    create_tables(conf_filepath)

    yield

    module = import_module('web_app.models.ITA_models')
    getattr(module, 'ItaActionHistory').objects.all().delete()
    getattr(module, 'ItaDriver').objects.all().delete()
    getattr(module, 'ItaParameterMatchInfo').objects.all().delete()
    getattr(module, 'ItaParametaCommitInfo').objects.all().delete()
    getattr(module, 'ItaParameterItemInfo').objects.all().delete()


@pytest.fixture()
def django_db_setup(django_db_setup, django_db_blocker):
    """
    dbに共通の初期値をロードする
    """
    with django_db_blocker.unblock():
        call_command('loaddata', 'init.yaml')


@pytest.fixture(name='admin')
def login_administrator(django_db_setup, django_db_blocker):
    """
    dbに共通の初期値をロードし、ログイン可能なadministratorを渡す
    """
    with django_db_blocker.unblock():
        call_command('loaddata', 'init.yaml')

    admin = get_adminstrator()

    yield admin


@pytest.fixture()
def django_db_setup_with_system_dmsettings(django_db_blocker):
    """
    dbにシステム（DMSETTINGS）の初期値をロードする
    """
    with django_db_blocker.unblock():
        call_command('loaddata', 'init.yaml')
        call_command('loaddata', 'tests/fixtures/system_dmsettings.yaml')
