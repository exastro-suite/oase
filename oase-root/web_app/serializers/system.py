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

import re
import ast

from rest_framework import serializers

from web_app.models.models import System
from libs.commonlibs import define as defs

from web_app.serializers.unicode_check import UnicodeCheck

class SystemSerializer(serializers.ModelSerializer):

    LOG_STORAGE_PERIOD_MIN     = 1
    LOG_STORAGE_PERIOD_MAX     = 7
    SESSION_TIMEOUT_MIN        = 1
    SESSION_TIMEOUT_MAX        = 60
    PASSWORD_LIFETIME_MIN      = 0
    PASSWORD_LIFETIME_MAX      = 180
    PASS_ERROR_THRESHOLD_MIN   = 0
    PASS_ERROR_THRESHOLD_MAX   = 10
    ACCOUNT_LOCK_PERIOD_MIN    = 1
    ACCOUNT_LOCK_PERIOD_MAX    = 120
    PASSWORD_GENERATION_MIN    = 0
    PASSWORD_GENERATION_MAX    = 5
    PASSWORD_INITTIME_MIN      = 0
    PASSWORD_INITTIME_MAX      = 72
    ACCOUNT_LOCK_MAX_TIMES_MIN = 0
    ACCOUNT_LOCK_MAX_TIMES_MAX = 10
    DISUSEFLAG_LIST            = ['0', '1', ]
    TARGET_GROUP_LIST_MAX      = 30
    IPADDR_LOGIN_RETRY_MIN     = 0
    IPADDR_LOGIN_RETRY_MAX     = 1000
    EMO_CHK                    = UnicodeCheck()
    EMAIL_PATTERN   = r'^([\w!#$%&\'*+\-\/=?^`{|}~]+(\.[\w!#$%&\'*+\-\/=?^`{|}~]+)*|"([\w!#$%&\'*+\-\/=?^`{|}~. ()<>\[\]:;@,]|\\[\\"])+")@(([a-zA-Z\d\-]+\.)+[a-zA-Z]+|\[(\d{1,3}(\.\d{1,3}){3}|IPv6:[\da-fA-F]{0,4}(:[\da-fA-F]{0,4}){1,5}(:\d{1,3}(\.\d{1,3}){3}|(:[\da-fA-F]{0,4}){0,2}))\])$'
    HOUR_PATTERN = r'([0-2]?[0-9])'

    class Meta:
        model = System
        fields = (
            'item_id', 'config_name', 'category', 'config_id', 'value', 'maintenance_flag'
        )

    def validate(self, data):

        if not data['maintenance_flag']:
            return data

        if data['category'] not in defs.SYSTEM_SETTINGS.CATEGORY_LIST:
            raise serializers.ValidationError("不明なカテゴリー categ=%s" % (data['category']))

        if data['category'] == 'LOG_STORAGE_PERIOD':
            if isinstance(data['value'], int):
                data['value'] = str(data['value'])

            if not isinstance(data['value'], str):
                raise serializers.ValidationError("予期せぬ型(ログ保存日数) type=%s, val=%s" % (type(data['value']), data['value']))

            if not data['value'].isdigit():
                raise serializers.ValidationError("数値以外の値(ログ保存日数) val=%s" % (data['value']))

            val_tmp = int(data['value'])
            if val_tmp < self.LOG_STORAGE_PERIOD_MIN or val_tmp > self.LOG_STORAGE_PERIOD_MAX:
                raise serializers.ValidationError("無効なログ保存日数 val=%s" % (val_tmp))

        if data['category'] == 'SESSION_TIMEOUT':
            if isinstance(data['value'], int):
                data['value'] = str(data['value'])

            if not isinstance(data['value'], str):
                raise serializers.ValidationError("予期せぬ型(セッションタイムアウト値) type=%s, val=%s" % (type(data['value']), data['value']))

            if not data['value'].isdigit():
                raise serializers.ValidationError("数値以外の値(セッションタイムアウト値) val=%s" % (data['value']))

            val_tmp = int(data['value'])
            if val_tmp < self.SESSION_TIMEOUT_MIN or val_tmp > self.SESSION_TIMEOUT_MAX:
                raise serializers.ValidationError("無効なセッションタイムアウト値 val=%s" % (val_tmp))

        if data['category'] == 'PASSWORD':
            if data['config_id'] == 'Pass_Valid_Period':
                if isinstance(data['value'], int):
                    data['value'] = str(data['value'])

                if not isinstance(data['value'], str):
                    raise serializers.ValidationError("予期せぬ型(パスワード有効期間) type=%s, val=%s" % (type(data['value']), data['value']))

                if not data['value'].isdigit():
                    raise serializers.ValidationError("数値以外の値(パスワード有効期間) val=%s" % (data['value']))

                val_tmp = int(data['value'])
                if val_tmp < self.PASSWORD_LIFETIME_MIN or val_tmp > self.PASSWORD_LIFETIME_MAX:
                    raise serializers.ValidationError("無効なパスワード有効期間 val=%s" % (val_tmp))

                if len(data['value']) > 1 and data['value'][0] == '0':
                    raise serializers.ValidationError("無効なパスワード有効期間 val=%s" % (data['value']))

            if data['config_id'] == 'Pass_generate_manage':
                if isinstance(data['value'], int):
                    data['value'] = str(data['value'])

                if not isinstance(data['value'], str):
                    raise serializers.ValidationError("予期せぬ型(同一パスワード設定不可世代数) type=%s, val=%s" % (type(data['value']), data['value']))

                if not data['value'].isdigit():
                    raise serializers.ValidationError("数値以外の値(同一パスワード設定不可世代数) val=%s" % (data['value']))

                val_tmp = int(data['value'])
                if val_tmp < self.PASSWORD_GENERATION_MIN or val_tmp > self.PASSWORD_GENERATION_MAX:
                    raise serializers.ValidationError("無効な同一パスワード設定不可世代数 val=%s" % (val_tmp))

            if data['config_id'] == 'PASS_ERROR_THRESHOLD':
                if isinstance(data['value'], int):
                    data['value'] = str(data['value'])

                if not isinstance(data['value'], str):
                    raise serializers.ValidationError("予期せぬ型(パスワード誤り閾値) type=%s, val=%s" % (type(data['value']), data['value']))

                if not data['value'].isdigit():
                    raise serializers.ValidationError("数値以外の値(パスワード誤り閾値) val=%s" % (data['value']))

                val_tmp = int(data['value'])
                if val_tmp < self.PASS_ERROR_THRESHOLD_MIN or val_tmp > self.PASS_ERROR_THRESHOLD_MAX:
                    raise serializers.ValidationError("無効なパスワード誤り閾値 val=%s" % (val_tmp))
                
                if len(data['value']) > 1 and data['value'][0] == '0':
                    raise serializers.ValidationError("無効なパスワード誤り閾値 val=%s" % (data['value']))

            if data['config_id'] == 'ACCOUNT_LOCK_PERIOD':
            
                if isinstance(data['value'], int):
                    data['value'] = str(data['value'])

                if not isinstance(data['value'], str):
                    raise serializers.ValidationError("予期せぬ型(アカウントロック継続期間) type=%s, val=%s" % (type(data['value']), data['value']))

                if not data['value'].isdigit():
                    raise serializers.ValidationError("数値以外の値(アカウントロック継続期間) val=%s" % (data['value']))

                val_tmp = int(data['value'])
                if val_tmp < self.ACCOUNT_LOCK_PERIOD_MIN or val_tmp > self.ACCOUNT_LOCK_PERIOD_MAX:
                    raise serializers.ValidationError("無効なアカウントロック継続期間 val=%s" % (val_tmp))

                if len(data['value']) > 1 and data['value'][0] == '0':
                    raise serializers.ValidationError("無効なアカウントロック継続期間 val=%s" % (data['value']))

            if data['config_id'] == 'INITIAL_PASS_VALID_PERIOD':
                if isinstance(data['value'], int):
                    data['value'] = str(data['value'])

                if not isinstance(data['value'], str):
                    raise serializers.ValidationError("予期せぬ型(初期パスワード有効期間) type=%s, val=%s" % (type(data['value']), data['value']))

                if not data['value'].isdigit():
                    raise serializers.ValidationError("数値以外の値(初期パスワード有効期間) val=%s" % (data['value']))

                val_tmp = int(data['value'])
                if val_tmp < self.PASSWORD_INITTIME_MIN or val_tmp > self.PASSWORD_INITTIME_MAX:
                    raise serializers.ValidationError("無効な初期パスワード有効期間 val=%s" % (val_tmp))
            if data['config_id'] == 'ACCOUNT_LOCK_MAX_TIMES':
                if isinstance(data['value'], int):
                    data['value'] = str(data['value'])

                if not isinstance(data['value'], str):
                    raise serializers.ValidationError("予期せぬ型(アカウントロック上限回数) type=%s, val=%s" % (type(data['value']), data['value']))

                if not data['value'].isdigit():
                    raise serializers.ValidationError("数値以外の値(アカウントロック上限回数) val=%s" % (data['value']))

                val_tmp = int(data['value'])
                if val_tmp < self.ACCOUNT_LOCK_MAX_TIMES_MIN or val_tmp > self.ACCOUNT_LOCK_MAX_TIMES_MAX:
                    raise serializers.ValidationError("無効なアカウントロック上限回数 val=%s" % (val_tmp))
            if data['config_id'] == 'NOTIFICATION_DESTINATION_TYPE':
                if isinstance(data['value'], int):
                    data['value'] = str(data['value'])

                if not isinstance(data['value'], str):
                    raise serializers.ValidationError("予期せぬ型(メール通知種別) type=%s, val=%s" % (type(data['value']), data['value']))

                if not (data['value'] in ('0','1','2')):
                    raise serializers.ValidationError("予期せぬ型(メール通知種別) type=%s, val=%s" % (type(data['value']), data['value']))

            # ログインID形式チェック
            if data['config_id'] == 'NOTIFICATION_DESTINATION':

                if not isinstance(data['value'], str):
                    raise serializers.ValidationError("予期せぬ型(メール通知先ログインID) type=%s, val=%s" % (type(data['value']), data['value']))

                # 絵文字チェック
                value_list = self.EMO_CHK.is_emotion(data['value'])
                if len(value_list) > 0:
                    raise serializers.ValidationError("メール通知先ログインIDに使用できない文字が含まれています。")

            # 同一IP連続ログイン試行上限チェック
            if data['config_id'] == 'IPADDR_LOGIN_RETRY_MAX':
                if isinstance(data['value'], int):
                    data['value'] = str(data['value'])

                if not isinstance(data['value'], str):
                    raise serializers.ValidationError("予期せぬ型(同一IPアドレス連続ログイン試行上限) type=%s, val=%s" % (type(data['value']), data['value']))

                if not data['value'].isdigit():
                    raise serializers.ValidationError("数値以外の値(同一IPアドレス連続ログイン試行上限) val=%s" % (data['value']))

                val_tmp = int(data['value'])
                if val_tmp < self.IPADDR_LOGIN_RETRY_MIN or val_tmp > self.IPADDR_LOGIN_RETRY_MAX:
                    raise serializers.ValidationError("無効な同一IPアドレス連続ログイン試行上限 val=%s" % (val_tmp))


        if data['category'] == 'ACTIVE_DIRECTORY':
            if data['config_id'] == 'ADCOLLABORATION':
                if isinstance(data['value'], int):
                    data['value'] = str(data['value'])

                if not isinstance(data['value'], str):
                    raise serializers.ValidationError("予期せぬ型(Active Directory連携値) type=%s, val=%s" % (type(data['value']), data['value']))

                if data['value'] not in self.DISUSEFLAG_LIST:
                    raise serializers.ValidationError("無効なActive Directory連携値 val=%s" % (data['value']))

            if data['config_id'] == 'ADMINISTRATOR_USER':
                value_len = len(data['value'])
                if value_len < 1:
                    raise serializers.ValidationError("管理者ユーザは必須項目です")

                # 絵文字チェック
                value_list = self.EMO_CHK.is_emotion(data['value'])
                if len(value_list) > 0:
                    raise serializers.ValidationError("管理者ユーザに使用できない文字が含まれています。")

            if data['config_id'] == 'ADMINISTRATOR_PW':
                value_len = len(data['value'])
                if value_len < 1:
                    raise serializers.ValidationError("管理者パスワードは必須項目です")

                # 絵文字チェック
                value_list = self.EMO_CHK.is_emotion(data['value'])
                if len(value_list) > 0:
                    raise serializers.ValidationError("管理者パスワードに使用できない文字が含まれています。")

            if data['config_id'] == 'ACCESS_POINT':
                value_len = len(data['value'])
                if value_len < 1:
                    raise serializers.ValidationError("接続先は必須項目です")

                # 絵文字チェック
                value_list = self.EMO_CHK.is_emotion(data['value'])
                if len(value_list) > 0:
                    raise serializers.ValidationError("接続先に使用できない文字が含まれています。")

            if data['config_id'] == 'CONNECTION_TIMEOUT':
                if isinstance(data['value'], int):
                    data['value'] = str(data['value'])

                if not isinstance(data['value'], str):
                    raise serializers.ValidationError("予期せぬ型(接続タイムアウト値) type=%s, val=%s" % (type(data['value']), data['value']))

                if not data['value'].isdigit():
                    raise serializers.ValidationError("数値以外の値(接続タイムアウト値) val=%s" % (data['value']))

            if data['config_id'] == 'READ_TIMEOUT':
                if isinstance(data['value'], int):
                    data['value'] = str(data['value'])

                if not isinstance(data['value'], str):
                    raise serializers.ValidationError("予期せぬ型(読み取りタイムアウト値) type=%s, val=%s" % (type(data['value']), data['value']))

                if not data['value'].isdigit():
                    raise serializers.ValidationError("数値以外の値(読み取りタイムアウト値) val=%s" % (data['value']))

            if data['config_id'] == 'AUTHSERVER_SEARCH_CHAR':
                value_len = len(data['value'])
                if value_len < 1:
                    raise serializers.ValidationError("認証サーバ検索文字は必須項目です")

                # 絵文字チェック
                value_list = self.EMO_CHK.is_emotion(data['value'])
                if len(value_list) > 0:
                    raise serializers.ValidationError("認証サーバ検索文字に使用できない文字が含まれています。")

            if data['config_id'] == 'TARGET_GROUP_LIST':
                targetlist = {}
                value_len = len(data['value'])
                if value_len < 1:
                    raise serializers.ValidationError("対象グループリストは必須項目です")

                value_list = data['value']
                if isinstance(value_list, str):
                    try:
                        value_list = ast.literal_eval(value_list)
                    except Exception as e:
                        raise serializers.ValidationError("対象グループリストの値が不正です val=%s" % (data['value']))

                if not isinstance(value_list, list):
                    raise serializers.ValidationError("対象グループリストの値が不正です val=%s" % (data['value']))

                if len(value_list) <= 0:
                    raise serializers.ValidationError("対象グループリストは必須項目です")

                if len(value_list) > self.TARGET_GROUP_LIST_MAX:
                    raise serializers.ValidationError("対象グループリストは %s 件までです" % (self.TARGET_GROUP_LIST_MAX))

                for i,val in enumerate(value_list):
                    if not isinstance(val, dict):
                        raise serializers.ValidationError("対象グループリストの値が不正です val=%s" % (val))

                    for k, v in val.items():
                        if not k:
                            targetlist[ i * 2 ] = "対象グループリストの値が不正です val=%s" % (val)
                            continue
                        else:
                            # 絵文字チェック
                            value_list = self.EMO_CHK.is_emotion(k)
                            if len(value_list) > 0:
                                targetlist[ i * 2 ] = "対象グループリストの値に使用できない文字が含まれています。"
                                continue

                        if not v:
                            targetlist[ i * 2 + 1 ] = "対象グループリストの値が不正です val=%s" % (val)
                            continue
                        else:
                            # 絵文字チェック
                            value_list = self.EMO_CHK.is_emotion(v)
                            if len(value_list) > 0:
                                targetlist[ i * 2 + 1] = "対象グループリストの値に使用できない文字が含まれています。"
                                continue
                
                if len(targetlist) > 0:
                    raise serializers.ValidationError(targetlist)

            if data['config_id'] == 'AD_LINKAGE_TIMER':
                value_len = len(data['value'])
                values = data['value'].split(',')
                
                # 未入力チェック 
                if not value_len:
                    raise serializers.ValidationError("必須項目が入力されていません。入力してください。")

                # 00～23 チェック
                for x in values:
                    if re.match(self.HOUR_PATTERN, x) is None:
                        raise serializers.ValidationError("00から23の数値を入力してください。")

        return data
