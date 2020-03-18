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
ITAのrest_apiを実行する
"""
import base64
import requests
import json
import os
import sys
import ssl
import urllib3
import datetime
import traceback
import pytz
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context

# import検索パス追加
my_path = os.path.dirname(os.path.abspath(__file__))
tmp_path = my_path.split('oase-root')
root_dir_path = tmp_path[0] + 'oase-root'
sys.path.append(root_dir_path)

from libs.commonlibs.oase_logger import OaseLogger
from libs.commonlibs.common import Common
from libs.commonlibs.define import *

from libs.backyardlibs.oase_action_common_libs import ActionDriverCommonModules
from libs.backyardlibs.oase_action_common_libs import ConstantModules as Cstobj
from libs.backyardlibs.action_driver.common.driver_core import DriverCore

logger = OaseLogger.get_instance()


class ITA1Rest:
    """
    [クラス概要]
        ITA RestAPI共通処理クラス
    """

    def __init__(self, trace_id):
        logger.logic_log('LOSI00001', 'trace_id: %s' % (trace_id))

        self.trace_id = trace_id

        logger.logic_log('LOSI00002', 'self.trace_id: %s' % (self.trace_id))

    def rest_set_config(self, configs):
        """
        [概要]
        設定値登録
        """
        logger.logic_log('LOSI00001', 'trace_id: %s, configs: %s' % (self.trace_id, configs))
        self.user = configs['user']
        self.password = configs['password']
        self.protocol = configs['Protocol']
        self.host = configs['Host']
        self.portno = configs['PortNo']
        self.menu_id = configs['menuID'] if 'menuID' in configs else ''

        logger.logic_log('LOSI00002', 'trace_id: %s' % (self.trace_id))

    def rest_symphony_execute(
            self,
            symphony_class_no,
            operation_id,
            list_symphony_instance_id,
            ary_result,
            resp_id,
            exe_order):
        """
        [概要]
          ITA RestAPI Symphony実行メゾット
        """
        logger.logic_log(
            'LOSI00001', 'trace_id: %s, symphony_class_no: %s, operation_id: %s, list_symphony_instance_id: %s' %
            (self.trace_id, symphony_class_no, operation_id, list_symphony_instance_id))
        # サ事開用設定
        proxies = {
            "http": None,
            "https": None,
        }

        keystr = self.user + ':' + self.password
        access_key_id = base64.encodestring(keystr.encode('utf8')).decode("ascii").replace('\n', '')
        url = "{}://{}:{}/default/menu/07_rest_api_ver1.php?no={}".format(
            self.protocol, self.host, self.portno, self.menu_id)

        logger.system_log('LOSI01000', url, self.trace_id)

        headers = {
            'host': '%s:%s' % (self.host, self.portno),
            'Content-Type': 'application/json',
            'Authorization': access_key_id
        }

        # X-Command
        headers['X-Command'] = 'EXECUTE'

        # SymphonyクラスIDとオペレーションを設定
        ary_execute = {}
        ary_execute['SYMPHONY_CLASS_NO'] = symphony_class_no
        ary_execute['OPERATION_ID'] = operation_id

        str_para_json_encoded = json.dumps(ary_execute)

        try:
            response = requests.post(url, headers=headers,timeout=30,verify=False,data=str_para_json_encoded.encode('utf-8'),proxies=proxies)
            ary_result['status'] = response.status_code
            ary_result['text'] = response.text

            try:
                json_string = json.dumps(response.json(), ensure_ascii=False, separators=(',', ': '))
                ary_result['response'] = json.loads(json_string)

                if ary_result['status'] != 200:
                    ary_result['response'] = json_string
                    logger.system_log('LOSM01300', self.trace_id, ary_execute['SYMPHONY_CLASS_NO'],
                                      ary_execute['OPERATION_ID'], ary_result['status'], ary_result['text'])
                    logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'False'))
                    ActionDriverCommonModules.SaveActionLog(resp_id, exe_order, self.trace_id, 'MOSJA01030')
                    return False

                if ary_result['response']['status'] != 'SUCCEED':
                    ary_result['response'] = json_string
                    logger.logic_log('LOSM01300', self.trace_id, ary_execute['SYMPHONY_CLASS_NO'],
                                     ary_execute['OPERATION_ID'], ary_result['status'], ary_result['text'])
                    logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'False'))
                    ActionDriverCommonModules.SaveActionLog(resp_id, exe_order, self.trace_id, 'MOSJA01029')
                    return False

                list_symphony_instance_id.append(ary_result['response']['resultdata']['SYMPHONY_INSTANCE_ID'])

            except Exception as ex:
                ary_result['status'] = '-1'
                back_trace = ActionDriverCommonModules.back_trace()
                ary_result['response'] = back_trace + '\nresponse.status_code:' + \
                    str(response.status_code) + '\nresponse.text\n' + response.text
                logger.system_log('LOSM01301', self.trace_id, traceback.format_exc())
                logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'False'))
                ActionDriverCommonModules.SaveActionLog(resp_id, exe_order, self.trace_id, 'MOSJA01031')
                return False

        except Exception as ex:
            ary_result['status'] = '-1'
            back_trace = ActionDriverCommonModules.back_trace()
            ary_result['response'] = back_trace + '\nhttp header\n' + str(headers)
            logger.system_log('LOSM01301', self.trace_id, traceback.format_exc())
            logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'False'))
            ActionDriverCommonModules.SaveActionLog(resp_id, exe_order, self.trace_id, 'MOSJA01032')
            return False

        logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'True'))
        ActionDriverCommonModules.SaveActionLog(resp_id, exe_order, self.trace_id, 'MOSJA01028')
        return True

    def rest_insert(self, insert_row_data, ary_result):
        """
        [概要]
        ITA RestAPI insertメゾット
        """
        logger.logic_log('LOSI00001', 'trace_id: %s' % (self.trace_id))
        # サ事開用設定
        proxies = {
            "http": None,
            "https": None,
        }

        keystr = self.user + ':' + self.password
        access_key_id = base64.encodestring(keystr.encode('utf8')).decode("ascii").replace('\n', '')
        url = "{}://{}:{}/default/menu/07_rest_api_ver1.php?no={}".format(
            self.protocol, self.host, self.portno, self.menu_id)

        logger.system_log('LOSI01000', url, self.trace_id)

        headers = {
            'host': '%s:%s' % (self.host, self.portno),
            'Content-Type': 'application/json',
            'Authorization': access_key_id
        }

        # X-Command
        headers['X-Command'] = 'EDIT'

        # insertデータを設定
        insert_data = [insert_row_data]
        str_para_json_encoded = json.dumps(insert_data)

        try:
            response = requests.post(
                url,
                headers=headers,
                timeout=30,
                verify=False,
                data=str_para_json_encoded.encode('utf-8'),
                proxies=proxies)
            ary_result['status'] = response.status_code
            ary_result['text'] = response.text

            try:
                json_string = json.dumps(response.json(), ensure_ascii=False, separators=(',', ': '))
                ary_result['response'] = json.loads(json_string)

                if ary_result['status'] != 200:
                    ary_result['response'] = json_string
                    logger.system_log('LOSM01302', self.trace_id, ary_result['status'], ary_result['response'])
                    logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'False'))
                    return False

                if ary_result['response']['resultdata']['LIST']['RAW'][0][0] != '000' or \
                   ary_result['response']['resultdata']['LIST']['NORMAL']['register']['ct'] == 0 or \
                   ary_result['response']['resultdata']['LIST']['NORMAL']['error']['ct'] != 0:

                    ary_result['response'] = ary_result['response']['resultdata']['LIST']['RAW'][0][2]
                    logger.system_log('LOSM01302', self.trace_id, ary_result['status'], ary_result['response'])
                    logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'False'))
                    return False

            except Exception as ex:
                ary_result['status'] = '-1'
                back_trace = ActionDriverCommonModules.back_trace()
                ary_result['response'] = back_trace + '\nresponse.status_code:' + \
                    str(response.status_code) + '\nresponse.text\n' + response.text
                logger.system_log('LOSM01301', self.trace_id, traceback.format_exc())
                logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'False'))
                return False

        except Exception as ex:
            ary_result['status'] = '-1'
            back_trace = ActionDriverCommonModules.back_trace()
            ary_result['response'] = back_trace + '\nhttp header\n' + str(headers)
            logger.system_log('LOSM01301', self.trace_id, traceback.format_exc())
            logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'False'))
            return False

        logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'True'))
        return True

    def rest_select(self, aryfilter, ary_result):
        """
        [概要]
          ITA RestAPI selectメゾット
        """
        logger.logic_log('LOSI00001', 'trace_id: %s, aryfilter: %s' % (self.trace_id, aryfilter))
        # サ事開用設定
        proxies = {
            "http": None,
            "https": None,
        }

        keystr = self.user + ':' + self.password
        access_key_id = base64.encodestring(keystr.encode('utf8')).decode("ascii").replace('\n', '')
        url = "{}://{}:{}/default/menu/07_rest_api_ver1.php?no={}".format(
            self.protocol, self.host, self.portno, self.menu_id)

        logger.system_log('LOSI01000', url, self.trace_id)

        headers = {
            'host': '%s:%s' % (self.host, self.portno),
            'Content-Type': 'application/json',
            'Authorization': access_key_id
        }

        # X-Command
        headers['X-Command'] = 'FILTER'

        # aryFilterの条件に合致するレコードを取得する
        str_para_json_encoded = json.dumps(aryfilter)

        try:
            response = requests.post(
                url,
                headers=headers,
                timeout=30,
                verify=False,
                data=str_para_json_encoded.encode('utf-8'),
                proxies=proxies)
            ary_result['status'] = response.status_code
            ary_result['text'] = response.text

            try:
                json_string = json.dumps(response.json(), ensure_ascii=False, separators=(',', ': '))
                ary_result['response'] = json.loads(json_string)
                if ary_result['status'] != 200:
                    ary_result['response'] = json_string
                    logger.system_log('LOSM01303', self.trace_id, ary_result['status'], ary_result['response'])
                    logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'False'))
                    return False

            except Exception as ex:
                ary_result['status'] = '-1'
                back_trace = ActionDriverCommonModules.back_trace()
                ary_result['response'] = back_trace + '\nresponse.status_code:' + \
                    str(response.status_code) + '\nresponse.text\n' + response.text
                logger.system_log('LOSM01301', self.trace_id, traceback.format_exc())
                logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'False'))
                return False

        except Exception as ex:
            ary_result['status'] = '-1'
            back_trace = ActionDriverCommonModules.back_trace()
            ary_result['response'] = back_trace + '\nhttp header\n' + str(headers)
            logger.system_log('LOSM01301', self.trace_id, traceback.format_exc())
            logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'False'))
            return False

        logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'True'))
        return True

    def rest_info(self, insert_row_data, operation_id, ary_result):
        """
        [概要]
        ITA RestAPI selectメゾット
        [引数]
        insert_row_data: dict
        operation_id: int
        ary_result: list
        """
        logger.logic_log('LOSI00001', 'trace_id: %s, operation_id: %s' % (self.trace_id, operation_id))

        # サ事開用設定
        proxies = {
            "http": None,
            "https": None,
        }

        keystr = self.user + ':' + self.password
        access_key_id = base64.encodestring(keystr.encode('utf8')).decode("ascii").replace('\n', '')
        url = "{}://{}:{}/default/menu/07_rest_api_ver1.php?no={}".format(
            self.protocol, self.host, self.portno, self.menu_id)

        headers = {
            'host': '%s:%s' % (self.host, self.portno),
            'Content-Type': 'application/json',
            'Authorization': access_key_id
        }
        headers['X-Command'] = 'INFO'
        content = json.dumps(insert_row_data)

        try:
            response = requests.post(
                url,
                headers=headers,
                timeout=30,
                verify=False,
                data=content.encode('utf-8'),
                proxies=proxies
            )

            json_string = json.dumps(
                response.json(),
                ensure_ascii=False,
                indent=4,
                separators=(',', ': ')
            )

            logger.logic_log('LOSI01300', json_string)
            ary_result['status'] = response.status_code
            ary_result['response'] = json.loads(json_string)

            logger.logic_log('LOSI00002', 'trace_id: %s, return: True' % self.trace_id)
            return True

        except requests.exceptions.RequestException as ex:
            ary_result['status'] = '-1'
            back_trace = ActionDriverCommonModules.back_trace()
            ary_result['response'] = back_trace + '\nhttp header\n' + str(headers)
            logger.system_log('LOSM01304', self.trace_id, ex)
            logger.logic_log('LOSI00002', 'trace_id: %s, return: False' % self.trace_id)
            return False

        except Exception as ex:
            ary_result['status'] = '-1'
            back_trace = ActionDriverCommonModules.back_trace()
            ary_result['response'] = back_trace + '\nresponse.status_code:' + \
                str(response.status_code) + '\nresponse.text\n' + response.text
            logger.system_log('LOSM01301', self.trace_id, traceback.format_exc())
            logger.logic_log('LOSI00002', 'trace_id: %s, return: False' % self.trace_id)
            return False

    def rest_get_row_count(self, ary_result):
        """
        [概要]
        select件数取得メゾット
        """
        return ary_result['response']['resultdata']['CONTENTS']['RECORD_LENGTH']

    def rest_get_row_data(self, ary_result):
        """
        [概要]
        selectデータ取得メゾット
        """
        logger.logic_log('LOSI00001', 'trace_id: %s' % (self.trace_id))
        if self.rest_get_row_count(ary_result) > 0:
            logger.logic_log('LOSI00002', 'trace_id: %s' % (self.trace_id))
            return ary_result['response']['resultdata']['CONTENTS']['BODY'][1:]
        logger.logic_log('LOSI00002', 'trace_id: %s, aryResul: %s' % (self.trace_id, ''))
        return []


class ITA1Core(DriverCore):
    """
    [クラス概要]
        ITAアクション処理クラス
    """

    def __init__(self, trace_id, symphony_class_no, response_id, execution_order):
        """
        [概要]
        コンストラクタ
        """
        logger.logic_log(
            'LOSI00001', 'trace_id: %s, symphony_class_no: %s, response_id: %s, execution_order: %s' %
            (trace_id, symphony_class_no, response_id, execution_order))
        self.trace_id = trace_id
        self.response_id = response_id
        self.execution_order = execution_order
        self.symphony_class_no = symphony_class_no
        self.restobj = ITA1Rest(trace_id)

        logger.logic_log('LOSI00002', 'None')

    def select_c_pattern_per_orch(self, ary_movement_list):
        """
        [概要]
        Movement一覧検索メゾット
        正常なら0を、異常ならエラーコードを返す。
        """
        logger.logic_log('LOSI00001', 'trace_id: %s, ary_movement_list: %s' %
                         (self.trace_id, ary_movement_list))
        target_table = 'C_PATTERN_PER_ORCH'
        self.restobj.menu_id = '2100000305'

        for movement_id, Items in ary_movement_list.items():
            aryfilter = {Cstobj.COL_DISUSE_FLAG: {'NORMAL': '0'},
                         Cstobj.CPPO_PATTERN_ID: {'LIST': {0: movement_id}}}
            ary_result = {}
            ret = self.restobj.rest_select(aryfilter, ary_result)
            if ret:
                row_count = self.restobj.rest_get_row_count(ary_result)
                if row_count < 1:
                    # Movement未登録
                    logger.system_log('LOSE01017', self.trace_id, target_table, self.response_id, self.execution_order, movement_id)
                    logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, Cstobj.RET_DATA_ERROR))
                    ActionDriverCommonModules.SaveActionLog(self.response_id, self.execution_order, self.trace_id, 'MOSJA01020')
                    return Cstobj.RET_DATA_ERROR
                select_data = self.restobj.rest_get_row_data(ary_result)
                ary_movement_list[movement_id]['MovementIDName'] = movement_id + ':' + select_data[0][Cstobj.CPPO_PATTERN_NAME]
            else:
                logger.system_log('LOSE01000', self.trace_id, target_table, 'Filter', ary_result['status'])
                logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, Cstobj.RET_REST_ERROR))
                ActionDriverCommonModules.SaveActionLog(self.response_id, self.execution_order, self.trace_id, 'MOSJA01019')
                return Cstobj.RET_REST_ERROR
        logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'True'))
        return 0

    def _select_c_operation_list_by_operation_name(self, operation_name, row_data, log_flg=True):
        """
        [概要]
        投入オペレーション一覧検索メゾット
        """
        logger.logic_log(
            'LOSI00001', 'trace_id: %s, operation_name: %s' %
            (self.trace_id, operation_name))
        target_table = 'C_OPERATION_LIST'
        self.restobj.menu_id = '2100000304'
        aryfilter = {
            Cstobj.COL_DISUSE_FLAG: {'NORMAL': '0'},
            Cstobj.COL_OPERATION_NAME: {'LIST': {1: operation_name}}
        }
        ary_result = {}
        ret = self.restobj.rest_select(aryfilter, ary_result)
        if ret:
            row_count  = self.restobj.rest_get_row_count(ary_result)
            if row_count < 1:
                # オペレーション未登録
                logger.system_log('LOSE01022', self.trace_id, target_table, self.response_id, self.execution_order, operation_name)
                if log_flg:
                    ActionDriverCommonModules.SaveActionLog(
                        self.response_id, self.execution_order, self.trace_id, 'MOSJA01026')
                return Cstobj.RET_DATA_ERROR
            select_data = self.restobj.rest_get_row_data(ary_result)
            for row in select_data:
                row_data.append(row)
        else:
            logger.system_log('LOSE01000', self.trace_id, target_table, 'Filter', ary_result['status'])
            ActionDriverCommonModules.SaveActionLog(self.response_id, self.execution_order, self.trace_id, 'MOSJA01026')
            return Cstobj.RET_REST_ERROR

        logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'True'))
        return 0

    def select_c_operation_list(self, ary_config, operation_id, row_data):
        """
        [概要]
        投入オペレーション一覧検索メゾット
        """
        logger.logic_log(
            'LOSI00001', 'trace_id: %s, ary_config: %s, operation_id: %s' %
            (self.trace_id, ary_config, operation_id))
        target_table = 'C_OPERATION_LIST'
        ary_config['menuID'] = '2100000304'
        self.restobj.rest_set_config(ary_config)
        aryfilter = {
            Cstobj.COL_DISUSE_FLAG: {'NORMAL': '0'},
            Cstobj.COL_OPERATION_NO_IDBH: {'LIST': {1: operation_id}}
        }
        ary_result = {}
        ret = self.restobj.rest_select(aryfilter, ary_result)
        if ret:
            row_count  = self.restobj.rest_get_row_count(ary_result)
            if row_count < 1:
                # オペレーション未登録
                logger.system_log('LOSE01022', self.trace_id, target_table, self.response_id, self.execution_order, operation_id)
                logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, Cstobj.RET_DATA_ERROR))
                ActionDriverCommonModules.SaveActionLog(self.response_id, self.execution_order, self.trace_id, 'MOSJA01026')
                return Cstobj.RET_DATA_ERROR
            select_data = self.restobj.rest_get_row_data(ary_result)
            for row in select_data:
                row_data.append(row)
        else:
            logger.system_log('LOSE01000', self.trace_id, target_table, 'Filter', ary_result['status'])
            logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, Cstobj.RET_REST_ERROR))
            ActionDriverCommonModules.SaveActionLog(self.response_id, self.execution_order, self.trace_id, 'MOSJA01026')
            return Cstobj.RET_REST_ERROR

        logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'True'))
        return 0

    def select_c_movement_class_mng(self, result):
        """
        [概要]
        "Symphony紐付Movement一覧"検索メゾット
        正常終了なら0を、異常があればエラーコードを返す。
        """
        logger.logic_log('LOSI00001', 'trace_id: %s' % (self.trace_id))
        target_table = 'C_MOVEMENT_CLASS_MNG'
        self.restobj.menu_id = '2100000311'
        aryfilter = {
            Cstobj.COL_DISUSE_FLAG: {'NORMAL': '0'},
            Cstobj.CMCM_SYMPHONY_CLASS_NO: {'LIST': {0: self.symphony_class_no}}
        }
        ary_result = {}
        ret = self.restobj.rest_select(aryfilter, ary_result)
        if ret:
            row_count = self.restobj.rest_get_row_count(ary_result)
            if row_count < 1:
                # Movement未登録
                logger.system_log('LOSE01018', self.trace_id, target_table, self.response_id, self.execution_order, self.symphony_class_no)
                logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, Cstobj.RET_DATA_ERROR))
                ActionDriverCommonModules.SaveActionLog(self.response_id, self.execution_order, self.trace_id, 'MOSJA01017')
                return Cstobj.RET_DATA_ERROR
            select_data = self.restobj.rest_get_row_data(ary_result)
            for row in select_data:
                result.append(row)
        else:
            logger.system_log('LOSE01000', self.trace_id, target_table, 'Filter', ary_result['status'])
            logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, Cstobj.RET_REST_ERROR))
            ActionDriverCommonModules.SaveActionLog(self.response_id, self.execution_order, self.trace_id, 'MOSJA01016')
            return Cstobj.RET_REST_ERROR

        logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'True'))
        return 0


    def select_symphony_movement_master(self, ary_ita_config, ary_movement_list):
        
        logger.logic_log('LOSI00001', 'trace_id: %s, ary_ita_config: %s' % (self.trace_id, ary_ita_config))
        row_data_000311 = []

        # SymphonyClassに紐づくMovement取得
        logger.system_log('LOSI01000', 'C_MOVEMENT_CLASS_MNG select', self.trace_id)
        self.restobj.rest_set_config(ary_ita_config)
        ret = self.select_c_movement_class_mng(row_data_000311)
        if ret > 0:
            logger.system_log('LOSE01011', self.trace_id, 'C_MOVEMENT_CLASS_MNG', self.response_id, self.execution_order)
            logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, ret))
            return ret
        
        # ary_movement_list
        #     movement_id:{'ORCHESTRATOR_ID':x,'MovementIDName':movement_id:MovementName}
        # SymphonyClassに紐づくMovement待避
        for row in row_data_000311:
            ary_movement_list[row[Cstobj.CMCM_PATTERN_ID]] = {'ORCHESTRATOR_ID':row[Cstobj.CMCM_ORCHESTRATOR_ID],'MovementIDName':''}

        logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, '0'))
        return 0

    def select_ita_master(self, ary_ita_config, ary_action_server_list, ary_movement_list, ary_action_server_id_name):
        """
        [概要]
        ITAマスタ情報存在確認
        """
        logger.logic_log('LOSI00001', 'trace_id: %s, ary_ita_config: %s' % (self.trace_id, ary_ita_config))
        row_data_000311 = []

        # SymphonyClassに紐づくMovement取得
        logger.system_log('LOSI01000', 'C_MOVEMENT_CLASS_MNG select', self.trace_id)
        self.restobj.rest_set_config(ary_ita_config)
        ret = self.select_c_movement_class_mng(row_data_000311)
        if ret > 0:
            logger.system_log('LOSE01011', self.trace_id, 'C_MOVEMENT_CLASS_MNG', self.response_id, self.execution_order)
            logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, ret))
            return ret

        # ary_movement_list
        #     movement_id:{'ORCHESTRATOR_ID':x,'MovementIDName':movement_id:MovementName}
        # SymphonyClassに紐づくMovement待避
        for row in row_data_000311:
            ary_movement_list[row[Cstobj.CMCM_PATTERN_ID]] = {'ORCHESTRATOR_ID':row[Cstobj.CMCM_ORCHESTRATOR_ID],'MovementIDName':''}

        # Movement一覧からMovement取得取得
        logger.system_log('LOSI01000', 'C_PATTERN_PER_ORCH select', self.trace_id)

        ret = self.select_c_pattern_per_orch(ary_movement_list)
        if ret > 0:
            logger.system_log('LOSE01011', self.trace_id, 'C_PATTERN_PER_ORCH', self.response_id, self.execution_order)
            logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, ret))
            return ret

        # 機器一覧からアクション先サーバのPkey取得
        logger.system_log('LOSI01000', 'C_STM_LIST select', self.trace_id)

        ret = self.select_c_stm_list(ary_ita_config, ary_action_server_list, ary_action_server_id_name)
        if ret > 0:
            logger.system_log('LOSE01011', self.trace_id, 'C_STM_LIST', self.response_id, self.execution_order)
            logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, ret))
            return ret

        logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, '0'))
        return 0


    def select_ope_ita_master(self, ary_ita_config, operation_id):
        """
        登録されてるオペレーションID検索
        """
        logger.logic_log(
            'LOSI00001', 'trace_id: %s, ary_ita_config: %s, operation_id: %s' %
            (self.trace_id, ary_ita_config, operation_id))

        logger.system_log('LOSI01000', 'C_OPERATION_LIST select', self.trace_id)

        row_data_000304 = []
        ret = self.select_c_operation_list(ary_ita_config, operation_id, row_data_000304)
        if ret > 0:
            logger.system_log('LOSE01011', self.trace_id, 'C_PATTERN_PER_ORCH', self.response_id, self.execution_order)
            logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, ret))
            return ret

        logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, '0'))
        return 0

    def symphony_execute(self, ary_ita_config, operation_id):
        """
        [概要]
        Symphony実行メゾット
        """
        # Symphony実行
        logger.logic_log('LOSI00001', 'trace_id: %s, ary_ita_config: %s, operation_id: %s' %
                         (self.trace_id, ary_ita_config, operation_id))
        logger.system_log('LOSI01000', 'Symphony Execute', self.trace_id)

        target_table = 'SYMPHONY'
        ary_ita_config['menuID'] = '2100000308'
        self.restobj.rest_set_config(ary_ita_config)
        ary_result = {}
        list_symphony_instance_id = []
        symphony_instance_id = 0
        symphony_url = ''

        ret = self.restobj.rest_symphony_execute(
            self.symphony_class_no,
            operation_id,
            list_symphony_instance_id,
            ary_result,
            self.response_id,
            self.execution_order)
        if not ret:
            logger.system_log('LOSE01023', self.trace_id, target_table, self.response_id, self.execution_order, self.symphony_class_no)
            logger.system_log('LOSE01000', self.trace_id, target_table, 'Insert', ary_result['status'])
            logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, Cstobj.RET_REST_ERROR))
            return Cstobj.RET_REST_ERROR, symphony_instance_id, symphony_url

        # Symphony instance_idと作業確認URL更新
        symphony_instance_id = list_symphony_instance_id[0]
        symphony_url = "{}://{}:{}/default/menu/01_browse.php?no=2100000309&symphony_instance_id={}".format(ary_ita_config['Protocol'], ary_ita_config['Host'],ary_ita_config['PortNo'],list_symphony_instance_id[0])

        logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'True'))
        return 0, symphony_instance_id, symphony_url

    def get_last_info(self, ary_config, symphony_instance_no, operation_id):
        """
        [概要]
        実行結果取得メゾット
        """
        logger.logic_log(
            'LOSI00001', 'trace_id: %s,ary_config: %s, symphony_instance_no: %s, operation_id: %s' %
            (self.trace_id, ary_config, symphony_instance_no, operation_id))

        ary_config['menuID'] = '2100000309'
        status_id = -1
        self.restobj.rest_set_config(ary_config)
        ary_result = {}
        insert_row_data = {"SYMPHONY_INSTANCE_ID": symphony_instance_no}

        result = self.restobj.rest_info(
            insert_row_data,
            operation_id,
            ary_result
        )
        if not result:
            logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, status_id))
            return status_id

        try:
            status_id = int(ary_result['response']['resultdata']['SYMPHONY_INSTANCE_INFO']['STATUS_ID'])
        except KeyError as e:
            logger.system_log('LOSE01024', self.trace_id)
            logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, status_id))
            return status_id

        logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, status_id))
        return status_id

    def insert_ita_master(self, configs, movements, action_server_id_names, operation_ids):

        logger.logic_log(
            'LOSI00001',
            'trace_id:%s, configs:%s, movements:%s, action_server_id_names:%s, operation_ids:%s' %
            (self.trace_id, configs, movements, action_server_id_names, operation_ids))
        # オペレーションID登録
        logger.system_log('LOSI01000', 'C_OPERATION_LIST insert', self.trace_id)

        row_data_000304 = [0] * Cstobj.TBL_COL_MAX
        row_data_000304[Cstobj.COL_FUNCTION_NAME] = '登録'
        row_data_000304[Cstobj.COL_OPERATION_NAME] = '%s%s' % (self.trace_id, self.execution_order)
        row_data_000304[Cstobj.COL_OPERATION_DATE] = datetime.datetime.now(pytz.timezone('UTC')).strftime("%Y/%m/%d")

        operation_name = '%s%s' % (self.trace_id, self.execution_order)

        self.restobj.rest_set_config(configs)
        ret = self._insert_c_operation_list(row_data_000304)
        if ret > 0:
            logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, ret))
            return ret

        # 登録したオペレーションID取得
        logger.system_log('LOSI01000', 'C_OPERATION_LIST select', self.trace_id)

        row_data_000304 = []
        ret = self._select_c_operation_list_by_operation_name(operation_name, row_data_000304)
        if ret > 0:
            logger.system_log('LOSE01011', self.trace_id, 'C_PATTERN_PER_ORCH', self.response_id, self.execution_order)
            logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, ret))
            return ret

        operation_id_name = row_data_000304[0][Cstobj.COL_OPERATION_NO_IDBH] + \
            ":" + row_data_000304[0][Cstobj.COL_OPERATION_NAME]

        # オペレーションID(4桁)
        operation_ids.append(row_data_000304[0][Cstobj.COL_OPERATION_NO_IDBH])
        # 採番したオペレーションIDでアクション先サーバ分の作業対象ホスト登録
        for movement_id, Items in movements.items():
            if movements[movement_id]['ORCHESTRATOR_ID'] == '3':
                self.restobj.menu_id = '2100020108'
                target_table = 'B_ANSIBLE_LNS_PHO_LINK'
            elif movements[movement_id]['ORCHESTRATOR_ID'] == '4':
                self.restobj.menu_id = '2100020209'
                target_table = 'B_ANSIBLE_PNS_PHO_LINK'
            else:
                self.restobj.menu_id = '2100020310'
                target_table = 'B_ANSIBLE_LRL_PHO_LINK'

            movement_id_name = movements[movement_id]['MovementIDName']
            # {HOST_NAME: SYSTEM_ID:HOST?NAME
            row_data_bapl = []
            for server_name in action_server_id_names:
                del row_data_bapl
                server_id_name = action_server_id_names[server_name]

                row_data_bapl = [0] * Cstobj.BAPL_LAST_UPDATE_USER
                row_data_bapl[Cstobj.COL_FUNCTION_NAME] = '登録'
                row_data_bapl[Cstobj.BAPL_OPERATION_NO_UAPK] = operation_id_name
                row_data_bapl[Cstobj.BAPL_PATTERN_ID] = movement_id_name
                row_data_bapl[Cstobj.BAPL_SYSTEM_ID] = server_id_name

                logger.system_log('LOSI01000', self.trace_id, target_table + ' insert', self.trace_id)
                ret = self._insert_b_ansible_pho_link(target_table, row_data_bapl)
                if ret > 0:
                    logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, ret))
                    return ret

        logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'True'))
        return True


    def insert_operation(self, configs):
        """
        [概要]
          オペレーション登録メゾット
        """
        logger.logic_log('LOSI00001', 'trace_id: %s' % self.trace_id)

        operation_name = '%s%s' % (self.trace_id, self.execution_order)
        operation_data = {}
        operation_data[Cstobj.COL_FUNCTION_NAME] = '登録'
        operation_data[Cstobj.COL_OPERATION_NAME] = operation_name
        operation_data[Cstobj.COL_OPERATION_DATE] = datetime.datetime.now(pytz.timezone('UTC')).strftime("%Y/%m/%d")

        self.restobj.rest_set_config(configs)
        ret = self._insert_c_operation_list(operation_data)
        if ret > 0:
            logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, ret))
            return ret, operation_name

        logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'True'))
        return True, operation_name


    def select_operation(self, configs, operation_name, log_flg=True):
        """
        [概要]
          オペレーション検索メゾット
        """
        logger.logic_log('LOSI00001', 'trace_id: %s' % self.trace_id)

        operation_data = []
        ret = self._select_c_operation_list_by_operation_name(operation_name, operation_data, log_flg)
        if ret > 0:
            logger.system_log('LOSE01011', self.trace_id, 'C_PATTERN_PER_ORCH', self.response_id, self.execution_order)
            logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, ret))
            return ret, operation_data

        logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'True'))
        return True, operation_data


    def _insert_c_operation_list(self, insert_row_data):
        """
        [概要]
          投入オペレーション一覧登録メゾット
        """
        logger.logic_log('LOSI00001', 'trace_id: %s' % self.trace_id)
        self.restobj.menu_id = '2100000304'
        ary_result = {}
        ret = self.restobj.rest_insert(insert_row_data, ary_result)
        if not ret:
            target_table = 'C_OPERATION_LIST'
            logger.system_log('LOSE01021', self.trace_id, target_table, self.response_id, self.execution_order)
            logger.system_log('LOSE01000', self.trace_id, target_table, 'Insert', ary_result['status'])
            ActionDriverCommonModules.SaveActionLog(self.response_id, self.execution_order, self.trace_id, 'MOSJA01025')
            return Cstobj.RET_REST_ERROR
        logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'True'))
        return 0

    def insert_c_parameter_sheet(self, host_name, operation_id, operation_name, exec_schedule_date, parameter_list):
        """
        [概要]
        パラメーターシート登録メソッド
        """
        logger.logic_log('LOSI00001', 'trace_id: %s' % self.trace_id)
        # TODO 紐づけテーブルができたらそれを参照するよう修正する
        self.restobj.menu_id = '0000000001'
        row_data_000001 = {}
        row_data_000001[Cstobj.COL_FUNCTION_NAME] = '登録'
        row_data_000001[Cstobj.COL_HOSTNAME] = host_name
        row_data_000001[Cstobj.COL_OPERATION_ID] = operation_id
        row_data_000001[Cstobj.COL_OPERATION_NAME_PARAM] = operation_name
        row_data_000001[Cstobj.COL_SCHEDULE_TIMESTAMP_ID_NAME] = exec_schedule_date
        # TODO 将来的にはfor文で回して設定する予定
        row_data_000001[Cstobj.COL_PARAMETER] = parameter_list[0]

        ary_result = {}
        ret = self.restobj.rest_insert(row_data_000001, ary_result)
        if not ret:
            target_table = 'C_PARAMETER_SHEET'
            logger.system_log('LOSE01021', self.trace_id,
                              target_table, self.response_id, self.execution_order)
            logger.system_log('LOSE01000', self.trace_id,
                              target_table, 'Insert', ary_result['status'])
            ActionDriverCommonModules.SaveActionLog(
                self.response_id, self.execution_order, self.trace_id, 'MOSJA01066')
            return Cstobj.RET_REST_ERROR
        logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' %
                         (self.trace_id, 'True'))
        return 0

    def _insert_b_ansible_pho_link(self, target_table, insert_row_data):
        """
        [概要]
          作業対象ホスト登録メゾット
        """
        logger.logic_log('LOSI00001', 'trace_id: %s, target_table: %s' % (self.trace_id, target_table))
        ary_result = {}
        ret = self.restobj.rest_insert(insert_row_data, ary_result)
        if not ret:
            logger.system_log('LOSE01021', self.trace_id, target_table, self.response_id, self.execution_order)
            logger.system_log('LOSE01000', self.trace_id, target_table, 'Insert', ary_result['status'])
            ActionDriverCommonModules.SaveActionLog(self.response_id, self.execution_order, self.trace_id, 'MOSJA01027')
            return Cstobj.RET_REST_ERROR
        logger.logic_log('LOSI00002', 'trace_id: %s, return: 0' % self.trace_id)
        return 0

    def select_c_stm_list(self, configs, action_servers, action_server_id_names):
        """
        [概要]
          機器一覧検索メゾット
        """
        logger.logic_log(
            'LOSI00001', 'trace_id: %s, configs: %s, action_servers: %s, action_server_id_names: %s' %
            (self.trace_id, configs, action_servers, action_server_id_names))
        target_table = 'C_STM_LIST'
        configs['menuID'] = '2100000303'
        self.restobj.rest_set_config(configs)
        for server_name in action_servers:
            aryfilter = {Cstobj.COL_DISUSE_FLAG: {'NORMAL': '0'},
                         Cstobj.CSL_HOSTNAME: {'LIST': {0: server_name}}}
            ary_result = {}
            ret = self.restobj.rest_select(aryfilter, ary_result)
            if ret:
                row_count = self.restobj.rest_get_row_count(ary_result)
                if row_count < 1:
                    # 機器一覧に未登録
                    logger.system_log('LOSE01020', self.trace_id, target_table,
                                      self.response_id, self.execution_order, server_name)
                    ActionDriverCommonModules.SaveActionLog(
                        self.response_id, self.execution_order, self.trace_id, 'MOSJA01022')
                    return Cstobj.RET_DATA_ERROR
                row_data = self.restobj.rest_get_row_data(ary_result)
                # ホスト名とPkeyの対応表作成
                action_server_id_names[server_name] = row_data[0][Cstobj.CSL_SYSTEM_ID] + ':' + server_name
            else:
                logger.system_log('LOSE01000', self.trace_id, target_table, 'Filter', ary_result['status'])
                ActionDriverCommonModules.SaveActionLog(
                    self.response_id, self.execution_order, self.trace_id, 'MOSJA01021')
                return Cstobj.RET_REST_ERROR

        logger.logic_log('LOSI00002', 'trace_id: %s, return: 0' % (self.trace_id))
        return 0

    def select_substitution_value_mng(self, config, operation_name, menu_id, target_table):
        """
        [概要]
          代入値管理検索メゾット
        """
        logger.logic_log('LOSI00001', 'trace_id: %s, operation_name: %s, menu_id: %s, target_table: %s' % (self.trace_id, operation_name, menu_id, target_table))
        aryfilter = {Cstobj.COL_DISUSE_FLAG: {'NORMAL': '0'},
                        3:{'NORMAL':operation_name}
        }

        config['menuID'] = menu_id
        self.restobj.rest_set_config(config)

        ary_result = {}
        ret = self.restobj.rest_select(aryfilter,ary_result)
        if ret:
            row_count  = self.restobj.rest_get_row_count(ary_result)
            logger.logic_log('LOSI00002', 'trace_id: %s, return: %s' % (self.trace_id, 'True'))
            return row_count
        else:
            logger.system_log('LOSE01025', self.trace_id, self.restobj.menu_id, 'Filter', ary_result['status'])
            ActionDriverCommonModules.SaveActionLog(self.response_id, self.execution_order, self.trace_id, 'MOSJA01065')
            return None
