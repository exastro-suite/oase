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
  デコレーター

[引数]


[戻り値]


"""




from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

from libs.commonlibs.oase_logger import OaseLogger
from libs.webcommonlibs.user_config import UserConfig


logger = OaseLogger.get_instance() # ロガー初期化


def check_allowed_auth(menu_id, auth_list):

    """
    [メソッド概要]
      view関数へのアクセス権限チェック
    [引数]
      menu_id   : 遷移先メニューのID
      auth_list : ユーザのメニュー別アクセス権限一覧
    [戻り値]
      権限あり
        view関数の結果
      権限なし
        リダイレクト先のHTTPレスポンス情報
    """

    def _check_auth(func):
        def wrapper(request, *args, **kwargs):

            user_auth = request.user_config.get_menu_auth_type(menu_id)
            if user_auth not in auth_list:
                logger.system_log('LOSI13003', request.path, user_auth, auth_list, request=request)
                if 'HTTP_X_REQUESTED_WITH' in request.META and request.META['HTTP_X_REQUESTED_WITH'] == 'XMLHttpRequest':
                    return HttpResponse(status=400)
                else:
                    return HttpResponseRedirect(reverse('web_app:top:notpermitted'))

            return func(request, *args, **kwargs)

        return wrapper

    return _check_auth


def check_allowed_ad(url):

    """
    [メソッド概要]
      ADユーザのview関数へのアクセス可否チェック
    [引数]
      url     : アクセス禁止時のリダイレクト先URL
    [戻り値]
      アクセス可能
        view関数の結果
      アクセス禁止
        リダイレクト先のHTTPレスポンス情報
    """

    def _check_ad(func):
        def wrapper(request, *args, **kwargs):

            if request.session['_auth_user_backend'].endswith('ActiveDirectoryAuthBackend'):
                logger.system_log('LOSI13020', request.path, request=request)
                if 'HTTP_X_REQUESTED_WITH' in request.META and request.META['HTTP_X_REQUESTED_WITH'] == 'XMLHttpRequest':
                    return HttpResponse(status=400)
                else:
                    return HttpResponseRedirect(url)

            return func(request, *args, **kwargs)

        return wrapper

    return _check_ad


