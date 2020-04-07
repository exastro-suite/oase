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
  システム設定情報を保持する

[引数]


[戻り値]


"""




class OASEError(Exception):

    def __init__(self, msgid, logid, msg_params=None, log_params=None):

        self.msg_id   = str(msgid)
        self.log_id   = str(logid)
        self.arg_dict = msg_params
        self.arg_list = log_params

    def __str__(self):

        return '%s' % (self.log_id)


class OASELoginError(Exception):

    def __init__(self, msgid, *args, **kwargs):

        self.msg_id   = str(msgid)
        self.log      = kwargs['log'] if 'log' in kwargs else ''
        self.arg_list = args
        self.arg_dict = kwargs

    def __str__(self):

        return '%s(%s)' % (self.log, self.msg_id)


