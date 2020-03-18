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
from django import forms
from .common_form import DivErrorList
from web_app.models.models import RuleType 
from web_app.serializers.unicode_check import UnicodeCheck

class RuleTypeForm(forms.Form):

    rule_type_name_errors = {
        'required': 'MOSJA00003',
        'max_length': 'MOSJA11003',
    }
    summary_errors = {
        'max_length': 'MOSJA11004',
    }
    rule_table_name_errors = {
        'required': 'MOSJA00003',
        'max_length': 'MOSJA11005',
    }

    rule_type_name = forms.CharField(label="ルール種別名称", max_length=64, error_messages=rule_type_name_errors) #unique
    summary = forms.CharField(label="概要", max_length=4000, required=False, error_messages=summary_errors)
    rule_table_name = forms.CharField(label="RuleTable名", max_length=64, error_messages=rule_table_name_errors) #unique

    required_css_class = 'tooltip-input validation-input'
    error_css_class = 'tooltip-input validation-input'


    def __init__(self, pk, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pk = pk
        self.emo_chk = UnicodeCheck()


    def clean_rule_type_name(self):
        d = self.cleaned_data['rule_type_name']
        
        # 絵文字チェック
        if len(self.emo_chk.is_emotion(d)):
            self.add_error('rule_type_name', 'MOSJA11040')

        # 重複チェック
        duplication = RuleType.objects.filter(rule_type_name=d)
        if len(duplication) and duplication[0].disuse_flag == '0':
            # 使用中のルール種別と重複
            self.add_error('rule_type_name', 'MOSJA11043')
        elif len(duplication) and duplication[0].disuse_flag == '1':
            # 削除済みのものと重複
            self.add_error('rule_type_name', 'MOSJA11044')

        return d


    def clean_summary(self):
        d = self.cleaned_data['summary']

        # 絵文字チェック
        if len(self.emo_chk.is_emotion(d)):
            self.add_error('summary', 'MOSJA11041')

        return d


    def clean_rule_table_name(self):
        d = self.cleaned_data['rule_table_name']

        # 絵文字チェック
        if len(self.emo_chk.is_emotion(d)):
            self.add_error('rule_table_name', 'MOSJA11042')

        # 半角英数字チェック
        re_obj = re.match('^[a-zA-Z0-9]+$', d)
        if re_obj == None:
            self.add_error('rule_table_name', 'MOSJA00240')

        # 重複チェック
        duplication = RuleType.objects.filter(rule_table_name=d)
        if len(duplication) and duplication[0].disuse_flag == '0':
            # 使用中のルール種別と重複
            self.add_error('rule_table_name', 'MOSJA11045')
        elif len(duplication) and duplication[0].disuse_flag == '1':
            # 削除済みのものと重複
            self.add_error('rule_table_name', 'MOSJA11046')

        return d


