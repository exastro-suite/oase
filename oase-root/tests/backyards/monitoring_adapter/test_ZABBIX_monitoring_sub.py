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
import django
import configparser
import datetime
import traceback
import pytz

from importlib import import_module
from django.db import transaction

from web_app.models.models import RuleType, DataObject

oase_root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..')
os.environ['OASE_ROOT_DIR'] = oase_root_dir
os.environ['RUN_INTERVAL']  = '3'
os.environ['PYTHON_MODULE'] = '/usr/bin/python3'
os.environ['LOG_LEVEL']     = "TRACE"
os.environ['LOG_DIR']       = oase_root_dir + "/logs/backyardlogs/oase_monitoring"


################################################
# テスト用DB操作
################################################
def set_data():
    """
    テストに必要なデータをDBに登録
    """
    now = datetime.datetime.now(pytz.timezone('UTC'))
    module = import_module('web_app.models.ZABBIX_monitoring_models')
    ZabbixAdapter           = getattr(module, 'ZabbixAdapter')
    ZabbixMatchInfo         = getattr(module, 'ZabbixMatchInfo')

    try:
        with transaction.atomic():

            # テスト用DT作成
            rule_type = RuleType(
                rule_type_name              = 'ZABBIX_TEST用',
                summary                     = '',
                rule_table_name             = 'zabbixtest',
                generation_limit            = 3,
                group_id                    = 'com.oase',
                artifact_id                 = 'zabbix',
                container_id_prefix_staging = 'testzabbix',
                container_id_prefix_product = 'prodzabbix',
                label_count                 = '2',
                last_update_timestamp       = now,
                last_update_user            = 'administrator'
            )
            rule_type.save(force_insert=True)

            # テスト用ラベル作衛
            label0 = DataObject(
                rule_type_id              = rule_type.rule_type_id,
                conditional_name          = 'トリガーID',
                label                     = 'label0',
                conditional_expression_id = 1,
                last_update_timestamp     = now,
                last_update_user          = 'administrator'
            )
            label0.save(force_insert=True)

            label1 = DataObject(
                rule_type_id              = rule_type.rule_type_id,
                conditional_name          = '説明',
                label                     = 'label1',
                conditional_expression_id = 2,
                last_update_timestamp     = now,
                last_update_user          = 'administrator'
            )
            label1.save(force_insert=True)

            # テスト用ZABBIX監視アダプタ作成
            zabbix = ZabbixAdapter(
                zabbix_disp_name          = 'ZABBIX',
                hostname                  = 'pytest-host',
                username                  = 'pytest',
                password                  = 'pytest',
                protocol                  = 'http',
                port                      = 80,
                rule_type_id              = rule_type.rule_type_id,
                last_update_timestamp     = now,
                last_update_user          = 'administrator'
            
            )
            zabbix.save(force_insert=True)

            # テスト用ZABBIX突合情報作成
            match1 = ZabbixMatchInfo(
                zabbix_adapter_id         = zabbix.zabbix_adapter_id,
                data_object_id            = label0.data_object_id,
                zabbix_response_key       = 'triggerid',
                last_update_timestamp     = now,
                last_update_user          = 'administrator'
            )
            match1.save(force_insert=True)

            match2 = ZabbixMatchInfo(
                zabbix_adapter_id         = zabbix.zabbix_adapter_id,
                data_object_id            = label1.data_object_id,
                zabbix_response_key       = 'description',
                last_update_timestamp     = now,
                last_update_user          = 'administrator'
            )
            match2.save(force_insert=True)

            return rule_type.rule_type_id, zabbix.zabbix_adapter_id

    except Exception as e:
        print(e)


def delete_data():
    """
    テストで使用したデータの削除
    zabbix関連テーブルは試験後に削除されているので不要
    """

    module = import_module('web_app.models.ZABBIX_monitoring_models')
    ZabbixAdapter           = getattr(module, 'ZabbixAdapter')
    ZabbixMatchInfo         = getattr(module, 'ZabbixMatchInfo')

    # テーブル初期化
    RuleType.objects.all().delete()
    DataObject.objects.all().delete()
    ZabbixAdapter.objects.all().delete()
    ZabbixMatchInfo.objects.all().delete()


@pytest.mark.django_db
def test_insert_monitoring_history(zabbix_table):
    """
    ZabbixMonitoringHistoryのレコードを作成するテスト
    """

    backyards_module        = import_module('backyards.monitoring_adapter.ZABBIX_monitoring_sub')
    ZabbixAdapterSubModules = getattr(backyards_module, 'ZabbixAdapterSubModules')

    zabbix_adapter_id = 1
    z = ZabbixAdapterSubModules(zabbix_adapter_id)
    zabbix_monitoring_his = z.insert_monitoring_history(10000, 1)

    assert zabbix_monitoring_his.zabbix_adapter_id == 1
    assert zabbix_monitoring_his.zabbix_lastchange == 10000
    assert zabbix_monitoring_his.status == 1
    assert zabbix_monitoring_his.last_update_user == 'ZABBIXアダプタプロシージャ'

    zabbix_adapter_id = 2
    z = ZabbixAdapterSubModules(zabbix_adapter_id)
    zabbix_monitoring_his = z.insert_monitoring_history(10000, 'aaa')

    assert zabbix_monitoring_his == None


@pytest.mark.django_db
def test_update_monitoring_history(zabbix_table):
    """
    ZabbixMonitoringHistoryのレコードを更新するテスト
    """

    backyards_module        = import_module('backyards.monitoring_adapter.ZABBIX_monitoring_sub')
    ZabbixAdapterSubModules = getattr(backyards_module, 'ZabbixAdapterSubModules')

    zabbix_adapter_id = 1
    z = ZabbixAdapterSubModules(zabbix_adapter_id)
    zabbix_monitoring_his = z.insert_monitoring_history(10000, 1)

    # テストコードのため、インスタンス変数に格納
    z.monitoring_history = zabbix_monitoring_his

    result = z.update_monitoring_history(2, 20000)
    assert result == True

    with pytest.raises(Exception):
        result = z.update_monitoring_history('aaa', 20000)
        assert False


@pytest.mark.django_db
def test_execute(zabbix_table, monkeypatch):
    """
    監視実行するテスト
    """

    zabbix_adapter = None
    module         = import_module('web_app.models.ZABBIX_monitoring_models')
    ZabbixAdapter  = getattr(module, 'ZabbixAdapter')
    backyards_module        = import_module('backyards.monitoring_adapter.ZABBIX_monitoring_sub')
    ZabbixAdapterSubModules = getattr(backyards_module, 'ZabbixAdapterSubModules')
    module = import_module('libs.backyardlibs.monitoring_adapter.ZABBIX.ZABBIX_api')
    ZabbixAPI = getattr(module, 'ZabbixApi')

    delete_data()
    rule_type_id, zabbix_adapter_id = set_data()

    zabbix_adapter = ZabbixAdapter.objects.get(pk=zabbix_adapter_id)
    z = ZabbixAdapterSubModules(zabbix_adapter_id)

    # 異常系(接続エラー)
    result, api_response, last_monitoring_time = z.execute(zabbix_adapter, 10000)

    assert result == False

    # 異常系(TypeError)
    monkeypatch.setattr(ZabbixAPI, '_request', lambda a, b, c: ({'result':'test_token'}))

    result, api_response, last_monitoring_time = z.execute(zabbix_adapter, 'aaa')

    assert result == False

    # 正常系
    monkeypatch.setattr(ZabbixAPI, 'get_active_triggers', lambda a, b: (0))
    monkeypatch.setattr(ZabbixAPI, '_request', lambda a, b, c: ({'result':'test_token'}))

    result, api_response, last_monitoring_time = z.execute(zabbix_adapter, 10000)

    assert result == True
    assert last_monitoring_time == 0

    delete_data()


@pytest.mark.django_db
def test_do_workflow(zabbix_table, monkeypatch):
    """
    監視実行するテスト
    """

    backyards_module        = import_module('backyards.monitoring_adapter.ZABBIX_monitoring_sub')
    ZabbixAdapterSubModules = getattr(backyards_module, 'ZabbixAdapterSubModules')
    module = import_module('libs.backyardlibs.monitoring_adapter.ZABBIX.ZABBIX_api')
    ZabbixAPI = getattr(module, 'ZabbixApi')

    delete_data()
    rule_type_id, zabbix_adapter_id = set_data()

    monkeypatch.setattr(ZabbixAPI, 'get_active_triggers', lambda a, b: (0))
    monkeypatch.setattr(ZabbixAPI, '_request', lambda a, b, c: ({'result':'test_token'}))

    z = ZabbixAdapterSubModules(zabbix_adapter_id)
    result = z.do_workflow()

    assert result == True

    delete_data()

