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
  アダプターの簡易インストーラー
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
from web_app.models.models import MonitoringType, AdapterType


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
            help='インストール対象のアダプタID(カンマ区切り)')
        parser.add_argument(
            '-u',
            '--uninst',
            action='store',
            default='',
            type=str,
            dest='uninsts',
            help='アンインストール対象のアダプタID(カンマ区切り)')
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

        self.adapter_ids_inst = []
        self.adapter_ids_uninst = []

        self.src_dir = ''
        self.dst_dir = ''

    def handle(self, *args, **options):

        self.adapter_ids_inst = self.ids_str_to_list(options['insts'])
        self.adapter_ids_uninst = self.ids_str_to_list(options['uninsts'])

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

        adp_master_inst = []
        adp_master_uninst = []

        if len(self.adapter_ids_inst) > 0:
            adp_master_inst = get_adapter_master(self.adapter_ids_inst)

        if len(self.adapter_ids_uninst) > 0:
            adp_master_uninst = get_adapter_master(self.adapter_ids_uninst)

        if len(adp_master_inst) <= 0 and len(adp_master_uninst) <= 0:
            adp_master = get_adapter_master()

            print('不正なアダプタIDが指定されています')
            print('')

            print('指定可能なアダプタID、および、その情報')
            if len(adp_master) > 0:
                print('  ID        アダプタ名      バージョン')

            else:
                print('  指定可能なアダプタIDが存在しません')
                print('  OASE_T_ADAPTER_TYPEにレコードが存在しません')

            for adp in adp_master:
                print('  {0:<8}  {1:<16}  {2:<8}'.format(adp['adapter_type_id'], adp['name'], adp['version']))

            print('')
            print('使い方')
            print('  python3 manage.py adapter_installer -i [インストール対象ID] -u [アンインストール対象ID]')
            print('')

            print('e.g.) アダプタIDが1の資材をインストール')
            print('  python3 manage.py adapter_installer -p /hoge/dir -i 1')
            print('')
            print('e.g.) アダプタIDが1の資材をアンインストール')
            print('  python3 manage.py adapter_installer -p /hoge/dir -u 1')
            print('')

            return

        for adp in adp_master_inst:
            adp_info = InstallAdapterInfo(
                adp['adapter_type_id'],
                adp['name'],
                adp['version'],
                adp['adapter_major_version'],
                self.src_dir,
                self.dst_dir,
                self.now)
            adp_info.install()

        for adp in adp_master_uninst:
            adp_info = InstallAdapterInfo(
                adp['adapter_type_id'],
                adp['name'],
                adp['version'],
                adp['adapter_major_version'],
                self.src_dir,
                self.dst_dir,
                self.now)
            adp_info.uninstall()


class InstallAdapterInfo():

    # インストール資材のパスとファイル名
    PLUGIN_FILES = [
        ['backyards/monitoring_adapter/', '%s_monitoring.py'],
        ['backyards/monitoring_adapter/', '%s_monitoring_sub.py'],
        ['backyards/monitoring_adapter/', 'oase-%s-monitoring.service'],
        ['libs/backyardlibs/monitoring_adapter/%s/', '%s_api.py'],
        ['libs/backyardlibs/monitoring_adapter/%s/', '%s_request.py'],
        ['libs/backyardlibs/monitoring_adapter/%s/', '%s_formatting.py'],
        ['libs/backyardlibs/monitoring_adapter/%s/', 'manage_trigger.py'],
        ['confs/backyardconfs/services/', '%s_monitoring_env'],
        ['web_app/models/', '%s_monitoring_models.py'],
        ['web_app/templates/system/%s/', 'monitoring_%s.html'],
        ['web_app/views/system/monitoring_%s/', 'monitoring_%s.py'],
    ]

    ZABBIX_CONF_PATH = 'confs/backyardconfs/services/'
    ZABBIX_CONF_FILE = 'ZABBIX_monitoring_env'
    ZABBIX_SERVICE_PATH = 'backyards/monitoring_adapter/'
    ZABBIX_SERVICE_FILE = 'oase-ZABBIX-monitoring.service'
    SYSCONFIG_PATH = '/etc/sysconfig/'
    SYSTEMD_PATH = '/usr/lib/systemd/system/'

    def __init__(self, id, name, ver, mver, src_path, dst_path, now=None):

        self.now = now
        if not now:
            self.now = datetime.datetime.now(pytz.timezone('UTC'))

        self.adapter_id = id
        self.adapter_name = name
        self.adapter_version = ver
        self.adapter_major = mver

        self.src_root_path = src_path
        self.dst_root_path = dst_path

        self.config = None
        self.load_config()

    def load_config(self):

        config_filepath = '%s%s/%s.conf' % (self.src_root_path, self.adapter_name, self.adapter_name)
        if not os.path.exists(config_filepath):
            print('コンフィグファイルが存在しません config=%s' % (config_filepath))
            return

        self.config = configparser.ConfigParser()
        self.config.read(config_filepath)

    def install(self):

        # 資材のコピー
        for plugins in self.PLUGIN_FILES:
            plugin_dir = plugins[0] if plugins[0].find('%s') < 0 else plugins[0] % (self.adapter_name)
            plugin_file = plugins[1] if plugins[1].find('%s') < 0 else plugins[1] % (self.adapter_name)

            dst_path = '%s%s' % (self.dst_root_path, plugin_dir)
            if not os.path.exists(dst_path):
                os.makedirs(dst_path, exist_ok=True)

            src_filepath = '%s%s/%s' % (self.src_root_path, self.adapter_name, plugin_file)
            dst_filepath = '%s%s' % (dst_path, plugin_file)

            if not os.path.exists(src_filepath):
                print('コピー元ファイルが存在しません src=%s' % (src_filepath))
                continue

            shutil.copy(src_filepath, dst_filepath)

        # インストール資材の読込
        subprocess.call(["systemctl", "reload", "uwsgi.service"])

        # テーブル作成
        if self.config:
            icnt = 1
            while True:
                sec_key = 'models'
                opt_sql_key = 'query%s' % (icnt)

                if not self.config.has_section(sec_key):
                    break

                if not self.config.has_option(sec_key, opt_sql_key):
                    break

                query = self.config.get(sec_key, opt_sql_key)
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    cursor.close()

                icnt += 1

        # レコード挿入/更新
        rcnt = MonitoringType.objects.filter(adapter_type_id=self.adapter_id).count()
        if rcnt > 0:
            MonitoringType.objects.filter(adapter_type_id=self.adapter_id).update(disuse_flag=str(defs.ENABLE))

        else:
            MonitoringType(
                adapter_type_id=self.adapter_id,
                disuse_flag=str(defs.ENABLE),
                last_update_timestamp=self.now,
                last_update_user='システム管理者'
            ).save(force_insert=True)

        # サービス起動
        if self.adapter_name == 'ZABBIX':
            # シンボリックリンクパス作成
            conf_src = '%s%s%s' % (self.dst_root_path, self.ZABBIX_CONF_PATH, self.ZABBIX_CONF_FILE)
            conf_dst = '%s%s' % (self.SYSCONFIG_PATH, self.ZABBIX_CONF_FILE)

            # シンボリックリンク作成
            os.symlink(conf_src, conf_dst)

            # サービスファイルパス作成
            service_src = '%s%s%s' % (self.dst_root_path, self.ZABBIX_SERVICE_PATH, self.ZABBIX_SERVICE_FILE)
            service_dst = '%s%s' % (self.SYSTEMD_PATH, self.ZABBIX_SERVICE_FILE)

            # サービスファイル格納
            shutil.copy(service_src, service_dst)

            # daemon-reload実行
            subprocess.call(["systemctl", "daemon-reload"])

            # サービス起動
            subprocess.call(["systemctl", "start", self.ZABBIX_SERVICE_FILE])

            # サービス自動起動有効
            subprocess.call(["systemctl", "enable", self.ZABBIX_SERVICE_FILE])

    def uninstall(self):

        # レコード更新
        MonitoringType.objects.filter(adapter_type_id=self.adapter_id).update(disuse_flag=str(defs.DISABLE))

        # 資材の削除
        for plugins in self.PLUGIN_FILES:
            plugin_dir = plugins[0] if plugins[0].find('%s') < 0 else plugins[0] % (self.adapter_name)
            plugin_file = plugins[1] if plugins[1].find('%s') < 0 else plugins[1] % (self.adapter_name)

            dst_path = '%s%s' % (self.dst_root_path, plugin_dir)
            dst_filepath = '%s%s' % (dst_path, plugin_file)

            if os.path.exists(plugin_dir):
                os.remove(dst_filepath)
                if self.adapter_name in plugin_dir:
                    shutil.rmtree(plugin_dir)

        # テーブル作成
        if self.config:
            icnt = 1
            while True:
                sec_key = 'del_models'
                opt_sql_key = 'query%s' % (icnt)

                if not self.config.has_section(sec_key):
                    break

                if not self.config.has_option(sec_key, opt_sql_key):
                    break

                query = self.config.get(sec_key, opt_sql_key)
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    cursor.close()

                icnt += 1

        # インストール資材の読込
        subprocess.call(["systemctl", "reload", "uwsgi.service"])

        # サービス停止
        if self.adapter_name == 'ZABBIX':

            # サービス自動起動無効
            subprocess.call(["systemctl", "enable", self.ZABBIX_SERVICE_FILE])

            # サービス停止
            subprocess.call(["systemctl", "stop", self.ZABBIX_SERVICE_FILE])

            # サービスファイル削除
            service_dst = '%s%s' % (self.SYSTEMD_PATH, self.ZABBIX_SERVICE_FILE)
            os.remove(service_dst)

            # confファイル削除
            conf_dst = '%s%s' % (self.SYSCONFIG_PATH, self.ZABBIX_CONF_FILE)
            os.remove(conf_dst)


def get_adapter_master(ids=[]):

    rset = AdapterType.objects.all()

    if len(ids) > 0:
        rset = rset.filter(adapter_type_id__in=ids)

    rset = rset.values('adapter_type_id', 'name', 'version', 'adapter_major_version')

    return rset
