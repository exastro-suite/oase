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
加工したリクエストをDMに投げ、ルールマッチング結果を取得する。
マッチング結果を保存する。
"""

import requests
import json
import base64
import os
import sys
import ssl
import urllib3
import time
from collections import OrderedDict
import calendar
import concurrent.futures
from abc import ABCMeta, abstractmethod
from urllib3.exceptions import InsecureRequestWarning
import pytz
import datetime
import copy
import django
import traceback
import re
import ast
import fcntl

# --------------------------------
# 環境変数取得
# --------------------------------
try:
    oase_root_dir = os.environ['OASE_ROOT_DIR']
    run_interval = os.environ['RUN_INTERVAL']
    python_module = os.environ['PYTHON_MODULE']
    log_level = os.environ['LOG_LEVEL']
except Exception as e:
    oase_root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../')
    run_interval = "10"
    python_module = "/usr/bin/python3"
    log_level = "NORMAL"


# --------------------------------
# パス追加
# --------------------------------
sys.path.append(oase_root_dir)

# --------------------------------
# django読み込み
# --------------------------------
os.environ['DJANGO_SETTINGS_MODULE'] = 'confs.frameworkconfs.settings'
django.setup()

from django.db import transaction, IntegrityError
from django.db.models import F
from django.conf import settings
from django.urls import reverse

# --------------------------------
# ロガー追加
# --------------------------------
from libs.commonlibs.oase_logger import OaseLogger
logger = OaseLogger.get_instance() # ロガー初期化

# --------------------------------
# oase lib追加
# --------------------------------
from web_app.models.models import User, EventsRequest, RhdmResponse, RhdmResponseAction, System, RuleType
from web_app.models.models import ActionType, DataObject, DriverType, RhdmResponseCorrelation
from libs.commonlibs.define import *
from libs.commonlibs.dt_component import DecisionTableComponent
from libs.commonlibs.aes_cipher import AESCipher
from web_app.templatetags.common import get_message
from libs.webcommonlibs.oase_mail import OASEMailSMTP, OASEMailUnknownEventNotify

urllib3.disable_warnings(InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context

# --------------------------------
# コンフィグファイル読み込み設定
# --------------------------------
rset = list(System.objects.filter(category='DMSETTINGS').values('config_id', 'value'))
dmconf = {r['config_id']:r['value'] for r in rset}
# パスワードを復号
cipher = AESCipher(settings.AES_KEY)
dmconf['DM_PASSWD'] = cipher.decrypt(dmconf['DM_PASSWD'])


# --------------------------------
# 負荷テスト設定
# --------------------------------
ENABLE_LOAD_TEST = getattr(settings, 'ENABLE_LOAD_TEST', False)
if ENABLE_LOAD_TEST:
    import logging
    loadtest_logger = logging.getLogger('oase_agent')


#ホスト名　コンフィグファイルに移動すべきか？
MAX_WORKER = 5


AGENT_USER_ID = -2140000002


class ActUtil:
    """
    [概要]
    DMのアクション情報格納用のDataObjectの変数名,クラス名
    """
    
    rule_name = 'ruleName'
    execution_order = 'executionOrder'
    type_id = 'id'
    server_list = 'serverList'
    parameter_info = 'parameterInfo'
    pre_info = 'preInfo'
    retry_interval = 'retryInterval'
    retry_count = 'retryCount'
    stop_interval = 'stopInterval'
    stop_count = 'stopCount'
    cond_count = 'condCount'
    cond_term = 'condTerm'
    cond_large_group = 'condGroup1'
    cond_large_priority = 'condPriority1'
    cond_small_group = 'condGroup2'
    cond_small_priority = 'condPriority2'
    incident_happened = 'incidentHappened'
    handling_summary = 'handlingSummary'


class Driver:
    """
    [概要]
    ルール毎のドライバー
    """

    def __init__(self, request_type_id, rule_type_id, trace_id=''):
        """
        [概要]
        """

        logger.logic_log('LOSI00001', 'TraceID: %s, request_type_id: %s, rule_type_id: %s' % (trace_id, request_type_id, rule_type_id))

        self.__trace_id = trace_id
        self.lost_flag  = False
        self.err_flag   = False
        self.none_cont  = False
        self.ruletype   = None

        try:
            self.ruletype = RuleType.objects.get(rule_type_id=rule_type_id)
            dataobjects = list(DataObject.objects.filter(rule_type_id=rule_type_id).order_by('data_object_id').values_list('label', flat=True))
            dataobjects = list(dict.fromkeys(dataobjects))
            dtcomp = DecisionTableComponent(self.ruletype.rule_table_name)

        except RuleType.DoesNotExist as e:
            self.lost_flag = True
            self.err_flag  = True
            logger.system_log('LOSE02000', trace_id, RuleType, traceback.format_exc())
            logger.logic_log('LOSI00002', 'TraceID: %s' % trace_id)
            return None

        except DataObject.DoesNotExist as e:
            self.lost_flag = True
            self.err_flag  = True
            logger.system_log('LOSE02000', trace_id, DataObject, traceback.format_exc())
            logger.logic_log('LOSI00002', 'TraceID: %s' % trace_id)
            return None

        except Exception as e:
            self.err_flag  = True
            logger.system_log('LOSE02000', trace_id, RuleType, traceback.format_exc())
            logger.logic_log('LOSI00002', 'TraceID: %s' % trace_id)
            return None

        self.__insert_obj = '%s.%s' % (dtcomp.rule_set, dtcomp.class_name)
        self.__insert_vars = []
        self.__insert_vars.extend(dataobjects)
        self.__action_ins_name = 'acts'
        self._lookup = 'ksession-dtables' 
        self.__insert_vars.append(self.action_ins_name)
        self.request_type_id = request_type_id
        self.__container_id = self.get_containerid(request_type_id, self.ruletype)

        if not self.__container_id:
            self.err_flag  = True
            self.none_cont = True
            logger.logic_log('LOSE02011', trace_id, rule_type_id, request_type_id)

        logger.logic_log('LOSI00002', 'TraceID: %s' % trace_id)

    @property
    def trace_id(self):
        return self.__trace_id
    @property
    def insert_obj(self):
        return self.__insert_obj
    @property
    def insert_vars(self):
        return self.__insert_vars
    @property
    def action_ins_name(self):
        return self.__action_ins_name
    @property
    def container_id(self):
        return self.__container_id


    def get_containerid(self, request_type_id, ruletype):
        """
        [概要]
        [引数]
        request_type_id : str リクエスト種別
        [戻り値]
        コンテナID 取得できなければNone
        """

        logger.logic_log('LOSI00001', 'TraceID: %s, request_type_id: %s' % (self.trace_id, request_type_id))

        if request_type_id == PRODUCTION:
            logger.logic_log('LOSI00002', 'current_container_id_product: %s' % (ruletype.current_container_id_product))
            return ruletype.current_container_id_product
        elif request_type_id == STAGING:
            logger.logic_log('LOSI00002', 'current_container_id_staging: %s' % (ruletype.current_container_id_staging))
            return ruletype.current_container_id_staging

        logger.logic_log('LOSI00002', 'TraceID: %s' % self.trace_id)
        return None


    def is_matched(self, value):
        """
        [概要]
        1個以上のルールに合致したか調べる
        [引数]
        value :dict DMのresponseのvalue要素
        [戻り値]
        bool
        """
        logger.logic_log('LOSI00001', 'TraceID: %s' % self.trace_id)
        if value[self.insert_obj][self.action_ins_name][ActUtil.rule_name] == []:
            logger.system_log('LOSE02002', self.trace_id)
            logger.logic_log('LOSI00002', 'TraceID: %s' % self.trace_id)
            return False
        
        logger.logic_log('LOSI00002', 'TraceID: %s' % self.trace_id)
        return True

    def get_value(self, value):
        """
        [概要]
        [引数]
        value :dict DMのresponseのvalue要素
        [戻り値]
        list アクション用オブジェクト
        """
        return value[self.insert_obj][self.action_ins_name]


    def make_dm_postdata(self, event_to_time, event_info):
        """
        [概要]
        Coreから取得したevent_infoとevent_to_timeをDMのpostdata(json形式)に変換する
        
        [引数]
        event_info: list イベント情報のリスト
        event_to_time: str イベント発生日時'YYYY-MM-DDThh:mm:ss'
        [戻り値]
        str
        """
        logger.logic_log('LOSI00001', 'TraceID: %s, event_to_time: %s, event_info: %s' % (self.trace_id, event_to_time, event_info))
        #dmに送るデータのテンプレート
        postdata = {
            "commands":[
                {"insert":{"object":{},"out-identifier":"in"}},
                {"set-global":{"identifier":"simulatedDateTime", "object":{"java.lang.String":""}}},
                {"fire-all-rules":{}},
                {"dispose":{}}
             ]
            }
        postdata["lookup"] = self._lookup

        j = json.loads(event_info)

        try:
            insertdata = j['EVENT_INFO']
        except KeyError as e:
            logger.system_log('LOSE02003', self.trace_id, traceback.format_exc())
            logger.logic_log('LOSI00002', 'TraceID: %s' % self.trace_id)
            return None

        
        #ルール結果格納用オブジェクト用に空のデータを追加
        insertdata.append({})
     
        # insertdata と input_varlistの要素数が同じかチェック
        if(len(insertdata) != len(self.insert_vars)) : 
            logger.system_log('LOSE02004', self.trace_id, len(insertdata), len(self.insert_vars))
            logger.logic_log('LOSI00002', 'TraceID: %s' % self.trace_id)
            return None

        insert_dict = OrderedDict(zip(self.insert_vars, insertdata))

        # インプット用のオブジェクト名とその変数名を代入
        postdata['commands'][0]['insert']['object'][self.insert_obj] = insert_dict

        # イベント発生日時をセット
        postdata['commands'][1]['set-global']['object']['java.lang.String'] = event_to_time
        
        logger.system_log('LOSI02002', self.trace_id, json.dumps(postdata,ensure_ascii=False,indent=4,separators=(',',':')))
        
        logger.logic_log('LOSI00002', 'TraceID: %s' % self.trace_id)
        return json.dumps(postdata, ensure_ascii=False)

        
class DMController:
    """
    [クラス概要]
    catsleのmcoドライバ core_apやdmに送るデータの生成を行う
    """
    def __init__(self, driver):
        """
        [引数]
        driver : Driver class
        """

        self.driver = driver
        logger.logic_log('LOSI00001', 'TraceID: %s, driver: %s, err_flag: %s' % (self.driver.trace_id, driver, driver.err_flag))
        if driver.err_flag:
            logger.logic_log('LOSI00002', 'TraceID: %s, err_flag: %s' % (self.driver.trace_id, driver.err_flag))
            return

        self.request_uri = '/kie-server/services/rest/server/containers/instances'
        self.auth = (dmconf['DM_USERID'],dmconf['DM_PASSWD'])
        self.timeout = int(dmconf['DM_TIMEOUT'])
        self.url = dmconf['DM_PROTOCOL'] + '://' + dmconf['DM_IPADDRPORT_KIE'] + \
                    self.request_uri + '/' + driver.container_id
        logger.logic_log('LOSI00002', 'TraceID: %s, url: %s' % (self.driver.trace_id, self.url))

    def _post(self,postdata):
        """
        [概要]
        [引数]
        [戻り値]
        """
        logger.logic_log('LOSI00001', 'TraceID: %s, postdata: %s' % (self.driver.trace_id, postdata))
        try:
            r = requests.post(
                    self.url,
                    timeout=self.timeout,
                    auth=self.auth,
                    headers={'content-type':'application/json'} ,
                    data=postdata.encode('utf-8')
                    )
            
            r.raise_for_status()

        except requests.exceptions.RequestException as e:
            logger.system_log('LOSI02005', self.driver.trace_id, traceback.format_exc())
            raise

        logger.system_log('LOSI02003', self.driver.trace_id, str(r.status_code))

        logger.logic_log('LOSI00002', 'TraceID: %s' % self.driver.trace_id)
        return  r

    def evaluates_rules(self, event_to_time, event_info):
        """
        [概要]
        イベント発生日時とイベント情報を基にDM用のファクトデータを作成してDMに投げる。
        [引数]
        event_to_time : str イベント発生時間
        event_info : str イベント情報
        [戻り値]
        """

        logger.logic_log('LOSI00001', 'TraceID:%s, evtime:%s' % (self.driver.trace_id, event_to_time))

        postdata = self.make_dm_postdata(event_to_time, event_info)
        status, matched_data, reception_time = self.throw_fact(postdata)

        logger.system_log('LOSI02003', self.driver.trace_id, 'sts:%s, recept_time:%s, match_data:%s' % (status, reception_time, matched_data))
        logger.logic_log('LOSI00002', 'TraceID: %s, status: %s, matched_data: %s, reception_time: %s' % (self.driver.trace_id, status, matched_data, reception_time))

        return status, matched_data, reception_time

    def throw_fact(self, postdata):
        """
        [概要]
        DMにfactを投げる。マッチング結果を返す。

        [引数]
        postdata:
        [戻り値]
        ステータス:
        マッチング結果:
        レスポンス受信日時:
        """
        logger.logic_log('LOSI00001', 'TraceID: %s, postdata: %s' % (self.driver.trace_id, postdata))
        try:
            r = self._post(postdata)
            reception_time = datetime.datetime.now(pytz.timezone('UTC')).strftime("%Y/%m/%d %H:%M:%S")
        except Exception as e:
            logger.system_log('LOSE02005', self.driver.trace_id, traceback.format_exc())
            logger.logic_log('LOSI00002', 'TraceID: %s, status: %s, matched_data: %s, reception_time: %s' % (self.driver.trace_id, 'RULE_ERROR', 'None', 'None'))
            return RULE_ERROR, None, None

        decided_data = json.loads(r.text)

        #postしたデータがDMで正しく処理されたか確認
        if(self._is_failure(decided_data)):
            logger.logic_log('LOSI00002', 'TraceID: %s, status: %s, matched_data: %s, reception_time: %s' % (self.driver.trace_id, 'RULE_ERROR', 'None', 'None'))
            return RULE_ERROR, None, None

        value = decided_data['result']['execution-results']['results'][0]['value']

        #1つ以上ルールにマッチしたか確認
        if(self._is_matched(value)):
            matched_data = self._get_value(value)
        else:
            logger.logic_log('LOSI00002', 'TraceID: %s, status: %s, matched_data: %s, reception_time: %s' % (self.driver.trace_id, 'RULE_MATCH', 'None', 'None'))
            return RULE_UNMATCH, None, None

        logger.logic_log('LOSI00002', 'TraceID: %s, status: %s, matched_data: %s, reception_time: %s' % (self.driver.trace_id, 'RULE_MATCH', matched_data, reception_time))
        return RULE_MATCH, matched_data, reception_time

    def make_dm_postdata(self, event_to_time, event_info):
        """
        [概要]
        DMへpostするdataを作成。処理はdriverに委譲
        [引数]
        event_to_time : str イベント発生時間
        event_info : str イベント情報
        [戻り値]
        """
        logger.logic_log('LOSI00001', 'TraceID: %s, event_to_time: %s, event_info: %s' % (self.driver.trace_id, event_to_time, event_info))
        data = self.driver.make_dm_postdata(event_to_time, event_info)
        logger.logic_log('LOSI00002', 'TraceID: %s, data: %s' % (self.driver.trace_id, data))
        return data

    def _is_failure(self, decided_data):
        """
        [概要]
        ルール実行が失敗したか調べる
        [引数]
        decided_data: dict
            DMから帰ってきたresponseのbody(json形式)を辞書変換したもの
        [戻り値]
        bool
        """
        logger.logic_log('LOSI00001', 'TraceID: %s, decided_data: %s' % (self.driver.trace_id, decided_data))
        if decided_data['type'] =='FAILURE':
            
            logger.system_log('LOSI02005', self.driver.trace_id)
            logger.logic_log('LOSI00002', 'TraceID: %s, is_filure: %s' % (self.driver.trace_id, 'True'))
            return True

        logger.logic_log('LOSI00002', 'TraceID: %s, is_filure: %s' % (self.driver.trace_id, 'False'))
        return False

    def _is_matched(self, value):
        """
        [概要]
        ルール検出したか調べる。処理はdriverに委譲
        [引数]
        value: list
        [戻り値]
        bool
        """
        logger.logic_log('LOSI00001', 'TraceID: %s, value: %s' % (self.driver.trace_id, value))
        result = self.driver.is_matched(value)
        logger.logic_log('LOSI00002', 'TraceID: %s, result: %s' % (self.driver.trace_id, result))
        return result

    def _get_value(self, value):
        """
        [概要]
        マッチした結果を取得する。_is_matched()で調べた後に使う
        処理はdriverに委譲
        [引数]
        value: list
        [戻り値]
        """
        logger.logic_log('LOSI00001', 'TraceID: %s, value: %s' % (self.driver.trace_id, value))
        result = self.driver.get_value(value)
        logger.logic_log('LOSI00002', 'TraceID: %s, result: %s' % (self.driver.trace_id, result))
        return result

class Agent:
    """
    [クラス概要]
    CoreとDMの仲介役
    """
    
    def __init__(self, dmctl=None, now=None):
        """
        [概要]
        [引数]
        dmctl: DMControllerクラスのインスタンス
        [戻り値]
        """

        logger.logic_log('LOSI00001', 'dmctl:%s, now:%s' % (dmctl, now))

        if not now:
            now = datetime.datetime.now(pytz.timezone('UTC'))

        self.dmctl = dmctl
        self.user = User.objects.get(user_id=AGENT_USER_ID)
        self.oase_userid = self.user.user_id
        self.now = now

        logger.logic_log('LOSI00002', 'UserID:%s' % self.oase_userid)


    def make_rhdm_response(self, trace_id, reception_time, request_type_id):
        """
        [概要]
        ルールマッチング結果管理テーブルに登録するためのデータを作成する
        [引数]
        matching_data : dmのresponse
        [戻り値]
        """

        logger.logic_log('LOSI00001', 'trace_id:%s, recept_time:%s, req_type:%s' % (trace_id, reception_time, request_type_id))

        rhdmres = RhdmResponse(
            trace_id               = trace_id,
            request_reception_time = reception_time,
            request_type_id        = request_type_id,
            resume_order           = 0,
            status                 = UNPROCESS,
            last_update_timestamp  = self.now,
            last_update_user       = self.user.user_name
        )

        return rhdmres

    def make_rhdm_response_action_data(self, acts, responseid):
        """
        [概要]
        ルールマッチング結果アクション管理に登録するためのデータを作る
        [引数]
        acts : list
            アクションのリスト
        [戻り値]
        アクション結果が格納されたリスト
        マッチング結果がなかった場合は空のリスト
        IndexErrorの場合はNone
        """

        logger.logic_log('LOSI00001', 'trace_id:%s, resp_id:%s, act_len:%s' % (self.dmctl.driver.trace_id, responseid, len(acts['id'])))

        act_type_dic = {}
        rs_act = ActionType.objects.filter(disuse_flag='0').values('action_type_id', 'driver_type_id')
        rs_dri = DriverType.objects.values('driver_type_id', 'name', 'driver_major_version')
        for act in rs_act:
            for dri in rs_dri:
                if act['driver_type_id'] == dri['driver_type_id']:
                    name = dri['name'] + '(ver' + str(dri['driver_major_version']) + ')'
                    act_type_dic[name] = act['action_type_id']

        noact_type_list = []
        for lang_key in LANG_MODE.KEY_LIST_ALL:
            str_noact_type = get_message('MOSJA03149', lang_key, showMsgId=False)
            noact_type_list.append(str_noact_type)

        no_action = get_message('MOSJA11159', self.user.get_lang_mode(), showMsgId=False)
        act_type_dic[no_action] = NO_ACTION

        #マッチングしたルールの個数をidで調べる
        length = len(acts['id'])

        paraminfo    = {}
        preinfo      = {}
        res_act_list = []

        try:
            for i in range(length):
                # グルーピングあり
                if acts[ActUtil.cond_large_group][i] not in ['x', 'X']:
                    continue

                # アクション種別なし
                if acts[ActUtil.type_id][i] in noact_type_list:
                    continue

                # アクション種別名からアクションIDに変換
                if acts[ActUtil.type_id][i] not in act_type_dic:
                    logger.system_log('LOSE02006', self.dmctl.driver.trace_id)
                    return None

                act_type  = act_type_dic[acts[ActUtil.type_id][i]]

                # アクションパラメータ情報取得
                paraminfo['ACTION_PARAMETER_INFO'] = acts[ActUtil.parameter_info][i].split(',')
                act_param = json.dumps(paraminfo, ensure_ascii=False) #アクションパラメータ情報

                # 事前アクション情報取得
                pre_param = ''
                tmp = acts[ActUtil.pre_info][i].split(',')
                if not tmp or tmp==["X"] or tmp==["x"]:
                    pre_param = ''
                else:
                    preinfo['ACTION_PARAMETER_INFO'] = acts[ActUtil.pre_info][i].split(',')
                    pre_param = json.dumps(preinfo, ensure_ascii=False) #事前アクション情報

                # 発生事象情報取得
                inc_param = acts[ActUtil.incident_happened][i]
                if not inc_param or inc_param=="X" or inc_param=="x":
                    inc_param = ''

                # 対処概要取得
                hand_param = acts[ActUtil.handling_summary][i]
                if not hand_param or hand_param=="X" or hand_param=="x":
                    hand_param = ''

                res_act_list.append(
                    RhdmResponseAction(
                        response_id           = responseid,                        # レスポンスID
                        rule_name             = acts[ActUtil.rule_name][i],        # ルール名
                        execution_order       = i+1,                               # アクション実行順
                        handling_summary      = hand_param,                        # 対処概要
                        incident_happened     = inc_param,                         # 発生事象
                        action_type_id        = act_type,                          # アクション種別
                        action_parameter_info = act_param,                         # アクションパラメータ情報
                        action_pre_info       = pre_param,                         # 事前アクション情報取得
                        action_retry_interval = acts[ActUtil.retry_interval][i],   # アクションリトライ間隔
                        action_retry_count    = acts[ActUtil.retry_count][i],      # アクションリトライ回数
                        action_stop_interval  = acts[ActUtil.stop_interval][i],    # アクション中断間隔
                        action_stop_count     = acts[ActUtil.stop_count][i],       # アクション中断回数
                        last_update_timestamp = self.now,                          # 最終更新日時
                        last_update_user      = self.user.user_name                # 最終更新者
                    )
                )

        except Exception as e:
            logger.system_log('LOSE02007', self.dmctl.driver.trace_id, traceback.format_exc())


        logger.logic_log('LOSI00002', 'trace_id:%s, act_len:%s' % (self.dmctl.driver.trace_id, len(res_act_list)))

        return res_act_list


    def make_rhdm_response_correlation(self, acts, responseid):
        """
        [概要]
          ルールマッチング結果コリレーション管理に登録するためのデータを作る
        [引数]
          マッチング結果
        """

        logger.logic_log('LOSI00001', 'trace_id:%s, resp_id:%s, act_len:%s' % (self.dmctl.driver.trace_id, responseid, len(acts['id'])))

        paraminfo    = {}
        preinfo      = {}

        # アクション種別を取得
        act_type_dic = {}
        rs_act = ActionType.objects.filter(disuse_flag='0').values('action_type_id', 'driver_type_id')
        rs_dri = DriverType.objects.values('driver_type_id', 'name', 'driver_major_version')
        for act in rs_act:
            for dri in rs_dri:
                if act['driver_type_id'] == dri['driver_type_id']:
                    name = dri['name'] + '(ver' + str(dri['driver_major_version']) + ')'
                    act_type_dic[name] = act['action_type_id']

        # アクション種別なしの文字列を取得
        noact_type_list = []
        for lang_key in LANG_MODE.KEY_LIST_ALL:
            str_noact_type = get_message('MOSJA03149', lang_key, showMsgId=False)
            noact_type_list.append(str_noact_type)


        no_action = get_message('MOSJA11159', self.user.get_lang_mode(), showMsgId=False)
        act_type_dic[no_action] = NO_ACTION

        # コリレーションチェック
        length = len(acts['id'])

        for i in range(length):
            if acts[ActUtil.cond_count][i] in ['x', 'X']:
                acts[ActUtil.cond_count][i] = 0

            if acts[ActUtil.cond_term][i] in ['x', 'X']:
                acts[ActUtil.cond_term][i] = 0

            if acts[ActUtil.cond_large_priority][i] in ['x', 'X']:
                acts[ActUtil.cond_large_priority][i] = 0

            if acts[ActUtil.cond_small_priority][i] in ['x', 'X']:
                acts[ActUtil.cond_small_priority][i] = 0

            save_data = self.check_group_cond(
                responseid,
                acts[ActUtil.rule_name][i],
                int(acts[ActUtil.cond_count][i]),
                int(acts[ActUtil.cond_term][i]),
                acts[ActUtil.cond_large_group][i],
                int(acts[ActUtil.cond_large_priority][i]),
                acts[ActUtil.cond_small_group][i],
                int(acts[ActUtil.cond_small_priority][i])
            )

            logger.logic_log('LOSI02006', self.dmctl.driver.trace_id, save_data)

            # DB保存
            if save_data:
                res_act = None

                # 条件達成、かつ、アクションがともなう場合は、先にルールマッチング結果アクション管理を保存
                if  save_data['status'] == 0 \
                and save_data['my_count'] >= int(acts[ActUtil.cond_count][i]) \
                and acts[ActUtil.type_id][i] not in noact_type_list:

                    # アクション種別名からアクションIDに変換
                    if acts[ActUtil.type_id][i] not in act_type_dic:
                        logger.system_log('LOSE02006', self.dmctl.driver.trace_id)
                        raise Exception('Cannot get action type id.')

                    act_type  = act_type_dic[acts[ActUtil.type_id][i]]

                    # アクションパラメータ情報取得
                    paraminfo['ACTION_PARAMETER_INFO'] = acts[ActUtil.parameter_info][i].split(',')
                    act_param = json.dumps(paraminfo, ensure_ascii=False) #アクションパラメータ情報

                    # 事前アクション情報取得
                    pre_param = ''
                    tmp = acts[ActUtil.pre_info][i].split(',')
                    if not tmp or tmp==["X"] or tmp==["x"]:
                        pre_param = ''

                    else:
                        preinfo['ACTION_PARAMETER_INFO'] = acts[ActUtil.pre_info][i].split(',')
                        pre_param = json.dumps(preinfo, ensure_ascii=False) #事前アクション情報

                    # 発生事象情報取得
                    inc_param = acts[ActUtil.incident_happened][i]
                    if not inc_param or inc_param=="X" or inc_param=="x":
                        inc_param = ''

                    # 対処概要取得
                    hand_param = acts[ActUtil.handling_summary][i]
                    if not hand_param or hand_param=="X" or hand_param=="x":
                        hand_param = ''


                    # アクション情報をDB保存
                    res_act = RhdmResponseAction(
                        response_id           = responseid,                        # レスポンスID
                        rule_name             = acts[ActUtil.rule_name][i],        # ルール名
                        execution_order       = i+1,                               # アクション実行順
                        handling_summary      = hand_param,                        # 対処概要
                        incident_happened     = inc_param,                         # 発生事象
                        action_type_id        = act_type,                          # アクション種別
                        action_parameter_info = act_param,                         # アクションパラメータ情報
                        action_pre_info       = pre_param,                         # 事前アクション情報取得
                        action_retry_interval = acts[ActUtil.retry_interval][i],   # アクションリトライ間隔
                        action_retry_count    = acts[ActUtil.retry_count][i],      # アクションリトライ回数
                        action_stop_interval  = acts[ActUtil.stop_interval][i],    # アクション中断間隔
                        action_stop_count     = acts[ActUtil.stop_count][i],       # アクション中断回数
                        last_update_timestamp = self.now,                          # 最終更新日時
                        last_update_user      = self.user.user_name                # 最終更新者
                    )
                    res_act.save(force_insert=True)

                # ルールの達成状態を保存
                self._save_rhdm_response_correlation(
                    save_data['rule_name'],
                    save_data['cond_cnt'],
                    save_data['cond_term'],
                    save_data['group1_name'],
                    save_data['priority1'],
                    save_data['group2_name'],
                    save_data['priority2'],
                    save_data['my_count'],
                    save_data['status'],
                    res_act.response_detail_id if res_act else None
                )


    def check_group_cond(self, resp_id, rule_name, cond_cnt, cond_term, group1_name, priority1, group2_name, priority2):
        """
        [概要]
          グループ情報を持つルールのアクション条件をチェックする
        [引数]
          コリレーション情報
        """

        def _get_priority(group2_flg, prio1, prio2):

            return prio2 if group2_flg else prio1


        logger.logic_log(
            'LOSI00001',
            'trace_id:%s, rule_name:%s, gr1:%s, gr2:%s, prio1:%s, prio2:%s' % (
                self.dmctl.driver.trace_id, rule_name, group1_name, group2_name, priority1, priority2
            )
        )

        save_flg = False
        correlation_info = {}


        # グループ情報なしの場合はチェック処理を行わない
        if group1_name in ['x', 'X']:
            return correlation_info

        # ルールマッチング結果管理の状態を「コリレーション」に遷移
        RhdmResponse.objects.filter(response_id=resp_id).update(status=CORRELATION)

        # 小グループの有無をチェック
        group2_flg = True
        if group2_name in ['x', 'X']:
            group2_flg = False
            priority2  = 0

        # ヒットルールが始点ルールかチェック
        start_point_flg = False
        priority_ev = _get_priority(group2_flg, priority1, priority2)
        if priority_ev == 1:
            start_point_flg = True


        # 同一グループのレコード取得
        rset = RhdmResponseCorrelation.objects.filter(
            rule_type_id     = self.dmctl.driver.ruletype.rule_type_id,
            request_type_id  = self.dmctl.driver.request_type_id,
            cond_large_group = group1_name
        ).values(
            'rule_name', 'cond_count', 'cond_term',
            'cond_large_group', 'cond_large_group_priority', 'cond_small_group', 'cond_small_group_priority',
            'current_count', 'start_time', 'status'
        ).order_by('cond_large_group_priority')

        # 同一グループの状態確認
        start_flg = False
        pre_count = 0
        my_count  = 0
        my_status = 0

        for rs in rset:
            priority_db = _get_priority(group2_flg, rs['cond_large_group_priority'], rs['cond_small_group_priority'])
            expire_time = rs['start_time'] + datetime.timedelta(seconds=rs['cond_term'])

            # 始点ルールが存在し、かつ、期限内であれば前提あり
            if priority_db == 1 and self.now < expire_time:
                start_flg = True

            # 自身の前提ルールの達成回数を保持
            if start_flg and priority_db == priority_ev - 1:
                pre_count = rs['current_count']

            # 自身の達成回数と状態を保持
            if start_flg and (rs['rule_name'] == rule_name) and (self.now < expire_time):
                my_count  = rs['current_count']
                my_status = rs['status']


        # 有効な始点ルールが存在せず、かつ、自身が始点ルールの場合は 1 からカウント
        if not start_flg and start_point_flg:
            my_count = 1
            save_flg = True

        # 有効な始点ルールが存在し、かつ、自身が始点ルールの場合は達成回数をカウントアップ
        elif start_flg and start_point_flg:
            save_flg = True
            my_count = my_count + 1

        # 前提ルールの条件達成回数未満であれば自身の達成回数をカウントアップ
        elif start_flg and my_count < pre_count:
            save_flg = True
            my_count = my_count + 1

        # DB保存するコリレーション情報を返す
        if save_flg:
            correlation_info['rule_name']   = rule_name
            correlation_info['cond_cnt']    = cond_cnt
            correlation_info['cond_term']   = cond_term
            correlation_info['group1_name'] = group1_name
            correlation_info['priority1']   = priority1
            correlation_info['group2_name'] = group2_name
            correlation_info['priority2']   = priority2
            correlation_info['my_count']    = my_count
            correlation_info['status']      = my_status

        return correlation_info


    def replace_reserv_var(self, events_request, data_obj_list, act_lists):
        """
        [概要]
        予約変数をイベント情報の値に置換する
        [引数]
        [戻り値]
        """

        loop = 0
        for act in act_lists:
            conditional_name_list = re.findall(r"{{ VAR_(\S+?) }}", act)

            for conditional_name in conditional_name_list:
                i = 0
                temp_list = []
                for data_obj in data_obj_list:

                    if conditional_name == data_obj:
                        replace = ast.literal_eval(events_request.event_info)['EVENT_INFO'][i]
                        act = act.replace('{{ VAR_' + conditional_name + ' }}', replace)
                        act_lists[loop] = act
                        break

                    if data_obj not in temp_list:
                        temp_list.append(data_obj)
                        i = i + 1

            loop = loop + 1

        return act_lists


    def decide(self, event_req, mode):
        """
        [概要]
        Get君から得たレコードを処理する
        [引数]
        [戻り値]
        """
        logger.logic_log('LOSI00001', 'TraceID:%s, mode:%s, retry:%s' % (
            event_req.trace_id, mode, event_req.retry_cnt))

        integrity_flag = False

        # ルール種別、もしくは、コンテナーが存在しない場合は、「異常終了」へ状態遷移
        if self.dmctl.driver.lost_flag or self.dmctl.driver.none_cont:
            return self._is_rules(event_req)

        # 初期化エラーの場合は中断
        if self.dmctl.driver.err_flag:
            logger.logic_log('LOSI00002', 'Driver class initialize error. TraceID: %s' % (event_req.trace_id))
            return False

        # モードによってステータス変更および試行回数のカウントアップ
        is_valid = self._check_mode(event_req, mode)
        if not is_valid:
            return False

        try:
            with transaction.atomic():
                #--------------------------
                # イベント情報をdm用に加工してpostする。マッチング結果を調べる
                #--------------------------
                ett = event_req.event_to_time.strftime('%Y-%m-%dT%H:%M:%S')
                rule_result, act_lists, reception_time = self.dmctl.evaluates_rules(
                    ett,
                    event_req.event_info,
                )
                #--------------------------
                # ルール実行結果からステータスを取得する
                #--------------------------
                status = self._get_status(mode, rule_result)

                #--------------------------
                # ルール実行に失敗したり、ルールにマッチしなかった場合は終了
                #--------------------------
                if status == RULE_ERROR or status == RULE_UNMATCH:
                    EventsRequest.objects.filter(request_id=event_req.request_id).update(
                        status=status, last_update_timestamp=self.now, last_update_user=self.user.user_name)

                    #--------------------------
                    # ルールにマッチしなかった場合は未知事象通知
                    #--------------------------
                    if status == RULE_UNMATCH:
                        notify_param = {
                            'decision_table_name' : self.dmctl.driver.ruletype.rule_type_name,
                            'event_to_time' : event_req.event_to_time,
                            'request_reception_time' : event_req.request_reception_time,
                            'event_info' : event_req.event_info,
                            'trace_id' : event_req.trace_id,
                        }

                        self._notify_unknown_event(
                            event_req.request_type_id,
                            notify_param
                        )

                #--------------------------
                #ルールにマッチした場合の処理
                #--------------------------
                else:
                    dt_reception = datetime.datetime.strptime(reception_time, "%Y/%m/%d %H:%M:%S")
                    rcnt = RhdmResponse.objects.filter(trace_id=event_req.trace_id).count()
                    if rcnt > 0:
                        logger.system_log('LOSE02001', event_req.trace_id, 1, rcnt)
                        raise Exception('Data length error.')

                    response = self.make_rhdm_response(
                        event_req.trace_id,
                        dt_reception,
                        event_req.request_type_id
                    )
                    response.save(force_insert=True)

                    events_request = EventsRequest.objects.get(trace_id=event_req.trace_id)
                    data_obj_list = DataObject.objects.filter(rule_type_id=events_request.rule_type_id).order_by(
                        'data_object_id').values_list('conditional_name', flat=True)

                    parame_lists = self.replace_reserv_var(events_request, data_obj_list, act_lists['parameterInfo'])
                    act_lists['parameterInfo'] = parame_lists

                    action_pre_lists = self.replace_reserv_var(events_request, data_obj_list, act_lists['preInfo'])
                    act_lists['preInfo'] = action_pre_lists

                    # マッチング結果詳細に登録するためのリストを生成して登録
                    rhdm_res_act_data = self.make_rhdm_response_action_data(
                        act_lists,
                        response.response_id
                    )

                    # マッチング結果コリレーション管理の情報かチェックして登録
                    self.make_rhdm_response_correlation(act_lists, response.response_id)

                    self._create_rhdm_res_act_data(rhdm_res_act_data)

                    EventsRequest.objects.filter(request_id=event_req.request_id).update(
                        status=status, last_update_timestamp=self.now, last_update_user=self.user.user_name)

        except IntegrityError as e:
            integrity_flag = True
            logger.system_log('LOSE02010', event_req.trace_id, traceback.format_exc())

        except Exception as e:
            logger.system_log('LOSM02001', event_req.trace_id, traceback.format_exc())
            try:
                with transaction.atomic():
                    EventsRequest.objects.filter(request_id=event_req.request_id).update(
                        status=SERVER_ERROR, last_update_timestamp=self.now, last_update_user=self.user.user_name)
            except Exception as e:
                logger.system_log('LOSE02008', event_req.trace_id, SERVER_ERROR, traceback.format_exc())


        # DB制約エラーとなるリクエストは再実行させない
        if integrity_flag:
            try:
                with transaction.atomic():
                    EventsRequest.objects.filter(request_id=event_req.request_id).update(
                        status=SERVER_ERROR, last_update_timestamp=self.now, last_update_user=self.user.user_name)
            except Exception as e:
                logger.system_log('LOSE02008', event_req.trace_id, SERVER_ERROR, traceback.format_exc())


        logger.logic_log('LOSI00002', 'TraceID:%s, integrity_flag:%s' % (event_req.trace_id, integrity_flag))
        return False


    def _is_rules(self, event_req):
        """
        ルール種別、もしくは、コンテナーが存在しない場合は、「異常終了」へ状態遷移する。
        TrueまたはFalseを返す。
        """
        try:
            with transaction.atomic():
                EventsRequest.objects.filter(request_id=event_req.request_id).update(
                    status=SERVER_ERROR, last_update_timestamp=self.now, last_update_user=self.user.user_name)
        except Exception as e:
            logger.system_log('LOSE02008', event_req.trace_id, SERVER_ERROR, traceback.format_exc())            
            return False

        if self.dmctl.driver.lost_flag:
            logger.logic_log('LOSI00002', 'RuleType lost. TraceID: %s' % (event_req.trace_id))

        if self.dmctl.driver.none_cont:
            logger.logic_log('LOSI00002', 'Container nothing. TraceID: %s' % (event_req.trace_id))

        return True

    def _check_mode(self, event_req, mode):
        """
        modeをcheckする。
        例外の場合はFalseを返す。
        """
        # 通常モードの場合は、「処理中」へ状態遷移
        if mode == NORMAL:
            try:
                with transaction.atomic():
                    EventsRequest.objects.filter(request_id=event_req.request_id, status=event_req.status).update(
                        status=PROCESSING, last_update_timestamp=self.now, last_update_user=self.user.user_name)
            except Exception as e:
                logger.system_log('LOSE02008', event_req.trace_id, PROCESSING, traceback.format_exc())
                return False

        # 再実行モードの場合は、試行回数をカウントアップ
        elif mode == RECOVER:
            try:
                with transaction.atomic():
                    EventsRequest.objects.filter(
                        request_id=event_req.request_id, 
                        status=event_req.status
                    ).update(
                        retry_cnt=F('retry_cnt')+1, 
                        last_update_timestamp=self.now, 
                        last_update_user=self.user.user_name
                    )
            except Exception as e:
                logger.system_log('LOSE02008', event_req.trace_id, PROCESSING, traceback.format_exc())
                return False
        return True


    def _get_status(self, mode, rule_result):
        """
        ルール実行結果からステータスをgetする。
        statusを返す。
        """
        if rule_result == RULE_MATCH and mode == NORMAL:
            return PROCESSED
        elif rule_result == RULE_MATCH and mode == RECOVER:
            return FORCE_PROCESSED
        elif rule_result == RULE_UNMATCH:
            return RULE_UNMATCH
        else:
            return RULE_ERROR

    def _create_rhdm_res_act_data(self, rhdm_res_act_data):
        """
        rhdm_res_act_dataが
        無ければExceptionをあげる。
        あればデータを作成する。
        """
        """
        if rhdm_res_act_data is None:
            raise Exception('Cannot get action type id.')
        """

        if len(rhdm_res_act_data) <= 0:
            return
            #raise Exception('Cannot make dm response action data.')

        RhdmResponseAction.objects.bulk_create(rhdm_res_act_data)


    def _save_rhdm_response_correlation(
        self,
        rule_name, cond_cnt, cond_term,
        group1_name, priority1, group2_name, priority2,
        cur_cnt, sts, resp_id
    ):
        """
        [概要]
          ルールマッチング結果コリレーション管理テーブルへレコードを保存する
        [引数]
          保存する情報
        """

        rcnt = RhdmResponseCorrelation.objects.filter(
            rule_type_id    = self.dmctl.driver.ruletype.rule_type_id,
            request_type_id = self.dmctl.driver.request_type_id,
            rule_name       = rule_name
        ).count()

        if rcnt > 0:
            RhdmResponseCorrelation.objects.filter(
                rule_type_id    = self.dmctl.driver.ruletype.rule_type_id,
                request_type_id = self.dmctl.driver.request_type_id,
                rule_name       = rule_name
            ).update(
                cond_large_group          = group1_name,
                cond_large_group_priority = priority1,
                cond_small_group          = group2_name,
                cond_small_group_priority = priority2,
                cond_count                = cond_cnt,
                cond_term                 = cond_term,
                current_count             = cur_cnt,
                start_time                = self.now,
                response_detail_id        = resp_id,
                status                    = sts,
                last_update_timestamp     = self.now,
                last_update_user          = self.user.user_name
            )

        else:
            RhdmResponseCorrelation(
                rule_type_id              = self.dmctl.driver.ruletype.rule_type_id,
                rule_name                 = rule_name,
                request_type_id           = self.dmctl.driver.request_type_id,
                cond_large_group          = group1_name,
                cond_large_group_priority = priority1,
                cond_small_group          = group2_name,
                cond_small_group_priority = priority2,
                cond_count                = cond_cnt,
                cond_term                 = cond_term,
                current_count             = cur_cnt,
                start_time                = self.now,
                response_detail_id        = resp_id,
                status                    = sts,
                last_update_timestamp     = self.now,
                last_update_user          = self.user.user_name
            ).save(force_insert=True)


    def _notify_unknown_event(self, req_type, notify_param):
        """
        未知事象のイベントを通知する
        """

        logger.logic_log(
            'LOSI00001', 'TraceID:%s, req_type:%s, notify_type:%s, mail_addr:%s' % (
                notify_param.get('trace_id'),
                req_type,
                self.dmctl.driver.ruletype.unknown_event_notification,
                self.dmctl.driver.ruletype.mail_address
            )
        )

        # キーチェック
        err_keys = []
        key_list = [
            'decision_table_name',
            'event_to_time',
            'request_reception_time',
            'event_info',
            'trace_id',
        ]

        for k in key_list:
            if k not in notify_param:
                err_keys.append(k)

        if len(err_keys) > 0:
            logger.logic_log('LOSI00002', 'Invalid notify parameter. keys:%s' % (err_keys))
            return

        trace_id = notify_param['trace_id']


        # 本番環境リクエスト以外は通知対象外
        if req_type != PRODUCTION:
            logger.logic_log('LOSI00002', 'Not Production. TraceID:%s' % (trace_id))
            return

        # 対象ルールの通知設定チェック
        if self.dmctl.driver.ruletype.unknown_event_notification != '1': # 1:メール通知
            logger.logic_log('LOSI00002', 'Not notify. TraceID:%s' % (trace_id))
            return

        if not self.dmctl.driver.ruletype.mail_address:
            logger.logic_log('LOSI00002', 'No mail address is defined. TraceID:%s' % (trace_id))
            return

        mail_list = self.dmctl.driver.ruletype.mail_address.split(';')

        # メール署名用URL
        url = getattr(settings, 'HOST_NAME', None)
        if not url:
            logger.logic_log('LOSI00002', 'No host is defined. TraceID:%s' % (trace_id))
            return

        url = url.rstrip('/')

        login_url   = reverse('web_app:top:login')
        inquiry_url = reverse('web_app:top:inquiry')
        login_url   = '%s%s' % (url, login_url)
        inquiry_url = '%s%s' % (url, inquiry_url)

        # メール情報作成
        smtp = OASEMailSMTP()
        for m in mail_list:
            m = m.strip()
            notify_mail = OASEMailUnknownEventNotify(
                m,
                notify_param,
                inquiry_url,
                login_url
            )
            smtp.send_mail(notify_mail)

        logger.logic_log('LOSI00002', 'Send mail. TraceID:%s' % (trace_id))


def check_rhdm_response_correlation(now):
    """
    [概要]
      マッチング結果コリレーション管理の状態をチェックする
    [戻り値]
    """

    def init_pre_info(sts):

        pre_info = {
            'rule_type_id'     : 0,
            'request_type_id'  : 0,
            'cond_large_group' : '',
            'cond_small_group' : '',
            'status'           : sts,
        }

        return pre_info


    logger.logic_log('LOSI00001', 'Check correlation info.')

    STS_REGISTED     = 0
    STS_REGISTABLE   = 1
    STS_NOTACHIEVE   = 2
    STS_ACHIEVED     = 3
    STS_UNACHIEVABLE = 4

    group_info = {}
    pre_info   = init_pre_info(STS_ACHIEVED)

    # 未アクションのコリレーション情報を取得
    rset = RhdmResponseCorrelation.objects.filter(status=STS_REGISTED)
    rset = rset.values_list(
        'correlation_id', 'rule_type_id', 'request_type_id',
        'rule_name',
        'cond_large_group', 'cond_small_group', 'cond_small_group_priority', 'cond_large_group_priority',
        'cond_count', 'cond_term',
        'current_count', 'start_time',
        'response_detail_id'
    )
    rset = rset.order_by(
        'rule_type_id', 'request_type_id',
        'cond_large_group', 'cond_small_group', 'cond_small_group_priority', 'cond_large_group_priority'
    )

    # 各グループの状態チェック
    for cid, rule_id, req_id, rname, gr1, gr2, prio1, prio2, cond_cnt, cond_term, cur_cnt, stime, resp_id in rset:

        # 前レコードと異なるグループの場合、
        if rule_id != pre_info['rule_type_id'] \
        or req_id  != pre_info['request_type_id'] \
        or gr1     != pre_info['cond_large_group']:
            pre_info = init_pre_info(STS_ACHIEVED)

        # 前レコードと小グループが異なる場合、前ルールの状態をリセット
        elif gr2 != pre_info['cond_small_group']:
            pre_info['status'] = STS_ACHIEVED

        ####################################
        # 条件達成チェック
        ####################################
        status = STS_NOTACHIEVE

        # 期限切れの場合「達成不可」へ遷移
        if now >= stime + datetime.timedelta(seconds=cond_term):
            status = STS_UNACHIEVABLE

        # 条件回数に到達、かつ、前提ルールが「達成」の場合「達成」へ遷移
        elif cond_cnt <= cur_cnt and pre_info['status'] == STS_ACHIEVED:
            status = STS_ACHIEVED


        # 現在レコードの情報を保持
        pre_info['rule_type_id']     = rule_id
        pre_info['request_type_id']  = req_id
        pre_info['cond_large_group'] = gr1
        pre_info['cond_small_group'] = gr2
        pre_info['status']           = status

        if rule_id not in group_info:
            group_info[rule_id] = {}

        if req_id not in group_info[rule_id]:
            group_info[rule_id][req_id] = {}

        if gr1 not in group_info[rule_id][req_id]:
            group_info[rule_id][req_id][gr1] = {}

        if gr2 not in group_info[rule_id][req_id][gr1]:
            group_info[rule_id][req_id][gr1][gr2] = {
                'priority' : prio1,
                'rules'    : [],
            }

        if prio1 < group_info[rule_id][req_id][gr1][gr2]['priority']:
            group_info[rule_id][req_id][gr1][gr2]['priority'] = prio1

        group_info[rule_id][req_id][gr1][gr2]['rules'].append(
            {
                'name' : rname,
                'prio' : prio2,
                'sts'  : status,
                'resp' : resp_id,
            }
        )


    # 大グループ内での優先順位チェック
    resp_ids = []
    for rule_id, v1 in group_info.items():
        for req_id, v2 in v1.items():
            for gr1, v3 in v2.items():

                del_ids = []
                mod_ids = []
                pnd_ids = []
                settle_flag = False

                for gr2, rule_info in sorted(v3.items(), key=lambda x: x[1]['priority']):

                    # 同じ小グループ内の状態チェック、および、アクションIDチェック
                    for ri in rule_info['rules']:

                        # 未達成状態の場合、状態が確定(アクションor期限切れ)するまで
                        # 後続グループをアクションさせないようフラグを立てる
                        if ri['sts'] == STS_NOTACHIEVE:
                            settle_flag = True

                        # アクションが登録されている場合
                        if  ri['resp']:
                            del_ids.append(ri['resp'])

                            # 状態が「達成」、かつ、前提グループが「達成不可」の場合、アクション実行可能
                            if ri['sts'] ==  STS_ACHIEVED and settle_flag == False:
                                settle_flag = True
                                mod_ids.append(ri['resp'])


                # アクション実行可能なグループが存在しない場合は、削除対象グループをクリア
                if len(mod_ids) <= 0:
                    del_ids.clear()

                # 削除対象グループに更新対象と同一のアクションIDがあれば削除対象から除外
                for mod_id in mod_ids:
                    while mod_id in del_ids:
                        del_ids.remove(mod_id)

                logger.logic_log('LOSI02007', rule_id, req_id, gr1, mod_ids, del_ids)

                # アクション実行登録可能な場合
                if len(mod_ids) > 0:

                    # 対象となる大グループの状態を変更
                    RhdmResponseCorrelation.objects.filter(
                        rule_type_id     = rule_id,
                        request_type_id  = req_id,
                        cond_large_group = gr1
                    ).update(
                        status           = STS_REGISTABLE
                    )

                # アクションしないレコードは削除
                if len(del_ids) > 0:
                    RhdmResponseAction.objects.filter(response_detail_id__in=del_ids).delete()

                # アクション実施レコードは実行順序を更新
                for i, md in enumerate(mod_ids, 1):
                    RhdmResponseAction.objects.filter(response_detail_id=md).update(execution_order=i)

                # アクション可能なIDを保持
                if len(mod_ids) > 0:
                    rset = RhdmResponseAction.objects.filter(response_detail_id__in=mod_ids).values_list('response_id', flat=True)
                    resp_ids.extend(rset)


    # アクション可能なマッチング結果を状態遷移させる
    logger.logic_log('LOSI02008', resp_ids)
    if len(resp_ids) > 0:
        RhdmResponse.objects.filter(response_id__in=resp_ids).update(status=UNPROCESS)


def multi(event_req_list, mode, now):
    """
    [概要]
    マルチプロセスまたは、マルチスレッド処理用
    [引数]
    [戻り値]
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKER) as executor:
        for er in event_req_list:
            driver = Driver(er.request_type_id, er.rule_type_id, er.trace_id)
            dmctl = DMController(driver)
            agent = Agent(dmctl, now=now)

            future = executor.submit(agent.decide, er, mode)


if __name__=='__main__':
    filepath = oase_root_dir + '/temp/exclusive/oase_agent.lock'
    with open(filepath, 'w') as f:
        try:
            # 排他制御を行う。
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                retry_max = 5
                try:
                    retry_max = int(System.objects.get(config_id='AGENT_RETRY_MAX').value)
                except Exception as e:
                    logger.logic_log('LOSI00005', traceback.format_exc())

                now = datetime.datetime.now(pytz.timezone('UTC'))

                #--------------------------
                #前回'処理中'で終わったレコードがあるものは再処理を行う
                #--------------------------
                logger.logic_log('LOSI02000')
                er_list = list(EventsRequest.objects.filter(status=PROCESSING, retry_cnt__lt=retry_max).order_by('request_id'))
                multi(er_list, RECOVER, now)
                #--------------------------
                #未処理のレコードを取得して処理する
                #--------------------------
                logger.logic_log('LOSI02001')
                er_list = list(EventsRequest.objects.filter(status=UNPROCESS).order_by('request_id'))
                multi(er_list, NORMAL, now)

                #--------------------------
                #コリレーション情報をチェック
                #--------------------------
                check_rhdm_response_correlation(now)

            except Exception as e:
                logger.logic_log('LOSE02009', traceback.format_exc())
  
            fcntl.flock(f, fcntl.LOCK_UN)

        except IOError:
            sys.exit(0)
