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
  イベントタイマー処理

[引数]
  HTTPリクエスト

[戻り値]
  HTTPレスポンス

"""


import traceback
import urllib

from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt

from libs.commonlibs.oase_logger import OaseLogger
from libs.webcommonlibs.event_timer import OASEEventTimer
from web_app.models.models import System


logger = OaseLogger.get_instance() # ロガー初期化
cls_event = OASEEventTimer.get_instance()
if cls_event:
    cls_event.initialize()


################################################
@csrf_exempt
def evtimer(request, ettype, config_id, query=''):
    """
    [メソッド概要]
      タイマー管理するイベントを管理する
    [引数]
      ettype      : イベント管理種別('cron' or 'timer')
      config_id : イベント管理するシステム設定ID
    """

    logger.logic_log('LOSI00001', 'ettype=%s, config_id=%s' % (ettype, config_id))

    result = False

    # イベントサーバーチェック
    if not cls_event:
        logger.logic_log('LOSM13017')
        return HttpResponse(status=404)

    # イベント管理種別チェック
    expect_types = ['cron', 'timer']
    if ettype not in expect_types:
        logger.user_log('LOSM13018', ettype, expect_types)
        return HttpResponse(status=404)

    try:
        month_list  = []
        day_list    = []
        hour_list   = []
        minute_list = []

        # AD連携タイマー
        if config_id == 'AD_LINKAGE_TIMER':

            value = urllib.parse.unquote(query)

            if value == 'None':
                value = None

            val = value if value is not None else ''
            if val:
                val_list = val.split('_')
                for v in val_list:
                    v = int(v.strip())
                    if v < 0 or v > 23:
                        continue

                    if v not in hour_list:
                        hour_list.append(v)
                        minute_list.append(0)

        # 予期せぬシステム設定値
        else:
            logger.user_log('LOSM13016', config_id)
            raise Exception()

        # cron設定
        if ettype == 'cron':
            result = cls_event.regist_cron(config_id, month_list, day_list, hour_list, minute_list)

        # タイマー登録
        elif ettype == 'timer':
            result = cls_event.regist_timer(config_id, hour_list, minute_list)

        if not result:
            logger.logic_log('LOSM13019', ettype, config_id)

    except Exception as e:
        logger.logic_log('LOSM00001', traceback.format_exc())
        result = False

    if not result:
        logger.logic_log('LOSI00002', 'error')
        return HttpResponse(status=400)

    logger.logic_log('LOSI00002', 'success')
    return HttpResponse(status=200)


