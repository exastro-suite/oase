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
  イベントリクエスト用のトークンを管理する

[引数]


[戻り値]


"""


import pytz
import datetime

from django.conf import settings

from web_app.templatetags.common import get_message
from libs.commonlibs import define as defs
from libs.commonlibs.oase_logger import OaseLogger


logger = OaseLogger.get_instance() # ロガー初期化


################################################################
# クラス
################################################################
# トークン管理クラス
class OASEEventToken(object):

    """
    [クラス概要]
      トークン管理クラス
    """

    _instance = None


    ############################################
    # 定数
    ############################################
    # トークンチェック結果
    STS_OK         = 0  # 正常
    STS_NOTOKEN    = 1  # トークンなし
    STS_INVALID    = 2  # 無効なトークン
    STS_PERMISSION = 3  # 権限なし

    # ステータス別メッセージID
    MSGID_NOTOKEN    = "MOSJA40001"
    MSGID_INVALID    = "MOSJA40002"
    MSGID_PERMISSION = "MOSJA40003"


    ############################################
    # メソッド
    ############################################
    def __new__(cls):

        raise Exception('既にインスタンスが生成されています')


    @classmethod
    def __internal_new__(cls):

        return super().__new__(cls)


    @classmethod
    def get_instance(cls):
        """
        [メソッド概要]
          シングルトンのインスタンス生成処理
        """

        # インスタンス生成
        if not cls._instance:
            cls._instance = cls.__internal_new__()

        return cls._instance


    def initialize(self):
        """
        [メソッド概要]
          初期化処理
        """

        self.token_info    = {}
        self.group_info    = {}


    def check_request_token(self, request, rule_name, req_type):
        """
        [メソッド概要]
          tokenチェック
        [引数]
          request : HTTPリクエスト
        [戻り値]
          stscode : int : HTTPステータスコード
          message : str : エラー理由
        """

        stscode = 200
        message = ""

        tkn = request.META.get('HTTP_AUTHORIZATION', None)
        sts = self.check_token(tkn, rule_name, req_type)
        if sts == self.STS_NOTOKEN:
            stscode = 401
            message = get_message(self.MSGID_NOTOKEN, 'JA')

        elif sts == self.STS_INVALID:
            stscode = 401
            message = get_message(self.MSGID_INVALID, 'JA')

        elif sts == self.STS_PERMISSION:
            stscode = 403
            message = get_message(self.MSGID_PERMISSION, 'JA')

        return  stscode, message


    def check_token(self, token, rule_name, req_type):
        """
        [メソッド概要]
          tokenチェック
        [引数]
          token : トークン
        [戻り値]
          int   : STS_OK         = 0  # 正常
                  STS_NOTOKEN    = 1  # トークンなし
                  STS_INVALID    = 2  # 無効なトークン
                  STS_PERMISSION = 3  # 権限なし
        """

        # リクエストにトークンがなければ異常
        if token is None:
            return self.STS_NOTOKEN

        # 登録されていないトークンは無効
        if token not in self.token_info:
            return self.STS_INVALID

        # トークンの有効期間外は無効
        now = datetime.datetime.now(pytz.timezone('UTC'))
        if (self.token_info[token]['period_from'] and now <  self.token_info[token]['period_from']) \
        or (self.token_info[token]['period_to']   and now >= self.token_info[token]['period_to']):
            return self.STS_INVALID

        # ルールに対する権限がなければ禁止
        perm = defs.NO_AUTHORIZATION
        for gr in self.token_info[token]['group_list']:
            if gr in self.group_info and rule_name in self.group_info[gr][req_type]:
                perm = defs.ALLOWED_MENTENANCE
                break

        if perm != defs.ALLOWED_MENTENANCE:
            return self.STS_PERMISSION


        return self.STS_OK


