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
文字列をmd5, sha256, AESCipherに変換する
第2引数にハッシュ化したい文字列を指定する

$python encrypter

"""
import os
import sys
import hashlib

# --------------------------------
# ルートパス追加
# --------------------------------
oase_root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../oase-root/')
sys.path.append(oase_root_dir)

from libs.commonlibs.common import Common 
from libs.commonlibs.aes_cipher import AESCipher
from confs.frameworkconfs.settings import AES_KEY

if __name__ == '__main__':

    input_value = 'P@$$w0rd'

    args = sys.argv
    if len(args) == 2:
        input_value = args[1]
    else:
        print("実行方法が間違っています。実行方法を確認してください。\n実行例）python /home/centos/OASE/oase-root/tool/encrypter.py 'password@1'")
        sys.exit(1)

    # AESCipher変換
    cipher = AESCipher(AES_KEY)
    encrypted = cipher.encrypt(input_value)
    # 暗号化結果
    print(encrypted)

    # 復号化結果
#    decrypted = cipher.decrypt(encrypted)
#    print(decrypted)
