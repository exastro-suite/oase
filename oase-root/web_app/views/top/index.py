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
  ホームビュー

[引数]


[戻り値]


"""




from django.shortcuts import render

from libs.commonlibs.oase_logger import OaseLogger


logger = OaseLogger.get_instance() # ロガー初期化


################################################
def index(request):
    """
    [メソッド概要]
      DashBoard画面のview関数
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    data = {
        'mainmenu_list' : request.user_config.get_menu_list(),
        'user_name'     : request.user.user_name,
        'lang_mode'     : request.user.get_lang_mode(),
    }

    logger.logic_log('LOSI00002', 'None', request=request)

    return render(request, 'top/index.html', data)


################################################
def notpermitted(request):
    """
    [メソッド概要]
      「権限なし」画面のview関数
    """

    logger.logic_log('LOSI00001', 'None', request=request)

    data = {
        'mainmenu_list' : request.user_config.get_menu_list(),
        'user_name'     : request.user.user_name,
        'lang_mode'     : request.user.get_lang_mode(),
    }

    logger.logic_log('LOSI00002', 'None', request=request)

    return render(request, 'top/notpermitted.html', data)
