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
  ログイン／ログアウト処理

[引数]


[戻り値]


"""



import traceback
import pytz
import datetime

from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib.auth import login  as auth_login
from django.contrib.auth import logout as auth_logout
from django.conf import settings
from django.urls import reverse
from django.utils.translation import LANGUAGE_SESSION_KEY

from libs.commonlibs import define as defs
from libs.commonlibs.oase_logger import OaseLogger
from libs.middleware.oase_auth import *
from libs.webcommonlibs.oase_exception import *
from libs.webcommonlibs.decorator import *
from libs.webcommonlibs.oase_mail import OASEMailSMTP, OASEMailAddBlackList
from libs.webcommonlibs.common import Common, get_client_ipaddr
from web_app.models.models import LoginLogIPAddress, BlackListIPAddress, System

logger = OaseLogger.get_instance() # ロガー初期化

################################################
def _ipaddr_login_log(request, ipaddr, login_id, flg, now):
    """
    [メソッド概要]
      ログインの成否によりログインログを操作する
    [引数]
      ipaddr   : ログイン元IPアドレス
      login_id : 入力ログインID
      flg      : ログイン成否 True=成功、False=失敗
      now      : ログイン試行日時
    """

    if not now:
        now = datetime.datetime.now(pytz.timezone('UTC'))

    try:
        with transaction.atomic():
            # ログイン成功IPアドレスを削除
            if flg:
                LoginLogIPAddress.objects.filter(ipaddr=ipaddr).delete()

            # ログイン失敗時はログインログに登録
            else:
                save_login_id = login_id[:32]

                # ログインログを保存
                LoginLogIPAddress(
                    ipaddr                = ipaddr,
                    login_id              = save_login_id,
                    last_update_timestamp = now,
                ).save(force_insert=True)

                # 連続失敗回数の規定値を取得
                threshold = 0
                try:
                    threshold = int(System.objects.get(config_id='IPADDR_LOGIN_RETRY_MAX').value)
                except Exception as e:
                    pass

                if threshold > 0:

                    # 連続失敗回数が規定数に達したら、ブラックリストに登録
                    rcnt = LoginLogIPAddress.objects.filter(ipaddr=ipaddr).count()
                    # ブラックリストに登録済かつ有効のIPを検索
                    recent_record = list(BlackListIPAddress.objects.filter(ipaddr=ipaddr).order_by('black_list_id').reverse()[:1])

                    auto_blacklist = 0
                    if len(recent_record) > 0:
                        if recent_record[0].release_timestamp == None:
                            auto_blacklist = 1

                    logger.logic_log('LOSI13005', ipaddr, rcnt, threshold, auto_blacklist)

                    if rcnt >= threshold and auto_blacklist < 1:
                        BlackListIPAddress(
                            ipaddr                = ipaddr,
                            release_timestamp     = None,
                            last_update_timestamp = now,
                            last_update_user      = '',
                            manual_reg_flag       = False
                        ).save(force_insert=True)

                        # ブラックリスト登録時、連続失敗回数をリセットする
                        LoginLogIPAddress.objects.filter(ipaddr=ipaddr).delete()

                        # URL生成
                        req_protcol = request.scheme
                        req_host    = request.get_host()
                        url         = reverse('web_app:user:black_list')
                        url         = '%s://%s%s' % (req_protcol, req_host, url)
                        # 署名用URL生成
                        login_url   = reverse('web_app:top:login')
                        contact_url = reverse('web_app:top:inquiry')
                        login_url   = '%s://%s%s' % (req_protcol, req_host, login_url)
                        contact_url = '%s://%s%s' % (req_protcol, req_host, contact_url)

                        # メール通知
                        mail_list = Common.get_mail_notification_list()
                        smtp = OASEMailSMTP()
                        for m in mail_list:
                            user_mail = OASEMailAddBlackList(m, ipaddr, url, contact_url, login_url)
                            _ = smtp.send_mail(user_mail)


    except Exception as e:
        logger.system_log('LOSM13015', ipaddr, login_id, flg, traceback.format_exc())


################################################
def _check_input_auth_info(login_id, password, request=None):
    """
    [メソッド概要]
      認証情報が入力されているかチェック
      ※try の中で呼び出すこと
    [引数]
      login_id : 入力ログインID
      password : 入力パスワード
      request  : リクエスト情報
    """

    if not login_id and not password:
        logger.user_log('LOSM13007', request=request)
        raise OASELoginError('MOSJA10002')
    elif not login_id:
        logger.user_log('LOSM13008', request=request)
        raise OASELoginError('MOSJA10003')
    elif not password:
        logger.user_log('LOSM13009', request=request)
        raise OASELoginError('MOSJA10004')


################################################
def _get_value_session_timeout():
    """
    [メソッド概要]
      セッションタイムアウト時間の設定値を取得
    """

    timeout_val = System.objects.get(config_id='SESSION_TIMEOUT').value
    if timeout_val is None:
        timeout_val = 30

    else:
        timeout_val = int(timeout_val)

    return timeout_val


################################################
def _get_url_after_login(request):
    """
    [メソッド概要]
      ログイン後の遷移先URLを取得
    """

    redirect_url = ''

    query_str_list = request.get_full_path().split('?')
    if len(query_str_list) > 1:
        del query_str_list[0]
        query_str = '?'.join(query_str_list)
        if 'logout' not in query_str:
            redirect_url = query_str

    if not redirect_url:
        redirect_url = settings.LOGIN_REDIRECT_URL

    return redirect_url


################################################
def login(request):

    logger.logic_log('LOSI00001', 'None', request=request)

    logout = True if "logout" in request.GET and request.GET.get("logout") == 'true' else False

    ad_collabo = int(System.objects.get(config_id='ADCOLLABORATION').value)

    pass_init_url = reverse('web_app:top:pass_initialize') + '?' + reverse('web_app:top:login')

    msg = ''
    if 'msg' in request.session:
        msg = request.session.pop('msg')

    data = {
        'msg'           : msg,
        'logout'        : logout,
        'ad_collabo'    : ad_collabo,
        'pass_init_url' : pass_init_url,
        'lang_mode'     : 'JA',
    }

    logger.logic_log('LOSI00002', '', request=request)

    return render(request, 'top/login.html', data)


################################################
def logout(request):

    logger.logic_log('LOSI00001', 'None', request=request)

    auth_logout(request)

    request.session.clear()
    request.session.flush()

    logger.logic_log('LOSI00002', 'None', request=request)

    return redirect('/oase_web/top/login?logout=true')


################################################
def auth(request):
    """
    [メソッド概要]
      ログイン認証処理
    [引数]
      なし
    [戻り値]
      HTTPレスポンス情報
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    msg = ''
    redirect_url = ''

    login_id = ''
    password = ''

    now = None

    try:
        # 認証情報の取得
        if request.method != 'POST':
            logger.user_log('LOSM13006', request=request)
            raise OASELoginError('MOSJA10001')

        login_id = request.POST.get('login_id', None)
        password = request.POST.get('password', None)

        # 認証情報のチェック
        _check_input_auth_info(login_id, password, request)

        # 認証に使用するバックエンドクラスの判定
        enable_ad      = getattr(settings, 'ENABLE_ACTIVEDIRECTORY', False)
        oase_auth_list = getattr(settings, 'OASE_AUTH_LIST', [])

        backend  = OASEAuthBackend()
        if enable_ad and login_id not in oase_auth_list:
            adcollabo_config = System.objects.get(config_id='ADCOLLABORATION').value
            if adcollabo_config != '0':
                backend = ActiveDirectoryAuthBackend()

        # 認証
        user = backend.authenticate(request, login_id, password)
        if not user:
            logger.user_log('LOSM13010', request=request)
            raise OASELoginError('MOSJA10010')

        auth_login(request, user, backend=backend.full_name)

        # セッションタイムアウト時間の設定
        timeout_val = _get_value_session_timeout()
        now = datetime.datetime.now(pytz.timezone('UTC'))
        request.session['cookie_age'] = (now + timedelta(minutes=timeout_val)).strftime('%Y-%m-%d %H:%M:%S')

        # 個人設定情報の取得
        lang = user.get_lang_mode()
        request.session[LANGUAGE_SESSION_KEY] = lang.lower()

        # ログイン後遷移ページのURLを設定
        redirect_url = _get_url_after_login(request)


    except User.DoesNotExist:
        logger.logic_log('LOSM13011', login_id, request=request)
        msg = 'MOSJA10005'

    except OASELoginError as e:
        logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
        msg = e.msg_id

    except Exception as e:
        logger.logic_log('LOSM00001', traceback.format_exc(), request=request)
        redirect_url = ''
        if not msg:
            logger.logic_log('LOSM13012', request=request)
            msg = 'MOSJA10011'

    # ログインログの操作
    ipaddr = get_client_ipaddr(request)
    _ipaddr_login_log(request, ipaddr, login_id, True if not msg else False, now)

    # 遷移先ページへ移動
    if redirect_url:
        return redirect(redirect_url)

    ad_collabo = int(System.objects.get(config_id='ADCOLLABORATION').value)

    pass_init_url = reverse('web_app:top:pass_initialize') + '?' + reverse('web_app:top:login')

    data = {
        'msg'       : msg,
        'logout'    : False,
        'ad_collabo': ad_collabo,
        'pass_init_url' : pass_init_url,
        'lang_mode'     : 'JA',
    }

    logger.logic_log('LOSI00002', 'None', request=request)

    return render(request, 'top/login.html', data)


################################################
@check_allowed_ad(settings.LOGIN_REDIRECT_URL)
def pass_ch(request):

    logger.logic_log('LOSI00001', 'None', request=request)

    pass_gen = ''
    pass_con = 'passch'  # 判定の何にもひっかからなければ通常のパスワード変更

    try:
        system = System.objects.get(config_id='Pass_generate_manage')
        pass_gen = int(system.value)

        password_last_modified = request.user.password_last_modified
        last_login = request.user.last_login

        # (初期パスワードまたはワンタイムパスワード用の) パスワード有効期限がある場合
        if request.user.password_expire is not None:

            # パスワード最終更新日時がある場合はワイタイムパスワード
            if password_last_modified is not None:
                pass_con = 'onetime'

            # パスワード最終更新日時がない場合は初期パスワード
            else:
                pass_con = 'initial'

        # 正規パスワードの有効期間のチェック
        else:
            # パスワード有効期間情報取得
            lifetime_val = int(System.objects.get(config_id='Pass_Valid_Period').value)

            pass_con = check_life_time_and_set_pass(lifetime_val, password_last_modified, last_login, pass_con)

    except Exception as e:
        logger.logic_log('LOSI00005', traceback.format_exc(), request=request)

    pass_init_url = reverse('web_app:top:pass_initialize') + '?' + reverse('web_app:top:pass_ch')

    data = {
        'uid'           : request.user.user_id,
        'loginId'       : request.user.login_id,
        'passGen'       : pass_gen,
        'passCon'       : pass_con,
        'mainmenu_list' : request.user_config.get_menu_list(),
        'user_name'     : request.user.user_name,
        'pass_init_url' : pass_init_url,
        'lang_mode'     : 'JA',
    }

    data_for_log = {key: value for key, value in data.items() if key != 'mainmenu_list'}

    logger.logic_log('LOSI00002', 'data=%s' % data_for_log, request=request)

    return render(request, 'top/pass_ch.html', data)


################################################
def check_life_time_and_set_pass(lifetime_val, password_last_modified, last_login, pass_con):
    """
    [概要]
    正規パスワードの有効期間情報を検証し、
    値に応じたパス文字列を返却します。
    """
    # パスワード有効期間が設定されている場合のみチェック処理を実施
    if lifetime_val > 0:
        # パスワード最終更新日時がある場合
        if password_last_modified is None or last_login is None:
            pass_con = 'period'
        else:
            # パスワード最終更新日時から一定期間を超過している場合、パスワード変更画面へ遷移
            valid_period = password_last_modified + timedelta(days=lifetime_val)
            if last_login > valid_period:
                pass_con = 'period'
    return pass_con


################################################
def pass_ch_logout(request):

    logger.logic_log('LOSI00001', 'None', request=request)

    auth_logout(request)

    request.session.clear()
    request.session.flush()

    logger.logic_log('LOSI00002', 'None', request=request)

    return redirect('/oase_web/top/login')

################################################
def pass_initialize(request):

    logger.logic_log('LOSI00001', 'None', request=request)

    login_id = ''
    oase_auth_list = getattr(settings, 'OASE_AUTH_LIST', [])

    if request.user.is_authenticated:
        login_id = request.user.login_id

    if login_id not in oase_auth_list:
        ad_collabo = int(System.objects.get(config_id='ADCOLLABORATION').value)
        # AD連携していたら403
        if ad_collabo > 0:
            logger.user_log('LOSM13022', 'ADCOLLABORATION :%s' % ad_collabo, request=request)
            return HttpResponseRedirect(reverse('web_app:top:notpermitted'))

    query_str_list = request.get_full_path().split('?')
    redirect_url = query_str_list[1] # 取れなければ開発時エラー

    data = {
        'passInit'      : int(System.objects.get(config_id='INITIAL_PASS_VALID_PERIOD').value),
        'msg'           : '',
        'logout'        : '',
        'ad_collabo'    : '',
        'redirect_url'  : redirect_url,
        'lang_mode'     : 'JA',
    }

    logger.logic_log('LOSI00002', 'None', request=request)

    return render(request,'top/pass_initialize.html', data)
