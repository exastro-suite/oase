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
  ルールページの表示処理
  また、ルールページからのリクエスト受信処理

[引数]
  HTTPリクエスト

[戻り値]
  HTTPレスポンス

"""


import copy
import os
import json
import pytz
import datetime
import ast
import re
import base64
import traceback
import requests
import xlrd
import uuid
import urllib.parse
import ssl
import urllib3

from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils.six.moves.urllib.parse import urlsplit

from urllib3.exceptions import InsecureRequestWarning

from libs.commonlibs import define as defs
from libs.commonlibs.dt_component import DecisionTableComponent
from libs.commonlibs.oase_logger import OaseLogger
from libs.webcommonlibs.decorator import *
from libs.webcommonlibs.common import RequestToApply
from libs.webcommonlibs.common import TimeConversion
from libs.webcommonlibs.common import Common as WebCommon
from libs.webcommonlibs.events_request import EventsRequestCommon
from libs.webcommonlibs.oase_exception import OASEError
from web_app.models.models import RuleFile
from web_app.models.models import RuleType
from web_app.models.models import RuleManage
from web_app.models.models import EventsRequest
from web_app.models.models import RhdmResponse
from web_app.models.models import RhdmResponseAction
from web_app.models.models import ActionType
from web_app.models.models import DataObject
from web_app.models.models import System
from web_app.models.models import DriverType
from web_app.models.models import ConditionalExpression
from web_app.templatetags.common import get_message
from web_app.serializers.unicode_check import UnicodeCheck

MENU_ID_STG = 2141001004
MENU_ID_PRD = 2141001005

logger = OaseLogger.get_instance()
urllib3.disable_warnings(InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context



class RuleDefs():
    """
    [クラス概要]
      ルールページ内で使用する定数をここに定義する
    """

    ############################################
    # 値定義
    ############################################
    # ルールファイル定義
    MAX_MB_SIZE       = 1024
    MAX_RULEFILE_SIZE = 1024 * 1024 * MAX_MB_SIZE

    ############################################
    # ルールファイル一時設置パス
    FILE_TEMP_PATH = '%s/temp/rule/' % (settings.BASE_DIR)

    ############################################
    # ルールファイル管理世代数
    GENERATION_MIN = 1
    GENERATION_MAX = 10

    ############################################
    # ルールファイル操作コード
    FILE_OPERATION_UPLOAD     = 1
    FILE_OPERATION_DOWNLOAD   = 2
    FILE_OPERATION_PSEUDOCALL = 3
    FILE_OPERATION_PRODUCT    = 4
    FILE_OPERATION_SWITCHBACK = 5

    ############################################
    # ルール状態
    RULE_FINISH_STS_OK  = -1  # 正常終了
    RULE_FINISH_STS_EXE = 0   # 未完了
    RULE_FINISH_STS_NG  = 1   # 異常終了

    RULE_STATUS = {
        1    : {'is_finish' : RULE_FINISH_STS_EXE, 'ope_sts' : None,                               'sts' : 'MOSJA12079',  'msg' : 'MOSJA12087'},
        2    : {'is_finish' : RULE_FINISH_STS_EXE, 'ope_sts' : None,                               'sts' : 'MOSJA12080',  'msg' : 'MOSJA12088'},
        3    : {'is_finish' : RULE_FINISH_STS_OK,  'ope_sts' : None,                               'sts' : 'MOSJA12081',  'msg' : 'MOSJA12089'},
        4    : {'is_finish' : RULE_FINISH_STS_NG,  'ope_sts' : defs.RULE_STS_OPERATION.STAGING_NG, 'sts' : 'MOSJA12082',  'msg' : 'MOSJA12090'},
        5    : {'is_finish' : RULE_FINISH_STS_NG,  'ope_sts' : defs.RULE_STS_OPERATION.STAGING_NG, 'sts' : 'MOSJA12083',  'msg' : 'MOSJA12091'},
        1000 : {'is_finish' : RULE_FINISH_STS_OK,  'ope_sts' : None,                               'sts' : 'MOSJA12084',  'msg' : 'MOSJA12092'},
        1001 : {'is_finish' : RULE_FINISH_STS_NG,  'ope_sts' : defs.RULE_STS_OPERATION.STAGING_NG, 'sts' : 'MOSJA12085',  'msg' : 'MOSJA12093'},
        2001 : {'is_finish' : RULE_FINISH_STS_NG,  'ope_sts' : defs.RULE_STS_OPERATION.STAGING_NG, 'sts' : 'MOSJA12086',  'msg' : 'MOSJA12094'},
    }

    STAGING_VALIDATE_STATUSES = [
        defs.RULE_STS_OPERATION.STAGING_NOTYET,
        defs.RULE_STS_OPERATION.STAGING_VERIFY,
        defs.RULE_STS_OPERATION.STAGING_NG,
        defs.RULE_STS_OPERATION.STAGING,
    ]

    MST_STS_OPERATION = {
            defs.RULE_STS_OPERATION.STAGING_NOAPPLY: 'MOSJA12095', # 未適用
            defs.RULE_STS_OPERATION.STAGING_NOTYET : 'MOSJA12079', # 検証未実施
            defs.RULE_STS_OPERATION.STAGING_VERIFY : 'MOSJA12080', # 検証実施中
            defs.RULE_STS_OPERATION.STAGING_NG     : 'MOSJA12096', # 検証NG
            defs.RULE_STS_OPERATION.STAGING        : 'MOSJA12097', # 検証完了
            defs.RULE_STS_OPERATION.STAGING_END    : 'MOSJA12098', # 適用終了
            defs.RULE_STS_OPERATION.PRODUCT_NOAPPLY: 'MOSJA12099', # プロダクション未適用
            defs.RULE_STS_OPERATION.PRODUCT        : 'MOSJA12100', # プロダクション未適用
            defs.RULE_STS_OPERATION.PRODUCT_END    : 'MOSJA12101', # プロダクション未適用
        }

    DISP_STAGING_STS_OPERATION = {
        k: v for k, v in MST_STS_OPERATION.items()
        if k <= defs.RULE_STS_OPERATION.STAGING and k >= defs.RULE_STS_OPERATION.STAGING_NOTYET
    }

    STAGING_OK_STATUSES = [
        defs.RULE_STS_SYSTEM.STAGING_OK,
        defs.RULE_STS_SYSTEM.PRODUCT,
        defs.RULE_STS_SYSTEM.PRODUCT_NG,
        defs.RULE_STS_SYSTEM.PRODUCT_OK,
    ]

    MST_STS_SYSTEM = {
            defs.RULE_STS_SYSTEM.UPLOAD     : 'MOSJA12102', # アップロード中
            defs.RULE_STS_SYSTEM.UPLOAD_NG  : 'MOSJA12103', # アップロード異常終了
            defs.RULE_STS_SYSTEM.UPLOAD_OK  : 'MOSJA12104', # アップロード完了
            defs.RULE_STS_SYSTEM.BUILD      : 'MOSJA12105', # ビルド中
            defs.RULE_STS_SYSTEM.BUILD_NG   : 'MOSJA12106', # ビルド異常終了
            defs.RULE_STS_SYSTEM.BUILD_OK   : 'MOSJA12107', # ビルド完了
            defs.RULE_STS_SYSTEM.STAGING    : 'MOSJA12108', # ステージング適用処理中
            defs.RULE_STS_SYSTEM.STAGING_NG : 'MOSJA12109', # ステージング適用異常終了
            defs.RULE_STS_SYSTEM.STAGING_OK : 'MOSJA12110', # ステージング適用完了
            defs.RULE_STS_SYSTEM.PRODUCT    : 'MOSJA12111', # プロダクション適用処理中
            defs.RULE_STS_SYSTEM.PRODUCT_NG : 'MOSJA12112', # プロダクション適用異常終了
            defs.RULE_STS_SYSTEM.PRODUCT_OK : 'MOSJA12113', # プロダクション適用完了
        }

    @classmethod
    def get_rulestatus_info(cls, sts_code, lang):
        """
        [メソッド概要]
          テストリクエストの適用状態から、完了状態や表示メッセージ等の情報を取得する
        """

        ret_info = {'is_finish' : cls.RULE_FINISH_STS_NG, 'ope_sts' : defs.RULE_STS_OPERATION.STAGING_NG, 'sts' : 'MOSJA12083',  'msg' : 'MOSJA12114'}

        if sts_code in cls.RULE_STATUS:
            ret_info = copy.deepcopy(cls.RULE_STATUS[sts_code])

            ret_info['sts'] = get_message(ret_info['sts'], lang, showMsgId=False)
            ret_info['msg'] = get_message(ret_info['msg'], lang, showMsgId=False)

        return ret_info



def makePseudoCallMessage(msg, reception_dt, event_dt, req_list, lang, add_msg=''):
    """
    [メソッド概要]
      ブラウザに表示するメッセージを作成する
    """

    ret_str  = ''

    ret_str += get_message('MOSJA12115', lang, showMsgId=False) + '%s \n'% (reception_dt)
    ret_str += get_message('MOSJA12116', lang, showMsgId=False) + '%s \n'% (event_dt)

    for r in req_list:
        ret_str += '%s %s \n' % (r['conditional_name'], r['value'])

    ret_str += '%s \n' % (msg)

    if add_msg:
        ret_str += '%s \n' % (add_msg)

    return ret_str


def makePseudoCallMessage_Bulk(msg, reception_dt, filename, cnt, max_cnt, lang):
    """
    [メソッド概要]
      ブラウザに表示するメッセージを作成する(一括リクエスト用)
    """

    ret_str = ''

    # ヘッダ
    ret_str += get_message('MOSJA12115', lang, showMsgId=False) + '\n'
    ret_str += get_message('MOSJA12116', lang, showMsgId=False) + '%s \n' % (reception_dt)
    ret_str += get_message('MOSJA12045', lang, showMsgId=False) + '%s \n' % (filename)

    # リクエスト件数
    ret_str += get_message('MOSJA12117', lang, showMsgId=False) + '%3s / %3s \n\n' % (cnt, max_cnt)

    # リクエスト詳細
    ret_str += '%s \n' % (msg)

    return ret_str


@check_allowed_auth([MENU_ID_STG, MENU_ID_PRD], defs.MENU_CATEGORY.ALLOW_EVERY)
def rule(request):
    """
    [メソッド概要]
      ルールページのトップ画面にアクセスされた際のリクエストを処理する
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    now = datetime.datetime.now(pytz.timezone('UTC'))
    msg = ''
    lang = request.user.get_lang_mode()

    # ステージング権限
    perm_type_stg = request.user_config.get_menu_auth_type(MENU_ID_STG)
    perm_info_stg = request.user_config.get_activerule_auth_type(MENU_ID_STG)
    rule_ids_stg_admin = perm_info_stg[defs.ALLOWED_MENTENANCE]

    # プロダクション権限
    perm_type_prd = request.user_config.get_menu_auth_type(MENU_ID_PRD)
    perm_info_prd = request.user_config.get_activerule_auth_type(MENU_ID_PRD)
    rule_ids_prd_admin = perm_info_prd[defs.ALLOWED_MENTENANCE]

    staging_list = []
    staging_history_list = []
    rule_product_list = []
    rule_history_list = []
    pseudo_rule_manage_id_dic = {}
    apply_rule_manage_id_dic = {}
    staging_pseudo_target = {}
    staging_pseudo_target_rule_type = {}

    try:
        # ステージング適用ルール取得
        staging_list, staging_history_list = _select_staging({}, perm_info_stg, request)

        # プロダクション適用ルール取得
        rule_product_list, rule_history_list = _select_production({}, perm_info_prd, request)

        # プロダクション適用前データ
        pseudo_rule_manage_id_dic = _get_testrequest_ids(staging_list)

        # テストリクエスト対象データ
        apply_rule_manage_id_dic = _get_production_appling_rule_id(staging_list)

        # 条件式マスタから入力例を取得
        staging_pseudo_target, staging_pseudo_target_rule_type = _get_staging_pseudo_targets(staging_list, pseudo_rule_manage_id_dic, lang)

    except:
        msg = get_message('MOSJA12000', request.user.get_lang_mode())
        logger.system_log('LOSM12000', traceback.format_exc())

    disp_staging_sts_operation = {
        k : get_message(v,request.user.get_lang_mode(), showMsgId=False)
        for k,v in RuleDefs.DISP_STAGING_STS_OPERATION.items()

    }

    data = {
        'msg': msg,  # TODO検討する
        'staging_list': staging_list,
        'staging_history_list': staging_history_list,
        'product_list': rule_product_list,
        'history_list': rule_history_list,
        'disp_staging_sts_operation': disp_staging_sts_operation,
        'now': now,
        'apply_rule_manage_id_dic': apply_rule_manage_id_dic,
        'pseudo_rule_manage_id_dic': pseudo_rule_manage_id_dic,
        'mainmenu_list': request.user_config.get_menu_list(),
        'stagingPseudoTargetList': staging_pseudo_target,
        'stagingPseudoTargetRuleTypeList': staging_pseudo_target_rule_type,
        'permission_type_stg': perm_type_stg,
        'permission_type_prd': perm_type_prd,
        'rule_ids_stg': rule_ids_stg_admin,
        'rule_ids_prd': rule_ids_prd_admin,
        'user_name': request.user.user_name,
        'lang_mode': request.user.get_lang_mode(),
    }

    log_data = {
        'staging_list_cnt': len(staging_list),
        'product_list_cnt': len(rule_product_list),
        'history_list_cnt': len(rule_history_list),
        'apply_rule_manage_ids': list(apply_rule_manage_id_dic.keys()),
        'pseudo_rule_manage_ids': list(pseudo_rule_manage_id_dic.keys()),
        'stagingPseudoTargetList': staging_pseudo_target,
    }
    logger.logic_log('LOSI00002', json.dumps(log_data, ensure_ascii=False), request=request)

    return render(request, 'rule/rule.html', data)


def _filter_staging_rule(staging_list):
    """
    ステージング適用ルールを画面に表示するために並ベ替える。
    _select_staging()でのみ呼ばれる。
    [引数]
    staging_list: _select()で取得したステージングのデータ
    [戻り値]
    present_list: 現在のステージングルールのリスト
    history_list: 過去のステージングルールのリスト
    """
    logger.logic_log('LOSI00001', 'staging_list count: %s' % len(staging_list))

    present_list = []
    history_list = []
    found_normalstatus_rule_type_ids = []

    normalstatus = RuleDefs.STAGING_VALIDATE_STATUSES + [defs.RULE_STS_OPERATION.STAGING_END]

    # ステージング適用ルールを並び替える
    for s in staging_list:

        # 正常なルールが見つかっていたら履歴のリストに積む
        # それ以外は運用ステータスが正常/異常にかかわらず現在のリストに積む
        if s['rule_type_id'] in found_normalstatus_rule_type_ids:
            history_list.append(s)
        else:
            present_list.append(s)

        # 正常なルールが見つかったら、それ以降の同じルールは
        # 過去リストに積めるようにルール種別IDを保存する
        if s['operation_status_id'] in normalstatus:
            found_normalstatus_rule_type_ids.append(s['rule_type_id'])

    logger.logic_log('LOSI00002', '[staging_list] present_list count: %s, history_list count: %s' % (len(present_list), len(history_list)))

    return present_list, history_list


def _get_testrequest_ids(rule_staging_list):
    """
    ステージング状態のルールから、テストリクエスト対象のレコードを取得。
    処理成功かつステージングであるものがテストリクエスト対象
    [引数]
    rule_staging_list: _select_staging()で取得したデータ
    [戻り値]
    pseudo_rule_manage_id_dic:
        key=rule_manage_id(これが必要)
        value="" (key取れればvalueは何でもいい)
    """
    logger.logic_log('LOSI00001', 'rule_staging_list count: %s' % len(rule_staging_list))

    # 処理成功かつステージングであるものが擬似呼対象
    pseudo_rule_manage_id_dic ={
        r['rule_manage_id']: ""
        for r in rule_staging_list
        if r['system_status_id'] in RuleDefs.STAGING_OK_STATUSES \
            and r['operation_status_id'] in RuleDefs.STAGING_VALIDATE_STATUSES
    }

    logger.logic_log('LOSI00002', ' pseudo_rule_manage_id_dic count: %s' % len(pseudo_rule_manage_id_dic))
    return pseudo_rule_manage_id_dic


def _get_production_appling_rule_id(rule_staging_list):
    """
    プロダクション適用待ちルールID取得
    [引数]
    rule_staging_list: _select_production()で取得したデータ
    [戻り値]
    apply_rule_manage_id_dic: プロダクション適用待ちルールid
    """
    logger.logic_log('LOSI00001', 'rule_staging_list count: %s' % len(rule_staging_list))

    apply_rule_manage_id_dic = {}
    for rs in rule_staging_list:

        # プロダクション適用前かどうか
        pro_teki_cnt = RuleManage.objects.filter(
            rule_type_id=rs['rule_type_id'],
            request_type_id=defs.PRODUCTION,
            rule_file_id=rs['rule_file_id']
        ).exclude(
            system_status=defs.RULE_STS_SYSTEM.PRODUCT_NG
        ).count()

        if pro_teki_cnt == 0 and rs['operation_status_id'] == defs.RULE_STS_OPERATION.STAGING:
            apply_rule_manage_id_dic[rs['rule_manage_id']] = rs['rule_type_id']

    logger.logic_log('LOSI00002', ' apply_rule_manage_id_dic count: %s' % len(apply_rule_manage_id_dic))
    return apply_rule_manage_id_dic


def _get_staging_pseudo_targets(rule_staging_list, pseudo_rule_manage_id_dic, lang):
    """
    擬似呼画面選択用ルール種別（staging）
    [引数]
    rule_staging_list: _select_staging()で取得したデータ
    pseudo_rule_manage_id_dic: プロダクション適用前データ
    [戻り値]
    staging_pseudo_target: テストリクエスト可能なルール
    staging_pseudo_target_rule_type: staging_pseudo_targetの条件式
    """
    logger.logic_log('LOSI00001', 'rule_staging_list count: %s, pseudo_rule_manage_id_dic:%s' % (len(rule_staging_list), len(pseudo_rule_manage_id_dic)))

    # 条件式マスタから入力例を取得
    ce_list = ConditionalExpression.objects.all()
    examples = {
        ce.conditional_expression_id : get_message(ce.example, lang, showMsgId=False)
        for ce in ce_list
    }

    staging_pseudo_target_rule_type = {}
    staging_pseudo_target = {'': ''}
    for u in rule_staging_list:
        if u['rule_manage_id'] in pseudo_rule_manage_id_dic:
            staging_pseudo_target[u['rule_manage_id']] = u['rule_type_name']

            if not u['rule_type_id'] in staging_pseudo_target_rule_type:
                conditions = list(DataObject.objects.filter(rule_type_id=u['rule_type_id']).order_by('data_object_id'))

                # 重複ラベルは入力例が同じなので上書きを認める
                condition_dict = {
                    c.conditional_name : examples[c.conditional_expression_id]
                    for c in conditions
                }

                staging_pseudo_target_rule_type[u['rule_type_id']] = condition_dict

    logger.logic_log('LOSI00002', ' staging_pseudo_target count: %s, staging_pseudo_target_rule_type count: %s' % (len(staging_pseudo_target), len(staging_pseudo_target_rule_type)))
    return staging_pseudo_target, staging_pseudo_target_rule_type


@check_allowed_auth(MENU_ID_STG, defs.MENU_CATEGORY.ALLOW_EVERY)
def rule_staging(request):
    """
    [メソッド概要]
      ステージングのデータ取得
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    now = datetime.datetime.now(pytz.timezone('UTC'))
    msg = ''
    lang = request.user.get_lang_mode()

    # 参照以上の権限を持つルール種別IDを取得し、フィルター条件に追加
    perm_type_stg = request.user_config.get_menu_auth_type(MENU_ID_STG)
    perm_info_stg = request.user_config.get_activerule_auth_type(MENU_ID_STG)
    rule_ids_stg_admin = perm_info_stg[defs.ALLOWED_MENTENANCE]

    perm_type_prd = request.user_config.get_menu_auth_type(MENU_ID_PRD)
    perm_info_prd = request.user_config.get_activerule_auth_type(MENU_ID_PRD)
    rule_ids_prd_admin = perm_info_prd[defs.ALLOWED_MENTENANCE]

    staging_list = []
    staging_history_list = []
    pseudo_rule_manage_id_dic = {}
    apply_rule_manage_id_dic = {}
    staging_pseudo_target = {}
    staging_pseudo_target_rule_type = {}

    try:
        filters = {}
        if request and request.method == 'POST':
            filters = request.POST.get('filters', "{}")
            filters = json.loads(filters)

        # ステージングのデータ取得
        staging_list, staging_history_list = _select_staging(filters, perm_info_stg, request)

        # プロダクション適用前データ
        pseudo_rule_manage_id_dic = _get_testrequest_ids(staging_list)

        # テストリクエスト対象データ
        apply_rule_manage_id_dic = _get_production_appling_rule_id(staging_list)

        # 条件式マスタから入力例を取得
        staging_pseudo_target, staging_pseudo_target_rule_type = _get_staging_pseudo_targets(staging_list, pseudo_rule_manage_id_dic, lang)

    except:
        msg = get_message('MOSJA12000', request.user.get_lang_mode())
        logger.system_log('LOSM12000', traceback.format_exc(), request=request)

    disp_staging_sts_operation = {
        k : get_message(v,request.user.get_lang_mode(), showMsgId=False)
        for k,v in RuleDefs.DISP_STAGING_STS_OPERATION.items()
    }

    data = {
        'msg': msg,
        'now': now,
        'staging_list': staging_list,
        'staging_history_list': staging_history_list,
        'apply_rule_manage_id_dic': apply_rule_manage_id_dic,
        'pseudo_rule_manage_id_dic': pseudo_rule_manage_id_dic,
        'disp_staging_sts_operation': disp_staging_sts_operation,
        'stagingPseudoTargetList': staging_pseudo_target,
        'stagingPseudoTargetRuleTypeList': staging_pseudo_target_rule_type,
        'rule_ids_stg': rule_ids_stg_admin,
        'rule_ids_prd': rule_ids_prd_admin,
        'permission_type_stg': perm_type_stg,
        'permission_type_prd': perm_type_prd,
        'lang_mode': request.user.get_lang_mode(),
    }

    log_data = {
        'staging_list_cnt': len(staging_list),
        'apply_rule_manage_ids': list(apply_rule_manage_id_dic.keys()),
        'pseudo_rule_manage_ids': list(pseudo_rule_manage_id_dic.keys()),
        'stagingPseudoTargetList': staging_pseudo_target,
    }
    logger.logic_log('LOSI00002', json.dumps(log_data, ensure_ascii=False), request=request)

    return render(request, 'rule/rule_staging_data.html', data)


@check_allowed_auth(MENU_ID_PRD, defs.MENU_CATEGORY.ALLOW_EVERY)
def rule_production(request):
    """
    [メソッド概要]
      プロダクションのデータ取得
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    msg = ''
    product_list = []
    history_list = []
    rule_ids_prd_admin = []
    permission_type_prd = request.user_config.get_menu_auth_type(MENU_ID_PRD)

    try:
        filters = {}
        if request and request.method == 'POST':
            filters = request.POST.get('filters', "{}")
            filters = json.loads(filters)

        # 参照以上の権限を持つルール種別IDを取得し、フィルター条件に追加
        perm_info_prd = request.user_config.get_activerule_auth_type(MENU_ID_PRD)
        rule_ids_prd_admin = perm_info_prd[defs.ALLOWED_MENTENANCE]
        product_list, history_list = _select_production(filters, perm_info_prd, request)

    except:
        msg = get_message('MOSJA12000', request.user.get_lang_mode())
        logger.system_log('LOSM12000', traceback.format_exc(), request=request)

    data = {
        'msg': msg,
        'product_list': product_list,
        'history_list': history_list,
        'rule_ids_prd': rule_ids_prd_admin,
        'permission_type_prd': permission_type_prd,
        'lang_mode': request.user.get_lang_mode(),
    }

    log_data = {
        'product_list_cnt': len(product_list) + len(history_list),
    }
    logger.logic_log('LOSI00002', json.dumps(log_data, ensure_ascii=False), request=request)

    return render(request, 'rule/rule_production_data.html', data)


@check_allowed_auth(MENU_ID_PRD, defs.MENU_CATEGORY.ALLOW_EVERY)
def rule_history(request):
    """
    [メソッド概要]
      プロダクション適用履歴のデータ取得
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    msg = ''

    try:
        filters = {}
        if request and request.method == 'POST':
            filters = request.POST.get('filters', "{}")
            filters = json.loads(filters)

        # 参照以上の権限を持つルール種別IDを取得し、フィルター条件に追加
        permission_info_prd = request.user_config.get_activerule_auth_type(MENU_ID_PRD)

        rule_ids_prd = []
        rule_ids_prd_view  = permission_info_prd[defs.VIEW_ONLY]
        rule_ids_prd_admin = permission_info_prd[defs.ALLOWED_MENTENANCE]
        rule_ids_prd.extend(rule_ids_prd_view)
        rule_ids_prd.extend(rule_ids_prd_admin)

        if 'rule_type_id' not in filters:
            filters['rule_type_id'] = {}

        if 'LIST' not in filters['rule_type_id']:
            filters['rule_type_id']['LIST'] = []

        filters['rule_type_id']['LIST'].extend(rule_ids_stg)
        rule_history_list = _select(filters, request)

    except:
        msg = get_message('MOSJA12000', request.user.get_lang_mode())
        logger.system_log('LOSM12000', traceback.format_exc(), request=request)

    data = {
        'msg': msg,
        'history_list': rule_history_list,
        'rule_ids_prd': rule_ids_prd_admin,
        'lang_mode': request.user.get_lang_mode(),
    }

    log_data = {
        'history_list_cnt': len(rule_history_list),
    }
    logger.logic_log('LOSI00002', json.dumps(log_data, ensure_ascii=False), request=request)

    return render(request, 'rule/rule_history_data.html', data)


@check_allowed_auth(MENU_ID_STG, defs.MENU_CATEGORY.ALLOW_EVERY)
@require_POST
def rule_pseudo_request(request, rule_type_id):
    """
    [メソッド概要]
      テストリクエスト実行時のリクエストを処理する
    """
    logger.logic_log('LOSI00001', 'None', request=request)

    err_flg = 1
    msg = ''
    reception_dt = datetime.datetime.now(pytz.timezone('UTC'))
    reception_dt = TimeConversion.get_time_conversion(reception_dt, 'Asia/Tokyo', request=request)
    trace_id = ''
    event_dt = '----/--/-- --:--:--'
    req_list = []

    try:
        with transaction.atomic():
            json_str = request.POST.get('json_str', None)
            post_data = json.loads(json_str)
            rule_table_name = post_data['ruletable']
            eventdatetime = post_data['eventdatetime']
            eventinfo = post_data['eventinfo']
            if json_str is None:
                msg = get_message('MOSJA12002', request.user.get_lang_mode())
                logger.user_log('LOSM12007', request=request)
                raise Exception()

            rt = RuleType.objects.get(rule_table_name=rule_table_name)

            # ルール別アクセス権限チェック
            rule_ids = []
            for chk_auth in defs.MENU_CATEGORY.ALLOW_EVERY:
                rule_ids.extend(request.user_config.get_activerule_auth_type(MENU_ID_STG, chk_auth))

            if rt.rule_type_id not in rule_ids:
                raise OASEError('MOSJA12031', 'LOSI12012', msg_params={'opename':get_message('MOSJA12035', request.user.get_lang_mode(), showMsgId=False), 'rule_type_name':rt.rule_type_name}, log_params=['Send Request', rt.rule_type_id, rule_ids])

            # 入力された情報のバリデーション
            errmsg_list = []
            _validate_eventdatetime(eventdatetime, errmsg_list, request.user.get_lang_mode())
            _validate_eventinfo(rule_type_id, eventinfo, errmsg_list, request.user.get_lang_mode())

            if len(errmsg_list):
                msg = '\n'.join(errmsg_list) + '\n'
                logger.system_log('LOSM12064', 'post_data:%s' % (post_data))
                raise Exception()

            # RestApiにリクエストを投げる
            scheme = urlsplit(request.build_absolute_uri(None)).scheme
            url = scheme + '://127.0.0.1:' + request.META['SERVER_PORT'] + reverse('web_app:event:eventsrequest')
            r = requests.post(
                url,
                headers={'content-type': 'application/json'},
                data=json_str.encode('utf-8'),
                verify=False
            )
            # レスポンスからデータを取得
            try:
                r_content = json.loads(r.content.decode('utf-8'))
            except json.JSONDecodeError:
                msg = get_message('MOSJA12012', request.user.get_lang_mode())
                logger.user_log('LOSM12052')
                raise

            # テストリクエストの実行中に失敗した場合
            if not r_content["result"]:
                msg = r_content["msg"]
                logger.user_log('LOSM12001', traceback.format_exc())
                raise

            trace_id = r_content["trace_id"]

            # 該当ルール種別をロック
            data_obj_list = DataObject.objects.filter(rule_type_id=rt.pk).order_by('data_object_id')

            label_list = []
            conditional_name_list = []

            for a in data_obj_list:
                if a.label not in label_list:
                    label_list.append(a.label)
                    conditional_name_list.append(a.conditional_name)

            # 実行ログに表示するためのデータ作成
            req_list = [
                {'conditional_name':conditional_name_list[i], 'value':v}
                for i, v in enumerate(eventinfo)
            ]
            event_dt = TimeConversion.get_time_conversion_utc(eventdatetime, 'Asia/Tokyo', request=request)
            event_dt = TimeConversion.get_time_conversion(event_dt, 'Asia/Tokyo', request=request)
            err_flg = 0

            msg = get_message('MOSJA12007', request.user.get_lang_mode(), showMsgId=False)

    except OASEError as e:
        if e.log_id:
            if e.arg_list and isinstance(e.arg_list, list):
                logger.logic_log(e.log_id, *(e.arg_list), request=request)
            else:
                logger.logic_log(e.log_id, request=request)

        if e.msg_id:
            if e.arg_dict and isinstance(e.arg_dict, dict):
                msg = get_message(e.msg_id, request.user.get_lang_mode(), **(e.arg_dict))
            else:
                msg = get_message(e.msg_id, request.user.get_lang_mode())

        resp_json = {
            'err_flg': err_flg,
            'msg': msg,
            'log_msg': msg,
            'trace_id': trace_id,
        }
        resp_json = json.dumps(resp_json, ensure_ascii=False)
        return HttpResponse(resp_json, status=None)

    except Exception as e:
        logger.system_log('LOSM12050', traceback.format_exc(), request=request)
        if not msg:
            msg = get_message('MOSJA12001', request.user.get_lang_mode())

        resp_json = {
            'err_flg': err_flg,
            'msg': get_message('MOSJA12023', request.user.get_lang_mode()),
            'log_msg': msg,
            'trace_id': trace_id,
        }
        resp_json = json.dumps(resp_json, ensure_ascii=False)
        return HttpResponse(resp_json, status=None)

    msg = makePseudoCallMessage(msg, reception_dt, event_dt, req_list, request.user.get_lang_mode())
    resp_json = {
        'err_flg': err_flg,
        'msg': get_message('MOSJA12024', request.user.get_lang_mode(), showMsgId=False),
        'log_msg': msg,
        'trace_id': trace_id,
    }
    resp_json = json.dumps(resp_json, ensure_ascii=False)

    logger.logic_log('LOSI00002', resp_json, request=request)
    return HttpResponse(resp_json)


@check_allowed_auth(MENU_ID_STG, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def rule_change_status(request):
    """
    [メソッド概要]
      ステージング適用ルールの運用ステータス変更
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    msg = ''
    err_flg = 1

    try:
        # パラメーターチェック
        status = request.POST.get('status', None)
        rule_manage_id = request.POST.get('rule_manage_id', None)

        if status is None or rule_manage_id is None:
            msg = get_message('MOSJA12002', request.user.get_lang_mode())
            logger.user_log('LOSM03005', status, rule_manage_id, request=request)
            raise Exception()

        status = int(status)
        rule_manage_id = int(rule_manage_id)

        logger.logic_log('LOSI03000', 'rule_manage_id:%s, status:%s' % (rule_manage_id, status), request=request)

        # リクエストステータスの妥当性チェック
        if status not in RuleDefs.DISP_STAGING_STS_OPERATION:
            msg = get_message('MOSJA12002', request.user.get_lang_mode())
            logger.user_log('LOSM03001', status, RuleDefs.DISP_STAGING_STS_OPERATION, request=request)
            raise Exception()

        with transaction.atomic():
            # 該当ルール適用管理テーブルをロック
            rule_manage = RuleManage.objects.select_for_update().get(pk=rule_manage_id)

            # ルール別アクセス権限チェック
            rule_ids = []
            for chk_auth in defs.MENU_CATEGORY.ALLOW_ADMIN:
                rule_ids.extend(request.user_config.get_activerule_auth_type(MENU_ID_STG, chk_auth))

            if rule_manage.rule_type_id not in rule_ids:
                ruletypename = RuleType.objects.get(rule_type_id=rule_manage.rule_type_id).rule_type_name
                raise OASEError('MOSJA12031', 'LOSI12012', msg_params={'opename':get_message('MOSJA12118', request.user.get_lang_mode(), showMsgId=False), 'rule_type_name':ruletypename}, log_params=['Change Status', rule_manage.rule_type_id, rule_ids])

            # 対象ルールの状態チェック
            if rule_manage.request_type_id != defs.STAGING:
                msg = get_message('MOSJA12010', request.user.get_lang_mode())
                logger.user_log('LOSI03001', 'req_type:%s, expect_type:%s' % (rule_manage.request_type_id, defs.STAGING), request=request)
                raise Exception()

            if rule_manage.system_status not in RuleDefs.STAGING_OK_STATUSES:
                msg = get_message('MOSJA12010', request.user.get_lang_mode())
                logger.user_log('LOSI03001', 'sys_sts:%s, expect_sts:%s' % (rule_manage.system_status, RuleDefs.STAGING_OK_STATUSES), request=request)
                raise Exception()

            if rule_manage.operation_status not in RuleDefs.STAGING_VALIDATE_STATUSES:
                msg = get_message('MOSJA12010', request.user.get_lang_mode())
                logger.user_log('LOSI03001', 'ope_sts:%s, expect_sts:%s' % (rule_manage.operation_status, RuleDefs.STAGING_VALIDATE_STATUSES), request=request)
                raise Exception()

            pro_flag = False
            rcnt = RuleManage.objects.filter(
                rule_type_id=rule_manage.rule_type_id,
                request_type_id=defs.PRODUCTION,
                rule_file_id=rule_manage.rule_file_id
            ).exclude(
                system_status=defs.RULE_STS_SYSTEM.PRODUCT_NG
            ).count()
            if rcnt == 0 and rule_manage.operation_status == defs.RULE_STS_OPERATION.STAGING:
                pro_flag = True

            if pro_flag == False and rule_manage.operation_status == defs.RULE_STS_OPERATION.STAGING:
                msg = get_message('MOSJA12011', request.user.get_lang_mode())
                logger.user_log('LOSI03001', 'pro_count:%s, rule_file_id:%s' % (rcnt, rule_manage.rule_file_id), request=request)
                raise Exception()

            # 状態更新
            rule_manage.operation_status = status
            rule_manage.last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC'))
            rule_manage.last_update_user = request.user.user_name
            rule_manage.save()
            msg = get_message('MOSJA12008', request.user.get_lang_mode(), showMsgId=False)
            err_flg = 0

    except OASEError as e:
        if e.log_id:
            if e.arg_list and isinstance(e.arg_list, list):
                logger.logic_log(e.log_id, *(e.arg_list), request=request)
            else:
                logger.logic_log(e.log_id, request=request)

        if e.msg_id:
            if e.arg_dict and isinstance(e.arg_dict, dict):
                msg = get_message(e.msg_id, request.user.get_lang_mode(), **(e.arg_dict))
            else:
                msg = get_message(e.msg_id, request.user.get_lang_mode())

    except RuleManage.DoesNotExist:
        logger.system_log('LOSM12002', traceback.format_exc(), request=request)
        msg = get_message('MOSJA12009', request.user.get_lang_mode())

    except Exception as e:
        logger.system_log('LOSM12002', traceback.format_exc(), request=request)
        if not msg:
            msg = get_message('MOSJA12001', request.user.get_lang_mode())

    resp_json = {
        'err_flg': err_flg,
        'msg': msg,
    }

    resp_json = json.dumps(resp_json, ensure_ascii=False)

    logger.logic_log('LOSI00002', resp_json, request=request)

    return HttpResponse(resp_json)


@check_allowed_auth(MENU_ID_STG, defs.MENU_CATEGORY.ALLOW_EVERY)
@require_POST
def rule_get_record(request):
    """
    [メソッド概要]
      ステージング適用ルール詳細に表示されるデータを取得する
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    data = {}
    msg = ''
    err_flg = 0

    try:
        # パラメーターチェック
        rule_manage_id = request.POST.get('rule_manage_id', None)

        if rule_manage_id is None:
            msg = get_message('MOSJA12002', request.user.get_lang_mode())
            raise Exception()

        rule_manage_id = int(rule_manage_id)
        logger.logic_log('LOSI03000', 'rule_manage_id:%s' % (rule_manage_id), request=request)

        rule_manage = RuleManage.objects.get(pk=rule_manage_id)
        rule_file_name = RuleFile.objects.get(rule_file_id=rule_manage.rule_file_id).rule_file_name

        # ルール別アクセス権限チェック
        rule_ids = []
        for chk_auth in defs.MENU_CATEGORY.ALLOW_EVERY:
            rule_ids.extend(request.user_config.get_activerule_auth_type(MENU_ID_STG, chk_auth))

        if rule_manage.rule_type_id not in rule_ids:
            ruletypename = RuleType.objects.get(rule_type_id=rule_manage.rule_type_id).rule_type_name
            raise OASEError('MOSJA12031', 'LOSI12012', msg_params={'opename':get_message('MOSJA12035', request.user.get_lang_mode(), showMsgId=False), 'rule_type_name':ruletypename}, log_params=['Select Rule', rule_manage.rule_type_id, rule_ids])

        # ステージング権限
        permission_info_stg = request.user_config.get_activerule_auth_type(MENU_ID_STG)
        rule_ids_stg_admin = permission_info_stg[defs.ALLOWED_MENTENANCE]

    except RuleManage.DoesNotExist:
        logger.system_log('LOSM12054', traceback.format_exc(), request=request)
        msg = get_message('MOSJA12009', request.user.get_lang_mode())
        err_flg = 1

    except RuleFile.DoesNotExist:
        logger.system_log('LOSM12054', traceback.format_exc(), request=request)
        msg = get_message('MOSJA12009', request.user.get_lang_mode())
        err_flg = 1

    except OASEError as e:
        if e.log_id:
            if e.arg_list and isinstance(e.arg_list, list):
                logger.logic_log(e.log_id, *(e.arg_list), request=request)
            else:
                logger.logic_log(e.log_id, request=request)

        if e.msg_id:
            if e.arg_dict and isinstance(e.arg_dict, dict):
                msg = get_message(e.msg_id, request.user.get_lang_mode(), **(e.arg_dict))
            else:
                msg = get_message(e.msg_id, request.user.get_lang_mode())

        err_flg = 1

    except Exception as e:
        logger.system_log('LOSM12054', traceback.format_exc(), request=request)
        err_flg = 1
        if not msg:
            msg = get_message('MOSJA12001', request.user.get_lang_mode())

    if err_flg == 0:
        # グループ情報取得
        _, rule_type_dict = _getRuleTypeData(request)


        operation_status_str = get_message(RuleDefs.MST_STS_OPERATION[rule_manage.operation_status],request.user.get_lang_mode(), showMsgId=False)
        system_status_str = get_message(RuleDefs.MST_STS_SYSTEM[rule_manage.system_status],request.user.get_lang_mode(), showMsgId=False)

        if request.user.get_lang_mode() == 'EN':
            last_update_timestamp = rule_manage.last_update_timestamp.astimezone(pytz.timezone('Asia/Tokyo')).strftime('%Y, %m, %d, %H:%M')
        else:
            last_update_timestamp = rule_manage.last_update_timestamp.astimezone(pytz.timezone('Asia/Tokyo')).strftime('%Y年%m月%d日%H:%M')

        data = {
            'rule_type_id': rule_manage.rule_type_id,
            'rule_type_name': rule_type_dict[rule_manage.rule_type_id]['name'],
            'rule_table_name': rule_type_dict[rule_manage.rule_type_id]['table'],
            'filename': rule_file_name,
            'operation_status_id': rule_manage.operation_status,
            'operation_status_str': operation_status_str,
            'system_status_str': system_status_str,
            'rule_ids_stg': rule_ids_stg_admin,
            'last_update_user_name': rule_manage.last_update_user,
            'last_update_timestamp': last_update_timestamp,
        }

    resp_json = {
        'data': data,
        'err_flg': err_flg,
        'msg': msg,
    }

    resp_json = json.dumps(resp_json, ensure_ascii=False)

    logger.logic_log('LOSI00002', resp_json, request=request)

    return HttpResponse(resp_json)


@check_allowed_auth(MENU_ID_STG, defs.MENU_CATEGORY.ALLOW_EVERY)
def rule_polling(request, rule_manage_id, trace_id):
    """
    [メソッド概要]
      テストリクエスト実行中のポーリングリクエストを処理する
    """

    logger.logic_log('LOSI00001', 'trace_id:%s, manage_id:%s' % (trace_id, rule_manage_id), request=request)

    resp_json = {}
    err_flg = 1
    is_finish = RuleDefs.RULE_FINISH_STS_NG
    msg = ''

    add_msg = ''
    reception_dt = '----/--/-- --:--:--'
    event_dt = '----/--/-- --:--:--'
    req_list = []

    try:
        with transaction.atomic():
            events_request = EventsRequest.objects.get(trace_id=trace_id)

            # ルール別アクセス権限チェック
            rule_ids = []
            for chk_auth in defs.MENU_CATEGORY.ALLOW_EVERY:
                rule_ids.extend(request.user_config.get_activerule_auth_type(MENU_ID_STG, chk_auth))

            if events_request.rule_type_id not in rule_ids:
                ruletypename = RuleType.objects.get(rule_type_id=events_request.rule_type_id).rule_type_name
                raise OASEError('MOSJA12031', 'LOSI12012', msg_params={'opename':get_message('MOSJA12035', request.user.get_lang_mode(), showMsgId=False), 'rule_type_name':ruletypename}, log_params=['Polling', events_request.rule_type_id, rule_ids])

            # テストリクエスト情報を取得
            evinfo = ast.literal_eval(events_request.event_info)
            evinfo = evinfo['EVENT_INFO'] if 'EVENT_INFO' in evinfo else []
            rset = DataObject.objects.filter(rule_type_id=events_request.rule_type_id).order_by('data_object_id')

            label_list = []
            conditional_name_list = []

            for a in rset:
                if a.label not in label_list:
                    label_list.append(a.label)
                    conditional_name_list.append(a.conditional_name)

            for rs, v in zip(conditional_name_list, evinfo):
                req_list.append({'conditional_name':rs, 'value':v})

            reception_dt = events_request.request_reception_time
            reception_dt = TimeConversion.get_time_conversion(reception_dt, 'Asia/Tokyo', request=request)
            event_dt = events_request.event_to_time
            event_dt = TimeConversion.get_time_conversion(event_dt, 'Asia/Tokyo', request=request)

            rule_info = RuleDefs.get_rulestatus_info(events_request.status, request.user.get_lang_mode())
            is_finish = rule_info['is_finish']
            msg = rule_info['msg']
            ope_sts = rule_info['ope_sts']

            # テストリクエスト終了の場合、状態を遷移させる
            if is_finish != RuleDefs.RULE_FINISH_STS_EXE and ope_sts:
                rule_manage = RuleManage.objects.select_for_update().get(pk=rule_manage_id)

                if rule_manage.operation_status in RuleDefs.STAGING_VALIDATE_STATUSES:
                    rule_manage.operation_status = ope_sts
                    rule_manage.last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC'))
                    rule_manage.last_update_user = request.user.user_name
                    rule_manage.save()

            # 正常時は適用されたルールを取得する
            if is_finish == RuleDefs.RULE_FINISH_STS_OK:
                target_rule = ''
                match_rulename = ''

                rhdm_res = RhdmResponse.objects.get(trace_id=trace_id)

                rhdm_res_acts = RhdmResponseAction.objects.filter(response_id=rhdm_res.response_id)

                for r in rhdm_res_acts:
                    if match_rulename:
                        match_rulename = '%s, %s' % (match_rulename, r.rule_name)
                    else:
                        match_rulename = r.rule_name

                for r in rhdm_res_acts:
                    try:
                        acttype = ActionType.objects.get(pk=r.action_type_id)
                        dritype = DriverType.objects.get(pk=acttype.driver_type_id)
                    except ActionType.DoesNotExist:
                        logger.user_log('LOSM03006', r.action_type_id, request=request)
                        msg = get_message('MOSJA12032', request.user.get_lang_mode())
                        raise
                    except DriverType.DoesNotExist:
                        logger.user_log('LOSM03007', acttype.driver_type_id, request=request)
                        msg = get_message('MOSJA12032', request.user.get_lang_mode())
                        raise
                    except Exception as e:
                        logger.user_log('LOSM03008', request=request)
                        msg = get_message('MOSJA12032', request.user.get_lang_mode())
                        raise

                    tmp_actparainfo = json.loads(r.action_parameter_info)

                    for i in range(len(tmp_actparainfo['ACTION_PARAMETER_INFO'])):
                        if i == 0:
                            actparainfo = tmp_actparainfo['ACTION_PARAMETER_INFO'][i]
                        else:
                            actparainfo = '%s, %s' % (actparainfo, tmp_actparainfo['ACTION_PARAMETER_INFO'][i])

                    name = dritype.name + '(ver' + str(dritype.driver_major_version) + ')'

                    if not r.action_pre_info:
                        actpreinfo = get_message('MOSJA12154', request.user.get_lang_mode(), showMsgId=False)
                    else:
                        actpreinfo = get_message('MOSJA12155', request.user.get_lang_mode(), showMsgId=False)

                    target_rule = r.rule_name
                    target_execution = r.execution_order
                    target_drivertype = name
                    target_actparainfo = actparainfo
                    target_actpreinfo = actpreinfo

                    if add_msg:
                        add_msg += '\n\n'
                        add_msg = add_msg + get_message('MOSJA12122', request.user.get_lang_mode(), showMsgId=False) + target_rule + ' \n'
                        add_msg = add_msg + get_message('MOSJA12123', request.user.get_lang_mode(), showMsgId=False) + str(target_execution) + ' \n'
                        add_msg = add_msg + get_message('MOSJA12124', request.user.get_lang_mode(), showMsgId=False) + target_drivertype + ' \n'
                        add_msg = add_msg + get_message('MOSJA12125', request.user.get_lang_mode(), showMsgId=False) + target_actparainfo + ' \n'
                        add_msg = add_msg + get_message('MOSJA12126', request.user.get_lang_mode(), showMsgId=False) + target_actpreinfo  + ' \n'
                    else:
                        add_msg  = match_rulename + get_message('MOSJA12127', request.user.get_lang_mode(), showMsgId=False)  + '\n\n'
                        add_msg = add_msg + get_message('MOSJA12141', request.user.get_lang_mode(), showMsgId=False) + '\n'
                        add_msg = add_msg + get_message('MOSJA12122', request.user.get_lang_mode(), showMsgId=False) + target_rule  + ' \n'
                        add_msg = add_msg + get_message('MOSJA12123', request.user.get_lang_mode(), showMsgId=False) + str(target_execution) + ' \n'
                        add_msg = add_msg + get_message('MOSJA12124', request.user.get_lang_mode(), showMsgId=False) + target_drivertype + ' \n'
                        add_msg = add_msg + get_message('MOSJA12125', request.user.get_lang_mode(), showMsgId=False) + target_actparainfo + ' \n'
                        add_msg = add_msg + get_message('MOSJA12126', request.user.get_lang_mode(), showMsgId=False) + target_actpreinfo + ' \n'

            err_flg = 0

    except OASEError as e:
        if e.log_id:
            if e.arg_list and isinstance(e.arg_list, list):
                logger.logic_log(e.log_id, *(e.arg_list), request=request)
            else:
                logger.logic_log(e.log_id, request=request)

        if e.msg_id:
            if e.arg_dict and isinstance(e.arg_dict, dict):
                msg = get_message(e.msg_id, request.user.get_lang_mode(), **(e.arg_dict))
            else:
                msg = get_message(e.msg_id, request.user.get_lang_mode())

        is_finish = RuleDefs.RULE_FINISH_STS_NG

    except Exception:
        logger.system_log('LOSM12000', traceback.format_exc(), request=request)
        is_finish = RuleDefs.RULE_FINISH_STS_NG
        if not msg:
            msg = get_message('MOSJA12001', request.user.get_lang_mode())

    msg = makePseudoCallMessage(msg, reception_dt, event_dt, req_list, request.user.get_lang_mode(), add_msg)

    resp_json = {
        'err_flg': err_flg,
        'is_finish': is_finish,
        'msg': msg,
        'trace_id': trace_id,
    }

    resp_json = json.dumps(resp_json, ensure_ascii=False)

    logger.logic_log('LOSI00002', resp_json, request=request)

    return HttpResponse(resp_json)


@check_allowed_auth(MENU_ID_STG, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def rule_upload(request):
    """
    [メソッド概要]
      ルールファイルアップロードを処理する
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    msg = ''
    filepath = ''
    response_data = {}
    lang = request.user.get_lang_mode()
    try:
        ####################################################
        # アップロードファイルチェック
        ####################################################
        # ファイル名チェック
        rulefile = request.FILES['rulefile']
        filename = rulefile.name
        if not rulefile or not filename:
            msg = get_message('MOSJA03004', lang)
            logger.system_log('LOSM12013', request=request)
            raise Exception()

        # 拡張子チェック
        if not (filename.endswith('.xls') or filename.endswith('.xlsx')):
            msg = get_message('MOSJA03005', lang)
            logger.system_log('LOSM12014', request=request)
            raise Exception()

        # サイズチェック
        if rulefile.size > RuleDefs.MAX_RULEFILE_SIZE:
            msg = get_message('MOSJA03006', lang, maxbytes=RuleDefs.MAX_MB_SIZE)
            logger.system_log('LOSM12015', RuleDefs.MAX_MB_SIZE, request=request)
            raise Exception()

        # チェックOKの場合、ファイルデータ取得
        filedata = ''
        for chunk in rulefile.chunks():
            filedata = '%s%s' % (filedata, base64.b64encode(chunk).decode('utf-8'))

        ####################################################
        # アップロードファイルからルール種別IDを判断する
        ####################################################
        # パスが存在しない場合、ディレクトリを作成
        temppath = RuleDefs.FILE_TEMP_PATH
        os.makedirs(temppath, exist_ok=True)

        # 一意のファイル名で保存
        tempname = '%s%s' % (str(uuid.uuid4()), request.user.user_id)
        filepath = '%s/%s' % (temppath, tempname)
        with open(filepath, 'wb') as fp:
            fp.write(base64.b64decode(filedata.encode('utf-8')))

        # Excelからルールテーブル名を取得
        error_flag, ret_str = DecisionTableComponent.get_tablename_by_excel(filepath)
        if error_flag == 1:
            msg = get_message(ret_str, lang)
            logger.logic_log('LOSM03004', '%s%s' % (temppath, rulefile.name), request=request)
            raise Exception()
        else:
            table_name = ret_str

        # ルールテーブル名からルール種別IDを取得
        ruletype   = RuleType.objects.get(rule_table_name=table_name)
        ruletypeid = ruletype.rule_type_id

        # 一時ファイル削除
        os.remove(filepath)

        # ルール別アクセス権限チェック
        rule_ids = []
        for chk_auth in defs.MENU_CATEGORY.ALLOW_ADMIN:
            rule_ids.extend(request.user_config.get_activerule_auth_type(MENU_ID_STG, chk_auth))

        if ruletypeid not in rule_ids:
            raise OASEError('MOSJA12031', 'LOSI12012', msg_params={'opename':get_message('MOSJA12038', lang, showMsgId=False), 'rule_type_name':ruletype.rule_type_name}, log_params=['Upload', ruletypeid, rule_ids])

        # 適用君へアップロード要求
        send_data = {
            'request'    : 'UPLOAD',
            'ruletypeid' : ruletypeid,
            'filename'   : filename,
            'filedata'   : filedata,
            'upload_user_id' : request.user.user_id,
        }
        result, msgid = RequestToApply.operate(send_data, request=request)

        # resultとmsgを変換
        if result:
            response_data['result'] = 'OK'
            response_data['msg'] = get_message(msgid, lang, showMsgId=False)
        else:
            response_data['result'] = 'NG'
            response_data['msg'] = get_message(msgid, lang)

    except OASEError as e:
        if e.log_id:
            if e.arg_list and isinstance(e.arg_list, list):
                logger.logic_log(e.log_id, *(e.arg_list), request=request)
            else:
                logger.logic_log(e.log_id, request=request)

        if e.msg_id:
            if e.arg_dict and isinstance(e.arg_dict, dict):
                msg = get_message(e.msg_id, lang, **(e.arg_dict))
            else:
                msg = get_message(e.msg_id, lang)

        response_data['result'] = 'NG'
        response_data['msg'] = msg

        if filepath and os.path.exists(filepath):
            os.remove(filepath)

    except Exception as e:
        logger.system_log('LOSM12003', traceback.format_exc(), request=request)
        response_data['result'] = 'NG'
        response_data['msg'] = msg if msg else get_message('MOSJA03007', lang)

        if filepath and os.path.exists(filepath):
            os.remove(filepath)

    resp_json = json.dumps(response_data, ensure_ascii=False)

    logger.logic_log('LOSI00002', resp_json, request=request)

    return HttpResponse(resp_json, status=None)


@check_allowed_auth([MENU_ID_STG, MENU_ID_PRD], defs.MENU_CATEGORY.ALLOW_EVERY)
def rule_download(request, rule_manage_id):
    """
    [メソッド概要]
      ルールファイルダウンロードを処理する
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    content_type='application/excel'

    try:
        file_name_expansion = ''

        if '_testrequest' in rule_manage_id:
            tmp_list = rule_manage_id.split('_')
            rule_manage_id = tmp_list[0]
            file_name_expansion = '_testrequest.xlsx'

        # ルール種別判定
        rule_manage = RuleManage.objects.get(pk=int(rule_manage_id))
        ruletypeid = rule_manage.rule_type_id

        send_data = {
            'request': 'DOWNLOAD',
            'ruletypeid': ruletypeid,
            'rule_manage_id': rule_manage_id,
            'file_name_expansion': file_name_expansion,
        }

        # ルール別アクセス権限チェック
        menu_id = 0
        if rule_manage.request_type_id == defs.PRODUCTION:
            menu_id = MENU_ID_PRD

        elif rule_manage.request_type_id == defs.STAGING:
            menu_id = MENU_ID_STG

        rule_ids = []
        for chk_auth in defs.MENU_CATEGORY.ALLOW_EVERY:
            rule_ids.extend(request.user_config.get_activerule_auth_type(menu_id, chk_auth))

        if ruletypeid not in rule_ids:
            ruletypename = RuleType.objects.get(rule_type_id=ruletypeid).rule_type_name
            raise OASEError('MOSJA12031', 'LOSI12012', msg_params={'opename':get_message('MOSJA00077', request.user.get_lang_mode(), showMsgId=False), 'rule_type_name':ruletypename}, log_params=['Download', ruletypeid, rule_ids])

        # 異常終了の場合はzipをリクエストする
        if rule_manage.system_status in (
            defs.RULE_STS_SYSTEM.UPLOAD_NG,
            defs.RULE_STS_SYSTEM.BUILD_NG,
            defs.RULE_STS_SYSTEM.STAGING_NG,
            defs.RULE_STS_SYSTEM.PRODUCT_NG
        ):
            send_data['request'] = 'DOWNLOAD_ZIP'
            content_type = 'application/zip'


        # 適用君へ新規ルール作成リクエスト送信
        result, msgid, filename, filedata  = RequestToApply.getfile(send_data, request=request)

        # 適用君異常
        if not result:
            logger.logic_log('LOSM03003', msgid, request=request)
            raise

        response = HttpResponse(filedata, content_type=content_type)
        response['Content-Disposition'] = "attachment; filename*=UTF-8''%s" % (urllib.parse.quote(filename))

        logger.logic_log('LOSI00002', 'filename=%s' % (filename), request=request)

        return response

    except OASEError as e:
        if e.log_id:
            if e.arg_list and isinstance(e.arg_list, list):
                logger.logic_log(e.log_id, *(e.arg_list), request=request)
            else:
                logger.logic_log(e.log_id, request=request)

        if e.msg_id:
            if e.arg_dict and isinstance(e.arg_dict, dict):
                msg = get_message(e.msg_id, request.user.get_lang_mode(), **(e.arg_dict))
            else:
                msg = get_message(e.msg_id, request.user.get_lang_mode())

        return HttpResponse(request, status=500)

    except Exception as e:
        logger.system_log('LOSM12004', traceback.format_exc(), request=request)
        logger.logic_log('LOSI00002', e, request=request)

        return HttpResponse(request, status=500)


@check_allowed_auth(MENU_ID_PRD, defs.MENU_CATEGORY.ALLOW_ADMIN)
def rule_switchback(request, rule_manage_id):
    """
    [メソッド概要]
      ルール切り戻しを処理する
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    msg = ''
    response_data = {}

    try:
        # 切り戻しルールチェック
        try:
            ruleManage = RuleManage.objects.get(rule_manage_id=rule_manage_id)
            rule_type_id = ruleManage.rule_type_id
            ruletype = RuleType.objects.get(pk=rule_type_id)

        except RuleManage.DoesNotExist:
            msg = get_message('MOSJA03010', request.user.get_lang_mode())
            logger.system_log('LOSM12016', request=request)
            raise

        except RuleType.DoesNotExist:
            msg = get_message('MOSJA03011', request.user.get_lang_mode())
            logger.system_log('LOSM12017', request=request)
            raise

        # ルール別アクセス権限チェック
        rule_ids = []
        for chk_auth in defs.MENU_CATEGORY.ALLOW_ADMIN:
            rule_ids.extend(request.user_config.get_activerule_auth_type(MENU_ID_PRD, chk_auth))

        if rule_type_id not in rule_ids:
            raise OASEError('MOSJA12031', 'LOSI12012', msg_params={'opename':get_message('MOSJA12046', request.user.get_lang_mode(), showMsgId=False), 'rule_type_name':ruletype.rule_type_name}, log_params=['SwitchBack', rule_type_id, rule_ids])

        # 切り戻しルールの状態チェック
        if ruleManage.request_type_id != defs.PRODUCTION:
            raise OASEError('MOSJA03001', 'LOSM03002', log_params=[ruleManage.request_type_id, defs.PRODUCTION])

        if not _is_switchbackable(ruleManage.system_status, ruleManage.operation_status):
            raise OASEError('MOSJA12033', 'LOSM03009', log_params=[ruleManage.system_status, [defs.RULE_STS_SYSTEM.PRODUCT_NG, defs.RULE_STS_SYSTEM.PRODUCT_OK], ruleManage.operation_status, [defs.RULE_STS_OPERATION.PRODUCT_NOAPPLY, defs.RULE_STS_OPERATION.PRODUCT_END]])

        # 適用君へルール切り戻しリクエスト送信
        send_data = {
            'request': 'APPLY',
            'ruletypeid': rule_type_id,
            'groupid': ruletype.group_id,
            'artifactid': ruletype.artifact_id,
            'rule_file_id': ruleManage.rule_file_id,
            'request_type_id': defs.PRODUCTION,
            'apply_user_id': request.user.user_id,
            'rule_manage_id': rule_manage_id,
        }

        result, msgid = RequestToApply.operate(send_data, request=request)

        if result:
            response_data['result'] = 'OK'
            response_data['msg'] = get_message(msgid, request.user.get_lang_mode(), showMsgId=False)
        else:
            response_data['result'] = 'NG'
            response_data['msg'] = get_message(msgid, request.user.get_lang_mode())
            logger.system_log('LOSM12005', '', request=request)

    except OASEError as e:
        if e.log_id:
            if e.arg_list and isinstance(e.arg_list, list):
                logger.logic_log(e.log_id, *(e.arg_list), request=request)
            else:
                logger.logic_log(e.log_id, request=request)

        if e.msg_id:
            if e.arg_dict and isinstance(e.arg_dict, dict):
                msg = get_message(e.msg_id, request.user.get_lang_mode(), **(e.arg_dict))
            else:
                msg = get_message(e.msg_id, request.user.get_lang_mode())

        response_data['result'] = 'NG'
        response_data['msg'] = msg if msg else get_message('MOSJA03008', request.user.get_lang_mode())

    except Exception:
        response_data['result'] = 'NG'
        response_data['msg'] = msg if msg else get_message('MOSJA03008', request.user.get_lang_mode())
        logger.system_log('LOSM12005', traceback.format_exc(), request=request)

    logger.logic_log('LOSI00002', response_data['result'], request=request)

    return HttpResponse(json.dumps(response_data, ensure_ascii=False), status=None)


@check_allowed_auth(MENU_ID_PRD, defs.MENU_CATEGORY.ALLOW_ADMIN)
def rule_apply(request, rule_manage_id, request_type_id):
    """
    [メソッド概要]
      ルールプロダクション適用を処理する
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    msg = ''
    response_data = {}

    try:
        # 適用前ルールチェック
        if int(request_type_id) != defs.PRODUCTION:
            msg = get_message('MOSJA03001', request.user.get_lang_mode())
            logger.user_log('LOSM03002', request_type_id, defs.PRODUCTION, request=request)
            raise

        try:
            rule_manage = RuleManage.objects.get(pk=rule_manage_id)
            rulefile = RuleFile.objects.get(pk=rule_manage.rule_file_id)
            ruletype = RuleType.objects.get(pk=rule_manage.rule_type_id)

        except RuleManage.DoesNotExist:
            msg = get_message('MOSJA03010', request.user.get_lang_mode())
            logger.system_log('LOSM12016', request=request)
            raise

        except RuleFile.DoesNotExist:
            msg = get_message('MOSJA03013', request.user.get_lang_mode())
            logger.system_log('LOSM12019', request=request)
            raise

        except RuleType.DoesNotExist:
            msg = get_message('MOSJA03011', request.user.get_lang_mode())
            logger.system_log('LOSM12017', request=request)
            raise


        # ルール別アクセス権限チェック
        rule_ids = []
        for chk_auth in defs.MENU_CATEGORY.ALLOW_ADMIN:
            rule_ids.extend(request.user_config.get_activerule_auth_type(MENU_ID_PRD, chk_auth))

        if ruletype.rule_type_id not in rule_ids:
            raise OASEError('MOSJA12031', 'LOSI12012', msg_params={'opename':get_message('MOSJA12100', request.user.get_lang_mode(), showMsgId=False), 'rule_type_name':ruletype.rule_type_name}, log_params=['Apply', ruletype.rule_type_id, rule_ids])

        # ステージング適用チェック
        is_staging = False
        if rule_manage.request_type_id == defs.STAGING:
            is_staging = True
        else:
            msg = get_message('MOSJA03012', request.user.get_lang_mode())
            logger.user_log('LOSM12018', request=request)
            raise Exception()

        # ステージング状態チェック
        if rule_manage.operation_status != defs.RULE_STS_OPERATION.STAGING:
            msg = get_message('MOSJA03014', request.user.get_lang_mode())
            logger.user_log('LOSM12020', request=request)
            raise Exception()

        # 適用君へルールプロダクション適用をリクエスト送信
        send_data = {
            'request': 'APPLY',
            'ruletypeid': rule_manage.rule_type_id,
            'groupid': ruletype.group_id,
            'artifactid': ruletype.artifact_id,
            'rule_file_id': rule_manage.rule_file_id,
            'request_type_id': defs.PRODUCTION,
            'apply_user_id': request.user.user_id,
            'rule_manage_id': rule_manage_id,
        }
        result, msgid = RequestToApply.operate(send_data, request=request)

        if result:
            response_data['result'] = 'OK'
            response_data['msg'] = get_message(msgid, request.user.get_lang_mode(), showMsgId=False)
        else:
            response_data['result'] = 'NG'
            response_data['msg'] = get_message(msgid, request.user.get_lang_mode())
            logger.system_log('LOSM12006', '', request=request)

    except OASEError as e:
        if e.log_id:
            if e.arg_list and isinstance(e.arg_list, list):
                logger.logic_log(e.log_id, *(e.arg_list), request=request)
            else:
                logger.logic_log(e.log_id, request=request)

        if e.msg_id:
            if e.arg_dict and isinstance(e.arg_dict, dict):
                msg = get_message(e.msg_id, request.user.get_lang_mode(), **(e.arg_dict))
            else:
                msg = get_message(e.msg_id, request.user.get_lang_mode())

        response_data['result'] = 'NG'
        response_data['msg'] = msg if msg else get_message('MOSJA03009', request.user.get_lang_mode())

    except Exception:
        response_data['result'] = 'NG'
        response_data['msg'] = msg if msg else get_message('MOSJA03009', request.user.get_lang_mode())
        logger.system_log('LOSM12006', traceback.format_exc(), request=request)

    response_json = json.dumps(response_data, ensure_ascii=False)

    logger.logic_log('LOSI00002', response_data['result'], request=request)

    return HttpResponse(response_json)


def _getRuleTypeData(request=None):
    """
    [メソッド概要]
      データ更新処理
    """

    logger.logic_log('LOSI00001', '', request=request)

    rule_types = RuleType.objects.all()
    rule_type_list = rule_types.values('rule_type_id', 'rule_type_name')
    rule_type_dict = {rt.rule_type_id:{'name': rt.rule_type_name, 'table': rt.rule_table_name,} for rt in rule_types}

    logger.logic_log('LOSI00002', 'rule_type_dict: %s' % json.dumps(rule_type_dict, ensure_ascii=False), request=request)

    return rule_type_list, rule_type_dict


def _select(filters={}, request=None):
    """
    [メソッド概要]
      ルールのデータ取得
    """

    logger.logic_log('LOSI00001', 'filters: %s' % (filters), request=request)

    rule_list = []

    # ルール管理情報取得
    where_info = {}
    WebCommon.convert_filters(filters, where_info)
    rule_manage_list = RuleManage.objects.filter(**where_info).order_by('rule_manage_id').reverse()

    #==================グループ情報取得==================#
    _, rule_type_dict = _getRuleTypeData(request)

    #==================ルールファイル情報取得==================#
    rule_file_ids = [rm.rule_file_id for rm in rule_manage_list]
    rule_file_list = RuleFile.objects.filter(pk__in=rule_file_ids)
    rule_file_dict = {rf.rule_file_id: rf.rule_file_name for rf in rule_file_list}

    # グループ情報作成
    for rm in rule_manage_list:

        operation_status_str = get_message(RuleDefs.MST_STS_OPERATION[rm.operation_status],request.user.get_lang_mode(), showMsgId=False)
        system_status_str = get_message(
            RuleDefs.MST_STS_SYSTEM[rm.system_status], request.user.get_lang_mode(), showMsgId=False)

        rule_info_dic = {
            'request_type_id': rm.request_type_id,
            'rule_manage_id': rm.rule_manage_id,
            'rule_type_id': rm.rule_type_id,
            'rule_type_name': rule_type_dict[rm.rule_type_id]['name'],
            'rule_table_name': rule_type_dict[rm.rule_type_id]['table'],
            'rule_file_id': rm.rule_file_id,
            'filename': rule_file_dict[rm.rule_file_id],
            'operation_status_id': rm.operation_status,
            'operation_status_str': operation_status_str,
            'system_status_id': rm.system_status,
            'system_status_str': system_status_str,
            'last_update_user_name': rm.last_update_user,
            'last_update_timestamp': rm.last_update_timestamp,
            'is_finish': True if rm.system_status in defs.RULE_STS_SYSTEM.FINISH_STATUS else False,
            'is_switchback': _is_switchbackable(rm.system_status, rm.operation_status),
        }
        rule_list.append(rule_info_dic)

    logger.logic_log('LOSI00002', 'hit_count: %s' % str(len(rule_list)), request=request)

    return rule_list

def _select_staging(filters, perm_info_stg, request):
    """
    [概要]
    ステージングルールのデータ取得
    [引数]
    filters: _select()に基づくfilters. {}でも可。
    perm_info_stg: ステージング権限
    [戻り値]
    rule_list: ステージングルール
    """

    logger.logic_log('LOSI00001', 'filters: %s' % (filters))

    # 参照以上の権限を持つルール種別IDを取得し、フィルター条件に追加
    rule_ids_stg_view = perm_info_stg[defs.VIEW_ONLY]
    rule_ids_stg_admin = perm_info_stg[defs.ALLOWED_MENTENANCE]
    rule_ids_stg = rule_ids_stg_view + rule_ids_stg_admin

    if 'rule_type_id' not in filters:
        filters['rule_type_id'] = {}

    if 'LIST' not in filters['rule_type_id']:
        filters['rule_type_id']['LIST'] = []

    filters['rule_type_id']['LIST'].extend(rule_ids_stg)
    filters['request_type_id'] = {'LIST': [defs.STAGING]}

    rule_list = _select(filters, request)
    staging_list, staging_history_list = _filter_staging_rule(rule_list)

    logger.logic_log('LOSI00002', 'staging_rule count: %s' % str(len(rule_list)))
    return staging_list, staging_history_list

def _select_production(filters, perm_info_prd, request):
    """
    [概要]
    プロダクションルールのデータ取得
    [引数]
    filters: _select()に基づくfilters. {}でも可。
    perm_info_prd: プロダクション権限
    [戻り値]
    rule_product_list: 適用中ルール
    rule_history_list: 適用終了ルール
    """

    logger.logic_log('LOSI00001', 'filters: %s' % (filters))

    rule_product_list = []
    rule_history_list = []

    # 参照以上の権限を持つルール種別IDを取得し、フィルター条件に追加
    rule_ids_prd_view  = perm_info_prd[defs.VIEW_ONLY]
    rule_ids_prd_admin = perm_info_prd[defs.ALLOWED_MENTENANCE]
    rule_ids_prd = rule_ids_prd_view + rule_ids_prd_admin

    if 'rule_type_id' not in filters:
        filters['rule_type_id'] = {}

    if 'LIST' not in filters['rule_type_id']:
        filters['rule_type_id']['LIST'] = []

    filters['rule_type_id']['LIST'].extend(rule_ids_prd)
    filters['request_type_id'] = {'LIST': [defs.PRODUCTION]}

    rule_list = _select(filters, request)

    # 運用ステータスにより、適用中／適用終了ルールを振り分ける
    noapply_type_ids = []
    for r in rule_list:
        # 未適用ステータス
        if r['operation_status_id'] == defs.RULE_STS_OPERATION.PRODUCT_NOAPPLY:
            # 最新の1件のみを適用中に振り分ける
            if r['rule_type_id'] not in noapply_type_ids:
                rule_product_list.append(r)

            # 最新でなければ適用終了に振り分ける
            else:
                rule_history_list.append(r)

            noapply_type_ids.append(r['rule_type_id'])

        # 適用中ステータス
        elif r['operation_status_id'] == defs.RULE_STS_OPERATION.PRODUCT:
            rule_product_list.append(r)

        # 適用終了ステータス
        elif r['operation_status_id'] == defs.RULE_STS_OPERATION.PRODUCT_END:
            rule_history_list.append(r)

        # 不明なステータス
        else:
            logger.logic_log('LOSM12070', r['operation_status_id'], r['rule_manage_id'])


    logger.logic_log('LOSI00002', 'production_rule count: %s' % str(len(rule_list)))
    return rule_product_list, rule_history_list


def _is_switchbackable(sys_sts, ope_sts):
    """
    [概要]
    切り戻し可否フラグ判定
    [引数]
    sys_sts: 作業ステータス
    ope_sts: 運用ステータス
    [戻り値]
    bool   : True=可能、False=不可
    """

    if  sys_sts in [defs.RULE_STS_SYSTEM.PRODUCT_NG, defs.RULE_STS_SYSTEM.PRODUCT_OK] \
    and ope_sts in [defs.RULE_STS_OPERATION.PRODUCT_NOAPPLY, defs.RULE_STS_OPERATION.PRODUCT_END]:
        return True

    return False



@check_allowed_auth(MENU_ID_STG, defs.MENU_CATEGORY.ALLOW_EVERY)
@require_POST
def bulkpseudocall(request, rule_type_id):
    """
    [メソッド概要]
      テストリクエストの一括実行を処理する
    """

    errmsg = ''
    response_data  = {}
    rule_data_list = []
    message_list   = []
    trace_id_list  = []

    reception_dt = datetime.datetime.now(pytz.timezone('UTC'))
    reception_dt = TimeConversion.get_time_conversion(reception_dt, 'Asia/Tokyo', request=request)

    logger.logic_log('LOSI00001', 'rule_type_id: %s' % rule_type_id, request=request)

    try:
        # データの取得
        rule_data_list, errmsg, message_list = _testrequest_upload(request, rule_type_id)

        if errmsg:
            logger.system_log('LOSM12003', 'rule_data_list:%s' % rule_data_list, request=request)
            raise Exception

        # ルール別アクセス権限チェック
        rule_ids = []
        for chk_auth in defs.MENU_CATEGORY.ALLOW_EVERY:
            rule_ids.extend(request.user_config.get_activerule_auth_type(MENU_ID_STG, chk_auth))

        rt = RuleType.objects.get(rule_type_id=rule_type_id)
        if rt.rule_type_id not in rule_ids:
            raise OASEError('MOSJA12031', 'LOSI12012', msg_params={'opename':get_message('MOSJA12035', request.user.get_lang_mode(), showMsgId=False), 'rule_type_name':rt.rule_type_name}, log_params=['Bulk Request', rt.rule_type_id, rule_ids])

        ####################################################
        # リクエスト送信
        ####################################################
        rule_table_name_list = list(RuleType.objects.filter(rule_type_id=rule_type_id).values('rule_table_name'))
        rule_table_name_dic = rule_table_name_list[0]
        rule_table_name = rule_table_name_dic['rule_table_name']

        scheme = urlsplit(request.build_absolute_uri(None)).scheme
        url = scheme + '://127.0.0.1:' + request.META['SERVER_PORT'] + reverse('web_app:event:eventsrequest')
        for rule_dic in rule_data_list:
            row = ''
            event_time = ''
            event_info = []

            for k, v in rule_dic.items():
                if k == 'eventtime':
                    event_time = str(v)
                    continue
                if k == 'row':
                    row = str(v)
                    continue
                event_info.append(v)

            # リクエストをJSON形式に変換
            json_str = {}
            json_str[EventsRequestCommon.KEY_RULETYPE]  = rule_table_name
            json_str[EventsRequestCommon.KEY_REQTYPE]   = defs.STAGING
            json_str[EventsRequestCommon.KEY_EVENTTIME] = event_time
            json_str[EventsRequestCommon.KEY_EVENTINFO] = event_info
            json_str = json.dumps(json_str)

            r_content = None
            r = requests.post(
                url,
                headers={'content-type': 'application/json'},
                data=json_str.encode('utf-8'),
                verify=False
            )

            # レスポンスからデータを取得
            r_content = json.loads(r.content.decode('utf-8'))

            # テストリクエストの実行中に失敗した場合
            if not r_content["result"]:
                errmsg = r_content["msg"]
                logger.user_log('LOSM12060', traceback.format_exc())
                raise

            if r_content is not None and r_content['trace_id']:
                trace_id_list.append({'id':r_content['trace_id'], 'row':row})

        response_data['result'] = 'OK'
        response_data['msg'] = get_message('MOSJA03015', request.user.get_lang_mode(), showMsgId=False)
        response_data['trace'] = trace_id_list
        response_data['recept'] = reception_dt
        response_data['filename'] = request.FILES['testreqfile'].name
        response_data['log_msg']  = makePseudoCallMessage_Bulk('', reception_dt, request.FILES['testreqfile'].name, 0, len(trace_id_list),request.user.get_lang_mode())

    except json.JSONDecodeError:
        response_data['result'] = 'NG'
        response_data['msg'] = get_message('MOSJA12012', request.user.get_lang_mode())
        logger.user_log('LOSM12052')

    except OASEError as e:
        if e.log_id:
            if e.arg_list and isinstance(e.arg_list, list):
                logger.logic_log(e.log_id, *(e.arg_list), request=request)
            else:
                logger.logic_log(e.log_id, request=request)

        if e.msg_id:
            if e.arg_dict and isinstance(e.arg_dict, dict):
                msg = get_message(e.msg_id, request.user.get_lang_mode(), **(e.arg_dict))
            else:
                msg = get_message(e.msg_id, request.user.get_lang_mode())

        response_data['result'] = 'NG'
        response_data['msg'] = msg

    except Exception as e:
        response_data['result'] = 'NG'
        response_data['msg'] = errmsg if errmsg else get_message('MOSJA03001', request.user.get_lang_mode())
        logger.system_log('LOSM12060', 'rule_data_list:%s, %s' % (rule_data_list,traceback.format_exc()), request=request)

    if len(message_list) > 0:
        response_data['log_msg'] = '\n' .join(message_list) + '\n'

    resp_json = json.dumps(response_data, ensure_ascii=False)
    logger.logic_log('LOSI00002', resp_json, request=request)

    return HttpResponse(resp_json, status=None)


@check_allowed_auth(MENU_ID_STG, defs.MENU_CATEGORY.ALLOW_EVERY)
@require_POST
def rule_polling_bulk(request, rule_manage_id):
    """
    [メソッド概要]
      一括テストリクエスト実行中のポーリングリクエストを処理する
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    resp_json  = {}
    err_flg    = 1
    is_finish  = RuleDefs.RULE_FINISH_STS_NG
    msg        = ''
    recept     = ''
    filename   = ''
    trace_list = []


    try:
        # パラメーター取得
        recept     = request.POST.get('recept',    '')
        filename   = request.POST.get('filename',  '')
        trace_list = request.POST.get('trace_ids', None)

        if trace_list is None:
            logger.user_log('LOSM12063', request=request)
            raise Exception()

        trace_list = ast.literal_eval(trace_list)

        trace_ids  = []
        trace_info = {}
        for trc in trace_list:
            trace_ids.append(trc['id'])

            trace_info[trc['id']] = {}
            trace_info[trc['id']]['row'] = int(trc['row'])
            trace_info[trc['id']]['sts'] = ''
            trace_info[trc['id']]['msg'] = ''
            trace_info[trc['id']]['respid'] = 0

        logger.logic_log('LOSI12009', str(len(trace_ids)), recept, filename, request=request)

        # ルール別アクセス権限チェック
        rule_ids = []
        for chk_auth in defs.MENU_CATEGORY.ALLOW_EVERY:
            rule_ids.extend(request.user_config.get_activerule_auth_type(MENU_ID_STG, chk_auth))

        rule_manage = RuleManage.objects.get(pk=rule_manage_id)
        if rule_manage.rule_type_id not in rule_ids:
            ruletypename = RuleType.objects.get(rule_type_id=rule_manage.rule_type_id).rule_type_name
            raise OASEError('MOSJA12031', 'LOSI12012', msg_params={'opename':get_message('MOSJA12035', request.user.get_lang_mode(), showMsgId=False), 'rule_type_name':ruletypename}, log_params=['Bulk Polling', rule_manage.rule_type_id, rule_ids])

        # 対象のリクエスト情報を取得
        ev_req_list = []
        if len(trace_ids) > 0:
            ev_req_list = EventsRequest.objects.filter(trace_id__in=trace_ids).order_by('request_id').values('trace_id', 'status')

        # リクエスト状態チェック
        ope_sts      = None
        finish_sts   = {'OK':0, 'NG':0, 'EXE':0}
        ok_trace_ids = []

        for evreq in ev_req_list:

            if evreq['trace_id'] in trace_info:
                # 状態取得
                rule_info = RuleDefs.get_rulestatus_info(evreq['status'],request.user.get_lang_mode())

                # 状態をカウント
                if rule_info['is_finish'] == RuleDefs.RULE_FINISH_STS_OK:
                    finish_sts['OK'] += 1
                    ok_trace_ids.append(evreq['trace_id'])

                elif rule_info['is_finish'] == RuleDefs.RULE_FINISH_STS_NG:
                    finish_sts['NG'] += 1

                elif rule_info['is_finish'] == RuleDefs.RULE_FINISH_STS_EXE:
                    finish_sts['EXE'] += 1

                # 全リクエスト完了した際の状態遷移情報を保持
                if rule_info['ope_sts'] and ope_sts != defs.RULE_STS_OPERATION.STAGING_NG:
                    ope_sts = rule_info['ope_sts']

                # リクエスト別のメッセージを保持
                trace_info[evreq['trace_id']]['sts'] = rule_info['sts']
                trace_info[evreq['trace_id']]['msg'] = rule_info['msg']


        # 正常終了リクエストのマッチングルール情報を取得
        resp_ids  = []
        resp_acts = []
        act_types = {}

        if len(ok_trace_ids) > 0:
            rset = RhdmResponse.objects.filter(trace_id__in=ok_trace_ids).values('trace_id', 'response_id')
            for rs in rset:
                trace_info[rs['trace_id']]['respid'] = rs['response_id']
                resp_ids.append(rs['response_id'])

        resp_act_info = {}
        if len(resp_ids) > 0:
            dti  = ActionType.objects.filter(disuse_flag='0').values_list('driver_type_id', flat=True)
            rset = DriverType.objects.filter(driver_type_id__in=dti).values('name', 'driver_major_version')

            ati = []
            for rs in rset:
                name_version = rs['name'] + '(ver' + str(rs['driver_major_version']) + ')'
                ati.append(name_version)

            act_types = dict(zip(dti, ati))

            rset = RhdmResponseAction.objects.filter(response_id__in=resp_ids).values('response_id', 'rule_name', 'execution_order', 'action_type_id', 'action_parameter_info', 'action_pre_info')
            for rs in rset:
                if rs['response_id'] not in resp_act_info:
                    resp_act_info[rs['response_id']] = []

                str_actparams = json.loads(rs['action_parameter_info'])
                str_actparams = '%s' % (str_actparams['ACTION_PARAMETER_INFO'])

                str_actpreinfo = ''
                if not rs['action_pre_info']:
                    str_actpreinfo = get_message('MOSJA12154', request.user.get_lang_mode(), showMsgId=False)

                else:
                    str_actpreinfo = get_message('MOSJA12155', request.user.get_lang_mode(), showMsgId=False)

                resp_act_info_tmp = {}
                resp_act_info_tmp['rulename']   = rs['rule_name']
                resp_act_info_tmp['exeorder']   = rs['execution_order']
                resp_act_info_tmp['acttype']    = act_types[rs['action_type_id']] if rs['action_type_id'] in act_types else get_message('MOSJA12156', request.user.get_lang_mode(), showMsgId=False)
                resp_act_info_tmp['actparam']   = str_actparams
                resp_act_info_tmp['actpreinfo'] = str_actpreinfo

                resp_act_info[rs['response_id']].append(resp_act_info_tmp)


        # 全リクエスト完了、および、状態遷移情報ありの場合は、状態を遷移させる
        if ope_sts and finish_sts['EXE'] <= 0:
            with transaction.atomic():
                rule_manage = RuleManage.objects.select_for_update().get(pk=rule_manage_id)

                if rule_manage.operation_status in RuleDefs.STAGING_VALIDATE_STATUSES:
                    rule_manage.operation_status = ope_sts
                    rule_manage.last_update_timestamp = datetime.datetime.now(pytz.timezone('UTC'))
                    rule_manage.last_update_user = request.user.user_name
                    rule_manage.save()


        # 応答情報作成
        for k, v in sorted(trace_info.items(), key=lambda x: x[1]['row']):

            msg += '%s' % (v['row']) + get_message('MOSJA12150', request.user.get_lang_mode(), showMsgId=False)
            if v['respid'] > 0 and v['respid'] in resp_act_info:
                msg += get_message('MOSJA12142', request.user.get_lang_mode(), showMsgId=False) + '%s' % (len(resp_act_info[v['respid']])) + get_message('MOSJA12143', request.user.get_lang_mode(), showMsgId=False) + '\n'

                for i, res_act in enumerate(resp_act_info[v['respid']]):
                    msg = msg + str(i + 1) + get_message('MOSJA12144', request.user.get_lang_mode(), showMsgId=False) + '\n'
                    msg = msg + get_message('MOSJA12145', request.user.get_lang_mode(), showMsgId=False) + res_act['rulename'] + '\n'
                    msg = msg + get_message('MOSJA12146', request.user.get_lang_mode(), showMsgId=False) + str(res_act['exeorder']) + '\n'
                    msg = msg + get_message('MOSJA12147', request.user.get_lang_mode(), showMsgId=False) + res_act['acttype'] + '\n'
                    msg = msg + get_message('MOSJA12148', request.user.get_lang_mode(), showMsgId=False) + res_act['actparam'] + '\n'
                    msg = msg + get_message('MOSJA12149', request.user.get_lang_mode(), showMsgId=False) + res_act['actpreinfo'] + '\n'

            msg += '\n %s \n\n' % (v['msg'])

        msg = makePseudoCallMessage_Bulk(msg, recept, filename, len(trace_ids) - finish_sts['EXE'], len(trace_ids),request.user.get_lang_mode())


        if finish_sts['EXE'] > 0:
            is_finish = RuleDefs.RULE_FINISH_STS_EXE

        else:
            if finish_sts['NG'] > 0:
                is_finish = RuleDefs.RULE_FINISH_STS_NG

            else:
                is_finish = RuleDefs.RULE_FINISH_STS_OK

        err_flg = 0

        logger.logic_log('LOSI12010', finish_sts['OK'], finish_sts['NG'], finish_sts['EXE'], request=request)

    except OASEError as e:
        if e.log_id:
            if e.arg_list and isinstance(e.arg_list, list):
                logger.logic_log(e.log_id, *(e.arg_list), request=request)
            else:
                logger.logic_log(e.log_id, request=request)

        if e.msg_id:
            if e.arg_dict and isinstance(e.arg_dict, dict):
                msg = get_message(e.msg_id, request.user.get_lang_mode(), **(e.arg_dict))
            else:
                msg = get_message(e.msg_id, request.user.get_lang_mode())

        is_finish = RuleDefs.RULE_FINISH_STS_NG

    except Exception:
        logger.system_log('LOSM12000', traceback.format_exc(), request=request)
        is_finish = RuleDefs.RULE_FINISH_STS_NG
        if not msg:
            msg = get_message('MOSJA12001', request.user.get_lang_mode())

    resp_json = {
        'err_flg': err_flg,
        'is_finish': is_finish,
        'msg': msg,
        'recept': recept,
        'filename': filename,
        'trace': trace_list,
    }

    resp_json = json.dumps(resp_json, ensure_ascii=False)

    logger.logic_log('LOSI00002', 'err_flg:%s, is_finish:%s' % (err_flg, is_finish), request=request)

    return HttpResponse(resp_json)



def _testrequest_upload(request, rule_type_id):
    """
    [メソッド概要]
      テストリクエスト用ファイルをtemp/testrequest配下にアップロードする
    """

    logger.logic_log('LOSI00001', 'rule_type_id: %s' % rule_type_id, request=request)

    msg = ''
    filepath = ''
    rule_data_list = []
    message_list = []

    try:

        ####################################################
        # アップロードファイルフォーマットチェック
        ####################################################
        # ファイル名取得
        rulefile = request.FILES['testreqfile']
        filename = rulefile.name

        # 拡張子チェック
        if not (filename.endswith('.xls') or filename.endswith('.xlsx')):
            msg = get_message('MOSJA03005', request.user.get_lang_mode())
            logger.system_log('LOSM12014', request=request)
            raise Exception()

        # チェックOKの場合、ファイルデータ取得
        filedata = ''
        for chunk in rulefile.chunks():
            filedata = '%s%s' % (filedata, base64.b64encode(chunk).decode('utf-8'))

        # パスが存在しない場合、ディレクトリを作成
        temppath = RuleDefs.FILE_TEMP_PATH
        os.makedirs(temppath, exist_ok=True)

        # 一意のファイル名で保存
        tempname = '%s%s' % (str(uuid.uuid4()), request.user.user_id)
        filepath = '%s%s' % (temppath, tempname)
        with open(filepath, 'wb') as fp:
            fp.write(base64.b64decode(filedata.encode('utf-8')))

        ####################################################
        # Excelから条件部のデータを取得
        ####################################################
        rule_data_list, message_list, msg = _get_data_by_excel(request, filepath, filename, rule_type_id)

        if msg:
            logger.system_log('LOSM12000', 'rule_data_list:%s' % rule_data_list, request=request)
            raise Exception(msg)

        # 一時ファイル削除
        os.remove(filepath)

    except Exception as e:
        msg = msg if msg else get_message('MOSJA03007', request.user.get_lang_mode())
        logger.system_log('LOSM12003', traceback.format_exc(), request=request)
        if filepath and os.path.exists(filepath):
            os.remove(filepath)

    logger.logic_log('LOSI00002', rule_data_list, request=request)

    return rule_data_list, msg, message_list


def _get_data_by_excel(request, filepath, filename, rule_type_id):
    """
    [メソッド概要]
      テストリクエスト用エクセルの情報を取得
    [引数]
      filepath : 一時保存先
    [戻り値]
      dict : 取得したデータの配列
    """
    logger.logic_log('LOSI00001', 'filepath: %s, rule_type_id: %s' % (filepath, rule_type_id), request=request)


    # ユーザー入力開始セルの番号
    COL_INDEX_RULE_START = 2
    ROW_INDEX_RULE_START = 2

    # ルール名が記載されている行
    ROW_RULE_NAME_START = 1

    col_max_length = ''
    row_max_length = ''
    rule_data_list = []
    message_list = []
    errmsg = ''

    try:
        wb = xlrd.open_workbook(filepath)
        tables_ws = wb.sheet_by_name('Values')
        col_max_length = tables_ws.ncols
        row_max_length = tables_ws.nrows

        ####################################################
        # フォーマットチェック
        ####################################################
        rule_data_list, message_list = _check_testrequest_data(rule_type_id, filename, tables_ws, ROW_INDEX_RULE_START, COL_INDEX_RULE_START, row_max_length, col_max_length, request.user.get_lang_mode())

        if len(message_list) > 0:
            errmsg = get_message('MOSJA12018', request.user.get_lang_mode())
            logger.system_log('LOSM12062', filename)

        # テストリクエストの上限数チェック
        request_row_max = int(System.objects.get(config_id = 'REQUEST_ROW_MAX').value)
        row_count = len(rule_data_list)
        if request_row_max < row_count:
            errmsg = get_message('MOSJA12018', request.user.get_lang_mode())
            message_list.append(get_message('MOSJA03123', rulerowmax=request_row_max))

    except Exception as e:
        errmsg = get_message('MOSJA03016', request.user.get_lang_mode())
        logger.system_log('LOSM12000', traceback.format_exc())


    logger.logic_log('LOSI00002', 'rule_data_list: %s' % rule_data_list, request=request)
    return rule_data_list, message_list, errmsg



def _check_testrequest_data(rule_type_id, filename, wsheet, row_index, col_index, row_max, col_max, lang):
    """
    [メソッド概要]
      条件部の入力チェック
    """

    rule_data_list = []
    label_list     = ['eventtime'] # イベント発生日時用ラベル名
    cond_id_list   = [0]        # イベント発生日時用cond_id
    message_list   = []
    chk_flag       = False
    cond_id        = ''
    chk_row_max    = 0
    emo_chk        = UnicodeCheck()

    # Excelのセル種別
    CELL_TYPE_EMPTY  = 0
    CELL_TYPE_TEXT   = 1
    CELL_TYPE_NUMBER = 2
    CELL_TYPE_DATE   = 3

    hhmm_repatter = re.compile(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$')
    date_repatter = re.compile(r'^0\.[0-9]+$')
    num_repatter = re.compile(r'^[0-9]+$')
    dec_repatter = re.compile(r'^[0-9]+[.]{1}0+$')

    # データオブジェクトを抽出
    tmp_data_list = list(DataObject.objects.filter(rule_type_id=rule_type_id).order_by('data_object_id'))
    checker = {}
    for dataObj in tmp_data_list:
        if dataObj.label in checker:
            continue
        checker[dataObj.label] = dataObj
    data_object_list = checker.values();

    for dobj in data_object_list:
        label_list.append(dobj.label)
        cond_id_list.append(dobj.conditional_expression_id)

    # シートに記載があればチェック
    for row in range(row_index, row_max):
       for col in range(col_index, col_max):
            if wsheet.cell_type(row, col) != CELL_TYPE_EMPTY:
                chk_flag = True
                chk_row_max = row
                break;

    if not chk_flag:
        message_list.append(get_message('MOSJA12019', lang, filename=filename))
        return rule_data_list, message_list

    for row in range(row_index, chk_row_max + 1):
        chk_flag = False
        index = 0
        rule_data_dic = {}

        # 列のいずれかに記載があればチェック
        col = col_index
        for col in range(col_index, col_max):
            if wsheet.cell_type(row, col) != CELL_TYPE_EMPTY:
                chk_flag = True

        # 最後の表の場合終了
        if not chk_flag and row > chk_row_max:
            break

        if not chk_flag:
            continue

        # 行数を辞書に追加
        rule_data_dic['row'] = row + 1
        col = col_index
        while col < col_max:
            cell_val = ''

            if wsheet.cell_type(row, col) == CELL_TYPE_EMPTY:
                message_list.append(get_message('MOSJA12014', lang, cellname=_convert_rowcol_to_cellno(row, col)))

            if wsheet.cell_type(row, col) == CELL_TYPE_TEXT \
            and wsheet.cell(row, col).value == '':
                message_list.append(get_message('MOSJA12014', lang, cellname=_convert_rowcol_to_cellno(row, col)))

            if index <= len(data_object_list):
                cond_id = cond_id_list[index]

                cell_val = wsheet.cell(row, col).value
                if cond_id == 0:
                    try:
                        cell_val = datetime.datetime.strptime(cell_val, '%Y-%m-%d %H:%M:%S')
                    except Exception as e:
                        message_list.append(get_message('MOSJA12017', lang, cellname=_convert_rowcol_to_cellno(row, col)))

                # 時刻条件
                elif cond_id == 15:
                    cell_val = wsheet.cell(row, col).value

                    if wsheet.cell_type(row, col) == CELL_TYPE_NUMBER:
                        message_list.append(get_message('MOSJA12016', lang, cellname=_convert_rowcol_to_cellno(row, col)))

                    elif wsheet.cell_type(row, col) == CELL_TYPE_TEXT:
                        if not hhmm_repatter.match(cell_val):
                            message_list.append(get_message('MOSJA12016', lang, cellname=_convert_rowcol_to_cellno(row, col)))

                    elif wsheet.cell_type(row, col) == CELL_TYPE_DATE:
                        cell_val_str = str(cell_val)
                        if not date_repatter.match(cell_val_str):
                            message_list.append(get_message('MOSJA12016', lang, cellname=_convert_rowcol_to_cellno(row, col)))

                        # Excelから取得した値からHH:mm方式に変換
                        cell_time = datetime.datetime(1899, 12, 30) + datetime.timedelta(days=cell_val)
                        cell_val = cell_time.strftime("%H:%M")

                # 数値条件
                elif cond_id in [1, 2, 5, 6, 7, 8]:
                    if wsheet.cell_type(row, col) == CELL_TYPE_DATE:
                        _col_name = get_message('MOSJA12151', lang, showMsgId=False)
                        message_list.append(get_message('MOSJA12015', lang, colname=_col_name, cellname=_convert_rowcol_to_cellno(row, col)))

                    elif wsheet.cell_type(row, col) == CELL_TYPE_TEXT:
                        if not num_repatter.match(str(cell_val)):
                            _col_name = get_message('MOSJA12151', lang, showMsgId=False)
                            message_list.append(get_message('MOSJA12015', lang, colname=_col_name, cellname=_convert_rowcol_to_cellno(row, col)))

                    elif wsheet.cell_type(row, col) == CELL_TYPE_NUMBER:
                        # 0 padding 消し？
                        cell_val = int(cell_val)
                        cell_val = str(cell_val)
                        if not num_repatter.match(cell_val) and not dec_repatter.match(cell_val):
                            _col_name = get_message('MOSJA12151', lang, showMsgId=False)
                            message_list.append(get_message('MOSJA12015', lang, colname=_col_name, cellname=_convert_rowcol_to_cellno(row, col)))

                # 文字条件
                elif cond_id in [3, 4, 9, 10]:
                    # 絵文字チェック
                    value_list = emo_chk.is_emotion(cell_val)
                    if len(value_list) > 0:
                        _col_name = get_message('MOSJA12152', lang, showMsgId=False)
                        message_list.append(get_message('MOSJA12028', lang, colname=_col_name, cellname=_convert_rowcol_to_cellno(row, col)))

                # 含む含まない
                elif cond_id in [13, 14]:
                    result = _validate_contains(cell_val)
                    if not result:
                        _col_name = get_message('MOSJA12153', lang, showMsgId=False)
                        message_list.append(get_message('MOSJA12021', lang, colname=_col_name, cellname=_convert_rowcol_to_cellno(row, col)))

                    # 絵文字チェック
                    value_list = emo_chk.is_emotion(cell_val)
                    if len(value_list) > 0:
                        _col_name = get_message('MOSJA12153', lang, showMsgId=False)
                        message_list.append(get_message('MOSJA12028', lang, colname=_col_name, cellname=_convert_rowcol_to_cellno(row, col)))

                key = label_list[index]
                rule_data_dic[key] = cell_val

            col += 1
            index += 1

        rule_data_list.append(rule_data_dic)

    return rule_data_list, message_list



def _convert_rowcol_to_cellno(row, col):
    """
    [メソッド概要]
      行番号、列番号をセル番号に変換
    """

    cellno = ''

    col_tmp  = col
    col_name = ''
    col_list = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    col_tmp, idx = divmod(col_tmp, 26)  # 26 : A-Z
    col_name = col_list[idx]
    while col_tmp > 0:
        col_tmp, idx = divmod(col_tmp - 1, 26)
        col_name = '%s%s' % (col_list[idx], col_name)

    cellno = '%s%s' % (col_name, row + 1)

    return cellno


def _validate_eventinfo(rule_type_id, eventinfo, message_list, lang):
    """
    [メソッド概要]
      eventinfoの入力チェック
    """
    hhmm_repatter = re.compile(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$')
    num_repatter = re.compile(r'^[0-9]+$')
    dec_repatter = re.compile(r'^[0-9]+[.]{1}0+$')
    emo_chk   = UnicodeCheck()

    # データオブジェクトを抽出
    data_object_list = DataObject.objects.filter(rule_type_id=rule_type_id).order_by('data_object_id')
    index = 0
    conditional_name_set = set()
    for i, d in enumerate(data_object_list):
        cond_id = d.conditional_expression_id
        cond_name = d.conditional_name
        # 重複している条件名はスキップ
        if cond_name in conditional_name_set:
            continue
        conditional_name_set.add(cond_name)

        # 空白チェック
        if eventinfo[index] == '':
            message_list.append(get_message('MOSJA12030', lang, conditional_name=cond_name))

        # 時刻条件
        elif cond_id == 15:
            if not hhmm_repatter.match(eventinfo[index]):
                message_list.append(get_message('MOSJA12026', lang, conditional_name=cond_name))

        # 数値条件
        elif cond_id in [1, 2, 5, 6, 7, 8]:
            if not num_repatter.match(eventinfo[index]) and not dec_repatter.match(eventinfo[index]):
                _col_name = get_message('MOSJA12151', lang, showMsgId=False)
                message_list.append(get_message('MOSJA12025', lang, colname=_col_name, conditional_name=cond_name))

        # 文字列 or 正規表現
        elif cond_id in [3, 4, 9, 10]:
            # 絵文字チェック
            value_list = emo_chk.is_emotion(eventinfo[index])
            if len(value_list) > 0:
                _col_name = get_message('MOSJA12152', lang, showMsgId=False)
                message_list.append(get_message('MOSJA12029', lang, colname=_col_name, conditional_name=cond_name))

        # 含む含まない
        elif cond_id in [13, 14]:
            if not _validate_contains(eventinfo[index]):
                _col_name = get_message('MOSJA12153', lang, showMsgId=False)
                message_list.append(get_message('MOSJA12027', lang, colname=_col_name, conditional_name=cond_name))
            # 絵文字チェック
            value_list = emo_chk.is_emotion(eventinfo[index])
            if len(value_list) > 0:
                _col_name = get_message('MOSJA12153', lang, showMsgId=False)
                message_list.append(get_message('MOSJA12029', lang, colname=_col_name, conditional_name=cond_name))

        index += 1


def _validate_eventdatetime(eventdatetime, message_list, lang):
    """
    [メソッド概要]
      イベント発生日時の入力チェック
    """
    try:
        eventdatetime = datetime.datetime.strptime(eventdatetime, '%Y-%m-%d %H:%M:%S')
    except Exception as e:
        message_list.append(get_message('MOSJA12022', lang))


def _validate_contains(value):
    """
    [メソッド概要]
      含む含まないのフォーマットチェック
    """

    chk_val = str(value).strip()
    if not (chk_val.startswith("[") and chk_val.endswith("]")):
        return False

    chk_list = chk_val.strip("[""]").split(",")
    for v in chk_list:
        v = v.strip()
        if not v.startswith("\"") or not v.endswith("\""):
            return False

    return True

