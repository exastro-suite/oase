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
  ZABBIXメッセージ整形処理

[引数]
  HTTPリクエスト

[戻り値]
  HTTPレスポンス


"""


import traceback
import datetime
import pytz
from datetime import datetime, timezone, timedelta

from web_app.models.models import RuleType
from web_app.models.ZABBIX_monitoring_models import ZabbixMatchInfo

from libs.commonlibs.oase_logger import OaseLogger
logger = OaseLogger.get_instance()

################################################
# メッセージを整形する
################################################
def message_formatting(zabbix_message, rule_type_id, zabbix_adapter_id ):
    """
    [メソッド概要]
      一括用に取得データを整形する
    """

    logger.logic_log('LOSI00001', 'zabbix_message: %s, rule_type_id: %s, zabbix_adapter_id: %s' % (len(zabbix_message),rule_type_id,zabbix_adapter_id))

    result            = True
    form_data         = {}
    request_data_list = []
    ruletable         = ''

    try:

        # データの有無確認
        if len(zabbix_message) <= 0 or rule_type_id is None or zabbix_adapter_id is None:
            logger.system_log('LOSM25005', len(zabbix_message), rule_type_id, zabbix_adapter_id)
            result = False
            raise

        # ruletable名取得
        ruletable = RuleType.objects.get(pk=rule_type_id).rule_table_name

        # zabbix_response_key取得
        key_list = list(ZabbixMatchInfo.objects.filter(zabbix_adapter_id=zabbix_adapter_id).order_by('zabbix_match_id').values_list('zabbix_response_key',flat=True))
        
        # zabbix_message内のresultをループ
        for data_dic in zabbix_message:

            # データ整形
            eventinfo = []
            result = formatting_eventinfo(key_list, data_dic, eventinfo)
            
            # データの不整合があった場合はそのデータを無視する
            if result == False:
                continue

            request_data  = { 'ruletable'     : ruletable,
                              'requesttype'   : '1',
                              'eventdatetime' : '',
                              'eventinfo'     : '',
                            }

            request_data['eventinfo'] = eventinfo

            # eventdatetimeの取得 lastchangeを2019/12/25 00:00:00の形式に変換する
            request_data['eventdatetime'] = datetime.fromtimestamp(int(data_dic['lastchange']), pytz.timezone('Asia/Tokyo')).strftime("%Y/%m/%d %H:%M:%S")

            request_data_list.append(request_data)

        form_data['request'] = request_data_list

    except RuleType.DoesNotExist as e:
        result = False
        logger.system_log('LOSM25006', rule_type_id)
        logger.logic_log('LOSM00001', 'rule_type_id: %s, Traceback: %s' % (rule_type_id, traceback.format_exc()))


    except Exception as e:
        if result:
            result = False
            logger.system_log('LOSM25007')
            logger.logic_log('LOSM00001', 'e: %s, Traceback: %s' % (e, traceback.format_exc()))


    logger.logic_log('LOSI00002', 'result: %s' % (result))

    return result, form_data
    

################################################
# リクエスト用データへ整形
################################################
def formatting_eventinfo(key_list, data_dic, eventinfo):
    """
    [メソッド概要]
      リクエスト用にデータを整形する

    [引数]
      key_list  : 設定されているzabbix項目
      data_dic  : 取得してきたzabbixのメッセージ
      eventinfo : リクエスト用イベントデータ

    [戻り値]
      True : 整形成功
      False: 整形失敗
    """

    # リクエスト用データへ整形開始
    for zabbix_key in key_list:

        # ZABBIX項目名が存在したら配列に追加
        if zabbix_key in data_dic and data_dic[zabbix_key] != None:
            eventinfo.append(data_dic[zabbix_key])

    # zabbix_response_keyとeventinfoの数が合わなかったらデータ作成終了
    if len(key_list) != len(eventinfo):
        logger.system_log('LOSM25008', len(eventinfo), len(key_list))
        return False

    return True
    

