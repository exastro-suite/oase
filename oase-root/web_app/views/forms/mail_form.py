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
メールテンプレートの入力項目チェック
"""
from django import forms
from web_app.serializers.unicode_check import UnicodeCheck
from web_app.models.models import MailTemplate
from libs.webcommonlibs.common import is_addresses


class MailTemplateForm(forms.Form):
    """
    メールテンプレートの入力確認
    データは自動的にstripされる
    """

    mail_template_name_errors = {
        'required': 'MOSJA25004',
        'max_length': 'MOSJA25007',
    }
    subject_errors = {
        'required': 'MOSJA25005',
        'max_length': 'MOSJA25008',
    }
    content_errors = {
        'required': 'MOSJA25006',
        'max_length': 'MOSJA25009',
    }
    destination_errors = {
        'max_length': 'MOSJA25010',
    }
    cc_errors = {
        'max_length': 'MOSJA25011',
    }
    bcc_errors = {
        'max_length': 'MOSJA25012',
    }
    pk = forms.IntegerField(required=False)
    mail_template_name = forms.CharField(max_length=64, error_messages=mail_template_name_errors)
    subject = forms.CharField(max_length=128, error_messages=subject_errors)
    content = forms.CharField(max_length=512, error_messages=content_errors)
    destination = forms.CharField(max_length=512, required=False, error_messages=destination_errors)
    cc = forms.CharField(max_length=512, required=False, error_messages=cc_errors)
    bcc = forms.CharField(max_length=200, required=False, error_messages=bcc_errors)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.emo_chk = UnicodeCheck()

    def clean_mail_template_name(self):
        """
        メールテンプレートチェック
        """
        mtn = self.cleaned_data['mail_template_name']

        if len(self.emo_chk.is_emotion(mtn)):
            self.add_error('mail_template_name', 'MOSJA25020')

        return mtn

    def clean_subject(self):
        """
        題名チェック
        """
        subject = self.cleaned_data['subject']

        if len(self.emo_chk.is_emotion(subject)):
            self.add_error('subject', 'MOSJA25021')

        return subject

    def clean_content(self):
        """
        本文チェック
        """
        content = self.cleaned_data['content']

        if len(self.emo_chk.is_emotion(content)):
            self.add_error('content', 'MOSJA25022')

        return content

    def clean_destination(self):
        """
        宛先チェック
        """
        destination = self.cleaned_data['destination']

        if len(self.emo_chk.is_emotion(destination)):
            self.add_error('destination', 'MOSJA25023')

        # 複数メールアドレスの形式チェック
        if not is_addresses(destination):
            self.add_error('destination', 'MOSJA25014')

        return destination

    def clean_cc(self):
        """
        CCチェック
        """
        cc = self.cleaned_data['cc']

        if len(self.emo_chk.is_emotion(cc)):
            self.add_error('cc', 'MOSJA25024')

        # 複数メールアドレスの形式チェック
        if not is_addresses(cc):
            self.add_error('cc', 'MOSJA25015')

        return cc

    def clean_bcc(self):
        """
        BCCチェック
        """
        bcc = self.cleaned_data['bcc']

        if len(self.emo_chk.is_emotion(bcc)):
            self.add_error('bcc', 'MOSJA25025')

        # 複数メールアドレスの形式チェック
        if not is_addresses(bcc):
            self.add_error('bcc', 'MOSJA25016')

        return bcc

    def clean(self):
        """
        重複チェック
        """
        mtn = self.cleaned_data.get('mail_template_name')
        pk = self.cleaned_data.get('pk')

        # 更新時の重複チェック
        if pk is None:
            duplication = MailTemplate.objects.filter(mail_template_name=mtn)
            if len(duplication):
                self.add_error('mail_template_name', 'MOSJA25013')
        # 新規追加時の重複チェック
        else:
            duplication = MailTemplate.objects.filter(mail_template_name=mtn).exclude(pk=pk)
            if len(duplication):
                self.add_error('mail_template_name', 'MOSJA25013')

        return self.cleaned_data
