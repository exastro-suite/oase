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
#  DOSL06003:メールアクション履歴管理
#  DOSL07002:メールアクションマスタ
#
#-------------------------------------------------------------------------------


#------------------------------------------------
# DOSL06003:メールアクション履歴管理
#------------------------------------------------
class MailActionHistory(models.Model):
    mail_action_his_id      = models.AutoField("メールアクション履歴ID", primary_key=True)
    action_his_id           = models.IntegerField("アクション履歴ID", unique=True)
    mail_address            = models.CharField("送信先メールアドレス", max_length=4000)
    mail_template_name      = models.CharField("メールテンプレート名", max_length=64)
    last_update_timestamp   = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user        = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_MAIL_ACTION_HISTORY'
       
    def __str__(self):
        return str(self.mail_action_his_id)

#------------------------------------------------
# DOSL07002:メールアクションマスタ
#------------------------------------------------
class MailDriver(models.Model):
    mail_driver_id          = models.AutoField("メールアクションマスタ", primary_key=True)
    mail_disp_name          = models.CharField("メール表示名", max_length=64, unique=True)
    smtp_server             = models.CharField("接続先SMTPサーバー", max_length=64)
    protocol                = models.IntegerField("プロトコル")
    port                    = models.IntegerField("ポート番号")
    user                    = models.CharField("接続ユーザ", max_length=64, null=True, blank=True)
    password                = models.CharField("接続パスワード", max_length=192, null=True, blank=True)
    last_update_timestamp   = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user        = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_MAIL_DRIVER'
       
    def __str__(self):
        return "%s(%s)" % (self.mail_disp_name, str(self.mail_driver_id))

