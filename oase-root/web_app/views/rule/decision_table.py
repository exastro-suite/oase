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
 ディシジョンテーブルページのデータ処理

"""


import sys
import copy
import pytz
import datetime
import hashlib
import json
import traceback
import re
import socket
import urllib.parse

from django.http import HttpResponse, Http404
from django.shortcuts import render,redirect
from django.db.models import Q
from django.db import transaction
from django.views.decorators.http import require_POST
from rest_framework import serializers
from libs.commonlibs import define as defs
from libs.commonlibs.oase_logger import OaseLogger
from libs.commonlibs.dt_component import DecisionTableComponent
from libs.webcommonlibs.decorator import *
from libs.webcommonlibs.common import RequestToApply
from libs.webcommonlibs.oase_exception import OASEError
from web_app.models.models import RuleType, DataObject, ConditionalExpression, System, Group, AccessPermission
from web_app.serializers.rule_type import RuleTypeSerializer
from web_app.serializers.data_obj import DataObjectSerializer
from web_app.templatetags.common import get_message

from web_app.views.forms.rule_type_form import RuleTypeForm
from web_app.views.forms.common_form import DivErrorList

logger = OaseLogger.get_instance() # ロガー初期化


MENU_ID_CREATE = 2141001006
MENU_ID_MODIFY = 2141001007
MENU_ID = [MENU_ID_CREATE, MENU_ID_MODIFY]


class DecisionTableAuthByRule(object):
    """
    [クラス概要]
      ルール種別によるディシジョンテーブル画面の権限制御
    """

    ############################################
    # 値定義
    ############################################
    # 画面操作権限
    ALLOW_403      = 0x0000  # 権限なし(403)
    ALLOW_HIDDEN   = 0x0001  # 非表示
    ALLOW_VIEW     = 0x0002  # 参照可能
    ALLOW_DOWNLOAD = 0x0004  # DL可能
    ALLOW_CREATE   = 0x0008  # 新規作成可能
    ALLOW_COPY     = 0x0010  # 複製可能
    ALLOW_UPDATE   = 0x0020  # 更新可能
    ALLOW_DELETE   = 0x0040  # 削除可能

    ALLOW_REGIST   = ALLOW_HIDDEN + ALLOW_CREATE
    ALLOW_VIEWONLY = ALLOW_VIEW   + ALLOW_DOWNLOAD
    ALLOW_MODIFY   = ALLOW_VIEW   + ALLOW_DOWNLOAD + ALLOW_UPDATE + ALLOW_DELETE
    ALLOW_VIEWREG  = ALLOW_VIEW   + ALLOW_DOWNLOAD + ALLOW_CREATE + ALLOW_COPY
    ALLOW_ALL      = ALLOW_VIEW   + ALLOW_DOWNLOAD + ALLOW_CREATE + ALLOW_COPY   + ALLOW_UPDATE + ALLOW_DELETE

    # 権限種別インデックス
    PERM_INDEX = {
        defs.NO_AUTHORIZATION   : 0,
        defs.VIEW_ONLY          : 1,
        defs.ALLOWED_MENTENANCE : 2,
    }


    ############################################
    # メソッド
    ############################################
    def __init__(self, request):
        """
        [メソッド概要]
          初期化処理
        """

        self.auth_create_rules = request.user_config.get_menu_auth_type(MENU_ID_CREATE)
        self.auth_modify_rules = request.user_config.get_activerule_auth_type(MENU_ID_MODIFY)

        self.auth_table = [
            #                     DT新規追加
            # 権限なし            参照                 更新可能
            [self.ALLOW_403,      self.ALLOW_HIDDEN,   self.ALLOW_REGIST],   # 権限なし
            [self.ALLOW_VIEWONLY, self.ALLOW_VIEWONLY, self.ALLOW_VIEWREG],  # 参照      DT編集削除
            [self.ALLOW_MODIFY,   self.ALLOW_MODIFY,   self.ALLOW_ALL],      # 更新可能
        ]


    def get_auth_table_val(self, rule_type_id):
        """
        [メソッド概要]
          指定ルールの画面操作権限を取得
        [引数]
          rule_type_id : ルール種別ID
        [戻り値]
          int          : 画面操作権限
        """

        # 指定のルールの権限を取得
        auth_modify = defs.NO_AUTHORIZATION
        if rule_type_id in self.auth_modify_rules[defs.NO_AUTHORIZATION]:
            auth_modify = defs.NO_AUTHORIZATION

        elif rule_type_id in self.auth_modify_rules[defs.VIEW_ONLY]:
            auth_modify = defs.VIEW_ONLY

        elif rule_type_id in self.auth_modify_rules[defs.ALLOWED_MENTENANCE]:
            auth_modify = defs.ALLOWED_MENTENANCE

        # 新規追加画面と更新削除画面の操作権限を取得
        idx_create = self.PERM_INDEX[self.auth_create_rules]
        idx_modify = self.PERM_INDEX[auth_modify]

        if idx_modify < len(self.auth_table) and idx_create < len(self.auth_table[idx_modify]):
            return self.auth_table[idx_modify][idx_create]

        return self.ALLOW_403


    def get_modify_rules(self, auth_type_list):

        ret_val = []

        if not isinstance(auth_type_list, list):
            auth_type_list = [auth_type_list, ]

        for auth_type in auth_type_list:
            if auth_type in self.auth_modify_rules:
                ret_val.extend(self.auth_modify_rules[auth_type])

        return ret_val


    def is_deny(self, auth_val=None, rule_type_id=0):
        """
        [メソッド概要]
          403チェック
        [引数]
          rule_type_id : ルール種別ID
        [戻り値]
          bool         : True=403画面, False=ディシジョンテーブル画面
        """

        if auth_val is None:
            auth_val = self.get_auth_table_val(rule_type_id)

        if auth_val == self.ALLOW_403:
            return True

        return False


    def is_hidden(self, auth_val=None, rule_type_id=0):
        """
        [メソッド概要]
          非表示チェック
        [引数]
          rule_type_id : ルール種別ID
        [戻り値]
          bool         : True=非表示, False=表示
        """

        if auth_val is None:
            auth_val = self.get_auth_table_val(rule_type_id)

        if auth_val & self.ALLOW_HIDDEN:
            return True

        return False


    def allow_view(self, auth_val=None, rule_type_id=0):
        """
        [メソッド概要]
          参照可能権限チェック
        [引数]
          rule_type_id : ルール種別ID
        [戻り値]
          bool         : 参照可否
        """

        if auth_val is None:
            auth_val = self.get_auth_table_val(rule_type_id)

        if auth_val & self.ALLOW_VIEW:
            return True

        return False


    def allow_download(self, auth_val=None, rule_type_id=0):
        """
        [メソッド概要]
          DL可能権限チェック
        [引数]
          rule_type_id : ルール種別ID
        [戻り値]
          bool         : DL可否
        """

        if auth_val is None:
            auth_val = self.get_auth_table_val(rule_type_id)

        if auth_val & self.ALLOW_DOWNLOAD:
            return True

        return False


    def allow_create(self, auth_val=None, rule_type_id=0):
        """
        [メソッド概要]
          新規追加権限チェック
        [引数]
          rule_type_id : ルール種別ID
        [戻り値]
          bool         : 新規追加可否
        """

        if auth_val is None:
            auth_val = self.get_auth_table_val(rule_type_id)

        if auth_val & self.ALLOW_CREATE:
            return True

        return False


    def allow_copy(self, auth_val=None, rule_type_id=0):
        """
        [メソッド概要]
          複製権限チェック
        [引数]
          rule_type_id : ルール種別ID
        [戻り値]
          bool         : 複製可否
        """

        if auth_val is None:
            auth_val = self.get_auth_table_val(rule_type_id)

        if auth_val & self.ALLOW_COPY:
            return True

        return False


    def allow_update(self, auth_val=None, rule_type_id=0):
        """
        [メソッド概要]
          更新権限チェック
        [引数]
          rule_type_id : ルール種別ID
        [戻り値]
          bool         : 更新可否
        """

        if auth_val is None:
            auth_val = self.get_auth_table_val(rule_type_id)

        if auth_val & self.ALLOW_UPDATE:
            return True

        return False


    def allow_delete(self, auth_val=None, rule_type_id=0):
        """
        [メソッド概要]
          更新権限チェック
        [引数]
          rule_type_id : ルール種別ID
        [戻り値]
          bool         : 削除可否
        """

        if auth_val is None:
            auth_val = self.get_auth_table_val(rule_type_id)

        if auth_val & self.ALLOW_DELETE:
            return True

        return False


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_EVERY)
def index(request):
    """
    [メソッド概要]
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    msg = ''
    lang = request.user.get_lang_mode()
    edit_mode = False
    decision_table_list = []
    dtabr = DecisionTableAuthByRule(request)
    hasUpdateAuthority = True if dtabr.auth_create_rules == defs.ALLOWED_MENTENANCE else False
    object_flg = 0
    dt_rule_ids_disp = []
    dt_rule_ids_edit = []

    dt_rule_ids_disp.extend(dtabr.get_modify_rules([defs.VIEW_ONLY, defs.ALLOWED_MENTENANCE]))
    dt_rule_ids_edit.extend(dtabr.get_modify_rules(defs.ALLOWED_MENTENANCE))

    try:
        #==================取得=================#
        filters = {}
        if request and request.method == 'POST':
            filters = request.POST.get('filters', None)
            filters = json.loads(filters)

        # 参照以上の権限を持つルール種別IDをフィルター条件に追加
        if 'rule_type_id' not in filters:
            filters['rule_type_id'] = {}

        if 'LIST' not in filters['rule_type_id']:
            filters['rule_type_id']['LIST'] = []

        filters['rule_type_id']['LIST'].extend(dt_rule_ids_disp)

        # ディシジョンテーブル情報を取得
        decision_table_list = _select(filters)
        msg = get_message('MOSJA11000', lang) if not decision_table_list else ''

        # ディシジョンテーブル情報に操作権限情報を追加
        for dt in decision_table_list:
            auth_val = dtabr.get_auth_table_val(dt['pk'])
            dt.update(
                {
                    'allow_view'     : dtabr.allow_view(auth_val, dt['pk']),
                    'allow_download' : dtabr.allow_download(auth_val, dt['pk']),
                    'allow_create'   : dtabr.allow_create(auth_val, dt['pk']),
                    'allow_copy'     : dtabr.allow_copy(auth_val, dt['pk']),
                    'allow_update'   : dtabr.allow_update(auth_val, dt['pk']),
                    'allow_delete'   : dtabr.allow_delete(auth_val, dt['pk']),
                }
            )

        group_list, group_list_default = get_group_list(dt_rule_ids_disp)
        add_group_information(decision_table_list, group_list)

        # 条件名の言語別変換処理
        ce = ConditionalExpression.objects.all()
        for c in ce:
            c.operator_name = get_message(c.operator_name, lang, showMsgId=False)

        #==================編集モード判定=================#
        if request and request.method == 'POST':
            edit_mode = request.POST.get('edit_mode', False)

    except Exception as e:
        msg = get_message('MOSJA11013', lang)
        logger.logic_log('LOSI00005', traceback.format_exc(), request=request)


    data = {
        'msg'                    : msg,
        'decision_table_list'    : decision_table_list,
        'conditional_expression' : ce,
        'object_list'            : get_data_object(dt_rule_ids_disp),
        'edit_mode'              : edit_mode,
        'mainmenu_list'          : request.user_config.get_menu_list(),
        'hasUpdateAuthority'     : hasUpdateAuthority,
        'rule_ids_disp'          : dt_rule_ids_disp,
        'rule_ids_edit'          : dt_rule_ids_edit,
        'object_flg'             : object_flg,
        'user_name'              : request.user.user_name,
        'group_list'             : group_list_default,
        'lang_mode'              : request.user.get_lang_mode(),
    }

    logger.logic_log('LOSI00002', 'edit_mode: %s, dt_count: %s' % (edit_mode, len(decision_table_list)), request=request)

    return render(request,'rule/decision_table.html',data)


@check_allowed_auth(MENU_ID_CREATE, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def modify(request):
    """
    [メソッド概要]
      データ更新処理
      POSTリクエストのみ
    """
    logger.logic_log('LOSI00001', 'None', request=request)

    msg = ''
    error_flag = False
    error_msg = {}
    error_msg_top = {}
    response_data = {}
    now = datetime.datetime.now(pytz.timezone('UTC'))

    # アクセスチェック
    add_record = request.POST.get('add_record',"{}")
    add_record = json.loads(add_record)

    request_record_check(add_record, request)

    try:
        ########################################################
        # リクエスト情報のバリデーションチェック
        ########################################################
        # DataObjectの登録データ存在チェック
        if not len(add_record['data_obj_info']):
            logger.user_log('LOSM14002', 'data_obj_info', request=request)
            error_msg['New3'] = get_message('MOSJA11018', request.user.get_lang_mode())
            raise Exception()

        # ルール種別のバリデーションチェック
        info = add_record['table_info']
        dtcomp = DecisionTableComponent(info['rule_table_name'])
        decision_table_data = {
            'rule_type_name'              : info['rule_type_name'],
            'summary'                     : info['summary'],
            'rule_table_name'             : info['rule_table_name'],
            'generation_limit'            : 3,
            'group_id'                    : dtcomp.group_id,
            'artifact_id'                 : dtcomp.artifact_id,
            'container_id_prefix_staging' : dtcomp.contid_stg,
            'container_id_prefix_product' : dtcomp.contid_prd,
            'last_update_user'            : request.user.user_name,
        }

        # 入力チェック
        f = RuleTypeForm(0, decision_table_data, auto_id=False, error_class=DivErrorList)

        # エラーがあればエラーメッセージを作成
        for content, validate_list in f.errors.items():
            error_msg_top[content] = '\n'.join([get_message(v, request.user.get_lang_mode()) for v in validate_list])
        if len(f.errors.items()):
            raise Exception("validate error")

        # データオブジェクトのバリデーションチェック
        data_obj_data = []
        for rq in add_record['data_obj_info']:
            data = {
                'conditional_name'          : rq['conditional_name'],
                'conditional_expression_id' : int(rq['conditional_expression_id']),
                'last_update_user'          : request.user.user_name,
            }
            data_obj_data.append(data)

        row_id_list = []
        for rq in add_record['data_obj_info']:
            row_id_list.append(rq['row_id'])

        conditionalList = {}

        for i,d in enumerate(data_obj_data):
            serializer = DataObjectSerializer(data=d)
            error_flag, error_msg = serializer_check(request, row_id_list, i, serializer, error_flag, error_msg)
            conditionalList, error_msg = conditional_name_type_check(i, d, serializer, conditionalList, error_msg, row_id_list, request)

        # label自動生成
        data_obj_info = []
        index         = 0

        data_obj_info, index = automatic_label_generation(data_obj_data)

        if len(error_msg) > 0:
            raise Exception(msg)

        # 適用君へ新規ルール作成リクエスト送信
        send_data = {
            'request'       : 'CREATE',
            'table_info'    : add_record['table_info'],
            'data_obj_info' : data_obj_info,
            'user_id'       : request.user.user_id,
            'label_count'   : index,
            'lang' : request.user.get_lang_mode(),
        }
        result, msg = RequestToApply.operate(send_data, request=request)

        # 正常処理
        if result:
            response_data['status'] = 'success'
            response_data['redirect_url'] = '/oase_web/rule/decision_table'

            with transaction.atomic():

                # 権限を追加
                ruletypeid = RuleType.objects.get(rule_table_name=info['rule_table_name']).rule_type_id
                group_list = add_record['group_list']

                # システム管理者グループ追加
                admin_perm = [{'menu_id': m, 'permission_type_id': '1'} for m in defs.MENU_BY_RULE]
                admin_group_dict = {'group_id': '1', 'permission': admin_perm}
                group_list.append(admin_group_dict)

                # システム管理者グループ以外のグループに権限追加
                permission_list = add_permission(request, now, ruletypeid, group_list)

                AccessPermission.objects.bulk_create(permission_list)

        # 適用君異常
        else:
            response_data['status'] = 'failure'
            response_data['error_msg'] = error_msg
            response_data['error_top'] = error_msg_top
            response_data['error_apl'] = ''
            if msg:
                response_data['error_apl'] = get_message(msg, request.user.get_lang_mode())

            logger.system_log('LOSM14004', response_data['error_apl'], request=request)

    except Exception as e:
        # 異常処理
        logger.system_log('LOSI00005', traceback.format_exc(), request=request)
        response_data['status'] = 'failure'
        response_data['error_msg'] = error_msg
        response_data['error_top'] = error_msg_top
        response_data['error_apl'] = ''
        response_data['error_flag'] = error_flag

    logger.logic_log('LOSI00002', 'status: %s' % (response_data['status']), request=request)

    response_json = json.dumps(response_data)
    return HttpResponse(response_json, content_type="application/json")


@check_allowed_auth(MENU_ID_MODIFY, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def modify_detail(request, rule_type_id):
    """
    [メソッド概要]
      データ更新処理(詳細画面)
      POSTリクエストのみ
    """

    logger.logic_log('LOSI00001', 'RuleTypeID: %s' % (rule_type_id), request=request)

    msg = ''
    error_flag = False
    error_msg = {}
    error_msg_top = {}
    response_data = {}

    now = datetime.datetime.now(pytz.timezone('UTC'))

    try:
        with transaction.atomic():

            rule_type = RuleType.objects.select_for_update().get(rule_type_id=rule_type_id)

            # ルール別アクセス権限チェック
            dtabr = DecisionTableAuthByRule(request)
            if not dtabr.allow_update(rule_type_id=int(rule_type_id)):
                rule_ids = dtabr.get_modify_rules(defs.MENU_CATEGORY.ALLOW_ADMIN)

                raise OASEError('MOSJA11022', 'LOSI14001', msg_params={'opename':'更新', 'rule_type_name':rule_type.rule_type_name}, log_params=['Update', rule_type_id, rule_ids])

            # アクセスチェック
            add_record = request.POST.get('add_record', "{}")
            add_record = json.loads(add_record)

            # TODO 後でログIDふり直す
            log_msg = 'posted add_record: %s' % (add_record)
            logger.logic_log('LOSI11000', log_msg, request=request)

            if 'table_info' not in add_record:
                logger.user_log('LOSM14002', 'table_info', request=request)
                error_msg = get_message('MOSJA11010', request.user.get_lang_mode())
                raise Exception('不正なリクエストです request=%s' % (add_record))

            # キーの存在確認
            if not {'rule_type_name', 'summary'} == set(add_record['table_info'].keys()):
                logger.user_log('LOSM14001', add_record['table_info'].keys(), ['rule_type_name', 'summary'], request=request)
                error_msg = get_message('MOSJA11010', request.user.get_lang_mode())
                raise Exception('不正なリクエストです request=%s' % (add_record))

            if 'group_list' not in add_record:
                logger.user_log('LOSM14001', add_record.keys(), 'group_list', request=request)
                error_msg = get_message('MOSJA11010', request.user.get_lang_mode())
                raise Exception('不正なリクエストです request=%s' % (add_record))

            #バリデーションチェック
            info = add_record['table_info']
            serializer = RuleTypeSerializer()
            try:
                serializer.validate_rule_type_name(info['rule_type_name'])
                serializer.validate_summary(info['summary'])

                select_object = RuleType.objects.filter(rule_type_name=info['rule_type_name'])

                if len(select_object) == 1 and rule_type_id != select_object[0].rule_type_id:
                    logger.user_log('LOSM14005', info['rule_type_name'], rule_type_id, select_object[0].rule_type_id, request=request)
                    error_msg = get_message('MOSJA00005', request.user.get_lang_mode()).replace('\\n', '\n')
                    error_msg_top['span_rule_type_name2'] = get_message('MOSJA11009', request.user.get_lang_mode())
                    raise Exception('ルール種別名称が重複しています。 request=%s' % (add_record))

            except serializers.ValidationError as e:
                error_msg = get_message('MOSJA00005', request.user.get_lang_mode())
                error_msg = error_msg.replace('\\n', '\n')

                log_txt = ''
                logger_txt = ''
                for d1, d2 in zip(e.get_full_details(), e.detail):
                    k = 'span_%s2' % (d1['code'])
                    v = str(d2) + ' (MOSJA11011)'
                    error_msg_top[k] = v

                    if logger_txt:
                        logger_txt += ', '
                    logger_txt += '%s:%s' % (d1['code'], str(d2))

                    if log_txt:
                        log_txt += '\n'
                    log_txt += v

                logger.user_log('LOSM14003', logger_txt, request=request)
                raise Exception(log_txt)

            # データ更新
            RuleType.objects.filter(rule_type_id=rule_type_id).update(
                rule_type_name = info['rule_type_name'],
                summary        = info['summary'],
                last_update_timestamp = now,
                last_update_user   = request.user.user_name
            )

            # アクセス権限データ更新
            grlock = Group.objects.select_for_update().filter(group_id__gt=1)
            group_ids = list(grlock.values_list('group_id', flat=True))
            perm_rset = list(AccessPermission.objects.filter(group_id__in=group_ids, menu_id__in=defs.MENU_BY_RULE, rule_type_id=rule_type_id).values('group_id', 'menu_id', 'rule_type_id', 'permission_type_id'))
            bulk_list = []

            # グループ管理に登録されているグループIDのみを更新対象とする
            for group_id in group_ids:
                for gr in add_record['group_list']:
                    if group_id != int(gr['group_id']):
                        continue

                    perm_list = gr['permission']

                    # 要求アクセス権限種別が、DBに登録済みか否かチェック
                    for perm in perm_list:
                        menu_id = int(perm['menu_id'])
                        type_id = int(perm['permission_type_id'])

                        # DB登録済みの場合は更新
                        for rs in perm_rset:
                            if group_id == rs['group_id'] and menu_id == rs['menu_id'] and rule_type_id == rs['rule_type_id']:
                                if type_id != rs['permission_type_id']:
                                    AccessPermission.objects.filter(group_id=group_id, menu_id=menu_id, rule_type_id=rule_type_id).update(
                                        permission_type_id    = type_id,
                                        last_update_timestamp = now,
                                        last_update_user      = request.user.user_name
                                    )

                                break

                        # DB未登録の場合は追加リストへ保持
                        else:
                            acperm = AccessPermission(
                                group_id              = group_id,
                                menu_id               = menu_id,
                                rule_type_id          = rule_type_id,
                                permission_type_id    = type_id,
                                last_update_timestamp = now,
                                last_update_user      = request.user.user_name
                            )

                            bulk_list.append(acperm)

                    break

                # 要求にないグループIDは追加リストへ保持
                else:
                    for menu_id in defs.MENU_BY_RULE:
                        acperm = AccessPermission(
                            group_id              = group_id,
                            menu_id               = menu_id,
                            rule_type_id          = rule_type_id,
                            permission_type_id    = defs.NO_AUTHORIZATION,
                            last_update_timestamp = now,
                            last_update_user      = request.user.user_name
                        )

                        bulk_list.append(acperm)

            # TODO 後でログIDふり直す
            log_msg = 'update count: %s' % len(bulk_list)
            logger.logic_log('LOSI11000', log_msg, request=request)

            # 追加リストがあればDBに一括挿入
            if len(bulk_list) > 0:
                AccessPermission.objects.bulk_create(bulk_list)

            # 正常処理
            response_data['status'] = 'success'
            response_data['redirect_url'] = '/oase_web/rule/decision_table'

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

        response_data['status'] = 'failure'
        response_data['error_msg'] = msg if msg else error_msg
        response_data['error_top'] = error_msg_top

    except Exception as e:
        # 異常処理
        if not error_msg:
            tb = sys.exc_info()[2]
            error_msg = '%s' % (e.with_traceback(tb))
            logger.logic_log('LOSI00005', traceback.format_exc(), request=request)

        response_data['status'] = 'failure'
        response_data['error_msg'] = error_msg
        response_data['error_top'] = error_msg_top


    logger.logic_log('LOSI00002', 'status: %s' % (response_data['status']), request=request)

    response_json = json.dumps(response_data)
    return HttpResponse(response_json, content_type="application/json")


@check_allowed_auth(MENU_ID_MODIFY, defs.MENU_CATEGORY.ALLOW_ADMIN)
@require_POST
def delete_table(request, rule_type_id):

    """
    [メソッド概要]
    データ削除処理
    POSTリクエストのみ
    """

    logger.logic_log('LOSI00001', 'RuleTypeID: %s' % (rule_type_id), request=request)

    response_data = {}

    try:
        # ルール別アクセス権限チェック
        dtabr = DecisionTableAuthByRule(request)
        if not dtabr.allow_delete(rule_type_id=int(rule_type_id)):
            rtname   = RuleType.objects.get(rule_type_id=rule_type_id).rule_type_name
            rule_ids = dtabr.get_modify_rules(defs.MENU_CATEGORY.ALLOW_ADMIN)

            raise OASEError('MOSJA11022', 'LOSI14001', msg_params={'opename':'削除', 'rule_type_name':rtname}, log_params=['Delete', rule_type_id, rule_ids])

        # 適用君へルール削除リクエスト送信
        send_data = {
            'request' : 'DELETE',
            'ruletypeid' : rule_type_id,
            'user_id' : request.user.user_id,
        }
        result, msg = RequestToApply.operate(send_data, request=request)

        # 正常処理
        if result:
            response_data['status'] = 'success'
            response_data['redirect_url'] = '/oase_web/rule/decision_table'

        # 適用君異常
        else:
            response_data['status'] = 'failure'
            response_data['error_msg'] = get_message('MOSJA11017', request.user.get_lang_mode())
            if msg:
                response_data['error_msg'] = get_message(msg, request.user.get_lang_mode())

            logger.system_log('LOSM14004', response_data['error_msg'], request=request)

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

        response_data['status'] = 'failure'
        response_data['error_msg'] = msg if msg else get_message('MOSJA11017', request.user.get_lang_mode())

    except Exception as e:
        # 異常処理
        logger.system_log('LOSI00005', traceback.format_exc(), request=request)
        response_data['status'] = 'failure'
        response_data['error_msg'] = get_message('MOSJA11017', request.user.get_lang_mode())

    logger.logic_log('LOSI00002', 'status: %s' % (response_data['status']), request=request)

    response_json = json.dumps(response_data)
    return HttpResponse(response_json, content_type="application/json")



@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_EVERY)
@require_POST
def data(request):
    """
    [メソッド概要]
      (フィルタ実行時の)データ取得
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    #メンテナンス権限チェック
    dtabr = DecisionTableAuthByRule(request)
    edit = True if dtabr.auth_create_rules == defs.ALLOWED_MENTENANCE else False
    filter_flg = False
    dt_rule_ids_disp = []
    dt_rule_ids_edit = []

    dt_rule_ids_disp.extend(dtabr.get_modify_rules([defs.VIEW_ONLY, defs.ALLOWED_MENTENANCE]))
    dt_rule_ids_edit.extend(dtabr.get_modify_rules(defs.ALLOWED_MENTENANCE))

    # postパラメータチェック
    filters = request.POST.get('filters',"{}")
    filters = json.loads(filters)

    if ('rule_type_name' not in filters
        or 'last_update_user' not in filters
        or 'last_update_timestamp' not in filters):

        logger.user_log('LOSM14001', filters.keys(), ['rule_type_name', 'last_update_user', 'last_update_timestamp'], request=request)
        msg = get_message('MOSJA11013', request.user.get_lang_mode())
        raise Http404

    #フィルター条件1つ以上あればフィルタフラグを立てる
    if (len(filters['rule_type_name'])
        or len(filters['last_update_user'])
        or len(filters['last_update_timestamp']) ):
        filter_flg = True

    # 参照以上の権限を持つルール種別IDをフィルター条件に追加
    if 'rule_type_id' not in filters:
        filters['rule_type_id'] = {}

    if 'LIST' not in filters['rule_type_id']:
        filters['rule_type_id']['LIST'] = []

    filters['rule_type_id']['LIST'].extend(dt_rule_ids_disp)

    # ディシジョンテーブル情報を取得
    decision_table_list = _select(filters)
    msg = get_message('MOSJA11000', request.user.get_lang_mode()) if not decision_table_list else ''

    # ディシジョンテーブル情報に操作権限情報を追加
    for dt in decision_table_list:
        auth_val = dtabr.get_auth_table_val(dt['pk'])
        dt.update(
            {
                'allow_view'     : dtabr.allow_view(auth_val, dt['pk']),
                'allow_download' : dtabr.allow_download(auth_val, dt['pk']),
                'allow_create'   : dtabr.allow_create(auth_val, dt['pk']),
                'allow_copy'     : dtabr.allow_copy(auth_val, dt['pk']),
                'allow_update'   : dtabr.allow_update(auth_val, dt['pk']),
                'allow_delete'   : dtabr.allow_delete(auth_val, dt['pk']),
            }
        )


    data = {
        'msg'                 : msg,
        'edit_mode'           : edit,
        'mainmenu_list'       : request.user_config.get_menu_list(),
        'decision_table_list' : decision_table_list,
        'user_name'           : request.user.user_name,
        'rule_ids_disp'       : dt_rule_ids_disp,
        'rule_ids_edit'       : dt_rule_ids_edit,
        'lang_mode'           : request.user.get_lang_mode(),
    }

    logger.logic_log('LOSI00002', 'edit_mode: %s, dt_count: %s' % (edit, len(decision_table_list)), request=request)

    return render(request,'rule/decision_table_data.html',data)


@check_allowed_auth(MENU_ID, defs.MENU_CATEGORY.ALLOW_EVERY)
def download(request, rule_type_id):
    """
    [メソッド概要]
      DecisionTableダウンロード処理
    """

    logger.logic_log('LOSI00001', 'RuleTypeID: %s' % (rule_type_id), request=request)

    try:
        # ルール別アクセス権限チェック
        dtabr = DecisionTableAuthByRule(request)
        if not dtabr.allow_download(rule_type_id=int(rule_type_id)):
            rtname   = RuleType.objects.get(rule_type_id=rule_type_id).rule_type_name
            rule_ids = dtabr.get_modify_rules(defs.MENU_CATEGORY.ALLOW_EVERY)

            raise OASEError('MOSJA11022', 'LOSI14001', msg_params={'opename':'ダウンロード', 'rule_type_name':rtname}, log_params=['Download', rule_type_id, rule_ids])

        # 適用君へDecisionTableダウンロードリクエスト送信
        send_data = {
            'request'    : 'DOWNLOAD_DT',
            'ruletypeid' : rule_type_id,
        }
        result, msg, filename, filedata = RequestToApply.getfile(send_data, request=request)

        # 正常処理
        if result:
            response = HttpResponse(filedata, content_type='application/excel')
            response['Content-Disposition'] = "attachment; filename*=UTF-8''%s" % (urllib.parse.quote(filename))

        # 適用君異常
        else:
            logger.system_log('LOSM14004', msg, request=request)
            raise Exception('ダウンロード失敗')

        logger.logic_log('LOSI00002', 'success', request=request)
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
        logger.logic_log('LOSI00005', traceback.format_exc(), request=request)
        return HttpResponse(request, status=500)


def _select(filters):
    """
    [メソッド概要]
      データ更新処理
    """

    logger.logic_log('LOSI00001', 'filters: %s' % (filters))

    # リスト表示用
    where_info = {}

    for k, v in filters.items():
        if len(v) <= 0:
            continue

        if 'LIKE' in v:
            where_info[k + '__contains'] = v['LIKE']

        if 'START' in v:
            where_info[k + '__gte'] = v['START']

        if 'END' in v:
            where_info[k + '__lte'] = v['END']

        if 'LIST' in v:
            where_info[k + '__in'] = v['LIST']
        
        if 'FROM' in v:
            where_info[k + '__gte'] = datetime.datetime.strptime(v['FROM'], '%Y-%m-%d')

        if 'TO' in v:
            where_info[k + '__lte'] = datetime.datetime.strptime(v['TO'], '%Y-%m-%d')


    decision_table = RuleType.objects.filter(**where_info)

    table_list = []
    for d in decision_table:

        if d.summary == None:
            d.summary = ''

        table_info = {
            'pk'                    : d.pk,
            'rule_type_name'        : d.rule_type_name,
            'summary'               : d.summary,
            'rule_table_name'       : d.rule_table_name,
            'last_update_timestamp' : d.last_update_timestamp,
            'last_update_user'      : d.last_update_user,
        }
        table_list.append(table_info)

    return table_list

def get_data_object(rule_ids):

    object_list   = []
    select_object = DataObject.objects.filter(rule_type_id__in=rule_ids)

    # データオブジェクト作成
    for s in select_object:
        object_info = {}
        object_info['rule_type_id']              = s.rule_type_id
        object_info['conditional_name']          = s.conditional_name
        object_info['conditional_expression_id'] = s.conditional_expression_id
        object_list.append(object_info)

    return object_list


def get_group_list(rule_ids):
    """
    [メソッド概要]
      グループごとのアクセス権限リストを取得
    [引数]
      rule_ids : アクセス権限の取得対象となるルール種別IDリスト
    [戻り値]
      group_list   : ルール別グループごとのアクセス権限を取得
      default_list : 全グループのアクセス権限を「権限なし」で取得
    """

    group_list = []
    default_list = []

    for rule_id in rule_ids:
        rule_info = {}
        rule_info[rule_id] = []

        group_list.append(rule_info)

    group_ids = []
    rset = Group.objects.filter(group_id__gt=1).values('group_id', 'group_name').order_by('group_id')
    for rs in rset:
        group_info = {}
        group_info['id']   = rs['group_id']
        group_info['name'] = rs['group_name']
        group_info['perm'] = {}

        for menu_id in defs.MENU_BY_RULE:
            group_info['perm'][menu_id] = defs.NO_AUTHORIZATION

        for gr in group_list:
            for k, v in gr.items():
                v.append(copy.deepcopy(group_info))

        default_list.append(copy.deepcopy(group_info))
        group_ids.append(rs['group_id'])

    rset = AccessPermission.objects.filter(group_id__in=group_ids, rule_type_id__in=rule_ids).values('rule_type_id', 'group_id', 'menu_id', 'permission_type_id')
    for rs in rset:
        rule_id  = rs['rule_type_id']
        group_id = rs['group_id']
        menu_id  = rs['menu_id']
        perm_id  = rs['permission_type_id']

        for group in group_list:
            if rule_id not in group:
                continue

            for gr in group[rule_id]:
                if group_id != gr['id']:
                    continue

                if menu_id in gr['perm']:
                    gr['perm'][menu_id] = perm_id

                break

            break

    return group_list, default_list


def add_group_information(decision_table_list, group_list):
    """
    [メソッド概要]
      ディシジョンテーブル情報にグループ情報を追加
    [引数]
      decision_table_list : ディシジョンテーブル情報リスト
      group_list          : ルール別グループごとのアクセス権限リスト
    [戻り値]
      なし
    """

    for dt in decision_table_list:
        for gr in group_list:
            if dt['pk'] not in gr:
                continue

            dt.update({'group_list' : gr[dt['pk']]})
            break


def request_record_check(add_record, request):
    """
    [メソッド概要]
      リクエスト情報のチェック
    [引数]
      add_record : 追加レコード
      request    : リクエスト情報
    [戻り値]
      なし
    """

    if 'table_info' not in add_record or 'data_obj_info' not in add_record:
        logger.user_log('LOSM14001', add_record.keys(), ['table_info', 'data_obj_info'], request=request)
        raise Http404

    # キーの存在確認
    if not {'rule_type_name', 'summary', 'rule_table_name'} == set(add_record['table_info'].keys()):
        logger.user_log('LOSM14001', add_record['table_info'].keys(), [
                        'rule_type_name', 'summary', 'rule_table_name'], request=request)
        raise Http404

    if 'group_list' not in add_record:
        logger.user_log('LOSM14001', add_record.keys(), 'group_list', request=request)
        raise Http404

    for gr in add_record['group_list']:
        if not {'group_id', 'permission'} == set(gr.keys()):
            logger.user_log('LOSM14001', gr.keys(), ['group_id', 'permission'], request=request)
            raise Http404

        for perm in gr['permission']:
            if not {'menu_id', 'permission_type_id'} == set(perm.keys()):
                logger.user_log('LOSM14001', perm.keys(), ['menu_id', 'permission_type_id'], request=request)
                raise Http404


def automatic_label_generation(data_obj_data):
    """
    [メソッド概要]
      labelを自動生成する。
    [引数]
      data_obj_data : データオブジェクトのリスト
    [戻り値]
      data_obj_info : データオブジェクト情報のリスト
      index         : インデックス
    """

    data_obj_info = []
    conNameDict   = {}
    index         = 0

    for d in data_obj_data:
        if not d['conditional_name'] in conNameDict:

            data = {
                'conditional_name'          : d['conditional_name'],
                'label'                     : 'label' + str(index),
                'conditional_expression_id' : int(d['conditional_expression_id']),
            }
            conNameDict[d['conditional_name']] = 'label' + str(index)
            data_obj_info.append(data)
            index = index + 1

        else:

            data = {
                'conditional_name'          : d['conditional_name'],
                'label'                     : conNameDict[d['conditional_name']],
                'conditional_expression_id' : int(d['conditional_expression_id']),
            }
            data_obj_info.append(data)

    return data_obj_info, index


def add_permission(request, now, ruletypeid, group_list):
    """
    [メソッド概要]
      システム管理者以外のグループに権限を追加する。
    [引数]
      request         : リクエスト情報
      now             : 現在時刻
      ruletypeid      : ルール種別ID
      group_list      : グループリスト
    [戻り値]
      permission_list : 権限リスト
    """

    permission_list     = []
    permission_list_reg = {}

    for gr in group_list:
        for permission in gr['permission']:
            permission_list_reg = AccessPermission(
                    group_id = gr['group_id'],
                    menu_id  = permission['menu_id'],
                    permission_type_id = permission['permission_type_id'],
                    last_update_user = request.user.user_name,
                    last_update_timestamp = now,
                    rule_type_id = ruletypeid
                )

            permission_list.append(copy.deepcopy(permission_list_reg))

    return permission_list


def serializer_check(request, row_id_list, i, serializer, error_flag, error_msg):
    """
    [メソッド概要]
      バリデーションチェックを行う
    [引数]
      request     : リクエスト情報
      row_id_list : レコードIDリスト
      i           : インデックス
      serializer  : serializer結果
      error_flag  : エラーフラグ
      error_msg   : エラーメッセージ
    [戻り値]
      error_flag  : エラーフラグ
      error_msg   : エラーメッセージ
    """

    result_valid = serializer.is_valid()

    if result_valid == False:
        msg = '%s' % serializer.errors
        logger.user_log('LOSM14003', msg, request=request)
        error_flag = True
        for vlist in serializer.errors.values():
            key = row_id_list[i]
            error_msg[key] = ''

            for v in vlist:
                if error_msg[key]:
                    error_msg[key] += '\n'
                error_msg[key] += v

            else:
                error_msg[key] += ' (MOSJA11011)'

    return error_flag, error_msg


def conditional_name_type_check(i, d, serializer, conditionalList, error_msg, row_id_list, request):
    """
    [メソッド概要]
      同一条件名の型チェックを行う
    [引数]
      i               : インデックス
      d               : 要素
      serializer      : serializer結果
      conditionalList : 条件付きリスト
      error_msg       : エラーメッセージ
      row_id_list     : レコードIDリスト
      request         : リクエスト情報
    [戻り値]
      conditional     : 条件付きリスト
    """

    expressionId = ''
    expressionType = ''

    if d['conditional_name'] in conditionalList:
        # 同一条件名があった場合
        if not d['conditional_expression_id'] in conditionalList[d['conditional_name']]:
            msg = '%s' % 'Error caused by conditional expression.'
            error_msg[row_id_list[i]] = [ d['conditional_name'],d['conditional_expression_id'] ]
            logger.user_log('LOSM14003', msg, request=request)
            raise Exception(msg)
    else:
        expressionId = d['conditional_expression_id']
        if expressionId in defs.EXPRESSION_TYPE.EXPRESSION_INTEGER:
            expressionType = defs.EXPRESSION_TYPE.EXPRESSION_INTEGER
        elif expressionId in defs.EXPRESSION_TYPE.EXPRESSION_STRING:
            expressionType = defs.EXPRESSION_TYPE.EXPRESSION_STRING
        elif expressionId in defs.EXPRESSION_TYPE.EXPRESSION_LIST_STRING:
            expressionType = defs.EXPRESSION_TYPE.EXPRESSION_LIST_STRING
        else:
            # 上記の定義に当てはまらない場合はエラーとする
            msg = '%s' % 'Error caused by conditional expression.'
            logger.user_log('LOSM14003', msg, request=request)
            raise Exception(msg)
        conditionalList[d['conditional_name']] = expressionType

    return conditionalList, error_msg


