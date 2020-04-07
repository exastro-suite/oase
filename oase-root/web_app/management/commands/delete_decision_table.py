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
  
"""

from django.core.management.base import BaseCommand
from backyards.apply_driver.oase_apply import delete as apply_delete
from web_app.models.models import RuleType


class Command(BaseCommand):

    help = 'ディシジョンテーブル全削除'

    def __init__(self):

        pass


    def handle(self, *args, **options):

        uid = 1

        rule_type_ids = RuleType.objects.filter(disuse_flag='0').values_list('rule_type_id', flat=True)
        for rid in rule_type_ids:
            req_info = {}
            req_info['user_id']    = uid
            req_info['ruletypeid'] = rid

            apply_delete(req_info)


