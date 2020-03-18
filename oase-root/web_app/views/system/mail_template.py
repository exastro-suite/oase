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
  メールテンプレートページの表示処理
  また、メールテンプレートからのリクエスト受信処理

[引数]
  HTTPリクエスト

[戻り値]
  HTTPレスポンス

"""
import json
import datetime
import traceback
import pytz

from django.shortcuts import render
from django.http import HttpResponse
from django.db import transaction
from django.views.decorators.http import require_POST
from django.http import Http404

from libs.commonlibs import define as defs
from libs.commonlibs.oase_logger import OaseLogger
from libs.webcommonlibs.decorator import *
from libs.webcommonlibs.common import Common

from web_app.models.models import MailTemplate
from web_app.templatetags.common import get_message
from web_app.views.forms.mail_form import MailTemplateForm

MENU_ID = 2141002007
logger = OaseLogger.get_instance()  # ロガー初期化


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_EVERY)
def index(request):
    """
    [メソッド概要]
      メールテンプレートページの一覧画面
    """

    logger.logic_log('LOSI00001', 'user_id: %s' % (request.user.user_id))

    permission_type = request.user_config.get_menu_auth_type(MENU_ID)
    editable_user = True if permission_type == defs.ALLOWED_MENTENANCE else False

    msg = ''
    mail_list   = []

    try:
        mail_list = _select()

    except Exception as e:
        logger.logic_log('LOSI00005', traceback.format_exc())
        msg = 'データの取得に失敗しました'

    data = {
        'mainmenu_list': request.user_config.get_menu_list(),
        'msg': msg,
        'editable_user': editable_user,
        'mail_list': mail_list,
        'user_name': request.user.user_name,
        'lang_mode': request.user.get_lang_mode(),
    }

    logger.logic_log('LOSI00002', 'user_id: %s, mail_list count: %s' % (request.user.user_id, len(mail_list)))

    return render(request, 'system/mail.html', data)


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def create(request):
    """
    [メソッド概要]
    メールテンプレートの新規作成
    """

    logger.logic_log('LOSI00001', 'user_id: %s' % (request.user.user_id))
    error_msg = ''
    error_flag = False
    lang = request.user.get_lang_mode()

    try:
        with transaction.atomic():
            # json形式判定
            json_str = json.loads(request.POST.get('json_str', '{}'))
            logger.user_log('LOSI16003', "json_str", json_str)
            if 'json_str' not in json_str:
                logger.user_log('LOSM16001', 'json_str', 'user_id: %s' % (request.user.user_id))
                raise Http404

            rq = json_str['json_str']
            data = {
                'mail_template_name': rq.get('mail_template_name', ''),
                'subject': rq.get('subject', ''),
                'content': rq.get('content', ''),
                'destination': rq.get('destination', ''),
                'cc': rq.get('cc', ''),
                'bcc': rq.get('bcc', ''),
            }
            f = MailTemplateForm(data, auto_id=False)

            # 入力値チェック
            if len(f.errors.items()):
                error_msg = {}
                for content, validate_list in f.errors.items():
                    error_msg[content] = '\n'.join([get_message(v, lang) for v in validate_list])
                response_json = json.dumps({
                    'status': 'failure',
                    'error_msg': error_msg,
                })
                logger.user_log('LOSM05004', 'error_msg: %s' % error_msg, request=request)
                logger.logic_log('LOSI00002', 'json_str: %s' % json_str, request=request)

                return HttpResponse(response_json, content_type="application/json")

            MailTemplate(
                mail_template_name=f.cleaned_data['mail_template_name'],
                subject=f.cleaned_data['subject'],
                content=f.cleaned_data['content'],
                destination=f.cleaned_data['destination'],
                cc=f.cleaned_data['cc'],
                bcc=f.cleaned_data['bcc'],
                last_update_user=request.user.user_name,
                last_update_timestamp=datetime.datetime.now(pytz.timezone('UTC')),
            ).save(force_insert=True)


    except Exception as e:
        error_flag = True
        logger.logic_log('LOSI00005', traceback.format_exc())
        error_msg = get_message('MOSJA24015', request.user.get_lang_mode())

    # 結果レスポンス
    response_data = {'status': 'success'}

    if error_flag:
        response_data['status'] = 'failure'
        response_data['error_msg'] = error_msg

    response_json = json.dumps(response_data)

    logger.logic_log('LOSI00002', 'response_json: %s' % (response_json), request=request)
    return HttpResponse(response_json, content_type="application/json")


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def update(request):
    """
    [メソッド概要]
      メールテンプレートの更新
    """

    logger.logic_log('LOSI00001', 'user_id: %s' % (request.user.user_id))

    uid = request.user.user_id
    error_flag = False
    lang = request.user.get_lang_mode()

    try:
        with transaction.atomic():
            # json形式判定
            json_str = json.loads(request.POST.get('json_str', '{}'))
            logger.user_log('LOSI16003', "json_str", json_str)
            if 'json_str' not in json_str:
                logger.user_log('LOSM16001', 'json_str', uid)
                raise Http404

            rq = json_str['json_str']
            data = {
                'pk': rq['template_id'],
                'mail_template_name': rq.get('mail_template_name', ''),
                'subject': rq.get('subject', ''),
                'content': rq.get('content', ''),
                'destination': rq.get('destination', ''),
                'cc': rq.get('cc', ''),
                'bcc': rq.get('bcc', ''),
            }
            f = MailTemplateForm(data)

            # 入力値チェック
            if len(f.errors.items()):
                error_msg = {}
                for content, validate_list in f.errors.items():
                    error_msg[content] = '\n'.join([get_message(v, lang) for v in validate_list])
                response_json = json.dumps({
                    'status': 'failure',
                    'error_msg': error_msg,
                })
                logger.user_log('LOSM05004', 'error_msg: %s' % error_msg, request=request)
                logger.logic_log('LOSI00002', 'json_str: %s' % json_str, request=request)

                return HttpResponse(response_json, content_type="application/json")

            # 更新レコード取得 更新
            mail_mod = MailTemplate.objects.select_for_update().get(pk=rq['template_id'])
            mail_mod.mail_template_name = f.cleaned_data['mail_template_name']
            mail_mod.subject = f.cleaned_data['subject']
            mail_mod.content = f.cleaned_data['content']
            mail_mod.destination = f.cleaned_data['destination']
            mail_mod.cc = f.cleaned_data['cc']
            mail_mod.bcc = f.cleaned_data['bcc']
            mail_mod.last_update_user = request.user.user_name
            mail_mod.last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC'))
            mail_mod.save(force_update=True)

    except MailTemplate.DoesNotExist:
        error_flag = True
        error_msg = get_message('MOSJA24001', request.user.get_lang_mode())
        logger.user_log('LOSM16002', request=request)
    except Exception as e:
        error_flag = True
        error_msg = get_message('MOSJA24015', request.user.get_lang_mode())
        logger.logic_log('LOSI00005', traceback.format_exc())

    # 結果レスポンス
    response_data = {'status' : 'success'}

    if error_flag:
        response_data['status'] = 'failure'
        response_data['error_msg'] = error_msg

    response_json = json.dumps(response_data)

    logger.logic_log('LOSI00002', 'response_json: %s' % (response_json), request=request)

    return HttpResponse(response_json, content_type="application/json")


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def delete(request):
    """
    [メソッド概要]
      メールテンプレートの削除
    """
    logger.logic_log('LOSI00001', 'user_id: %s' % (request.user.user_id))

    error_flag = False
    uid = request.user.user_id
    template_id = 0

    try:
        with transaction.atomic():
            # json形式判定
            template_id = request.POST.get('template_id', None)
            logger.user_log('LOSI16003', "template_id", template_id)
            if template_id is None:
                logger.user_log('LOSM16001', 'template_id', uid)
                raise Http404

            # レコード削除
            MailTemplate.objects.get(pk=template_id).delete()

    except MailTemplate.DoesNotExist:
        error_flag = True
        logger.user_log('LOSM16002', request=request)

    except Exception as e:
        error_flag = True
        logger.logic_log('LOSI00005', traceback.format_exc())

    # 結果レスポンス
    response_data = {'status': 'success'}

    if error_flag:
        response_data['status'] = 'failure'

    response_json = json.dumps(response_data)

    logger.logic_log('LOSI00002', 'response_json: %s' % (response_json), request=request)

    return HttpResponse(response_json, content_type="application/json")


def _select(filters={}):
    """
    [メソッド概要]
      グループのデータ取得
    """

    logger.logic_log('LOSI00001', 'filters: %s' % (filters))

    where_info = {}

    Common.convert_filters(filters, where_info)
    mail_list = MailTemplate.objects.filter(**where_info)

    logger.logic_log('LOSI00002', 'mail_list: %s' % mail_list)

    return mail_list
