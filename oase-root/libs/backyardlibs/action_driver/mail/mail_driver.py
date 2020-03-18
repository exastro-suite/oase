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
  アクションドライバ アクション実行処理（メール）


"""

from libs.backyardlibs.action_driver.common.action_abstract import AbstractManager
from collections import defaultdict
from libs.webcommonlibs.oase_exception import OASEError
from libs.backyardlibs.action_driver.mail.mail_core import Mail1Core
from libs.backyardlibs.oase_action_common_libs import TimeConversion
from libs.backyardlibs.oase_action_common_libs import ActionDriverCommonModules
from libs.commonlibs.define import *
from libs.commonlibs.common import Common
from libs.commonlibs.aes_cipher import AESCipher
from web_app.models.models import DriverType
from web_app.models.models import PreActionHistory
from web_app.models.models import ActionType
from web_app.models.models import DataObject
from web_app.models.models import RuleType
from web_app.models.models import EventsRequest
from web_app.models.models import System
from web_app.models.models import MailTemplate
from web_app.models.mail_models import MailDriver
from web_app.models.mail_models import MailActionHistory
from web_app.models.models import ActionHistory
from web_app.models.models import RhdmResponseAction
from web_app.models.models import RhdmResponse
from libs.commonlibs.oase_logger import OaseLogger
from django.db.models import Q
from django.db import transaction
from django.urls import reverse
from django.conf import settings
import os
import sys
import json
import datetime
import django
import traceback
from collections import OrderedDict
import abc

# OASE モジュール importパス追加
my_path = os.path.dirname(os.path.abspath(__file__))
tmp_path = my_path.split('oase-root')
root_dir_path = tmp_path[0] + 'oase-root'
sys.path.append(root_dir_path)

# OASE モジュール import
# #LOCAL_PATCH#
os.environ['DJANGO_SETTINGS_MODULE'] = 'confs.frameworkconfs.settings'
django.setup()


# ロガー初期化
logger = OaseLogger.get_instance()


Comobj = ActionDriverCommonModules()


class mailManager(AbstractManager):
    """
    [クラス概要]
        アクションドライバメイン処理クラス
    """

    ACTIONPARAM_KEYS = [
        'MAIL_NAME',
        'MAIL_TEMPLATE',
        'MAIL_TO',
        'MAIL_CC',
        'MAIL_BCC',
    ]

    ACTIONPARAM_KEYS_REQUIRE = [
        'MAIL_NAME',
    ]

    ACTIONPARAM_KEYS_REQUIRE_NOTPRE = [
        'MAIL_TEMPLATE',
    ]

    def __init__(self, trace_id, response_id, last_update_user):
        self.trace_id = trace_id
        self.response_id = response_id
        self.action_history = None
        self.mail_template = None
        self.mail_driver = None
        self.aryActionParameter = {}
        self.last_update_user = last_update_user
        self.core = Mail1Core(trace_id)

    def mail_action_history_insert(self, mail_address, mail_template_name, exe_order, action_history_id):
        """
        [概要]
          Mailアクション履歴登録メゾット
        """
        logger.logic_log(
            'LOSI00001', 'mail_address: % s, mail_template_name: % s, exe_order: % s, action_history_id: % s' % (
                mail_address, mail_template_name, exe_order, action_history_id))

        try:
            with transaction.atomic():
                MailActionHistory(
                    action_his_id=action_history_id,
                    mail_address=mail_address,
                    mail_template_name=mail_template_name,
                    last_update_timestamp=Comobj.getStringNowDateTime(),
                    last_update_user=self.last_update_user,
                ).save(force_insert=True)

        except Exception as e:
            logger.system_log('LOSE01100', self.trace_id,
                              traceback.format_exc())
            ActionDriverCommonModules.SaveActionLog(
                self.response_id, exe_order, self.trace_id, 'MOSJA01037')

        logger.logic_log('LOSI00002', 'None')

    def reset_variables(self):
        """
        [概要]
          メンバ変数を初期化する 
        """
        self.mail_driver = None
        self.mail_template = None
        self.aryActionParameter = {}

    def set_information(self, rhdm_res_act, action_history):
        """
        [概要]
          メール情報登録
        """
        logger.logic_log('LOSI00001', 'action_type_id: %s' %
                         (rhdm_res_act.action_type_id))

        self.action_history = action_history

        try:
            # アクションパラメータ解析
            param_info = json.loads(rhdm_res_act.action_parameter_info)
            self.set_action_parameters(
                param_info, rhdm_res_act.execution_order, rhdm_res_act.response_detail_id)
            self.set_driver(rhdm_res_act.execution_order)
            self.set_mailtemplate(rhdm_res_act.execution_order)

        except OASEError as e:
            if e.log_id:
                if e.arg_list and isinstance(e.arg_list, list):
                    logger.system_log(e.log_id, *(e.arg_list))
                else:
                    logger.system_log(e.log_id)

            if e.arg_dict and isinstance(e.arg_dict, dict) \
                    and 'sts' in e.arg_dict and 'detail' in e.arg_dict:
                return e.arg_dict['sts'], e.arg_dict['detail']

        except Exception as e:
            logger.system_log(*e.args)
            return ACTION_DATA_ERROR, 0

        logger.logic_log('LOSI00002', 'return: True')
        return 0, 0

    def set_driver(self, exe_order):
        """Mailドライバーmodelをセット"""
        disp_name = self.aryActionParameter['MAIL_NAME']
        try:
            self.mail_driver = MailDriver.objects.get(mail_disp_name=disp_name)
        except MailDriver.DoesNotExist:
            ActionDriverCommonModules.SaveActionLog(
                self.response_id, exe_order, self.trace_id, 'MOSJA01014')
            raise OASEError('', 'LOSE01115',
                            log_params=['OASE_T_MAIL_DRIVER', 'MAIL_DISP_NAME',
                                        self.trace_id], msg_params={
                                        'sts': ACTION_DATA_ERROR,
                                        'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_VAL})

    def set_mailtemplate(self, exe_order, pre_flag=False):
        """Mailテンプレートをセット"""
        template_name = self.aryActionParameter['MAIL_TEMPLATE']

        # 事前メールの場合はテンプレート名が無くてもよい
        if pre_flag and not template_name:
            return

        try:
            self.mail_template = MailTemplate.objects.get(
                mail_template_name=template_name)

        except MailTemplate.DoesNotExist:
            ActionDriverCommonModules.SaveActionLog(
                self.response_id, exe_order, self.trace_id, 'MOSJA01015')
            raise OASEError('', 'LOSE01115',
                            log_params=['OASE_T_MAIL_TEMPLATE',
                                        'MAIL_DISP_NAME', self.trace_id],
                            msg_params={'sts': ACTION_DATA_ERROR,
                                        'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_VAL})

    def set_action_parameters(self, param_list, exe_order, response_detail_id, pre_flg=False):
        """
        [概要]
          Mailパラメータ解析
        """
        logger.logic_log('LOSI00001', 'param_list: %s' % (param_list))
        ActionDriverCommonModules.SaveActionLog(
            self.response_id, exe_order, self.trace_id, 'MOSJA01004')

        key1 = 'ACTION_PARAMETER_INFO'
        if key1 not in param_list:
            ActionDriverCommonModules.SaveActionLog(
                self.response_id, exe_order, self.trace_id, 'MOSJA01005')
            raise OASEError('', 'LOSE01114',
                            log_params=[self.trace_id, 'OASE_T_RHDM_RESPONSE_ACTION',
                                        response_detail_id, key1],
                            msg_params={
                                'sts': ACTION_DATA_ERROR,
                                'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_KEY})

        # mailアクションパラメーター サーチ
        check_info = self.analysis_parameters(param_list[key1])
        for key, val in check_info.items():
            if val is None:
                ActionDriverCommonModules.SaveActionLog(
                    self.response_id, exe_order, self.trace_id, 'MOSJA01006', **{'key': key})
                raise OASEError('', 'LOSE01114',
                                log_params=[self.trace_id, 'OASE_T_RHDM_RESPONSE_ACTION',
                                            response_detail_id, key],
                                msg_params={
                                    'sts': ACTION_DATA_ERROR,
                                    'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_KEY})

            if (val == '' and key in self.ACTIONPARAM_KEYS_REQUIRE_NOTPRE and pre_flg == False) \
                    or (val == '' and key in self.ACTIONPARAM_KEYS_REQUIRE):
                ActionDriverCommonModules.SaveActionLog(
                    self.response_id, exe_order, self.trace_id, 'MOSJA01006', **{'key': key})
                raise OASEError('', 'LOSE01114',
                                log_params=[self.trace_id, 'OASE_T_RHDM_RESPONSE_ACTION',
                                            response_detail_id, key],
                                msg_params={
                                    'sts': ACTION_DATA_ERROR,
                                    'detail': ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_VAL})

            self.aryActionParameter[key] = val

        MailToAddres = []
        MailToAddres.append("Decision Table")
        MailToAddres.append(self.aryActionParameter['MAIL_TO'])
        MailToAddres.append(self.aryActionParameter['MAIL_CC'])
        MailToAddres.append(self.aryActionParameter['MAIL_BCC'])

        self.aryActionParameter['MAIL_TO_ADDRES'] = json.dumps(
            MailToAddres, ensure_ascii=False)

    @classmethod
    def analysis_parameters(cls, param_list):

        check_info = {}
        for key in cls.ACTIONPARAM_KEYS:
            check_info[key] = None

        for string in param_list:
            for key in cls.ACTIONPARAM_KEYS:
                ret = Comobj.KeyValueStringFind(key, string)
                if ret is not None:
                    check_info[key] = ret

        return check_info

    def act(self, rhdm_res_act, retry=False, pre_flag=False):
        """
        [概要]
            メール送信アクションを実行
        """
        logger.logic_log('LOSI00001', 'self.trace_id: %s, aryActionParameter: %s' % (
            self.trace_id, self.aryActionParameter))
        # 宛先
        MAIL_TO, mail_to = self._get_mail_to()

        # CC
        MAIL_CC, mail_cc = self._get_mail_cc()

        # BCC
        MAIL_BCC, mail_bcc = self._get_mail_bcc()

        # 宛先、Cc、Bcc確認
        if len(MAIL_TO) == 0 and \
                len(MAIL_CC) == 0 and \
                len(MAIL_BCC) == 0:

            # 空の場合
            errkey = "MAIL_TO/MAIL_CC/MAIL_BCC"
            logger.system_log('LOSE01111', 'OASE_T_RHDM_RESPONSE_ACTION',
                              rhdm_res_act.response_detail_id, errkey, self.trace_id)
            ActionDriverCommonModules.SaveActionLog(
                self.response_id, rhdm_res_act.execution_order, self.trace_id, 'MOSJA01033')
            return ACTION_DATA_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.DATAERR_PARAM_VAL

        MailToAddres = {}
        MailToAddres = json.loads(
            self.aryActionParameter['MAIL_TO_ADDRES'], object_pairs_hook=OrderedDict)
        MailToAddres.append("Template")
        MailToAddres.append(mail_to)
        MailToAddres.append(mail_cc)
        MailToAddres.append(mail_bcc)

        self.aryActionParameter['MAIL_TO_ADDRES'] = json.dumps(
            MailToAddres, ensure_ascii=False)

        # パスワードを復号
        cipher = AESCipher(settings.AES_KEY)
        if self.mail_driver.password is not None and self.mail_driver.password != '':
            password = cipher.decrypt(self.mail_driver.password)
        else:
            password = self.mail_driver.password

        # 件名と本文を取得
        mail_subject = ''
        mail_content = ''
        if self.mail_template:
            mail_subject = self.mail_template.subject
            mail_content = self.mail_template.content

        # テンプレート指定なし、および、事前アクションメールの場合は、デフォルトの件名と本文を取得
        elif pre_flag:
            # アクションタイプ取得処理
            act_type = self._get_action_type()

            mail_add_info = {}
            act_his_url = reverse('web_app:rule:action_history')
            act_his_url = '%s%s' % (settings.HOST_NAME, act_his_url)

            mail_add_info['act_his_url'] = act_his_url
            mail_add_info['trace_id'] = self.trace_id

            # イベント情報取得
            er = EventsRequest.objects.get(trace_id=self.trace_id)
            event_info = MailContentCreater()
            mail_add_info['event_info'] = event_info._transform_event_info(
                er.event_info, er.rule_type_id)
            mail_add_info['event_to_time'] = TimeConversion.get_time_conversion(
                er.event_to_time, 'Asia/Tokyo')

            # アクション情報取得
            mail_add_info = self._get_action_parameter(mail_add_info, act_type)

            # 承認待ちアクション通知件名、本文取得処理
            mail_subject, mail_content = self._get_mail_subject_content(
                mail_subject, mail_content, mail_add_info)

        logger.logic_log('LOSI01107', self.mail_driver.smtp_server,
                        self.mail_driver.protocol, self.mail_driver.port, mail_subject,
                        mail_content, self.mail_driver.user, password, MAIL_TO, MAIL_CC,
                        MAIL_BCC, self.trace_id)

        # メール本文作成処理
        content = self._create_mail_content(mail_content)

        # メール送信
        mm = MailContentCreater()
        content = mm.replace_tags(content, self.trace_id)
        mailsend_ret = self.core.send(self.mail_driver.smtp_server,
                                    self.mail_driver.protocol, self.mail_driver.port,
                                    mail_subject, content, self.mail_driver.user, password,
                                    MAIL_TO, MAIL_CC, MAIL_BCC, 'utf-8')

        # メール送信結果判定
        status = PROCESSED if mailsend_ret else ACTION_EXEC_ERROR

        logger.logic_log('LOSI01108', status, str(
            rhdm_res_act.execution_order), self.trace_id)

        if not pre_flag and not retry:
            # メールアクション履歴登録
            logger.logic_log('LOSI01109', str(
                rhdm_res_act.execution_order), self.trace_id)
            self.mail_action_history_insert(
                self.aryActionParameter['MAIL_TO_ADDRES'],
                self.aryActionParameter['MAIL_TEMPLATE'],
                rhdm_res_act.execution_order,
                self.action_history.pk,
            )

        # メール送信に失敗した場合は異常終了する。
        if status != PROCESSED:
            logger.system_log('LOSE01112', status, self.trace_id)
            ActionDriverCommonModules.SaveActionLog(self.response_id,
                                                    rhdm_res_act.execution_order, self.trace_id, 'MOSJA01034'
                                                    )
            return ACTION_EXEC_ERROR, ACTION_HISTORY_STATUS.DETAIL_STS.EXECERR_SEND_FAIL

        logger.logic_log('LOSI00002', 'return: PROCESSED')
        return PROCESSED, ACTION_HISTORY_STATUS.DETAIL_STS.NONE

    def _get_mail_to(self):
        """
        [概要]
            メール宛先取得処理
        """
        # 宛先
        if self.mail_template and self.mail_template.destination:
            if self.aryActionParameter['MAIL_TO']:
                if (self.mail_template.destination[-1:] == ';'):
                    MAIL_TO = self.mail_template.destination + \
                        self.aryActionParameter['MAIL_TO']
                    mail_to = "MAIL_TO=" + str(self.mail_template.destination)
                else:
                    MAIL_TO = self.mail_template.destination + \
                        ';' + self.aryActionParameter['MAIL_TO']
                    mail_to = "MAIL_TO=" + str(self.mail_template.destination)
            else:
                MAIL_TO = self.mail_template.destination
                mail_to = "MAIL_TO=" + str(self.mail_template.destination)
        elif self.aryActionParameter['MAIL_TO']:
            MAIL_TO = self.aryActionParameter['MAIL_TO']
            mail_to = "MAIL_TO="
        else:
            MAIL_TO = ""
            mail_to = "MAIL_TO="

        return MAIL_TO, mail_to

    def _get_mail_cc(self):
        """
        [概要]
            メールCC取得処理
        """
        if self.mail_template and self.mail_template.cc:
            if self.aryActionParameter['MAIL_CC']:
                if (self.mail_template.cc[-1:] == ';'):
                    MAIL_CC = self.mail_template.cc + \
                        self.aryActionParameter['MAIL_CC']
                    mail_cc = "MAIL_CC=" + str(self.mail_template.cc)
                else:
                    MAIL_CC = self.mail_template.cc + ';' + \
                        self.aryActionParameter['MAIL_CC']
                    mail_cc = "MAIL_CC=" + str(self.mail_template.cc)
            else:
                MAIL_CC = self.mail_template.cc
                mail_cc = "MAIL_CC=" + str(self.mail_template.cc)
        elif self.aryActionParameter['MAIL_CC']:
            MAIL_CC = self.aryActionParameter['MAIL_CC']
            mail_cc = "MAIL_CC="
        else:
            MAIL_CC = ""
            mail_cc = "MAIL_CC="

        return MAIL_CC, mail_cc

    def _get_mail_bcc(self):
        """
        [概要]
            メールBCC取得処理
        """
        if self.mail_template and self.mail_template.bcc:
            if self.aryActionParameter['MAIL_BCC']:
                if (self.mail_template.bcc[-1:] == ';'):
                    MAIL_BCC = self.mail_template.bcc + \
                        self.aryActionParameter['MAIL_BCC']
                    mail_bcc = "MAIL_BCC=" + str(self.mail_template.bcc)
                else:
                    MAIL_BCC = self.mail_template.bcc + ';' + \
                        self.aryActionParameter['MAIL_BCC']
                    mail_bcc = "MAIL_BCC=" + str(self.mail_template.bcc)
            else:
                MAIL_BCC = self.mail_template.bcc
                mail_bcc = "MAIL_BCC=" + str(self.mail_template.bcc)
        elif self.aryActionParameter['MAIL_BCC']:
            MAIL_BCC = self.aryActionParameter['MAIL_BCC']
            mail_bcc = "MAIL_BCC="
        else:
            MAIL_BCC = ""
            mail_bcc = "MAIL_BCC="

        return MAIL_BCC, mail_bcc

    def _get_action_parameter(self, mail_add_info, act_type):
        """
        [概要]
            アクション情報取得処理
        """
        mail_add_info['rule_type'] = self.action_history.rule_type_name if self.action_history else ''
        mail_add_info['rule_name'] = self.action_history.rule_name if self.action_history else ''
        mail_add_info['act_type'] = act_type
        mail_add_info['timestamp'] = ''
        if self.action_history and self.action_history.action_start_time:
            if isinstance(self.action_history.action_start_time, str):
                mail_add_info['timestamp'] = TimeConversion.get_time_conversion(datetime.datetime.strptime(
                    self.action_history.action_start_time, '%Y-%m-%d %H:%M:%S.%f'), 'Asia/Tokyo')

            else:
                mail_add_info['timestamp'] = TimeConversion.get_time_conversion(
                    self.action_history.action_start_time, 'Asia/Tokyo')

        return mail_add_info

    def _get_mail_subject_content(self, mail_subject, mail_content, mail_add_info):
        """
        [概要]
            承認待ちアクション通知件名、本文取得処理
        """
        rset = System.objects.filter(config_id__in=[
                                     'PREACTION_MAIL_SUBJECT', 'PREACTION_MAIL_CONTENT']).values('config_id', 'value')
        for r in rset:
            if r['config_id'] == 'PREACTION_MAIL_SUBJECT':
                mail_subject = r['value']

            elif r['config_id'] == 'PREACTION_MAIL_CONTENT':
                mail_content = (r['value'] % mail_add_info)

        return mail_subject, mail_content

    def _create_mail_content(self, mail_content):
        """
        [概要]
            メール本文作成処理
        """
        rset = list(System.objects.filter(config_id__in=[
                    'MAIL_HEADER_JP', 'MAIL_SIGNATURE_JP']).order_by('item_id').values('config_id', 'value'))
        for r in rset:
            if r['config_id'] == 'MAIL_HEADER_JP':
                header = r['value']
            if r['config_id'] == 'MAIL_SIGNATURE_JP':
                # URL整形
                login_url = reverse('web_app:top:login')
                inquiry_url = reverse('web_app:top:inquiry')
                login_url = '%s%s' % (settings.HOST_NAME, login_url)
                inquiry_url = '%s%s' % (settings.HOST_NAME, inquiry_url)
                signature = r['value'] % (inquiry_url, login_url)

        return str(header) + '\n' + mail_content + '\n\n' + str(signature)

    def _get_action_type(self):
        """
        [概要]
            アクションタイプ取得処理
        """
        act_type = ''
        if self.action_history:
            rset = list(ActionType.objects.filter(
                action_type_id=self.action_history.action_type_id).values_list('driver_type_id', flat=True))
            if len(rset) > 0:
                dri_type = DriverType.objects.get(driver_type_id=rset[0])
                act_type = dri_type.name + \
                    '(ver' + str(dri_type.driver_major_version) + ')'

        return act_type

    def retry(self, rhdm_res_act, retry=True):
        """再実行"""
        status, detail = self.act(rhdm_res_act, retry=retry)
        return status, detail

    @classmethod
    def has_action_master(cls):
        """
        [概要]
          アクションマスタの登録確認
        """

        if MailDriver.objects.all().count():
            return True

        return False


class MailContentCreater:
    """
    [クラス概要]
        メールアクション管理クラス
        replace_tags()を実行してタグを置き換える
    """

    def __init__(self):
        """
        デリミターとパラメータからタグを定義する。
        """
        # todo クラス内部に持つか、DB,settings.pyに持つか
        left_delimiter = "["
        right_delimiter = "]"
        param_list = ["EVENT_INFO", "ACTION_INFO"]
        self.tag_list = [left_delimiter + p +
                         right_delimiter for p in param_list]

    def replace_tags(self, content, trace_id):
        """
        本文をタグで置き換える
        
        [引数]
        content : str 文章
        trace_id : str トレースid
        
        [戻り値]
        タグを置き換えた文章
        """
        logger.logic_log('LOSI00001', 'content: %s, trace_id: %s' %
                         (content, trace_id))

        content = self._replace_events_info(
            content, trace_id, self.tag_list[0])
        content = self._replace_action_info(
            content, trace_id, self.tag_list[1])

        logger.logic_log('LOSI00002', 'content: %s')
        return content

    def _replace_events_info(self, content, trace_id, tag):
        """
        EVENT_INFOタグを置き換えるための、リクエスト情報を取得する

        [引数]
        trace_id : トレースid

        [戻り値]
        events_request : str リクエスト情報
        """
        logger.logic_log('LOSI00001', 'content: %s, trace_id: %s, tag: %s' % (
            content, trace_id, tag))

        er = EventsRequest.objects.get(trace_id=trace_id)
        event_info = self._transform_event_info(er.event_info, er.rule_type_id)
        event_to_time = TimeConversion.get_time_conversion(
            er.event_to_time, 'Asia/Tokyo')
        rule_type_name = RuleType.objects.get(
            pk=er.rule_type_id).rule_type_name
        info = """
[リクエスト情報]
トレースID：{}
ルール種別名：{}
リクエストユーザ：{}
リクエストサーバ：{}

[イベント情報]
イベント発生日時：{}
{}
""".format(er.trace_id, rule_type_name, er.request_user,
            er.request_server, event_to_time, event_info)

        content = content.replace(tag, info)
        logger.logic_log('LOSI00002', 'content: %s' % (content))

        return content

    def _transform_event_info(self, event_info, rule_type_id):
        """
        [概要]
        送られたイベント情報と条件名がわかるように文字列を生成する。
        以下のような文字列を生成する

        [引数]
        event_info : str DBに保存されているevent_info
        rule_type_id : int ルール種別id

        [戻り値]
        event_info : str イベント情報
        """
        logger.logic_log('LOSI00001', 'event_info: %s, rule_type_id: %s' % (
            event_info, rule_type_id))

        event_info_dict = json.loads(event_info)
        event_info_list = event_info_dict['EVENT_INFO']
        data_obj_list = DataObject.objects.filter(
            rule_type_id=rule_type_id).order_by('data_object_id')

        if not len(data_obj_list):
            logger.system_log('LOSE01122', 'rule_type_id: %s' % rule_type_id)
            return '\n'

        index = 0
        conditional_name_set = set()
        result = "条件名 = 値 :\n"
        for d in data_obj_list:
            cond_id = d.conditional_expression_id
            cond_name = d.conditional_name

            # 重複している条件名はスキップ
            if cond_name in conditional_name_set:
                continue

            conditional_name_set.add(cond_name)
            result += cond_name + " = " + str(event_info_list[index]) + "\n"
            index += 1

        logger.logic_log('LOSI00002', 'result: %s' % (result))
        return result

    def _replace_action_info(self, content, trace_id, tag):
        """
        ACTION_INFOタグを置き換えるための、アクション情報を取得する

        [引数]
        trace_id : トレースid

        [戻り値]
        str 置換後の文章
        """
        logger.logic_log('LOSI00001', 'content: %s, trace_id: %s, tag: %s' % (
            content, trace_id, tag))

        try:
            er = EventsRequest.objects.get(trace_id=trace_id)
            rr = RhdmResponse.objects.get(trace_id=trace_id)
        except Exception as e:
            # 取得に失敗したら置換しないで返す
            logger.system_log('LOSE01123', traceback.format_exc())
            return content

        rra_list = RhdmResponseAction.objects.filter(
            response_id=rr.response_id)
        action_type_list = ActionType.objects.all()
        rule_type_name = RuleType.objects.get(
            pk=er.rule_type_id).rule_type_name
        driver_type_list = DriverType.objects.all()
        info = ''
        for rra in rra_list:
            # メールアクションの情報は載せない
            if rra.action_type_id == MAIL:
                continue
            driver_type_id = action_type_list[rra.action_type_id -
                                              1].driver_type_id
            action_type_str = driver_type_list[driver_type_id-1].name + '(ver' + str(
                driver_type_list[driver_type_id-1].driver_major_version) + ')'

            act_param_info = self._transform_json_str(
                rra.action_parameter_info, 'ACTION_PARAMETER_INFO')
            info += """
[アクション情報]
ルール種別 : {}
ルール名: {}
アクション実行順 : {}
アクション種別 : {}
アクションパラメータ情報 : {}
アクションリトライ間隔 : {}
アクションリトライ回数 : {}
アクション中断間隔 : {}
アクション中断回数 : {}
""".format(rule_type_name, rra.rule_name, rra.execution_order, action_type_str,
                act_param_info, rra.action_retry_interval, rra.action_retry_count,
                rra.action_stop_interval, rra.action_stop_count)

            # アクション日時書き込み
            try:
                ah = ActionHistory.objects.get(
                    response_id=rra.response_id, execution_order=rra.execution_order)
                time_stamp = TimeConversion.get_time_conversion(
                    ah.action_start_time, 'Asia/Tokyo')
                info += "アクション開始日時 : " + time_stamp + "\n"

            except ActionHistory.DoesNotExist:
                info += "アクション開始日時 : 未実行\n"

        content = content.replace(tag, info)

        logger.logic_log('LOSI00002', 'content: %s' % (content))
        return content

    def _transform_json_str(self, json_str, key):
        """
        json形式のパラメータの見栄えを良くする文字列を生成する
        [引数]
        json_str : json形式のstr keyの
        key : json_strのkey。json_str[key]はlistであること
        """
        logger.logic_log('LOSI00001', 'json_str: %s, key: %s' %
                         (json_str, key))

        info = json.loads(json_str)
        value_list = info.get(key, [])
        result = ', '.join(value_list)

        logger.logic_log('LOSI00002', 'result: %s' % (result))
        return result
