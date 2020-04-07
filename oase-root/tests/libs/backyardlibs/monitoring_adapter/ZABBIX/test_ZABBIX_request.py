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

from libs.backyardlibs.monitoring_adapter.ZABBIX.ZABBIX_request import send_request


def test_send_request(monkeypatch):
    """
    send_request()はTrueかFalseを返すためそのテストを行う

    """
    class DummyTrue:
        """正常系用 response.contentを置き換えるクラス"""
        content = b'{"result": true}'

    class DummyFalse:
        """異常系用 response.contentを置き換えるクラス"""
        content = b'{"result": false}'

    def post_dummy_true(*args, **kwargs):
        """正常系用 request.postの戻り値"""
        return DummyTrue()

    def post_dummy_false(*args, **kwargs):
        """異常系用 request.postの戻り値"""
        return DummyFalse()

    # 一致するルールが存在する場合
    monkeypatch.setattr(requests, 'post', post_dummy_true)
    request_data = {
        'ruletable': 'rulet01',
        'requesttype': '1',
        'eventdatetime': '2020/1/14 18:27:29',
        'eventinfo': ['1'],
    }
    request_data_dic = {'request': [request_data]}
    assert send_request(request_data_dic)

    # 一致するルールが存在しない場合
    monkeypatch.setattr(requests, 'post', post_dummy_false)
    request_data = {
        'ruletable': 'test',
        'requesttype': '1',
        'eventdatetime': '',
        'eventinfo': ['1'],
    }
    request_data_dic = {'request': [request_data]}
    assert send_request(request_data_dic) is False

    # ルールが0件の場合
    with pytest.raises(Exception):
        request_data_list = []
        request_data_dic['request'] = request_data_list
        send_request(request_data_dic)
        assert False
