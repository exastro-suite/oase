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

[引数]

[戻り値]


"""

import base64
import json
import socket
import pytz
import datetime
import re
from libs.commonlibs.oase_logger import OaseLogger
from web_app.models.models import User,System,AccessPermission,UserGroup


logger = OaseLogger.get_instance() # ロガー初期化


class RequestToApply:
    @classmethod
    def _request(cls, send_data, request=None):
        """
        [概要]
        適用君へリクエスト送信

        [引数]
        send_data : リクエスト用データ
        
        [戻り値]
        recv_data : 受信データ
        """
        # 適用君サーバーのIPアドレス、ポート番号を取得する
        apply_ipaddr, apply_port = System.get_apply_ip_and_port()

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                send_data = json.dumps(send_data)
                send_data = send_data.encode()

                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8192)
                sock.connect((apply_ipaddr, apply_port))

                logger.logic_log('LOSI13021', apply_ipaddr, apply_port, request=request)

                sock.sendall(send_data)
                sock.shutdown(socket.SHUT_WR)

                # 応答受信
                recv_data = b''
                while True:
                    rcvtmp = sock.recv(4096)
                    if not rcvtmp:
                        break

                    recv_data = b'%s%s' % (recv_data, rcvtmp)

                sock.close()

        except ConnectionRefusedError:
            return {'result':'NG', 'msg':'MOSJA00016'}

        recv_data = recv_data.decode()
        recv_data = json.loads(recv_data)

        return recv_data

    @classmethod
    def operate(cls, send_data, request=None):
        """
        [概要]
        アプライ君にルール関連の操作を要求する

        [引数]
        send_data : リクエスト用データ

        [戻り値]
        result : 正常ならTrue, 異常ならFalse
        msg : 受信メッセージ 
        """
        recv_data = cls._request(send_data, request=request)

        if recv_data['result'] == 'NG':
            return False, recv_data['msg']

        elif recv_data['result'] == 'OK':
            return True, recv_data['msg']


    @classmethod
    def getfile(cls, send_data, request=None):
        """
        [概要]
        アプライ君にファイルを要求する

        [引数]
        send_data : リクエスト用データ
        
        [戻り値]
        result : 正常ならTrue, 異常ならFalse
        msg : 受信メッセージ 
        filename : ファイル名
        filedata : ファイルデータ
        """
        recv_data = cls._request(send_data, request=request)

        filedata = recv_data['filedata']
        filedata = base64.b64decode(filedata.encode('utf-8'))

        if recv_data['result'] == 'NG':
            return False, recv_data['msg'], recv_data['filename'], filedata,

        elif recv_data['result'] == 'OK':
            return True, recv_data['msg'], recv_data['filename'], filedata,


class Common:
    @classmethod
    def convert_filters(cls, filters, where_info):
        """
        [概要]
          jsフィルターをDjangoORM filterに変換する
        [引数]
          filters : dict
          where_info : dict DjangoORM filter
        """
        # todo where_infoのdictチェック

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

    @classmethod
    def get_mail_notification_list(cls):
        """
        [概要]
        メール通知先リストを取得する
        [戻り値]
        mail_list : list メールリスト
        """

        ndt    = '0'
        ad_flg = False

        mail_list = []
        mail_list.append(User.objects.get(pk=1).mail_address)

        # システム設定からメール通知先種別、および、AD連携フラグを取得
        rset = System.objects.filter(config_id__in=['NOTIFICATION_DESTINATION_TYPE', 'ADCOLLABORATION']).values('config_id', 'value')
        for rs in rset:
            # AD連携フラグをセット
            if rs['config_id'] == 'ADCOLLABORATION':
                if rs['value'] != '0':
                    ad_flg = True

            # メール通知先種別をセット
            elif rs['config_id'] == 'NOTIFICATION_DESTINATION_TYPE':
                ndt = rs['value']

        # AD連携時はメール通知先種別を無視する
        if ad_flg == False:
            if ndt == '1':
                # ユーザ更新権限のあるグループ (group_id=1は除外)
                group_list = list(AccessPermission.objects.exclude(group_id=1).filter(permission_type_id=1,menu_id=2141002004).values_list('group_id', flat=True))
                user_list = list(UserGroup.objects.filter(group_id__in=group_list).values_list('user_id', flat=True)
                )
                mail_list.extend(list(User.objects.filter(user_id__in=user_list).values_list('mail_address', flat=True)))

            if ndt == '2':
                login_id_list = System.objects.get(config_id='NOTIFICATION_DESTINATION').value.split(',')
                mail_list.extend(list(User.objects.filter(login_id__in=login_id_list).values_list('mail_address', flat=True)))

        return mail_list

class TimeConversion:
    @classmethod
    def get_time_conversion(cls, naive, tz, request=None):
        """
        [概要]
        時刻変換処理を行う
        [戻り値]
        変換した時刻
        """

        conv_dt = naive.astimezone(pytz.timezone(tz)).strftime('%Y-%m-%d %H:%M:%S')

        logger.logic_log('LOSI13022', tz, naive, conv_dt, request=request)

        return conv_dt


    @classmethod
    def get_time_conversion_utc(cls, naive, tz, request=None):
        """
        [概要]
        時刻変換処理を行う
        [戻り値]
        utc_dt : 変換した時刻(UTC)
        """

        tz_ex   = pytz.timezone(tz)
        naive   = naive.replace('/', '-')
        user_dt = datetime.datetime.strptime(naive, '%Y-%m-%d %H:%M:%S')
        cou_dt  = tz_ex.localize(user_dt, is_dst=None)
        utc_dt  = cou_dt.astimezone(pytz.utc)

        logger.logic_log('LOSI13022', tz, naive, utc_dt, request=request)

        return utc_dt


def get_client_ipaddr(request):

    """
    [概要]
      クライアントのIPアドレスを取得する
    [戻り値]
      ipaddr : str : IPアドレス
    """

    ipaddr = ''

    if not getattr(request, 'META', None):
        return ipaddr

    # x-real-ip > x-forwarded-for > remote_addr の優先順位でIPアドレスを取得
    if 'HTTP_X_REAL_IP' in request.META:
        ipaddr = request.META['HTTP_X_REAL_IP']

    elif 'HTTP_X_FORWARDED_FOR' in request.META:
        ipaddr = request.META['HTTP_X_FORWARDED_FOR']

    elif 'REMOTE_ADDR' in request.META:
        ipaddr = request.META['REMOTE_ADDR']

    return ipaddr


def is_addresses(addresses):
    """
    カンマ区切りのメールアドレス形式チェック
    [引数]
    addresses : str カンマ区切りのメールアドレスス
    """

    pattern = r'^([\w!#$%&\'*+\-\/=?^`{|}~]+(\.[\w!#$%&\'*+\-\/=?^`{|}~]+)*|"([\w!#$%&\'*+\-\/=?^`{|}~. ()<>\[\]:;@,]|\\[\\"])+")@(([a-zA-Z\d\-]+\.)+[a-zA-Z]+|\[(\d{1,3}(\.\d{1,3}){3}|IPv6:[\da-fA-F]{0,4}(:[\da-fA-F]{0,4}){1,5}(:\d{1,3}(\.\d{1,3}){3}|(:[\da-fA-F]{0,4}){0,2}))\])$'
    repatter = re.compile(pattern)
    address_list = addresses.split(',')

    # 0件チェック
    if addresses == '':
        return True

    for address in address_list:
        if not repatter.match(address):
            return False

    return True


def set_wild_iterate(ipaddr):
    """
    [メソッド概要]
    # 第1～3オクテットで出現した[*]以降、オクテッドは[*]に変換
    [戻り値]
    tmp_ip : str : オクテット変換後のIPアドレス
    """
    wild_flag = False
    wild_list = ipaddr.split('.')
    tmp_ip = ''

    loop = 0
    for v in wild_list:
        if '*' in v and loop < 3:
            wild_flag = True

        if wild_flag:
            tmp_ip += '*'
        else:
            tmp_ip += v

        if loop < 3:
            tmp_ip += '.'

        loop += 1

    return tmp_ip
