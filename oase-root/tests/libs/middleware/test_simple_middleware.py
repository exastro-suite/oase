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
from mock import Mock


from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.test import override_settings

from libs.middleware.simple_middleware import SimpleMiddleware
from web_app.models.models import BlackListIPAddress, WhiteListIPAddress


@pytest.mark.django_db
def test__chk_white_black_list(django_db_setup):
    """
    関数の戻り値がTrueの時とFalseの時の2パターンのテストを行う
    """
    request = Mock()    
    simple = SimpleMiddleware(Mock())
    now = datetime.datetime.now(pytz.timezone('UTC'))
    ipaddr = '127.0.0.1'
    user = 'oasetest'

    ipaddress_info = WhiteListIPAddress(
        ipaddr = ipaddr,
        last_update_user = user,
        last_update_timestamp = now
    ).save(force_insert=True)

    result = simple._chk_white_black_list(ipaddr)
    assert result == True

    WhiteListIPAddress.objects.filter(ipaddr=ipaddr).delete()

    ipaddress_info = BlackListIPAddress(
        ipaddr = ipaddr,
        last_update_user = user,
        last_update_timestamp = now
    ).save(force_insert=True)

    result = simple._chk_white_black_list(ipaddr)
    assert result == False 



@pytest.mark.django_db
@override_settings(DISABLE_WHITE_BLACK_LIST=False) 
def test___call__(admin):
    """
    PermissionDenied例外が発生するテスト
    """
    with pytest.raises(PermissionDenied):
        now = datetime.datetime.now(pytz.timezone('UTC'))
        ipaddr = '127.0.0.1'
        user = 'oasetest'
        ipaddress_info = BlackListIPAddress(
            ipaddr = ipaddr,
            last_update_user = user,
            last_update_timestamp = now
        ).save(force_insert=True)
        
        response = admin.get(reverse('web_app:user:white_list'))
        my_middleware = SimpleMiddleware(Mock())
        my_middleware(response.wsgi_request)





