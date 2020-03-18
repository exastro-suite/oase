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
  認証バックエンド処理

[引数]


[戻り値]


"""




import pytz
import datetime
import traceback
import hashlib
import requests

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db import transaction
from django.urls import reverse
import libs.commonlibs.define as defs
from libs.commonlibs.ad_authenticator import AdAuthenticator
from libs.commonlibs.common import Common
from libs.commonlibs.oase_logger import OaseLogger
from libs.webcommonlibs.oase_exception import *
from libs.webcommonlibs.oase_mail import OASEMailSMTP, OASEMailUserLocked
from libs.webcommonlibs.common import Common as WebCommon
from web_app.models.models import User,System,AccessPermission,UserGroup

from datetime import timedelta

logger = OaseLogger.get_instance() # ロガー初期化


################################################################
# OASEユーザー認証
################################################################
class OASEAuthBackend(ModelBackend):

    full_name = 'libs.middleware.oase_auth.OASEAuthBackend'

    ############################################################
    def authenticate(self, request, username=None, password=None, **kwargs):

        try:
            with transaction.atomic():
                password_hash = Common.oase_hash(password)
                now  = datetime.datetime.now(pytz.timezone('UTC'))
                user = User.objects.select_for_update().get(login_id=username, login_id__contains=username, disuse_flag='0')
                uid  = user.user_id
                msg  = None

                self.check_account_lock_parameter(now, user, uid, username)

                # パスワードが一致したらユーザ情報を返却し終了
                if user.password == password_hash:
                    # ミス回数,アカウントロック回数リセット
                    user.password_count = 0
                    user.account_lock_times = 0
                    user.save(force_update=True)
                    return user

                logger.logic_log('LOSI13014', username, user.password_count, user.account_lock_times)
                msg = 'MOSJA10006'

                pass_err_obj = System.objects.get(config_id='PASS_ERROR_THRESHOLD')
                pass_err_int = int(pass_err_obj.value)
                if pass_err_int != 0 and uid > 0:
                    # ミス回数カウントアップ
                    if user.password_count is None:
                        user.password_count = 1
                    else:
                        user.password_count += 1

                    # 規定回数到達ならばロック
                    if user.password_count >= pass_err_int:

                        locktime_obj = System.objects.get(config_id='ACCOUNT_LOCK_PERIOD')
                        locktime_int = int(locktime_obj.value)

                        user.account_lock_time = now + timedelta(minutes=locktime_int)

                        logger.logic_log('LOSI13015', username, user.password_count, pass_err_int, user.account_lock_time)
                        msg = 'MOSJA10007'

                        # ロックタイミングでミス回数リセット
                        user.password_count = 0
                        user.account_lock_times += 1

                    # アカウントロック上限回数に達したらアカウントを永久ロック&メール通知
                    # アカウントロック上限回数が 0 の時はロックしない   
                    acct_lock_max = int(System.objects.get(config_id='ACCOUNT_LOCK_MAX_TIMES').value)
                    if user.account_lock_times >= acct_lock_max >= 1  and user.pk != 1:
                        logger.logic_log('LOSI13016', username, user.account_lock_times, acct_lock_max)
                        user.account_lock_flag = True
                        self._send_user_locked_mail(user.login_id, request)
                        msg = 'MOSJA10017'

                    # ユーザデータ更新
                    user.save(force_update=True)

        except System.DoesNotExist:
            logger.system_log('LOSM00001', traceback.format_exc())
            msg = 'MOSJA10015'

        except OASELoginError as e:
            logger.user_log('LOSM00001', traceback.format_exc())
            msg = e.msg_id

        raise OASELoginError(msg)

    def check_account_lock_parameter(self, now, user, uid, username):
        """
        [概要]
        アカウントロックフラグ,
        アカウントロック時間の検証を行います。
        """
        # アカウントロックフラグ確認
        if user.account_lock_flag:
            if uid > 0:
                logger.logic_log('LOSI13012', username, user.account_lock_flag)
                raise OASELoginError('MOSJA10018')

        # アカウントロック確認
        if user.account_lock_time is not None and user.account_lock_time > now:
            if uid > 0:
                logger.logic_log('LOSI13013', username, user.account_lock_time)
                raise OASELoginError('MOSJA10008')

    def get_user(self, user_id):

        user = None

        try:
            user = User.objects.get(user_id=user_id)

        except Exception as e:
            logger.system_log('LOSM00001', traceback.format_exc())
            return None

        return user


    def _send_user_locked_mail(self, login_id, request):
        """
        [概要]
        メール通知種別に応じてメールを送信する
        [引数]
        login_id : int ログインid
        """
        mail_list = WebCommon.get_mail_notification_list()
        smtp = OASEMailSMTP()
        # 署名用URL生成
        req_protcol = request.scheme
        req_host    = request.get_host()
        locked_url  = reverse('web_app:user:locked_user')
        login_url   = reverse('web_app:top:login')
        inquiry_url = reverse('web_app:top:inquiry')
        locked_url  ='%s://%s%s' % (req_protcol, req_host, locked_url)
        login_url   = '%s://%s%s' % (req_protcol, req_host, login_url)
        inquiry_url = '%s://%s%s' % (req_protcol, req_host, inquiry_url)

        for m in mail_list:
            user_mail = OASEMailUserLocked(m, login_id, locked_url, inquiry_url, login_url)
            _ = smtp.send_mail(user_mail)


################################################################
# ActiveDirectoryユーザー認証
################################################################
class ActiveDirectoryAuthBackend(ModelBackend):

    full_name = 'libs.middleware.oase_auth.ActiveDirectoryAuthBackend'

    def authenticate(self, request, username=None, password=None, **kwargs):

        # AD連携用のシステム設定値を取得する
        conf_dic = {}
        rset = System.objects.filter(category='ACTIVE_DIRECTORY').values('config_id', 'value')
        for rs in rset:
            key = rs['config_id']
            val = rs['value']

            # 接続先情報は配列に変換
            if key == 'ACCESS_POINT':
                tmp = val.split(',')
                val = []
                for t in tmp:
                    val.append(t.strip())

            # タイムアウト情報は数値に変換
            if key in ['CONNECTION_TIMEOUT', 'READ_TIMEOUT']:
                val = int(val)

            conf_dic[key] = val

        # AD連携フラグチェック
        if conf_dic['ADCOLLABORATION'] == '0':
            logger.system_log('LOSI13017', username)
            return None

        logger.logic_log('LOSI13018', username, conf_dic['ACCESS_POINT'], conf_dic['AUTHSERVER_SEARCH_CHAR'])

        # AD認証情報セット
        ad_auth = AdAuthenticator(
            conf_dic['AUTHSERVER_SEARCH_CHAR'],
            hosts           = conf_dic['ACCESS_POINT'],
            connect_timeout = conf_dic['CONNECTION_TIMEOUT'],
            read_timeout    = conf_dic['READ_TIMEOUT']
        )

        # 認証、および、その成否チェック
        conn_result = ad_auth.authenticate(username, password)
        if conn_result != defs.AD_AUTH.RESULT_SUCCESS:
            logger.system_log('LOSI13019', username, conn_result)

            # ユーザーID or パスワード誤り
            if conn_result == defs.AD_AUTH.RESULT_INVALID_CREDENCIALS:
                raise OASELoginError('MOSJA10012')

            # アカウントロック
            if conn_result == defs.AD_AUTH.RESULT_ACCOUNT_LOCKED:
                raise OASELoginError('MOSJA10013')

            # その他の認証時エラー
            raise OASELoginError('MOSJA10014')

        # AD認証成功後は、OASE認証を実施
        user = User.objects.get(login_id=username, login_id__contains=username, disuse_flag='0')

        return user


    def get_user(self, user_id):

        user = None

        try:
            user = User.objects.get(user_id=user_id)

        except Exception as e:
            logger.system_log('LOSM00001', traceback.format_exc())
            return None

        return user


