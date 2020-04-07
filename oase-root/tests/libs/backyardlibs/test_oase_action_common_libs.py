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
from libs.backyardlibs.oase_action_common_libs import ActionDriverCommonModules


def test_KeyValueStringFind_ok():
    """
    KeyValueStringFind()の正常系テスト
    """
    common_module = ActionDriverCommonModules()
    key_val_str1 = 'ITA_NAME=121'
    key_val_str2 = 'ITA_NAME='
    pattern = 'ITA_NAME'
    assert common_module.KeyValueStringFind(pattern, key_val_str1) == '121'
    assert common_module.KeyValueStringFind(pattern, key_val_str2) == ''


def test_KeyValueStringFind_ng():
    """
    KeyValueStringFind()の異常系テスト
    key_val_strの形式が間違っている場合
    """
    common_module = ActionDriverCommonModules()
    key_val_str = 'ITA_NAME121'
    pattern = 'ITA_NAME'
    assert common_module.KeyValueStringFind(pattern, key_val_str) is None


def test_KeyValueStringFind_ng_key_not_found():
    """
    KeyValueStringFind()の異常系テスト
    キーが見つからない場合
    """
    common_module = ActionDriverCommonModules()
    key_val_str = 'ITA_NAME=121'
    pattern = 'AAA'
    assert common_module.KeyValueStringFind(pattern, key_val_str) is None
