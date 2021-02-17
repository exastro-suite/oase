
import pytest
import unittest
from django.urls import reverse
from web_app.models.models import System
from web_app.templatetags.common import get_message
from web_app.models.models import Menu
from libs.commonlibs import define as defs
@pytest.mark.django_db
class TestSsoInfoIndex(object):
    """
    web_app/views/system/sso_info.pyのテストクラス一覧表示
    """
    def test_index_ok(self, admin):
        """
        正常系
        """
        response = admin.get(reverse('web_app:system:sso_info'))
        content = response.content.decode('utf-8')
        assert response.status_code == 200
    def test_index_ng(self,admin):
        """
        異常系
        """
        with pytest.raises(Exception):
            response = admin.get(reverse('web_app:system:sso_info'))
            assert response.status_code == 404

