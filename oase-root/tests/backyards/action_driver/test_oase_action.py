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
アクションドライバメイン処理（親プロセス）
"""

import pytest
import unittest

import os
import django
import configparser
import datetime
import sys
import traceback
import pytz

from importlib import import_module
from django.db import transaction
from django.conf import settings

from libs.backyardlibs.oase_action_common_libs import ConstantModules as Cstobj
from libs.commonlibs.aes_cipher import AESCipher
from libs.commonlibs.define import *
from libs.webcommonlibs.events_request import EventsRequestCommon
from web_app.models.models import ActionHistory, User


oase_root_dir = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '../..')
log_dir = oase_root_dir + "/logs/backyardlogs/oase_action"

os.environ['OASE_ROOT_DIR'] = oase_root_dir
os.environ['RUN_INTERVAL'] = '10'
os.environ['PYTHON_MODULE'] = '/usr/bin/python3'
os.environ['LOG_LEVEL'] = "TRACE"
os.environ['LOG_DIR'] = log_dir

from backyards.action_driver.oase_action import ActionDriverMainModules

# 実行ファイル名取得
filename, ext = os.path.splitext(os.path.basename(__file__))
# ログファイルのパスを生成
log_file_path = log_dir + '/' + 'oase_action.log'


def set_test_regist_data():
    """
    テストで使用するデータの作成
    """
    now = datetime.datetime.now(pytz.timezone('UTC'))
    trace_id = EventsRequestCommon.generate_trace_id(now)
    response_id = 1

    act_his = ActionHistory(
        response_id=response_id,
        trace_id=trace_id,
        rule_type_id=1,
        rule_type_name='pytest_ruletable',
        rule_name='pytest_rule',
        execution_order=1,
        action_start_time=now,
        action_type_id=1,
        status=2106,
        status_detail=0,
        status_update_id='pytest_id',
        retry_flag=False,
        retry_status=None,
        retry_status_detail=None,
        action_retry_count=0,
        last_act_user='administrator',
        last_update_timestamp=now,
        last_update_user='administrator'
    )
    act_his.save(force_insert=True)

    now = datetime.datetime.now(pytz.timezone('UTC'))

    user = User(
        user_id=Cstobj.DB_OASE_USER,
        user_name='unittest_procedure',
        login_id='',
        mail_address='',
        password='',
        disp_mode_id=DISP_MODE.DEFAULT,
        lang_mode_id=LANG_MODE.JP,
        password_count=0,
        password_expire=datetime.datetime.now(pytz.timezone('UTC')),
        last_update_user='unittest_user',
        last_update_timestamp=datetime.datetime.now(pytz.timezone('UTC')),
    )
    user.save(force_insert=True)


def delete_test_regist_data():
    """
    テストで使用したデータの削除
    """

    # テーブル初期化
    ActionHistory.objects.all().delete()
    User.objects.all().delete()


def dummy_true(*args, **kwargs):
    """正常系用 request.postの戻り値"""
    return True


def dummy_false(*args, **kwargs):
    """異常系用 request.postの戻り値"""
    return False


@pytest.mark.django_db
def test_regist_exastro(monkeypatch):
    """
    regist_exastro()はTrueかFalseを返すためそのテストを行う
    """

    delete_test_regist_data()
    set_test_regist_data()

    ADM = ActionDriverMainModules(log_file_path)

    # Trueの場合
    target_method = ActionDriverMainModules
    monkeypatch.setattr(
        target_method, 'ExecuteSubProcess', dummy_true)

    aryPCB = {}
    expected_aryPCB_keys = []

    result_return = ADM.regist_exastro(aryPCB)
    assert result_return
    assert expected_aryPCB_keys == list(aryPCB)

    # Falseの場合
    monkeypatch.setattr(
        target_method, 'ExecuteSubProcess', dummy_false)

    result_return = ADM.regist_exastro(aryPCB)
    assert not result_return

    # 子プロで失敗する場合
    with pytest.raises(Exception):
        result_return = ADM.regist_exastro(aryPCB)
        assert False

    delete_test_regist_data()
    del ADM
