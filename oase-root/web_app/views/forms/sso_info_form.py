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
from web_app.models.models import SsoInfo
from web_app.serializers.unicode_check import UnicodeCheck
from libs.webcommonlibs.common import is_addresses

class SsoInfoForm(forms.Form):

    provider_name_errors = {
        'required': 'MOSJA00003',
        'max_length': 'MOSJA28036',
    }
    auth_type_errors = {
        'required': 'MOSJA00003',
    }
    logo_errors = {
        'max_length': 'MOSJA28037',
    }
    visible_flag_errors = {
        'required': 'MOSJA00003',
    }

    clientid_errors = {
        'required': 'MOSJA00003',
        'max_length': 'MOSJA28038',
    }
    clientsecret_errors = {
        'required': 'MOSJA00003',
        'max_length': 'MOSJA28039',
    }
    authorizationuri_errors = {
        'required': 'MOSJA00003',
        'max_length': 'MOSJA28040',
    }
    accesstokenuri_errors = {
        'required': 'MOSJA00003',
        'max_length': 'MOSJA28041',
    }
    resourceowneruri_errors = {
        'required': 'MOSJA00003',
        'max_length': 'MOSJA28042',
    }
    scope_errors = {
        'max_length': 'MOSJA28043',
    }
    id_errors = {
        'required': 'MOSJA00003',
        'max_length': 'MOSJA28044',
    }
    name_errors = {
        'required': 'MOSJA00003',
        'max_length': 'MOSJA28045',
    }
    email_errors = {
        'max_length': 'MOSJA28046',
    }
    imageurl_errors = {
        'max_length': 'MOSJA28047',
    }
    proxy_errors = {
        'max_length': 'MOSJA28048',
    }

    provider_name = forms.CharField(label="プロバイダー名", max_length=128, error_messages=provider_name_errors)
    logo = forms.CharField(label="ロゴ", max_length=64, required=False, error_messages=logo_errors)
    clientid = forms.CharField(label="clientid", max_length=256, error_messages=clientid_errors)
    clientsecret = forms.CharField(label="clientsecret", max_length=256, error_messages=clientsecret_errors)
    authorizationuri = forms.CharField(label="authorizationuri", max_length=256, error_messages=authorizationuri_errors)
    accesstokenuri = forms.CharField(label="accesstokenuri", max_length=256, error_messages=accesstokenuri_errors)
    resourceowneruri = forms.CharField(label="resourceowneruri", max_length=256, error_messages=resourceowneruri_errors)
    scope = forms.CharField(label="scope", max_length=256, required=False, error_messages=scope_errors)
    id = forms.CharField(label="id", max_length=256, error_messages=id_errors)
    name = forms.CharField(label="name", max_length=256, error_messages=name_errors)
    email = forms.CharField(label="email", max_length=256, required=False, error_messages=email_errors)
    imageurl = forms.CharField(label="imageurl", max_length=256, required=False, error_messages=imageurl_errors)
    proxy = forms.CharField(label="proxy", max_length=256, required=False, error_messages=proxy_errors)

    required_css_class = 'tooltip-input validation-input'
    error_css_class = 'tooltip-input validation-input'

    def __init__(self, pk, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pk = pk
        self.emo_chk = UnicodeCheck()


    def clean_provider_name(self):
        """
        プロバイダー名チェック
        """
        provider_name = self.cleaned_data['provider_name']

        # 絵文字チェック
        if len(self.emo_chk.is_emotion(provider_name)):
            self.add_error('provider_name', 'MOSJA28049')

        return provider_name


    def clean_auth_type(self):
        """
        認証方式チェック
        """

        auth_type = self.cleaned_data['auth_type']

        if auth_type not in ['0']:
            self.add_error('auth_type', 'MOSJA28051')

        return auth_type


    def clean_logo(self):
        """
        logoチェック
        """
        logo = self.cleaned_data['logo']

        # 絵文字チェック
        if len(self.emo_chk.is_emotion(logo)):
            self.add_error('logo', 'MOSJA28052')

        return logo


    def clean_visible_flag(self):
        """
        表示フラグチェック
        """

        visible_flag = self.cleaned_data['visible_flag']

        if visible_flag not in ['0', '1']:
            self.add_error('visible_flag', 'MOSJA28054')

        return visible_flag


    def clean_clientid(self):
        """
        clientidチェック
        """
        clientid = self.cleaned_data['clientid']

        # 絵文字チェック
        if len(self.emo_chk.is_emotion(clientid)):
            self.add_error('clientid', 'MOSJA28055')

        return clientid


    def clean_clientsecret(self):
        """
        clientsecretチェック
        """
        clientsecret = self.cleaned_data['clientsecret']

        # 絵文字チェック
        if len(self.emo_chk.is_emotion(clientsecret)):
            self.add_error('clientsecret', 'MOSJA28056')

        return clientsecret


    def clean_authorizationuri(self):
        """
        authorizationuriチェック
        """
        authorizationuri = self.cleaned_data['authorizationuri']

        # 絵文字チェック
        if len(self.emo_chk.is_emotion(authorizationuri)):
            self.add_error('authorizationuri', 'MOSJA28057')

        return authorizationuri


    def clean_accesstokenuri(self):
        """
        accesstokenuriチェック
        """
        accesstokenuri = self.cleaned_data['accesstokenuri']

        # 絵文字チェック
        if len(self.emo_chk.is_emotion(accesstokenuri)):
            self.add_error('accesstokenuri', 'MOSJA28058')

        return accesstokenuri


    def clean_resourceowneruri(self):
        """
        resourceowneruriチェック
        """
        resourceowneruri = self.cleaned_data['resourceowneruri']

        # 絵文字チェック
        if len(self.emo_chk.is_emotion(resourceowneruri)):
            self.add_error('resourceowneruri', 'MOSJA28059')

        return resourceowneruri


    def clean_scope(self):
        """
        scopeチェック
        """
        scope = self.cleaned_data['scope']

        # 絵文字チェック
        if len(self.emo_chk.is_emotion(scope)):
            self.add_error('scope', 'MOSJA28060')

        return scope


    def clean_id(self):
        """
        idチェック
        """
        id = self.cleaned_data['id']

        # 絵文字チェック
        if len(self.emo_chk.is_emotion(id)):
            self.add_error('id', 'MOSJA28061')

        return id


    def clean_name(self):
        """
        nameチェック
        """
        name = self.cleaned_data['name']

        # 絵文字チェック
        if len(self.emo_chk.is_emotion(name)):
            self.add_error('name', 'MOSJA28062')

        return name


    def clean_email(self):
        """
        emailチェック
        """
        email = self.cleaned_data['email']

        # 絵文字チェック
        if len(self.emo_chk.is_emotion(email)):
            self.add_error('email', 'MOSJA28063')

        return email


    def clean_imageurl(self):
        """
        imageurlチェック
        """
        imageurl = self.cleaned_data['imageurl']

        # 絵文字チェック
        if len(self.emo_chk.is_emotion(imageurl)):
            self.add_error('imageurl', 'MOSJA28064')

        return imageurl


    def clean_proxy(self):
        """
        proxyチェック
        """
        proxy = self.cleaned_data['proxy']

        # 絵文字チェック
        if len(self.emo_chk.is_emotion(proxy)):
            self.add_error('proxy', 'MOSJA28065')

        return proxy

