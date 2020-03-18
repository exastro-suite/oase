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
    ブラックリスト画面のコントローラ

"""

import json
import traceback
import re
import datetime
import pytz

from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models.aggregates import Count
from django.conf import settings

from libs.commonlibs import define as defs
from libs.commonlibs.oase_logger import OaseLogger

from libs.webcommonlibs.common import Common, set_wild_iterate

from web_app.models.models import BlackListIPAddress
from web_app.templatetags.common import get_message
from web_app.views.user.locked_user import has_permission_user_auth

logger = OaseLogger.get_instance()  # ロガー初期化

################################################


def black_list(request):
    """
    [メソッド概要]
      ブラックリスト一覧表示
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    # システム設定のメール通知種別に入っていない場合権限なしページへ
    if not has_permission_user_auth(request):
        return HttpResponseRedirect(reverse('web_app:top:notpermitted'))

    black_ipaddr_list = BlackListIPAddress.objects.all().values_list(
        'ipaddr', flat=True).annotate(cnt=Count("*"))

    black_list = []
    for b_ip in black_ipaddr_list:
        recent_record = list(BlackListIPAddress.objects.filter(
            ipaddr=b_ip).order_by('black_list_id').reverse()[:1])[0]

        if recent_record.release_timestamp == None:
            black_list.append(recent_record)

    disabled_flag = getattr(settings, 'DISABLE_WHITE_BLACK_LIST', False)

    data = {
        'edit_mode': False,
        'black_list': black_list,
        'mainmenu_list': request.user_config.get_menu_list(),
        'user_name': request.user.user_name,
        'lang_mode': request.user.get_lang_mode(),
        'disabled_flag': disabled_flag,
    }

    logger.logic_log('LOSI00002', 'black_list count: %s, disabled_flag: %s' % (
        len(black_list), disabled_flag), request=request)

    return render(request, 'user/black_list_disp.html', data)

################################################
@require_POST
def edit(request):
    """
    [メソッド概要]
      ブラックリストの編集画面
    """

    msg = ''

    logger.logic_log('LOSI00001', 'None', request=request)

    try:
        # IPリスト情報取得
        filters = request.POST.get('filters', None)
        filters = json.loads(filters)

        black_list = _getBlackListData(filters, request=request)

    except:
        msg = get_message('MOSJA24001', request.user.get_lang_mode())
        logger.logic_log('LOSM19000', 'traceback: %s' %
                         traceback.format_exc(), request=request)
        raise Http404

    data = {
        'msg': msg,
        'black_list': black_list,
        'opelist_non': defs.DABASE_OPECODE.OPELIST_MOD[0],
        'opelist_up': defs.DABASE_OPECODE.OPELIST_MOD[1],
        'opelist_del': {'k': '無効', 'v': defs.DABASE_OPECODE.OPE_DELETE},
        'mainmenu_list': request.user_config.get_menu_list(),
        'edit_mode': True,
        'user_name': request.user.user_name,
        'lang_mode': request.user.get_lang_mode(),
    }

    logger.logic_log('LOSI00002', 'black_list: %s' %
                     black_list, request=request)
    return render(request, 'user/black_list_edit.html', data)

################################################


def _getBlackListData(filters, request=None):
    """
    [メソッド概要]
      データ更新処理
    [引数]
      request :logger.logic_logでuserId sessionIDを表示するために使用する
    [戻り値]
      ip_list
    """

    logger.logic_log('LOSI00001', 'filters: %s' % filters, request=request)

    # リスト表示用
    where_info = {
        'release_timestamp': None
    }
    Common.convert_filters(filters, where_info)

    # フィルタ情報によるデータ抽出
    black = BlackListIPAddress.objects.filter(**where_info)

    # 抽出結果を画面表示用に整形
    black_list = []
    for b in black:
        black_list_info = {
            'black_list_id': b.black_list_id,
            'ipaddr': b.ipaddr,
            'release_timestamp': b.release_timestamp,
            'manual_reg_flag': b.manual_reg_flag,
            'upd_user': b.last_update_user,
            'updated': b.last_update_timestamp,
        }
        black_list.append(black_list_info)

    logger.logic_log('LOSI00002', 'black_list: %s' %
                     len(black_list), request=request)

    return black_list

################################################
@require_POST
def modify(request):
    """
    [メソッド概要]
      データ更新処理
    """

    msg = ''
    error_msg = {}
    error_flag = False
    json_str_list = []
    now = datetime.datetime.now(pytz.timezone('UTC'))
    json_str = request.POST.get('json_str', '{}')

    logger.logic_log('LOSI00001', 'json_str: %s' % json_str, request=request)

    try:
        with transaction.atomic():
            json_str = json.loads(json_str)

            # バリデーションチェック
            error_flag, error_msg, json_str_list = _validate(
                json_str, request=request)

            if error_flag:
                raise Exception('validation error.')

            ip_address_list_reg = []
            for rq in sorted(json_str_list, key=lambda x: x['row_id']):
                ope = int(rq['ope'])

                # 更新
                if ope == defs.DABASE_OPECODE.OPE_UPDATE:
                    ip_address_list_mod = BlackListIPAddress.objects.select_for_update().get(
                        black_list_id=rq['row_id'])

                    # IPアドレス更新の場合、更新前IPアドレスの「無効」レコードと、更新後IPアドレスの「有効」レコードを作成する。
                    # 更新前IPアドレスの「無効」レコード
                    ipaddress_info_before = BlackListIPAddress(
                        ipaddr=ip_address_list_mod.ipaddr,
                        release_timestamp=now,
                        manual_reg_flag=True,  # 手動登録
                        last_update_user=request.user.user_name,
                        last_update_timestamp=ip_address_list_mod.last_update_timestamp
                    )
                    ip_address_list_reg.append(ipaddress_info_before)

                    # 更新後IPアドレスの「有効」レコード
                    ipaddress_info_after = BlackListIPAddress(
                        ipaddr=rq['ipaddr'],
                        release_timestamp=None,
                        manual_reg_flag=True,  # 手動登録
                        last_update_user=request.user.user_name,
                        last_update_timestamp=now
                    )
                    ip_address_list_reg.append(ipaddress_info_after)

                # 無効対象の保存
                elif ope == defs.DABASE_OPECODE.OPE_DELETE:
                    # 自動/手動判定用
                    black_ipaddr = BlackListIPAddress.objects.select_for_update().get(
                        black_list_id=rq['row_id'])

                    ipaddress_info = BlackListIPAddress(
                        ipaddr=rq['ipaddr'],
                        release_timestamp=now,
                        manual_reg_flag=black_ipaddr.manual_reg_flag,
                        last_update_user=request.user.user_name,
                        last_update_timestamp=black_ipaddr.last_update_timestamp
                    )
                    ip_address_list_reg.append(ipaddress_info)

                # 新規追加対象の保存
                elif ope == defs.DABASE_OPECODE.OPE_INSERT:
                    ipaddress_info = BlackListIPAddress(
                        ipaddr=rq['ipaddr'],
                        release_timestamp=None,
                        manual_reg_flag=True,  # 手動登録
                        last_update_user=request.user.user_name,
                        last_update_timestamp=now
                    )
                    ip_address_list_reg.append(ipaddress_info)

            # 追加
            reg_count = len(ip_address_list_reg)
            if reg_count > 1:
                BlackListIPAddress.objects.bulk_create(ip_address_list_reg)

            elif reg_count == 1:
                blacklist = ip_address_list_reg[0]
                blacklist.save(force_insert=True)

    except BlackListIPAddress.DoesNotExist:
        error_flag = True
        logger.logic_log('LOSM19006', traceback.format_exc(), request=request)

    except Exception as e:
        error_flag = True
        logger.logic_log('LOSM19004', 'json_str: %s, traceback: %s' % (
            json_str, traceback.format_exc()), request=request)

    # 結果レスポンス
    response_data = {}

    # 異常処理
    if error_flag == True:
        response_data['status'] = 'failure'
        response_data['error_msg'] = error_msg
        response_data['msg'] = msg
        logger.logic_log('LOSM19005', 'json_str: %s, response_data: %s, traceback: %s' % (
            json_str, response_data, traceback.format_exc()), request=request)

    # 正常処理
    else:
        response_data['status'] = 'success'
        response_data['redirect_url'] = '/oase_web/user/black_list'

    response_json = json.dumps(response_data)

    logger.logic_log('LOSI00002', 'json_str: %s, response_json: %s' %
                     (json_str, response_json), request=request)
    return HttpResponse(response_json, content_type="application/json")


################################################
def _validate(json_str, request=None):
    """
    [メソッド概要]
      入力チェック
    [引数]
      request :logger.logic_logでuserId sessionIDを表示するために使用する
    [戻り値]
      error_flag
      error_msg
      json_str_list
    """

    error_flag = False
    error_msg = {}
    chk_iplist = []
    json_str_list = []

    logger.logic_log('LOSI00001', 'json_str: %s' % json_str, request=request)

    ipAddr_pattern = r'^(([\*]|[1-9]?[0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.){3}([1-9]?[\*0-9]|1[0-9][\*0-9]|2[0-4][\*0-9]|25[\*0-5])$'
    ipAddr_repatter = re.compile(ipAddr_pattern)

    # jsonの形式チェック
    if {'insertInfo', 'updateInfo', 'delInfo'} != set(list(json_str.keys())):
        logger.user_log('LOSM19000', request=request)
        raise TypeError('json_strの形式不正')

    # 削除
    for rq in json_str['delInfo']:
        delete_info = {}

        # 削除時にIPアドレスが更新されていた場合はエラーとする
        black_ipaddr = BlackListIPAddress.objects.select_for_update().get(
            black_list_id=rq['row_id'])
        if black_ipaddr.ipaddr != rq['ipaddr']:
            error_flag = True
            error_msg[rq['row_id']] += get_message('MOSJA34010', request.user.get_lang_mode(), showMsgId=False) + '\n'
            logger.user_log('LOSM19002', 'ipaddr', request=request)
            continue

        delete_info['ope'] = defs.DABASE_OPECODE.OPE_DELETE
        delete_info['ipaddr'] = rq['ipaddr']
        delete_info['row_id'] = rq['row_id']
        json_str_list.append(delete_info)

    # 追加
    status = defs.DABASE_OPECODE.OPE_INSERT
    json_str_list, error_msg, error_flag = _check_blacklist_data(
        json_str['insertInfo'], json_str_list, error_msg, request, error_flag, ipAddr_repatter, chk_iplist, status)

    # 更新
    status = defs.DABASE_OPECODE.OPE_UPDATE
    json_str_list, error_msg, error_flag = _check_blacklist_data(
        json_str['updateInfo'], json_str_list, error_msg, request, error_flag, ipAddr_repatter, chk_iplist, status)

    logger.logic_log('LOSI00002', 'error_flag: %s' % error_flag, request=request)

    return error_flag, error_msg, json_str_list


def _check_blacklist_data(json_info, json_str_list, error_msg, request, error_flag, ipAddr_repatter, chk_iplist, status):
    """
    [メソッド概要]
    追加、変更時の詳細入力チェック
    """
    for rq in json_info:
        json_str_dic = {}
        error_msg[rq['row_id']] = ''

        # IPアドレスチェック
        continue_flg, error_msg, rq, error_flag = _check_rq_ipaddr(
            request, rq, error_flag, error_msg, ipAddr_repatter)
        if continue_flg:
            continue

        # 重複チェック
        if rq['ipaddr'] in chk_iplist:
            error_flag = True
            error_msg[rq['row_id']] += get_message('MOSJA34006', request.user.get_lang_mode(), showMsgId=False) + '\n'
            logger.user_log('LOSM19003', 'ipaddr', rq['ipaddr'], request=request)
            continue
        else:
            # 入力したIPアドレスの最新のレコードを取得
            recent_record = list(BlackListIPAddress.objects.filter(ipaddr=rq['ipaddr']).order_by('black_list_id').reverse()[:1])

            if len(recent_record) > 0:
                error_flag, error_msg = _check_duple_pattern(recent_record[0], error_flag, request, rq, error_msg)
                if error_flag:
                    continue

        chk_iplist.append(rq['ipaddr'])
        json_str_dic['ope'] = status
        json_str_dic['ipaddr'] = rq['ipaddr']
        json_str_dic['row_id'] = rq['row_id']
        json_str_list.append(json_str_dic)

    return json_str_list, error_msg, error_flag


def _check_rq_ipaddr(request, rq, error_flag, error_msg, ipAddr_repatter):
    """
    [メソッド概要]
    IPアドレスチェック
    """
    continue_flg = False
    if 'ipaddr' not in rq or len(rq['ipaddr']) == 0:
        error_flag = True
        error_msg[rq['row_id']] += get_message(
            'MOSJA34002', request.user.get_lang_mode(), showMsgId=False) + '\n'
        logger.user_log('LOSM19001', 'ipaddr', request)
        continue_flg = True
        return continue_flg, error_msg, rq, error_flag

    re_obj = ipAddr_repatter.match(rq['ipaddr'])
    if not re_obj:
        error_flag = True
        error_msg[rq['row_id']] += get_message(
            'MOSJA34003', request.user.get_lang_mode(), showMsgId=False) + '\n'
        logger.user_log('LOSM19002', 'ipaddr',
                        rq['ipaddr'], request=request)

    # 第1～3オクテットで[*]が出現した場合以降のオクテットは[*]埋め
    if '*' in rq['ipaddr']:
        rq['ipaddr'] = set_wild_iterate(rq['ipaddr'])

    return continue_flg, error_msg, rq, error_flag


def _check_duple_pattern(recent_record, error_flag, request, rq, error_msg):
    """
    [メソッド概要]
    # 重複チェック詳細ログ
    """

    if recent_record.release_timestamp is None:
        if recent_record.manual_reg_flag == 0:
            error_flag = True
            error_msg[rq['row_id']] += get_message('MOSJA34008', request.user.get_lang_mode(), showMsgId=False) + '\n'
            logger.user_log('LOSM19003', 'ipaddr', rq['ipaddr'], request=request)
        elif recent_record.manual_reg_flag == 1:
            error_flag = True
            error_msg[rq['row_id']] += get_message('MOSJA34009', request.user.get_lang_mode(), showMsgId=False) + '\n'
            logger.user_log('LOSM19003', 'ipaddr', rq['ipaddr'], request=request)

    return error_flag, error_msg
