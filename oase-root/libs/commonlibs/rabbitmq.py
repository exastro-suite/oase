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
    RabbitMQ共通処理クラス 格納
"""


import pika
from django.conf import settings
from web_app.models.models import System
from libs.commonlibs.aes_cipher import AESCipher

cipher = AESCipher(settings.AES_KEY)

class RabbitMQ:

    @classmethod
    def settings(cls):
        """
        [概要]
          RabbitMQ設定情報読み込みメソッド
        """
        settings = {}
        rset = list(System.objects.filter(category='RABBITMQ').values('config_id', 'value'))
        for r in rset:
            if r['config_id'] == 'MQ_USER_ID':
                settings['userid'] = r['value']
            if r['config_id'] == 'MQ_PASSWORD':
                settings['password'] = cipher.decrypt(r['value'])
            if r['config_id'] == 'MQ_IPADDRESS':
                settings['ipaddress'] = r['value']
            if r['config_id'] == 'MQ_QUEUE_NAME':
                settings['queuename'] = r['value']

        return settings


    @classmethod
    def connect(cls, settings):
        """
        [概要]
          RabbitMQ接続メソッド
        """
        # ユーザー名とパスワード
        credentials = pika.PlainCredentials(settings['userid'], settings['password'])

        # 接続パラメーター作成
        connect_param = pika.ConnectionParameters(
            host=settings['ipaddress'],
            credentials=credentials)

        # コネクション作成
        connection = pika.BlockingConnection(connect_param)
        channel    = connection.channel()

        return channel, connection

