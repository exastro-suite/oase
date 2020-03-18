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
アクション機構とcoreを繋ぐ機構。

"""

from abc import ABCMeta, abstractmethod
import abc


class AbstractManager(metaclass=ABCMeta):
    """
    [概要]
    アクション機構の抽象クラス
    """

    @abc.abstractmethod
    def set_action_parameters(self):
        """
        [概要]
        [引数]
        [戻り値]
        """
        pass

    @abc.abstractmethod
    def set_driver(self, exe_order):
        """
        [概要]
        [引数]
        [戻り値]
        """
        pass

    @abc.abstractmethod
    def set_information(self, rhdm_res_act, action_history):
        """
        [概要]
        [引数]
        [戻り値]
        """
        pass

    @abc.abstractmethod
    def act(self, rhdm_res_act, retry=False):
        """
        [概要]
        [引数]
        """
        pass

    @abc.abstractmethod
    def retry(self, rhdm_res_act, retry=True):
        """
        [概要]
        再実行
        [引数]
        """
        pass

    def is_exastro_suite(self):
        """
        [概要]
        エグザストロシリーズか否か。基本はFalseとする。
        [戻り値]
        """
        return False

    def act_with_menuid(self, act_his_id, exec_order):
        """
        [概要]
        [引数]
        """
        pass
