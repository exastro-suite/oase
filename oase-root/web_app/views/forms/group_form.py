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
from django import forms
from web_app.serializers.unicode_check import UnicodeCheck


class GroupForm(forms.Form):
    """
    グループの入力チェック
    """
    group_name_errors = {
        'required': 'MOSJA23011',
        'max_length': 'MOSJA23012',
    }
    summary_errors = {
        'max_length': 'MOSJA23013',
    }

    group_name = forms.CharField(max_length=64, error_messages=group_name_errors)
    summary = forms.CharField(max_length=4000, required=False, error_messages=summary_errors)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.emo_chk = UnicodeCheck()

    def clean_group_name(self):
        group_name = self.cleaned_data['group_name']

        if len(self.emo_chk.is_emotion(group_name)):
            self.add_error('group_name', 'MOSJA23037')

        return group_name

    def clean_summary(self):
        summary = self.cleaned_data['summary']

        if len(self.emo_chk.is_emotion(summary)):
            self.add_error('summary', 'MOSJA23038')

        return summary
