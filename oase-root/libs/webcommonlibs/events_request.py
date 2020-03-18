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
  イベントリクエスト関連処理

[引数]


[戻り値]


"""




import uuid
import pytz
import datetime

from libs.commonlibs.oase_logger import OaseLogger


logger = OaseLogger.get_instance() # ロガー初期化


class EventsRequestCommon():
    """
    [クラス概要]
      イベントリクエスト関連の処理をまとめる
    """

    ############################################
    # 定数
    ############################################
    # キー名
    KEY_RULETYPE  = 'ruletable'
    KEY_REQTYPE   = 'requesttype'
    KEY_EVENTTIME = 'eventdatetime'
    KEY_EVENTINFO = 'eventinfo'
    KEY_TRACEID   = 'traceid'

    # リクエストの状態
    REQUEST_OK                = 0  # 正常
    REQUEST_ERR_RULETYPE_KEY  = 1  # キーエラー(ルール種別)
    REQUEST_ERR_REQTYPE_KEY   = 2  # キーエラー(リクエスト種別)
    REQUEST_ERR_DATETIME_KEY  = 3  # キーエラー(イベント発生日時)
    REQUEST_ERR_EVINFO_KEY    = 4  # キーエラー(イベント情報)
    REQUEST_ERR_EVINFO_TYPE   = 5  # イベント情報形式不正
    REQUEST_ERR_EVINFO_LENGTH = 6  # イベント情報数不正


    ############################################
    # メソッド
    ############################################
    @staticmethod
    def generate_trace_id(now=None):
        """
        [メソッド概要]
          トレースIDを生成する
        """

        # トレースID接頭辞
        prefix = 'TOS'

        # トレースID生成日時
        if not now:
            now = datetime.datetime.now(pytz.timezone('UTC'))

        # UUID(v4)生成
        u4 = str(uuid.uuid4())
        u4 = u4.replace('-', '')

        # トレースID生成
        trace_id = '%s%s%s' % ('TOS', now.strftime('%Y%m%d%H%M%S%f'), u4)

        return trace_id


    @classmethod
    def check_events_request_key(cls, req):
        """
        [メソッド概要]
          リクエストのキーをチェックする
        """

        # 必須キーの存在チェック
        if cls.KEY_RULETYPE not in req:
            return cls.REQUEST_ERR_RULETYPE_KEY

        if cls.KEY_REQTYPE not in req:
            return cls.REQUEST_ERR_REQTYPE_KEY

        if cls.KEY_EVENTTIME not in req:
            return cls.REQUEST_ERR_DATETIME_KEY

        if cls.KEY_EVENTINFO not in req:
            return cls.REQUEST_ERR_EVINFO_KEY

        return cls.REQUEST_OK


    @classmethod
    def check_events_request_len(cls, req, evinfo_len):
        """
        [メソッド概要]
          リクエストのキーをチェックする
        """

        # イベント情報の形式、長さチェック
        if evinfo_len <= 0:
            return cls.REQUEST_ERR_EVINFO_LENGTH

        else:
            if isinstance(req[cls.KEY_EVENTINFO], list) == False:
                return cls.REQUEST_ERR_EVINFO_TYPE

            if len(req[cls.KEY_EVENTINFO]) != evinfo_len:
                return cls.REQUEST_ERR_EVINFO_LENGTH

        return cls.REQUEST_OK


