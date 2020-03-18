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
  テストリクエスト投入コマンド

[引数]


[戻り値]


"""




import os
import pytz
import time
import datetime
import random
import traceback

from django.core.management.base import BaseCommand

from libs.commonlibs import define as defs
from libs.webcommonlibs.password import RandomPassword
from libs.webcommonlibs.events_request import EventsRequestCommon
from web_app.models.models import RuleType, DataObject, EventsRequest
from web_app.views.rule.rule import _get_data_by_excel


class Command(BaseCommand):

    help = '疑似リクエスト送信コマンド'

    def add_arguments(self, parser):

        parser.add_argument('-H', '--host',     action='store', default='', type=str, dest='host',     help='webサーバーのIPアドレス', required=True)
        parser.add_argument('-P', '--port',     action='store', default=0,  type=int, dest='port',     help='webサーバーのポート番号', required=True)
        parser.add_argument('-r', '--rule',     action='store', default='', type=str, dest='rule',     help='リクエスト対象のルールID。指定のルールが存在しない場合はエラー、無指定なら全てのルールID')
        parser.add_argument('-f', '--file',     action='store', default='', type=str, dest='filename', help='tsvファイル(絶対パス)。リクエストするイベント情報')
        parser.add_argument('-q', '--request',  action='store', default=2,  type=int, dest='reqtype',  help='リクエスト種別。0:ランダム、1:プロダクション、2:ステージング、無指定:ステージング、それ以外の値:エラー')
        parser.add_argument('-c', '--reqcount', action='store', default=1,  type=int, dest='reqcnt',   help='1回のリクエスト送信数。0>:1回、0:ランダム(1-100)、1-100:指定の回数、100<:100回')
        parser.add_argument('-p', '--repeat',   action='store', default=0,  type=int, dest='repeat',   help='リクエスト送信の繰り返し回数。無指定なら繰り返しなし')
        parser.add_argument('-i', '--interval', action='store', default=1,  type=int, dest='interval', help='繰り返しの間隔(秒単位)。無指定なら1秒間隔')


    def handle(self, *args, **options):

        random.seed()

        try:
            # パラメーター取得
            self.now       = datetime.datetime.now(pytz.timezone('UTC'))
            self.host      = options['host']
            self.port      = options['port']
            self.rule_ids  = self.get_target_ruleid_list(options['rule'])
            self.req_type  = options['reqtype']
            self.count     = options['reqcnt']
            self.repeat    = options['repeat']
            self.interval  = options['interval']
            self.data_objs = {}

            # パラメーターチェック
            if len(self.rule_ids) <= 0:
                raise Exception('送信対象のルール種別がありません')

            if self.req_type not in [0, 1, 2]:
                raise Exception('リクエスト種別が不正です')

            if self.count == 0:
                self.count = random.randint(1, 100)

            if self.count < 0:
                self.count = 1

            if self.count > 100:
                self.count = 100

            if self.repeat < 0:
                self.repeat = 0

            if self.interval <= 0:
                self.interval = 1

            if self.repeat == 0:
                self.interval = 0

            # ルール別データオブジェクト取得
            self.get_data_objects(options['filename'])

            # プロダクション向けのリクエストを送信する可能性がある場合は確認
            if self.req_type in [0, 1]:
                while True:
                    choice = input("プロダクション向けのリクエストを送信しようとしています。\n実行しても、よろしいですか？ (y/n)\n").lower()
                    if choice in ['y', 'yes']:
                        break

                    elif choice in ['n', 'no']:
                        return

            # リクエスト送信
            total_cnt = 0
            for repeat_cnt in range(self.repeat + 1):
                events_request_list = []

                for req_cnt in range(self.count):
                    rule_type_id = random.choice(self.rule_ids)
                    req_type_id = self.req_type
                    if req_type_id == 0:
                        req_type_id = random.randint(1, 2)

                    evinfo_str = ''
                    evinfo_str = random.choice(self.data_objs[rule_type_id])
                    evinfo_str = '{"EVENT_INFO":[%s]}' % (evinfo_str)

                    evreq_obj = EventsRequest(
                        trace_id               = EventsRequestCommon.generate_trace_id(),
                        request_type_id        = req_type_id,
                        rule_type_id           = rule_type_id,
                        request_reception_time = self.now,
                        request_user           = 'TestCommand',
                        request_server         = 'TestCommand',
                        event_to_time          = self.now,
                        event_info             = evinfo_str,
                        status                 = defs.UNPROCESS,
                        status_update_id       = '',
                        retry_cnt              = 0,
                        last_update_timestamp  = self.now,
                        last_update_user       = 'TestCommand'
                    )

                    events_request_list.append(evreq_obj)

                if len(events_request_list) > 0:
                    EventsRequest.objects.bulk_create(events_request_list)

                if self.interval > 0:
                    time.sleep(self.interval)

        except Exception as e:
            print(e)


    def get_target_ruleid_list(self, rule_str):

        ret_val = []

        rule_cond = []
        if rule_str:
            rule_temp_list = rule_str.split(',')
            for rule_temp in rule_temp_list:
                rule_temp = rule_temp.split('-')
                if len(rule_temp) == 1:
                    rule_temp = int(rule_temp[0])
                    if rule_temp not in rule_cond:
                        rule_cond.append(rule_temp)

                elif len(rule_temp) == 2:
                    rule_min = int(rule_temp[0] if rule_temp[0] < rule_temp[1] else rule_temp[1])
                    rule_max = int(rule_temp[0] if rule_temp[0] > rule_temp[1] else rule_temp[1])
                    for i in range(rule_min, rule_max + 1):
                        if i not in rule_cond:
                            rule_cond.append(i)

                else:
                    pass


        rset = RuleType.objects.all()
        if len(rule_cond) > 0:
            rset = rset.filter(rule_type_id__in=rule_cond)

        ret_val = list(rset.values_list('rule_type_id', flat=True))

        return ret_val


    def get_data_objects(self, filename):

        if filename and not os.path.exists(filename):
            filename = ''
            print('指定のファイルが存在しないため、ランダム値を使用します。')

        # ファイルからイベント情報取得
        if filename:
            event_list, msg_list, msg = _get_data_by_excel(None, filename, filename, self.rule_ids[0])
            if len(msg_list) > 0:
                print('エラーが発生したため中断します')
                print(msg)
                print(msg_list)

            label_list = []
            cond_ids   = []
            rset = DataObject.objects.filter(rule_type_id=self.rule_ids[0]).values('label', 'conditional_expression_id').order_by('data_object_id')
            for rs in rset:
                if rs['label'] not in label_list:
                    label_list.append(rs['label'])
                    cond_ids.append(rs['conditional_expression_id'])

            self.data_objs[self.rule_ids[0]] = []
            for eve_info in event_list:
                tmp_data_objs = []
                for k, v in eve_info.items():
                    if k in ['row', 'eventtime']:
                        continue

                    tmp_data_objs.append(str(v))

                evinfo_str = ''
                for cid, v in zip(cond_ids, tmp_data_objs):
                    if evinfo_str:
                        evinfo_str += ','

                    if cid in (13, 14):
                        evinfo_str += '%s' % (v)

                    else:
                        evinfo_str += '"%s"' % (v)

                self.data_objs[self.rule_ids[0]].append(evinfo_str)

        if self.data_objs:
            return

        # ランダムにイベント情報生成
        data_objs_tmp = {}
        rset = list(DataObject.objects.filter(rule_type_id__in=self.rule_ids).order_by('rule_type_id', 'data_object_id').values('rule_type_id', 'conditional_expression_id'))
        for r in rset:
            rtype = r['rule_type_id']
            ceid  = r['conditional_expression_id']

            if rtype not in data_objs_tmp:
                data_objs_tmp[rtype] = []

            evinfo = self.get_evinfo(ceid)
            data_objs_tmp[rtype].append(evinfo)

        for k, data_list in data_objs_tmp.items():
            self.data_objs[k] = []
            evinfo_str = ''
            for v in data_list:
                if evinfo_str:
                    evinfo_str += ',' + v
                else:
                    evinfo_str = v

            self.data_objs[k].append(evinfo_str)


    def get_evinfo(self, ceid):

        val = None

        # 数値型
        if ceid in [1, 2, 5, 6, 7, 8]:  # 等しい、等しくない、超過、以上、未満、以下
            val = random.randint(0, 1000)
            val = '"%s"' % (val)

        # 文字列型
        elif ceid in [3, 4, 9, 10]:
            ranpass = RandomPassword()
            val = ranpass.get_password()
            val = '"%s"' % (val)

        # 文字列型(複数)
        elif ceid in [13, 14]:
            ranpass1 = RandomPassword()
            ranpass2 = RandomPassword()
            val = '["%s","%s"]' % (ranpass1.get_password(), ranpass2.get_password())

        # 時間
        elif ceid in [15]:
            h = random.randint(0, 23)
            m = random.randint(0, 59)
            val = '"%02d:%02d"' % (h, m)

        return val


