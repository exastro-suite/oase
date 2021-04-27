
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
get_default_langのテスト
"""

import pytest
from libs.commonlibs import define as defs
from django.conf import settings
from django.test import override_settings

@override_settings(LANGUAGE_CODE='ja') 
def test_get_default_lang_ja():
    # settings.LANGUAGE_CODEがjaの場合
    lang_mode = defs.LANG_MODE.get_default_lang()
    assert lang_mode == 1

@override_settings(LANGUAGE_CODE='en-us') 
def test_get_default_lang_en():
    # settings.LANGUAGE_CODEがen-usの場合
    lang_mode = defs.LANG_MODE.get_default_lang()
    assert lang_mode == 2
