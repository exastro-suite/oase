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
import datetime

from web_app.models.models import RuleType
from web_app.serializers.rule_type import RuleTypeSerializer
from rest_framework import serializers

def test_validate_mail_address_ok_single():
    """
    validate_mail_address 正常終了 1件
    """
    serializer = RuleTypeSerializer()
    mail_address = "test@test.com"

    result = serializer.validate_mail_address(mail_address)

    assert mail_address == result


def test_validate_mail_address_ok_multiple():
    """
    validate_mail_address 正常終了　複数件
    """
    serializer = RuleTypeSerializer()
    mail_address = "test1@test.com;test2@test.com"

    result = serializer.validate_mail_address(mail_address)

    assert mail_address == result


def test_validate_mail_address_ng_length():
    """
    validate_mail_address 異常終了 文字数オーバー
    """
    serializer = RuleTypeSerializer()
    mail_address = "abcdefghijalmnopqrstuvwxyzabcdefghijalmnopqrstuvwxyzabcdefghijalmnopqrstuvwxyzabcdefghijalmnopqrstuvwxyzabcdefghijalmnopqrstuvwxyzabcdefghijalmnopqrstuvwxyzabcdefghijalmnopqrstuvwxyzabcdefghijalmnopqrstuvwxyzabcdefghijalmnopqrstuvwxyzabcdefghijalmnopqrstuvwxyzabcdefghijalmnopqrstuvwxyzabcdefghijalmnopqrstuvwxyzabcdefghijalmnopqrstuvwxyzabcdefghijalmnopqrstuvwxyzabcdefghijalmnopqrstuvwxyzabcdefghijalmnopqrstuvwxyzabcdefghijalmnopqrstuvwxyzabcdefghijalmnopqrstuvwxyzabcdefghijalmnopqrstuvwxyzabcdefghij@test.com"

    try:
        with pytest.raises(serializers.ValidationError):
            result = serializer.validate_mail_address(mail_address)
            assert False
    except:
        assert False


def test_validate_mail_address_ng_format():
    """
    validate_mail_address 異常終了　形式エラー
    """
    serializer = RuleTypeSerializer()
    mail_address = "test1@testcom"

    try:
        with pytest.raises(serializers.ValidationError):
            result = serializer.validate_mail_address(mail_address)
            assert False
    except:
        assert False