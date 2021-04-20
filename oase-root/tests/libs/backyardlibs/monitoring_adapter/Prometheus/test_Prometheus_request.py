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
  PrometheusRequest tests
"""


import pytest
import os
import datetime
import traceback
import pytz
import requests
import json

from importlib import import_module

from libs.backyardlibs.monitoring_adapter.Prometheus import Prometheus_request as PromReq


################################################################
# テスト用ダミークラス
################################################################
# レスポンスデータ
class DummyJson(object):

    content = ''


################################################################
# テスト
################################################################
# メイン処理
@pytest.mark.django_db
class TestSendRequest(object):

    ############################################################
    # テスト用ダミー関数
    ############################################################
    # Jsonデータ(正常系)
    def response_dummy_ok(self, *args, **kwargs):

        dummy = DummyJson()
        dummy.content = json.dumps({"result":"success"}).encode('utf-8')

        return dummy


    def response_dummy_fail(self, *args, **kwargs):

        dummy = DummyJson()
        dummy.content = json.dumps({"msg":"pytest"}).encode('utf-8')

        return dummy


    ############################################
    # Jsonデータ(異常系)
    def response_dummy_err(self, *args, **kwargs):

        dummy = DummyJson()
        dummy.content = {"result":"success"}

        return dummy


    ############################################################
    # テスト
    ############################################################
    def test_ok(self, monkeypatch):
        """
        正常系
        """

        monkeypatch.setattr(requests, 'post', self.response_dummy_ok)

        result = PromReq.send_request({'decisiontable':'pytest'})

        assert result == True


    def test_ng_reqdata_zero(self):
        """
        異常系(リクエストデータなし)
        """

        result = PromReq.send_request({})

        assert result == False


    def test_ng_json_err(self, monkeypatch):
        """
        異常系(JSONデータ異常)
        """

        monkeypatch.setattr(requests, 'post', self.response_dummy_err)

        result = PromReq.send_request({'decisiontable':'pytest'})

        assert result == False


    def test_ng_resp_err(self, monkeypatch):
        """
        異常系(応答ステータス異常)
        """

        monkeypatch.setattr(requests, 'post', self.response_dummy_fail)

        result = PromReq.send_request({'decisiontable':'pytest'})

        assert result == False


