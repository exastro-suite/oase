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
#  DOSL22001:Mail監視マスタ
#  DOSL22002:Mail突合情報
#  DOSL22003:Mail監視履歴管理
#  DOSL22004:Mail障害取得履歴管理
#
#-------------------------------------------------------------------------------

#------------------------------------------------
# DOSL22001:Mail監視マスタ
#------------------------------------------------
class MailAdapter(models.Model):
    mail_adapter_id       = models.AutoField("Mail監視マスタID", primary_key=True)
    mail_disp_name        = models.CharField("Mail表示名", max_length=64, unique=True)
    imap_server           = models.CharField("接続先IMAPサーバー", max_length=64)
    encryption_protocol   = models.IntegerField("暗号化プロトコル")
    port                  = models.IntegerField("ポート番号")
    user                  = models.CharField("接続ユーザ", max_length=64, null=True, blank=True)
    password              = models.CharField("接続パスワード", max_length=192, null=True, blank=True)
    rule_type_id          = models.IntegerField("ルール種別ID")
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user      = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_MAIL_ADAPTER'

    def __str__(self):
        return "%s(%s)" % (self.mail_disp_name, str(self.mail_adapter_id))


#------------------------------------------------
# DOSL22002:Mail突合情報
#------------------------------------------------
class MailMatchInfo(models.Model):
    mail_match_id         = models.AutoField("Mail突合情報ID", primary_key=True)
    mail_adapter_id       = models.IntegerField("Mail監視マスタID")
    data_object_id        = models.IntegerField("データオブジェクトID")
    mail_response_key     = models.CharField("Mail応答情報key", max_length=128)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user      = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_MAIL_MATCH_INFO'

    def __str__(self):
        return str(self.mail_match_id)

#------------------------------------------------
# DOSL22003:Mail監視履歴管理
#------------------------------------------------
class MailMonitoringHistory(models.Model):
    mail_monitoring_his_id = models.AutoField("Mail監視履歴ID", primary_key=True)
    mail_adapter_id        = models.IntegerField("Mail監視マスタID")
    mail_lastchange        = models.DateTimeField("Mail最終更新日時")
    status                 = models.IntegerField("ステータス")
    status_update_id       = models.CharField("ステータス更新ID", max_length=128, null=True, blank=True)
    last_update_timestamp  = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user       = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_MAIL_MONITORING_HISTORY'

    def __str__(self):
        return str(self.mail_monitoring_his_id)

#------------------------------------------------
# DOSL22004:Mail障害取得履歴管理
#------------------------------------------------
class MailTriggerHistory(models.Model):
    mail_trigger_his_id   = models.AutoField("Mail障害取得履歴ID", primary_key=True)
    mail_adapter_id       = models.IntegerField("Mail監視マスタID")
    trigger_id            = models.CharField("トリガーID", max_length=512)
    lastchange            = models.IntegerField("トリガー最終更新日時")
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user      = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_MAIL_TRIGGER_HISTORY'
        unique_together = ('mail_adapter_id', 'trigger_id')

    def __str__(self):
        return str(self.mail_trigger_his_id)

