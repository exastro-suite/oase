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
from . import action_history, rule, decision_table, request_history

app_name = 'rule'
urlpatterns = [

    # デシジョンテーブル
    path('decision_table', decision_table.index,    name='decision_table'),
    path('decision_table/data', decision_table.data,   name='decision_table_data'),
    path('decision_table/modify', decision_table.modify,   name='table_modify'),
    path('decision_table/delete_table/<int:rule_type_id>/', decision_table.delete_table, name='delete_table'),
    path('decision_table/modify/<int:rule_type_id>/', decision_table.modify_detail, name='table_modify_detail'),
    re_path(r'^decision_table/download/(?P<rule_type_id>\d+)/$',  decision_table.download,  name='download'),

    # ルール
    re_path(r'^rule$',         rule.rule,         name='rule'),
    re_path(r'^rule/data/staging$',    rule.rule_staging,    name='rule_staging'),
    re_path(r'^rule/data/production$', rule.rule_production, name='rule_production'),
    re_path(r'^rule/data/history$',    rule.rule_history,    name='rule_history'),
    path('rule/pseudo_request/<int:rule_type_id>', rule.rule_pseudo_request, name='rule_pseudo_request'),
    re_path(r'^rule/upload$',  rule.rule_upload,  name='rule_upload'),
    re_path(r'^rule/polling/bulk/(?P<rule_manage_id>\d+)/$',                   rule.rule_polling_bulk, name='rule_polling_bulk'),
    re_path(r'^rule/polling/(?P<rule_manage_id>\d+)/(?P<trace_id>\w+)/$',      rule.rule_polling,      name='rule_polling'),
    re_path(r'^rule/download/(?P<rule_manage_id>\w+)/$',                       rule.rule_download,     name='rule_download'),
    re_path(r'^rule/switchback/(?P<rule_manage_id>\d+)/$',                     rule.rule_switchback,   name='rule_switchback'),
    re_path(r'^rule/apply/(?P<rule_manage_id>\d+)/(?P<request_type_id>\d+)/$', rule.rule_apply,        name='rule_apply'),
    re_path(r'^rule/change_status$',    rule.rule_change_status,    name='rule_change_status'),
    re_path(r'^rule/get_record$',    rule.rule_get_record,    name='rule_get_record'),
    path('rule/bulkpseudocall/<int:rule_type_id>/', rule.bulkpseudocall, name='bulkpseudocall'),

    # リクエスト履歴
    path('request_history',  request_history.index,  name='request_history'),
  
    # アクション履歴
    re_path(r'^action_history$',  action_history.action_history,  name='action_history'),
    path('action_history/download/<int:response_id>/<int:execution_order>/',  action_history.download,  name='action_history_download'),
    path('action_history/action_dataobject/<int:response_id>/<int:execution_order>/',  action_history.dataobject,  name='action_dataobject'),
    path('action_history/retry', action_history.retry, name='retry'),
    path('action_history/resume', action_history.resume, name='action_history_resume'),
    path('action_history/stop', action_history.stop, name='action_history_stop'),
]

