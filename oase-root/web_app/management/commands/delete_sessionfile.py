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
  セッションファイル削除コマンド

    削除対象の判定となるファイルのタイムスタンプは、
    サーバー設定のタイムゾーンに関わらず、UTCで判定する

[引数]


[戻り値]


"""




import os
import pytz
import time
import glob
import datetime
import traceback

from django.core.management.base import BaseCommand

from django.conf import settings


class Command(BaseCommand):

    help = 'セッションファイル削除コマンド'

    def add_arguments(self, parser):

        parser.add_argument('-e', '--expire', action='store', default=14, type=int, dest='expire', help='削除対象とするセッションファイル最終更新日時からの経過日数')


    def handle(self, *args, **options):

        try:
            self.now = datetime.datetime.now(pytz.timezone('UTC'))

            # パラメーター取得
            expire_day = options['expire']
            if expire_day < 0:
                expire_day = 0


            # 削除対象日時の設定
            self.delete_dt = self.now - datetime.timedelta(days=expire_day)


            # セッションエンジンの確認
            str_session_engine = getattr(settings, 'SESSION_ENGINE', 'None')
            if not str_session_engine.endswith('.file'):
                print('セッションエンジンがファイルではありません engine=%s' % (str_session_engine))
                return


            # セッションファイルパスの確認
            session_dir = getattr(settings, 'SESSION_FILE_PATH', None)
            if not session_dir:
                print('セッションファイルパスが設定されていません path=%s' % (session_dir))
                return

            if session_dir.endswith('/') == False:
                session_dir = '%s/' % (session_dir)


            # 削除前の確認
            msg = '最終更新日時から%s日経過しているセッションファイルを削除します。\nよろしいですか？ (y/n)\n' % (expire_day)
            if expire_day <= 0:
                msg = '全てのセッションファイルを削除します。\nログイン中のユーザーは切断されます。\nよろしいですか？ (y/n)\n'

            while True:
                choice = input(msg).lower()
                if choice in ['y', 'yes']:
                    break

                elif choice in ['n', 'no']:
                    return


            # セッションファイル取得
            session_files = glob.glob('%s*' % (session_dir))
            for sf in session_files:
                if not os.path.isfile(sf):
                    continue

                # ファイルの更新日時を取得
                updated_epoch = os.path.getmtime(sf)
                updated_dt = datetime.datetime.fromtimestamp(updated_epoch, datetime.timezone.utc)

                # 指定の日数経過しているファイルは削除
                if updated_dt < self.delete_dt:
                    os.remove(sf)
                    print('削除しました file=%s' % (os.path.split(sf)[1]))

        except Exception as e:
            print(e)


