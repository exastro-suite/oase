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
from django import forms


class ItaParameterMatchInfoForm(forms.Form):
    """
    ITAパラメータ抽出条件の入力チェック
    """
    ita_driver_id_errors = {
        'required': 'MOSJA27315',
    }
    menu_id_errors = {
        'required': 'MOSJA27317',
    }
    parameter_name_errors = {
        'required': 'MOSJA27318',
        'max_length': 'MOSJA27319',
    }
    order_errors = {
        'required': 'MOSJA27320',
    }
    conditional_name_errors = {
        'required': 'MOSJA27321',
        'max_length': 'MOSJA27322',
    }
    extraction_method1_errors = {
        'max_length': 'MOSJA27323',
    }
    extraction_method2_errors = {
        'max_length': 'MOSJA27324',
    }

    ita_driver_id = forms.IntegerField(required=True, error_messages=ita_driver_id_errors)
    menu_id = forms.IntegerField(required=True, error_messages=menu_id_errors)
    parameter_name = forms.CharField(max_length=256, required=True, error_messages=parameter_name_errors)
    order = forms.IntegerField(required=True, error_messages=order_errors)
    conditional_name = forms.CharField(max_length=32, required=True, error_messages=conditional_name_errors)
    extraction_method1 = forms.CharField(max_length=512, required=False, error_messages=extraction_method1_errors)
    extraction_method2 = forms.CharField(max_length=512, required=False, error_messages=extraction_method2_errors)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_ita_driver_id(self):
        ita_driver_id = self.cleaned_data['ita_driver_id']

        return ita_driver_id

    def clean_menu_id(self):
        menu_id = self.cleaned_data['menu_id']

        return menu_id

    def clean_parameter_name(self):
        parameter_name = self.cleaned_data['parameter_name']

        return parameter_name

    def clean_order(self):
        order = self.cleaned_data['order']

        return order

    def clean_conditional_name(self):
        conditional_name = self.cleaned_data['conditional_name']

        return conditional_name

    def clean_extraction_method1(self):
        extraction_method1 = self.cleaned_data['extraction_method1']

        return extraction_method1

    def clean_extraction_method2(self):
        extraction_method2 = self.cleaned_data['extraction_method2']

        return extraction_method2

