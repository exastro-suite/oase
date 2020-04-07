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

from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.utils import timezone
from django.core.validators import MinLengthValidator, MinValueValidator
#-------------------------------------------------------------------------------
#
#【概要】
#  OASEテーブル定義
#【特記事項】
#  記録履歴：
#
#【その他】
#
#【テーブル定義】
#  DOSL12001:ZABBIX監視マスタ
#  DOSL12002:ZABBIX突合情報
#  DOSL13001:ZABBIX監視履歴管理
#  DOSL13002:ZABBIX障害取得履歴管理
#
#-------------------------------------------------------------------------------

#------------------------------------------------
# DOSL12001:ZABBIX監視マスタ
#------------------------------------------------
class ZabbixAdapter(models.Model):
    zabbix_adapter_id       = models.AutoField("ZABBIX監視マスタID", primary_key=True)
    zabbix_disp_name        = models.CharField("ZABBIX表示名", max_length=64, unique=True)
    hostname                = models.CharField("ホスト名", max_length=128)
    username                = models.CharField("接続ユーザ", max_length=64)
    password                = models.CharField("接続パスワード", max_length=192)
    protocol                = models.CharField("プロトコル", max_length=8)
    port                    = models.IntegerField("ポート番号")
    rule_type_id            = models.IntegerField("ルール種別ID")
    last_update_timestamp   = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user        = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_ZABBIX_ADAPTER'
        unique_together = (('hostname', 'rule_type_id'), )

    def __str__(self):
        return "%s(%s)" % (self.zabbix_disp_name, str(self.zabbix_adapter_id))


#------------------------------------------------
# DOSL12002:ZABBIX突合情報
#------------------------------------------------
class ZabbixMatchInfo(models.Model):
    zabbix_match_id         = models.AutoField("ZABBIX突合情報ID", primary_key=True)
    zabbix_adapter_id       = models.IntegerField("ZABBIX監視マスタID")
    data_object_id          = models.IntegerField("データオブジェクトID")
    zabbix_response_key     = models.CharField("ZABBIX応答情報key", max_length=32)
    last_update_timestamp   = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user        = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_ZABBIX_MATCH_INFO'

    def __str__(self):
        return str(self.zabbix_match_id)

#------------------------------------------------
# DOSL13001:ZABBIX監視履歴管理
#------------------------------------------------
class ZabbixMonitoringHistory(models.Model):
    zabbix_monitoring_his_id   = models.AutoField("ZABBIX監視履歴ID", primary_key=True)
    zabbix_adapter_id          = models.IntegerField("ZABBIX監視マスタID")
    zabbix_lastchange          = models.IntegerField("ZABBIX最終更新日時")
    status                     = models.IntegerField("ステータス")
    status_update_id           = models.CharField("ステータス更新ID", max_length=128, null=True, blank=True)
    last_update_timestamp      = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user           = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_ZABBIX_MONITORING_HISTORY'

    def __str__(self):
        return str(self.zabbix_monitoring_his_id)

#------------------------------------------------
# DOSL13002:ZABBIX障害取得履歴管理
#------------------------------------------------
class ZabbixTriggerHistory(models.Model):
    zabbix_trigger_his_id = models.AutoField("ZABBIX障害取得履歴ID", primary_key=True)
    zabbix_adapter_id     = models.IntegerField("ZABBIX監視マスタID")
    trigger_id            = models.IntegerField("トリガーID")
    lastchange            = models.IntegerField("トリガー最終更新日時")
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user      = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_ZABBIX_TRIGGER_HISTORY'
        unique_together = ('zabbix_adapter_id', 'trigger_id')

    def __str__(self):
        return str(self.zabbix_trigger_his_id)
