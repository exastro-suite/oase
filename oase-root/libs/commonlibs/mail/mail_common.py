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
  メールドライバーのライブラリ

"""

import traceback

from web_app.models.models import MailTemplate
from web_app.models.mail_models import MailDriver
from web_app.models.mail_models import MailActionHistory
from libs.backyardlibs.action_driver.mail.mail_driver import mailManager
from libs.commonlibs.oase_logger import OaseLogger
from libs.commonlibs.common import DriverCommon

logger = OaseLogger.get_instance()


def check_dt_action_params(params, act_info, conditions, *args, **kwargs):
    """
    アクションパラメータのチェックをする。
    エラーメッセージのリストを返す。
    """
    message_list = []
    to_list = []
    to_info = kwargs['to_info'] if 'to_info' in kwargs else {}
    pre_flg = kwargs['pre_flg'] if 'pre_flg' in kwargs else False

    for param in params:
        param = param.strip()

    # パラメーター情報取得
    check_info = mailManager.analysis_parameters(params)

    # MAIL_NAME チェック
    message_list = check_dt_action_params_mail_name(check_info, act_info,message_list)

    # MAIL_TEMPLATE チェック
    result = check_dt_action_params_mail_template(check_info, pre_flg, act_info, to_list, to_info, message_list)
    message_list = result[0] 
    to_list = result[1]
    to_info = result[2]

    # メール送信先設定の有無チェック(MAIL_TO MAIL_CC MAIL_BCC)
    message_list = check_dt_action_params_mail_to_list(check_info, conditions, to_list, message_list)

    return message_list


def check_dt_action_params_mail_name(check_info, act_info, message_list):
    """
    MAIL_NAME のチェックをする。
    エラーメッセージのリストを返す。
    """   
    mail_name = check_info['MAIL_NAME']
    
    if mail_name is None:
        logger.logic_log('LOSM00008', check_info)
        message_list.append({'id': 'MOSJA03113', 'param': 'MAIL_NAME'})

    else:
        # MAIL_NAME の値が登録済みのドライバー名であるかチェック
        if 'drv_name' not in act_info:
            act_info['drv_name'] = {}

        if mail_name not in act_info['drv_name']:
            rcnt = MailDriver.objects.filter(mail_disp_name=mail_name).count()
            act_info['drv_name'][mail_name] = True if rcnt > 0 else False

        if not act_info['drv_name'][mail_name]:
            logger.logic_log('LOSM00009', check_info)
            message_list.append({'id': 'MOSJA03117', 'param': None})
    
    return message_list


def check_dt_action_params_mail_template(check_info, pre_flg, act_info, to_list, to_info, message_list):
    """
    MAIL_TEMPLATE のチェックをする。
    エラーメッセージのリスト、宛先のリスト、テンプレート名と宛先の情報を返す。
    """
    template = check_info['MAIL_TEMPLATE']

    if template is None:
        logger.logic_log('LOSM00010', check_info)
        message_list.append({'id': 'MOSJA03113', 'param': 'MAIL_TEMPLATE'})

    elif template == '':
        if not pre_flg:
            logger.logic_log('LOSM00011', check_info)
            message_list.append({'id': 'MOSJA03118', 'param': None})

    else:
        # MAIL_TEMPLATE の値が登録済みのメールテンプレート名であるかチェック
        result = is_dt_action_params_mail_template(act_info, template, to_list, to_info)
        if result:
            to_list.extend(to_info[template])

        else:
            logger.logic_log('LOSM00011', check_info)
            message_list.append({'id': 'MOSJA03118', 'param': None})

    return message_list, to_list, to_info


def check_dt_action_params_mail_to_list(check_info, conditions, to_list, message_list):
    """
    メール送信先設定の有無チェックをする。
    エラーメッセージのリストを返す。
    """
    # MAIL_TO チェック
    mail_to = check_info['MAIL_TO']
    if mail_to is None:
        logger.logic_log('LOSM00012', check_info)
        message_list.append({'id': 'MOSJA03114', 'param': 'MAIL_TO'})
    elif not DriverCommon.has_right_reserved_value(conditions, mail_to):
        logger.logic_log('LOSM00023', mail_to)
        message_list.append({'id': 'MOSJA03137', 'param': 'MAIL_TO'})
    elif mail_to != '':
        to_list.append(mail_to)

    # MAIL_CC チェック
    mail_cc = check_info['MAIL_CC']
    if mail_cc is None:
        logger.logic_log('LOSM00013', check_info)
        message_list.append({'id': 'MOSJA03114', 'param': 'MAIL_CC'})

    elif not DriverCommon.has_right_reserved_value(conditions, mail_cc):
        logger.logic_log('LOSM00023', mail_cc)
        message_list.append({'id': 'MOSJA03137', 'param': 'MAIL_CC'})

    # MAIL_BCC チェック
    mail_bcc = check_info['MAIL_BCC']
    if mail_bcc is None:
        logger.logic_log('LOSM00014', check_info)
        message_list.append({'id': 'MOSJA03114', 'param': 'MAIL_BCC'})

    elif not DriverCommon.has_right_reserved_value(conditions, mail_bcc):
        logger.logic_log('LOSM00023', mail_bcc)
        message_list.append({'id': 'MOSJA03137', 'param': 'MAIL_BCC'})

    # メール送信先設定の有無チェック
    if len(to_list) <= 0:
        logger.logic_log('LOSM00015', check_info)
        message_list.append({'id': 'MOSJA03119', 'param': None})

    return message_list


def is_dt_action_params_mail_template(act_info, template, to_list, to_info):
    """
    登録済みのメールテンプレート名であるかチェックをする。
    メールテンプレート名が登録済みであればTrueを返す。
    """
    if 'tmp_name' not in act_info:
        act_info['tmp_name'] = {}

    if template not in act_info['tmp_name']:
        rset = list(MailTemplate.objects.filter(
            mail_template_name=template,
        ).values_list(
            'destination', flat=True)
        )
        for r in rset:
            if r:
                to_list.append(r)
        else:
            if template not in to_info:
                to_info[template] = to_list

        act_info['tmp_name'][template] = True if len(rset) > 0 else False
    
    return act_info['tmp_name'][template]


def get_history_data(action_his_id):
    """
    [概要]
    action_his_idのメールアクション履歴を取得する
    [引数]
    action_his_id: int
    [戻り値]
    result: dict アクション情報に表示したい情報
    """

    result = {}
    try:
        history = MailActionHistory.objects.get(action_his_id=action_his_id)
        result['MOSJA13029'] = history.mail_template_name
        result['MOSJA13030'] = history.mail_address

    except MailActionHistory.DoesNotExist:
        logger.system_log('LOSE00000', action_his_id, traceback.format_exc())

    finally:
        return result
