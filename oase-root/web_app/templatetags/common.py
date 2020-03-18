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

from django import template
register = template.Library()

from django.db.models.query import QuerySet
from libs.messages.oase_messageid import OASEMessageID

class SetVarNode(template.Node):

    def __init__(self, var_name, var_value):
        self.var_name = var_name
        self.var_value = var_value

    def render(self, context):
        try:
            value = template.Variable(self.var_value).resolve(context)
        except template.VariableDoesNotExist:
            value = ""
        context[self.var_name] = value

        return u""


@register.tag(name='set')
def set_var(parser, token):
    """
      {% set some_var = '123' %}
    """
    parts = token.split_contents()
    if len(parts) < 4:
        raise template.TemplateSyntaxError("'set' tag must be of the form: {% set <var_name> = <var_value> %}")

    return SetVarNode(parts[1], parts[3])


@register.filter
def search_red(text, hit_list):
    """フィルタ検索で、ヒットした文字を赤くする"""

    if len(hit_list) <= 0:
        return text

    hit_list.sort(key=lambda x:len(x), reverse=True)

    for hit in hit_list:
        if hit in text:
            red_tag  = '<span style="color:red;">%s</span>' % (hit)
            text = text.replace(hit, red_tag, 1)
            break

    return text

@register.filter
def ellipsis(text, disp_len):
    """文字数が長い場合ピリオド3つで省略表示する"""

    suffix  = '...'
    end_pos = disp_len - len(suffix)

    if len(text) >= disp_len:
        text = text[0:end_pos] + suffix

    return text


@register.simple_tag
def get_message(msgid, *args, **kwargs):

    msg = ''

    for a in args:
        if a in ["JA", "EN"]:
            msgid = change_lang(msgid, a, 4)

    if msgid in OASEMessageID.Ary:
        msg = ('%s' % (OASEMessageID.Ary[msgid]))
    else:
        # ID見つからないとき処理終了
        return '[ %s ] not found.' % msgid

    if len(kwargs) > 0:
        msg = msg % (kwargs)

    """
    for k, v in kwargs.items():
        msg += (' %s=%s' % (k, v))
    """

    if 'showMsgId' in kwargs and kwargs['showMsgId'] == False:
        pass
    else:
        msg += (' (%s)' % (msgid))

    return msg


@register.filter
def newline_to_br(value):
    """\nを</br>に置換する"""
    return value.replace('\n', '</br>')


def change_lang(msgid, lang, sindex):

    if sindex < 0:
        return msgid

    eindex = sindex + len(lang) - 1
    if len(msgid) < eindex:
        return msgid

    msgid = list(msgid)
    for i, ch in enumerate(list(lang)):
        msgid[sindex + i - 1] = ch

    msgid = "".join(msgid)

    return msgid

@register.filter
def index(list_, i):
    """リストの要素をindexを指定して取得する"""
    return list_[int(i)]


@register.filter
def change_datestyle(changetime, lang):
    """言語によって表示方法を変える"""
    if lang == "EN":
        datetime = changetime.strftime('%Y, %m, %d, %H:%M')
    elif lang =="JA":
        datetime = changetime.strftime(u'%Y年 %m月 %d日 %H:%M')
    return datetime

@register.filter( is_safe=True )
def jsonify(object):

    if isinstance(object, QuerySet):
        return serialize('json', object)
    return json.dumps(object)
