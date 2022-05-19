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
    Mailサーバで受信しているメールを管理する
"""


import datetime
import django
import json
import os
import sys
import pytz
import traceback

# OASE モジュール importパス追加
my_path = os.path.dirname(os.path.abspath(__file__))
tmp_path = my_path.split('oase-root')
root_dir_path = tmp_path[0] + 'oase-root'
sys.path.append(root_dir_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'confs.frameworkconfs.settings'
django.setup()

from django.db import transaction

# ロガー初期化
from libs.commonlibs.oase_logger import OaseLogger
logger = OaseLogger.get_instance()

from web_app.models.Mail_monitoring_models import MailTriggerHistory 
from libs.backyardlibs.monitoring_adapter.Mail.Mail_api import MailApi


class ManageTrigger:

    def __init__(self, mail_adapter_id, user):
        """
        Mail監視マスタID=mail_adapter_idとなるMail障害取得履歴管理を取得する
        """
        self.mail_adapter_id = mail_adapter_id
        self.user = user


    def main(self, triggerid_lastchange_list):
        """
        [概要]
        障害取得管理を行う。Mailから取得したtriggerid,lastchangeと、
        oaseに登録されているtriggerid,lastchangeを比較し登録済みの障害か、未登録の障害か調べ結果を返す
        [引数]
        triggerid_lastchange_list: [(trigger_id, lastchange),(trigger_id, lastchange),...]
        Mail apiで得られるtriggeridとlastchangeのsetのリスト
        [戻り値]
        list: 各trigger_idの管理状態をboolのリストとして返す。
              未登録の障害又は新たに障害が発生した場合はTrue, 既に取得済みの障害の場合はFalse
              例外が発生した場合は空のリストを返す
        """
        logger.logic_log('LOSI00001', 'triggerid_lastchange_list count:%s' % (len(triggerid_lastchange_list)))

        trigger_history_list = list(MailTriggerHistory.objects.filter(mail_adapter_id=self.mail_adapter_id).values_list('trigger_id', flat=True))

        result = []
        for trigger_id, lastchange in triggerid_lastchange_list:

            # トリガーID未登録時はテーブルに追加して、新規障害が発生とする。
            if trigger_id in trigger_history_list:
                result.append(False)

            else:
                result.append(True)
                new_trigger = self.create(trigger_id, lastchange, self.user)


        logger.logic_log('LOSI00002', 'result: %s' % (result))
        return result


    def create(self, trigger_id, lastchange, user):
        """
        [概要]
        レコード作成
        [戻り値]
        MailTriggerHistory: 作成したモデルを返す。 例外の場合はNoneを返す
        """
        logger.logic_log('LOSI00001', 'trigger_id: %s, lastchange: %s, user_name: %s' % (trigger_id, lastchange, user))

        mail_trigger_his = MailTriggerHistory(
            mail_adapter_id = self.mail_adapter_id,
            trigger_id = trigger_id,
            lastchange = lastchange,
            last_update_user = user,
            last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
        )
        mail_trigger_his.save(force_insert=True)

        logger.logic_log('LOSI00002', 'mail_trigger_history_id: %s' % (mail_trigger_his))
        return mail_trigger_his


