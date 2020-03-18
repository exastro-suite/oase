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
OASE共通定数

"""

#-------------------
# DISUSE_FLAG
#-------------------
ENABLE              = 0   # 有効
DISABLE             = 1   # 無効

#-------------------
# PERMISSION_TYPE_ID
#-------------------
ALLOWED_MENTENANCE  = 1   # メンテナンス可
VIEW_ONLY           = 2   # 閲覧のみ
NO_AUTHORIZATION    = 3   # 権限なし

#-------------------
# REQUEST_TYPE_ID
#-------------------
PRODUCTION          = 1   #プロダクション
STAGING             = 2   #ステージング

#-------------------
# STATUS
#-------------------
# 共通
UNPROCESS           = 1   # 未処理
PROCESSING          = 2   # 処理中(データを取得開始)
PROCESSED           = 3   # 処理済み(正常終了)
FORCE_PROCESSED     = 4   # 強制処理済み
SERVER_ERROR        = 5   # 異常終了(サーバーエラー)
PENDING             = 6   # 処理保留
NO_DRIVER           = 7   # 不明なドライバー
STOP                = 8   # 停止
PREVENT             = 9   # 抑止済
WAITING             = 10  # 待機

# リクエスト管理のステータス
RULE_UNMATCH        = 1000  # 処理済み(ルール未検出)
RULE_ERROR          = 1001  # 処理済み(ルール実行エラー)
RULE_MATCH          = 1002
# ルールマッチング結果管理
BREAK_ACTION        = 2001  # アクション中断
ACTION_DATA_ERROR   = 2002    # アクション実行前エラー　ルールマッチング結果詳細情報エラーなど
ACTION_EXEC_ERROR   = 2003    # アクション実行エラー


#-------------------
# ACTION_STATUS
#-------------------
ACTION_STATUS = {
        1      : 'MOSJA13064',
        2      : 'MOSJA13065',
        3      : 'MOSJA13066',
        4      : 'MOSJA13067',
        5      : 'MOSJA13068',
        1000   : 'MOSJA13069',
        1001   : 'MOSJA13070',
        1002   : 'MOSJA13071',
        2001   : 'MOSJA13072',
        2002   : 'MOSJA13073',
        2003   : 'MOSJA13063',
}


#-------------------
# ACTION_HISTORY_STATUS
#-------------------
class ACTION_HISTORY_STATUS():

    ############################################
    # 状態コード
    ############################################
    # 共通ステータス
    PROCESSING = PROCESSING
    PROCESSED  = PROCESSED
    PENDING    = PENDING
    NO_DRIVER  = NO_DRIVER
    STOP       = STOP
    PREVENT    = PREVENT
    WAITING    = WAITING

    # アクション固有ステータス
    BREAK_ACTION      = BREAK_ACTION
    ACTION_DATA_ERROR = ACTION_DATA_ERROR
    ACTION_EXEC_ERROR = ACTION_EXEC_ERROR
    ACTION_EXEC_ERROR_HOLD = 2004
    EXASTRO_REQUEST   = 2005
    RETRY             = 2007

    # ITAアクション固有ステータス
    ITA_UNPROCESS  = 2101  # 未実行
    ITA_PROCESSING = 2102  # 実行中
    ITA_ERROR      = 2103  # 異常
    ITA_CANCEL     = 2104  # 取消
    ITA_FAIL       = 2105  # 状態取得失敗
    ITA_REGISTERING_SUBSTITUTION_VALUE = 2106  # 代入値管理登録中

    STATUS_DESCRIPTION = {
        UNPROCESS        : 'MOSJA13064',
        PROCESSING       : 'MOSJA13065',
        PROCESSED        : 'MOSJA13066',
        FORCE_PROCESSED  : 'MOSJA13067',
        SERVER_ERROR     : 'MOSJA13068',
        PENDING          : 'MOSJA13056',
        STOP             : 'MOSJA13057',
        EXASTRO_REQUEST  : 'MOSJA13074',
        RETRY            : 'MOSJA13075',
        BREAK_ACTION     : 'MOSJA13072',
        ACTION_DATA_ERROR: 'MOSJA13073',
        ACTION_EXEC_ERROR: 'MOSJA13063',
        ITA_UNPROCESS    : 'MOSJA13076',
        ITA_PROCESSING   : 'MOSJA13077',
        ITA_ERROR        : 'MOSJA13078',
        ITA_CANCEL       : 'MOSJA13079',
        ITA_FAIL         : 'MOSJA13080',
        PREVENT          : 'MOSJA13081',
        ITA_REGISTERING_SUBSTITUTION_VALUE : 'MOSJA13081',
    }

    DISABLE_RETRY_LIST = [
        PROCESSING, PROCESSED, PENDING, NO_DRIVER, STOP,
        BREAK_ACTION, ACTION_EXEC_ERROR_HOLD, EXASTRO_REQUEST, RETRY, PREVENT,
        ITA_UNPROCESS, ITA_PROCESSING, ITA_CANCEL, ITA_REGISTERING_SUBSTITUTION_VALUE
    ]

    EXASTRO_CHECK_LIST = [
        EXASTRO_REQUEST,
        ITA_UNPROCESS,
        ITA_PROCESSING,
    ]
    EXASTRO_REGIST_LIST = [
        ITA_REGISTERING_SUBSTITUTION_VALUE,
    ]

    ICON_INFO = {
        PROCESSING:{
                  'status':'running',
                  'name':'owf-gear',
                  'description':'MOSJA13053'
        },
        PROCESSED:{
                  'status':'complete',
                  'name':'owf-check',
                  'description':'MOSJA13054'
        },
        FORCE_PROCESSED:{
                  'status':'error',
                  'name':'owf-cross',
                  'description':'MOSJA13055'
        },
        PENDING:{
                  'status':'attention',
                  'name':'owf-stop',
                  'description':'MOSJA13056'
        },
        STOP:{
                  'status':'addressed',
                  'name':'owf-square',
                  'description':'MOSJA13057'
        },   
        EXASTRO_REQUEST:{
                  'status':'running',
                  'name':'owf-gear',
                  'description':'MOSJA13058'
        },
        RETRY:{
                  'status':'running',
                  'name':'owf-gear',
                  'description':'MOSJA13053'
        },
        ITA_UNPROCESS:{
                  'status':'running',
                  'name':'owf-gear',
                  'description':'MOSJA13058'
        },
        ITA_PROCESSING:{
                  'status':'running',
                  'name':'owf-gear',
                  'description':'MOSJA13058'
        },
        ITA_ERROR:{
                  'status':'attention',
                  'name':'owf-attention',
                  'description':'MOSJA13059'
        },
        ITA_CANCEL:{
                  'status':'attention',
                  'name':'owf-attention',
                  'description':'MOSJA13060'
        },
        ITA_FAIL:{
                  'status':'attention',
                  'name':'owf-attention',
                  'description':'MOSJA13061'
        },
        PREVENT:{
                  'status':'prevent',
                  'name':'owf-prevent',
                  'description':'MOSJA13062'
        },
        ITA_REGISTERING_SUBSTITUTION_VALUE:{
            'status':'running',
            'name':'owf-gear',
            'description':'MOSJA13083'
        },
        
    }


    ############################################
    # 詳細コード
    ############################################
    class DETAIL_STS():

        # 共通
        NONE = 0  # 詳細なし

        # NO_DRIVER固有
        DRV_UNKNOWN   = 1  # 不明なドライバー
        DRV_UNINSTALL = 2  # アンインストールドライバー

        # ACTION_DATA_ERROR固有
        DATAERR_SRVLIST_KEY = 1  # サーバーリストキー異常
        DATAERR_SRVLIST_VAL = 2  # サーバーリスト値異常
        DATAERR_PARAM_KEY   = 3  # パラメーター情報キー異常
        DATAERR_PARAM_VAL   = 4  # パラメーター情報値異常
        DATAERR_OPEID_KEY   = 5  # オペレーションIDキー異常
        DATAERR_OPEID_VAL   = 6  # オペレーションID値異常

        # ACTION_EXEC_ERROR固有
        EXECERR_OPEID_FAIL  = 101  # オペレーションID作成／取得失敗
        EXECERR_SYMP_FAIL   = 102  # Symphony実行エラー
        EXECERR_PARAM_FAIL  = 103  # パラメータシート登録失敗
        EXECERR_SEND_FAIL   = 201  # メール送信エラー

        # ITA_UNPROCESS固有
        ITAUNPROC         = 1  # 未実行
        ITAUNPROC_RESERVE = 2  # 未実行(予約)

        # ITA_PROCESSING固有
        ITAPROC      = 1  # 実行中
        ITAPROC_LATE = 2  # 実行中(遅延)

        # ITA_ERROR固有
        ITAERR          = 1  # 異常終了
        ITAERR_UNEXPECT = 2  # 想定外エラー

        # ITA_CANCEL固有
        ITACANCEL_STOP = 1  # 緊急停止
        ITACANCEL      = 2  # 予約取消

        # ITA_FAIL固有
        ITAFAIL_COMM = 1  # 通信障害
        ITAFAIL_AUTH = 2  # 認証失敗
        ITAFAIL_SYMP = 3  # 該当SymphonyIDなし
        ITAFAIL_DB   = 4  # DB参照エラー
        ITAFAIL_FOUT = 5  # ファイル出力エラー

#-------------------
# ACTION_TYPE_ID
#-------------------
ITA                 = 1   # ITA
MAIL                = 2   # メール

class ACTION_TYPE_ID():
    def __init__(self):
        self.ITA     = 1   # ITA
        self.mail    = 2   # メール

#-------------------
# RULE_TYPE_ID
#-------------------

#-------------------
# OPERATION_STATUS
#-------------------
class RULE_STS_OPERATION():
    STAGING_NOAPPLY = 20  # ステージング未適用
    STAGING_NOTYET  = 21  # ステージング検証未実施
    STAGING_VERIFY  = 22  # ステージング検証実施中
    STAGING_NG      = 23  # ステージング検証異常
    STAGING         = 24  # ステージング検証完了
    STAGING_END     = 25  # ステージング適用終了
    PRODUCT_NOAPPLY = 30  # プロダクト未適用
    PRODUCT         = 31  # プロダクト適用中
    PRODUCT_END     = 32  # プロダクト適用終了

#-------------------
# SYSTEM_STATUS
#-------------------
class RULE_STS_SYSTEM():
    UPLOAD          = 1   # アップロード中
    UPLOAD_NG       = 2   # アップロード異常終了
    UPLOAD_OK       = 3   # アップロード完了
    BUILD           = 11  # ビルド中
    BUILD_NG        = 12  # ビルド異常終了
    BUILD_OK        = 13  # ビルド完了
    STAGING         = 21  # ステージング適用中
    STAGING_NG      = 22  # ステージング適用異常終了
    STAGING_OK      = 23  # ステージング完了
    PRODUCT         = 31  # プロダクト適用中
    PRODUCT_NG      = 32  # プロダクト適用異常終了
    PRODUCT_OK      = 33  # プロダクト適用完了

    FINISH_STATUS = [2, 3, 12, 22, 23, 32, 33,]     # 最終ステータス

#-------------------
# PROCESS_MODE_ID
#-------------------
NORMAL              = 0   # 通常モード
RECOVER             = 1   # 強制処理モード

#-------------------
# LANG_MODE_ID
#-------------------
class LANG_MODE():
    JP              = 1
    EN              = 2

    LIST_ALL = [
            {'k': '日本語',  'v': JP},
            {'k': 'English', 'v': EN},
        ]

#-------------------
# DISP_MODE_ID
#-------------------
class DISP_MODE():
    DEFAULT         = 1
    SPECIAL         = 2

    LIST_ALL = [
            {'k': 'デフォルト', 'v': DEFAULT},
            {'k': 'スペシャル', 'v': SPECIAL},
        ]

#-------------------
# HTTPプロトコル
#-------------------
class HTTP_PROTOCOL():

    HTTP            = 'http'     # http(80)
    HTTPS           = 'https'     # https(443) 

    LIST_ALL = [
            {'k': 'http',   'v': HTTP},
            {'k': 'https',  'v': HTTPS},
        ]

#-------------------
# SMTPプロトコル
#-------------------
class SMTP_PROTOCOL():

    SMTP            = 1     # smtp(25)
    SMTP_AUTH       = 2     # smtp auth(587) 

    LIST_ALL = [
            {'k': 'smtp',      'v': SMTP},
            {'k': 'smtp_auth', 'v': SMTP_AUTH},
        ]

#-------------------
# DB操作コード
#-------------------
class DABASE_OPECODE():

    OPE_NOTHING     = 0
    OPE_INSERT      = 1
    OPE_UPDATE      = 2
    OPE_DELETE      = 3

    OPELIST_ADD     = [{'k':'', 'v':OPE_NOTHING}, {'k':'追加', 'v':OPE_INSERT}, ]
    OPELIST_MOD     = [{'k':'', 'v':OPE_NOTHING}, {'k':'更新', 'v':OPE_UPDATE}, {'k':'削除', 'v':OPE_DELETE}, ]

#-------------------
# メニューカテゴリー／アイテム
#-------------------
MENU = [
    #2141001001 , # 'ディシジョンテーブル',
    2141001006 , # 'ディシジョンテーブル新規追加',
    2141001007 , # 'ディシジョンテーブル編集削除',
    #2141001002 , # 'ルール',
    2141001004 , # 'ステージング',
    2141001005 , # 'プロダクション',
    2141001003 , # 'アクション履歴',
    2141001008 , # 'リクエスト履歴',
    2141002001 , # 'サービス状況',
    2141002002 , # 'システム設定',
    2141002003 , # 'グループ',
    2141002004 , # 'ユーザ',
    #2141002005 , # 'メールテンプレート',
    2141002006 , # '監視アダプタ',
    2141002007 , # 'アクション設定',
    2141003001 , # '個人設定',
    2141003002 , # 'アカウントロックユーザ',
    2141003003 , # 'お問い合わせ',
    2141003004 , # 'ログアウト',
    2141003005 , # 'ブラックリスト',
    2141003006 , # 'ホワイトリスト',
    ]

MENU_BY_RULE = [
    2141001007, 2141001004, 2141001005, 2141001003, 2141001008, 2141002006
]

class MENU_CATEGORY():

    ALLOW_EVERY = [ALLOWED_MENTENANCE, VIEW_ONLY, ]
    ALLOW_ADMIN = [ALLOWED_MENTENANCE, ]

    """
    CATEGORY_LIST = [
        {
            'name'      : 'メニューバータイトル表示名',
            'sub_name'  : '右側のメニュー識別 + 吹き出し文言'
            'classname' : '付与するクラス名',
            'selected'  : '選択中のページ表現に使用',
            'link'      : '遷移先',
            'item_list' : [子メニュー番号],
            'default'   : デフォルト表示するか否か True or False,
        },
    """


    CATEGORY_LIST = [
        {
            'name'      : 'MOSJA10021',
            'sub_name'  : '',
            'classname' : 'owf owf-dashboard',
            'selected'  : 'top',
            'link'      : 'web_app:top:index',
            'item_list' : [],
            'default'   : True,
        },
        {
            'name'      : 'MOSJA10038',
            'sub_name'  : '',
            'classname' : 'owf owf-rule',
            'selected'  : 'rule',
            'link'      : '#',
            'item_list' : [2141001001, 2141001002, 2141001008, 2141001003],
            'default'   : False,
        },
        {
            'name'      : 'MOSJA10039',
            'sub_name'  : '',
            'classname' : 'owf owf-setting',
            'selected'  : 'system',
            'link'      : '#',
            #'item_list' : [2141002001, 2141002002, 2141002003, 2141002004, 2141002006, 2141002007],
            'item_list' : [2141002002, 2141002003, 2141002004, 2141002006, 2141002007],
            'default'   : False,
        },
        {
            'name'      : 'MOSJA10040',
            'sub_name'  : '',
            'classname' : 'owf owf-authority',
            'selected'  : 'user',
            'link'      : '#',
            'item_list' : [2141003002, 2141003005, 2141003006],
            'default'   : False,
        },
        {
            'name'      : 'MOSJA10041',
            'classname' : 'owf owf-mail',
            'selected'  : 'contact',
            'link'      : 'web_app:top:inquiry',
            'item_list' : [],
            'default'   : True,
        },
        {
            'name'      : 'MOSJA10042',
            'classname' : 'owf owf-logout',
            'selected'  : 'logout',
            'link'      : '#',
            'item_list' : [],
            'default'   : True,
        },
    ]

    MENU_ITEM_URL = {
        2141001001 : {'name':'MOSJA00078', 'url':'web_app:rule:decision_table'},   # ディシジョンテーブル
        2141001002 : {'name':'MOSJA00089', 'url':'web_app:rule:rule'},             # ルール
        2141001008 : {'name':'MOSJA00091', 'url':'web_app:rule:request_history'},  # リクエスト履歴
        2141001003 : {'name':'MOSJA00092', 'url':'web_app:rule:action_history'},   # アクション履歴

        2141002001 : {'name':'MOSJA00237', 'url':'web_app:system:service'},        # サービス状況
        2141002002 : {'name':'MOSJA23031', 'url':'web_app:system:system_conf'},    # システム設定
        2141002003 : {'name':'MOSJA00037', 'url':'web_app:system:group'},          # グループ
        2141002004 : {'name':'MOSJA23032', 'url':'web_app:system:user'},           # ユーザ
        2141002006 : {'name':'MOSJA00238', 'url':'web_app:system:monitoring'},     # 監視アダプタ
        2141002007 : {'name':'MOSJA23033', 'url':'web_app:system:action'},         # アクション設定

        2141003001 : {'name':'MOSJA00032', 'url':'web_app:user:personal_config'},  # 個人設定
        2141003002 : {'name':'MOSJA33005', 'url':'web_app:user:locked_user'},      # アカウントロックユーザ
        2141003003 : {'name':'MOSJA00073', 'url':'web_app:top:inquiry'},           # お問い合わせ
        2141003004 : {'name':'MOSJA00239', 'url':'web_app:top:logout'},            # ログアウト
        2141003005 : {'name':'MOSJA34011', 'url':'web_app:user:black_list'},       # ブラックリスト
        2141003006 : {'name':'MOSJA35009', 'url':'web_app:user:white_list'},       # ホワイトリスト

    }

    MENU_ITEM_FRAME = {
        # アイテム : フレームリスト
        2141001001 : [2141001006, 2141001007],
        2141001002 : [2141001004, 2141001005],
    }


#-------------------
# システム設定
#-------------------
class SYSTEM_SETTINGS():

    CATEGORY_LIST = [
        'LOG_STORAGE_PERIOD',
        'SESSION_TIMEOUT',
        'ACTIVE_DIRECTORY',
        'PASSWORD',
        'ACCESS_RESTRICT',
    ]

    LOG_PERIOD = {
        #'agent_driver'    : 'MESSAGE_SORT_LOG', # いない？
        'oase_agent'       : 'RULE_ENGINE_LOG',
        'oase_action'      : 'AUTOMATION_LOG',
        'oase_apply'       : 'RULE_APPLY_LOG',
        'ad_collaboration' : 'AD_COLLAB_LOG',
        'oase_accept'      : 'REQUEST_ACCEPT_LOG',
        'oase_monitoring'  : 'MONITORING_LOG',
}

#-------------------
# AD認証
#-------------------
class AD_AUTH():

    import re

    REGEXP_INVALID_CREDENCIALS_MESSAGE = re.compile('.*, data 52e, .*')
    REGEXP_ACCOUNT_LOCKED_MESSAGE = re.compile('.*, data 775, .*')

    RESULT_SUCCESS              = 101
    RESULT_INVALID_CREDENCIALS  = 401
    RESULT_ACCOUNT_LOCKED       = 402
    RESULT_OTHER_ERROR          = 999

#-------------------
# DataObject条件IDの型
#-------------------
class EXPRESSION_TYPE():

    EXPRESSION_INTEGER = [1, 2, 5, 6, 7, 8,]
    EXPRESSION_STRING = [3, 4, 9, 10, 15,]
    EXPRESSION_LIST_STRING = [13, 14,]

#-------------------
# REQUEST_HISTORY_STATUS
#-------------------
class REQUEST_HISTORY_STATUS():

    ############################################
    # 状態コード
    ############################################
    # 共通ステータス
    PROCESSING = PROCESSING
    PROCESSED  = PROCESSED
    PENDING    = PENDING
    NO_DRIVER  = NO_DRIVER
    STOP       = STOP

    # リクエスト履歴固有ステータス
    RULE_MATCH = PROCESSED      # ルールマッチ
    RULE_UNMATCH = RULE_UNMATCH  # ルール未検出
    RULE_ERROR = RULE_ERROR      # ルール実行エラー


    STATUS_DESCRIPTION = {
        RULE_UNMATCH     : '処理済み(ルール未検出)',
        RULE_ERROR       : '処理済み(ルール実行エラー)',
        RULE_MATCH       : 'マッチ済',
    }

    ICON_INFO = {
        UNPROCESS:{
                  'status':'attention',
                  'name':'owf-gear',
                  'description':'未処理'
        },
        PROCESSING:{
                  'status':'running',
                  'name':'owf-gear',
                  'description':'処理中'
        },
        RULE_MATCH:{
                  'status':'complete',
                  'name':'owf-check',
                  'description':'マッチ済'
        },
        RULE_UNMATCH:{
                  'status':'attention',
                  'name':'owf-question',
                  'description':'ルール未検出'
        },
        RULE_ERROR:{
                  'status':'attention',
                  'name':'owf-attention',
                  'description':'ルール実行エラー'
        },
        FORCE_PROCESSED:{
                  'status':'error',
                  'name':'owf-attention',
                  'description':'強制終了'
        },
    }


