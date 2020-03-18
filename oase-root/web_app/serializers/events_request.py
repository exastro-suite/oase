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

import json

from rest_framework import serializers

from web_app.models.models import EventsRequest
from libs.commonlibs import define as defs


class EventsRequestSerializer(serializers.ModelSerializer):

    TRACE_ID_LENGTH   = 55
    REQUEST_TYPE_LIST = [defs.PRODUCTION, defs.STAGING, ]
    EVENT_INFO_KEY    = 'EVENT_INFO'

    class Meta:
        model = EventsRequest
        fields = (
            'trace_id', 'request_type_id', 'rule_type_id',
            'request_reception_time', 'request_user', 'request_server',
            'event_to_time', 'event_info', 'status', 'status_update_id',
            'last_update_timestamp', 'last_update_user'
        )


    def validate_trace_id(self, trace_id):

        trace_len = len(trace_id)
        if trace_len != self.TRACE_ID_LENGTH:
            raise serializers.ValidationError("トレースID不正 trace_id=%s, req_len=%s, valid_len=%s" % (trace_id, trace_len, self.TRACE_ID_LENGTH))

        return trace_id


    def validate_request_type_id(self, request_type_id):

        req_type = int(request_type_id)
        if req_type not in self.REQUEST_TYPE_LIST:
            raise serializers.ValidationError("不明なリクエスト種別 req_type=%s" % (request_type_id))

        return request_type_id


    def validate_event_info(self, event_info):

        value = event_info
        if isinstance(value, str) == False:
            raise serializers.ValidationError("文字列ではありません val=%s, type=%s" % (value, type(value)))

        try:
            value = json.loads(value)
        except:
            raise serializers.ValidationError("JSON形式ではありません val=%s" % (value))

        if isinstance(value, dict) == False:
            raise serializers.ValidationError("JSON形式ではありません val=%s" % (value))

        if self.EVENT_INFO_KEY not in value:
            raise serializers.ValidationError("必要なキーが存在しません json=%s, valid_key=%s" % (value, self.EVENT_INFO_KEY))

        value = value[self.EVENT_INFO_KEY]
        if isinstance(value, list) == False:
            raise serializers.ValidationError("イベント情報が配列ではありません val=%s, type=%s" % (value, type(value)))


        return event_info


