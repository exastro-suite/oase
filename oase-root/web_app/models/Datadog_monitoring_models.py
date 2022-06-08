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
#  DOSL20001:Datadog監視マスタ
#  DOSL20002:Datadog突合情報
#  DOSL21001:Datadog監視履歴管理
#  DOSL21002:Datadog障害取得履歴管理
#
#-------------------------------------------------------------------------------

#------------------------------------------------
# DOSL20001:Datadog監視マスタ
#------------------------------------------------
class DatadogAdapter(models.Model):
    datadog_adapter_id        = models.AutoField("Datadog監視マスタID", primary_key=True)
    datadog_disp_name         = models.CharField("Datadog表示名", max_length=64, unique=True)
    uri                       = models.CharField("URI", max_length=512)
    api_key                   = models.CharField("APIキー", max_length=48)
    application_key           = models.CharField("Applicationキー", max_length=48)
    status_flag               = models.IntegerField("ステータスフラグ", default=0)
    proxy                     = models.CharField("プロキシ", max_length=256)
    rule_type_id              = models.IntegerField("ルール種別ID")
    match_evtime              = models.CharField("突合情報(イベント発生日時)", max_length=128)
    match_instance            = models.CharField("突合情報(マッチインスタンス名)", max_length=128)
    last_update_timestamp     = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user          = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_DATADOG_ADAPTER'

    def __str__(self):
        return "%s(%s)" % (self.datadog_disp_name, str(self.datadog_adapter_id))


#------------------------------------------------
# DOSL20002:Datadog突合情報
#------------------------------------------------
class DatadogMatchInfo(models.Model):
    datadog_match_id        = models.AutoField("Datadog突合情報ID", primary_key=True)
    datadog_adapter_id      = models.IntegerField("Datadog監視マスタID")
    data_object_id          = models.IntegerField("データオブジェクトID")
    datadog_response_key    = models.CharField("Datadog応答情報key", max_length=128)
    last_update_timestamp   = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user        = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_DATADOG_MATCH_INFO'

    def __str__(self):
        return str(self.datadog_match_id)

#------------------------------------------------
# DOSL21001:Datadog監視履歴管理
#------------------------------------------------
class DatadogMonitoringHistory(models.Model):
    datadog_monitoring_his_id    = models.AutoField("Datadog監視履歴ID", primary_key=True)
    datadog_adapter_id           = models.IntegerField("Datadog監視マスタID")
    datadog_lastchange           = models.DateTimeField("Datadog最終更新日時")
    status                       = models.IntegerField("ステータス")
    status_update_id             = models.CharField("ステータス更新ID", max_length=128, null=True, blank=True)
    last_update_timestamp        = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user             = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_DATADOG_MONITORING_HISTORY'

    def __str__(self):
        return str(self.datadog_monitoring_his_id)

#------------------------------------------------
# DOSL21002:Datadog障害取得履歴管理
#------------------------------------------------
class DatadogTriggerHistory(models.Model):
    datadog_trigger_his_id    = models.AutoField("Datadog障害取得履歴ID", primary_key=True)
    datadog_adapter_id        = models.IntegerField("Datadog監視マスタID")
    trigger_id                = models.CharField("トリガーID", max_length=11)
    lastchange                = models.IntegerField("トリガー最終更新日時")
    last_update_timestamp     = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user          = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_DATADOG_TRIGGER_HISTORY'
        unique_together = ('datadog_adapter_id', 'trigger_id')

    def __str__(self):
        return str(self.datadog_trigger_his_id)
