
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
templatetags/common.pyのテスト
"""
import datetime
from web_app.templatetags.common import *


def test_search_red_ok():
    """
    フィルタ検索で、ヒットした文字を赤くする
    """
    text = 'one-two-three'
    hit_list = ['two', 'three']
    result = search_red(text, hit_list)
    expected = 'one-two-<span style="color:red;">three</span>'
    assert result == expected


def test_search_red_ng():
    """
    フィルタ検索で、ヒットした文字を赤くする
    """
    result = search_red('one-two-three', ['two', 'three'])
    assert result != 'one-two-three'
    assert result != 'one-<span style="color:red;">two</span>-three'


def test_ellipsis_ok():
    """
    ellipsis()のテスト
    """
    assert ellipsis('1234567890', 5) == '12...'
    assert ellipsis('1234', 5) == '1234'
    assert ellipsis('あいうえ', 5) == 'あいうえ'
    assert ellipsis('あいうえお', 5) == 'あい...'


def test_get_message_ok():
    """
    get_message()のテスト
    """
    assert get_message('MOSJA00018', 'JA') == 'キャンセル (MOSJA00018)'
    assert get_message('MOSJA00018', 'JA', showMsgId=False) == 'キャンセル'
    assert get_message('MOSJA00018', 'EN', showMsgId=False) == 'Cancel'
    assert get_message('MOSJA-----', showMsgId=False) == '[ MOSJA----- ] not found.'


def test_get_message_with_kwargs_ok():
    """
    get_message()のキーワードを含む場合のテスト
    """
    expected = "10秒経過以後に、1回目のリトライを実施します。 (MOSJA01057)"
    assert get_message('MOSJA01057', 'JA', interval=10, ret_count=1) == expected


def test_newline_to_br_ok():
    """
    newline_to_br()のテスト
    """
    value = 'aaa\nbbb\n'
    assert value.replace('\n', '</br>') == 'aaa</br>bbb</br>'


def test_change_lang_ok():
    """
    change_lang()のテスト
    """
    assert change_lang('MOSJA00018', 'EN', 4) == 'MOSEN00018'
    assert change_lang('MOSJA00018', 'EN', -1) == 'MOSJA00018'
    assert change_lang('MOSJA00018', 'EN', 10) == 'MOSJA00018'


def test_change_datestyle_ok():
    """
    change_datestyle()のテスト
    """
    changetime = datetime.datetime(2020, 1, 1)
    assert change_datestyle(changetime, 'EN') == '2020, 01, 01, 00:00'
    assert change_datestyle(changetime, 'JA') == '2020年 01月 01日 00:00'
    assert change_datestyle(changetime, 'FR') == changetime

