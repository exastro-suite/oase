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

from rest_framework import serializers

from web_app.models.models import AccessPermission
from libs.commonlibs import define as defs


class AccessPermissionSerializer(serializers.ModelSerializer):

    PERM_TYPE_LIST = [defs.ALLOWED_MENTENANCE, defs.VIEW_ONLY, defs.NO_AUTHORIZATION, ]

    class Meta:
        model = AccessPermission
        fields = (
            'menu_id', 'permission_type_id'
        )


    def validate_menu_id(self, menu_id):

        if menu_id not in defs.MENU:
            raise serializers.ValidationError("不明なメニューID menu=%s" % (menu_id))

        return menu_id


    def validate_permission_type_id(self, permission_type_id):

        if permission_type_id not in self.PERM_TYPE_LIST:
            raise serializers.ValidationError("不明な権限種別 perm_type=%s" % (permission_type_id))

        return permission_type_id


