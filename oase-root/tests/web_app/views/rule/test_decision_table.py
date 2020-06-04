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

import pytest
import datetime

from web_app.models.models import RuleType
from web_app.views.rule.decision_table import _select


@pytest.mark.django_db
class TestDecisionTableSelect:
    """
    decision_table._select テストクラス
    """

    def set_test_data(self):
        """
        テストデータの作成
        """

        RuleType(
            rule_type_id = 9999,
            rule_type_name = 'pytest_name',
            summary = None,
            rule_table_name = 'pytest_table',
            generation_limit = 5,
            group_id = 'pytest_com',
            artifact_id = 'pytest_oase',
            container_id_prefix_staging = 'test',
            container_id_prefix_product = 'prod',
            current_container_id_staging = None,
            current_container_id_product = None,
            label_count = 1,
            unknown_event_notification = '1',
            mail_address = 'pytest@pytest.com',
            disuse_flag = '0',
            last_update_timestamp = datetime.datetime(2020, 6, 4, 12, 0, 0, tzinfo=datetime.timezone.utc),
            last_update_user = 'pytest'
        ).save(force_insert=True)


    def del_test_data(self):
        """
        テストデータの削除
        """

        RuleType.objects.all().delete()


    def test_ok(self):
        """
        正常系
        """

        self.del_test_data()
        self.set_test_data()

        filter_info = {
            'rule_type_id': {'LIST': [9999, ]},
            'rule_type_name': {'LIKE': 'pytest_'},
            'label_count': {'END': '1'},
            'generation_limit': {'START': '4'},
            'last_update_timestamp': {'FROM': '2020-06-03', 'TO': '2020-06-05', }
        }

        table_list = _select(filter_info)

        assert len(table_list) == 1

        self.del_test_data()
