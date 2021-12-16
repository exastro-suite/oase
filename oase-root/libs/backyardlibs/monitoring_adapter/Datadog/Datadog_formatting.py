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
  Datadogメッセージ整形処理

[引数]
  

[戻り値]
  
"""

import traceback
import datetime
import pytz
from datetime import datetime, timezone, timedelta

from django.conf import settings

from web_app.models.models import RuleType
from web_app.models.Datadog_monitoring_models import DatadogMatchInfo

from libs.commonlibs import define as defs
from libs.commonlibs.oase_logger import OaseLogger
logger = OaseLogger.get_instance()


################################################
# メッセージを整形する
################################################
def message_formatting(datadog_message, rule_type_id, datadog_adapter_id):
    """
    [メソッド概要]
      一括用に取得データを整形する
    """

    logger.logic_log(
        'LOSI00001', 'datadog_message: %s, rule_type_id: %s, datadog_adapter_id: %s' %
        (len(datadog_message), rule_type_id, datadog_adapter_id))

    result            = True
    form_data         = {}
    request_data_list = []
    ruletypename      = ''

    try:

        # データの有無確認
        if len(datadog_message) <= 0 or rule_type_id is None or datadog_adapter_id is None:
            logger.system_log('LOSM38021', 'Datadog', len(datadog_message), rule_type_id, datadog_adapter_id)
            result = False
            raise

        # ルール種別名称取得
        ruletypename = RuleType.objects.get(pk=rule_type_id, disuse_flag=str(defs.ENABLE)).rule_type_name

        # datadog_message内のresultをループ
        for data_dic in datadog_message:

            # データの不整合があった場合はそのデータを無視する
            if result == False:
                continue

            for i, d in enumerate(data_dic['evinfo']):
                if isinstance(d, str):
                    d = d.replace('\n', '\\n')
                    data_dic['evinfo'][i] = d

            request_data  = { 'decisiontable' : ruletypename,
                              'requesttype'   : '1',
                              'eventdatetime' : '',
                              'eventinfo'     : data_dic['evinfo'],
                            }

            # eventdatetimeの取得 lastchangeを2019/12/25 00:00:00の形式に変換する
            request_data['eventdatetime'] = datetime.fromtimestamp(
                int(data_dic['evtime']),
                pytz.timezone(getattr(settings, 'TIME_ZONE'))
            ).strftime("%Y/%m/%d %H:%M:%S")

            request_data_list.append(request_data)

        form_data['request'] = request_data_list

    except RuleType.DoesNotExist as e:
        result = False
        logger.system_log('LOSM38008', rule_type_id)
        logger.logic_log('LOSM00001', 'rule_type_id: %s, Traceback: %s' % (rule_type_id, traceback.format_exc()))

    except Exception as e:
        if result:
            result = False
            logger.system_log('LOSM38002')
            logger.logic_log('LOSM00001', 'e: %s, Traceback: %s' % (e, traceback.format_exc()))

    logger.logic_log('LOSI00002', 'result: %s' % (result))

    return result, form_data

