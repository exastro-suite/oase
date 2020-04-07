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

common.pyのテスト

"""
from libs.webcommonlibs.common import is_addresses, set_wild_iterate


def test_is_addresses_ok():
    """
    複数メールアドレスのテスト
    """
    assert is_addresses('')
    assert is_addresses("aZ0123456789!#$%&'*+-/=?^_`.{|}~@example.com")
    assert is_addresses('"a() <>[]:;@"@example.com')
    # assert is_addresses('"a() <>[]:;,@def"@example.com')  # todo 失敗する
    assert is_addresses('sample@example.org,sample@example.ne.jp,sample@example.com')


def test_is_addresses_ng():
    """
    不正なメールアドレスのテスト
    """
    assert not is_addresses('"test@example.com')
    assert not is_addresses('a.@example.com')
    assert not is_addresses('a..1@example.com')


def test_set_wild_iterate_ok():
    """
    ipアドレスの[*]出現時の変換テスト
    """
    assert set_wild_iterate('*.10.1.1') == '*.*.*.*'
    assert set_wild_iterate('192.*.1.1') == '192.*.*.*'
    assert set_wild_iterate('192.10.*.1') == '192.10.*.*'
    assert set_wild_iterate('192.10.1.*') == '192.10.1.*'
    assert set_wild_iterate('192.10.1.1') == '192.10.1.1'
