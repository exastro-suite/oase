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
    メールアクションモジュール

"""

import os
import sys
import smtplib
import traceback
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formatdate

# oase-rootまでのバスを取得
my_path = os.path.dirname(os.path.abspath(__file__))
tmp_path = my_path.split('oase-root')
# ログファイルのパスを生成
root_dir_path = tmp_path[0] + 'oase-root'
sys.path.append(root_dir_path)

from libs.commonlibs.common import Common
from libs.commonlibs.oase_logger import OaseLogger
from libs.commonlibs.define import *
from libs.backyardlibs.action_driver.common.driver_core import DriverCore

logger = OaseLogger.get_instance() # ロガー初期化

class Mail1Core(DriverCore):
    """
    [クラス概要]
        メールアクションクラス
    """
    def __init__(self, TraceID):
        """
        [概要]
            コンストラクタ
        """
        self.TraceID = TraceID

    def send(self, smtpderver, protocol, port, \
             subject, text, \
             from_address, password,
             to_address, cc_address, bcc_address, \
             charset = 'utf-8'):
        """
        [メソッド概要]
            メール送信メゾット
        """
        logger.logic_log('LOSI00001', 'smtpderver: %s, protocol: %s, port: %s, subject: %s, text: %s, from_address: %s, password: %s, to_address: %s, cc_address: %s, bcc_address: %s,' % (smtpderver, protocol, port, subject, text, from_address, password, to_address, cc_address, bcc_address))

        try:
            smtpHeader = {}
            if len(text) != 0:
                smtpHeader = MIMEText(text.encode(charset), 'plain', charset)
            else:
                smtpHeader = MIMEText(" ".encode(charset), 'plain', charset)
            if len(subject) != 0:
                smtpHeader['Subject'] = Header(subject, charset)
            else:
                smtpHeader['Subject'] = ''
            smtpHeader['From'] = from_address
            if len(to_address) != 0:
                smtpHeader['To']   = to_address
            if len(cc_address) != 0:
                smtpHeader['Cc']   = cc_address
            if len(bcc_address) != 0:
                smtpHeader['Bcc']  = bcc_address
            smtpHeader['Date'] = formatdate(localtime=True)

            smtp = smtplib.SMTP(smtpderver,port)
            if protocol == SMTP_PROTOCOL.SMTP:   #smtp
                pass
            else:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                smtp.login(from_address,password)

            smtp.sendmail(from_address, [to_address,cc_address,bcc_address], smtpHeader.as_string())
            smtp.close()

            logger.logic_log('LOSI00002', 'None')
            return True

        except Exception as ex:
            logger.logic_log('LOSM01400', self.TraceID, traceback.format_exc())
            return False
