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


"""


import pytest
import os
import sys
import django
import json
import pytz
import datetime
import subprocess
import traceback
import ast
import pika
import time
import threading
import memcache
import copy
from time import sleep

from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from importlib import import_module

from libs.backyardlibs.backyard_common import disconnect

from web_app.models.models import User, EventsRequest, RuleType
from web_app.serializers.events_request import EventsRequestSerializer
from libs.commonlibs import define as defs
from libs.commonlibs.rabbitmq import RabbitMQ

from libs.webcommonlibs.events_request import EventsRequestCommon
from libs.webcommonlibs.common import TimeConversion

from backyards.accept_driver.oase_accept import data_list


@pytest.mark.django_db
class TestOaseAcceptDataList:
    """
    oase_accept.data_list テストクラス
    """

    # disconnect()をmonkeypatchできないため、コメントアウト
    #def test_data_list_ok(self, monkeypatch):
    #    """
    #    正常系
    #    """
    #
    #    user = User.objects.get(user_id=1)
    #    rule_type_id_list = {'pytest_name': 9999}
    #    label_count_list = {'pytest_name': 1}
    #
    #    monkeypatch.setattr(EventsRequestSerializer, 'is_valid', lambda data=None:True)
    #
    #    json_str = {
    #        'decisiontable': 'pytest_name',
    #        'requesttype': '1',
    #        'eventdatetime': '2020/06/29 11:27:00',
    #        'eventinfo': ['1'],
    #        'traceid': 'TOS202006300025273975321dfee20a399d466e92ee3610457efc6b'
    #    }
    #
    #    body = json.dumps(json_str).encode('utf-8')
    #
    #    assert data_list(body, user, rule_type_id_list, label_count_list)


    def test_data_list_ng(self):
        """
        異常系
        """

        user = User.objects.get(user_id=1)
        rule_type_id_list = {}
        label_count_list = {}

        json_str = {
            'decisiontable': 'pytest_name',
            'requesttype': '1',
            'eventdatetime': '2020/06/29 11:27:00',
            'eventinfo': ['1'],
            'traceid': 'TOS202006300025273975321dfee20a399d466e92ee3610457efc6b'
        }

        assert not data_list(json_str, user, rule_type_id_list, label_count_list)

