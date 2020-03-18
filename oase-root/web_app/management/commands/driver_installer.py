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
  ドライバーの簡易インストーラー
"""

import os
import pytz
import datetime
import shutil
import configparser
import subprocess
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from libs.commonlibs import define as defs
from web_app.models.models import ActionType, DriverType


class Command(BaseCommand):

    help = '簡易インストーラー(動作確認用)'

    def add_arguments(self, parser):

        parser.add_argument(
            '-i',
            '--inst',
            action='store',
            default='',
            type=str,
            dest='insts',
            help='インストール対象のドライバーID(カンマ区切り)')
        parser.add_argument(
            '-u',
            '--uninst',
            action='store',
            default='',
            type=str,
            dest='uninsts',
            help='アンインストール対象のドライバーID(カンマ区切り)')
        parser.add_argument(
            '-p',
            '--path',
            action='store',
            default='',
            type=str,
            dest='srcpath',
            help='インストール資材のコピー元ルートパス',
            required=True)

    def __init__(self):

        self.now = datetime.datetime.now(pytz.timezone('UTC'))

        self.driver_ids_inst = []
        self.driver_ids_uninst = []

        self.src_dir = ''
        self.dst_dir = ''

    def handle(self, *args, **options):

        self.driver_ids_inst = self.ids_str_to_list(options['insts'])
        self.driver_ids_uninst = self.ids_str_to_list(options['uninsts'])

        self.src_dir = options['srcpath']
        self.dst_dir = settings.BASE_DIR

        if not self.src_dir.endswith('/'):
            self.src_dir = '%s/' % (self.src_dir)

        if not self.dst_dir.endswith('/'):
            self.dst_dir = '%s/' % (self.dst_dir)

        self.installer_main()

    def ids_str_to_list(self, str_ids):

        ids_list = []

        if str_ids and isinstance(str_ids, str):
            tmp_list = str_ids.split(',')
            for tmp in tmp_list:
                try:
                    id = int(tmp.strip())
                    ids_list.append(id)
                except Exception:
                    pass

        return ids_list

    def installer_main(self):

        if not os.path.exists(self.src_dir):
            print(self.dst_dir)
            print('指定のディレクトリが存在しません')
            return

        drv_master_inst = []
        drv_master_uninst = []

        if len(self.driver_ids_inst) > 0:
            drv_master_inst = get_driver_master(self.driver_ids_inst)

        if len(self.driver_ids_uninst) > 0:
            drv_master_uninst = get_driver_master(self.driver_ids_uninst)

        if len(drv_master_inst) <= 0 and len(drv_master_uninst) <= 0:
            drv_master = get_driver_master()

            print('使い方')
            print('  python3 manage.py driver_installer -i [インストール対象ID] -u [アンインストール対象ID]')
            print('')

            print('e.g.) ドライバーIDが1と2の資材をインストール')
            print('  python3 manage.py driver_installer -p /hoge/dir -i 1,2')
            print('')
            print('e.g.) ドライバーIDが1の資材をインストール、2の資材をアンインストール')
            print('  python3 manage.py driver_installer -p /hoge/dir -i 1 -u 2')
            print('')

            print('指定可能なドライバーID、および、その情報')
            if len(drv_master) > 0:
                print('  ID        ドライバー名      バージョン')

            else:
                print('  指定可能なドライバーIDが存在しません')
                print('  OASE_T_DRIVER_TYPEにレコードが存在しません')

            for drv in drv_master:
                print('  {0:<8}  {1:<16}  {2:<8}'.format(drv['driver_type_id'], drv['name'], drv['version']))

            return

        for drv in drv_master_inst:
            drv_info = InstallDriverInfo(
                drv['driver_type_id'],
                drv['name'],
                drv['version'],
                drv['driver_major_version'],
                self.src_dir,
                self.dst_dir,
                self.now)
            drv_info.install()

        for drv in drv_master_uninst:
            drv_info = InstallDriverInfo(
                drv['driver_type_id'],
                drv['name'],
                drv['version'],
                drv['driver_major_version'],
                self.src_dir,
                self.dst_dir,
                self.now)
            drv_info.uninstall()


class InstallDriverInfo():

    # インストール資材のパスとファイル名
    PLUGIN_FILES = [
        ['libs/backyardlibs/action_driver/%s/', '%s_driver.py'],
        ['libs/backyardlibs/action_driver/%s/', '%s_core.py'],
        ['libs/commonlibs/%s/', '%s_common.py'],
        ['web_app/models/', '%s_models.py'],
        ['web_app/templates/system/%s/', 'action_%s.html'],
        ['web_app/views/system/%s/', 'action_%s.py'],
    ]

    # インポート修正対象ファイルパス
    MODIFY_IMPORT_FILES = [
        'web_app/views/system/urls.py',
    ]

    # urls修正対象ファイルパス
    MODIFY_URLS_FILES = [
        'web_app/views/system/urls.py',
    ]

    # モデル名
    TARGET_MODEL_NAMES = []

    def __init__(self, id, name, ver, mver, src_path, dst_path, now=None):

        self.now = now
        if not now:
            self.now = datetime.datetime.now(pytz.timezone('UTC'))

        self.driver_id = id
        self.driver_name = name
        self.driver_version = ver
        self.driver_major = mver

        self.src_root_path = src_path
        self.dst_root_path = dst_path

        self.config = None
        self.load_config()

    def load_config(self):

        config_filepath = '%s%s/%s.conf' % (self.src_root_path, self.driver_name, self.driver_name)
        if not os.path.exists(config_filepath):
            print('コンフィグファイルが存在しません config=%s' % (config_filepath))
            return

        self.config = configparser.ConfigParser()
        self.config.read(config_filepath)

    def copy_files(self):
        """
        資材のコピー
        """
        for plugins in self.PLUGIN_FILES:
            plugin_dir = plugins[0] if plugins[0].find('%s') < 0 else plugins[0] % (self.driver_name)
            plugin_file = plugins[1] if plugins[1].find('%s') < 0 else plugins[1] % (self.driver_name)

            dst_path = '%s%s' % (self.dst_root_path, plugin_dir)
            os.makedirs(dst_path, exist_ok=True)

            src_filepath = '%s%s/%s' % (self.src_root_path, self.driver_name, plugin_file)
            dst_filepath = '%s%s' % (dst_path, plugin_file)

            if not os.path.exists(src_filepath):
                print('コピー元ファイルが存在しません src=%s' % (src_filepath))
                continue

            shutil.copy(src_filepath, dst_filepath)

    def install(self):
        """
        インストールを実行
        """
        self.copy_files()
        # インストール資材の読込
        subprocess.call(["systemctl", "reload", "uwsgi.service"])

        # テーブル作成
        if self.config:
            icnt = 1
            while True:
                sec_key = 'models'
                opt_sql_key = 'query%s' % (icnt)

                if not self.config.has_section(sec_key) or not self.config.has_option(sec_key, opt_sql_key):
                    break

                query = self.config.get(sec_key, opt_sql_key)
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    cursor.close()

                icnt += 1

        # レコード挿入/更新
        rcnt = ActionType.objects.filter(driver_type_id=self.driver_id).count()
        if rcnt > 0:
            ActionType.objects.filter(driver_type_id=self.driver_id).update(disuse_flag=str(defs.ENABLE))

        else:
            ActionType(
                driver_type_id=self.driver_id,
                disuse_flag=str(defs.ENABLE),
                last_update_timestamp=self.now,
                last_update_user='システム管理者',
            ).save(force_insert=True)

    def uninstall(self):
        """
        アンインストールを実行
        """

        # レコード更新
        ActionType.objects.filter(driver_type_id=self.driver_id).update(disuse_flag=str(defs.DISABLE))

        # 資材の削除
        for plugins in self.PLUGIN_FILES:
            plugin_dir = plugins[0] if plugins[0].find('%s') < 0 else plugins[0] % (self.driver_name)
            plugin_file = plugins[1] if plugins[1].find('%s') < 0 else plugins[1] % (self.driver_name)

            dst_path = '%s%s' % (self.dst_root_path, plugin_dir)
            dst_filepath = '%s%s' % (dst_path, plugin_file)

            if os.path.exists(plugin_dir):
                os.remove(dst_filepath)
                if self.driver_name in plugin_dir:
                    shutil.rmtree(plugin_dir)

        # インストール資材の読込
        subprocess.call(["systemctl", "reload", "uwsgi.service"])


def get_driver_master(ids=[]):

    rset = DriverType.objects.all()

    if len(ids) > 0:
        rset = rset.filter(driver_type_id__in=ids)

    rset = rset.values('driver_type_id', 'name', 'version', 'driver_major_version')

    return rset
