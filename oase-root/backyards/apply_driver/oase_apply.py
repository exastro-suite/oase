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
    ルールの作成更新削除アップロードを行う。
    ルールファイルのDLを行う。
"""

import os
import django
import sys
import socket
import pytz
import datetime
import json
import base64
import threading
import subprocess
import re
import requests
import time
import zipfile
import traceback

my_path = os.path.dirname(os.path.abspath(__file__))
tmp_path = my_path.split('oase-root')
root_dir_path = tmp_path[0] + 'oase-root'
sys.path.append(root_dir_path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'confs.frameworkconfs.settings'
django.setup()

from django.db import transaction
from django.db.models import Q
from django.conf import settings

from libs.commonlibs.oase_logger import OaseLogger
logger = OaseLogger.get_instance() # ロガー初期化

from libs.commonlibs.define import *
from libs.commonlibs.createxl import DecisionTableFactory
from libs.commonlibs.createxl import DecisionTableCustomizer
from libs.commonlibs.testrequest_createxl import TestRequestXlFactory
from libs.commonlibs.dt_component import DecisionTableComponent
from libs.commonlibs.aes_cipher import AESCipher
from libs.backyardlibs.backyard_common import disconnect

from web_app.models.models import RuleFile
from web_app.models.models import RuleType
from web_app.models.models import System
from web_app.models.models import User
from web_app.models.models import RuleManage
from web_app.models.models import DataObject
from web_app.models.models import AccessPermission
from web_app.templatetags.common import get_message


APPLY_LOCK = threading.Lock()
DOWNLOAD_LOCK = threading.Lock()

APPLY_USER_ID = -2140000003


def conv_tz(dt, tzname):

    return dt.astimezone(pytz.timezone(tzname)).strftime('%Y-%m-%d %H:%M:%S.%f')


def make_send_data(data, need_keys=[], omit_keys=[]):

    logger.logic_log('LOSI00001', 'need_keys: %s' % need_keys)

    ret_data = data.copy()

    if len(need_keys) > 0:
        for k, v in ret_data.items():
            if k not in need_keys:
                omit_keys.append(k)

    for k in omit_keys:
        if k in ret_data:
            ret_data.pop(k)

    logger.logic_log('LOSI00002', 'None')
    return ret_data


def create(request):
    disconnect()
    logger.logic_log('LOSI00001', request)

    result = ''
    msg = ''

    # リクエストのパラメーター取得
    uid = int(request['user_id'])
    table_info = request['table_info']
    data_objs = request['data_obj_info']
    label_cnt = request['label_count']
    lang = request['lang']

    type_name = table_info['rule_type_name']
    summary = table_info['summary']
    table_name = table_info['rule_table_name']

    now = datetime.datetime.now(pytz.timezone('UTC'))
    user = User.objects.get(user_id=uid)
    dtcomp = DecisionTableComponent(table_name)

    rule_type_id = 0

    ret_info = {
        'result': 'OK',
        'msg': '',
    }

    try:
        with transaction.atomic():
            ########################################
            # DB保存
            ########################################
            # ルール種別
            rule_type = RuleType(
                rule_type_name=type_name,
                summary=summary,
                rule_table_name=table_name,
                generation_limit=3,
                group_id=dtcomp.group_id,
                artifact_id=dtcomp.artifact_id,
                container_id_prefix_staging=dtcomp.contid_stg,
                container_id_prefix_product=dtcomp.contid_prd,
                label_count=label_cnt,
                last_update_timestamp=now,
                last_update_user=user.user_name
            )
            rule_type.save(force_insert=True)

            # データオブジェクト
            data_obj_list = []
            for dob in data_objs:
                data_object = DataObject(
                    rule_type_id=rule_type.rule_type_id,
                    conditional_name=dob['conditional_name'],
                    label=dob['label'],
                    conditional_expression_id=int(dob['conditional_expression_id']),
                    last_update_timestamp=now,
                    last_update_user=user.user_name
                )
                data_obj_list.append(data_object)

            if len(data_obj_list) > 0:
                DataObject.objects.bulk_create(data_obj_list)

            ########################################
            # RHDMコンポーネント作成
            ########################################
            rule_type_id = rule_type.rule_type_id
            dtcomp.make_component_all(rule_type_id)

            ########################################
            # Excel作成
            ########################################
            dt_fact = DecisionTableFactory(
                rule_type_id,
                dtcomp.rule_set,
                dtcomp.table_name,
                dtcomp.class_name,
                dtcomp.fact_name,
                dtcomp.get_dtable_path(),
                lang)
            success_flg = dt_fact.create_decision_table()
            if not success_flg:
                msg = 'MOSJA03501'
                logger.system_log('LOSM12021', 'rule_type_id: %s, rule_type_name: %s' % (rule_type_id, type_name))
                raise Exception()

            ########################################
            # Excel作成(TestRequest)
            ########################################
            testreq_fact = TestRequestXlFactory(rule_type_id, dtcomp.table_name, dtcomp.get_dtable_path(), request)
            success_flg = testreq_fact.create_testrequest_table()
            if not success_flg:
                msg = 'MOSJA03503'
                logger.system_log('LOSM12053', 'rule_type_id: %s, rule_type_name: %s' % (rule_type_id, type_name))
                raise Exception()

    except FileExistsError as e:
        # RHDMコンポーネント作成において、新規作成するルール種別のディレクトリが既に存在していた場合
        logger.system_log('LOSM12051', 'traceback: %s' % traceback.format_exc())

        ret_info = {
            'result': 'NG',
            'msg': 'MOSJA03502',
        }

    except Exception as e:
        if rule_type_id > 0:
            dtcomp.remove_component(rule_type_id)
        if not msg:
            msg = 'MOSJA03001'
            logger.system_log('LOSM12007', 'traceback: %s' % traceback.format_exc())

        ret_info = {
            'result': 'NG',
            'msg': msg,
        }
    logger.logic_log('LOSI00002', 'ret_info: %s' % ret_info)
    return ret_info


def upload(request):

    disconnect()
    logger.logic_log('LOSI00001', 'ruletypeid: %s, filename: %s' % (request['ruletypeid'], request['filename']))

    result = ''
    msg = ''
    errmsg = ''
    userlog = 'user_id=' + str(request['upload_user_id'])
    errlog_prefix = True

    ret_info = {
        'result': 'OK',
        'msg': '',
    }

    try:
        now = datetime.datetime.now(pytz.timezone('UTC'))
        now_tz = conv_tz(now, 'Asia/Tokyo')
        user = User.objects.get(user_id=request['upload_user_id'])
        lang = user.get_lang_mode()

        ruletypeid = int(request['ruletypeid'])

        rulefile = None
        rule_manage = None

        try:
            with transaction.atomic():
                # ルールファイルDB登録
                rulefile = RuleFile(
                    rule_type_id=ruletypeid,
                    rule_file_name=request['filename'],
                    last_update_timestamp=now,
                    last_update_user=user.user_name
                )
                rulefile.save(force_insert=True)

                # ルール適用管理登録
                rule_manage = RuleManage(
                    rule_type_id=ruletypeid,
                    request_type_id=STAGING,
                    rule_file_id=rulefile.pk,
                    system_status=RULE_STS_SYSTEM.UPLOAD,
                    operation_status=RULE_STS_OPERATION.STAGING_NOAPPLY,
                    last_update_timestamp=now,
                    last_update_user=user.user_name
                )
                rule_manage.save(force_insert=True)

        except Exception as e:
            ret_info = {
                'result': 'NG',
                'msg': 'MOSJA03101',
            }
            logger.system_log('LOSM12022', traceback.format_exc())
            logger.logic_log('LOSI00002', ret_info)
            return ret_info

        # ルール種別情報取得
        ruleType = RuleType.objects.get(rule_type_id=ruletypeid)

        artifactid = ruleType.artifact_id
        groupid = ruleType.group_id

        dtcomp = DecisionTableComponent(ruleType.rule_table_name)
        dtcomp.set_path(rule_path['rule_srcpath'], '%s%s/' % (rule_path['rule_rootpath'], ruletypeid))

        srcpath = dtcomp.get_pom_path()
        dstpath = '%s%s/%s/' % (request['rule_dstpath'], ruletypeid, rulefile.pk)
        filepath = request['rule_filepath'] % (ruletypeid, rulefile.pk) + ruleType.rule_table_name + '/'

        # kjar構築用ファイルをコピー
        os.makedirs(dstpath, exist_ok=True)
        if not os.path.exists(srcpath):

            try:
                with transaction.atomic():
                    rule_manage.system_status = RULE_STS_SYSTEM.UPLOAD_NG
                    rule_manage.last_update_timestamp = now
                    rule_manage.last_update_user      = user.user_name
                    rule_manage.save(force_update=True)
            except Exception as e:
                errmsg = str(now_tz) + ' ' + userlog + ' ' + get_message('MOSJA03104', lang)
                errmsg = errmsg + '\n' + str(now_tz) + ' ' + userlog + ' ' + str(e)
                msg    = 'MOSJA03104'
                logger.system_log('LOSM12023',userlog)
                raise Exception(errmsg)

            errmsg = str(now_tz) + ' ' + userlog + ' ' + get_message('MOSJA03102', lang)
            msg = 'MOSJA03102'
            logger.system_log('LOSM12024', srcpath)
            raise Exception(errmsg)

        dtcomp.copy_tree(dstpath)

        # ルールファイルの保存
        os.makedirs(filepath, exist_ok=True)

        filename = request['filename']
        filedata = request['filedata']
        filedata = base64.b64decode(filedata.encode('utf-8'))

        with open(filepath + filename, 'wb') as fp:
            fp.write(filedata)

        # 保存したルールファイルのチェック
        dtcomp.set_rule_type_id(ruletypeid)
        errmsg_list = dtcomp.check_decision_table_file(filepath + filename, lang)
        if len(errmsg_list) > 0:
            errmsg += str(now_tz) + ' ' + userlog + ' ' + get_message('MOSJA03121', lang) + '\n'
            for em in errmsg_list:
                errmsg += str(now_tz) + ' ' + userlog + ' ' + em + '\n'

            errlog_prefix = False
            logger.user_log('LOSM12061')
            raise Exception(errmsg)

    except User.DoesNotExist:
        ret_info = {
            'result': 'NG',
            'msg': 'MOSJA03101',
        }
        logger.system_log('LOSM12022', traceback.format_exc())
        logger.logic_log('LOSI00002', ret_info)
        return ret_info

    except Exception as e:
        rule_manage.system_status = RULE_STS_SYSTEM.UPLOAD_NG
        rule_manage.last_update_timestamp = now
        rule_manage.last_update_user      = user.user_name
        rule_manage.save(force_update=True)

        errfilename = '%s_err.log' % (request['filename'].rsplit('.')[0])
        errfilepath = dstpath + errfilename
        errmsg = ''
        if errlog_prefix:
            errmsg = str(now_tz) + ' ' + userlog + ' ' + get_message('MOSJA03106', lang).replace('\n', '\n')
            errmsg = errmsg + '\n' + str(now_tz) + ' ' + userlog + ' ' + str(e) + '\n'
        else:
            errmsg = str(e) + '\n'

        if not os.path.exists(dstpath):
            os.makedirs(dstpath, exist_ok=True)
        with open(errfilepath, 'a') as f:
            f.write(errmsg)

        msg = 'MOSJA03007' if not msg else msg
        ret_info = {
            'result': 'NG',
            'msg': msg,
        }

        logger.system_log('LOSM12025', traceback.format_exc())
        logger.logic_log('LOSI00002', 'ret_info: %s' % ret_info)
        return ret_info

    ret_info.update(
        msg='MOSJA03002',
        ruletypeid=ruletypeid,
        rule_file_id=rulefile.pk,
        artifactid=artifactid,
        groupid=groupid,
        pompath=dstpath,
        request_type_id=STAGING,
        apply_user_id=request['upload_user_id'],
        rule_manage_id=rule_manage.rule_manage_id
    )

    logger.logic_log('LOSI00002', 'ret_info: %s' % ret_info)

    return ret_info


def apply_req(request):

    disconnect()
    logger.logic_log('LOSI00001', 'request: %s' % (request))

    result = 'OK'
    msg = ''

    try:

        ruletypeid = request['ruletypeid']
        rulefileid = request['rule_file_id']
        reqtypeid = request['request_type_id']
        manageid = request['rule_manage_id']

        now = datetime.datetime.now(pytz.timezone('UTC'))
        user = User.objects.get(user_id=request['apply_user_id'])

        # プロダクション環境以外のリクエストは拒否
        if reqtypeid != PRODUCTION:
            msg = 'MOSJA03202'
            logger.system_log('LOSM12026', str(request['apply_user_id']), reqtypeid)
            raise Exception()

        # プロダクション環境データ作成処理
        with transaction.atomic():
            # ロック取得
            ruleManageLock = RuleManage.objects.get(rule_manage_id=manageid)

            # データ作成状況チェック
            rcnt = RuleManage.objects.filter(
                rule_type_id=ruleManageLock.rule_type_id,
                request_type_id=ruleManageLock.request_type_id,
                rule_file_id=ruleManageLock.rule_file_id,
                operation_status=RULE_STS_OPERATION.PRODUCT
            ).count()

            if rcnt > 0:
                msg = 'MOSJA03201'
                logger.system_log('LOSM12027',
                                  str(request['apply_user_id']),
                                  ruleManageLock.rule_type_id,
                                  ruleManageLock.request_type_id,
                                  ruleManageLock.rule_file_id)
                raise Exception()

            # プロダクション環境データ作成
            ruleManage = RuleManage(
                rule_type_id=ruletypeid,
                request_type_id=reqtypeid,
                rule_file_id=rulefileid,
                system_status=RULE_STS_SYSTEM.PRODUCT,
                operation_status=RULE_STS_OPERATION.PRODUCT_NOAPPLY,
                last_update_timestamp=now,
                last_update_user=user.user_name
            )
            ruleManage.save(force_insert=True)

            request['rule_manage_id'] = ruleManage.rule_manage_id

    except User.DoesNotExist:
        result = 'NG'
        msg    = 'MOSJA32010'
        logger.system_log('LOSM12068', traceback.format_exc())

    except RuleManage.DoesNotExist:
        result = 'NG'
        msg    = 'MOSJA03302'
        logger.system_log('LOSM12035', str(request['apply_user_id']), manageid, traceback.format_exc())

    except Exception as e:
        result = 'NG'
        msg = msg if msg else 'MOSJA03018'
        logger.system_log('LOSM12069', traceback.format_exc())

    ret_info = {
        'result': result,
        'msg': 'MOSJA03017' if result == 'OK' else msg,
    }

    return ret_info


def apply(request):

    disconnect()
    logger.logic_log('LOSI00001', 'request: %s' % (request))

    try:
        # データ取得
        ruletypeid = request['ruletypeid']
        groupid = request['groupid']
        artifactid = request['artifactid']
        rulefileid = request['rule_file_id']
        reqtypeid = request['request_type_id']
        manageid = request['rule_manage_id']

        rulefile = RuleFile.objects.get(rule_file_id=rulefileid)
        filename = '%s_err.log' % (rulefile.rule_file_name.rsplit('.')[0])
        errfilepath = '%s%s/%s/%s' % (request['rule_dstpath'], ruletypeid, rulefileid, filename)
        userlog = 'user_id=' + str(request['apply_user_id'])
        msg = ''

        data = {}
        data['release-id'] = {}

        now = datetime.datetime.now(pytz.timezone('UTC'))
        now_tz = conv_tz(now, 'Asia/Tokyo')
        user = User.objects.get(user_id=request['apply_user_id'])
        lang = user.get_lang_mode()

        ret_info = {
            'result': 'OK',
            'msg': msg,
        }

        if reqtypeid not in [PRODUCTION, STAGING]:
            errmessage = str(now_tz) + ' ' + userlog + ' ' + get_message('MOSJA03206',
                                                                         lang, reqtypeid=reqtypeid).replace('\n', '\n') + '\n'
            with open(errfilepath, 'a') as f:
                f.write(errmessage)

            ret_info = {
                'result': 'NG',
                'msg': 'MOSJA03202'
            }
            logger.system_log('LOSM12026', str(request['apply_user_id']), reqtypeid)
            logger.logic_log('LOSI00002', 'ret_info: %s' % ret_info)
            return ret_info

        with transaction.atomic():
            ruleManageLock = RuleManage.objects.get(rule_manage_id=manageid)
            if reqtypeid == PRODUCTION:
                rcnt = RuleManage.objects.filter(
                    rule_type_id=ruleManageLock.rule_type_id,
                    request_type_id=ruleManageLock.request_type_id,
                    rule_file_id=ruleManageLock.rule_file_id,
                    operation_status=RULE_STS_OPERATION.PRODUCT
                ).count()

                if rcnt > 0:
                    msg = 'MOSJA03201'
                    errmessage = str(now_tz) + ' ' + userlog + ' ' + get_message('MOSJA03201', lang)
                    logger.system_log('LOSM12027',
                                      str(request['apply_user_id']),
                                      ruleManageLock.rule_type_id,
                                      ruleManageLock.request_type_id,
                                      ruleManageLock.rule_file_id)
                    raise Exception(errmessage)

            # コンテナID取得
            rule_type = RuleType.objects.select_for_update().get(rule_type_id=ruletypeid)
            # ルール適用管理検索
            tmp_working_rule = RuleManage.objects.select_for_update().filter(
                rule_type_id=ruletypeid, request_type_id=reqtypeid)

            if reqtypeid == PRODUCTION:
                tmp_working_rule = tmp_working_rule.filter(
                    system_status=RULE_STS_SYSTEM.PRODUCT_OK,
                    operation_status=RULE_STS_OPERATION.PRODUCT
                )

            elif reqtypeid == STAGING:
                tmp_working_rule = tmp_working_rule.filter(
                    system_status=RULE_STS_SYSTEM.STAGING_OK,
                    operation_status__in=[
                        RULE_STS_OPERATION.STAGING_NOTYET,
                        RULE_STS_OPERATION.STAGING_VERIFY,
                        RULE_STS_OPERATION.STAGING_NG,
                        RULE_STS_OPERATION.STAGING
                    ]
                )

            old_manage_ids = list(tmp_working_rule.values_list('rule_manage_id', flat=True))

            # 適用対象となるルール適用管理情報を取得
            ruleManage = RuleManage.objects.get(rule_manage_id=manageid)

            if reqtypeid == PRODUCTION:
                ContID = rule_type.container_id_prefix_product
                oldContID = rule_type.current_container_id_product
            elif reqtypeid == STAGING:
                ContID = rule_type.container_id_prefix_staging
                oldContID = rule_type.current_container_id_staging

            # デプロイ実施
            headers = {
                'accept': 'application/json',
                'content-type': 'application/json',
            }

            ContID = ContID + '_' + datetime.datetime.now(pytz.timezone('UTC')).strftime('%Y%m%d%H%M%S%f')

            data['container-id'] = ContID
            data['status'] = 'STARTED'
            data['release-id']['group-id'] = groupid
            data['release-id']['artifact-id'] = artifactid
            data['release-id']['version'] = rulefileid

            send_data = json.dumps(data)
            send_data = send_data.encode()

            PROTOCOL, IPADDRPORT, dmuser, dmpass = get_dm_conf()

            HTTP = '%s://%s/decision-central/rest/controller/management/servers/default-kieserver/containers/%s' % (
                PROTOCOL, IPADDRPORT, ContID)

            response = requests.put(HTTP, headers=headers, data=send_data, auth=(dmuser, dmpass))
            logger.system_log('LOSI12000', 'response: %s, ContID: %s' % (response, ContID))

            # デプロイ失敗
            if response.status_code != 201:

                ret_info = {
                    'result': 'NG',
                    'msg': 'MOSJA03204',
                }

                # システム処理状態更新
                # 適用異常終了
                if reqtypeid == PRODUCTION:
                    ruleManage.system_status = RULE_STS_SYSTEM.PRODUCT_NG
                elif reqtypeid == STAGING:
                    ruleManage.system_status = RULE_STS_SYSTEM.STAGING_NG

                ruleManage.last_update_timestamp = now
                ruleManage.last_update_user = user.user_name
                ruleManage.save(force_update=True)

                if response.status_code == 400:
                    msg = 'MOSJA03208'
                    errmessage = str(now_tz) + ' ' + userlog + ' ' + get_message('MOSJA03208', lang)
                    logger.system_log('LOSM12029', str(request['apply_user_id']), reqtypeid, ContID)
                    raise Exception(errmessage)
                elif response.status_code == 404:
                    msg = 'MOSJA03209'
                    errmessage = str(now_tz) + ' ' + userlog + ' ' + get_message('MOSJA03209', lang)
                    logger.system_log('LOSM12030', str(request['apply_user_id']), reqtypeid, ContID)
                    raise Exception(errmessage)
                else:
                    msg = 'MOSJA03210'
                    errmessage = str(now_tz) + ' ' + userlog + ' ' + get_message('MOSJA03210', lang)
                    logger.system_log('LOSM12031', str(request['apply_user_id']), reqtypeid, ContID)
                    raise Exception(errmessage)

                logger.system_log('LOSM12028', str(request['apply_user_id']), reqtypeid, ContID)

            # デプロイ成功
            else:
                # 現コンテナID更新
                if reqtypeid == PRODUCTION:
                    RuleType.objects.filter(
                        rule_type_id=ruletypeid
                    ).update(
                        current_container_id_product=ContID,
                        last_update_timestamp=now,
                        last_update_user=user.user_name
                    )
                elif reqtypeid == STAGING:
                    RuleType.objects.filter(
                        rule_type_id=ruletypeid
                    ).update(
                        current_container_id_staging=ContID,
                        last_update_timestamp=now,
                        last_update_user=user.user_name
                    )

                # システム処理状態更新
                # 適用完了
                if reqtypeid == PRODUCTION:
                    ruleManage.system_status = RULE_STS_SYSTEM.PRODUCT_OK
                    ruleManage.operation_status = RULE_STS_OPERATION.PRODUCT
                elif reqtypeid == STAGING:
                    ruleManage.system_status = RULE_STS_SYSTEM.STAGING_OK
                    ruleManage.operation_status = RULE_STS_OPERATION.STAGING_NOTYET

                ruleManage.last_update_timestamp = now
                ruleManage.last_update_user = user.user_name
                ruleManage.save(force_update=True)

                # 古いコンテナが存在する場合は削除
                if oldContID:

                    # スリープ処理
                    time.sleep(5)

                    # 古いコンテナ削除
                    headers = {
                        'accept': 'application/json',
                        'content-type': 'application/json',
                    }

                    HTTP2 = '%s://%s/decision-central/rest/controller/management/servers/default-kieserver/containers/%s' % (
                        PROTOCOL, IPADDRPORT, oldContID)
                    response2 = requests.delete(HTTP2, headers=headers, auth=(dmuser, dmpass))
                    logger.system_log('LOSI12000', 'response2: %s, oldContID: %s' % (response2, oldContID))

                    # プロダクション処理の場合
                    # システム処理状態更新
                    mod_sts = RULE_STS_OPERATION.STAGING_END
                    if reqtypeid == PRODUCTION:
                        mod_sts = RULE_STS_OPERATION.PRODUCT_END

                    if len(old_manage_ids) > 0:
                        RuleManage.objects.filter(
                            rule_manage_id__in=old_manage_ids).exclude(
                            rule_manage_id=manageid
                        ).update(
                            operation_status=mod_sts,
                            last_update_timestamp=now,
                            last_update_user=user.user_name
                        )

                    if response2.status_code != 204:
                        if response2.status_code == 400:
                            msg    = 'MOSJA03215'
                            errmessage = str(now_tz) + ' ' + userlog + ' ' + get_message('MOSJA03215', lang)
                            logger.system_log('LOSM12032', str(request['apply_user_id']), reqtypeid, ContID)
                            raise Exception(errmessage)

                        # コンテナ削除時の接続エラーはすでに削除済みであるためファイルに記載し、準正常とする。
                        elif response2.status_code == 404:
                            errmessage = str(now_tz) + ' ' + userlog + ' ' + get_message('MOSJA03216', lang) + '\n'
                            with open(errfilepath, 'a') as f:
                                f.write(errmessage)
                            logger.system_log('LOSM12033', str(request['apply_user_id']), reqtypeid, ContID)

                        else:
                            msg    = 'MOSJA03217'
                            errmessage = str(now_tz) + ' ' + userlog + ' ' + get_message('MOSJA03217', lang)
                            logger.system_log('LOSM12034', str(request['apply_user_id']), reqtypeid, ContID)
                            raise Exception(errmessage)

                # 世代管理
                table_name = rule_type.rule_table_name
                dtcomp = DecisionTableComponent(table_name)
                dtcomp.set_rule_type_id(ruletypeid)
                if reqtypeid == PRODUCTION:
                    production_generation = int(System.objects.get(config_id='PRODUCTION_GENERATION').value)

                    if production_generation > 0:
                        # プロダクション適用履歴管理の方を消す
                        production_rules_queryset = RuleManage.objects.filter(
                            rule_type_id=ruletypeid, request_type_id=reqtypeid
                        ).filter(
                            system_status=RULE_STS_SYSTEM.PRODUCT_OK
                        )

                        p_rules_cnt = production_rules_queryset.count()
                        if p_rules_cnt > production_generation:
                            p_rules = list(production_rules_queryset.order_by('rule_manage_id').reverse())

                            p_rules_del = p_rules[production_generation:]
                            logger.system_log('LOSI12007', ', '.join([str(r.rule_manage_id) for r in p_rules_del]))
                            for p_rule_manage in p_rules_del:
                                # ルールファイル削除
                                #   ただしステージングで使用されているものはチェックして消さない
                                p_rule_file_id = p_rule_manage.rule_file_id
                                qs = RuleManage.objects.filter(
                                    rule_type_id=ruletypeid, request_type_id=STAGING, rule_file_id=p_rule_file_id)
                                if qs.count() == 0:
                                    dstpath = '%s%s/%s/' % (request['rule_dstpath'], ruletypeid, p_rule_file_id)
                                    dtcomp.remove_component_related_one_file(dstpath)
                                    dtcomp.remove_mavenrepository_related_one_file(p_rule_file_id)
                                else:
                                    logger.system_log('LOSM12058', p_rule_file_id)

                                # manage削除
                                p_rule_manage.delete()

                        # プロダクション適用中のエラーがあった方を消す
                        RuleManage.objects.filter(
                            rule_type_id=ruletypeid, request_type_id=reqtypeid
                        ).filter(
                            system_status=RULE_STS_SYSTEM.PRODUCT_NG
                        ).delete()

                elif reqtypeid == STAGING:
                    staging_generation = int(System.objects.get(config_id='STAGING_GENERATION').value)

                    if staging_generation > 0:
                        # ステージング削除
                        staging_rules_queryset = RuleManage.objects.filter(
                            rule_type_id=ruletypeid,
                            request_type_id=reqtypeid
                        ).exclude(
                            system_status__in=[
                                RULE_STS_SYSTEM.UPLOAD,
                                RULE_STS_SYSTEM.UPLOAD_OK,
                                RULE_STS_SYSTEM.BUILD,
                                RULE_STS_SYSTEM.BUILD_OK,
                            ])

                        s_rules_cnt = staging_rules_queryset.count()
                        if s_rules_cnt > staging_generation:
                            s_rules = list(staging_rules_queryset.order_by('rule_manage_id').reverse())

                            s_rules_del = s_rules[staging_generation:]
                            logger.system_log('LOSI12008', ', '.join([str(r.rule_manage_id) for r in s_rules_del]))
                            for s_rule_manage in s_rules_del:
                                # ルールファイル削除
                                # ただしプロダクションで使用されているものはチェックして消さない
                                s_rule_file_id = s_rule_manage.rule_file_id
                                qs = RuleManage.objects.filter(
                                    rule_type_id=ruletypeid, request_type_id=PRODUCTION, rule_file_id=s_rule_file_id)
                                if qs.count() == 0:
                                    dstpath = '%s%s/%s/' % (request['rule_dstpath'], ruletypeid, s_rule_file_id)
                                    dtcomp.remove_component_related_one_file(dstpath)
                                    dtcomp.remove_mavenrepository_related_one_file(s_rule_file_id)
                                else:
                                    logger.system_log('LOSM12059', s_rule_manage.rule_file_id)

                                # manage削除
                                s_rule_manage.delete()

                ret_info = {
                    'result': 'OK',
                    'msg': 'MOSJA03003',
                }

    except RuleFile.DoesNotExist:
        logger.system_log('LOSM12019', traceback.format_exc())

        ret_info = {
            'result': 'NG',
            'msg': 'MOSJA03013',
        }

    except User.DoesNotExist:
        logger.system_log('LOSM12022', traceback.format_exc())

        ret_info = {
            'result': 'NG',
            'msg': 'MOSJA32010',
        }

    except RuleManage.DoesNotExist:
        errmessage = str(now_tz) + ' ' + userlog + ' ' + get_message('MOSJA03218',
                                                                     lang, manageid=manageid).replace('\n', '\n')
        errmessage = errmessage + '\n'
        with open(errfilepath, 'a') as f:
            f.write(errmessage)
        logger.system_log('LOSM12035', str(request['apply_user_id']), manageid, traceback.format_exc())

        ret_info = {
            'result': 'NG',
            'msg': 'MOSJA03302',
        }

    except Exception as e:
        try:
            rulemanage = RuleManage.objects.get(rule_manage_id=manageid)

            if reqtypeid == STAGING:
                rulemanage.system_status = RULE_STS_SYSTEM.STAGING_NG
                rulemanage.last_update_timestamp = now
                rulemanage.last_update_user = user.user_name
                rulemanage.save(force_update=True)

            elif reqtypeid == PRODUCTION:
                rulemanage.system_status = RULE_STS_SYSTEM.PRODUCT_NG
                rulemanage.last_update_timestamp = now
                rulemanage.last_update_user = user.user_name
                rulemanage.save(force_update=True)

            errmessage = str(now_tz) + ' ' + userlog + ' ' + get_message('MOSJA03219', lang).replace('\n', '\n')
            errmessage = errmessage + '\n' + str(now_tz) + ' ' + userlog + ' ' + str(e) + '\n'
            with open(errfilepath, 'a') as f:
                f.write(errmessage)
            logger.system_log('LOSM12036', str(request['apply_user_id']), reqtypeid, manageid, traceback.format_exc())

            ret_info = {
                'result': 'NG',
                'msg': msg,
            }
        except Exception as e:
            logger.system_log('LOSM12036', str(request['apply_user_id']), reqtypeid, manageid, traceback.format_exc())
            ret_info = {
                'result': 'NG',
                'msg': 'MOSJA03219',
            }

    logger.logic_log('LOSI00002', 'ret_info: %s' % ret_info)
    return ret_info


def download(request):

    logger.logic_log('LOSI00001', 'manageid: %s, ruletypeid: %s' % (request['rule_manage_id'], request['ruletypeid']))

    manageid = request['rule_manage_id']
    ruletypeid = request['ruletypeid']
    testrequestflag = request['file_name_expansion']

    rule_file_id, rule_filename, rule_table_name, errmsg = _get_downloadfile_info(
        ruletypeid, manageid, testrequestflag, request)

    ret_info = {
        'result': 'OK',
        'msg': 'OK',
        'filename': rule_filename,
        'filedata': '',
    }

    if errmsg:
        ret_info.update(
            result='NG',
            msg=errmsg,
            filename='',
            filedata='',
        )
        logger.system_log('LOSM12037', ruletypeid, manageid)
        logger.logic_log('LOSI00002', 'ret_info: %s' % ret_info)
        return ret_info

    # テストリクエスト用エクセルDLの場合
    if len(request['file_name_expansion']) > 0:
        dtcomp = DecisionTableComponent(rule_table_name)
        dtcomp.set_rule_type_id(ruletypeid)
        dtcomp.set_path()
        rule_filepath = dtcomp.get_dtable_path() + rule_filename
        ret_info['filename'] = rule_filename
    else:
        # ルールファイル読み込み
        rule_filepath = request['rule_filepath'] % (ruletypeid, rule_file_id) + rule_table_name + '/' + rule_filename

    if os.path.exists(rule_filepath):
        with open(rule_filepath, 'rb') as fp:
            ruledata = base64.b64encode(fp.read()).decode('utf-8')
            ret_info.update(filedata=ruledata)
    else:
        ret_info.update(
            result='NG',
            msg='MOSJA03304',
            filename='',
            filedata=''
        )
        logger.system_log('LOSM12038', rule_filepath)

    logger.logic_log('LOSI00002', 'result: %s, msg: %s, filename: %s' %
                     (ret_info['result'], ret_info['msg'], ret_info['filename']))
    return ret_info


def download_zip(request):
    """
    [概要]
    excelファイルとエラーログファイルをまとめたzipファイルをダウンロード
    """

    logger.logic_log('LOSI00001','manageid: %s, ruletypeid: %s' % (request['rule_manage_id'], request['ruletypeid']))

    with DOWNLOAD_LOCK:

        manageid = request['rule_manage_id']
        ruletypeid = request['ruletypeid']

        rule_file_id, rule_filename, rule_table_name, errmsg = _get_downloadfile_info(
            ruletypeid, manageid, '', request=request)

        ret_info = {
            'result': 'OK',
            'msg': 'OK',
            'filename': rule_filename,
            'filedata': '',
        }

        if errmsg:
            ret_info.update(
                result='NG',
                msg=errmsg,
                filename='',
                filedata=''
            )
            logger.system_log('LOSM12037', ruletypeid, manageid)
            logger.logic_log('LOSI00002', 'ret_info: %s' % ret_info)
            return ret_info

        # excelファイルパス, errorlogファイルパス,保存先パスをset
        rule_filename_body = rule_filename.split('.')[0]

        rule_filepath = request['rule_filepath'] % (ruletypeid, rule_file_id) + rule_table_name + '/' + rule_filename
        dstpath = '%s%s/%s/' % (request['rule_dstpath'], ruletypeid, rule_file_id)
        errlog_filepath = dstpath + rule_filename_body + '_err.log'

        # zipファイルを取得
        zip_filename = rule_filename_body + '.zip'
        filepath = _get_zipfile(rule_filepath, errlog_filepath, dstpath, zip_filename)

        if os.path.exists(filepath):
            # zipファイルを読み込みデータを返す
            with open(filepath, 'rb') as fp:
                ruledata = base64.b64encode(fp.read()).decode('utf-8')
                ret_info.update(
                    filename=zip_filename,
                    filedata=ruledata
                )
        else:
            ret_info.update(
                result='NG',
                msg='MOSJA03304',
                filename='',
                filedata=''
            )
            logger.system_log('LOSM12038', filepath)

        logger.logic_log('LOSI00002', 'result: %s, msg: %s, filename: %s' %
                         (ret_info['result'], ret_info['msg'], ret_info['filename']))
        return ret_info


def _get_downloadfile_info(ruletypeid, manageid, testrequestflag, request):
    """
    [概要]
    dtまたはdtとエラーログをまとめたzipファイルに必要な情報を取得
    [引数]
    ruletypeid : ルール種別id
    manageid : ルール管理id
    [戻り値]
    rule_file_id : ルール管理id
    rule_filename : ルールファイル名
    msg : エラーメッセージ

    """
    disconnect()
    # ルール種別情報を取得

    logger.logic_log('LOSI00001', 'ruletypeid: %s, manageid: %s' % (ruletypeid, manageid))
    ruletype = ''
    artifactid = ''

    try:
        ruletype = RuleType.objects.get(pk=ruletypeid)
        artifactid = ruletype.artifact_id
        rule_table_name = ruletype.rule_table_name
    except BaseException:
        logger.system_log('LOSM12039', ruletypeid, traceback.format_exc())
        logger.logic_log('LOSI00002', "'', '', '', '', 'MOSJA03301'")
        return '', '', '', 'MOSJA03301'

    # ルールファイル情報を取得
    try:
        rule_file_id = RuleManage.objects.get(rule_manage_id=manageid).rule_file_id
        rule_filename = RuleFile.objects.get(pk=rule_file_id).rule_file_name

        # テストリクエスト用エクセルDLの場合
        if len(testrequestflag) > 0:
            rule_filename = rule_table_name + testrequestflag

    except RuleManage.DoesNotExist:
        logger.system_log('LOSM12040', manageid, traceback.format_exc())
        logger.logic_log('LOSI00002', 'ruletypeid: %s' % ruletypeid)
        return '', '', '', 'MOSJA03302'
    except RuleFile.DoesNotExist:
        logger.system_log('LOSM12041', rule_file_id, traceback.format_exc())
        logger.logic_log('LOSI00002', 'ruletypeid: %s' % ruletypeid)
        return '', '', '', 'MOSJA03303'

    logger.logic_log('LOSI00002', 'rule_id: %s, rule_filename: %s, msg: None' % (rule_file_id, rule_filename))
    return rule_file_id, rule_filename, rule_table_name, None


def _get_zipfile(rule_filepath, errlog_filepath, dstpath, filename):
    """
    [概要]
    引数の情報からzipファイルを作成してzipファイルパスを返す
    ファイルが存在しない場合は return None
    [引数]
    rule_filepath : ルールファイルのパス
    errlog_filepath : エラーログファイルのパス
    dstpath : 保存先のパス
    filename : 保存ファイル名
    """

    disconnect()
    logger.logic_log('LOSI00001', 'rule_filepath: %s, errlog_filepath: %s, dstpath: %s, filename: %s' %
                     (rule_filepath, errlog_filepath, dstpath, filename))

    filepath = dstpath + filename

    #zipファイルが存在する場合は削除する
    if os.path.exists(filepath):
        os.remove(filepath)

    #zipファイルを作成する
    with zipfile.ZipFile(filepath, 'w', compression=zipfile.ZIP_DEFLATED) as new_zip:
        if os.path.exists(errlog_filepath):
            new_zip.write(errlog_filepath, arcname=os.path.basename(errlog_filepath))
        if os.path.exists(rule_filepath):
            new_zip.write(rule_filepath, arcname=os.path.basename(rule_filepath))

        logger.logic_log('LOSI00002', 'filepath: %s' % filepath)
        return filepath


def download_dt(request):

    disconnect()
    logger.logic_log('LOSI00001', request)

    filename = ''
    ruledata = ''

    ruletypeid = int(request['ruletypeid'])

    try:
        ruletype = RuleType.objects.get(rule_type_id=ruletypeid)
    except RuleType.DoesNotExist:
        logger.system_log('LOSM12039', ruletypeid, traceback.format_exc())
        ret_info = {
            'result': 'NG',
            'msg': 'MOSJA03302',
            'filename': '',
            'filedata': '',
        }
        logger.logic_log('LOSI00002', 'ret_info: %s' % ret_info)
        return ret_info

    dtcomp = DecisionTableComponent(ruletype.rule_table_name)
    dtcomp.set_rule_type_id(ruletypeid)
    dtcomp.set_path(src_path=rule_path['rule_srcpath'], root_path=('%s%s/' % (request['rule_rootpath'], ruletypeid)))

    rule_filepath = dtcomp.get_dtable_path()
    filename = '%s.xlsx' % (ruletype.rule_table_name)

    # ルールファイル読み込み
    filepath = rule_filepath + filename
    if not os.path.exists(filepath):
        ret_info = {
            'result': 'NG',
            'msg': 'MOSJA03304',
            'filename': '',
            'filedata': '',
        }
        logger.system_log('LOSM12038', filepath)
        logger.logic_log('LOSI00002', 'ret_info: %s' % ret_info)
        return ret_info

    # ルールファイルのアクション種別の選択肢を更新する
    ruledata = None
    try:
        customizer = DecisionTableCustomizer(filepath)
        customizer.custom_action_type()
        ruledata = customizer.output()
    except Exception as e:
        logger.system_log('LOSM12065', 'error: %s' % e)
        logger.logic_log('LOSI00005', traceback.format_exc())

    if not ruledata:
        ret_info = {
            'result': 'NG',
            'msg': 'MOSJA03304',
            'filename': '',
            'filedata': '',
        }
        logger.logic_log('LOSI00002', 'ret_info: %s' % ret_info)
        return ret_info

    ruledata = base64.b64encode(ruledata).decode('utf-8')

    ret_info = {
        'result': 'OK',
        'msg': 'OK',
        'filename': filename,
        'filedata': ruledata,
    }

    logger.logic_log('LOSI00002', 'result: %s, msg: %s, filename: %s' %
                     (ret_info['result'], ret_info['msg'], ret_info['filename']))

    return ret_info


def get_dm_conf():
    """
    [概要]
    DecisionManagerの設定値を取得する
    [戻り値]
    protocol : str プロトコル
    ipaddress : str ipアドレス
    dmuser : str DecisionManagerのユーザ名
    dmpass : str DecisionManagerのパスワード
    """
    logger.logic_log('LOSI00001', 'None')

    rset = list(System.objects.filter(category='DMSETTINGS').values('config_id', 'value'))
    dmconf = {r['config_id']: r['value'] for r in rset}
    # passwordを復号
    cipher = AESCipher(settings.AES_KEY)
    dmconf['DM_PASSWD'] = cipher.decrypt(dmconf['DM_PASSWD'])

    protocol = dmconf["DM_PROTOCOL"]
    ipaddrport = dmconf["DM_IPADDRPORT"]
    dmuser = dmconf["DM_USERID"]
    dmpass = dmconf["DM_PASSWD"]

    logger.logic_log(
        'LOSI00002', '(protocol, ipaddrport, dmuser, dmpass) = (%s, %s, %s, %s)' %
        (protocol, ipaddrport, dmuser, dmpass))

    return protocol, ipaddrport, dmuser, dmpass


def delete(request):

    disconnect()
    logger.logic_log('LOSI00001', request)

    msg = ''
    now = datetime.datetime.now(pytz.timezone('UTC'))
    user_name = User.objects.get(user_id=request['user_id']).user_name

    ret_info = {
        'result': 'OK',
        'msg': '',
    }

    try:
        with transaction.atomic():

            ruletypeid = int(request['ruletypeid'])
            rule_type = RuleType.objects.select_for_update().get(rule_type_id=ruletypeid)

            #########################################
            # コンテナ削除
            #########################################
            headers = {
                'accept': 'application/json',
                'content-type': 'application/json',
            }

            # コンテナID取得
            product_ContID = rule_type.current_container_id_product
            staging_ContID = rule_type.current_container_id_staging

            PROTOCOL, IPADDRPORT, dmuser, dmpass = get_dm_conf()

            if product_ContID is not None:
                HTTP2 = '%s://%s/decision-central/rest/controller/management/servers/default-kieserver/containers/%s' % (
                    PROTOCOL, IPADDRPORT, product_ContID)
                response2 = requests.delete(HTTP2, headers=headers, auth=(dmuser, dmpass))
                logger.system_log('LOSI12000', 'response2: %s, product_ContID: %s' % (response2, product_ContID))

            if staging_ContID is not None:
                HTTP2 = '%s://%s/decision-central/rest/controller/management/servers/default-kieserver/containers/%s' % (
                    PROTOCOL, IPADDRPORT, staging_ContID)
                response2 = requests.delete(HTTP2, headers=headers, auth=(dmuser, dmpass))
                logger.system_log('LOSI12000', 'response2: %s, staging_ContID: %s' % (response2, staging_ContID))

            #########################################
            # MRディレクトリ削除
            #########################################
            dtcomp = DecisionTableComponent(rule_type.rule_table_name)
            if ruletypeid > 0:
                dtcomp.remove_mavenrepository()

            #########################################
            # DTディレクトリ削除
            #########################################
            if ruletypeid > 0:
                dtcomp.remove_component(ruletypeid)

            #########################################
            # アクセス権限管理レコード削除
            #########################################
            try:
                ap_list = AccessPermission.objects.filter(rule_type_id=ruletypeid)
                for a in ap_list:
                    a.disuse_flag = 1
                    a.last_update_user = user_name
                    a.last_update_timestamp = now
                    a.save(force_update=True)
            except Exception as e:
                msg = 'MOSJA03605'
                logger.system_log('LOSM12066', ruletypeid, traceback.format_exc())
                raise Exception()

            #########################################
            # ルール適用管理レコード削除
            #########################################
            try:
                RuleManage.objects.filter(rule_type_id=ruletypeid).delete()
            except Exception as e:
                msg = 'MOSJA03601'
                logger.system_log('LOSM12042', ruletypeid, traceback.format_exc())
                raise Exception()

            #########################################
            # ルールファイル情報管理レコード削除
            #########################################
            try:
                RuleFile.objects.filter(rule_type_id=ruletypeid).delete()
            except Exception as e:
                msg = 'MOSJA03602'
                logger.system_log('LOSM12043', ruletypeid, traceback.format_exc())
                raise Exception()

            #########################################
            # データオブジェクト管理レコード削除
            #########################################
            try:
                DataObject.objects.filter(rule_type_id=ruletypeid).delete()
            except Exception as e:
                msg = 'MOSJA03603'
                logger.system_log('LOSM12044', ruletypeid, traceback.format_exc())
                raise Exception()

            #########################################
            # ルール種別管理レコード削除
            #########################################
            try:
                rule_type.disuse_flag = 1
                rule_type.rule_type_name = rule_type.rule_type_name + '_deleted_' + now.strftime('%Y%m%d%H%M%s')
                rule_type.rule_table_name = rule_type.rule_table_name + '_deleted_' + now.strftime('%Y%m%d%H%M%s')
                rule_type.last_update_user = user_name
                rule_type.last_update_timestamp = now
                rule_type.save(force_update=True)

            except Exception as e:
                msg = 'MOSJA03604'
                logger.system_log('LOSM12045', ruletypeid, traceback.format_exc())
                raise Exception()

    except RuleType.DoesNotExist:
        logger.system_log('LOSM12039', ruletypeid, traceback.format_exc())
        ret_info = {
            'result': 'NG',
            'msg': 'MOSJA03301',
        }

    except Exception as e:
        ret_info = {
            'result': 'NG',
            'msg': msg,
        }

    logger.logic_log('LOSI00002', 'ret_info: %s' % ret_info)
    return ret_info


def build_kjar(request):

    disconnect()
    logger.logic_log('LOSI00001', request)
    logger.logic_log('LOSI12001')

    with APPLY_LOCK:

        logger.logic_log('LOSI12002')

        try:
            # データ取得
            now = datetime.datetime.now(pytz.timezone('UTC'))
            now_tz = conv_tz(now, 'Asia/Tokyo')
            user = User.objects.get(user_id=request['apply_user_id'])
            ruletypeid = request['ruletypeid']
            ruleid = request['rule_file_id']
            artifactid = request['artifactid']
            groupid = request['groupid']
            filepath = request['pompath'] + 'pom.xml'
            reqtypeid = request['request_type_id']
            manageid = request['rule_manage_id']

            rulefile = RuleFile.objects.get(rule_file_id=ruleid)
            filename = '%s_err.log' % (rulefile.rule_file_name.rsplit('.')[0])
            errfilepath = request['pompath'] + filename
            userlog = 'user_id=' + str(request['apply_user_id'])

            # システム処理状態更新
            try:
                with transaction.atomic():
                    ruleManage = RuleManage.objects.select_for_update().get(rule_manage_id=manageid)
                    ruleManage.system_status = RULE_STS_SYSTEM.BUILD
                    ruleManage.last_update_timestamp = now
                    ruleManage.last_update_user = user.user_name
                    ruleManage.save(force_update=True)

            except Exception as e:
                RuleManage.objects.filter(
                    rule_manage_id=manageid
                ).update(
                    system_status=RULE_STS_SYSTEM.BUILD_NG, last_update_timestamp=now, last_update_user=user.user_name
                )

                errmessage = str(now_tz) + ' ' + userlog + ' ' + \
                    get_message('MOSJA03404', user.get_lang_mode()).replace('\n', '\n')
                errmessage = errmessage + '\n' + str(now_tz) + ' ' + userlog + ' ' + str(e) + '\n'
                with open(errfilepath, 'a') as f:
                    f.write(errmessage)
                logger.system_log('LOSM12046', str(request['apply_user_id']),
                                  reqtypeid, manageid, traceback.format_exc())

                ret_info = {
                    'result': 'NG',
                    'msg': 'MOSJA03401',
                }

                logger.logic_log('LOSI00002', 'ret_info: %s' % ret_info)
                return ret_info

            # pomファイル編集
            regex_groupid = r'<groupId>.*</groupId>'
            regex_artifactid = r'<artifactId>.*</artifactId>'
            regex_version = r'<version>.*</version>'

            with open(filepath, 'r+') as fp:
                pom_xml = fp.read()
                pom_xml = re.sub(regex_groupid, '<groupId>%s</groupId>' % (groupid), pom_xml, 1)
                pom_xml = re.sub(regex_artifactid, '<artifactId>%s</artifactId>' % (artifactid), pom_xml, 1)
                pom_xml = re.sub(regex_version, '<version>%s</version>' % (ruleid), pom_xml, 1)
                fp.seek(0)
                fp.write(pom_xml)
                fp.truncate()

            # ビルド実行
            exec_cmd = []
            exec_cmd.append('mvn')
            exec_cmd.append('install')
            exec_cmd.append('-Ddrools.dateformat=yyyy-MM-dd HH:mm')
            exec_cmd.append('-f')
            exec_cmd.append(filepath)
            ret = subprocess.run(exec_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # システム処理状態更新
            sys_sts = RULE_STS_SYSTEM.BUILD_OK if ret.returncode == 0 else RULE_STS_SYSTEM.BUILD_NG

            try:
                with transaction.atomic():
                    ruleManage = RuleManage.objects.select_for_update().get(rule_manage_id=manageid)
                    ruleManage.system_status = sys_sts
                    ruleManage.last_update_timestamp = now
                    ruleManage.last_update_user = user.user_name
                    ruleManage.save(force_update=True)

            except Exception as e:
                RuleManage.objects.filter(
                    rule_manage_id=manageid).update(
                    system_status=RULE_STS_SYSTEM.BUILD_NG,
                    last_update_timestamp=now,
                    last_update_user=user.user_name)

                errmessage = str(now_tz) + ' ' + userlog + ' ' + \
                    get_message('MOSJA03405', user.get_lang_mode()).replace('\n', '\n')
                errmessage = errmessage + '\n' + str(now_tz) + ' ' + userlog + ' ' + str(e) + '\n'
                with open(errfilepath, 'a') as f:
                    f.write(errmessage)

                logger.system_log('LOSM12047', str(request['apply_user_id']),
                                  reqtypeid, manageid, traceback.format_exc())

                ret_info = {
                    'result': 'NG',
                    'msg': 'MOSJA03402',
                }

                logger.logic_log('LOSI00002', 'ret_info: %s' % ret_info)
                return ret_info

            if ret.returncode != 0:
                ruleManage.system_status = RULE_STS_SYSTEM.BUILD_NG
                ruleManage.last_update_timestamp = now
                ruleManage.last_update_user = user.user_name
                ruleManage.save(force_update=True)

                errmessage = str(now_tz) + ' ' + userlog + ' ' + \
                    get_message('MOSJA03406', user.get_lang_mode()).replace('\n', '\n')
                errmessage = errmessage + '\n' + str(now_tz) + ' ' + userlog + ' ' + ret.stdout.decode("utf8") + '\n'
                with open(errfilepath, 'a') as f:
                    f.write(errmessage)

                logger.system_log('LOSM12048', str(request['apply_user_id']), reqtypeid, manageid, ret.returncode)

                ret_info = {
                    'result': 'NG',
                    'msg': 'MOSJA03403',
                }

                logger.logic_log('LOSI00002', 'ret_info: %s' % ret_info)

                return ret_info

        except User.DoesNotExist:
            ret_info = {
                'result': 'NG',
                'msg': 'MOSJA03101',
            }
            logger.system_log('LOSM12022', traceback.format_exc())
            logger.logic_log('LOSI00002', ret_info)
            return ret_info

        except RuleFile.DoesNotExist:
            ret_info = {
                'result': 'NG',
                'msg': 'MOSJA03013',
            }
            logger.system_log('LOSM12019', traceback.format_exc())
            logger.logic_log('LOSI00002', ret_info)
            return ret_info

        except Exception as e:
            RuleManage.objects.filter(
                rule_manage_id=manageid).update(
                system_status=RULE_STS_SYSTEM.BUILD_NG,
                last_update_timestamp=now,
                last_update_user=user.user_name)

            errmessage = str(now_tz) + ' ' + userlog + ' ' + \
                get_message('MOSJA03406', user.get_lang_mode()).replace('\n', '\n')
            errmessage = errmessage + '\n' + str(now_tz) + ' ' + userlog + ' ' + str(e) + '\n'
            with open(errfilepath, 'a') as f:
                f.write(errmessage)
            logger.system_log('LOSM12048', str(request['apply_user_id']), reqtypeid, manageid, traceback.format_exc())

            ret_info = {
                'result': 'NG',
                'msg': 'MOSJA03403',
            }

            logger.logic_log('LOSI00002', 'ret_info: %s' % ret_info)
            return ret_info

        logger.logic_log('LOSI12003')

        res = apply(request)
        logger.logic_log('LOSI00002', 'res: %s' % res)
        return res


# ルールファイル関連パス取得
def load_filepath():

    disconnect()

    logger.logic_log('LOSI00001', 'None')

    rule_path = {}
    rule_path['rule_rootpath'] = ''
    rule_path['rule_srcpath'] = ''
    rule_path['rule_dstpath'] = ''
    rule_path['rule_filepath'] = ''

    # "System" != "os.system" | OASE_T_SYSTEM => System(model) class
    system_list = System.objects.filter(Q(config_id='RULEFILE_ROOTPATH') |
                                        Q(config_id='RULEFILE_SRCPATH'))

    for system in system_list:
        if system.config_id == 'RULEFILE_ROOTPATH':
            rule_path['rule_rootpath'] = system.value
            if not rule_path['rule_rootpath'].endswith('/'):
                rule_path['rule_rootpath'] = '%s/' % (rule_path['rule_rootpath'])

            rule_path['rule_dstpath'] = rule_path['rule_rootpath']
            rule_path['rule_filepath'] = '%s%%s/%%s/%s' % (rule_path['rule_dstpath'], 'src/main/resources/com/oase/')

        elif system.config_id == 'RULEFILE_SRCPATH':
            rule_path['rule_srcpath'] = '%s%s' % (settings.BASE_DIR, system.value)

    logger.logic_log('LOSI00002', 'rule_path: %s' % rule_path)
    return rule_path


def load_settings():
    """
    [メソッド概要]
      適用君設定情報を読み込む
    """
    disconnect()

    logger.logic_log('LOSI00001', 'None')
    apply_settings = {}
    apply_settings['host'] = '127.0.0.1'
    apply_settings['port'] = 50001

    rset = list(System.objects.filter(category='APPLYSETTINGS').values('config_id', 'value'))
    for r in rset:
        if r['config_id'] == 'APPLY_IPADDRPORT':
            apval = r['value']
            apval = apval.split(':')
            if len(apval) == 2:
                apply_settings['host'] = apval[0]
                apply_settings['port'] = int(apval[1])

    logger.logic_log('LOSI00002', 'apply_settings: %s' % apply_settings)
    return apply_settings


if __name__ == '__main__':

    logger.logic_log('LOSI00001', 'None')

    apply_settings = load_settings()
    host = apply_settings['host']
    port = apply_settings['port']

    func_info = {
        'CREATE': {'func': create, 'thread': None, 'use_recv': False, 'need_keys': ['result', 'msg']},
        'UPLOAD': {'func': upload, 'thread': build_kjar, 'use_recv': False, 'need_keys': ['result', 'msg']},
        'APPLY': {'func': apply_req, 'thread': apply, 'use_recv': True, 'need_keys': ['result', 'msg']},
        'DOWNLOAD' : {'func':download, 'thread':None, 'use_recv':False, 'need_keys':['result', 'msg', 'filename', 'filedata']},
        'DOWNLOAD_ZIP': {'func':download_zip, 'thread':None, 'use_recv':False, 'need_keys':['result', 'msg', 'filename', 'filedata']},
        'DOWNLOAD_DT' : {'func':download_dt, 'thread':None, 'use_recv':False, 'need_keys':['result', 'msg', 'filename', 'filedata']},
        'DELETE': {'func': delete, 'thread': None, 'use_recv': False, 'need_keys': ['result', 'msg']},
    }

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8192)
        sock.bind((host, port))
        sock.listen(5)

        logger.logic_log('LOSI12004')

        while True:
            try:
                logger.logic_log('LOSI12005', host, port)
                recv_data = bytes(b'')
                clientsocket, (client_address, client_port) = sock.accept()
                logger.logic_log('LOSI12006', client_address, client_port)
                with clientsocket:
                    while True:
                        rcvtmp = clientsocket.recv(4096)
                        if not rcvtmp:
                            logger.logic_log('LOSI12013', len(recv_data))
                            break

                        recv_data = b'%s%s' % (recv_data, rcvtmp)

                    rule_path = load_filepath()
                    recv_data = recv_data.decode()
                    recv_data = json.loads(recv_data)
                    recv_data.update(rule_path)

                    need_keys = []
                    send_data = {}
                    if recv_data['request'] in func_info:

                        need_keys = func_info[recv_data['request']]['need_keys']
                        send_data = func_info[recv_data['request']]['func'](recv_data)
                        req_data = recv_data
                        if not func_info[recv_data['request']]['use_recv']:
                            req_data = make_send_data(send_data, omit_keys=['result', 'msg'])
                        req_data.update(rule_path)

                        if func_info[recv_data['request']]['thread']:
                            if 'result' in send_data and send_data['result'] == 'OK':
                                thrd = threading.Thread(
                                    target=func_info[recv_data['request']]['thread'], args=(req_data,))
                                thrd.start()

                    else:
                        logger.system_log('LOSM12049', 'request: %s' % recv_data['request'])
                        need_keys = ['result', 'msg']
                        send_data = {
                            'result': 'NG',
                            'msg': 'MOSJA03001'
                        }

                    send_data = make_send_data(send_data, need_keys=need_keys)
                    ret_info = send_data
                    send_data = json.dumps(send_data)
                    send_data = send_data.encode()

                    clientsocket.sendall(send_data)
                    clientsocket.shutdown(socket.SHUT_RDWR)
                    clientsocket.close()

                    logger.logic_log('LOSI00002', 'result: %s, msg: %s' % (ret_info['result'], ret_info['msg']))

            except Exception as e:
                logger.system_log('LOSM12049', traceback.format_exc())
                logger.logic_log('LOSI00002', 'apply_settings: %s' % apply_settings)

        sock.close()
