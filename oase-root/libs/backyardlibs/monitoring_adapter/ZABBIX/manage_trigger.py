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
    ZABBIXで発生している障害を管理する
"""


import datetime
import django
import json
import os
import sys
import pytz
import traceback
import ast

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

from web_app.models.ZABBIX_monitoring_models import ZabbixTriggerHistory 
from libs.backyardlibs.monitoring_adapter.ZABBIX.ZABBIX_api import ZabbixApi


class ManageTrigger:

    def __init__(self, zabbix_adapter_id, user):
        """
        ZABBIX監視マスタID=zabbix_adapter_idとなるZABBIX障害取得履歴管理を取得する
        """
        self.zabbix_adapter_id = zabbix_adapter_id
        self.user = user
        self.path = os.path.join(*[root_dir_path, 'temp', 'monitor'])
        self.filepath = os.path.join(self.path, 'zabbix%s.dat' % (self.zabbix_adapter_id))


    def main(self, triggerid_lastchange_list):
        """
        [概要]
        障害取得管理を行う。zabbixから取得したtriggerid,lastchangeと、
        oaseに登録されているtriggerid,lastchangeを比較し登録済みの障害か、未登録の障害か調べ結果を返す
        [引数]
        triggerid_lastchange_list: [(trigger_id, lastchange),(trigger_id, lastchange),...]
        ZABBIX apiで得られるtriggeridとlastchangeのsetのリスト
        [戻り値]
        list: 各trigger_idの管理状態をboolのリストとして返す。
              未登録の障害又は新たに障害が発生した場合はTrue, 既に取得済みの障害の場合はFalse
              例外が発生した場合は空のリストを返す
        """

        logger.logic_log('LOSI00001', 'zabbix_adapter_id: %s, triggerid_lastchange_list: %s' % (self.zabbix_adapter_id, triggerid_lastchange_list))

        result = []

        # ディレクトリが存在しなければ作成
        os.makedirs(self.path, exist_ok=True)

        # ファイルが存在しなければ取得分は全て追加
        if os.path.exists(self.filepath) == False:
            result = [True] * len(triggerid_lastchange_list)

        # 前回取得データを保存したファイルをオープン
        else:
            with open(self.filepath, 'r') as fp:
                before_data = fp.read()
                before_data = ast.literal_eval(before_data)

            result = self.compare_data(before_data, triggerid_lastchange_list)


        """
        trigger_history_list = ZabbixTriggerHistory.objects.select_for_update().filter(zabbix_adapter_id=self.zabbix_adapter_id)
        trigger_history_dict = {t.trigger_id:t for t in trigger_history_list}

        result = []
        active_trigger_id_list = []
        for trigger_id, lastchange in triggerid_lastchange_list:

            active_trigger_id_list.append(trigger_id)
            # トリガーID未登録時はテーブルに追加して、新規障害が発生とする。
            if not trigger_id in trigger_history_dict.keys():
                new_trigger = self.create(trigger_id, lastchange, self.user)
                result.append(True)
                continue

            if lastchange == trigger_history_dict[trigger_id].lastchange:
                # lastchangeが変わっていなければ登録済み
                result.append(False)
            else:
                # lastchangeが変わっているなら障害が発生 更新 
                _ = self.update(trigger_history_dict[trigger_id], lastchange, self.user)
                result.append(True)

        self.delete_resolved_records(trigger_history_list, active_trigger_id_list)
        """

        logger.logic_log('LOSI00002', 'zabbix_adapter_id: %s, result: %s' % (self.zabbix_adapter_id, result))
        return result


    def create(self, trigger_id, lastchange, user):
        """
        [概要]
        レコード作成
        [戻り値]
        ZabbixTriggerHistory: 作成したモデルを返す。　例外の場合はNoneを返す
        """
        logger.logic_log('LOSI00001', 'trigger_id: %s, lastchange: %s, user_name: %s' % (trigger_id, lastchange, user))

        zabbix_trigger_his = ZabbixTriggerHistory(
            zabbix_adapter_id = self.zabbix_adapter_id,
            trigger_id = trigger_id,
            lastchange = lastchange,
            last_update_user = user,
            last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC')),
        )
        zabbix_trigger_his.save(force_insert=True)

        logger.logic_log('LOSI00002', 'zabbix_trigger_history_id: %s' % (zabbix_trigger_his))
        return zabbix_trigger_his


    def update(self, trigger_his, lastchange, user):
        """
        [概要]
        lastchangeを更新する
        """
        logger.logic_log('LOSI00001', 'trigger_his: %s, lastchange: %s, user: %s' % (trigger_his, lastchange, user))

        trigger_his.lastchange = lastchange
        trigger_his.last_update_user = user
        trigger_his.last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC'))
        trigger_his.save(force_update=True)

        logger.logic_log('LOSI00002', 'zabbix_trigger_history_id: %s' % (trigger_his))


    def delete_resolved_records(self, trigger_history_list, active_trigger_id_list):
        """
        [概要]
        解決済みになった障害は削除する
        [引数]
        trigger_history_list: テーブルに登録されているZabbixTriggerHistoryのクラスのリスト
        active_trigger_id_list: zabbixから取得したトリガーIDのリスト
        """
        for t in trigger_history_list:
            if not t.trigger_id in active_trigger_id_list:
                logger.logic_log('LOSI25000', self.zabbix_adapter_id, t.trigger_id)
                t.delete()


    def compare_data(self, trg1_list, trg2_list):
        """
        [概要]
        Zabbix から取得したトリガーとその更新日時を比較する

        [引数]
        trg1_list : 比較対象1のトリガーID、および、更新日時のset配列
        trg2_list : 比較対象2のトリガーID、および、更新日時のset配列

        [戻り値]
        list : 真偽値の配列(True=trg2_listの要素に変更あり, False=trg1_listと同じ要素)
        """

        result = []

        # 比較対象2にのみ存在する要素を取得
        diff_list = list(set(trg2_list) - set(trg1_list))

        # 比較対象2の各要素に対して、差分の有無を真偽値として返却
        for t2 in trg2_list:
            if t2 in diff_list:
                result.append(True)

            else:
                result.append(False)


        return result


    def save_trigger_info(self, trg_list):
        """
        [概要]
        Zabbix から取得したトリガーとその更新日時を保存する

        [引数]
        trg_list : 保存するトリガー情報リスト
        """

        with open(self.filepath, 'w') as fp:
            fp.write(str(trg_list))


