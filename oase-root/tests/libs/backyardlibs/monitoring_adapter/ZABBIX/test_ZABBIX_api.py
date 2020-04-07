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
[概要]
  ZABBIX_fomatting tests


"""


import pytest
import os
import datetime
import traceback
import pytz
import unittest
from unittest.mock import MagicMock
from unittest      import mock
from importlib     import import_module

"""
def test_ZabbixApi(monkeypatch):
    module = import_module('web_app.models.ZABBIX_monitoring_models')
    ZabbixAdapter = getattr(module, 'ZabbixAdapter')
    ZabbixApi = import_module('libs.backyardlibs.monitoring_adapter.ZABBIX.ZABBIX_api')
    
    # テスト用データを作成してインスタンスを作成
    ZA = ZabbixAdapter(
            zabbix_disp_name = 'a',
            hostname         = 'pytest-host',
            username         = 'pytest',
            password         = 'pytest',
            protocol         = 'http',
            port             = '80',
            rule_type_id     = '1',
            last_update_user = 'pytest',
    )

    # インスタンス作成成功パターン
    api = None
    try:
        api = ZabbixApi.ZabbixApi(ZA)
        assert api is not None
    except:
        assert False

    # APIから全件取得
    result = api.get_active_triggers(0) 
    assert result is not None

    # APIから0件取得
    result = api.get_active_triggers(16000000000) 
    assert result is not None

    # TypeErrorの確認（unixtimeが文字列の場合で確認）
    try:
        with pytest.raises(TypeError):
            api.get_active_triggers('0')
            assert False
    except:
        assert False

    # TypeErrorの確認（日付形式で確認）
    try:
        with pytest.raises(TypeError):
            now = datetime.datetime.now(pytz.timezone('UTC'))
            api.get_active_triggers(now)
            assert False
    except:
        assert False

    # ログアウト
    try:
        lo_result = api.logout()
        assert lo_result is not None
    except:
        assert False

    # APIから全件取得(ログアウトした状態で実施)
    with pytest.raises(Exception):
        api.get_active_triggers(0)
        assert False

    # インスタンス作成失敗パターン
    ZA.username = 'xxxxx'
    with pytest.raises(Exception):
        zabbix_api = ZabbixApi.ZabbixApi(ZA)
        assert False
"""
