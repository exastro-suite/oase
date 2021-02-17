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
  
sso_info tests

"""



import pytest
import unittest
from django.urls import reverse
from web_app.models.models import System
from web_app.templatetags.common import get_message
from web_app.models.models import Menu
from libs.commonlibs import define as defs
@pytest.mark.django_db
class TestSsoInfoIndex(object):
    """
    web_app/views/system/sso_info.pyのテストクラス一覧表示
    """
    def test_index_ok(self, admin):
        """
        正常系
        """
        response = admin.get(reverse('web_app:system:sso_info'))
        content = response.content.decode('utf-8')
        assert response.status_code == 200
    def test_index_ng(self,admin):
        """
        異常系
        """
        with pytest.raises(Exception):
            response = admin.get(reverse('web_app:system:sso_info'))
            assert response.status_code == 404

