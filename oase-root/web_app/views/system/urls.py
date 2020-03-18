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
    "システム"カテゴリのURI定義

"""


from django.urls import path, re_path
from . import system_conf, mail_template, monitoring, action, group, user

app_name = 'system'
urlpatterns = [
    # システム設定
    re_path(r'^system_conf$', system_conf.index, name='system_conf'),
    re_path(r'^system_conf/edit$', system_conf.edit, name='system_conf_edit'),
    re_path(r'^system_modify$',     system_conf.modify,       name='system_modify'),
    re_path(r'^run_ad$',            system_conf.run_ad,       name='run_ad'),

    # グループ
    re_path(r'^group$',         group.group,    name='group'),
    path('group/edit', group.edit, name='group_edit'),
    path('group/complete_permission/<int:group_id>/', group.complete_permission, name='complete_permission'),
    re_path(r'^group/modify$',  group.modify,   name='group_modify'),
    re_path(r'^group/data$',    group.data,     name='group_data'),

    # ユーザー
    re_path(r'^user$',  user.user,   name='user'),
    path('user/edit',  user.edit,   name='user_edit'),
    re_path(r'^user/modify$',  user.modify,   name='user_modify'),
    re_path(r'^user/data$',    user.data,   name='user_data'),

    # 監視アダプタ
    path('monitoring',             monitoring.monitoring,  name='monitoring'),
    path('monitoring/create',      monitoring.create,      name='monitoring_create'),
    path('monitoring/delete',      monitoring.delete,      name='monitoring_delete'),
    path('monitoring/update',      monitoring.update,      name='monitoring_update'),

    # アクション設定
    path('action',             action.action,  name='action'),
    path('action/modify',      action.modify,  name='action_modify'),

    # メールテンプレート
    path('mail', mail_template.index, name='mail'),
    path('mail/create', mail_template.create, name='mail_create'),
    path('mail/update', mail_template.update, name='mail_update'),
    path('mail/delete', mail_template.delete, name='mail_delete'),
]
