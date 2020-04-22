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
import requests
from unittest.mock import MagicMock, patch
from libs.backyardlibs.action_driver.ITA.ITA_core import ITA1Core, ITA1Rest
from libs.backyardlibs.oase_action_common_libs import ConstantModules as Cstobj
from libs.backyardlibs.oase_action_common_libs import ActionDriverCommonModules

def get_configs():
    configs = {
        'Protocol': 'https',
        'Host': 'pytest-host-name',
        'PortNo': '443',
        'user': u'pytest',
        'password': u'pytest',
        'menuID': '',
    }
    return configs


def create_ita1core():
    """
    ITA1Coreのインスタンスを作成して返す
    """
    trace_id = '-' * 40
    symphony_class_no_ = '1'
    response_id = '2'
    execution_order = '3'
    return ITA1Core(trace_id, symphony_class_no_, response_id, execution_order)


def method_dummy_true(*args, **kwargs):
    """正常系用 request.postの戻り値"""
    return True

def method_dummy_count(*args, **kwargs):
    """正常系用"""
    return 1


def method_dummy_data(*args, **kwargs):
    """正常系用"""
    return [[None, '', '1', '3', '1', '1', '2', None, '1', None, '2020/02/20 09:26:35', 'T_20200220092635765311', 'システム管理者']]



def test_select_c_movement_class_mng_true(monkeypatch):
    """
    select_c_movement_class_mng()の正常系テスト
    """

    def method_dummy_data(*args, **kwargs):
        """正常系用"""
        return [[None, '', '1', '3', '1', '1', '2', None, '1', None, '2020/02/20 09:26:35', 'T_20200220092635765311', 'システム管理者']]

    result = []
    core = create_ita1core()
    core.restobj.rest_set_config(get_configs())

    # 正常系
    monkeypatch.setattr(core.restobj, 'rest_select', method_dummy_true)
    monkeypatch.setattr(core.restobj, 'rest_get_row_count', method_dummy_count)
    monkeypatch.setattr(core.restobj, 'rest_get_row_data', method_dummy_data)
    assert core.select_c_movement_class_mng(result) == 0


#def test_select_c_movement_class_mng_false(monkeypatch):
    """
    select_c_movement_class_mng()の異常系テスト
    """

    #def method_dummy_false(*args, **kwargs):
    #    """異常系用 request.postの戻り値"""
    #    return False

    #result = []
    #ary_result = {}
    #ary_result['status'] = 400

    # 異常系
    #monkeypatch.setattr(ITA1Rest, 'rest_select', lambda x, y: None, ary_result)
    #monkeypatch.setattr(ITA1Rest, 'rest_select', method_dummy_false)
    #core = create_ita1core()
    #core.restobj.rest_set_config(get_configs())
    #assert core.select_c_movement_class_mng(result) == 100


def test_select_c_pattern_per_orch_true(monkeypatch):
    """
    select_c_pattern_per_orch()の正常系テスト
    """

    def method_dummy_data(*args, **kwargs):
        """正常系用"""
        return {'1': {'ORCHESTRATOR_ID': '3', 'MovementIDName': '1:サービス起動'}}

    result = {}
    core = create_ita1core()
    core.restobj.rest_set_config(get_configs())

    # 正常系
    monkeypatch.setattr(core.restobj, 'rest_select', method_dummy_true)
    monkeypatch.setattr(core.restobj, 'rest_get_row_count', method_dummy_count)
    monkeypatch.setattr(core.restobj, 'rest_get_row_data', method_dummy_data)
    assert core.select_c_pattern_per_orch(result) == 0

def test_select_ita_master(monkeypatch):
    """
    select_ita_master()のテスト
    select_ita_master()によって
    """

    core = create_ita1core()
    configs = get_configs()
    servers = ["host1", "host2"]
    movementid_data = {}
    servername_serverid = {}

    monkeypatch.setattr(core, 'select_c_movement_class_mng', lambda a: (0))
    monkeypatch.setattr(core, 'select_c_pattern_per_orch', lambda a: (0))
    monkeypatch.setattr(core, 'select_c_stm_list', lambda a, b, c: (0))

    ret = core.select_ita_master(configs, servers, movementid_data, servername_serverid)

    # 正常系 todo Mockに置き換える
    assert ret == 0

    # todo 異常系

#def test_insert_ita_master(monkeypatch):
#    """
#    insert_ita_master()のテスト
#    """
#    core = create_ita1core()
#    configs = get_configs()
#    servers = ["host1", "host2"]
#    movementid_data = {}
#    servername_serverid = {}
#    ret = core.select_ita_master(configs, servers, movementid_data, servername_serverid)

#    operation_ids = []
#    ret = core.insert_ita_master(configs, movementid_data, servername_serverid, operation_ids)

#    assert ret == 100

def test_insert_c_operation_list(monkeypatch):
    """
    insert_c_operation_list()のテスト
    """
    core = create_ita1core()
    core.restobj.rest_set_config(get_configs())
    comobj = ActionDriverCommonModules()
    rand = 'aaaaa'

    operation_data = [0] * Cstobj.TBL_COL_MAX
    operation_data[Cstobj.COL_FUNCTION_NAME] = '登録'
    operation_data[Cstobj.COL_OPERATION_NAME] = rand + core.trace_id + core.execution_order
    operation_data[Cstobj.COL_OPERATION_DATE] = comobj.getStringNowDate()

    monkeypatch.setattr(core.restobj, 'rest_insert', method_dummy_true)
    is_registered = core._insert_c_operation_list(operation_data)
    assert is_registered == 0

    # todo 異常系

def test_insert_b_ansible_pho_link(monkeypatch):
    """
    insert_b_ansible_pho_link()のテスト
    """
    core = create_ita1core()
    configs = get_configs()
    comobj = ActionDriverCommonModules()
    rand = 'aaaaa'
    target_table = 'C_OPERATION_LIST'
    ary_config = ''
    insert_row_data = ''

    operation_data = [0] * Cstobj.TBL_COL_MAX
    operation_data[Cstobj.COL_FUNCTION_NAME] = '登録'
    operation_data[Cstobj.COL_OPERATION_NAME] = rand + core.trace_id + core.execution_order
    operation_data[Cstobj.COL_OPERATION_DATE] = comobj.getStringNowDate()

    monkeypatch.setattr(core.restobj, 'rest_insert', method_dummy_true)
    is_registered = core._insert_b_ansible_pho_link(target_table, insert_row_data)
    assert is_registered == 0

    # todo 異常系

def test_insert_c_parameter_sheet(monkeypatch):
    """
    insert_c_parameter_sheet()のテスト
    """
    core = create_ita1core()
    core.restobj.rest_set_config(get_configs())

    menu_id = ''
    host_name = 'host1'
    operation_id = '27'
    operation_name = 'pytest'
    exec_schedule_date = '2020/03/02 17:45_27:pytest'
    parameter_list = ['param1', 'param2']

    monkeypatch.setattr(core.restobj, 'rest_insert', method_dummy_true)
    ret = core.insert_c_parameter_sheet(host_name, operation_id, operation_name,
                                        exec_schedule_date, parameter_list, menu_id)
    assert ret == 0

    # todo 異常系


def test_select_substitution_value_mng(monkeypatch):
    """
    select_substitution_value_mng()のテスト
    """
    core = create_ita1core()
    config = get_configs()
    operation_name = 'oase'
    menu_id = ''
    target_table = 'TEST'

    # 正常系
    monkeypatch.setattr(core.restobj, 'rest_select', lambda a, b: (True))
    monkeypatch.setattr(core.restobj, 'rest_get_row_count', lambda a: (1))
    result = core.select_substitution_value_mng(config, operation_name, menu_id, target_table)
    assert result >= 1

    # 異常系
    monkeypatch.setattr(core.restobj, 'rest_select', lambda a, b: (False))
    #result = core.select_substitution_value_mng(config, operation_name, menu_id, target_table)
    #assert result == None


def test_insert_operation(monkeypatch):
    """
    insert_operation()のテスト
    """
    core = create_ita1core()
    configs = get_configs()

    # 正常系
    monkeypatch.setattr(core, '_insert_c_operation_list', method_dummy_true)
    ret, operation_name = core.insert_operation(configs)
    assert ret == True

    # 異常系 (RET_REST_ERROR)
    monkeypatch.setattr(core, '_insert_c_operation_list', lambda x: Cstobj.RET_REST_ERROR)
    ret, operation_name = core.insert_operation(configs)
    assert ret == Cstobj.RET_REST_ERROR


def test_select_operation(monkeypatch):
    """
    select_operation()のテスト
    """
    core = create_ita1core()
    configs = get_configs()

    # 正常系
    operation_name = ''
    monkeypatch.setattr(core, '_select_c_operation_list_by_operation_name', method_dummy_true)
    ret, operation_data = core.select_operation(configs, operation_name)
    assert ret == True


    # 異常系 (RET_DATA_ERROR)
    operation_name = ''
    monkeypatch.setattr(core, '_select_c_operation_list_by_operation_name', lambda a, b, c: Cstobj.RET_DATA_ERROR )
    ret, operation_data = core.select_operation(configs, operation_name)
    assert ret == Cstobj.RET_DATA_ERROR

    # 異常系 (RET_REST_ERROR)
    operation_name = ''
    monkeypatch.setattr(core, '_select_c_operation_list_by_operation_name', lambda a, b, c: Cstobj.RET_REST_ERROR )
    ret, operation_data = core.select_operation(configs, operation_name)
    assert ret == Cstobj.RET_REST_ERROR


def test_select_create_menu_info_list_OK(monkeypatch):
    """
    select_create_menu_info_list()の正常系テスト
    """

    result = []
    core = create_ita1core()
    core.restobj.rest_set_config(get_configs())

    def method_dummy_data(*args, **kwargs):
        """正常系用"""
        return {'1': {'ORCHESTRATOR_ID': '3', 'MovementIDName': '1:サービス起動'}}

    # 正常系
    monkeypatch.setattr(core.restobj, 'rest_select', method_dummy_true)
    monkeypatch.setattr(core.restobj, 'rest_get_row_data', method_dummy_data)

    flg, getdata = core.select_create_menu_info_list(result)

    assert flg == True
    assert getdata == method_dummy_data


def test_select_create_menu_info_list_NG(monkeypatch):
    """
    select_create_menu_info_list()の異常系テスト
    """

    result = []
    core = create_ita1core()
    core.restobj.rest_set_config(get_configs())

    monkeypatch.setattr(core.restobj, 'rest_select', method_dummy_false)

    flg, getdata = core.select_create_menu_info_list(result)

    assert flg == False
    assert getdata == []


def test_select_menu_list_OK(monkeypatch):
    """
    select_menu_list()の正常系テスト
    """




def test_select_menu_list_NG(monkeypatch):
    """
    select_menu_list()の異常系テスト
    """
