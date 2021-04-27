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
    conductor_class_no = ''
    return ITA1Core(trace_id, symphony_class_no_, response_id, execution_order, conductor_class_no)

def create_ita1core_c():
    """
    ITA1Coreのインスタンスを作成して返す
    """
    trace_id = '-' * 40
    symphony_class_no_ = ''
    response_id = '2'
    execution_order = '3'
    conductor_class_no = '4'
    return ITA1Core(trace_id, symphony_class_no_, response_id, execution_order, conductor_class_no)

def method_dummy_true(*args, **kwargs):
    """正常系用 request.postの戻り値"""
    return True

def method_dummy_none(*args, **kwargs):
    """正常系用 request.postの戻り値"""
    return None

def method_dummy_count(*args, **kwargs):
    """正常系用"""
    return 1

def method_dummy_count_zero(*args, **kwargs):
    """正常系用"""
    return 0


def method_dummy_data(*args, **kwargs):
    """正常系用"""
    return [[None, '', '1', '3', '1', '1', '2', None, '1', None, '2020/02/20 09:26:35', 'T_20200220092635765311', 'システム管理者']]

def test_get_last_info_conductor(monkeypatch):
    """
    get_last_info_conductorのテスト
    """

    ary_config = get_configs()
    conductor_instance_no = '1'
    operation_id = '27'
    core = create_ita1core_c()
    core.restobj.rest_set_config(get_configs())

    monkeypatch.setattr(core.restobj, 'rest_info', method_dummy_true)
    result = core.get_last_info_conductor(ary_config, conductor_instance_no, operation_id)
    assert(result)

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

def test_select_c_movement_class_mng_conductor_true(monkeypatch):
    """
    select_c_movement_class_mng_conductor()の正常系テスト
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
    assert core.select_c_movement_class_mng_conductor(result) == 0

def test_select_c_movement_class_mng_conductor_false(monkeypatch):
    """
    select_c_movement_class_mng_conductor()の異常系テスト
    """

    def method_dummy_false(aryfilter, ary_result):
        """異常系用"""
        ary_result['status'] = '-1'
        return False

    result = []
    core = create_ita1core()
    core.restobj.rest_set_config(get_configs())

    # 異常系
    monkeypatch.setattr(core.restobj, 'rest_select', method_dummy_false)
    monkeypatch.setattr(core.restobj, 'rest_get_row_count', method_dummy_count)
    monkeypatch.setattr(core.restobj, 'rest_get_row_data', method_dummy_data)
    assert core.select_c_movement_class_mng_conductor(result) == 100

def test_select_conductor_movement_master_true(monkeypatch):
    """
    select_conductor_movement_master()の正常系テスト
    """

    def method_dummy_data(*args, **kwargs):
        """正常系用"""
        return [[None, '', '1', '3', '1', '1', '2', None, '1', None, '2020/02/20 09:26:35', 'T_20200220092635765311', 'システム管理者']]

    result = {}
    core = create_ita1core()
    core.restobj.rest_set_config(get_configs())

    # 正常系
    monkeypatch.setattr(core, 'select_c_movement_class_mng_conductor', method_dummy_true)
    assert core.select_conductor_movement_master(get_configs(), result) == True

def test_select_conductor_movement_master_false(monkeypatch):
    """
    select_conductor_movement_master()の異常系テスト
    """

    #def method_dummy_false(aryfilter, ary_result):
    #    """異常系用"""
    #    ary_result['status'] = '-1'
    #    return False

    def method_dummy_false(*args, **kwargs):
        """異常系用"""
        return False

    result = []
    core = create_ita1core()
    core.restobj.rest_set_config(get_configs())

    # 異常系
    monkeypatch.setattr(core, 'select_c_movement_class_mng_conductor', method_dummy_false)
    assert core.select_conductor_movement_master(get_configs(), result) == False

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


def test_select_ita_master_conductor_ok(monkeypatch):
    """
    select_ita_master_conductor()のテスト
    """

    core = create_ita1core_c()
    configs = get_configs()
    servers = ["host1", "host2"]
    movementid_data = {}
    servername_serverid = {}

    monkeypatch.setattr(core, 'select_c_movement_class_mng_conductor', lambda a: (0))
    monkeypatch.setattr(core, 'select_c_pattern_per_orch', lambda a, b: (0))
    monkeypatch.setattr(core, 'select_c_stm_list', lambda a, b, c: (0))

    ret = core.select_ita_master_conductor(configs, servers, movementid_data, servername_serverid)

    # 正常系
    assert ret == 0


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


def test_select_c_parameter_sheet_ok(monkeypatch):
    """
    select_c_parameter_sheet(正常系)のテスト
    """
    core = create_ita1core()
    core.restobj.rest_set_config(get_configs())

    config = {}
    host_name = 'host1'
    operation_name = 'pytest'
    menu_id = ''

    monkeypatch.setattr(core.restobj, 'rest_set_config',    method_dummy_true)
    monkeypatch.setattr(core.restobj, 'rest_select',        method_dummy_true)
    monkeypatch.setattr(core.restobj, 'rest_get_row_count', method_dummy_count)
    ret, ary_result = core.select_c_parameter_sheet(config, host_name, operation_name, menu_id)
    assert ret == 1


def test_select_c_parameter_sheet_ok_zero(monkeypatch):
    """
    select_c_parameter_sheet(正常系0件)のテスト
    """
    core = create_ita1core()
    core.restobj.rest_set_config(get_configs())

    config = {}
    host_name = 'host1'
    operation_name = 'pytest'
    menu_id = ''

    monkeypatch.setattr(core.restobj, 'rest_set_config',    method_dummy_true)
    monkeypatch.setattr(core.restobj, 'rest_select',        method_dummy_true)
    monkeypatch.setattr(core.restobj, 'rest_get_row_count', method_dummy_count_zero)
    ret, ary_result = core.select_c_parameter_sheet(config, host_name, operation_name, menu_id)
    assert ret == 0


def test_update_c_parameter_sheet_ok(monkeypatch):
    """
    update_c_parameter_sheet()の正常系テスト
    """

    def method_dummy_input_data(*args, **kwargs):

        return [[None, '', '1', 'OASEメニュー1', 'パラメータシート(ホスト/オペレーション含む)', '1', 'ホスト用', '', '', 'OASE_MenuGroup(Host)', 'OASE_MenuGroup(Ref)', '', None, None, '2020/04/10 15:02:08', 'T_20200410150208611888', 'システム管理者'], [None, '', '2', 'OASEメニュー2', 'パラメータシート(ホスト/オペレーション含む)', '2', 'ホスト 用', '', '', 'テストメニュー（Host）', 'testメニュー （Ref）', '', 'テスト', None, '2020/04/16 17:35:02', 'T_20200416173502336962', 'システム管理者']]

    def method_dummy_output_data(*args, **kwargs):

        return [[None, '', '1', 'OASEメニュー1', 'パラメータシート(ホスト/オペレーション含む)', '1', 'ホスト用', '', '', 'OASE_MenuGroup(Host)', 'OASE_MenuGroup(Ref)', '', None, None, '2020/04/10 15:02:08', 'T_20200410150208611888', 'システム管理者'], [None, '', '2', 'OASEメニュー2', 'パラメータシート(ホスト/オペレーション含む)', '2', 'ホスト 用', '', '', 'テストメニュー（Host）', 'testメニュー （Ref）', '', 'テスト', None, '2020/04/16 17:35:02', 'T_20200416173502336962', 'システム管理者']]

    core = create_ita1core()
    core.restobj.rest_set_config(get_configs())

    config = {}
    host_name = 'host1'
    operation_id = '27'
    operation_name = 'pytest'
    exec_schedule_date = '2020/03/02 17:45_27:pytest'
    parameter_list = ['param1', 'param2']
    menu_id = ''
    ary_result = []

    monkeypatch.setattr(core.restobj, 'rest_set_config',   method_dummy_true)
    monkeypatch.setattr(core.restobj, 'rest_get_row_data', method_dummy_input_data)
    monkeypatch.setattr(core.restobj, 'rest_insert',       method_dummy_output_data)
    ret = core.update_c_parameter_sheet(
        config, host_name, operation_name, 
        exec_schedule_date, parameter_list, menu_id, ary_result, 3
    )
    assert ret == 0


def test_select_substitution_value_mng(monkeypatch):
    """
    select_substitution_value_mng()のテスト
    """
    core = create_ita1core()
    config = get_configs()
    operation_name = 'oase'
    movement_names = {}
    menu_id = ''
    target_table = 'TEST'

    # monkeypatchをかけているrest_select内で「ary_result」の値を入れている
    # select_substitution_value_mngでは「ary_result」を使ってfor文を回している
    # pytestでは使用上外側から「ary_result」の設定ができず、動作確認ができないため、コメントアウト
    # 正常系
    monkeypatch.setattr(core.restobj, 'rest_select', lambda a, b: (True))
    monkeypatch.setattr(core.restobj, 'rest_get_row_count', lambda a: (1))
    #result = core.select_substitution_value_mng(config, operation_name, movement_names, menu_id, target_table)
    #assert result >= 1

    # 異常系
    monkeypatch.setattr(core.restobj, 'rest_select', lambda a, b: (False))
    #result = core.select_substitution_value_mng(config, operation_name, movement_names, menu_id, target_table)
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

    result = [[None, '', '1', 'OASEメニュー1', 'パラメータシート(ホスト/オペレーション含む)', '1', 'ホスト用', '', '', 'OASE_MenuGroup(Host)', 'OASE_MenuGroup(Ref)', '', None, None, '2020/04/10 15:02:08', 'T_20200410150208611888', 'システム管理者'], [None, '', '2', 'OASEメニュー2', 'パラメータシート(ホスト/オペレーション含む)', '2', 'ホスト 用', '', '', 'テストメニュー（Host）', 'testメニュー （Ref）', '', 'テスト', None, '2020/04/16 17:35:02', 'T_20200416173502336962', 'システム管理者']]
    core = create_ita1core()
    configs = get_configs()

    def method_dummy_data(*args, **kwargs):
        """正常系用"""
        return [[None, '', '1', 'OASEメニュー1', 'パラメータシート(ホスト/オペレーション含む)', '1', 'ホスト用', '', '', 'OASE_MenuGroup(Host)', 'OASE_MenuGroup(Ref)', '', None, None, '2020/04/10 15:02:08', 'T_20200410150208611888', 'システム管理者'], [None, '', '2', 'OASEメニュー2', 'パラメータシート(ホスト/オペレーション含む)', '2', 'ホスト 用', '', '', 'テストメニュー（Host）', 'testメニュー （Ref）', '', 'テスト', None, '2020/04/16 17:35:02', 'T_20200416173502336962', 'システム管理者']]

    # 正常系
    monkeypatch.setattr(core.restobj, 'rest_select', method_dummy_true)
    monkeypatch.setattr(core.restobj, 'rest_get_row_data', method_dummy_data)

    flg, get_data = core.select_create_menu_info_list(configs, 'パラメータシート')
    assert flg == True
    get_data == result

def test_select_create_menu_info_list_NG(monkeypatch):
    """
    select_create_menu_info_list()の異常系テスト
    """

    result = []
    core = create_ita1core()
    configs = get_configs()

    def method_dummy_false(aryfilter, ary_result):
        """異常系用"""
        ary_result['status'] = '-1'
        return False

    monkeypatch.setattr(core.restobj, 'rest_select', method_dummy_false)
    flg, getdata = core.select_create_menu_info_list(configs, 'パラメータシート')

    assert flg == False
    assert getdata == result


def test_select_menu_list_OK(monkeypatch):
    """
    select_menu_list()の正常系テスト
    """

    result = [[None, '', '1', 'OASEメニュー1', 'パラメータシート(ホスト/オペレーション含む)', '1', 'ホスト用', '', '', 'OASE_MenuGroup(Host)', 'OASE_MenuGroup(Ref)', '', None, None, '2020/04/10 15:02:08', 'T_20200410150208611888', 'システム管理者'], [None, '', '2', 'OASEメニュー2', 'パラメータシート(ホスト/オペレーション含む)', '2', 'ホスト 用', '', '', 'テストメニュー（Host）', 'testメニュー （Ref）', '', 'テスト', None, '2020/04/16 17:35:02', 'T_20200416173502336962', 'システム管理者']]
    core = create_ita1core()
    core.restobj.rest_set_config(get_configs())
    configs = get_configs()

    def method_dummy_data(*args, **kwargs):
        """正常系用"""
        return [[None, '', '1', 'OASEメニュー1', 'パラメータシート(ホスト/オペレーション含む)', '1', 'ホスト用', '', '', 'OASE_MenuGroup(Host)', 'OASE_MenuGroup(Ref)', '', None, None, '2020/04/10 15:02:08', 'T_20200410150208611888', 'システム管理者'], [None, '', '2', 'OASEメニュー2', 'パラメータシート(ホスト/オペレーション含む)', '2', 'ホスト 用', '', '', 'テストメニュー（Host）', 'testメニュー （Ref）', '', 'テスト', None, '2020/04/16 17:35:02', 'T_20200416173502336962', 'システム管理者']]

    # 正常系
    monkeypatch.setattr(core.restobj, 'rest_select', method_dummy_true)
    monkeypatch.setattr(core.restobj, 'rest_get_row_data', method_dummy_data)

    flg, getdata = core.select_menu_list(configs, None, None, [], [])

    assert flg == True
    assert getdata == result

def test_select_menu_list_NG(monkeypatch):
    """
    select_menu_list()の異常系テスト
    """

    result = []
    core = create_ita1core()
    core.restobj.rest_set_config(get_configs())
    configs = get_configs()

    def method_dummy_false(aryfilter, ary_result):
        """異常系用"""
        ary_result['status'] = '-1'
        return False

    monkeypatch.setattr(core.restobj, 'rest_select', method_dummy_false)
    flg, getdata = core.select_menu_list(configs, None, None, [], [])

    assert flg == False
    assert getdata == result

def test_select_create_item_list_OK(monkeypatch):
    """
    select_create_item_list()の正常系テスト
    """

    result = [[None, '', '1', 'OASEメニュー1', 'パラメータシート(ホスト/オペレーション含む)', '1', 'ホスト用', '', '', 'OASE_MenuGroup(Host)', 'OASE_MenuGroup(Ref)', '', None, None, '2020/04/10 15:02:08', 'T_20200410150208611888', 'システム管理者'], [None, '', '2', 'OASEメニュー2', 'パラメータシート(ホスト/オペレーション含む)', '2', 'ホスト 用', '', '', 'テストメニュー（Host）', 'testメニュー （Ref）', '', 'テスト', None, '2020/04/16 17:35:02', 'T_20200416173502336962', 'システム管理者']]
    core = create_ita1core()
    configs = get_configs()

    def method_dummy_data(*args, **kwargs):
        """正常系用"""
        return [[None, '', '1', 'OASEメニュー1', 'パラメータシート(ホスト/オペレーション含む)', '1', 'ホスト用', '', '', 'OASE_MenuGroup(Host)', 'OASE_MenuGroup(Ref)', '', None, None, '2020/04/10 15:02:08', 'T_20200410150208611888', 'システム管理者'], [None, '', '2', 'OASEメニュー2', 'パラメータシート(ホスト/オペレーション含む)', '2', 'ホスト 用', '', '', 'テストメニュー（Host）', 'testメニュー （Ref）', '', 'テスト', None, '2020/04/16 17:35:02', 'T_20200416173502336962', 'システム管理者']]

    # 正常系
    monkeypatch.setattr(core.restobj, 'rest_select', method_dummy_true)
    monkeypatch.setattr(core.restobj, 'rest_get_row_data', method_dummy_data)

    flg, get_data = core.select_create_item_list(configs, 'パラメータシート')
    assert flg == True
    get_data == result

def test_select_create_item_list_NG(monkeypatch):
    """
    select_create_item_list()の異常系テスト
    """

    result = []
    core = create_ita1core()
    configs = get_configs()

    def method_dummy_false(*args, **kwargs):
        """異常系用"""
        return {}

    monkeypatch.setattr(core.restobj, 'rest_select', method_dummy_false)
    try:
        with pytest.raises(KeyError):
            flg, getdata = core.select_create_menu_info_list(configs)
            assert flg == False
            assert getdata == result
    except:
        assert flg == False
        assert getdata == result

