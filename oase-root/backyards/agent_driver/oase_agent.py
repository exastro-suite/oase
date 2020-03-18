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
config_file = oase_root_dir + '/confs/backyardconfs/'+ 'config.ini'

# --------------------------------
# django読み込み
# --------------------------------
os.environ['DJANGO_SETTINGS_MODULE'] = 'confs.frameworkconfs.settings'
django.setup()

from django.db import transaction, IntegrityError
from django.db.models import F
from django.conf import settings

# --------------------------------
# ロガー追加
# --------------------------------
from libs.commonlibs.oase_logger import OaseLogger
logger = OaseLogger.get_instance() # ロガー初期化

# --------------------------------
# oase lib追加
# --------------------------------
from web_app.models.models import User, EventsRequest, RhdmResponse, RhdmResponseAction, System, RuleType, ActionType, DataObject, DriverType
from libs.commonlibs.define import *
from libs.commonlibs.dt_component import DecisionTableComponent
from libs.commonlibs.aes_cipher import AESCipher

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

        ruletype = None
        try:
            ruletype = RuleType.objects.get(rule_type_id=rule_type_id)
            dataobjects = list(DataObject.objects.filter(rule_type_id=rule_type_id).order_by('data_object_id').values_list('label', flat=True))
            dataobjects = list(dict.fromkeys(dataobjects))
            dtcomp = DecisionTableComponent(ruletype.rule_table_name)

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
        self.__container_id = self.get_containerid(request_type_id, ruletype)

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
        self.url = dmconf['DM_PROTOCOL'] + '://' + dmconf['DM_IPADDRPORT'] + \
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
        self.user = User.objects.get(login_id='oase_agent')
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

        #マッチングしたルールの個数をidで調べる
        length = len(acts['id'])

        server       = {}
        paraminfo    = {}
        preinfo      = {}
        res_act_list = []
        try:
            for i in range(length):
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

                res_act_list.append(
                    RhdmResponseAction(
                        response_id           = responseid,                        # レスポンスID
                        rule_name             = acts[ActUtil.rule_name][i],        # ルール名
                        execution_order       = i+1,                               # アクション実行順
                        action_type_id        = act_type,                          # アクション種別
                        action_parameter_info = act_param,                         # アクションパラメータ情報
                        action_pre_info       = pre_param,                         # 事前アクション情報取得
                        action_retry_interval = acts[ActUtil.retry_interval][i],   # アクションリトライ間隔
                        action_retry_count    = acts[ActUtil.retry_count][i],      # アクションリトライ回数
                        action_stop_interval  = acts[ActUtil.stop_interval][i],    # アクション中断間隔
                        action_stop_count     = acts[ActUtil.stop_count][i],       # アクション中断回数
                        last_update_timestamp = self.now,                          # 最終更新日時
                        last_update_user   = self.user.user_name                   # 最終更新者
                    )
                )
                
        except Exception as e:
            logger.system_log('LOSE02007', self.dmctl.driver.trace_id, traceback.format_exc())


        logger.logic_log('LOSI00002', 'trace_id:%s, act_len:%s' % (self.dmctl.driver.trace_id, len(res_act_list)))

        return res_act_list


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
        if rhdm_res_act_data is None:
            raise Exception('Cannot get action type id.')

        if len(rhdm_res_act_data) <= 0:
            raise Exception('Cannot make dm response action data.')

        RhdmResponseAction.objects.bulk_create(rhdm_res_act_data)


def multi(event_req_list, mode):
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
            agent = Agent(dmctl)

            future = executor.submit(agent.decide, er, mode)


if __name__=='__main__':
    try:
        retry_max = 5
        try:
            retry_max = int(System.objects.get(config_id='AGENT_RETRY_MAX').value)
        except Exception as e:
            logger.logic_log('LOSI00005', traceback.format_exc())

        #--------------------------
        #前回'処理中'で終わったレコードがあるものは再処理を行う
        #--------------------------
        logger.logic_log('LOSI02000')
        er_list = list(EventsRequest.objects.filter(status=PROCESSING, retry_cnt__lt=retry_max).order_by('request_id'))
        multi(er_list, RECOVER)
        #--------------------------
        #未処理のレコードを取得して処理する
        #--------------------------
        logger.logic_log('LOSI02001')
        er_list = list(EventsRequest.objects.filter(status=UNPROCESS).order_by('request_id'))
        multi(er_list, NORMAL)

    except Exception as e:
        logger.logic_log('LOSE02009', traceback.format_exc())

