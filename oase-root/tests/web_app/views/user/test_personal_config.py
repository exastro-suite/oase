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
import json

from django.urls import reverse

from web_app.models.models import User
from web_app.templatetags.common import get_message

@pytest.mark.django_db
class TestModifyLanguage:

    def test_ok(self, admin):
        """
        正常系
        """

        req_data = {
            'lang_info' : {
                'lang_mode_id' : 1,
            },
        }
        req_data = json.dumps(req_data)

        response = admin.post(reverse('web_app:user:modify_language'), {'lang_info':req_data})
        content = response.content.decode('utf-8')

        assert 'success' in content


    def test_ng(self, admin):
        """
        異常系
        """

        req_data = {
            'lang_info' : {
                'lang_mode_id' : 'XXX',
            },
        }
        req_data = json.dumps(req_data)

        response = admin.post(reverse('web_app:user:modify_language'), {'lang_info':req_data})
        content = response.content.decode('utf-8')

        assert 'MOSJA31048' in content


