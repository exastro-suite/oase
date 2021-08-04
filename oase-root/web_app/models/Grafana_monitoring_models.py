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
#  DOSL18001:Grafana監視マスタ
#  DOSL18002:Grafana突合情報
#  DOSL19001:Grafana監視履歴管理
#  DOSL19002:Grafana障害取得履歴管理
#
#-------------------------------------------------------------------------------

#------------------------------------------------
# DOSL18001:Grafana監視マスタ
#------------------------------------------------
class GrafanaAdapter(models.Model):
    grafana_adapter_id    = models.AutoField("Grafana監視マスタID", primary_key=True)
    grafana_disp_name     = models.CharField("Grafana表示名", max_length=64, unique=True)
    uri                   = models.CharField("URI", max_length=512)
    username              = models.CharField("接続ユーザ", max_length=64)
    password              = models.CharField("接続パスワード", max_length=192)
    match_evtime          = models.CharField("突合情報(イベント発生日時)", max_length=128)
    match_instance        = models.CharField("突合情報(メトリック名)", max_length=128)
    rule_type_id          = models.IntegerField("ルール種別ID")
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user      = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_GRAFANA_ADAPTER'
        unique_together = (('hostname', 'rule_type_id'), )

    def __str__(self):
        return "%s(%s)" % (self.grafana_disp_name, str(self.grafana_adapter_id))


#------------------------------------------------
# DOSL18002:Grafana突合情報
#------------------------------------------------
class GrafanaMatchInfo(models.Model):
    grafana_match_id        = models.AutoField("Grafana突合情報ID", primary_key=True)
    grafana_adapter_id      = models.IntegerField("Grafana監視マスタID")
    data_object_id          = models.IntegerField("データオブジェクトID")
    grafana_response_key    = models.CharField("Grafana応答情報key", max_length=128)
    last_update_timestamp   = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user        = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_GRAFANA_MATCH_INFO'

    def __str__(self):
        return str(self.grafana_match_id)

#------------------------------------------------
# DOSL19001:Grafana監視履歴管理
#------------------------------------------------
class GrafanaMonitoringHistory(models.Model):
    grafana_monitoring_his_id    = models.AutoField("Grafana監視履歴ID", primary_key=True)
    grafana_adapter_id           = models.IntegerField("Grafana監視マスタID")
    grafana_lastchange           = models.DateTimeField("Grafana最終更新日時")
    status                       = models.IntegerField("ステータス")
    status_update_id             = models.CharField("ステータス更新ID", max_length=128, null=True, blank=True)
    last_update_timestamp        = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user             = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_GRAFANA_MONITORING_HISTORY'

    def __str__(self):
        return str(self.grafana_monitoring_his_id)

#------------------------------------------------
# DOSL19002:Grafana障害取得履歴管理
#------------------------------------------------
class GrafanaTriggerHistory(models.Model):
    grafana_trigger_his_id    = models.AutoField("Grafana障害取得履歴ID", primary_key=True)
    grafana_adapter_id        = models.IntegerField("Grafana監視マスタID")
    trigger_id                = models.CharField("トリガーID", max_length=256)
    lastchange                = models.IntegerField("トリガー最終更新日時")
    last_update_timestamp     = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user          = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_GRAFANA_TRIGGER_HISTORY'
        unique_together = ('grafana_adapter_id', 'trigger_id')

    def __str__(self):
        return str(self.grafana_trigger_his_id)
