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
    ディシジョンテーブルに関連する各種要素のクラス

"""



import smtplib
import ast
import traceback

from email.mime.text import MIMEText
from email.header import Header
from email.utils import formatdate

from django.conf import settings

from libs.commonlibs.oase_logger import OaseLogger
from web_app.models.models import System


logger = OaseLogger.get_instance() # ロガー初期化


class OASEMailSMTP(object):

    """
    [クラス概要]
      OASEからのメール送信クラス
    """

    ############################################
    # 定数定義
    ############################################
    # システム設定ID
    CONFIG_ID = 'OASE_MAIL_SMTP'


    def __init__(self, str_conf=None, ip_addr=None, port=None, auth_flg=None, request=None):
        """
        [メソッド概要]
          初期化処理
        [引数]
          str_conf : str  接続情報(DBから取得した文字列)
          ip_addr  : str  接続先IPアドレス
          port     : int  接続先ポート
          auth_flg : bool 認証要否フラグ
          request  : HttpRequest  HTTPリクエスト情報
        """

        self.request  = request

        # 接続先SMTP情報を初期化
        self.ip_addr  = ip_addr
        self.port     = port
        self.auth_flg = auth_flg

        # 既にDBから取得している情報が指定された場合
        if str_conf:
            self.parse_str(str_conf)

        # 初期パラメーターが不完全の場合は、DBから情報を取得
        if self.ip_addr is None or self.port is None or self.auth_flg is None:
            self.load_config()


    def load_config(self):
        """
        [メソッド概要]
          システム設定情報の読み込み
        """

        try:
            conf_val = System.objects.get(config_id=self.CONFIG_ID).value
            self.parse_str(conf_val)

        except System.DoesNotExist:
            logger.system_log('LOSE13002', 'mail', 'OASE_MAIL_SMTP', request=self.request)

        except Exception as e:
            logger.logic_log('LOSM00001', traceback.format_exc(), request=self.request)


    def parse_str(self, conf_val):
        """
        [メソッド概要]
          システム設定情報の解析
        [引数]
          conf_val : DBから取得した文字列(OASE_T_SYSTEM.value)
        """

        conf = ast.literal_eval(conf_val)
        self.ip_addr  = conf['IPADDR'] if 'IPADDR' in conf else None
        self.port     = conf['PORT']   if 'PORT'   in conf else None
        self.auth_flg = conf['AUTH']   if 'AUTH'   in conf else None


    def send_mail(self, cls_mail, passwd=None):
        """
        [メソッド概要]
          システム設定情報の読み込み
        [引数]
          cls_mail : OASEMailBase
          passwd   : str 要認証時のパスワード
        [戻り値]
          str : エラーメッセージ
        """

        msg = ''

        try:
            logger.logic_log('LOSI13011', cls_mail.__class__.__name__, cls_mail.addr_to, cls_mail.subject, request=self.request)

            # 接続先情報チェック
            if self.ip_addr is None or self.port is None or self.auth_flg is None:
                if getattr(settings, 'DEBUG', False):
                    print('####### 実際にメール送信は行いません #######')
                    print('[Subject]%s' % (cls_mail.subject))
                    print('   [From]%s' % (cls_mail.addr_from))
                    print('     [To]%s' % (cls_mail.addr_to))
                    print('------- 本文 -------')
                    print('%s' % (cls_mail.mail_text))
                    return ''

                msg = 'MOSJA00006'
                logger.logic_log('LOSM13020', self.ip_addr, self.port, self.auth_flg, request=self.request)
                raise Exception(msg)

            if self.auth_flg and not passwd:
                msg  = 'MOSJA00007'
                logger.logic_log('LOSM13021', 'SMTP authentication information', request=self.request)
                raise Exception(msg)

            # 件名チェック
            if len(cls_mail.subject) <= 0:
                msg = 'MOSJA00008'
                logger.logic_log('LOSM13021', 'subject', request=self.request)
                raise Exception(msg)

            # 本文チェック
            if len(cls_mail.mail_text) <= 0:
                msg = 'MOSJA00009'
                logger.logic_log('LOSM13021', 'mail text', request=self.request)
                raise Exception(msg)

            # 送信内容セット
            smtp_header = {}
            smtp_header = MIMEText(cls_mail.mail_text.encode(cls_mail.charset), 'plain', cls_mail.charset)
            smtp_header['Subject'] = Header(cls_mail.subject, cls_mail.charset)
            smtp_header['From']    = cls_mail.addr_from
            smtp_header['To']      = cls_mail.addr_to
            smtp_header['Date']    = formatdate(localtime=True)

            # メール送信
            smtp = smtplib.SMTP(self.ip_addr, self.port)
            if self.auth_flg:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                smtp.login(cls_mail.addr_from, passwd)

            smtp.sendmail(cls_mail.addr_from, cls_mail.addr_to, smtp_header.as_string())
            smtp.close()

        except Exception as e:
            logger.logic_log('LOSM00001', traceback.format_exc(), request=self.request)
            if not msg:
                msg = 'MOSJA00010'

        return msg


class OASEMailBase(object):

    """
    [クラス概要]
      OASEからのメール基本クラス
    """

    def __init__(self, addr_from, addr_to, subject, mail_text, inquiry_url, login_url, charset='utf-8', lang='jp'):
        """
        [メソッド概要]
          初期化処理
        [引数]
          addr_from   : str 送信者メールアドレス
          addr_to     : str 宛先メールアドレス
          subject     : str 件名
          mail_text   : str メール本文
          charset     : str 文字コード
          inquiry_url : str お問い合わせ画面
          login_url   : str ログイン画面
        """

        # メール情報を初期化
        self.addr_from   = addr_from
        self.addr_to     = addr_to
        self.subject     = subject
        self.mail_text   = mail_text
        self.charset     = charset
        self.inquiry_url = inquiry_url
        self.login_url   = login_url


        # 前文,署名の初期化
        try:
            if lang == 'jp':
                header, signature = System.objects.filter(config_id__in=['MAIL_HEADER_JP','MAIL_SIGNATURE_JP']).order_by('item_id')
                self.header = header.value
                self.signature = signature.value %(self.inquiry_url, self.login_url)
        except Exception as e:
            self.header = '' 
            self.signature = ''
            logger.system_log('LOSM00001', traceback.format_exc())

    def add_header(self):
        """
        [メソッド概要]
          文章に前文を追加
        """
        self.mail_text = self.header + self.mail_text

    def add_signature(self):
        """
        [メソッド概要]
          文章の最後に署名を追加
        """
        self.mail_text = self.mail_text + self.signature



    def add_text(self, text):
        """
        [メソッド概要]
          文章にtextを追加
        """
        self.mail_text += text

    def create_mail_text(self):
        """
        [メソッド概要]
          仮想のため処理は行わない
        """
        pass


class OASEMailInitialPasswd(OASEMailBase):

    """
    [クラス概要]
      初期パスワード通知メール
    """

    # メール情報
    MAILACC  = "noreply@omcs.jp.nec.com"
    SUBJECT  = "パスワード通知"
    MAILTEXT = (
        "%s 様\n"
        "\n"
        "Operation Autonomy Support Engineへのご登録ありがとうございます。\n\n"
        "ユーザが新規作成されました。\n"
        "以下のログインID、ワンタイムパスワードでの初回ログインが必要です。\n"
        "\n"
        "[ログインID] 別途メールにて送信\n"
        "[ワンタイムパスワード] %s\n"
        "\n"
        "ワンタイムパスワードの有効期間は%s時間です。\n"
        "有効期間を過ぎた場合は、ログイン画面の「パスワードをお忘れの場合」\n"
        "での再発行が必要となります。\n"
        "\n"
    )
    #有効時間が0の場合
    MAILTEXT2 = (
        "%s 様\n"
        "\n"
        "Operation Autonomy Support Engineへのご登録ありがとうございます。\n\n"
        "ユーザが新規作成されました。\n"
        "以下のログインID、ワンタイムパスワードでの初回ログインが必要です。\n"
        "\n"
        "[ログインID] 別途メールにて送信\n"
        "[ワンタイムパスワード] %s\n\n"
    )

    def __init__(self, addr_from, addr_to, user_name, passwd, expire_h, inquiry_url, login_url, charset='utf-8'):
        """
        [メソッド概要]
          初期化処理
        [引数]
          addr_from   : str 送信者メールアドレス
          addr_to     : str 宛先メールアドレス
          user_name   : str 宛先ユーザ名
          passwd      : str 初期パスワード
          expire_h    : int パスワード有効期間(hour)
          inquiry_url : str お問い合わせ画面
          login_url   : str ログイン画面
          charset     : str 文字コード
        """
        super(OASEMailInitialPasswd, self).__init__(self.MAILACC, addr_to, self.SUBJECT, '', inquiry_url, login_url, charset)
        self.create_mail_text(user_name, passwd, expire_h)

    def create_mail_text(self, user_name, passwd, expire_h):
        """
        [メソッド概要]
          メール本文作成
        [引数]
          user_name : str 宛先ユーザ名
          passwd    : str 初期パスワード
          expire_h  : int パスワード有効期間(hour)
        """
        self.add_header()
        if 1 <= expire_h <= 24:
            self.add_text(self.MAILTEXT % (user_name, passwd, expire_h))
        else:
            self.add_text(self.MAILTEXT2 % (user_name, passwd))
        self.add_signature()



class OASEMailInitialLoginID(OASEMailBase):

    """
    [クラス概要]
      ログインID通知メール
    """

    # メール情報
    MAILACC  = "noreply@omcs.jp.nec.com"
    SUBJECT  = "ログインID通知"
    MAILTEXT = (
        "%s 様\n"
        "\n"
        "Operation Autonomy Support Engineへのご登録ありがとうございます。\n\n"
        "ユーザが新規作成されました。\n"
        "以下のログインID、ワンタイムパスワードでの初回ログインが必要です。\n"
        "\n"
        "[ログインID] %s\n"
        "[ワンタイムパスワード] 別途メールにて送信\n"
        "\n"
        "ワンタイムパスワードの有効期間は%s時間です。\n"
        "有効期間を過ぎた場合は、ログイン画面の「パスワードをお忘れの場合」\n"
        "での再発行が必要となります。\n"
        "\n"
    )
    #有効時間が0の場合
    MAILTEXT2 = (
        "%s 様\n"
        "\n"
        "Operation Autonomy Support Engineへのご登録ありがとうございます。\n\n"
        "ユーザが新規作成されました。\n"
        "以下のログインID、ワンタイムパスワードでの初回ログインが必要です。\n"
        "\n"
        "[ログインID] %s\n"
        "[ワンタイムパスワード] 別途メールにて送信\n\n"
    )

    def __init__(self, addr_from, addr_to, user_name, login_id, expire_h, inquiry_url, login_url, charset='utf-8'):
        """
        [メソッド概要]
          初期化処理
        [引数]
          addr_from   : str 送信者メールアドレス
          addr_to     : str 宛先メールアドレス
          user_name   : str 宛先ユーザ名
          login_id    : str ログインID
          expire_h    : int パスワード有効期間(hour)
          inquiry_url : str お問い合わせ画面
          login_url   : str ログイン画面
          charset     : str 文字コード
        """

        super(OASEMailInitialLoginID, self).__init__(self.MAILACC, addr_to, self.SUBJECT, '', inquiry_url, login_url, charset)
        self.create_mail_text(user_name, login_id, expire_h)

    def create_mail_text(self, user_name, login_id, expire_h):
        """
        [メソッド概要]
          メール本文作成
        [引数]
          user_name : str 宛先ユーザ名
          login_id  : str ログインID
          expire_h  : int パスワード有効期間(hour)
        """

        self.add_header()
        if 1 <= expire_h <= 24:
            self.add_text(self.MAILTEXT % (user_name, login_id, expire_h))
        else:
            self.add_text(self.MAILTEXT2 % (user_name, login_id))
        self.add_signature()

class OASEMailOnetimePasswd(OASEMailBase):

    """
    [クラス概要]
      ワンタイムパスワード通知メール
    """
    # メール情報
    MAILACC  = "noreply@omcs.jp.nec.com"
    SUBJECT  = "パスワードリセット通知"
    MAILTEXT = (
        "%s 様\n"
        "\n"
        "ワンタイムパスワードを発行致しました。\n"
        "\n"
        "[ワンタイムパスワード]  %s\n"
        "\n"
        "ワンタイムパスワードの有効期間は%s時間です。\n"
        "有効期間を過ぎると、再設定が必要となります。\n"
        "必ず、有効期間内にログイン、パスワード変更をお願い致します。\n"
        "\n"
    )
    #有効時間が0の場合
    MAILTEXT2 = (
        "%s 様\n"
        "\n"
        "ワンタイムパスワードを発行致しました。\n"
        "\n"
        "[ワンタイムパスワード]  %s\n\n"
    )

    def __init__(self, addr_from, addr_to, user_name, passwd, expire_h, inquiry_url, login_url, charset='utf-8'):
        """
        [メソッド概要]
          初期化処理
        [引数]
          addr_from   : str 送信者メールアドレス
          addr_to     : str 宛先メールアドレス
          user_name   : str 宛先ユーザ名
          passwd      : str ワンタイムパスワード
          expire_h    : int パスワード有効期間(hour)
          inquiry_url : str お問い合わせ画面
          login_url   : str ログイン画面
          charset     : str 文字コード
        """
        super(OASEMailOnetimePasswd, self).__init__(self.MAILACC, addr_to, self.SUBJECT, '', inquiry_url, login_url, charset)
        self.create_mail_text(user_name, passwd, expire_h)

    def create_mail_text(self, user_name, passwd, expire_h):
        """
        [メソッド概要]
          メール本文作成
        [引数]
          user_name : str 宛先ユーザ名
          passwd    : str ワンタイムパスワード
          expire_h  : int パスワード有効期間(hour)
        """
        self.add_header()
        if 1 <= expire_h <= 24:
            self.add_text(self.MAILTEXT % (user_name, passwd, expire_h))
        else:
            self.add_text(self.MAILTEXT2 % (user_name, passwd))
        self.add_signature()

class OASEMailUserLocked(OASEMailBase):

    """
    [クラス概要]
      ワンタイムパスワード通知メール
    """
    # メール情報
    MAILACC  = "noreply@omcs.jp.nec.com"
    SUBJECT  = "ユーザロック通知"
    MAILTEXT = (
        "ユーザID「%s」が連続ロック上限回数に達しました。\n"
        "確認し、問題がなければロックの解除をお願い致します。\n"
        " %s \n"
        "\n"
    )

    def __init__(self, addr_to, login_id, locked_url, inquiry_url, login_url, charset='utf-8'):
        """
        [メソッド概要]
          初期化処理
        [引数]
          addr_to     : str 宛先メールアドレス
          user_name   : str 宛先ユーザ名
          login_id    : str ユーザロックされたログインID
          locked_url  : str アカウントロックユーザ画面
          inquiry_url : str お問い合わせ画面
          login_url   : str ログイン画面
          charset     : str 文字コード
        """
        super(OASEMailUserLocked, self).__init__(self.MAILACC, addr_to, self.SUBJECT, '', inquiry_url, login_url, charset)
        self.create_mail_text(login_id, locked_url)

    def create_mail_text(self, login_id, locked_url):
        """
        [メソッド概要]
          メール本文作成
        [引数]
          user_name  : str 宛先ユーザ名
          login_id   : str ユーザロックされたログインID
          locked_url : str アカウントロックユーザ画面
        """

        self.add_header()
        self.add_text(self.MAILTEXT % (login_id, locked_url))
        self.add_signature()

class OASEMailAddBlackList(OASEMailBase):

    """
    [クラス概要]
      ブラックリスト登録通知メール
    """

    # メール情報
    MAILACC  = "noreply@omcs.jp.nec.com"
    SUBJECT  = "ブラックリスト登録"
    MAILTEXT = (
        "　IP「%s」からのログインが、連続ログイン試行回数の上限に達したため、ブラックリストに登録しました。\n"
        "確認後、問題なければ、解除を実施してください\n"
        "\n"
        "%s\n"
    )

    def __init__(self, addr_to, ipaddr, url, inquiry_url, login_url, charset='utf-8'):
        """
        [メソッド概要]
          初期化処理
        [引数]
          addr_to   : str 宛先メールアドレス
          user_name : str 宛先ユーザ名
          ipaddr    : str ブラックリスト登録されたipアドレス
          url       : url ブラックリスト画面URL
          charset   : str 文字コード
        """
        super(OASEMailAddBlackList, self).__init__(self.MAILACC, addr_to, self.SUBJECT, '', inquiry_url, login_url, charset)
        self.create_mail_text(ipaddr, url)

    def create_mail_text(self, ipaddr, url):
        """
        [メソッド概要]
          メール本文作成
        [引数]
          user_name : str 宛先ユーザ名
          ipaddr    : str ブラックリスト登録されたipアドレス
        """
        self.add_header()
        self.add_text(self.MAILTEXT % (ipaddr, url))
        self.add_signature()


class OASEMailModifyMailAddressNotify(OASEMailBase):

    """
    [クラス概要]
      メールアドレス変更通知メール
    """

    # メール情報
    MAILACC   = "noreply@omcs.jp.nec.com"
    SUBJECT   = "メールアドレスのご変更"
    CONFIG_ID = "MODIFY_MAILADDR_NOTIFY"

    def __init__(self, addr_to, user_name, valid_hour, url, inquiry_url, login_url, charset='utf-8'):
        """
        [メソッド概要]
          初期化処理
        [引数]
          addr_to    : str 宛先メールアドレス
          user_name  : str 宛先ユーザ名
          valid_hour : int メールアドレス変更URLの有効期間(hour)
          url        : url メールアドレス変更URL
        """
        super(OASEMailModifyMailAddressNotify, self).__init__(self.MAILACC, addr_to, self.SUBJECT, '', inquiry_url, login_url, charset)
        self.create_mail_text(user_name, valid_hour, url)

    def create_mail_text(self, user_name, valid_hour, url):
        """
        [メソッド概要]
          メール本文作成
        [引数]
          user_name : str 宛先ユーザ名
          ipaddr    : str ブラックリスト登録されたipアドレス
        """
        self.mail_text = System.objects.get(config_id=self.CONFIG_ID).value
        self.mail_text = self.mail_text % (user_name, valid_hour, url)

        self.add_header()
        self.add_signature()


