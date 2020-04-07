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
import json

from rest_framework import serializers

from web_app.models.models import RuleType

from libs.commonlibs import define as defs

from web_app.serializers.unicode_check import UnicodeCheck

class RuleTypeSerializer(serializers.ModelSerializer):

    GENERATION_MIN          = 1
    GENERATION_MAX          = 10
    RULE_TYPE_NAME_LENGTH   = 64
    SUMMARY_LENGTH          = 4000
    RULE_TABLE_NAEM_LENGTH  = 64
    RULE_TABLE_NAME_PATTERN = '^[a-zA-Z0-9]+$'
    EMO_CHK                 = UnicodeCheck()

    class Meta:
        model = RuleType
        fields = (
            'rule_type_id',
            'rule_type_name',
            'summary',
            'rule_table_name',
            'generation_limit',
            'group_id',
            'artifact_id',
            'container_id_prefix_staging',
            'container_id_prefix_product',
            'current_container_id_staging',
            'current_container_id_product',
            'last_update_timestamp',
            'last_update_user',
        )

    def validate_generation_limit(self, generation_limit):

        if generation_limit < self.GENERATION_MIN or generation_limit > self.GENERATION_MAX:
            raise serializers.ValidationError("不正な世代管理数 generation_limit=%s" % (generation_limit))

        return generation_limit


    def validate_rule_type_name(self, rule_type_name):

        rule_type_name_len = len(rule_type_name)

        # 未入力チェック
        if rule_type_name_len <= 0:
            raise serializers.ValidationError("ルール種別名称未入力", "rule_type_name")


        # 文字数チェック
        if rule_type_name_len > self.RULE_TYPE_NAME_LENGTH:
            raise serializers.ValidationError("ルール種別名称 入力文字数不正 rule_type_name=%s, req_len=%s, valid_len=%s" %(rule_type_name, rule_type_name_len, self.RULE_TYPE_NAME_LENGTH), "rule_type_name")

        # 絵文字チェック
        value_list = self.EMO_CHK.is_emotion(rule_type_name)
        if len(value_list) > 0:
            raise serializers.ValidationError("ルール種別名称 入力文字不正", "rule_type_name")

        return rule_type_name


    def validate_summary(self, summary):

        # 文字数チェック
        summary_len = len(summary)
        if summary_len > self.SUMMARY_LENGTH:
            raise serializers.ValidationError("概要 入力文字数不正 summary=%s, req_len=%s, valid_len=%s" %(summary, summary_len, self.SUMMARY_LENGTH), "summary")

        value_list = self.EMO_CHK.is_emotion(summary)
        if len(value_list) > 0:
            raise serializers.ValidationError("概要 入力文字不正", "summary")
        return summary

    def validate_rule_table_name(self, rule_table_name):

        rule_table_name_len = len(rule_table_name)

        # 未入力チェック
        if rule_table_name_len <= 0:
            raise serializers.ValidationError("RuleTable名未入力", "rule_table_name")


        # 文字数チェック
        if rule_table_name_len > self.RULE_TABLE_NAEM_LENGTH:
            raise serializers.ValidationError("RuleTable名 入力文字数不正 rule_table_name=%s, req_len=%s, valid_len=%s" %(rule_table_name, rule_table_name_len, self.RULE_TABLE_NAEM_LENGTH), "rule_table_name")


        # 半角英数字チェック
        re_obj = re.match(self.RULE_TABLE_NAME_PATTERN, rule_table_name)
        if re_obj is None:
            raise serializers.ValidationError("RuleTable名 入力文字不正 rule_table_name=%s" % (rule_table_name), "rule_table_name")

        # 絵文字チェック
        value_list = self.EMO_CHK.is_emotion(rule_table_name)
        if len(value_list) > 0:
            raise serializers.ValidationError("RuleTable名 入力文字不正", "rule_table_name")

        return rule_table_name
