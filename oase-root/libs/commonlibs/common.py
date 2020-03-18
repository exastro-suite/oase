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
    汎用的なライブラリ

"""

import calendar
import codecs
import base64
import hashlib
import re


class Common:

    @classmethod
    def convert_response_date(cls, date):
        """
        [概要]
        [引数]
        date: レスポンスの受信日時 response.headers['Date']
        """
        # decode
        words = date.split(' ')
        months = {}

        for i, v in enumerate(calendar.month_abbr):
            months[v] = i

        # レスポンス受信日時を YYYY/MM/DD HH:mm:ss の形式にする
        result = words[3] + '/' + str(months[words[2]]) + '/' + words[1] + ' ' + words[4]

        return result

    @classmethod
    def ky_encrypt(cls, plain_string):
        """
        [メソッド概要]
            スクランブル化

            @param plain_string 平文
            @return 暗号文
        """

        return codecs.encode(
            base64.encodebytes(
                plain_string.encode('utf8')).decode("ascii").replace(
                '\n', ''), 'rot_13')

    @classmethod
    def ky_decrypt(cls, encrypted_string):
        """
        [メソッド概要]
            スクランブル解除

            @param encrypted_string 暗号文
            @return 平文
        """

        return base64.decodebytes(codecs.encode(encrypted_string, 'rot_13').encode('utf8')).decode("ascii")

    @classmethod
    def oase_hash(cls, plain_string):
        """
        [メソッド概要]
            OASE共通暗号化部分のハッシュ文字列化

            @param plain_string 平文
            @return sha256ハッシュ
        """

        return cls.sha256_hash_str(plain_string)

    @classmethod
    def md5_hash_str(cls, plain_string):
        """
        [メソッド概要]
            md5ハッシュ文字列化

            @param plain_string 平文
            @return md5ハッシュ
        """

        return hashlib.md5(plain_string.encode()).hexdigest()

    @classmethod
    def sha256_hash_str(cls, plain_string):
        """
        [メソッド概要]
            sha256ハッシュ文字列化

            @param plain_string 平文
            @return sha256ハッシュ
        """

        return hashlib.sha256(plain_string.encode()).hexdigest()


class DriverCommon:
    """
    ドライバー共通のライブラリ
    """
    @classmethod
    def has_right_reserved_value(cls, conditions, value):
        """
        valueに含まれる予約変数が正しく使われているか調べる。
        予約変数が未使用か、正しい場合はTrue,
        不正の場合は、Falseを返す。
        conditions: 条件名のリスト
        """
        reserved_values = cls.get_reserved_values(value)
        conditions = ["VAR_" + c for c in conditions]

        for v in reserved_values:
            if v not in conditions:
                return False
        return True

    @classmethod
    def get_reserved_values(cls, value):
        """
        valueから予約変数名の文字列のリストを返す。
        予約変数の形式(変数名はhoge): {{ VAR_hoge }}
        空マッチは結果に含まれる
        """
        return re.findall(r"{{ (.+?) }}", value)
