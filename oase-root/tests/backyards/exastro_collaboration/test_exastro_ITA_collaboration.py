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
  エージェントドライバ 実行処理


"""


import pytest
import os
import django
import configparser
import datetime
import traceback
import pytz

from django.db import transaction
from mock import Mock


from libs.backyardlibs.oase_action_common_libs import ConstantModules as Cstobj
from libs.backyardlibs.action_driver.ITA.ITA_core import ITA1Core
from libs.commonlibs.define import *
from libs.webcommonlibs.events_request import EventsRequestCommon
from web_app.models.models import EventsRequest


# 環境変数設定
oase_root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..')
os.environ['OASE_ROOT_DIR'] = oase_root_dir 
os.environ['RUN_INTERVAL']  = '3600'
os.environ['PYTHON_MODULE'] = '/usr/bin/python3'
os.environ['LOG_LEVEL']     = "TRACE"
os.environ['LOG_DIR']       = oase_root_dir + "/logs/backyardlogs/exastro_collaboration/"


@pytest.fixture(scope='function')
def exastro_ITA_collaboration_data():

    # 動的インポート
    # module = import_module('web_app.models.ZABBIX_monitoring_models')
    # ZabbixMonitoringHistory = getattr(module, 'ZabbixMonitoringHistory')

    # zabbix_monitoring_history_list = []
    # for index in range(1, 5):
    #     zabbix_monitoring_history = ZabbixMonitoringHistory(
    #             zabbix_adapter_id     = TEST_ZABBIX_ADAPTER_ID + index,
    #             zabbix_lastchange     = index,
    #             status                = index,
    #             status_update_id      = gethostname(),
    #             last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
    #             last_update_user      = 'unittest_user',
    #         )
    #     zabbix_monitoring_history.save(force_insert=True)
    #     zabbix_monitoring_history_list.append(zabbix_monitoring_history)

    yield

    for zabbix_monitoring_history_item in zabbix_monitoring_history_list:
        zabbix_monitoring_history_item.delete()




@pytest.mark.django_db
# @pytest.mark.usefixtures('prepare_data')
class TestITAParameterSheetMenuManager(object):

    @classmethod
    def setup_class(cls):
        print('TestITAParameterSheetMenuManager - start')

    @classmethod
    def teardown_class(cls):
        print('TestITAParameterSheetMenuManager - end')

    def setup_method(self, method):
        print('method_name: {}'.format(method.__name__))

        # 動的インポート
        module = import_module('backyards.monitoring_adapter.ZABBIX_monitoring')
        ITAParameterSheetMenuManager = getattr(module, 'ITAParameterSheetMenuManager')

        self.target = ITAParameterSheetMenuManager()

    def teardown_method(self, method):
        print('method_name: {}:'.format(method.__name__))
        del self.target


    ########################
    # TESTここから
    ########################

    @pytest.mark.usefixtures('')
    def test_get_menu_list_1(self, monkeypatch):
        """
        パラメーターシートメニューの情報リストを取得(正常系)
        """
        module = getattr(import_module('web_app.views.system'), 'ITA_paramsheet')

        monkeypatch.setattr(module, 'select_create_menu_info_list', lambda x, y, z: (False, {}))







