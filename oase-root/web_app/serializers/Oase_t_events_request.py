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
from web_app.models.models import EventsRequest
from libs.commonlibs import define as defs
import json

class EventsRequestSerializer(serializers.ModelSerializer):

    TRACE_ID_LENGTH   = 40 
    REQUEST_TYPE_LIST = [defs.PRODUCTION, defs.STAGING, ]
    EVENT_INFO_KEY    = 'EVENT_INFO'
    EVENT_INFO_LENGTH = 5

    class Meta:
        model = EventsRequest
        fields = (
            'trace_id', 'request_type_id', 'rule_type_id',
            'request_reception_time', 'request_user', 'request_server',
            'event_to_time', 'event_info', 'status', 'status_update_id',
            'last_update_timestamp', 'last_update_user_id'
        )


    def validate_trace_id(self, trace_id):
        
        if len(trace_id) != self.TRACE_ID_LENGTH:
            raise serializers.ValidationError("トレースID不正 trace_id=%s, req_len=%s, valid_len=%s" % (trace_id, len(trace_id), self.TRACE_ID_LENGTH))

        return trace_id


    def validate_request_type_id(self, request_type_id):

        if request_type_id not in self.REQUEST_TYPE_LIST:
            raise serializers.ValidationError("不明なリクエスト種別 req_type=%s")

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
        return event_info

class OaseTEventsRequestSerializerForRestAPI(serializers.Serializer):

    # T_EVENTS_REQUEST のカラム
    REQUEST_ID                  = serializers.IntegerField(required=False)
    TRACE_ID                    = serializers.CharField(min_length=22, max_length=22)
    REQUEST_TYPE_ID             = serializers.IntegerField()
    RULE_TYPE_ID                = serializers.IntegerField()
    REQUEST_RECEPTION_TIME      = serializers.DateTimeField(input_formats=('%Y/%m/%d %H:%M:%S',))
    REQUEST_USER                = serializers.CharField(max_length=128)
    REQUEST_SERVER              = serializers.CharField(max_length=128)
    EVENT_TO_TIME               = serializers.DateTimeField(input_formats=('%Y/%m/%d %H:%M:%S',))
    EVENT_INFO                  = serializers.CharField(max_length=4000)
    STATUS                      = serializers.IntegerField()
    STATUS_UPDATE_ID            = serializers.CharField(max_length=15, allow_blank=True)
    LAST_UPDATE_OASE_USER_ID    = serializers.IntegerField()

    class Meta:
        fields = (
            'REQUEST_ID', 'TRACE_ID', 'REQUEST_TYPE_ID', 'RULE_TYPE_ID',
            'REQUEST_RECEPTION_TIME', 'REQUEST_USER', 'REQUEST_SERVER',
            'EVENT_TO_TIME', 'EVENT_INFO', 'STATUS', 'STATUS_UPDATE_ID', 'LAST_UPDATE_OASE_USER_ID'
        )

        fields_index = {
             2 : 'REQUEST_ID',
             3 : 'TRACE_ID',
             4 : 'REQUEST_TYPE_ID',
             5 : 'RULE_TYPE_ID',
             6 : 'REQUEST_RECEPTION_TIME',
             7 : 'REQUEST_USER',
             8 : 'REQUEST_SERVER',
             9 : 'EVENT_TO_TIME',
            10 : 'EVENT_INFO',
            11 : 'STATUS',
            12 : 'STATUS_UPDATE_ID',
            13 : 'LAST_UPDATE_OASE_USER_ID',
        }

    def __init__(self, data, evinfo_length=0):

        if evinfo_length > 0:
            self.evinfo_length = evinfo_length

        json_data = self.MakeJson(data)
        super(OaseTEventsRequestSerializerForRestAPI, self).__init__(data=json_data)

    def MakeJson(self, data):

        json_data = {}
        for k, v in data.items():
            if not k.isdecimal():
                continue

            if int(k) not in self.Meta.fields_index:
                continue

            key_name = self.Meta.fields_index[int(k)]
            json_data[key_name] = v

        return json_data


