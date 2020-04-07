
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

mail_component.pyのテスト

"""


import pytest
import os
import datetime
import traceback
import pytz
import unittest
from importlib import import_module
from unittest.mock import MagicMock, patch
from libs.commonlibs.common import DriverCommon


@pytest.mark.django_db
def test_get_reserved_values():
    """
    予約変数名抽出テスト
    """
    test_value1 = '{{ VAR_value1 }} ; {{ VAR_value2 }}; sample@aaa.bbb {{ VAR_value3 }}'

    get_result1 = DriverCommon.get_reserved_values(test_value1)
    assert len(get_result1) == 3

    test_value2 = '{{ VAR_value1 }} ; {{ VAR_value2 }}; sample@aaa.bbb'

    get_result2 = DriverCommon.get_reserved_values(test_value2)
    assert len(get_result2) == 2

    test_value3 = '{{ VAR_value1 }} ; sample@aaa.bbb'

    get_result3 = DriverCommon.get_reserved_values(test_value3)
    assert len(get_result3) == 1

    test_value4 = 'MAIL_NAME=OASE_MAIL,MAIL_TO=,MAIL_CC=,MAIL_BCC=,MAIL_TEMPLATE='

    get_result4 = DriverCommon.get_reserved_values(test_value4)
    assert len(get_result4) == 0


def test_has_right_reserved_value():
    """
    予約変数チェック　テスト
    """
    test_value1 = '{{ VAR_value1 }} ; {{ VAR_value2 }}; sample@aaa.bbb {{ VAR_value3 }}'
    test_condition1 = {'value1', 'value2', 'value3'}

    chk_result1 = DriverCommon.has_right_reserved_value(
        test_condition1, test_value1)
    assert chk_result1 == True

    test_value2 = '{{ VAR_value1 }} ; {{ VAR_value2 }}; sample@aaa.bbb {{ VAR_value3 }}'
    test_condition2 = {'value4'}

    chk_result2 = DriverCommon.has_right_reserved_value(
        test_condition2, test_value2)
    assert chk_result2 == False
