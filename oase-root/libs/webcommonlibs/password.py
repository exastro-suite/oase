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
  ランダムパスワード情報を生成する

[引数]


[戻り値]


"""




import random

class RandomPassword:


    def __init__(self):

        list            = []
        self.password   = ''
        lowercaselist   = 'abcdefghijklmnopqrstuvwxyz'
        uppercaselist   = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        digitslist      = '0123456789'
        punctuationlist = r'!#$%&()*+,-./;<=>?@[]^_{}|~'
        alllist         = lowercaselist + uppercaselist + digitslist + punctuationlist

        list.append(random.choice(lowercaselist))
        list.append(random.choice(uppercaselist))
        list.append(random.choice(digitslist))
        list.append(random.choice(punctuationlist))
        list.extend(random.choices(alllist, k=6))
        random.shuffle(list)

        for l in list:
            self.password = self.password + str(l)


    def get_password(self):

        return self.password

