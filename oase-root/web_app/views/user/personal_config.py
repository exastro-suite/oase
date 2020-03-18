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
    個人設定の画面コントローラ

"""

import re
import json
import traceback
import pytz
import datetime

from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseServerError
from django.conf import settings
from django.views.decorators.http import require_POST
from django.urls import reverse

from libs.commonlibs import define as defs
from libs.commonlibs.oase_logger import OaseLogger
from libs.commonlibs.common import Common as OaseCommon
from libs.webcommonlibs.decorator import *
from libs.webcommonlibs.oase_exception import OASEError
from libs.webcommonlibs.oase_mail import OASEMailSMTP, OASEMailModifyMailAddressNotify
from web_app.models.models import System, User, MailAddressModify
from web_app.templatetags.common import get_message

from web_app.serializers.unicode_check import UnicodeCheck

logger = OaseLogger.get_instance() # ロガー初期化


################################################
def personal_config(request):

    pass_init_url = reverse('web_app:top:pass_initialize') + '?' + reverse('web_app:user:personal_config')

    password_generation = int(System.objects.get(config_id='Pass_generate_manage').value)

    data = {
        'title'        : '【OASE】個人設定',
        'page_name'    : '個人設定',
        'username'     : request.user.user_name,
        'login_id'     : request.user.login_id,
        'mail_address' : request.user.mail_address,
        'pass_init_url' : pass_init_url,
        'password_generation' : password_generation,
        'lang_mode_id' : request.user.lang_mode_id,
        'disp_mode_id' : request.user.disp_mode_id,
        'langlist'     : defs.LANG_MODE.LIST_ALL,
        'displist'     : defs.DISP_MODE.LIST_ALL,
        'mainmenu_list': request.user_config.get_menu_list(),
        'ad_flag': True if request.session['_auth_user_backend'].endswith('ActiveDirectoryAuthBackend') else False,
        'user_name'    : request.user.user_name,
        'lang_mode'    : request.user.get_lang_mode(),
    }

    return render(request, 'user/personal_config.html', data)


################################################
@check_allowed_ad(settings.LOGIN_REDIRECT_URL)
@require_POST
def modify_mailaddr(request):
    """
    [メソッド概要]
      メールアドレス変更処理
    """

    msg = {}
    error_msg  = {}
    result = 'success'

    now = datetime.datetime.now(pytz.timezone('UTC'))

    mail_pass = request.POST.get('password', '')
    mail_addr = request.POST.get('mail', '')
    uid = request.user.user_id
    login_id  = request.user.login_id
    emo_chk   = UnicodeCheck()

    logger.logic_log('LOSI00001', mail_pass, mail_addr, request=request)

    if uid == '':
        error_msg = get_message('MOSJA32009', request.user.get_lang_mode())
        logger.user_log('LOSM17000')
        return HttpResponseServerError(error_msg)

    try:

        # パスワードチェック
        error_msg = _check_password(request, mail_pass, uid)

        # 値チェック
        if mail_addr == request.user.mail_address:
            error_msg['txtMailAddr'] = get_message('MOSJA31008', request.user.get_lang_mode())
            logger.user_log('LOSI10001', login_id, mail_addr, request=request)
            logger.logic_log('LOSM10000', request=request)

        # バリデーションチェック
        dot_string = r'[\w!#$%&\'*+\-\/=?^`{|}~]+(\.[\w!#$%&\'*+\-\/=?^`{|}~]+)*'
        quoted_string = r'"([\w!#$%&\'*+\-\/=?^`{|}~. ()<>\[\]:;@,]|\\[\\"])+"'
        domain = r'([a-zA-Z\d\-]+\.)+[a-zA-Z]+'
        ip_v4 = r'(\d{1,3}(\.\d{1,3}){3}'
        ip_v6 = r'IPv6:[\da-fA-F]{0,4}(:[\da-fA-F]{0,4}){1,5}(:\d{1,3}(\.\d{1,3}){3}|(:[\da-fA-F]{0,4}){0,2}))'
        mail_ip_addr = r'\[' + ip_v4 + r'|' + ip_v6 + r'\]'

        mail_pattern = r'^(' + dot_string + r'|' + quoted_string + \
            r')@(' + domain + r'|' + mail_ip_addr + r')$'

        if len(mail_addr) <= 0:
            error_msg['txtMailAddr'] = get_message('MOSJA31004', request.user.get_lang_mode())
            logger.user_log('LOSI10002', request=request)
            logger.logic_log('LOSM10000', request=request)

        elif len(mail_addr) > 256:
            error_msg['txtMailAddr'] = get_message('MOSJA31005', request.user.get_lang_mode())
            logger.user_log('LOSI10003', request=request)
            logger.logic_log('LOSM10000', request=request)

        # 絵文字チェック
        value_list = emo_chk.is_emotion(mail_addr)
        if len(value_list) > 0:
            error_msg['txtMailAddr'] = get_message('MOSJA31018', request.user.get_lang_mode())
            logger.user_log('LOSI10011', request=request)
            logger.logic_log('LOSM10000', request=request)

        elif not re.match(mail_pattern, mail_addr):
            error_msg['txtMailAddr'] = get_message('MOSJA31006', request.user.get_lang_mode())
            logger.user_log('LOSI10004', request=request)
            logger.logic_log('LOSM10000', request=request)

        # 機密情報URL生成
        req_protcol = request.scheme
        req_host    = request.get_host()
        modify_url  = reverse('web_app:user:user_determ_mailaddr')
        hash_login  = OaseCommon.oase_hash(login_id)
        hash_maddr  = OaseCommon.oase_hash(mail_addr)
        modify_url  = '%s://%s%s?arg=%s&tok=%s' % (req_protcol, req_host, modify_url, hash_login, hash_maddr)

        # 重複チェック
        error_msg = _check_duplication(request, error_msg, mail_addr, now, login_id)

        # DB保存
        hour_expire = int(System.objects.get(config_id='MAILADDR_URL_VALID_PERIOD').value)
        url_expire  = now + datetime.timedelta(hours=hour_expire)

        rcnt = MailAddressModify.objects.filter(login_id=login_id, login_id__contains=login_id).count()
        if rcnt > 0:
            MailAddressModify.objects.filter(login_id=login_id, login_id__contains=login_id).update(
                mail_address          = mail_addr,
                mail_address_hash     = hash_maddr,
                url_expire            = url_expire,
                last_update_timestamp = now,
                last_update_user      = request.user.user_name
            )

        else:
            MailAddressModify(
                login_id              = login_id,
                mail_address          = mail_addr,
                mail_address_hash     = hash_maddr,
                url_expire            = url_expire,
                last_update_timestamp = now,
                last_update_user      = request.user.user_name
            ).save(force_insert=True)

        if len(error_msg) == 0:
            # 署名用URL生成
            req_protcol = request.scheme
            req_host    = request.get_host()
            login_url   = reverse('web_app:top:login')
            inquiry_url = reverse('web_app:top:inquiry')
            login_url   = '%s://%s%s' % (req_protcol, req_host, login_url)
            inquiry_url = '%s://%s%s' % (req_protcol, req_host, inquiry_url)

            # メール送信
            obj_smtp = OASEMailSMTP(request=request)
            obj_mail = OASEMailModifyMailAddressNotify(
                mail_addr, request.user.user_name, hour_expire, modify_url, inquiry_url, login_url)

            send_result = obj_smtp.send_mail(obj_mail)
            if send_result:
                error_msg['system'] = get_message(send_result, request.user.get_lang_mode())
                logger.user_log('LOSI10006', request=request)
                logger.logic_log('LOSM10000', request=request)

    except Exception as e:
        logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
        error_msg['system'] = get_message('MOSJA31014', request.user.get_lang_mode())


    if len(error_msg) > 0:
        result = 'failure'
    else:
        msg['system'] = get_message('MOSJA31017', request.user.get_lang_mode())

    data = {
        'status' : result,
        'msg'    : msg,
        'error_msg'    : error_msg,
    }

    respdata = json.dumps(data)

    logger.logic_log('LOSI00002', result, request=request)

    return HttpResponse(respdata, content_type="application/json")


################################################
def determ_mailaddr(request):
    """
    [メソッド概要]
      メールアドレス変更確定処理
    """

    msg = ''

    now = datetime.datetime.now(pytz.timezone('UTC'))

    hash_login = request.GET.get('arg', None)
    hash_maddr = request.GET.get('tok', None)

    logger.logic_log('LOSI00001', hash_maddr)


    try:
        login_id   = ''
        mail_addr  = ''

        # パラメーター不正
        if not hash_login or not hash_maddr:
            logger.user_log('LOSM10002', hash_login, hash_maddr)
            raise OASEError('MOSJA31009', 'LOSM10000')

        # メールアドレス変更情報取得
        login_id, mail_addr = _reverse_conv_login_id_mailaddr(hash_login, hash_maddr, now)

        # 重複チェック
        rcnt = User.objects.filter(mail_address=mail_addr, mail_address__contains=mail_addr).exclude(
            login_id=login_id, login_id__contains=login_id).count()
        if rcnt > 0:
            logger.logic_log('LOSI10005', mail_addr)
            raise OASEError('MOSJA31011', 'LOSM10000')

        # メールアドレス変更
        user = User.objects.get(login_id=login_id, login_id__contains=login_id)
        if mail_addr == user.mail_address:
            logger.logic_log('LOSI10001', login_id, mail_addr)
            msg = get_message('MOSJA31012')

        else:
            logger.logic_log('LOSI10010', login_id, user.mail_address, mail_addr)
            user.mail_address = mail_addr
            user.save(force_update=True)
            msg = get_message('MOSJA31013')

    except OASEError as e:
        if e.log_id:
            logger.logic_log(e.log_id)

        if e.msg_id:
            if e.arg_dict:
                msg = get_message(e.msg_id, e.arg_dict)

            else:
                msg = get_message(e.msg_id)

    except Exception as e:
        result = 'error'
        logger.logic_log('LOSI00005', traceback.format_exc())
        msg = get_message('MOSJA31015')

    logger.logic_log('LOSI00002', msg)

    data = {
        'msg'           : msg,
        'lang_mode'     : user.get_lang_mode(),
    }

    return render(request, 'user/determ_mailaddr.html', data)


################################################
def _check_password(request, mail_pass, uid):
    """
    [メソッド概要]
      パスワードチェック
    """
    error_msg  = {}

    if len(mail_pass) <= 0:
        error_msg['mailPw'] = get_message('MOSJA10004', request.user.get_lang_mode())
        logger.user_log('LOSI10012', request=request)
        logger.logic_log('LOSM17015', request=request)

    else:
        password_hash = OaseCommon.oase_hash(mail_pass)

        user = User.objects.get(user_id=uid)

        if not user:
            error_msg['mailPw'] = get_message('MOSJA32010', request.user.get_lang_mode())
            logger.user_log('LOSI10013', request=request)
            logger.logic_log('LOSM17001', request=request)

        if user and user.password != password_hash:
            error_msg['mailPw'] = get_message('MOSJA32038', request.user.get_lang_mode())
            logger.user_log('LOSI10013', request=request)
            logger.logic_log('LOSM17016', request=request)

    return error_msg


################################################
def _check_duplication(request, error_msg, mail_addr, now, login_id):
    """
    [メソッド概要]
      重複チェック
    """
    rcnt = User.objects.filter(
        mail_address=mail_addr, mail_address__contains=mail_addr).count()
    if rcnt > 0:
        error_msg['txtMailAddr'] = get_message(
            'MOSJA31007', request.user.get_lang_mode())
        logger.user_log('LOSI10005', mail_addr, request=request)
        logger.logic_log('LOSM10000', request=request)

    rcnt = MailAddressModify.objects.filter(mail_address=mail_addr,
                                            mail_address__contains=mail_addr,
                                            url_expire__gte=now).exclude(
        login_id=login_id, login_id__contains=login_id).count()
    if rcnt > 0:
        error_msg['txtMailAddr'] = get_message(
            'MOSJA31007', request.user.get_lang_mode())
        logger.user_log('LOSI10006', request=request)
        logger.logic_log('LOSM10000', request=request)

    return error_msg


################################################
def _reverse_conv_login_id_mailaddr(hash_login, hash_maddr, now):
    """
    [メソッド概要]
      メールアドレス変更情報取得処理
    """
    rset = MailAddressModify.objects.filter(mail_address_hash=hash_maddr).values(
        'login_id', 'mail_address', 'url_expire')

    for r in rset:
        login_id = r['login_id']
        hash_login_db = OaseCommon.oase_hash(login_id)

        if hash_login == hash_login_db:
            logger.user_log('LOSI10007', login_id, r['mail_address'])

            # 有効期限チェック
            if now >= r['url_expire']:
                logger.logic_log('LOSI10008', now, r['url_expire'])
                raise OASEError('MOSJA31016', 'LOSM10000')

            mail_addr = r['mail_address']
            return login_id, mail_addr

    # メールアドレス変更情報取得失敗
    else:
        logger.user_log('LOSI10009', hash_maddr)
        raise OASEError('MOSJA31010', 'LOSM10000')
