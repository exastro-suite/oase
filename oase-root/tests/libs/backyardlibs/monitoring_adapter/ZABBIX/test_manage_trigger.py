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
from importlib import import_module

from django.db import transaction


@pytest.mark.django_db
def test_create(zabbix_table):
    """
    ZabbixTriggerHistoryのレコードを作成するテスト
    """

    backyardlibs_module = import_module('libs.backyardlibs.monitoring_adapter.ZABBIX.manage_trigger')
    ManageTrigger = getattr(backyardlibs_module, 'ManageTrigger')

    zabbix_adapter_id = 1
    m = ManageTrigger(zabbix_adapter_id, 'oase')
    zabbix_trigger_his = m.create(1, 10000, 'testuser')

    assert zabbix_trigger_his.zabbix_adapter_id == 1 
    assert zabbix_trigger_his.trigger_id == 1
    assert zabbix_trigger_his.lastchange == 10000
    assert zabbix_trigger_his.last_update_user == 'testuser'


@pytest.mark.django_db
def test_update(zabbix_table):
    """
    ZabbixTriggerHistoryのレコードを更新するテスト
    """

    backyardlibs_module = import_module('libs.backyardlibs.monitoring_adapter.ZABBIX.manage_trigger')
    ManageTrigger = getattr(backyardlibs_module, 'ManageTrigger')

    zabbix_adapter_id = 1
    m = ManageTrigger(zabbix_adapter_id, 'oase')
    zabbix_trigger_his = m.create(1, 10000, 'testuser')
    m.update(zabbix_trigger_his,  20000, 'testuser2')

    assert zabbix_trigger_his.zabbix_adapter_id == 1
    assert zabbix_trigger_his.trigger_id == 1
    assert zabbix_trigger_his.lastchange == 20000
    assert zabbix_trigger_his.last_update_user == 'testuser2'


@pytest.mark.django_db
def test_delete_resolved_records(zabbix_table):
    """
    解決済みの障害のレコードが削除されていることを確認するテスト
    zabbixで障害が発生→障害解決のシミュレーションをし、テーブルのレコード数
    の増減を確認している。
    """

    module = import_module('web_app.models.ZABBIX_monitoring_models')
    backyardlibs_module = import_module('libs.backyardlibs.monitoring_adapter.ZABBIX.manage_trigger')
    ZabbixTriggerHistory = getattr(module, 'ZabbixTriggerHistory')
    ManageTrigger = getattr(backyardlibs_module, 'ManageTrigger')

    zabbix_adapter_id = 1
    trigger_id = 1
    m = ManageTrigger(zabbix_adapter_id, 'oase')
    zabbix_trigger_his = m.create(trigger_id, 10000, 'testuser')
    result = ZabbixTriggerHistory.objects.all()    
    assert len(result) == 1

    trigger_history_list = [zabbix_trigger_his]
    active_trigger_id_list = []
    m.delete_resolved_records(trigger_history_list, active_trigger_id_list)

    result = ZabbixTriggerHistory.objects.all()
    assert len(result) == 0


@pytest.mark.django_db
def test_main(zabbix_table):
    """
    ManageTriggerクラスの機能テスト
    """

    module = import_module('web_app.models.ZABBIX_monitoring_models')
    backyardlibs_module = import_module('libs.backyardlibs.monitoring_adapter.ZABBIX.manage_trigger')
    ZabbixTriggerHistory = getattr(module, 'ZabbixTriggerHistory')
    ManageTrigger = getattr(backyardlibs_module, 'ManageTrigger')

    # ZABBIX監視マスタIDを渡してインスタンス作成
    zabbix_adapter_id = 1
    m = ManageTrigger(zabbix_adapter_id, 'oase')

    # 新規作成時
    triggerid_lastchange_list = [(1,11),(2,22)]
    r = m.main(triggerid_lastchange_list)
    assert r == [True, True]
    
    # 障害が再発した時と、障害が増えた場合
    triggerid_lastchange_list = [(1,13),(2,22),(3,33)]
    r = m.main(triggerid_lastchange_list)
    assert r == [True, False, True]
    
    # 障害が減った時
    triggerid_lastchange_list = [(2,33)]
    r = m.main(triggerid_lastchange_list)
    assert r == [True]
    
    # 削除されていたら登録されたレコードは1個になる
    trigger_history_list = ZabbixTriggerHistory.objects.filter(zabbix_adapter_id=zabbix_adapter_id)
    assert 1 == len(trigger_history_list)


