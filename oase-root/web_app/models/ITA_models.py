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
from django.utils import timezone
"""
【概要】
 OASEテーブル定義
【テーブル定義】
 DOSL06002:ITAアクション履歴管理
 DOSL07001:ITAアクションマスタ
 DOSL07004:ITAパラメータ抽出条件管理
 DOSL07005:ITAパラメータ実行管理
"""


class ItaActionHistory(models.Model):
    """
    DOSL06002:ITAアクション履歴管理
    """
    ita_action_his_id = models.AutoField("ITAアクション履歴ID", primary_key=True)
    action_his_id = models.IntegerField("アクション履歴ID", unique=True)
    ita_disp_name = models.CharField("ITA表示名", max_length=64)
    symphony_instance_no = models.IntegerField("Symphonyインスタンス番号", null=True)
    symphony_class_id = models.IntegerField("SymphonyクラスID")
    operation_id = models.IntegerField("オペレーションID", null=True)
    symphony_workflow_confirm_url = models.CharField("Symphony作業確認URL", max_length=128, null=True, blank=True)
    restapi_error_info = models.CharField("RESTAPI異常時の詳細内容", max_length=1024, null=True, blank=True)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_ITA_ACTION_HISTORY'

    def __str__(self):
        return str(self.ita_action_his_id)


class ItaDriver(models.Model):
    """
    DOSL07001:ITAアクションマスタ
    """
    ita_driver_id = models.AutoField("項番", primary_key=True)
    ita_disp_name = models.CharField("ITA表示名", max_length=64, unique=True)
    hostname = models.CharField("ホスト名", max_length=128, unique=True)
    username = models.CharField("接続ユーザ", max_length=64)
    password = models.CharField("接続パスワード", max_length=192)
    protocol = models.CharField("プロトコル", max_length=8)
    port = models.IntegerField("ポート番号")
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_ITA_DRIVER'

    def __str__(self):
        return "%s(%s)" % (self.ita_disp_name, str(self.ita_driver_id))


class ItaParameterMatchInfo(models.Model):
    """
    DOSL07004:ITAパラメータ抽出条件管理
    """
    match_id = models.AutoField("パラメータ抽出条件ID", primary_key=True)
    menu_group_id = models.IntegerField("メニューグループID")
    menu_id = models.IntegerField("メニューID")
    parameter_name = models.CharField("パラメータ名", max_length=256)
    order = models.IntegerField("順序")
    conditional_name = models.CharField("抽出対象条件名", max_length=32)
    extraction_method1 = models.CharField("抽出方法1", max_length=512)
    extraction_method2 = models.CharField("抽出方法2", max_length=512)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_ITA_PARAMETER_MATCH_INFO'
        unique_together = (('menu_group_id', 'menu_id', 'order'), )

    def __str__(self):
        return str(self.match_id)


class ItaParametaCommitInfo(models.Model):
    """
    DOSL07005:ITAパラメータ実行管理
    """
    commit_id = models.AutoField("パラメータ実行ID", primary_key=True)
    response_id = models.IntegerField("レスポンスID")
    commit_order = models.IntegerField("実行順序")
    ita_order = models.IntegerField("ITA順序")
    parameter_value = models.CharField("抽出パラメータ値", max_length=4000)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_ITA_PARAMETER_COMMIT_INFO'
        unique_together = (('response_id', 'commit_order', 'ita_order'), )

    def __str__(self):
        return str(self.commit_id)
