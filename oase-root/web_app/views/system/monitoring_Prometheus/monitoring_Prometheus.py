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
    Prometheusアダプタ用画面表示補助クラス

"""


import pytz
import datetime
import json
import socket
import traceback

from django.http import HttpResponse
from django.http import HttpResponseServerError
from django.db import transaction
from django.conf import settings

from libs.commonlibs import define as defs
from libs.commonlibs.oase_logger import OaseLogger
from libs.commonlibs.aes_cipher import AESCipher

from web_app.models.Prometheus_monitoring_models import PrometheusAdapter, PrometheusMatchInfo, PrometheusMonitoringHistory
from web_app.models.models import RuleType, DataObject
from web_app.templatetags.common import get_message
from web_app.views.system.monitoring import get_rule_type_data_obj_dict

from web_app.serializers.unicode_check import UnicodeCheck

logger = OaseLogger.get_instance() # ロガー初期化


class PrometheusAdapterInfo():

    def __init__(self, adp_id, mni_id, name, ver, icon_name):

        self.adp_id = adp_id
        self.mni_id = mni_id
        self.name   = name
        self.ver    = ver
        self.icon_name = icon_name


    def __str__(self):

        return '%s(ver%s)' % (self.name, self.ver)


    def get_adapter_name(self):

        return '%s Adapter ver%s' % (self.name, self.ver)


    def get_adapter_id(self):

        return self.adp_id


    def get_icon_name(self):

        return self.icon_name


    def get_template_file(self):

        return ''


    def get_prometheus_items(self):

        return ''


    def get_info_list(self, request):

        return []


    def get_define(self):

        return {}


    def record_lock(self, adapter_id, request):

        pass


    def delete(self, json_str, request):
        """
        [メソッド概要]
          DB削除処理
        """

        response = {"status": "success"}

        return response


    def update(self, rq, request):
        """
        [メソッド概要]
          DB更新処理
        """

        response = {"status": "success",}

        return response


    def create(self, json_str, request):
        """
        [メソッド概要]
          DB作成処理
        """

        response = {"status": "success",}

        return response


    def _validate(self, rq, error_msg, request, mode):
        """
        [概要]
        入力チェック
        [引数]
        rq: dict リクエストされた入力データ
        error_msg: dict
        [戻り値]
        """

        return False


