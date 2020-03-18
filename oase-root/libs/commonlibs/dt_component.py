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
    ディシジョンテーブルに関連する各種要素のクラス
"""

import os
import shutil
import re
import xlrd
import traceback
import datetime
import xml.etree.ElementTree as ET
from importlib import import_module
from django.conf import settings
from libs.commonlibs.oase_logger import OaseLogger
from libs.webcommonlibs.oase_exception import OASEError
from web_app.models.models import System, DataObject, RuleType, ActionType, DriverType
from web_app.templatetags.common import get_message
logger = OaseLogger.get_instance()


class DecisionTableComponent(object):

    """
    [クラス概要]
      ディシジョンテーブルの部品を取り扱う
    """

    ############################################
    # 定数定義
    ############################################
    # ルールテーブル名が記述されたExcelのセル番号
    ROW_INDEX_TABLENAME = 6
    COL_INDEX_TABLENAME = 2

    # ユーザー入力禁止範囲のセル番号
    ROW_INDEX_HEADER_START = 1
    COL_INDEX_HEADER_START = 1
    ROW_INDEX_HEADER_END   = 10

    # ユーザー入力開始セル番号
    ROW_INDEX_RULE_START = 11
    COL_INDEX_RULE_START = 2

    # アクション部のカラム
    ACTION_COLUMN_COUNT               = 8  # アクション部のカラム数(必須項目)
    ACTION_COLUMN_COUNT_FULL          = ACTION_COLUMN_COUNT + 2  # アクション部のカラム数(有効日無効日含む)
    REVISION_COL_INDEX_ACTION_TYPE    = 1   # アクション種別のカラム補正値
    REVISION_COL_INDEX_ACTION_PARAMS  = 2   # アクションパラメーターのカラム補正値
    REVISION_COL_INDEX_PREACT_INFO    = 3   # 事前アクション情報のカラム補正値
    REVISION_COL_INDEX_RETRY_INTERVAL = 4   # リトライ間隔のカラム補正値
    REVISION_COL_INDEX_RETRY_MAX      = 5   # リトライ回数のカラム補正値
    REVISION_COL_INDEX_BREAK_INTERVAL = 6   # 抑止間隔のカラム補正値
    REVISION_COL_INDEX_BREAK_MAX      = 7   # 抑止回数のカラム補正値

    # Excelのセル種別
    CELL_TYPE_EMPTY  = 0
    CELL_TYPE_TEXT   = 1
    CELL_TYPE_NUMBER = 2
    CELL_TYPE_DATE   = 3

    def __init__(self, table_name):
        """
        [メソッド概要]
          初期化処理
        [引数]
          table_name : str ルールテーブル名
        """

        # ルール種別
        self.rule_type_id = 0  # ルール種別ID

        # データオブジェクト
        self.data_object_list = []  # データオブジェクト一覧

        # 各種ID、名前を設定
        self._table_name = table_name   # ルールテーブル名
        self._group_id = 'com.oase'     # グループID:固定値
        self._artifact_id = table_name  # アーティファクトID
        self._fact_name = 'RuleTable %s' % table_name           # ファクト変数名
        self._rule_set = '%s.%s' % (self.group_id, table_name)  # ルールセット、名前空間(java)
        self._contid_stg = 'test%s' % table_name                # コンテナID接頭辞(ステージング)
        self._contid_prd = 'prod%s' % table_name                # コンテナID接頭辞(プロダクション)
        self._class_name = '%sObject' % table_name              # javaクラス名
        self._java_file = '%s.java' % self.class_name           # javaファイル名

        # 各種パスを初期化
        self.src_path = ''      # 部品コピー元パス
        self.root_path = ''     # ルール作成ルートパス
        self.pom_path = ''      # pom.xml作成パス
        self.java_path = ''     # javaファイル作成パス
        self.kmodule_path = ''  # kmodule.xmlコピー先パス
        self.dtable_path = ''   # ディシジョンテーブルExcelファイル作成パス
        self.maven_path = ''    # Maven Repositoryパス
        self.oase_path = ''     # SetClock.xmls設置パス

    @property
    def table_name(self):
        """
        [メソッド概要]
          ルールテーブル名取得
        [戻り値]
          str : ルールテーブル名
        """

        return self._table_name

    @property
    def group_id(self):
        """
        [メソッド概要]
          グループID取得
        [戻り値]
          str : グループID
        """

        return self._group_id

    @property
    def artifact_id(self):
        """
        [メソッド概要]
          アーティファクトID取得
        [戻り値]
          str : アーティファクトID
        """

        return self._artifact_id

    @property
    def fact_name(self):
        """
        [メソッド概要]
          ファクト変数名取得
        [戻り値]
          str : ファクト変数名
        """

        return self._fact_name

    @property
    def rule_set(self):
        """
        [メソッド概要]
          ルールセット名取得
        [戻り値]
          str : ルールセット名
        """

        return self._rule_set

    @property
    def contid_stg(self):
        """
        [メソッド概要]
          コンテナID接頭辞(ステージング)取得
        [戻り値]
          str : コンテナID接頭辞(ステージング)
        """

        return self._contid_stg

    @property
    def contid_prd(self):
        """
        [メソッド概要]
          コンテナID接頭辞(プロダクション)取得
        [戻り値]
          str : コンテナID接頭辞(プロダクション)
        """

        return self._contid_prd

    @property
    def class_name(self):
        """
        [メソッド概要]
          javaクラス名取得
        [戻り値]
          str : javaクラス名
        """

        return self._class_name

    @property
    def java_file(self):
        """
        [メソッド概要]
          javaファイル名取得
        [戻り値]
          str : javaファイル名
        """

        return self._java_file

    def get_dtable_path(self):
        """
        [メソッド概要]
          Excelのファイルパス取得
        [戻り値]
          str : Excelのファイルパス
        """

        return self.dtable_path

    def get_pom_path(self):
        """
        [メソッド概要]
          pom.xmlのファイルパス取得
        [戻り値]
          str : pom.xmlのファイルパス
        """

        return self.pom_path

    @classmethod
    def get_tablename_by_excel(cls, excel_path):
        """
        [メソッド概要]
          指定のExcelに記述されたルールテーブル名を取得する
        [引数]
          excel_path : str Excelのファイルパス
        [戻り値]
          str : ルールテーブル名
        """

        table_name = ''

        # 指定のExcelファイルが存在しない場合は処理を中断
        if not os.path.exists(excel_path):
            logger.logic_log('LOSM12057', excel_path)
            return 1, 'MOSJA03007'  # error_flag = 1, error_msg = MOSJA03007

        # Excelからルールテーブル名を取得
        try:
            wbook = xlrd.open_workbook(excel_path)
        except Exception as e:
            return 1, 'MOSJA03005'  # error_flag = 1, error_msg = MOSJA03005

        wsheet = wbook.sheet_by_index(0)
        table_name = wsheet.cell_value(cls.ROW_INDEX_TABLENAME, cls.COL_INDEX_TABLENAME)
        table_name = table_name.split(" ")
        table_name = table_name[-1]

        return 0, table_name

    def set_rule_type_id(self, id=0, table_name=''):
        """
        [メソッド概要]
          ルール種別IDの設定
        [引数]
          id         : int 設定するルール種別ID
          table_name : str 設定するルール種別IDの抽出条件となるテーブル名
        """

        # 無指定の場合は、テーブル名から取得するよう設定
        if not id and not table_name:
            table_name = self.table_name

        # 指定のIDをルール種別IDとして設定
        self.rule_type_id = id

        # ルールテーブル名が指定された場合は、DBから該当のルール種別IDを抽出
        if id == 0 and table_name:
            try:
                self.rule_type_id = RuleType.objects.get(rule_table_name=table_name).rule_type_id

            except RuleType.DoesNotExist:
                logger.logic_log('LOSM12055', table_name)

    def load_data_object(self):
        """
        [メソッド概要]
          データオブジェクトをDBから取得
        """

        # ルール種別IDが未設定の場合は、ルールテーブル名からIDを取得する
        if self.rule_type_id == 0:
            self.set_rule_type_id()

        # データオブジェクトを抽出
        self.data_object_list = list(
            DataObject.objects.filter(
                rule_type_id=self.rule_type_id).order_by('data_object_id').values(
                'label', 'conditional_name', 'conditional_expression_id'))

    def set_path(self, src_path='', root_path='', maven_path=''):
        """
        [メソッド概要]
          各種パスの設定
        [引数]
          src_path  : str 部品のコピー元パス
          root_path : str 部品の作成先ルートパス
        """

        # 部品コピー元の指定がない場合は、システム設定から取得
        if not src_path:
            src_path = System.objects.get(config_id='RULEFILE_SRCPATH').value
            src_path = '%s%s' % (settings.BASE_DIR, src_path)

        # ルール作成先ルートパスの指定がない場合は、システム設定から取得
        if not root_path:
            root_path = System.objects.get(config_id='RULEFILE_ROOTPATH').value
            if not root_path.endswith('/'):
                root_path = '%s/' % (root_path)

            root_path = '%s%s/' % (root_path, self.rule_type_id)

        # MavenRepositoryパスの指定がない場合は、システム設定から取得
        if not maven_path:
            maven_path = System.objects.get(config_id='MAVENREP_PATH').value
            if not maven_path.endswith('/'):
                maven_path = '%s/' % (maven_path)

            maven_path = '%s%s/' % (maven_path, self.table_name)

        # 各種パスを設定
        self.src_path = src_path
        self.root_path = root_path
        self.pom_path = '%sorigin/' % (self.root_path)
        self.java_path = '%ssrc/main/java/' % (self.pom_path)
        for g in self.group_id.split('.'):
            self.java_path = '%s%s/' % (self.java_path, g)
        self.kmodule_path = '%ssrc/main/resources/META-INF/' % (self.pom_path)
        self.oase_path = self.pom_path + 'src/main/resources/com/oase/'
        self.dtable_path = self.oase_path + self.table_name + '/'
        self.maven_path = maven_path

    def make_rule_dir(self, force_create=True):
        """
        [メソッド概要]
          ディジョンテーブルのディレクトリ作成
        [引数]
          force_create: root_pathが重複する場合にdel->createとするか
        """

        # 作成パスが既に存在していた場合、既存のディレクトリは削除する
        if os.path.exists(self.root_path) and force_create:
            shutil.rmtree(self.root_path)

        # 各種ディレクトリ作成
        os.makedirs(self.root_path, exist_ok=False)    # 作成先ルートパス
        os.makedirs(self.pom_path, exist_ok=True)      # pom.xml設置パス
        os.makedirs(self.java_path, exist_ok=True)     # *.java設置パス
        os.makedirs(self.kmodule_path, exist_ok=True)  # kmodule.xml設置パス
        os.makedirs(self.dtable_path, exist_ok=True)   # ディシジョンテーブルExcel設置パス

    def copy_tree(self, dstpath):
        """
        [メソッド概要]
          DTに必要な部品ファイルをコピー元から対象ルールへコピーする
        """
        dst_java_path = dstpath + 'src/main/java/'
        dst_meta_path = dstpath + 'src/main/resources/META-INF/'
        dst_oase_path = dstpath + 'src/main/resources/com/oase/'

        os.makedirs(dstpath, exist_ok=True)
        os.makedirs(dst_java_path, exist_ok=True)
        os.makedirs(dst_meta_path, exist_ok=True)
        os.makedirs(dst_oase_path, exist_ok=True)

        self.copy_component(self.pom_path, dstpath, 'pom.xml')
        self.copy_component(self.java_path, dst_java_path, 'OaseActionUtility.java')
        self.copy_component(self.java_path, dst_java_path, '%sObject.java' % self.table_name)
        self.copy_component(self.kmodule_path, dst_meta_path, 'kmodule.xml')
        self.copy_component(self.oase_path, dst_oase_path, 'setClock.xlsx')

    def copy_component(self, src_path, dst_path, filename, dst_file=''):
        """
        [メソッド概要]
          DTに必要な部品ファイルをコピー元から対象ルール種別へコピーする
        """

        if not dst_file:
            dst_file = filename

        # パスが未設定の場合は、パスを設定する
        if not src_path or not dst_path:
            self.set_path()

        # コピー先パスが存在しない場合は、ディレクトリを作成する
        if not os.path.exists(dst_path):
            self.make_rule_dir()

        # ファイルをコピー
        src_filepath = '%s%s' % (src_path, filename)
        dst_filepath = '%s%s' % (dst_path, dst_file)
        shutil.copy(src_filepath, dst_filepath)

    def copy_component_all(self):
        """
        [メソッド概要]
          DTに必要な部品ファイルをコピー元から対象ルール種別ディレクトリへ全てコピーする
        """

        self.copy_component(self.src_path, self.pom_path, 'pom.xml')
        self.copy_component(self.src_path, self.java_path, 'OaseActionUtility.java')
        self.copy_component(self.src_path, self.java_path, 'TableNameObject.java', self.java_file)
        self.copy_component(self.src_path, self.kmodule_path, 'kmodule.xml')
        self.copy_component(self.src_path, self.oase_path, 'setClock.xlsx')

    def edit_action_java(self):
        """
        [メソッド概要]
          DataObjectアクション部の編集を行う
        """

        # 編集対象のファイルが存在しない場合は、処理を中断する
        filepath = '%sOaseActionUtility.java' % (self.java_path)
        if not os.path.exists(filepath):
            logger.logic_log('LOSM12056', filepath)

        # ファイル編集
        regex_package = r'package.*'
        with open(filepath, 'r+') as fp:
            act_java = fp.read()
            act_java = re.sub(regex_package, 'package %s;' % (self.rule_set), act_java, 1)
            fp.seek(0)
            fp.write(act_java)
            fp.truncate()

    def edit_condition_java(self):
        """
        [メソッド概要]
          DataObject条件部の編集を行う
        """

        # 編集対象のファイルが存在しない場合は、処理を中断する
        filepath = '%s%s' % (self.java_path, self.java_file)
        if not os.path.exists(filepath):
            logger.logic_log('LOSM12056', filepath)

        ##############################################
        # ファイル編集
        #   変更が必要な箇所を置換することで編集を実現
        ##############################################
        # 置換前のプレースホルダーを設定
        regex_list = []
        regex_list.append('{{rule_set}}')
        regex_list.append('{{class_name}}')
        regex_list.append('{{declare_label}}')
        regex_list.append('{{getter_setter}}')
        regex_list.append('{{constructor}}')

        # 置換後の文字列を設定
        repl_list = []
        repl_list.append(self.rule_set)
        repl_list.append(self.class_name)
        repl_list.append(self.get_declare_string())
        repl_list.append(self.get_getter_setter_string())
        repl_list.append(self.get_constructor_string())

        # ファイル編集
        with open(filepath, 'r+') as fp:
            cond_java = fp.read()
            for reg, rep in zip(regex_list, repl_list):
                cond_java = re.sub(reg, rep, cond_java)
            fp.seek(0)
            fp.write(cond_java)
            fp.truncate()

    def get_declare_string(self):
        """
        [メソッド概要]
          DataObject条件クラスのメンバ変数宣言を文字列として取得
        [戻り値]
          str : メンバ変数宣言文
        """

        ret_str = ''

        # データオブジェクトを身取得の場合は、DBから抽出
        if len(self.data_object_list) <= 0:
            self.load_data_object()

        # 設定されたラベルの数だけ変数を宣言する
        labelList = []
        for dobj in self.data_object_list:
            if not dobj['label'] in labelList:
                var_name = dobj['label']
                cond_id = dobj['conditional_expression_id']
                type_name = self.get_type_by_condition(cond_id)

                ret_str = "%s    private %s %s;\n" % (ret_str, type_name, var_name)
                labelList.append(dobj['label'])

        return ret_str

    def get_getter_setter_string(self):
        """
        [メソッド概要]
          DataObject条件クラスのメンバ変数のgetter,setter処理を文字列として取得
        [戻り値]
          str : メンバ変数のgetter,setter関数文
        """

        ret_str = ''

        # データオブジェクトを身取得の場合は、DBから抽出
        if len(self.data_object_list) <= 0:
            self.load_data_object()

        # 設定されたラベルの数だけgetter, setterを作成する
        labelList = []
        for dobj in self.data_object_list:
            if not dobj['label'] in labelList:
                var_name = dobj['label']
                cond_id = dobj['conditional_expression_id']
                type_name = self.get_type_by_condition(cond_id)

                # 関数名がキャメル形式のため、変数名の先頭文字を大文字に変換
                var_name_list = list(var_name)
                var_name_list[0] = var_name_list[0].upper()
                func_name = "".join(var_name_list)

                # getter関数文を作成
                ret_str = "%s    public %s get%s() {\n" \
                          "        return this.%s;\n" \
                          "    }\n\n" % (ret_str, type_name, func_name, var_name)

                # setter関数文を作成
                ret_str = "%s    public void set%s(%s %s) {\n" \
                          "        this.%s = %s;\n" \
                          "    }\n\n" % (ret_str, func_name, type_name, var_name, var_name, var_name)
                labelList.append(dobj['label'])

        return ret_str

    def get_constructor_string(self):
        """
        [メソッド概要]
          DataObject条件クラスのコンストラクタ処理を文字列として取得
        [戻り値]
          str : コンストラクタ文
        """

        ret_str = '    public %s(' % (self.class_name)

        # データオブジェクトを身取得の場合は、DBから抽出
        if len(self.data_object_list) <= 0:
            self.load_data_object()

        # 設定されたラベルの数だけコンストラクタのパラメーターを設定する
        labelList = []
        for dobj in self.data_object_list:
            if not dobj['label'] in labelList:
                var_name = dobj['label']
                cond_id = dobj['conditional_expression_id']
                type_name = self.get_type_by_condition(cond_id)

                ret_str = "%s%s %s, " % (ret_str, type_name, var_name)
                labelList.append(dobj['label'])

        # アクション部クラスをコンストラクタのパラメーターに設定する
        ret_str = "%s%s.OaseActionUtility acts) {\n" % (ret_str, self.rule_set)

        # 設定されたラベルをコンストラクタ内で初期化する文を作成する
        labelList = []
        for dobj in self.data_object_list:
            if not dobj['label'] in labelList:
                var_name = dobj['label']
                ret_str = "%s        this.%s = %s;\n" % (ret_str, var_name, var_name)
                labelList.append(dobj['label'])

        ret_str = "%s        this.acts = acts;\n" % (ret_str)
        ret_str = "%s    }\n\n" % (ret_str)

        return ret_str

    def get_type_by_condition(self, cond_id):
        """
        [メソッド概要]
          DataObject条件IDに応じた型名を取得する
        [戻り値]
          str : メンバ変数の型
        """

        ret_str = ""

        if cond_id in [1, 2, 5, 6, 7, 8]:
            ret_str = "java.lang.Integer"

        elif cond_id in [3, 4, 9, 10, 15]:
            ret_str = "java.lang.String"

        elif cond_id in [13, 14]:
            ret_str = "java.util.List<java.lang.String>"

        return ret_str

    def edit_kmodule(self):
        """
        [概要]
        kmodule.xmlのpackagesをset
        packages="com.oase, com.oase.ルールテーブル名 "
        """
        # xmlファイル読み込み
        kmodule_path = self.kmodule_path + 'kmodule.xml'
        tree = ET.parse(kmodule_path)

        ET.register_namespace('', 'http://www.drools.org/xsd/kmodule')

        # packagesをセット
        root = tree.getroot()
        root[0].attrib['packages'] = '{0}, {0}.{1}'.format(self._group_id, self.table_name)

        # 上書き保存
        tree.write(kmodule_path, 'utf-8', True)

    def make_component_all(self, id=0):
        """
        [メソッド概要]
          ディシジョンテーブルの部品を全て作成する
        """

        self.set_rule_type_id(id)   # ルール種別IDを設定
        self.set_path()             # ディシジョンテーブル関連のディレクトリ名を設定
        self.make_rule_dir(force_create=False)  # ディシジョンテーブル部品設置ディレクトリを作成
        self.copy_component_all()   # ディシジョンテーブルに必要な部品をコピー
        self.edit_kmodule()
        self.edit_action_java()     # アクション部javaファイルを編集
        self.edit_condition_java()  # 条件部javaファイルを編集

    def remove_component(self, id):
        """
        [メソッド概要]
          指定のルール種別ディレクトリを削除する
        """

        self.set_rule_type_id(id)
        self.set_path()
        if os.path.exists(self.root_path):
            shutil.rmtree(self.root_path)

    def remove_component_related_one_file(self, dst_path):
        """
        [メソッド概要]
          指定のディレクトリを削除する(ルール種別, ルールファイルで決まるパス)
        """

        if os.path.exists(dst_path):
            shutil.rmtree(dst_path)

    def remove_mavenrepository(self):
        """
        [メソッド概要]
          指定のMavenRepositoryを削除する
        """

        self.set_path()
        if os.path.exists(self.maven_path):
            shutil.rmtree(self.maven_path)

    def remove_mavenrepository_related_one_file(self, rule_file_id):
        """
        [メソッド概要]
          指定のMavenRepositoryを削除する(ルールファイルID指定)
        """

        self.set_path()
        if os.path.exists(self.maven_path):
            related_file = os.path.join(self.maven_path, str(rule_file_id))
            if os.path.exists(related_file):
                shutil.rmtree(related_file)

    def check_decision_table_file(self, dt_filepath, lang):
        """
        [メソッド概要]
          ディシジョンテーブルファイルの内容をチェックする
        """

        message_list = []

        # 指定のディシジョンテーブルファイルが存在しない場合は処理を中断
        if not os.path.exists(dt_filepath):
            logger.logic_log('LOSM12057', dt_filepath)
            message_list.append(get_message('MOSJA03120', lang))
            return message_list

        ########################################
        # チェック処理
        ########################################
        try:
            # ファイルオープン
            wbook = xlrd.open_workbook(dt_filepath)
            wsheet = wbook.sheet_by_index(0)

            # データオブジェクトからアクション部の開始列を取得
            cond_col_cnt = 0
            if len(self.data_object_list) <= 0:
                self.load_data_object()

            for dobj in self.data_object_list:
                cond_col_cnt += 1
                # 15:時刻の"From"と"To"で2カラム分を計上
                if dobj['conditional_expression_id'] == 15:
                    cond_col_cnt += 1

            # チェック対象の範囲を設定
            row_index = self.ROW_INDEX_RULE_START
            row_max = self.ROW_INDEX_RULE_START
            row_rule_cnt = 0
            col_index = self.COL_INDEX_RULE_START
            col_index_act = self.COL_INDEX_RULE_START + cond_col_cnt
            col_max = self.COL_INDEX_RULE_START + cond_col_cnt + self.ACTION_COLUMN_COUNT
            date_effective_col_index = col_max
            date_expires_col_index = date_effective_col_index + 1

            if col_max > wsheet.ncols:
                message_list.append(get_message('MOSJA03109', lang))
                raise OASEError()

            # ルール上限数取得
            rule_row_max = int(System.objects.get(config_id='RULE_ROW_MAX').value)

            for row in range(row_index, wsheet.nrows):
                for col in range(col_index, col_max):
                    if wsheet.cell_type(row, col) == self.CELL_TYPE_EMPTY:
                        continue

                    if wsheet.cell_type(row, col) == self.CELL_TYPE_TEXT \
                            and wsheet.cell(row, col).value == '':
                        continue

                    row_max = row + 1
                    row_rule_cnt += 1
                    break

                else:
                    break

                # ルール上限数チェック
                if row_rule_cnt > rule_row_max:
                    message_list.append(get_message('MOSJA03122', lang, rulerowmax=rule_row_max))
                    break

            # 修正不可領域のチェック
            if wsheet.ncols > self.COL_INDEX_RULE_START + cond_col_cnt + self.ACTION_COLUMN_COUNT_FULL:
                cellname = self.convert_colno_to_colname(
                    self.COL_INDEX_RULE_START + cond_col_cnt + self.ACTION_COLUMN_COUNT_FULL - 1)
                message_list.append(get_message('MOSJA03128', lang, cellname=cellname))

            # 修正禁止項目チェック
            self.check_header_part(wsheet, message_list, lang)  # オリジナルとの差分チェック

            # 条件部 入力チェック
            self.check_condition_part(wsheet, row_index, col_index, row_max, col_index_act, message_list, lang)

            # アクション部チェック
            col_max_required  = self.COL_INDEX_RULE_START + cond_col_cnt + self.ACTION_COLUMN_COUNT
            self.check_action_part(wsheet, row_index, col_index_act, row_max, col_max_required, message_list, lang)
            self.check_retry_part(wsheet, row_index, col_index_act, row_max, message_list, lang)
            self.check_break_part(wsheet, row_index, col_index_act, row_max, message_list, lang)
            self.check_rule_name(wsheet, row_index, col_index_act, row_max, message_list, lang)
            self.check_action_type_and_param(wsheet, row_index, col_index_act, row_max, message_list, lang)
            self.check_pre_action(wsheet, row_index, col_index_act, row_max, message_list, lang)

            # 有効日無効日チェック
            self.check_date_effective(wsheet, row_index, date_effective_col_index, row_max, message_list, lang)
            self.check_date_expires(wsheet, row_index, date_expires_col_index, row_max, message_list, lang)

        except OASEError as e:
            if e.msg_id:
                if e.arg_dict:
                    message_list.append(get_message(e.msg_id, lang, e.arg_dict))

                else:
                    message_list.append(get_message(e.msg_id, lang))

        except Exception as e:
            message_list.append(get_message('MOSJA03120', lang))
            logger.system_log('LOSM00001', traceback.format_exc())

        # message_listから None を除去したもの返す
        return [m for m in message_list if m]

    def check_header_part(self, wsheet, message_list, lang):
        """
        [メソッド概要]
          修正禁止項目のチェック
        """

        # ファイルオープン
        org_filepath = '%s%s.xlsx' % (self.dtable_path, self.table_name)

        wb_org = xlrd.open_workbook(org_filepath)
        ws_org = wb_org.sheet_by_index(0)

        # オリジナルファイルとの比較
        row_index = self.ROW_INDEX_HEADER_START
        col_index = self.COL_INDEX_HEADER_START
        row_max   = self.ROW_INDEX_HEADER_END
        col_max   = min(ws_org.ncols, wsheet.ncols)

        for row in range(row_index, row_max):
            for col in range(col_index, col_max):
                if ws_org.cell_type(row, col)  != wsheet.cell_type(row, col) \
                        or ws_org.cell(row, col).value != wsheet.cell(row, col).value:
                    cellname = self.convert_rowcol_to_cellno(row, col)
                    message_list.append(get_message('MOSJA03107', lang, cellname=cellname))

    def check_condition_part(self, wsheet, row_index, col_index, row_max, col_max, message_list, lang):
        """
        [メソッド概要]
          条件部の入力チェック
        """
        for row in range(row_index, row_max):
            col = col_index
            index = 0
            data_obj_len = len(self.data_object_list)

            if self.is_all_blank_condition(wsheet, row, col_index, col_max):
                msg = get_message('MOSJA03138', lang, row=row + 1)
                message_list.append(msg)
                continue

            while col < col_max:
                if index >= data_obj_len:
                    continue

                msg = None
                cond_id = self.data_object_list[index]['conditional_expression_id']

                # 時刻条件
                if cond_id == 15:
                    # from check
                    cell_val = wsheet.cell(row, col).value
                    cell_type = wsheet.cell_type(row, col)
                    cellname = self.convert_rowcol_to_cellno(row, col)
                    msg = self.check_time_condition(cell_val, cell_type, cellname, lang)
                    message_list.append(msg)

                    # to check
                    col += 1
                    cell_val = wsheet.cell(row, col).value
                    cell_type = wsheet.cell_type(row, col)
                    cellname = self.convert_rowcol_to_cellno(row, col)
                    msg = self.check_time_condition(cell_val, cell_type, cellname, lang)
                    message_list.append(msg)

                # 数値条件
                elif cond_id in [1, 2, 5, 6, 7, 8]:
                    cell_val = wsheet.cell(row, col).value
                    cell_type = wsheet.cell_type(row, col)
                    cellname = self.convert_rowcol_to_cellno(row, col)
                    colname = get_message('MOSJA03131', lang, showMsgId=False)

                    msg = self.check_number_condition(cell_val, cell_type, cellname, colname, lang)
                    message_list.append(msg)

                col += 1
                index += 1

    def is_all_blank_condition(self, wsheet, row, col_index, col_max):
        """
        条件部が全て空白か調べる。全て空白の場合はエラーメッセージを返す。
        全て空白でない場合はNoneを返す。
        """
        cell_types = [wsheet.cell_type(row, c) for c in range(col_index, col_max)]
        col_len = col_max - col_index
        return True if(cell_types.count(self.CELL_TYPE_EMPTY) == col_len) else False

    def check_time_condition(self, cell_val, cell_type, cellname, lang):
        """
        時刻条件のチェックを行う
        """
        hhmm_repatter = re.compile(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$')
        date_repatter = re.compile(r'^0\.[0-9]+$')
        msg = get_message('MOSJA03111', lang, cellname=cellname)

        if cell_type == self.CELL_TYPE_NUMBER:
            return msg

        elif cell_type == self.CELL_TYPE_TEXT:
            if not hhmm_repatter.match(cell_val):
                return msg

        elif cell_type == self.CELL_TYPE_DATE:
            cell_val = str(cell_val)
            if not date_repatter.match(cell_val):
                return msg

    def check_number_condition(self, cell_val, cell_type, cellname, colname, lang):
        """
        数値条件のチェックを行う
        """
        num_repatter = re.compile(r'^[0-9]+$')
        dec_repatter = re.compile(r'^[0-9]+[.]{1}0+$')
        msg = get_message('MOSJA03110', lang, colname=colname, cellname=cellname)
        if cell_type == self.CELL_TYPE_DATE:
            return msg
        elif cell_type == self.CELL_TYPE_TEXT:
            if not num_repatter.match(cell_val):
                return msg
        elif cell_type == self.CELL_TYPE_NUMBER:
            cell_val = str(cell_val)
            if not num_repatter.match(cell_val) and not dec_repatter.match(cell_val):
                return msg

    def check_action_part(self, wsheet, row_index, col_index, row_max, col_max, messages, lang):
        """
        [メソッド概要]
          アクション部の入力チェック
        """

        for row in range(row_index, row_max):
            for col in range(col_index, col_max):
                if wsheet.cell_type(row, col) == self.CELL_TYPE_EMPTY:
                    messages.append(get_message('MOSJA03108', lang, cellname=self.convert_rowcol_to_cellno(row, col)))

                if wsheet.cell_type(row, col) == self.CELL_TYPE_TEXT \
                        and wsheet.cell(row, col).value == '':
                    messages.append(get_message('MOSJA03108', lang, cellname=self.convert_rowcol_to_cellno(row, col)))

    def is_valid_number(self, cell_type, cell_val, accept0=True):
        """
        セルに入力された値が妥当かどうかチェックする
        """
        pattern = r'^(0|[1-9]\d*)$' if accept0 else r'^[1-9]\d*$'
        pattern2 = r'^(0|[1-9]\d*|[1-9]\d*[.]{1}0+)$' if accept0 else r'^([1-9]\d*|[1-9]\d*[.]{1}0+)$'

        result = not ((cell_type in [self.CELL_TYPE_DATE, self.CELL_TYPE_EMPTY])
                      or (cell_type == self.CELL_TYPE_TEXT and not re.match(pattern, cell_val))
                      or (cell_type == self.CELL_TYPE_NUMBER and not re.match(pattern2, cell_val)))
        return result

    def check_gt0(self, wsheet, row, col, col_name, message_list, lang):
        """
        入力項目が正の整数かチェックする
        不正の場合はエラーメッセージを追加する
        """

        cell_val = str(wsheet.cell(row, col).value)
        cellname = self.convert_rowcol_to_cellno(row, col)
        cell_type = wsheet.cell_type(row, col)

        if not self.is_valid_number(cell_type, cell_val, accept0=False):
            message_list.append(
                get_message('MOSJA03110', lang, colname=col_name, cellname=cellname)
            )

    def check_gte0(self, wsheet, row, col, col_name, message_list, lang):
        """
        入力項目が空欄か0以上の正数かチェックする
        """
        cell_val = str(wsheet.cell(row, col).value)
        cellname = self.convert_rowcol_to_cellno(row, col)
        cell_type = wsheet.cell_type(row, col)

        if not self.is_valid_number(cell_type, cell_val):
            message_list.append(
                get_message('MOSJA03110', lang, colname=col_name, cellname=cellname)
            )
            return False

        return True

    def check_retry_part(self, wsheet, row_index, col_index, row_max, message_list, lang):
        """
        リトライ回数、リトライ間隔の数値チェック
        """
        logger.logic_log('LOSI12014', row_index, col_index, row_max, message_list, lang)

        retry_interval_name = get_message('MOSJA03132', lang, showMsgId=False)
        retry_max_name = get_message('MOSJA03133', lang, showMsgId=False)
        retry_interval_col = col_index + self.REVISION_COL_INDEX_RETRY_INTERVAL
        retry_max_col = col_index + self.REVISION_COL_INDEX_RETRY_MAX

        for row in range(row_index, row_max):
            self.check_gt0(wsheet, row, retry_interval_col,
                           retry_interval_name, message_list, lang)

            self.check_gt0(wsheet, row, retry_max_col,
                           retry_max_name, message_list, lang)

    def check_break_part(self, wsheet, row_index, col_index, row_max, message_list, lang):
        """
          抑止回数、抑止間隔のチェック
        """

        logger.logic_log('LOSI12015', row_index, col_index, row_max, message_list, lang)
        interval_name = get_message('MOSJA03134', lang, showMsgId=False)
        max_name = get_message('MOSJA03135', lang, showMsgId=False)
        interval_col = col_index + self.REVISION_COL_INDEX_BREAK_INTERVAL
        max_col = col_index + self.REVISION_COL_INDEX_BREAK_MAX

        for row in range(row_index, row_max):
            result1 = self.check_gte0(wsheet, row, interval_col,
                                      interval_name, message_list, lang)

            result2 = self.check_gte0(wsheet, row, max_col,
                                      max_name, message_list, lang)

            if result1 and result2:
                interval_val = int(wsheet.cell(row, interval_col).value)
                max_val = int(wsheet.cell(row, max_col).value)
                self.check_use0(interval_val, max_val, row, interval_col,
                                max_name, message_list, lang)

    def check_use0(self, interval_val, max_val, row, col, col_name, message_list, lang):
        """
        抑止間隔、抑止回数のどちらかが0の場合はエラーとする(排他的論理和でチェック)
        エラーの場合抑止間隔、抑止回数のセルのエラーメッセージを追加する。
        抑止間隔、抑止回数が両方0または、1以上なら正常とする。
        """
        logger.logic_log('LOSI12016', interval_val, max_val, row, col, col_name)
        interval_bool = 1 if interval_val > 0 else 0
        max_bool = 1 if max_val > 0 else 0
        cellname1 = self.convert_rowcol_to_cellno(row, col)
        cellname2 = self.convert_rowcol_to_cellno(row, col + 1)

        if interval_bool ^ max_bool:
            message_list.extend([
                get_message('MOSJA03136', lang, colname=col_name, cellname=cellname1),
                get_message('MOSJA03136', lang, colname=col_name, cellname=cellname2),
            ])

    def check_rule_name(self, wsheet, row_index, col_index_act, row_max, message_list, lang):
        """
        [メソッド概要]
          ルール名のパラメーターチェック
        """

        for row in range(row_index, row_max):
            # ルール名長チェック
            rule_name = str(wsheet.cell(row, col_index_act).value)

            if len(rule_name) > 64:
                cellname = self.convert_rowcol_to_cellno(row, col_index_act)
                message_list.append(get_message('MOSJA03125', lang, cellname=cellname))
                continue

    def check_action_type_and_param(self, wsheet, row_index, col_index, row_max, message_list, lang):
        """
        [メソッド概要]
          アクション種別とそのパラメーターチェック
        """

        to_info = {}
        rset = []

        dti = list(ActionType.objects.filter(disuse_flag='0').values_list('driver_type_id', flat=True))
        rs = DriverType.objects.filter(driver_type_id__in=dti).values('name', 'driver_major_version')

        for r in rs:
            name_version = r['name'] + '(ver' + str(r['driver_major_version']) + ')'
            rset.append([r['name'], name_version])

        act_type_info = {r[1]: {'driver_name': r[0], 'driver_method': None} for r in rset}

        for row in range(row_index, row_max):
            # アクション種別をチェック
            col = col_index + self.REVISION_COL_INDEX_ACTION_TYPE
            act_type = str(wsheet.cell(row, col).value)
            if act_type not in act_type_info.keys():

                cellname = self.convert_rowcol_to_cellno(row, col)
                acttypes = list(act_type_info.keys())
                if len(act_type_info):
                    message_list.append(get_message('MOSJA03112', lang, acttypes=acttypes, cellname=cellname))
                else:
                    # アクション種別が1つもない場合
                    message_list.append(get_message('MOSJA03124', lang, acttypes=acttypes, cellname=cellname))
                continue

            # アクション種別ごとのドライバー登録情報をチェック
            col = col_index + self.REVISION_COL_INDEX_ACTION_PARAMS
            cell_values = str(wsheet.cell(row, col).value).split(',')

            # アクション種別ごとのパラメーターチェック
            drv_method = None
            if act_type_info[act_type]['driver_method']:
                drv_method = act_type_info[act_type]['driver_method']

            else:
                drv_module = import_module(
                    'libs.commonlibs.%s.%s_common' %
                    (act_type_info[act_type]['driver_name'],
                     act_type_info[act_type]['driver_name']))
                drv_method = getattr(drv_module, 'check_dt_action_params')
                act_type_info[act_type]['driver_method'] = drv_method

            conditional_names = {d['conditional_name'] for d in self.data_object_list}
            mosja_list = drv_method(cell_values, act_type_info[act_type], conditional_names,
                                    to_info=to_info, pre_flg=False)
            for mosja in mosja_list:
                cellname = self.convert_rowcol_to_cellno(row, col)
                if mosja['param'] is None:
                    message_list.append(get_message(mosja['id'], lang, cellname=cellname))

                else:
                    message_list.append(get_message(mosja['id'], lang, keyname=mosja['param'], cellname=cellname))

    def check_pre_action(self, wsheet, row_index, col_index, row_max, message_list, lang):
        """
        [メソッド概要]
          事前アクションのパラメーターチェック
        [引数]
        col_index: アクション部の開始カラム
        """

        to_info = {}
        act_type_info = {}
        act_type_info['mail(ver1)'] = {'driver_method': None}

        # todo 条件名のリストを取得

        for row in range(row_index, row_max):

            # 人的確認メールのドライバー登録情報をチェック
            col = col_index + self.REVISION_COL_INDEX_PREACT_INFO
            cell_values = str(wsheet.cell(row, col).value).split(',')
            if cell_values == ["X"] or cell_values == ["x"]:
                continue

            # アクション種別ごとのパラメーターチェック
            drv_method = None
            if act_type_info['mail(ver1)']['driver_method']:
                drv_method = act_type_info['mail(ver1)']['driver_method']

            else:
                drv_module = import_module('libs.commonlibs.%s.%s_common' % ('mail', 'mail'))
                drv_method = getattr(drv_module, 'check_dt_action_params')
                act_type_info['mail(ver1)']['driver_method'] = drv_method

            conditional_names = {d['conditional_name'] for d in self.data_object_list}
            mosja_list = drv_method(cell_values, act_type_info['mail(ver1)'],
                                    conditional_names, to_info=to_info, pre_flg=True)
            for mosja in mosja_list:
                cellname = self.convert_rowcol_to_cellno(row, col)
                if mosja['param'] is None:
                    message_list.append(get_message(mosja['id'], lang, cellname=cellname))
                else:
                    message_list.append(get_message(mosja['id'], lang, keyname=mosja['param'], cellname=cellname))

    def check_date_format(self, wsheet, row_index, col_index, row_max, message_list, msgid, lang):
        """
        [メソッド概要]
          有効日無効日の形式がyyyy-mm-dd hh:mmか空欄かチェック
        """
        format_ = '%Y-%m-%d %H:%M'
        for row in range(row_index, row_max):
            date_text = str(wsheet.cell(row, col_index).value)
            # 空欄は無視
            if not date_text:
                continue
            # yyyy-mm-dd hh:mm形式チェック
            try:
                date = datetime.datetime.strptime(date_text, format_).strftime(format_)
                # 0埋め出ない場合 ValueError
                if date != date_text:
                    raise ValueError
            except ValueError:
                message_list.append(get_message(msgid, lang, cellname=self.convert_rowcol_to_cellno(row, col_index)))

    def check_date_effective(self, wsheet, row_index, col_index, row_max, message_list, lang):
        """
        [メソッド概要]
          有効日チェック
        """
        self.check_date_format(wsheet, row_index, col_index, row_max, message_list, 'MOSJA03126', lang)

    def check_date_expires(self, wsheet, row_index, col_index, row_max, message_list, lang):
        """
        [メソッド概要]
          無効日チェック
        """
        self.check_date_format(wsheet, row_index, col_index, row_max, message_list, 'MOSJA03127', lang)

    @classmethod
    def convert_rowcol_to_cellno(self, row, col):
        """
        [メソッド概要]
          行番号、列番号をセル番号に変換
        """

        col_name = self.convert_colno_to_colname(col)
        cellno = '%s%s' % (col_name, row + 1)

        return cellno

    @classmethod
    def convert_colno_to_colname(self, col):
        """
        [メソッド概要]
          列番号を列名に変換
        """

        col_name = ''

        col_tmp = col
        col_list = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

        col_tmp, idx = divmod(col_tmp, 26)  # 26 : A-Z
        col_name = col_list[idx]
        while col_tmp > 0:
            col_tmp, idx = divmod(col_tmp - 1, 26)
            col_name = '%s%s' % (col_list[idx], col_name)

        return col_name
