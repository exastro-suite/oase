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
  RabbitMQ接続処理

[引数]


[戻り値]


"""
import pika
from retry import retry
from libs.commonlibs.oase_logger import OaseLogger
from libs.commonlibs.rabbitmq import RabbitMQ

logger = OaseLogger.get_instance() # ロガー初期化

# 設定情報読み込み
_mq_settings = None

# RabbitMQ接続
_channel    = None
_connection = None
_properties = None


@retry(tries=3, delay=0.5)
def _produce(json_str):
    """
    [概要]
        RabbitMQへの接続
        retryデコレータにより、接続エラーが発生した場合はdelay秒間隔でtries回数、再接続を試みる
        tries回数試行しても繋がらなかった場合は呼び元のexceptに飛ぶ
    """
    try:
        global _channel
        global _connection
        global _mq_settings
        global _properties

        _channel.queue_bind(exchange='amq.direct', queue=_mq_settings['queuename'], routing_key=_mq_settings['queuename'])

        _channel.basic_publish(exchange='amq.direct',
            routing_key=_mq_settings['queuename'],
            body=json_str,
            properties=_properties)

    except pika.exceptions.AMQPConnectionError:
        _channel = None
        _rabbitMQ_conf()

        #continue
        raise Exception

    except Exception as e:
        raise


def _rabbitMQ_conf():
    """
    [概要]
        RabbitMQ接続に関しての設定を行う
    """
    global _channel
    global _connection
    global _mq_settings
    global _properties

    try:
        if _channel is None:
            # 設定情報読み込み
            _mq_settings = RabbitMQ.settings()

            # RabbitMQ接続
            _channel, _connection = RabbitMQ.connect(_mq_settings)

            # キューに接続
            _channel.queue_declare(queue=_mq_settings['queuename'], durable=True)

            _properties = pika.BasicProperties(
                content_type='application/json',
                content_encoding='utf-8',
                delivery_mode=2)

    except Exception as e:
        logger.system_log('LOSM13024', traceback.format_exc())
