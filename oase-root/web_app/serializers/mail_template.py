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

from rest_framework import serializers

from web_app.models.models import MailTemplate


class MailTemplateSerializer(serializers.ModelSerializer):

    class Meta:
        model = MailTemplate
        fields = (
            'mail_template_name', 'subject', 'content',
        )


    def validate_mail_template_name(self, mail_template_name):

        if len(mail_template_name) <= 0:
            raise serializers.ValidationError("テンプレート名未入力")

        return mail_template_name


    def validate_subject(self, subject):

        if len(subject) <= 0:
            raise serializers.ValidationError("件名未入力")

        return subject


    def validate_content(self, content):

        if len(content) <= 0:
            raise serializers.ValidationError("本文未入力")

        return content


