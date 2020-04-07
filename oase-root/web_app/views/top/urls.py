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
from . import index, login, pass_ch, onetime_pass, inquiry

app_name = 'top'
urlpatterns = [
    re_path(r'^index$',  index.index,   name='index'),
    path('notpermitted', index.notpermitted,   name='notpermitted'),

    re_path(r'^login$',      login.login,  name='login'),
    re_path(r'^login/auth$', login.auth,   name='login_auth'),
    re_path(r'^logout$',     login.logout, name='logout'),

    path('pass_ch',         login.pass_ch,          name='pass_ch'),
    path('pass_ch_logout',  login.pass_ch_logout,   name='pass_ch_logout'),
    path('pass_ch_exec',    pass_ch.pass_ch_exec,   name='pass_ch_exec'),

    re_path(r'^pass_initialize',    login.pass_initialize,          name='pass_initialize'),
    re_path(r'^onetime_pass_exec',  onetime_pass.onetime_pass_exec, name='onetime_pass_exec'),

    re_path(r'^inquiry$',  inquiry.inquiry,   name='inquiry'),

]

