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
[概要]
  system_conf tests


"""


import pytest
import unittest

from django.urls import reverse
from django.test import override_settings

from web_app.models.models import System
from web_app.templatetags.common import get_message


@pytest.mark.django_db
class TestSystemConf_beforeRendaring(object):
    """
    web_app/views/system/system_conf.pyのテストクラス その１
    （view側の処理の確認、contextの確認、private methodの確認か）
    """

    # 今はまだ無し
    pass

@pytest.mark.django_db
class TestSystemConf_rendered(object):
    """
    web_app/views/system/system_conf.pyのテストクラス その２
    （render後のtemplate実装内容含めた画面出力結果の確認）
    """

    @override_settings(DISABLE_WHITE_BLACK_LIST=False)
    def test_index_1(self, admin):
        """
        参照画面表示
        ※ 今はブラック/ホワイトリスト機能部分のみ確認
        """

        response = admin.get(reverse('web_app:system:system_conf'))
        content = response.content.decode('utf-8')

        assert response.status_code == 200


    @override_settings(DISABLE_WHITE_BLACK_LIST=True)
    def test_index_2(self, admin):
        """
        参照画面表示（ブラック/ホワイトリスト機能OFF確認）
        """

        response    = admin.get(reverse('web_app:system:system_conf'))
        content     = response.content.decode('utf-8')
        config_name = System.objects.get(item_id=37).config_name

        assert response.status_code == 200
        assert config_name in content
        assert get_message('MOSJA22072', 'JA', showMsgId=False) in content


    @override_settings(DISABLE_WHITE_BLACK_LIST=False)
    def test_edit_1(self, admin):
        """
        編集画面表示
        ※ 今はブラック/ホワイトリスト機能部分のみ確認
        """

        response = admin.get(reverse('web_app:system:system_conf_edit'))
        content = response.content.decode('utf-8')

        assert response.status_code == 200


    @override_settings(DISABLE_WHITE_BLACK_LIST=True)
    def test_edit_2(self, admin):
        """
        編集画面表示（ブラック/ホワイトリスト機能OFF確認）
        """

        response = admin.get(reverse('web_app:system:system_conf_edit'))
        content = response.content.decode('utf-8')
        config_name = System.objects.get(item_id=37).config_name

        assert response.status_code == 200
        assert config_name in content
        assert get_message('MOSJA22072', 'JA', showMsgId=False) in content

