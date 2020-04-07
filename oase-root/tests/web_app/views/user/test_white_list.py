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

import pytest

from django.urls import reverse
from django.test import override_settings

from web_app.models.models import User
from web_app.templatetags.common import get_message


@pytest.mark.django_db
class TestWhiteList:


    @override_settings(DISABLE_WHITE_BLACK_LIST=False) 
    def test_index(self, admin):
        """
        登録0件時の表示テスト
        """
        response = admin.get(reverse('web_app:user:white_list'))
        content = response.content.decode('utf-8')

        assert response.status_code == 200
        assert get_message('MOSJA35000', 'JA', showMsgId=False) in content


    @override_settings(DISABLE_WHITE_BLACK_LIST=True) 
    def test_index2(self, admin):
        """
        ホワイトリスト機能OFF時の表示テスト
        """
        response = admin.get(reverse('web_app:user:white_list'))
        content = response.content.decode('utf-8')

        assert response.status_code == 200
        assert get_message('MOSJA35010', 'JA', showMsgId=False) in content


