=================================
1 イベントリクエスト
=================================

| 本章では、ルール画面で設定したルールに対して、
| RestAPI機能を用いたリクエストを行うために必要なパラメータなどについて説明します。


1.1 リクエストの形式
=====================

下記の情報で HTTPS リクエストを発行します。


1.1.1 リクエスト例
-----------------------

**例）プロダクション適用ルール**

::

 curl -X POST -k "https://<HostName>/oase_web/event/event/eventsrequest" -H "accept: application/json" -d "{\"decisiontable\":\"decisiontable001\",\"requesttype\":\"1\",\"eventdatetime\":\"2018/12/13 15:16:29\",\"eventinfo\":[\"2\",\"あああ\"]}" -H "Authorization: Bearer ACCESS_TOKEN"



1.1.2 リクエストヘッダ
--------------------------

.. csv-table:: 表 1.1.2 フォーマット定義
   :header: No.,  物理名,論理名, 備考
   :widths: 5, 20, 20, 40

   1, Host, ホスト名,
   2, Content-Type, 形式名,値は「application/json」で固定
   3, token, トークン,Token払い出し画面にて取得した値を設定

1.1.3 パラメータ
--------------------------------------
    
.. csv-table:: 表 1.1.3 フォーマット定義
   :header: No,  物理名,論理名, 属性,長さ,空白
   :widths: 5, 20, 20,15,15,10

   1, decisiontable, ディシジョンテーブル名,文字列, 64, 不可
   2, requesttype, リクエスト種別,文字列,  11,不可
   3, eventdatetime, イベント発生日時,文字列,19, 不可
   4, eventinfo, イベント情報,リスト,4000 ,不可



decisiontable
~~~~~~~~~~~~~

ディシジョンテーブル画面で作成したディシジョンテーブル名を記述することができます。

**記述例**

:: 

 decisiontable001

requesttype
~~~~~~~~~~~~

投入先である「1:プロダクション」「2:ステージング」のどちらかを記述します。

**記述例**

::

 1

eventdatetime
~~~~~~~~~~~~~~~

「yyyy/mm/dd hh:mm:ss」または、イベント発生日時を指定しない場合「-」のどちらかを記述します。

**記述例**

::

 2018/12/13 15:16:29

eventinfo
~~~~~~~~~~~~

ディシジョンテーブルで作成したルール条件の数値や、文字列を記述することができます。複数ある時はカンマ区切りで記述します。

**記述例**

::

 [\"2\",\"あああ\"]



1.2 レスポンスの形式 
=====================

下記の情報で 応答データを受け取ります。


1.2.1 レスポンス例
--------------------------------------

**例）プロダクション適用ルール**

::

 {"result": true, "msg": "Accept request.", "trace_id": "TOS_20210412053112220048_0000000010"} 



1.2.2 ヘッダ
--------------------------------------

1.2.3 レスポンスボディ
--------------------------------------

| リクエストを投入し内容に問題が無い場合は、「"result": true」「"msg": "Accept request."」となり、
| 末尾に受け付けられたリクエストのイベントシリアルNo.が表示されます。
| 内容に問題がある場合は「"result": false」となり、処理が受け付けられません。
| その場合は「"msg"」に記載の内容を確認し解消することでリクエストが受け付けられるようになります。

    
.. csv-table:: 表 1.2.1 フォーマット定義
   :header: No,  物理名,論理名
   :widths: 5, 30, 40

   1, result, 判定
   2, msg, メッセージ
   3, trace_id,イベントシリアルNo.


result
~~~~~~~~

.. csv-table:: 
   :header: No,value,備考
   :widths: 5, 40,40

   1,true,正常
   2,false,異常

msg
~~~~~~~~
.. csv-table:: 
   :header: No,value,備考
   :widths: 5, 40,40

   1,Accept request.,リクエストを受け付けます。
   2,"Unmatch, Number of event information elements.",イベント情報の要素の数が不一致です。
   3,Invalid request. Must be POST. Not GET.,無効なリクエスト。 POSTである必要があります。GETではありません。
   4,Invalid request format. Must be JSON.,無効なリクエスト形式。 JSON形式である必要があります。 
   5,Invalid request type.,無効なリクエストの種類です
   6,Invalid request., 無効なリクエストです。
   7,Unexpected error.,予想外のエラーです。
   8,other error.,その他エラーです。
