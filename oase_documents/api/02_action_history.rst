=================================
2 アクション履歴
=================================

| 本章では、RestAPI機能を用いてアクション履歴を取得するために
| 必要なパラメータなどについて説明します。


2.1 リクエストの形式 
=====================

下記の情報で HTTPS リクエストを発行します。


2.1.1 リクエスト例
-------------------

**例）プロダクション適用ルール**

::

 curl -X GET -k "https://<HostName>/oase_web/restapi/actionhistory/historyrequest" -H "accept: application/json" -d "{\"traceid\":\"TOS_20210412053112220048_0000000010\"}"


2.1.2 リクエストヘッダ
---------------------------

.. csv-table:: 表 2.1.2 フォーマット定義
   :header: No.,  物理名,論理名, 備考
   :widths: 5, 20, 20, 40

   1, Host, ホスト名,
   2, Content-Type, 形式名,値は「application/json」で固定


2.1.3 パラメータ
--------------------------------------

.. csv-table:: 表 2.1.3 フォーマット定義
   :header: No,  物理名,論理名, 属性,長さ,空白
   :widths: 5, 20, 20,15,15,10

   1, traceid, トレースID,文字列,  55,不可


traceid
~~~~~~~~~~~~
取得したいアクション履歴に紐付くトレースIDを指定します。

**記述例**

::

 TOS_20210412053112220048_0000000010



2.2 レスポンスの形式 
=====================

下記の情報で 応答データを受け取ります。


2.2.1 レスポンス例
--------------------------------------

**例）ステージング適用ルール**
::

{"result": true, "msg": "Successful completion. (Staging environment)", "status": "処理済み(正常終了)"}


**例）プロダクション適用ルール**
::

 {"result": true, "msg": "Successful completion.", "action_history_list": [{"status": "処理済み(正常終了)", "rule_type_name": "ルール種別001", "rule_name": "rule01", "action_type_id": "ITA(ver1)", "last_update_timestamp": "2018/11/20 14:31", "last_update_user": "アクションドライバープロシージャ"}]}


2.2.2 ヘッダ
--------------------------------------


2.2.3 レスポンスボディ
--------------------------------------

| リクエストを投入し内容に問題が無い場合は 「"result": true」「"msg": "Successful completion."」となり、
| 以降に「どのようなステータス状況なのか」等の情報が表示されます。
| 内容に問題がある場合は「"result": false」となり、処理が受け付けられません。
| その場合は「"msg"」に記載の内容を確認し解消することでリクエストが受け付けられるようになります。

    
.. csv-table:: 表 2.2.3 フォーマット定義
   :header: No,  物理名,論理名
   :widths: 5, 30, 40

   1, result, 判定
   2, msg, メッセージ
   3, action_history_list,アクション履歴リスト
   4, status,ステータス
   5, rule_type_name,ルール種別名
   6, rule_name,ルール名
   7, action_type_id,アクション種別
   8, last_update_timestamp,最終更新日時
   9, last_update_user,最終更新者
   

result
~~~~~~~~~~
.. csv-table::
   :header: No,value,備考
   :widths: 5, 40,40

   1,true,正常
   2,false,異常


msg
~~~~~~
.. csv-table:: 
   :header: No,value,備考
   :widths: 5, 40,40

   1,Successful completion.,正常終了
   2,Successful completion. (Staging environment),正常終了（ステージング）
   3,Successful completion. (Production environment),正常終了(プロダクション)
   4,Invalid trace ID,無効なトレースIDです
   5,Invalid data.,無効なデータです。
   6,Invalid request. Must be GET. Not POST.,無効なリクエスト。 GETである必要があります。POSTではありません。
   7,Invalid request format. Must be JSON.,無効なリクエスト形式。 JSON形式である必要があります。
   8,ActionType does not exists.,存在しないアクションタイプです。
   9,Unexpected error.,予想外のエラーです。


action_history_list
~~~~~~~~~~~~~~~~~~~~~~~~~~~
リクエストしたトレースIDに対するアクション履歴の情報（status、rule_type_name、rule_name、action_type_id、last_update_timestamp、last_update_user）が記述されます。


status
~~~~~~~~~~~~
.. csv-table::
   :header: No,value,備考
   :widths: 5, 40,40

   1,未処理,
   2,処理中(データを取得開始),
   3,処理済み(正常終了),
   4,強制処理済み,何らかのエラーが発生し処理が終らない場合、「処理中」から「強制処理済み」に変更されます。 
   5,異常終了(サーバーエラー),このエラーとなった場合はアクション履歴画面の「アクション再実行ボタン」からの再実行はできません。
   6,承認待ち,
   7,処理済み,
   8,Exastroリクエスト,
   9,処理中(リトライ実行),
   10, アクション中断,
   11,アクション実行前エラー,
   12,アクション実行エラー,
   13,未実行,
   14,実行中,
   15,異常,
   16,取消,
   17,状態取得失敗,
   18,抑止済,
 


rule_type_name
~~~~~~~~~~~~~~~~~~~
ディシジョンテーブル画面で設定したルール種別が表示されます。

**記述例**

::

  ルール種別001



rule_name
~~~~~~~~~~~~
ディシジョンテーブルExcelファイルで設定したルール名が表示されます。
 
**記述例**

::

  rule01


action_type_id
~~~~~~~~~~~~~~~
.. csv-table::
   :header: No,value,備考
   :widths: 5, 20,60

   1,ITA,末尾にバージョン情報が表示されます。 例）ITA(ver1)
   2,メール,末尾にバージョン情報が表示されます。 例）mail(ver1)



last_update_timestamp
~~~~~~~~~~~~~~~~~~~~~~~~~
最終実行日時が表示されます。

**記述例**

::

  2018/11/20 14:31



last_update_user
~~~~~~~~~~~~~~~~~~~~~~
最終実行者が表示されます。

**記述例**

::

  アクションドライバープロシージャ

