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
#  DOSL06006:ServiceNowアクション履歴管理
#  DOSL07010:ServiceNowアクションマスタ
#
#-------------------------------------------------------------------------------


#------------------------------------------------
# DOSL06006:ServiceNowアクション履歴管理
#------------------------------------------------
class ServiceNowActionHistory(models.Model):
    servicenow_action_his_id = models.AutoField("ServiceNowアクション履歴ID", primary_key=True)
    action_his_id            = models.IntegerField("アクション履歴ID", unique=True)
    servicenow_disp_name     = models.CharField("ServiceNow表示名", max_length=64)
    short_description        = models.CharField("概要説明", max_length=512)
    last_update_timestamp    = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user         = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_SERVICENOW_ACTION_HISTORY'

    def __str__(self):
        return str(self.servicenow_action_his_id)

#------------------------------------------------
# DOSL07010:ServiceNowアクションマスタ
#------------------------------------------------
class ServiceNowDriver(models.Model):
    servicenow_driver_id  = models.AutoField("ServiceNowアクションマスタ", primary_key=True)
    servicenow_disp_name  = models.CharField("ServiceNow表示名", max_length=64, unique=True)
    hostname              = models.CharField("ホスト名", max_length=128, unique=True)
    protocol              = models.CharField("プロトコル", max_length=8)
    port                  = models.IntegerField("ポート番号")
    username              = models.CharField("接続ユーザ", max_length=64)
    password              = models.CharField("接続パスワード", max_length=192)
    count                 = models.IntegerField("連携カウント")
    proxy                 = models.CharField("プロキシ", max_length=256)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user      = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_SERVICENOW_DRIVER'

    def __str__(self):
        return "%s(%s)" % (self.servicenow_disp_name, str(self.servicenow_driver_id))

