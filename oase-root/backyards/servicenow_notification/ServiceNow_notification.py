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
  ServiceNow通知メイン処理
"""


import base64
import json
import os
import sys
import traceback
import django
import datetime
import requests
import ssl
import urllib3
import pytz
import fcntl
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context


# OASE モジュール importパス追加
my_path       = os.path.dirname(os.path.abspath(__file__))
tmp_path      = my_path.split('oase-root')
root_dir_path = tmp_path[0] + 'oase-root'
sys.path.append(root_dir_path)

# 排他制御ファイル名
exclusive_file = tmp_path[0] + 'oase-root/temp/exclusive/servicenow_notification.lock'

# OASE モジュール import
# #LOCAL_PATCH#
os.environ['DJANGO_SETTINGS_MODULE'] = 'confs.frameworkconfs.settings'
django.setup()

from django.conf import settings
from django.db import transaction
from django.db.models import Q

#################################################
# デバック用
if settings.DEBUG and getattr(settings, 'ENABLE_NOSERVICE_BACKYARDS', False):
    oase_root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..')
    os.environ['OASE_ROOT_DIR'] = oase_root_dir 
    os.environ['RUN_INTERVAL']  = '10'
    os.environ['PYTHON_MODULE'] = '/usr/bin/python3'
    os.environ['LOG_LEVEL']     = "TRACE"
    os.environ['LOG_DIR']       = oase_root_dir + "/logs/backyardlogs/servicenow_notification/"
#################################################

# 環境変数取得
try:
    root_dir_path = os.environ['OASE_ROOT_DIR']
    run_interval  = os.environ['RUN_INTERVAL']
    python_module = os.environ['PYTHON_MODULE']
    log_dir       = os.environ['LOG_DIR']
    log_level     = os.environ['LOG_LEVEL']
except Exception as e:
    print(str(e))
    sys.exit(2)

# ロガー初期化
from libs.commonlibs.oase_logger import OaseLogger
logger = OaseLogger.get_instance()


from web_app.models.models import User, RuleType, EventsRequest
from web_app.models.ServiceNow_models import ServiceNowDriver

from libs.commonlibs.define import *
from libs.commonlibs.aes_cipher import AESCipher

#-------------------
# STATUS
#-------------------
DB_OASE_USER = -2140000008


def events_request_update(request_id, status, user_name):
    """
    [概要]
    リクエスト管理更新メソッド
    """
    logger.logic_log('LOSI00001', 'request_id: %s, status: %s' % (request_id, status))

    try:
        with transaction.atomic():
            now = datetime.datetime.now()

            events_request = EventsRequest.objects.select_for_update().get(request_id=request_id)
            events_request.status = status
            events_request.last_update_timestamp = now
            events_request.last_update_user = user_name
            events_request.save(force_update=True)

    except Exception as e:
        logger.system_log('LOSM31003', traceback.format_exc())
        return False

    return True


#-------------------
# MAIN
#-------------------
if __name__ == '__main__':

    with open(exclusive_file, "w") as f:

        # 排他ロックを獲得する。
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)

        except IOError:
            sys.exit(0)

        try:
            with transaction.atomic():
                logger.logic_log('LOSI00001', 'Start ServiceNow notification.')
                user_name = User.objects.get(user_id=DB_OASE_USER).user_name

                # ServiceNow連携設定のルール種別IDを取得
                ruletypeid_list = list(RuleType.objects.filter(
                    Q(unknown_event_notification='2') | Q(unknown_event_notification='3')).order_by(
                    'rule_type_id').values_list('rule_type_id', flat=True))

                # ルール未検出かつプロダクション環境かつServiceNow連携設定のレコード取得
                rset = EventsRequest.objects.filter(
                    status=RULE_UNMATCH, request_type_id=PRODUCTION, rule_type_id__in=ruletypeid_list).order_by(
                    'request_id').values(
                    'request_id', 'trace_id', 'request_type_id', 'rule_type_id', 'event_to_time', 'event_info', 'status')

                for r in rset:
                    # イベントリクエストのステータスを「ServiceNow連携中」に更新
                    ret = events_request_update(r['request_id'], RULE_IN_COOPERATION, user_name)
                    if not ret:
                        logger.system_log('LOSM31002', r['request_id'], RULE_IN_COOPERATION)
                        raise Exception()

                    rt_data = RuleType.objects.filter(rule_type_id=r['rule_type_id'])
                    snd_data = ServiceNowDriver.objects.filter(servicenow_driver_id=rt_data[0].servicenow_driver_id)

                    cipher = AESCipher(settings.AES_KEY)
                    password = cipher.decrypt(snd_data[0].password)

                    user = snd_data[0].username

                    url = "{}://{}:{}/api/now/table/incident".format(
                        snd_data[0].protocol, snd_data[0].hostname, snd_data[0].port)

                    headers = {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                    }

                    temp = snd_data[0].count + 1
                    count = str(temp).zfill(4)

                    ary_data = {}
                    ary_data['short_description'] = 'OASE Unknown Event Notify #' + count
                    ary_data['description'] = {
                        'trace_id': r['trace_id'],
                        'decisiontable': rt_data[0].rule_type_name,
                        'eventdatetime': r['event_to_time'],
                        'eventinfo': r['event_info']
                    }
                    str_para_json_encoded = json.dumps(ary_data, default=str)

                    proxies = {
                        'http' : snd_data[0].proxy,
                        'https': snd_data[0].proxy,
                    }

                    response = requests.post(
                        url, auth=(user, password), headers=headers, timeout=30,verify=False,
                        data=str_para_json_encoded.encode('utf-8'), proxies=proxies)

                    if response.status_code != 201:
                        logger.system_log('LOSM31000', r['trace_id'], response.status_code)
                        raise Exception()

                    # イベントリクエストのステータスを「ServiceNow連携済み」に更新
                    ret = events_request_update(r['request_id'], RULE_ALREADY_LINKED, user_name)
                    if not ret:
                        logger.system_log('LOSM31002', r['request_id'], RULE_ALREADY_LINKED)
                        raise Exception()

                    servicenow = ServiceNowDriver.objects.select_for_update().get(
                        servicenow_driver_id=rt_data[0].servicenow_driver_id)
                    servicenow.count = snd_data[0].count + 1
                    servicenow.save(force_update=True)

        except Exception as e:
            logger.system_log('LOSM31001', 'main')
            logger.logic_log('LOSM00001', 'e: %s, Traceback: %s' % (e, traceback.format_exc()))
            # イベントリクエストのステータスを「ルール未検出」に更新
            ret = events_request_update(r['request_id'], RULE_UNMATCH, user_name)
            if not ret:
                logger.system_log('LOSM31002', r['request_id'], RULE_UNMATCH)

        fcntl.flock(f, fcntl.LOCK_UN)

    sys.exit(0)
