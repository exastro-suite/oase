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




from libs.commonlibs import define as defs
from web_app.models.models import System, AccessPermission, UserGroup, User


# ユーザ権限を持つグループに属するユーザのuser_idを返す
def get_userid_at_user_auth():
    user_objects_list = []
    user_id_list = []
    auth_user_objects = AccessPermission.objects.filter(menu_id=2141002004,permission_type_id=1)
    for perm in auth_user_objects:
        user_objects_list = UserGroup.objects.filter(group_id=perm.group_id)
        for user in user_objects_list:
            user_id_list.append(user.user_id)
    return set(user_id_list)

# OASE_T_SYSTEMで指定したアカウントロック権限のloginIDを返す
def get_lock_auth_user():
    login_id_comma = System.objects.get(config_id="NOTIFICATION_DESTINATION")
    login_id_list = login_id_comma.value.split(',')
    user_list = []
    for login_id in login_id_list:
        # 存在しないlogin_idが登録されていたとき回避
        if User.objects.filter(login_id=login_id):
            user = User.objects.get(login_id=login_id)
            user_list.append(user.user_id)
    return set(user_list)

