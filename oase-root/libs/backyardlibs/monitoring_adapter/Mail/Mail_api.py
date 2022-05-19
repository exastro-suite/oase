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
Mail apiを使って現在受信している新規メールを取得する。


"""
import json
import urllib
import requests 
import os
import sys
import hashlib
import pprint
import django
import traceback
import base64
import ssl

from imapclient import IMAPClient

# import検索パス追加
my_path = os.path.dirname(os.path.abspath(__file__))
tmp_path = my_path.split('oase-root')
root_dir_path = tmp_path[0] + 'oase-root'
sys.path.append(root_dir_path)

# OASE モジュール import
# #LOCAL_PATCH#
os.environ['DJANGO_SETTINGS_MODULE'] = 'confs.frameworkconfs.settings'
django.setup()

from django.conf                 import settings
from libs.commonlibs.oase_logger import OaseLogger
from libs.commonlibs.aes_cipher  import AESCipher
from web_app.models.Mail_monitoring_models import MailAdapter

logger = OaseLogger.get_instance() # ロガー初期化

class MailApi(object):

    def __init__(self, request_rec):
        """
        Mail API インスタンスを返す
        [引数]
          request_rec: 対象Mail監視マスタレコード
        """

        self.imap_server = None


        cipher = AESCipher(settings.AES_KEY)
        pw = cipher.decrypt(request_rec.password)


        # SSL/TLS 設定
        ssl_flag = False
        ssl_context = None
        if request_rec.encryption_protocol > 0:
            ssl_flag = True
            ssl_context = ssl.create_default_context()


        self.imap_server = IMAPClient(request_rec.imap_server, port=request_rec.port, ssl=ssl_flag, ssl_context=ssl_context)
        self.imap_server.login(request_rec.user, pw)


    def __del__(self):
        """
        デストラクタ
        """

        self.logout()


    def get_active_triggers(self, last_change_since, now=None):
        """
        現在発生している障害を全て取得する。
        発生しているhostidとhost名も要求する。
        [戻り値]
        result: 発生中の障害情報
        """

        response = []

        try:
            select_info = self.imap_server.select_folder('INBOX')
            msg = self.imap_server.search(['SINCE', last_change_since])
            dic = self.imap_server.fetch(msg, ['ENVELOPE', 'RFC822.HEADER', 'RFC822.TEXT'])
            for mid, d in dic.items():
                e = d[b'ENVELOPE']
                h = d[b'RFC822.HEADER']
                b = d[b'RFC822.TEXT']

                ef = e.from_[0] if isinstance(e.from_, tuple) and len(e.from_) > 0 else None
                et = e.to[0]    if isinstance(e.to,    tuple) and len(e.to)    > 0 else None

                info = {}
                info['message_id']    = e.message_id.decode()
                info['envelope_from'] = '%s@%s' % (ef.mailbox.decode(), ef.host.decode()) if ef else ''
                info['envelope_to']   = '%s@%s' % (et.mailbox.decode(), et.host.decode()) if et else ''
                info['header_from']   = self._parser(h.decode(), 'Return-Path: ')
                info['header_to']     = self._parser(h.decode(), 'Delivered-To: ')
                info['mailaddr_from'] = self._parser(h.decode(), 'From: ')
                info['mailaddr_to']   = self._parser(h.decode(), 'To: ')
                info['date']          = e.date.strftime('%Y-%m-%d %H:%M:%S')
                info['lastchange']    = e.date.timestamp()
                info['subject']       = e.subject.decode() if e.subject else ''
                info['body']          = b.decode()

                response.append(info)

        except Exception as e:
            raise

        logger.logic_log('LOSI41002', len(response))

        return response


    def logout(self):
        """
        ログアウトを行う。
        成功した場合レスポンスの'result'キーの値がTrueになる。
        [戻り値]
        bool
        """

        if self.imap_server:
            self.imap_server.logout()
            self.imap_server = None


    def _parser(self, header_text, key):

        val = ''

        text_list = header_text.split('\r\n')
        for t in text_list:
            if t.startswith(key):
                val = t[len(key):]
                break

        return val


