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
ItaParameterMatchInfoテーブルにデータを挿入するコマンド
"""

import pytz
import datetime
from importlib import import_module

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    """
    ItaParameterMatchInfoテーブルに対してレコードを操作する簡易コマンド
    """

    help = 'ItaParameterMatchInfoテーブルにレコードを追加します'

    def add_arguments(self, parser):
        """コマンドライン引数を設定"""

        parser.add_argument(
            'values',
            nargs='+',
            type=str,
            help='必須データを指定します')

    def handle(self, *args, **options):
        """コマンド実行時の処理"""

        values = options['values']
        if len(values) != 7:
            print('[ERROR] 引数が不正です。 引数は7個必要です。')
            return

        self.insert(values)

    def insert(self, values):
        """
        ItaParameterMatchInfoテーブルに値がvaluesのレコードを追加する。
        values: list
        """
        try:
            with transaction.atomic():
                module = import_module('web_app.models.ITA_models')
                ItaParameterMatchInfo = getattr(module, 'ItaParameterMatchInfo')
                ItaParameterMatchInfo(
                    menu_group_id=values[0],
                    menu_id=values[1],
                    parameter_name=values[2],
                    order=values[3],
                    conditional_name=values[4],
                    extraction_method1=values[5],
                    extraction_method2=values[6],
                    last_update_timestamp=datetime.datetime.now(pytz.timezone('UTC')),
                    last_update_user='administrator',
                ).save()
        except ModuleNotFoundError:
            print('[ERROR] ITAドライバがインストールされていません。ITAドライバをインストールしてください。')
        except Exception as e:
            print('[ERROR] ', e)
            print('[usage]')
            print('    python3 manage.py insert_ita_parameter_match_info <menu_group_id>, <menu_id>,\
<parameter_name>, <order>, <conditional_name>, <extraction_method1>, <extraction_method2>')
