
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

simple_middleware.pyのテスト

"""

import pytest
import os
import datetime
import traceback
import pytz
import unittest
from importlib import import_module
from unittest.mock import MagicMock, patch


from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.test import override_settings

from libs.commonlibs.dt_component import DecisionTableComponent
from web_app.templatetags.common import get_message


class wsheetMock:
    def cell_type(self):
        return 1


@pytest.mark.django_db
def test_is_valid_number():
    """
    """
    dtcomp = DecisionTableComponent('testrule')
    row, col = (11, 11)
    col_name = "col_name"
    lang = 'JA'
    cellname = dtcomp.convert_rowcol_to_cellno(row, col)
    expected_msg = get_message(
        'MOSJA03110', lang, colname=col_name, cellname=cellname)
    wsheet = MagicMock()

    pattern = r'^(0|[1-9]\d*)$'
    pattern2 = r'^(0|[1-9]\d*|[1-9]\d*[.]{1}0+)$'

    # check date pattern
    cell_type = dtcomp.CELL_TYPE_DATE
    cell_val = '2020/02/02'
    result = dtcomp.is_valid_number(cell_type, cell_val)
    assert result == False

    # check number pattern
    cell_type = dtcomp.CELL_TYPE_NUMBER
    print("type", cell_type)
    cell_val = '10'
    result = dtcomp.is_valid_number(cell_type, cell_val)
    assert result == True

    cell_val = '0'
    result = dtcomp.is_valid_number(cell_type, cell_val)
    assert result == True

    result = dtcomp.is_valid_number(cell_type, cell_val, accept0=False)
    assert result == False

    cell_val = '11.0'
    result = dtcomp.is_valid_number(cell_type, cell_val)
    assert result == True

    cell_val = '-1'
    result = dtcomp.is_valid_number(cell_type, cell_val)
    assert result == False

    # check text pattern
    cell_type = dtcomp.CELL_TYPE_TEXT
    cell_val = '11'
    result = dtcomp.is_valid_number(cell_type, cell_val)
    assert result == True

    cell_val = '0'
    result = dtcomp.is_valid_number(cell_type, cell_val)
    assert result == True

    result = dtcomp.is_valid_number(cell_type, cell_val, accept0=False)
    assert result == False

    cell_val = 'str'
    result = dtcomp.is_valid_number(cell_type, cell_val)
    assert result == False


@pytest.mark.django_db
def test_check_gte0():
    """
    セルの値が不正な場合は、message_listにエラーメッセージが
    追加されていることをテストする。
    セルの値が正常な場合は、message_listに追加されない

    """
    dtcomp = DecisionTableComponent('testrule')
    row, col = (11, 11)
    col_name = "col_name"
    lang = 'JA'
    cellname = dtcomp.convert_rowcol_to_cellno(row, col)
    expected_msg = get_message(
        'MOSJA03110', lang, colname=col_name, cellname=cellname)
    message_list = []
    wsheet = MagicMock()

    # 値が正常な場合
    wsheet.cell_type.return_value = dtcomp.CELL_TYPE_NUMBER
    wsheet.cell().value = '10'
    result = dtcomp.check_gte0(wsheet, row, col, col_name, message_list, lang)
    assert result == True
    assert len(message_list) == 0

    # 値が不正な場合
    wsheet.cell().value = '-1'
    result = dtcomp.check_gte0(wsheet, row, col, col_name, message_list, lang)
    assert result == False
    assert message_list[0] == expected_msg


@pytest.mark.django_db
def test_check_gt0():
    """
    セルの値が不正な場合は、message_listにエラーメッセージが
    追加されていることをテストする。
    セルの値が正常な場合は、message_listに追加されない
    """
    dtcomp = DecisionTableComponent('testrule')
    row, col = (11, 11)
    col_name = "col_name"
    lang = 'JA'
    cellname = dtcomp.convert_rowcol_to_cellno(row, col)
    expected_msg = get_message(
        'MOSJA03110', lang, colname=col_name, cellname=cellname)
    message_list = []
    wsheet = MagicMock()

    # 値が正常な場合
    wsheet.cell_type.return_value = dtcomp.CELL_TYPE_NUMBER
    wsheet.cell().value = '10'
    dtcomp.check_gt0(wsheet, row, col, col_name, message_list, lang)
    assert len(message_list) == 0

    # 値が不正な場合
    wsheet.cell().value = '0'
    dtcomp.check_gt0(wsheet, row, col, col_name, message_list, lang)
    assert message_list[0] == expected_msg


@pytest.mark.django_db
def test_check_use0():
    """
    check_use0()のテスト
    """
    dtcomp = DecisionTableComponent('testrule')
    row, col = (11, 11)
    col_name = "col_name"
    lang = 'JA'
    cellname1 = dtcomp.convert_rowcol_to_cellno(row, col)
    cellname2 = dtcomp.convert_rowcol_to_cellno(row, col+1)
    expected_msg1 = get_message(
        'MOSJA03136', lang, colname=col_name, cellname=cellname1)
    expected_msg2 = get_message(
        'MOSJA03136', lang, colname=col_name, cellname=cellname2)
    message_list = []
    wsheet = MagicMock()

    # 値が正常な場合
    dtcomp.check_use0(2, 10, row, col, col_name, message_list, lang)
    assert len(message_list) == 0

    dtcomp.check_use0(0, 0, row, col, col_name, message_list, lang)
    assert len(message_list) == 0

    # 値が不正な場合
    dtcomp.check_use0(10, 0, row, col, col_name, message_list, lang)
    assert len(message_list) == 2
    assert message_list[0] == expected_msg1
    assert message_list[1] == expected_msg2

    dtcomp.check_use0(0, 10, row, col, col_name, message_list, lang)
    assert len(message_list) == 4
    assert message_list[2] == expected_msg1
    assert message_list[3] == expected_msg2


@pytest.mark.django_db
def test_check_date_format():
    '''
    check_date_format()のテスト
    '''
    dtcomp = DecisionTableComponent('testrule')
    row, col = (13, 11)
    lang = 'JA'
    cellname = dtcomp.convert_rowcol_to_cellno(row, col)
    expected_msg = get_message('MOSJA03126', lang, cellname=cellname)

    wsheet = MagicMock()

    # 値が正常の場合
    message_list = []
    test_date_list = ['2020-01-01 00:00', '2020-12-31 23:59']
    for test_date in test_date_list:
        wsheet.cell(row, col).value = test_date
        dtcomp.check_date_format(wsheet, row, col, row + 1,
                                 message_list, 'MOSJA03126', lang)
        assert len(message_list) == 0

    # 値が異常の場合
    test_err_date_list = ['2020-13-01', '2020-12-32', '2020-0-0', '2020-01-01 24:00', '2020-01-01 :00',
                          '2020-01-01 00:', '2020-01-01 00:60', '0000-01-01', '2020-01-01', '2020-12-31',
                          '24 Feb 2020', '2020-1-1 0:0', '2020-12-1 0:59']
    message_list = []
    n = 0
    for test_err_date in test_err_date_list:
        wsheet.cell(row, col).value = test_err_date

        dtcomp.check_date_format(
            wsheet, row, col, row + 1, message_list, 'MOSJA03126', lang)
        assert len(message_list) > 0
        assert message_list[n] == expected_msg



@pytest.mark.django_db
def test_is_all_blank_condition():
    '''
    is_all_blank_condition()のテスト
    '''
    dtcomp = DecisionTableComponent('testrule')
    row= 11
    col_index = 2
    col_max = 4
    wsheet = MagicMock()

    # 値が正常の場合
    wsheet.cell_type.return_value = 0
    result = dtcomp.is_all_blank_condition(wsheet, row, col_index, col_max)
    assert result == True

    # 値が異常の場合
    wsheet.cell_type.return_value = 1
    result = dtcomp.is_all_blank_condition(wsheet, row, col_index, col_max)
    assert result == False

