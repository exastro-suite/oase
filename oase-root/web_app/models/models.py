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
【概要】
OASEテーブル定義

【テーブル定義】
DOSL01001:グループ管理
DOSL01002:ユーザー管理
DOSL01003:ユーザーグループ管理
DOSL01004:メールアドレス変更管理
DOSL02001:アクセス権限管理
DOSL03001:セッション管理
DOSL04001:リクエスト管理
DOSL05001:ルールマッチング結果管理
DOSL05002:ルールマッチング結果アクション管理
DOSL06001:アクション履歴管理
DOSL06004:アクション履歴ログ管理
DOSL06005:事前アクション履歴管理
DOSL07003:メールテンプレートマスタ
DOSL08001:ルールファイル情報管理
DOSL08002:ルール適用管理
DOSL09001:OASEサーバー管理
DOSL09002:OASEサービス管理RestAPI情報
DOSL10001:パスワード履歴
DOSL11001:ディシジョンテーブル管理
DOSL11002:データオブジェクト管理
DOSL11003:条件式マスタ
DOSL99001:システム設定
DOSL99002:メニューグループ管理
DOSL99003:メニュー管理
DOSL99004:ルール種別管理
DOSL99005:アクション種別管理
DOSL99006:権限種別管理
DOSL99007:ログイン失敗IPアドレス管理
DOSL99008:ブラックリストIPアドレス管理
DOSL99009:ホワイトリストIPアドレス管理
DOSL99010:ドライバ種別管理
DOSL99011:監視種別管理
DOSL99012:監視アダプタ種別管理
"""

from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.utils import timezone
from django.core.validators import MinLengthValidator, MinValueValidator


class Group(models.Model):
    """
    DOSL01001:グループ管理
    """
    group_id = models.AutoField("グループID", primary_key=True)
    group_name = models.CharField("グループ名", max_length=64, unique=True)
    summary = models.CharField("概要", max_length=4000, null=True, blank=True)
    ad_data_flag = models.CharField("AD連携対象フラグ", max_length=1, default='0')
    last_update_timestamp = models.DateTimeField("最終更新日時pp", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_GROUP'

    def __str__(self):
        return "%s(%s)" % (self.group_name, self.group_id)


class User(AbstractBaseUser):
    """
    DOSL01002:ユーザー管理
    """
    user_id = models.AutoField("ユーザID", primary_key=True)
    login_id = models.CharField("ログインID", max_length=32, unique=True)
    user_name = models.CharField("ユーザ名", max_length=64)
    password = models.CharField("パスワード", max_length=64)
    mail_address = models.EmailField("メールアドレス", max_length=256)
    lang_mode_id = models.IntegerField("言語種別")
    disp_mode_id = models.IntegerField("表示設定")
    password_last_modified = models.DateTimeField("パスワード最終更新日時", null=True)
    password_expire = models.DateTimeField("パスワード有効期限日時", null=True)
    password_count = models.IntegerField("パスワードカウンタ", null=True)
    account_lock_time = models.DateTimeField("アカウントロック日時", max_length=64, null=True)
    disuse_flag = models.CharField("廃止フラグ", max_length=1, default='0')
    ad_data_flag = models.CharField("AD連携対象フラグ", max_length=1, default='0')
    pass_exp_check_flag = models.BooleanField("パスワード有効期限チェックフラグ", default=True)
    pass_hist_check_flag = models.BooleanField("パスワード履歴チェックフラグ", default=True)
    account_lock_times = models.IntegerField("アカウントロック回数", default=0)
    account_lock_flag = models.BooleanField("アカウントロックフラグ", default=False)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)
    last_login = models.DateTimeField("最終ログイン日時", null=True)

    REQUIRED_FIELDS = ['user_id', ]
    USERNAME_FIELD = 'login_id'
    EMAIL_FIELD = 'mail_address'

    class Meta:
        db_table = 'OASE_T_USER'

    def get_user_name(self):
        name = self.user_name if self.disuse_flag == '0' else '不明なユーザ'
        return name

    def get_lang_mode(self):
        lang_info = {1: "JA", 2: "EN"}
        lang = lang_info[self.lang_mode_id] if self.lang_mode_id in lang_info else "JA"
        return lang

    def get_group_info(self):
        group_id_list = [
            ug['group_id'] for ug in UserGroup.objects.filter(user_id=self.user_id).values('group_id')
        ]
        group_name_list = [
            g['group_name'] for g in Group.objects.filter(group_id__in=group_id_list).values('group_name')
        ]
        return group_id_list, group_name_list

    def __str__(self):
        return "%s(%s)" % (self.user_name, str(self.user_id))


class UserGroup(models.Model):
    """
    DOSL01003:ユーザグループ管理
    """
    user_group_id = models.AutoField("ユーザグループID", primary_key=True)
    user_id = models.IntegerField("ユーザID")
    group_id = models.IntegerField("グループID")
    ad_data_flag = models.CharField("AD連携対象フラグ", max_length=1, default='0')
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_USER_GROUP'
        unique_together = (('user_id', 'group_id'), )

    def __str__(self):
        return str(self.user_group_id)


class MailAddressModify(models.Model):
    """
    DOSL01004:メールアドレス変更管理
    """
    mail_addr_id = models.AutoField("メールアドレス変更ID", primary_key=True)
    login_id = models.CharField("ログインID", max_length=32, unique=True)
    mail_address = models.EmailField("メールアドレス", max_length=256)
    mail_address_hash = models.CharField("メールアドレスハッシュ", max_length=64)
    url_expire = models.DateTimeField("メールアドレス変更URL有効期限日時", null=True)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_MAIL_ADDRESS_MODIFY'

    def __str__(self):
        return str(self.mail_addr_id)


class AccessPermission(models.Model):
    """
    DOSL02001:アクセス権限管理
    """
    permission_id = models.AutoField("権限ID", primary_key=True)
    group_id = models.IntegerField("グループID")
    menu_id = models.IntegerField("メニューID")
    rule_type_id = models.IntegerField("ルール種別ID", default=0)
    permission_type_id = models.IntegerField("権限種別ID")
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_ACCESS_PERMISSION'
        unique_together = (('group_id', 'menu_id', 'rule_type_id'), )

    def __str__(self):
        return str(self.permission_id)


class Session(models.Model):
    """
    DOSL03001:セッション管理
    """
    user_id = models.AutoField("ユーザID", primary_key=True)
    session = models.CharField("セッション情報", max_length=1, null=True, blank=True)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_SESSION'

    def __str__(self):
        return "%s(%s)" % (self.session, str(self.user_id))


class EventsRequest(models.Model):
    """
    DOSL04001:リクエスト管理
    """
    request_id = models.AutoField("リクエストID", primary_key=True)
    trace_id = models.CharField("トレースID", max_length=55, unique=True, validators=[MinLengthValidator(55)])
    request_type_id = models.IntegerField("リクエスト種別")
    rule_type_id = models.IntegerField("ルール種別ID")
    request_reception_time = models.DateTimeField("リクエスト受信日時")
    request_user = models.CharField("リクエストユーザ", max_length=128)
    request_server = models.CharField("リクエストサーバ", max_length=128)
    event_to_time = models.DateTimeField("イベント発生日時")
    event_info = models.CharField("イベント情報", max_length=4000)
    status = models.IntegerField("ステータス")
    status_update_id = models.CharField("ステータス更新ID", max_length=128, null=True, blank=True)
    retry_cnt = models.IntegerField("再試行回数", default=0)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_EVENTS_REQUEST'

    def __str__(self):
        return str(self.request_id)


class RhdmResponse(models.Model):
    """
    DOSL05001:ルールマッチング結果管理
    """
    response_id = models.AutoField("レスポンスID", primary_key=True)
    trace_id = models.CharField("トレースID", max_length=55, unique=True, validators=[MinLengthValidator(55)])
    request_reception_time = models.DateTimeField("レスポンス受信日時")
    request_type_id = models.IntegerField("リクエスト種別")
    resume_order = models.IntegerField("再開アクション実行順", validators=[MinValueValidator(1)])
    resume_timestamp = models.DateTimeField("再開日時", null=True)
    status = models.IntegerField("ステータス")
    status_update_id = models.CharField("ステータス更新ID", max_length=128, null=True, blank=True)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_RHDM_RESPONSE'

    def __str__(self):
        return "%s(%s)" % (str(self.response_id), self.trace_id)


class RhdmResponseAction(models.Model):
    """
    DOSL05002:ルールマッチング結果アクション管理
    """
    response_detail_id = models.AutoField("レスポンス詳細ID", primary_key=True)
    response_id = models.IntegerField("レスポンスID")
    rule_name = models.CharField("ルール名", max_length=64)
    execution_order = models.IntegerField("アクション実行順")
    action_type_id = models.IntegerField("アクション種別")
    action_parameter_info = models.CharField("アクションパラメータ情報", max_length=1024)
    action_pre_info = models.CharField("事前アクション情報", max_length=1024)
    action_retry_interval = models.IntegerField("アクションリトライ間隔", validators=[MinValueValidator(1)])
    action_retry_count = models.IntegerField("アクションリトライ回数", validators=[MinValueValidator(1)])
    action_stop_interval = models.IntegerField("アクション抑止間隔", null=True, blank=True)
    action_stop_count = models.IntegerField("アクション抑止回数", null=True, blank=True)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_RHDM_RESPONSE_ACTION'
        unique_together = (('response_id', 'execution_order'), )

    def __str__(self):
        return "%s(%s)" % (self.rule_name, str(self.response_detail_id))


class ActionHistory(models.Model):
    """
    DOSL06001:アクション履歴管理
    """
    action_history_id = models.AutoField("アクション履歴ID", primary_key=True)
    response_id = models.IntegerField("レスポンスID")
    trace_id = models.CharField("トレースID", max_length=55, validators=[MinLengthValidator(55)])
    rule_type_id = models.IntegerField("ルール種別ID")
    rule_type_name = models.CharField("ルール種別名", max_length=64)
    rule_name = models.CharField("ルール名", max_length=64)
    execution_order = models.IntegerField("アクション実行順")
    action_start_time = models.DateTimeField("アクション開始日時")
    action_type_id = models.IntegerField("アクション種別")
    status = models.IntegerField("ステータス")
    status_detail = models.SmallIntegerField("詳細ステータス")
    status_update_id = models.CharField("ステータス更新ID", max_length=128, null=True, blank=True)
    retry_flag = models.BooleanField("再実行フラグ", default=False)
    retry_status = models.IntegerField("再実行ステータス", null=True)
    retry_status_detail = models.SmallIntegerField("再実行詳細ステータス", null=True)
    action_retry_count = models.IntegerField("アクションリトライ回数", null=True)
    last_act_user = models.CharField("最終実行者", max_length=64)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_ACTION_HISTORY'
        unique_together = (('response_id', 'execution_order'), )

    def __str__(self):
        return str(self.action_history_id)


class ActionLog(models.Model):
    """
    DOSL06004:アクション履歴ログ管理
    """
    action_log_id = models.AutoField("アクション履歴ログID", primary_key=True)
    response_id = models.IntegerField("レスポンスID")
    execution_order = models.IntegerField("アクション実行順")
    trace_id = models.CharField("トレースID", max_length=55, validators=[MinLengthValidator(55)])
    message_id = models.CharField("メッセージID", max_length=16)
    message_params = models.CharField("メッセージパラメーター", max_length=512, null=True, blank=True)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)

    class Meta:
        db_table = 'OASE_T_ACTION_LOG'

    def __str__(self):
        return str(self.action_log_id)


class PreActionHistory(models.Model):
    """
    DOSL06005:事前アクション履歴管理
    """
    preact_history_id = models.AutoField("事前アクション履歴ID", primary_key=True)
    action_history_id = models.IntegerField("アクション履歴ID")
    trace_id = models.CharField("トレースID", max_length=55, validators=[MinLengthValidator(55)])
    status = models.IntegerField("ステータス")
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_PREACTION_HISTORY'

    def __str__(self):
        return str(self.preact_history_id)


class MailTemplate(models.Model):
    """
    DOSL07003:メールテンプレートマスタ
    """
    template_id = models.AutoField("テンプレートID", primary_key=True)
    mail_template_name = models.CharField("テンプレート名", max_length=64, unique=True)
    subject = models.CharField("タイトル", max_length=128)
    content = models.CharField("本文", max_length=512)
    destination = models.CharField("宛先", max_length=512, null=True, blank=True)
    cc = models.CharField("CC", max_length=512, null=True, blank=True)
    bcc = models.CharField("BCC", max_length=512, null=True, blank=True)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_MAIL_TEMPLATE'

    def __str__(self):
        return "%s(%s)" % (self.mail_template_name, str(self.template_id))


class RuleFile(models.Model):
    """
    DOSL08001:ルールファイル情報管理
    """
    rule_file_id = models.AutoField("ルールファイルID", primary_key=True)
    rule_type_id = models.IntegerField("ルール種別ID")
    rule_file_name = models.CharField("ルールファイル名", max_length=256)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_RULE_FILE'

    def __str__(self):
        return "%s(%s)" % (self.rule_file_name, str(self.rule_file_id))


class RuleManage(models.Model):
    """
    DOSL08002:ルール適用管理
    """
    rule_manage_id = models.AutoField("ルール管理ID", primary_key=True)
    rule_type_id = models.IntegerField("ルール種別ID")
    request_type_id = models.IntegerField("リクエスト種別")
    rule_file_id = models.IntegerField("ルールファイルID")
    system_status = models.IntegerField("システム処理状態", null=True)
    operation_status = models.IntegerField("ルール運用状態", null=True)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_RULE_MANAGE'

    def __str__(self):
        return str(self.rule_manage_id)


class Server(models.Model):
    """
    DOSL09001:OASEサーバー管理
    """
    host_id = models.AutoField("ホストID", primary_key=True)
    hostname = models.CharField("ホスト名", max_length=128, unique=True)
    ip_address = models.CharField("IPアドレス", max_length=15, unique=True)
    ca_file = models.FileField("サーバー証明書ファイル", max_length=256, null=True, blank=True)
    service_mng_flag = models.CharField("サービス管理対象フラグ", max_length=1)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_SERVER'

    def __str__(self):
        return "%s(%s)" % (self.host_name, self.ip_address)


class ServiceMngRestapiInfo(models.Model):
    """
    DOSL09002:OASEサービス管理RestAPI情報
    """
    rest_id = models.AutoField("項番", primary_key=True)
    protocol = models.CharField("プロトコル", max_length=8)
    port = models.IntegerField("ポート番号")
    access_key_id = models.CharField(max_length=64)
    secret_access_key = models.CharField(max_length=64)
    ca_file = models.FileField("サーバー証明書ファイル", max_length=256, null=True, blank=True)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_SERVICE_MNG_RESTAPI_INFO'

    def __str__(self):
        return str(self.rest_id)


class PasswordHistory(models.Model):
    """
    DOSL10001:パスワード履歴
    """
    password_id = models.AutoField("パスワードID", primary_key=True)
    user_id = models.IntegerField("ユーザID")
    password = models.CharField("パスワード", max_length=64)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_PASSWORD_HISTORY'

    def __str__(self):
        return str(self.passwrod_id)


class DataObject(models.Model):
    """
    DOSL11002:データオブジェクト管理
    """
    data_object_id = models.AutoField("データオブジェクトID", primary_key=True)
    rule_type_id = models.IntegerField("ルール種別")
    conditional_name = models.CharField("条件名", max_length=32)
    label = models.CharField("Label", max_length=32)
    conditional_expression_id = models.IntegerField("条件式ID")
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_DATA_OBJECT'

    def __str__(self):
        return "%s(%s)" % (self.conditional_name, str(self.data_object_id))


class ConditionalExpression(models.Model):
    """
    DOSL11003:条件式マスタ
    """
    conditional_expression_id = models.AutoField("条件式ID", primary_key=True)
    operator_name = models.CharField("演算子名", max_length=32)
    operator = models.CharField("演算子", max_length=64)
    description = models.CharField("説明", max_length=64, null=True, blank=True)
    example = models.CharField("入力例", max_length=64)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_CONDITIONAL_EXPRESSION'
        unique_together = ('operator_name', 'operator',)

    def __str__(self):
        return "%s(%s)" % (self.operator_name, str(self.conditional_expression_id))


class System(models.Model):
    """
    DOSL99001:システム設定
    """
    item_id = models.AutoField("項番", primary_key=True)
    config_name = models.CharField("項目名", max_length=64, null=True, blank=True)
    category = models.CharField("分類", max_length=32, null=True, blank=True)
    config_id = models.CharField("識別ID", max_length=32, unique=True)
    value = models.CharField("設定値", max_length=4000, null=True, blank=True)
    maintenance_flag = models.IntegerField("メンテナンス要否フラグ", null=True)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_SYSTEM'

    def __str__(self):
        return "%s(%s)" % (self.config_name, self.value)

    @classmethod
    def get_apply_ip_and_port(cls):
        """
        [メソッド概要]
          適用君のIPアドレス、および、ポート番号を取得する
        """
        apply_ipaddr = '127.0.0.1'
        apply_port = 50001
        try:
            apply_val = cls.objects.get(config_id='APPLY_IPADDRPORT').value
        except BaseException:
            pass
        if apply_val:
            apval = apply_val.split(':')
            if len(apval) == 2:
                apply_ipaddr = apval[0]
                apply_port = int(apval[1])

        return apply_ipaddr, apply_port


class MenuGroup(models.Model):
    """
    DOSL99002:メニューグループ管理
    """
    menu_group_id = models.AutoField("メニューグループID", primary_key=True)
    menu_group_name = models.CharField("メニューグループ名", max_length=64, unique=True)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_MENU_GROUP'

    def __str__(self):
        return "%s(%s)" % (self.menu_group_name, str(self.menu_group_id))


class Menu(models.Model):
    """
    DOSL99003:メニュー管理
    """
    menu_id = models.AutoField("メニューID", primary_key=True)
    menu_group_id = models.IntegerField("メニューグループID")
    menu_name = models.CharField("メニュー名", max_length=64, unique=True)
    login_necessity = models.IntegerField("認証要否")
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_MENU'

    def __str__(self):
        return "%s(%s)" % (self.menu_name, str(self.menu_id))


class RuleType(models.Model):
    """
    DOSL99004:ルール種別管理
    """
    rule_type_id = models.AutoField("ルール種別", primary_key=True)
    rule_type_name = models.CharField("ルール種別名称", max_length=128, unique=True)
    summary = models.CharField("概要", max_length=4000, null=True, blank=True)
    rule_table_name = models.CharField("RuleTable名", unique=True, max_length=128)
    generation_limit = models.IntegerField("ルールファイル管理世代数")
    group_id = models.CharField("グループID", max_length=64)
    artifact_id = models.CharField("アーティファクトID", max_length=64)
    container_id_prefix_staging = models.CharField("ステージング用コンテナID接頭辞", max_length=72)
    container_id_prefix_product = models.CharField("プロダクト用コンテナID接頭辞", max_length=72)
    current_container_id_staging = models.CharField("現ステージング用コンテナID", max_length=96, null=True, blank=True)
    current_container_id_product = models.CharField("現プロダクト用コンテナID", max_length=96, null=True, blank=True)
    label_count = models.IntegerField("Label件数")
    disuse_flag = models.CharField("廃止フラグ", max_length=1, default='0')
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_RULE_TYPE'

    def __str__(self):
        return "%s(%s)" % (self.rule_type_name, str(self.rule_type_id))


class ActionType(models.Model):
    """
    DOSL99005:アクション種別管理
    """
    action_type_id = models.AutoField("アクション種別", primary_key=True)
    driver_type_id = models.IntegerField("ドライバ種別")
    disuse_flag = models.CharField("廃止フラグ", max_length=1, default='0')
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_ACTION_TYPE'

    def __str__(self):
        return str(self.action_type_id)


class PermissionType(models.Model):
    """
    DOSL99006:権限種別管理
    """
    permission_type_id = models.AutoField("権限種別ID", primary_key=True)
    permission_type_name = models.CharField("権限種別名称", max_length=64, unique=True)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_PERMISSION_TYPE'

    def __str__(self):
        return "%s(%s)" % (self.permission_type_name, str(self.permission_type_id))


class LoginLogIPAddress(models.Model):
    """
    DOSL99007:ログイン失敗IPアドレス管理
    """
    login_log_id = models.AutoField("ログインログID", primary_key=True)
    ipaddr = models.CharField("IPアドレス", max_length=16)
    login_id = models.CharField("ログインID", max_length=32)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)

    class Meta:
        db_table = 'OASE_T_IPADDR_LOGIN_LOG'

    def __str__(self):
        return self.ipaddr


class BlackListIPAddress(models.Model):
    """
    DOSL99008:ブラックリストIPアドレス管理
    """
    black_list_id = models.AutoField("ブラックリストID", primary_key=True)
    ipaddr = models.CharField("IPアドレス", max_length=16)
    release_timestamp = models.DateTimeField("ブラックリスト解除日時", null=True)
    manual_reg_flag = models.BooleanField("手動登録フラグ", default=False)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_IPADDR_BLACKLIST'

    def __str__(self):
        return self.ipaddr


class WhiteListIPAddress(models.Model):
    """
    DOSL99009:ホワイトリストIPアドレス管理
    """
    white_list_id = models.AutoField("ホワイトリストID", primary_key=True)
    ipaddr = models.CharField("IPアドレス", max_length=16)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_IPADDR_WHITELIST'

    def __str__(self):
        return self.ipaddr


class DriverType(models.Model):
    """
    DOSL99010:ドライバ種別管理
    """
    driver_type_id = models.AutoField("ドライバ種別", primary_key=True)
    name = models.CharField("ドライバ名", max_length=64)
    version = models.CharField("バージョン", max_length=64)
    driver_major_version = models.IntegerField("メジャーバージョン")
    exastro_flag = models.CharField("Exastroフラグ", max_length=1, default='0')
    icon_name = models.CharField("アイコン名", max_length=64)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_DRIVER_TYPE'

    def __str__(self):
        return "%s(%s)_%s" % (self.name, str(self.driver_type_id), self.version)


class MonitoringType(models.Model):
    """
    DOSL99011:監視種別管理
    """
    monitoring_type_id = models.AutoField("監視種別ID", primary_key=True)
    adapter_type_id = models.IntegerField("アダプタ種別")
    disuse_flag = models.CharField("廃止フラグ", max_length=1, default='0')
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_MONITORING_TYPE'

    def __str__(self):
        return str(self.monitoring_type_id)


class AdapterType(models.Model):
    """
    DOSL99012:監視アダプタ種別管理
    """
    adapter_type_id = models.AutoField("ドライバ種別ID", primary_key=True)
    name = models.CharField("ドライバ名", max_length=64)
    version = models.CharField("バージョン", max_length=64)
    adapter_major_version = models.IntegerField("メジャーバージョン")
    icon_name = models.CharField("アイコン名", max_length=64)
    last_update_timestamp = models.DateTimeField("最終更新日時", default=timezone.now)
    last_update_user = models.CharField("最終更新者", max_length=64)

    class Meta:
        db_table = 'OASE_T_ADAPTER_TYPE'

    def __str__(self):
        return "%s(%s)_%s" % (self.name, str(self.adapter_type_id), self.version)
