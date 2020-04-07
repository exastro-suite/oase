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
from web_app.models.models import DataObject
from libs.commonlibs import define as defs

from web_app.serializers.unicode_check import UnicodeCheck

class DataObjectSerializer(serializers.ModelSerializer):


    CONDITIONAL_NAME_LENGTH  = 32
    EMO_CHK                  = UnicodeCheck()
    symbol_repatter          = '[\u0021-\u002F\u003A-\u0040\u005B-\u0060\u007B-\u007E\uFF01-\uFF0F\uFF1A-\uFF20\uFF3B-\uFF40\uFF5B-\uFF5E]'

    class Meta:
        model  = DataObject
        fields = (
            'conditional_name',
            'conditional_expression_id',
            'last_update_user',
            'last_update_timestamp',
        )


    def validate_conditional_name(self, conditional_name):

        conditional_name_len = len(conditional_name)
        #未入力チェック
        if conditional_name_len <= 0:
            raise serializers.ValidationError("条件名 未入力")


        #文字数チェック
        if conditional_name_len > self.CONDITIONAL_NAME_LENGTH:
            raise serializers.ValidationError("条件名 入力文字数不正 conditional_name=%s, req_len=%s, valid_len=%s" %(conditional_name, conditional_name_len, self.CONDITIONAL_NAME_LENGTH))


        # 絵文字チェック
        value_list = self.EMO_CHK.is_emotion(conditional_name)
        if len(value_list) > 0:
            raise serializers.ValidationError("条件名 入力文字不正")

        # 記号チェック
        re_obj = re.search(self.symbol_repatter, conditional_name)
        if re_obj:
            raise serializers.ValidationError("条件名 入力文字不正")

        return conditional_name

