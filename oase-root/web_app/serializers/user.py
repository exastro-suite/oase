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

from rest_framework import serializers

from web_app.models.models import User
from libs.commonlibs import define as defs


class UserSerializer(serializers.ModelSerializer):

    PASSWD_PATTERN  = r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!#$%&()*+,-./;<=>?@\[\]^_{}|~]).{8,}$'
    EMAIL_PATTERN   = r'^([\w!#$%&\'*+\-\/=?^`{|}~]+(\.[\w!#$%&\'*+\-\/=?^`{|}~]+)*|"([\w!#$%&\'*+\-\/=?^`{|}~. ()<>\[\]:;@,]|\\[\\"])+")@(([a-zA-Z\d\-]+\.)+[a-zA-Z]+|\[(\d{1,3}(\.\d{1,3}){3}|IPv6:[\da-fA-F]{0,4}(:[\da-fA-F]{0,4}){1,5}(:\d{1,3}(\.\d{1,3}){3}|(:[\da-fA-F]{0,4}){0,2}))\])$'
    DISUSEFLAG_LIST = ['0', '1', ]

    class Meta:
        model = User
        fields = (
            'login_id', 'password', 'mail_address',
            'lang_mode_id', 'disp_mode_id', 'disuse_flag',
        )


    def validate_password(self, password):

        if len(password) <= 0:
            raise serializers.ValidationError("パスワード未入力")

        re_obj = re.match(self.PASSWD_PATTERN, password)
        if re_obj is None:
            raise serializers.ValidationError("パスワード不正 pass=%s" % (password))

        return password


    def validate_mail_address(self, mail_address):

        if len(mail_address) <= 0:
            raise serializers.ValidationError("メールアドレス未入力")

        re_obj = re.match(self.EMAIL_PATTERN, mail_address)
        if re_obj is None:
            raise serializers.ValidationError("メールアドレス不正 email=%s" % (mail_address))

        return mail_address


    def validate_lang_mode_id(self, lang_mode_id):

        for lang_mode in defs.LANG_MODE.LIST_ALL:
            if lang_mode_id == lang_mode['v']:
                break
        else:
            raise serializers.ValidationError("不明な言語モード lang_mode=%s" % (lang_mode_id))

        return lang_mode_id


    def validate_disp_mode_id(self, disp_mode_id):

        for disp_mode in defs.DISP_MODE.LIST_ALL:
            if disp_mode_id == disp_mode['v']:
                break
        else:
            raise serializers.ValidationError("不明な表示モード disp_mode=%s" % (disp_mode_id))

        return disp_mode_id


    def validate_disuse_flag(self, disuse_flag):

        if disuse_flag not in self.DISUSEFLAG_LIST:
            raise serializers.ValidationError("無効なフラグ値 flag=%s" % (disuse_flag))

        return disuse_flag


