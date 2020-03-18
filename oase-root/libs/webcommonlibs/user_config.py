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
  ユーザー設定情報を保持する

[引数]


[戻り値]


"""




from django.urls import reverse
from django.db import transaction
from libs.commonlibs import define as defs
from libs.commonlibs.oase_logger import OaseLogger
from libs.webcommonlibs.sys_config import *
from web_app.templatetags.common import get_message
from web_app.models.models import AccessPermission, UserGroup, System, User, RuleType


logger = OaseLogger.get_instance() # ロガー初期化


class UserConfig(object):

    """
    [クラス概要]
      ユーザの個人設定情報を管理する
    """

    class AccessPermission(object):

        """
        [クラス概要]
          ユーザのアクセス権限を管理する
        """

        # アクセス権限種別の優劣を定義
        PERM_PRIORITY = {
            defs.ALLOWED_MENTENANCE : 100,
            defs.VIEW_ONLY          :  50,
            defs.NO_AUTHORIZATION   :   0,
        }


        def __init__(self, user_name, group_id_list, user_id, lang):
            """
            [メソッド概要]
              初期化処理
            [引数]
              group_id_list : ユーザが所属するグループ一覧
            """

            self.user_name = user_name
            self.user_id = user_id
            self.lang_mode = lang
            self.group_id_list = group_id_list
            self.perm_info = {}
            self.perm_info_by_rule = {}
            self.load(group_id_list)


        def load(self, group_id_list):
            """
            [メソッド概要]
              アクセス権限読み込み
            [引数]
              group_id_list : ユーザが所属するグループ一覧
            """

            # 各メニューのアクセス権限種別をセット
            rs = AccessPermission.objects.filter(group_id__in=group_id_list).values('menu_id', 'rule_type_id', 'permission_type_id')
            for r in rs:
                menu_id   = r['menu_id']
                rule_type = r['rule_type_id']
                perm_type = r['permission_type_id']

                # アクセス権限種別がセットされていないメニューは、取得した値をそのままセット
                if menu_id not in self.perm_info:
                    self.perm_info[menu_id] = perm_type

                # アクセス権限種別がセット済みのメニューは、優劣にしたがって値をセット
                else:
                    self.perm_info[menu_id] = self.compare_priority(perm_type, self.perm_info[menu_id])

                # ルールカテゴリーのメニューは、ルール種別ごとにアクセス権限を設定する
                if menu_id in defs.MENU_BY_RULE and rule_type > 0:
                    if menu_id not in self.perm_info_by_rule:
                        self.perm_info_by_rule[menu_id] = {}
                        self.perm_info_by_rule[menu_id][defs.NO_AUTHORIZATION]   = []
                        self.perm_info_by_rule[menu_id][defs.VIEW_ONLY]          = []
                        self.perm_info_by_rule[menu_id][defs.ALLOWED_MENTENANCE] = []

                    # ルール種別が既にセット済みの場合は、そのアクセス権限種別を取得
                    perm_tmp = None
                    for k in self.PERM_PRIORITY.keys():
                        if rule_type in self.perm_info_by_rule[menu_id][k]:
                            perm_tmp = k
                            break

                    # 初出のルール種別の場合は、そのまま値をセット
                    if perm_tmp is None:
                        self.perm_info_by_rule[menu_id][perm_type].append(rule_type)

                    # 既存のルール種別の場合は、優劣にしたがって値をセット
                    else:
                        perm_key = self.compare_priority(perm_type, perm_tmp)
                        if perm_key != perm_tmp:
                            self.perm_info_by_rule[menu_id][perm_tmp].remove(rule_type)
                            self.perm_info_by_rule[menu_id][perm_key].append(rule_type)


        def get_mainmenu_info(self):
            """
            [メソッド概要]
              メニューバーの表示情報を取得する
            [戻り値]
              list : 各メニューの表示情報リスト
            """

            ret_list = []

            # ユーザのアクセス権限種別に応じて、表示するメニュー情報を作成
            for categ_info in defs.MENU_CATEGORY.CATEGORY_LIST:
                item_list = []

                # カテゴリー別に各メニューのアクセス権限種別をチェック
                for menu_id in categ_info['item_list']:
                    # 不明なメニューは無視する
                    if menu_id not in defs.MENU_CATEGORY.MENU_ITEM_URL:
                        logger.system_log('LOSM13014', menu_id)
                        continue

                    menu_ids = [menu_id, ] if menu_id not in defs.MENU_CATEGORY.MENU_ITEM_FRAME else defs.MENU_CATEGORY.MENU_ITEM_FRAME[menu_id]
                    # メニュー存在チェック
                    for mid in menu_ids:
                        if mid not in defs.MENU:
                            logger.system_log('LOSM13014', mid)
                            continue

                    # メニューに対するユーザのアクセス権限種別を取得
                    perm_type = defs.NO_AUTHORIZATION
                    for mid in menu_ids:
                        if mid in self.perm_info:
                            perm_type = self.compare_priority(perm_type, self.perm_info[mid])

                    # AD連携しているか確認
                    ad_collabo = System.objects.get(config_id="ADCOLLABORATION").value

                    # アクセス権限があれば表示対象とする
                    # アカウントロックページはシステム設定の条件を満たすユーザのみ表示
                    if menu_id in [2141003002, 2141003005, 2141003006]:
                        # administratorに権限付与
                        if self.user_id == 1:

                            # AD連携時はアカウントロックページは表示しない
                            if ad_collabo == "1" and menu_id == 2141003002:
                                 continue

                            item_list.append(menu_id)

                        else:
                            # メール通知種別の値をセット 0 or 1 or 2
                            notification_type = int(System.objects.get(config_id="NOTIFICATION_DESTINATION_TYPE").value)

                            # [1] administrator + ユーザ権限を持つグループに表示
                            if notification_type == 1:
                                # ユーザ権限を持つユーザに画面表示権限付与
                                if self.user_id in get_userid_at_user_auth():
                                    # AD連携時はアカウントロックページは表示しない
                                    if ad_collabo == "1" and menu_id == 2141003002:
                                        continue

                                    item_list.append(menu_id)

                            # [2] administrator + 指定されたloginIDのユーザ
                            # 指定されたloginIDの属するグループにアカウントロック画面への権限付与
                            elif notification_type == 2:
                                #ユーザごとにアカウントロックメニューの表示権限付与
                                if self.user_id in get_lock_auth_user():
                                    # AD連携時はアカウントロックページは表示しない
                                    if ad_collabo == "1" and menu_id == 2141003002:
                                        continue

                                    item_list.append(menu_id)


                    elif menu_id in [2141003003, 2141003004]:
                        item_list.append(menu_id)

                    # アカウントロックページ以外は権限があれば付与
                    elif perm_type > 0 and perm_type != defs.NO_AUTHORIZATION:
                        item_list.append(menu_id)

                # 表示するメニューが存在 or CATEGORY_LISTのdefaultフラグがTrue メニュー情報をセット
                if len(item_list) > 0 or categ_info['default'] :
                    ret_info  = {}

                    # カテゴリー情報をセット
                    ret_info['caption']    = get_message(categ_info['name'], self.lang_mode, showMsgId=False)
                    # リンク情報セット:メールアドレス or リンクなし
                    if categ_info['link'] == '#':
                        ret_info['link']   = categ_info['link']
                    # djangoの形式でリンクセット
                    else :
                        ret_info['link']   = reverse(categ_info['link'])
                    ret_info['classname']  = categ_info['classname']
                    ret_info['menu_items'] = []
                    ret_info['selected']   = categ_info['selected']
                    ret_info['default']   = categ_info['default']


                    # カテゴリーに紐づくメニュー情報をセット
                    for i in item_list:
                        ret_info['menu_items'].append(
                          {
                            'name' : get_message(defs.MENU_CATEGORY.MENU_ITEM_URL[i]['name'], self.lang_mode, showMsgId=False),
                            'link' : reverse(defs.MENU_CATEGORY.MENU_ITEM_URL[i]['url']),
                          }
                        )

                    ret_list.append(ret_info)

            return ret_list


        def compare_priority(self, perm1, perm2):
            """
            [メソッド概要]
              アクセス権限種別の優先度を比較する
            [引数]
              perm1 : int 比較する権限種別その１
              perm2 : int 比較する権限種別その２
            [戻り値]
              int : 優先度が高いほうの権限種別
            """

            perm_priority1 = self.PERM_PRIORITY[perm1] if perm1 in self.PERM_PRIORITY else self.PERM_PRIORITY[defs.NO_AUTHORIZATION]
            perm_priority2 = self.PERM_PRIORITY[perm2] if perm2 in self.PERM_PRIORITY else self.PERM_PRIORITY[defs.NO_AUTHORIZATION]

            if perm_priority1 > perm_priority2:
                return perm1

            return perm2


    def __init__(self, user):
        """
        [メソッド概要]
          初期化処理
        [引数]
          user : ユーザ情報オブジェクト
        """

        # ユーザの所属するグループから、アクセス権限を設定する
        self.group_id_list = list(UserGroup.objects.filter(user_id=user.user_id).values_list('group_id', flat=True))
        self.cls_access_permission = self.AccessPermission(user.user_name, self.group_id_list, user.pk, user.get_lang_mode())


    def get_menu_auth_type(self, menu_id, rule_type_id=0):
        """
        [メソッド概要]
          指定のメニューIDに対するユーザのアクセス権限種別を取得する
        [引数]
          menu_id : 権限チェック対象のメニューID
        [戻り値]
          int     : アクセス権限種別(※ libs/commonlibs/define.py の PERMISSION_TYPE_ID を参照)
        """

        if not isinstance(menu_id, list):
            menu_id = [menu_id, ]

        auth_type = defs.NO_AUTHORIZATION
        for mid in menu_id:
            mid = int(mid)

            # ルール指定なしの権限を取得
            if mid not in defs.MENU_BY_RULE or rule_type_id <= 0:
                if mid in self.cls_access_permission.perm_info:
                    auth_type = self.cls_access_permission.compare_priority(auth_type, self.cls_access_permission.perm_info[mid])

            # ルール種別ごとの権限を取得
            else:
                admin_group_ids      = set([1, ])  # 1=システム管理者グループ
                user_group_ids       = set(self.cls_access_permission.group_id_list)
                user_admin_group_ids = list(user_group_ids & admin_group_ids)

                # システム管理者の場合は、全てのルールにアクセス可能
                if len(user_admin_group_ids) > 0:
                    auth_type = defs.ALLOWED_MENTENANCE

                # ユーザーの所属グループに応じた権限を取得
                else:
                    for mid in menu_id:
                        mid = int(mid)
                        if mid in self.cls_access_permission.perm_info_by_rule:
                            if rule_type_id in self.cls_access_permission.perm_info_by_rule[mid][defs.NO_AUTHORIZATION]:
                                auth_type = self.cls_access_permission.compare_priority(auth_type, defs.NO_AUTHORIZATION)

                            elif rule_type_id in self.cls_access_permission.perm_info_by_rule[mid][defs.VIEW_ONLY]:
                                auth_type = self.cls_access_permission.compare_priority(auth_type, defs.VIEW_ONLY)

                            elif rule_type_id in self.cls_access_permission.perm_info_by_rule[mid][defs.ALLOWED_MENTENANCE]:
                                auth_type = self.cls_access_permission.compare_priority(auth_type, defs.ALLOWED_MENTENANCE)

        return auth_type


    def get_rule_auth_type(self, menu_id, auth_type=None):
        """
        [メソッド概要]
          指定のメニューIDに対するユーザのアクセス権限種別ごとのルール種別IDを取得する
        [引数]
          menu_id   : 権限チェック対象のメニューID
          auth_type : 取得対象のアクセス権限種別
        [戻り値]
          list      : 指定のアクセス権限種別にひもづくルール種別IDリスト
          dict      : アクセス権限種別(※ libs/commonlibs/define.py の PERMISSION_TYPE_ID を参照)にひもづくルール種別IDリスト
        """

        auth_type_info = {
            defs.NO_AUTHORIZATION   : [],
            defs.VIEW_ONLY          : [],
            defs.ALLOWED_MENTENANCE : [],
        }

        # ユーザーの所属に応じた権限をセット
        if menu_id in defs.MENU_BY_RULE and menu_id in self.cls_access_permission.perm_info_by_rule:
            user_group_ids = set(self.cls_access_permission.group_id_list)
            auth_type_info[defs.NO_AUTHORIZATION].extend(self.cls_access_permission.perm_info_by_rule[menu_id][defs.NO_AUTHORIZATION])
            auth_type_info[defs.VIEW_ONLY].extend(self.cls_access_permission.perm_info_by_rule[menu_id][defs.VIEW_ONLY])
            auth_type_info[defs.ALLOWED_MENTENANCE].extend(self.cls_access_permission.perm_info_by_rule[menu_id][defs.ALLOWED_MENTENANCE])

        if auth_type in auth_type_info:
            return auth_type_info[auth_type]

        return auth_type_info


    def get_activerule_auth_type(self, menu_id, auth_type=None):
        """
        [メソッド概要]
          指定のメニューIDに対するユーザのアクセス権限種別ごとのルール種別IDを取得する(廃止ルール除く)
        [引数]
          menu_id   : 権限チェック対象のメニューID
          auth_type : 取得対象のアクセス権限種別
        [戻り値]
          list      : 指定のアクセス権限種別にひもづくルール種別IDリスト
          dict      : アクセス権限種別(※ libs/commonlibs/define.py の PERMISSION_TYPE_ID を参照)にひもづくルール種別IDリスト
        """

        auth_type_info = {
            defs.NO_AUTHORIZATION   : [],
            defs.VIEW_ONLY          : [],
            defs.ALLOWED_MENTENANCE : [],
        }
        
        # 有効なルールを全て取得
        ruletypeset = set(RuleType.objects.filter(disuse_flag='0').values_list('pk', flat=True))

        # ユーザーの所属に応じた権限をセット
        if menu_id in defs.MENU_BY_RULE and menu_id in self.cls_access_permission.perm_info_by_rule:
            no_auth = set(self.cls_access_permission.perm_info_by_rule[menu_id][defs.NO_AUTHORIZATION])
            view_only = set(self.cls_access_permission.perm_info_by_rule[menu_id][defs.VIEW_ONLY])
            _all = set(self.cls_access_permission.perm_info_by_rule[menu_id][defs.ALLOWED_MENTENANCE])

            auth_type_info[defs.NO_AUTHORIZATION].extend(list(ruletypeset & no_auth))
            auth_type_info[defs.VIEW_ONLY].extend(list(ruletypeset & view_only))
            auth_type_info[defs.ALLOWED_MENTENANCE].extend(list(ruletypeset & _all))

        if auth_type in auth_type_info:
            return auth_type_info[auth_type]

        return auth_type_info


    def get_menu_list(self):
        """
        [メソッド概要]
          ユーザのアクセス権限に基づき、表示するメニュー情報を取得する
        [戻り値]
          list : 各メニューの表示情報リスト
        """

        return self.cls_access_permission.get_mainmenu_info()

