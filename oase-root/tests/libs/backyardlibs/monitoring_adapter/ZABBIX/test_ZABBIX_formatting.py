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
  ZABBIX_fomatting tests


"""


import pytest
import django
import datetime
import traceback
import pytz

from django.db import transaction
from importlib import import_module
from web_app.models.models import RuleType, DataObject

################################################
# テスト用データ準備
################################################
# テスト用zabbixメッセージ
ZABBIX_MESSAGE = [{
                     'triggerid': '15984',
                     'expression': '{18215}>20',
                     'description': 'CPU usage is 20%',
                     'url': '',
                     'status': '0',
                     'value': '1',
                     'priority': '2',
                     'lastchange': '1572936568',
                     'comments': '最近 2 分間の CPU 使用率の平均が 20 % を超えています',
                     'error': '',
                     'templateid': '15920',
                     'type': '0',
                     'state': '0',
                     'flags': '0',
                     'recovery_mode': '0',
                     'recovery_expression': '',
                     'correlation_mode': '0',
                     'correlation_tag': '',
                     'manual_close': '1',
                     'details': '',
                     'hosts': [
                       {
                         'hostid': '10084',
                         'host': 'Zabbix server'
                       }
                     ]
                   },
                   {
                     'triggerid': '15985',
                     'expression': '{18216}>50',
                     'description': 'CPU usage is 50%',
                     'url': '',
                     'status': '0',
                     'value': '1',
                     'priority': '3',
                     'lastchange': '1572936818',
                     'comments': '最近 2 分間の CPU 使用率の平均が 50 % を超えています',
                     'error': '',
                     'templateid': '15981',
                     'type': '0',
                     'state': '0',
                     'flags': '0',
                     'recovery_mode': '0',
                     'recovery_expression': '',
                     'correlation_mode': '0',
                     'correlation_tag': '',
                     'manual_close': '1',
                     'details': '',
                     'hosts': [
                       {
                         'hostid': '10084',
                         'host': 'Zabbix server'
                       }
                     ]
                   }]

# 整形後zabbixメッセージ
FORMAT_RESULT ={'request': [
                  {
                     'decisiontable': 'ZABBIX_TEST用',
                     'requesttype': '1',
                     'eventdatetime': '2019/11/05 15:49:28',
                     'eventinfo': ['15984', 'CPU usage is 20%']
                  },
                  {
                     'decisiontable': 'ZABBIX_TEST用',
                     'requesttype': '1',
                     'eventdatetime': '2019/11/05 15:53:38',
                     'eventinfo': ['15985', 'CPU usage is 50%']
                  }
              ]}

# key_list
KEY_LIST = ['triggerid', 'description']

# 正常系用data_dic
OK_DATA_DIC = {
               'triggerid': '15984',
               'expression': '{18215}>20',
               'description': 'CPU usage is 20%',
               'url': '', 'status': '0',
               'value': '1', 'priority': '2',
               'lastchange': '1572936568',
               'comments': '最近 2 分間の CPU 使用率の平均が 20 % を超えています',
               'error': '',
               'templateid': '15920',
               'type': '0', 'state': '0',
               'flags': '0',
               'recovery_mode': '0',
               'recovery_expression': '',
               'correlation_mode': '0',
               'correlation_tag': '',
               'manual_close': '1',
               'details': '',
               'hosts': [{'hostid': '10084', 'host': 'Zabbix server'}]
           }

# 異常系用data_dic
NG_DATA_DIC = {
               'triggerid': '15984',
               'expression': '{18215}>20',
               'url': '', 'status': '0',
               'value': '1', 'priority': '2',
               'lastchange': '1572936568',
               'comments': '最近 2 分間の CPU 使用率の平均が 20 % を超えています',
               'error': '',
               'templateid': '15920',
               'type': '0', 'state': '0',
               'flags': '0',
               'recovery_mode': '0',
               'recovery_expression': '',
               'correlation_mode': '0',
               'correlation_tag': '',
               'manual_close': '1',
               'details': '',
               'hosts': [{'hostid': '10084', 'host': 'Zabbix server'}]
           }

# 整形後zabbixメッセージ
EVENT_INFO = ['15984', 'CPU usage is 20%']


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

    # テーブル初期化
    RuleType.objects.all().delete()
    DataObject.objects.all().delete()


################################################
# テスト
################################################
def test_formatting_eventinfo():
    """
    zabbixメッセージの整形テスト
    """

    backyardlibs_module = import_module('libs.backyardlibs.monitoring_adapter.ZABBIX.ZABBIX_formatting')
    formatting_eventinfo = getattr(backyardlibs_module, 'formatting_eventinfo')


    # データ整形異常ルート
    eventinfo = []
    result = formatting_eventinfo(KEY_LIST, NG_DATA_DIC, eventinfo)
    assert result == False

    # データ整形正常ルート
    eventinfo = []
    result = formatting_eventinfo(KEY_LIST, OK_DATA_DIC, eventinfo)
    assert result == True
    assert EVENT_INFO == eventinfo


@pytest.mark.django_db
def test_message_formatting(zabbix_table):
    """
    zabbixメッセージをリクエストデータに整形するテスト
    """

    # インポート
    backyardlibs_module = import_module('libs.backyardlibs.monitoring_adapter.ZABBIX.ZABBIX_formatting')
    message_formatting  = getattr(backyardlibs_module, 'message_formatting')


    # 試験データセット
    rule_type_id, zabbix_adapter_id = set_data()

    # メッセージデータなし
    res, data = message_formatting('', rule_type_id, zabbix_adapter_id)
    assert res == False
    assert 0 == len(data)

    # rule_type_idなし
    res, data = message_formatting(ZABBIX_MESSAGE, None, zabbix_adapter_id)
    assert res == False
    assert 0 == len(data)

    # zabbix_adapter_idなし
    res, data = message_formatting(ZABBIX_MESSAGE, rule_type_id, None)
    assert res == False
    assert 0 == len(data)

    # RuleType.DoesNotExist
    res, data = message_formatting(ZABBIX_MESSAGE, 100, zabbix_adapter_id)
    assert res == False
    assert 0 == len(data)

    # exception
    res, data = message_formatting(ZABBIX_MESSAGE, 'test', zabbix_adapter_id)
    assert res == False
    assert 0 == len(data)

    # メイン正常ルート
    res, data = message_formatting(ZABBIX_MESSAGE, rule_type_id, zabbix_adapter_id)
    assert res == True
    assert FORMAT_RESULT == data

    # 試験データ初期化
    delete_data()

