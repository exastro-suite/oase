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
  AES形式の暗号化、復号化を実施する。

[引数]


[戻り値]


"""




import base64
from Crypto import Random
from Crypto.Cipher import AES


class AESCipher(object):
    """
    [クラス概要]
        AES暗号化ライブラリ

        引用元:
        https://github.com/teitei-tk/Simple-AES-Cipher
        (License MIT)
    """

    def __init__(self, key, key_size=32, word_size=64):
        """
        [メソッド概要]
            コンストラクタ

            ※ word_size -> AES.block_size=16の倍数であること
        """
        self.word_size = word_size
        if len(key) >= len(str(key_size)):
            self.key = key[:key_size]
        else:
            self.key = self._pad(key, key_size)

    def encrypt(self, raw, mode=AES.MODE_CBC):
        raw = self._pad(raw, self.word_size)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, mode, iv)
        return base64.b64encode(iv + cipher.encrypt(raw)).decode('utf-8')

    def decrypt(self, enc, mode=AES.MODE_CBC):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, mode, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s, bs):
        return s + (bs - len(s) % bs) * chr(bs - len(s) % bs)

    def _unpad(self, s):
        return s[:-ord(s[len(s)-1:])]
