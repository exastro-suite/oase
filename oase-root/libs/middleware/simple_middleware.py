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
  ミドルウェア
  リクエスト／レスポンス時のフック処理

[引数]


[戻り値]


"""



import pytz
import datetime

from datetime import timedelta

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth import load_backend
from django.db.models.aggregates import Count

from libs.commonlibs import define as defs
from libs.commonlibs.oase_logger import OaseLogger
from libs.webcommonlibs.common import get_client_ipaddr, TimeConversion
from libs.webcommonlibs.user_config import UserConfig
from web_app.models.models import User, PasswordHistory, BlackListIPAddress, WhiteListIPAddress, System


logger = OaseLogger.get_instance() # ロガー初期化

from django.conf import settings
# 負荷テスト設定
ENABLE_LOAD_TEST = getattr(settings, 'ENABLE_LOAD_TEST', False)
if ENABLE_LOAD_TEST:
    import time
    import logging
    loadtest_logger = logging.getLogger('simple_middleware')

################################################
class SimpleMiddleware:

    """
    [クラス概要]
      HTTPリクエスト/レスポンス時の制御を行う
    """

    def __init__(self, get_response):

        """
        [メソッド概要]
          初期化処理
        [引数]
          get_response : HTTPレスポンス情報
        """

        self.get_response = get_response


    def __call__(self, request):

        """
        [メソッド概要]
          view関数呼び出し
        [引数]
          request : HTTPリクエスト情報
        [戻り値]
          HTTPレスポンス情報
        """

        # 負荷テスト設定
        if ENABLE_LOAD_TEST:
            start_time = time.time()
            loadtest_logger.warn('処理開始')

        ipaddr = get_client_ipaddr(request)

        # アクセス元IPアドレスのホワイトリストチェック
        if not settings.DISABLE_WHITE_BLACK_LIST and not self._chk_white_black_list(ipaddr):
            raise PermissionDenied

        response = self.get_response(request)
        
        # 負荷テスト設定
        if ENABLE_LOAD_TEST:
            elapsed_time = time.time() - start_time
            loadtest_logger.warn('処理終了 所要時間[%s]' % (elapsed_time))
        
        return response


    def  _chk_white_black_list(self, ipaddr):
        """
        [メソッド概要]
          ブラックリストチェック処理
        [引数]
          ipaddr     : アクセス元のIPアドレス
        [戻り値]
          なし
        """
        whiteip_list = list(WhiteListIPAddress.objects.all().values_list('ipaddr', flat=True))
        if not self._check_list(ipaddr, whiteip_list, 'White'):

            # アクセス元IPアドレスのブラックリストチェック
            black_ipaddr_list = BlackListIPAddress.objects.all().values_list('ipaddr', flat=True).annotate(cnt=Count("*"))

            blackip_list = []
            for b_ip in black_ipaddr_list:
                recent_record = list(BlackListIPAddress.objects.filter(ipaddr=b_ip).order_by('black_list_id').reverse()[:1])[0]

                if recent_record.release_timestamp == None:
                    blackip_list.append(recent_record.ipaddr)

            if self._check_list(ipaddr, blackip_list, 'Black'):
                logger.system_log('LOSI13004', ipaddr, )
                return False

        return True

    def _check_list(self, ipaddr, ip_list, str_type=''):
        """
        [メソッド概要]
          IPリストチェック処理
        [引数]
          ipaddr     : アクセス元のIPアドレス
          ip_list    : ブラックまたはホワイトリストのデータ
        [戻り値]
          チェック結果
        """
        for ip in ip_list:

            if ipaddr == ip:
                logger.system_log('LOSI13010', str_type, ipaddr , ip)
                return True

            wild_position = ip.find('*')
            sub_ip = ip[0:wild_position]

            if wild_position == 0 or wild_position > 0 and ipaddr.startswith(sub_ip):
                logger.system_log('LOSI13010', str_type, ipaddr , ip)
                return True

        return False


    def process_view(self, request, view_func, view_args, view_kwargs):

        """
        [メソッド概要]
          view関数呼び出し時処理
        [引数]
          request     : HTTPリクエスト情報
          view_func   : view関数名
          view_args   : view関数パラメーター(list)
          view_kwargs : view関数パラメーター(dict)
        [戻り値]
          HTTPレスポンス情報
        """
        ########################################################
        # セッションチェック処理
        ########################################################
        # 認証前のリクエスト時はログイン画面へ遷移
        if not request.session:
            return self.get_redirect(request, 'LOSI00015')

        # セッション情報が異常の場合、ログイン画面へ遷移
        if '_auth_user_id' not in request.session:
            return self.get_redirect(request, 'LOSM00017')

        if '_auth_user_backend' not in request.session:
            return self.get_redirect(request, 'LOSM00018')

        if 'cookie_age' not in request.session:
            return self.get_redirect(request, 'LOSM00019')

        # 認証時に使用したバックエンドクラスからユーザー情報取得
        backend_path = request.session['_auth_user_backend']
        backend = load_backend(backend_path)

        request.user = backend.get_user(request.session['_auth_user_id'])

        if request.user == None:
            request.session['msg'] = 'MOSJA10016'
            return self.get_redirect(request, 'LOSM00020')

        # セッション有効期限切れの場合、ログイン画面へ遷移
        now = datetime.datetime.now(pytz.timezone('UTC'))

        if now > TimeConversion.get_time_conversion_utc(request.session['cookie_age'], 'UTC', request):
            request.session.clear()
            request.session.flush()
            return self.get_redirect(request, 'LOSI00014')

        # セッション有効期間を取得(デフォルト30分)
        timeout_val = System.objects.get(config_id='SESSION_TIMEOUT').value
        if timeout_val is None:
            timeout_val = 30

        else:
            timeout_val = int(timeout_val)

        # 設定値にしたがいセッション有効期間を延長
        request.session['cookie_age'] = (now + timedelta(minutes=timeout_val)).strftime('%Y-%m-%d %H:%M:%S')

        # ユーザー設定のロード
        uconf = UserConfig(request.user)
        setattr(request, 'user_config', uconf)

        # パスワード有効期限チェックフラグがFalseなら何もしない
        if not request.user.pass_exp_check_flag:
            return None

        # パスワードの状態取得
        pass_flag = self.chk_password_state(request,now)

        if pass_flag == 'initial_pass_expired':
            logger.logic_log('LOSI00016', request=request)
            request.session['msg'] = 'MOSJA32023'
            return HttpResponseRedirect(reverse('web_app:top:login'))

        if pass_flag in ['initial_pass' ,'onetime_pass' ,'pass_expired']:
            logger.logic_log('LOSI00017', request=request)
            return HttpResponseRedirect(reverse('web_app:top:pass_ch'))

        return None

    def get_redirect(self, request, msgid):

        """
        [メソッド概要]
          ログイン画面へのリダイレクト
        [引数]
          request : HTTPリクエスト情報
        [戻り値]
          リダイレクト先のHTTPレスポンス情報
        """

        # リクエスト先URLが認証無用の場合、リダイレクトは行わない
        allowed_path = []
        allowed_path.append(reverse('web_app:top:login'))
        allowed_path.append(reverse('web_app:top:login_auth'))
        allowed_path.append(reverse('web_app:event:eventsrequest'))
        allowed_path.append(reverse('web_app:top:pass_initialize'))
        allowed_path.append(reverse('web_app:top:onetime_pass_exec'))
        allowed_path.append(reverse('web_app:user:user_determ_mailaddr'))
        allowed_path.append(reverse('web_app:restapi:historyrequest'))
        allowed_path.append(reverse('web_app:event:bulk_eventsrequest'))

        if request.path in allowed_path:
            return None

        if request.path.startswith('/oase_web/event/evtimer/'):
            return None

        # デバッグログ出力
        logger.system_log(msgid, request=request)

        # ログイン後の遷移先画面情報を取得
        req_path = ''
        for k, v in defs.MENU_CATEGORY.MENU_ITEM_URL.items():
            req_path = reverse(v['url'])
            if request.path.startswith(req_path):
                break

        else:
            req_path = ''

        # ajaxの場合はエラーステータスを応答
        if 'HTTP_X_REQUESTED_WITH' in request.META and request.META['HTTP_X_REQUESTED_WITH'] == 'XMLHttpRequest':
            logger.logic_log('LOSM00016')
            return HttpResponse(status=400)

        # ログイン画面へ遷移
        url = reverse('web_app:top:login')
        if req_path:
            url = '%s?%s' % (url, req_path)

        logger.logic_log('LOSI00013')
        return HttpResponseRedirect(url)

    def chk_password_state(self, request, now):
        """
        [メソッド概要]
          パスワードの状態判定
        [引数]
          request : HTTPリクエスト情報
          now     : 現在時刻日時
        [戻り値]
          パスワードの状態
        """

        ########################################################
        # AD連携をしていない場合のみ、チェックを実施
        ########################################################
        if request.session['_auth_user_backend'].endswith('ActiveDirectoryAuthBackend'):
            return 'normal'

        ########################################################
        # URLチェック
        ########################################################
        allowed_path = []
        allowed_path.append(reverse('web_app:top:login'))
        allowed_path.append(reverse('web_app:top:logout'))
        allowed_path.append(reverse('web_app:top:pass_ch'))
        allowed_path.append(reverse('web_app:top:pass_ch_logout'))
        allowed_path.append(reverse('web_app:top:pass_ch_exec'))
        allowed_path.append(reverse('web_app:top:pass_initialize'))
        allowed_path.append(reverse('web_app:top:onetime_pass_exec'))
        allowed_path.append(reverse('web_app:user:user_determ_mailaddr'))

        if request.path in allowed_path:
            return 'normal'

        ########################################################
        # 初回ログイン判定処理
        ########################################################
        # ユーザ情報取得
        uid       = request.user.user_id
        user      = request.user
        password_last_modified = user.password_last_modified
        password_expire        = user.password_expire

        # (初期パスワードまたはワンタイムパスワード用の) パスワード有効期限がある場合
        if password_expire is not None:

            # 有効期限切れの場合
            if password_expire < now:
                return 'initial_pass_expired'

            # パスワード最終更新日時がある場合はワイタイムパスワード
            if password_last_modified is not None:
                # ワンタイムパスワード
                return 'onetime_pass'

            return 'initial_pass'

        ########################################################
        # パスワード有効期間チェック処理
        ########################################################
        # パスワード有効期間情報取得
        lifetime_val = int(System.objects.get(config_id='Pass_Valid_Period').value)

        # パスワード有効期間が設定されている場合のみチェック処理を実施
        if lifetime_val > 0:

            # パスワード最終更新日時がある場合
            last_login = user.last_login
            if password_last_modified is None or last_login is None:
                return 'pass_expired'

            # パスワード最終更新日時から一定期間を超過している場合、パスワード変更画面へ遷移
            valid_period = password_last_modified + timedelta(days=lifetime_val)
            if last_login > valid_period:
                return 'pass_expired'

        return 'normal'
