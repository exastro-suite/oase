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

from django.urls import path, re_path
from . import personal_config, locked_user, black_list, white_list

app_name = 'user'
urlpatterns = [
    # 個人設定
    re_path(r'^personal_config$',  personal_config.personal_config,  name='personal_config'),
    re_path(r'^modify/mailaddr$',  personal_config.modify_mailaddr,  name='user_modify_mailaddr'),
    re_path(r'^determ/mailaddr$',  personal_config.determ_mailaddr,  name='user_determ_mailaddr'),

    # アカウントロックユーザ
    path('locked_user', locked_user.locked_user, name='locked_user'),
    path('unlock', locked_user.unlock, name='unlock'),

    # パスワード設定
    # top/urls.pyで対応

    # ブラックリスト
    path('black_list', black_list.black_list, name='black_list'),
    path('black_list/black_list_edit', black_list.edit, name='black_list_edit'),
    path('black_list/modify',  black_list.modify,   name='black_list_modify'),

    # ホワイトリスト
    path('white_list',                 white_list.white_list, name='white_list'),
    path('white_list/white_list_edit', white_list.edit,       name='white_list_edit'),
    path('white_list/modify',          white_list.modify,     name='white_list_modify'),

    # その他設定
]

