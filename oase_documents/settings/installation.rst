=================================
インストール手順
=================================

OASEのインストール手順を下記に示します。

.. note:: ディレクトリのパスは構築するOSによって「centos」を読み替えて作成してください。

1. 事前準備
-----------

1.1 ファイアーウォール停止
~~~~~~~~~~~~~~~~~~~~~~~~~~

・ステータス確認

.. code-block:: rst

 # systemctl status firewalld

★Active: activeの場合

.. code-block:: rst

 # systemctl stop firewalld
 # systemctl disable firewalld


1.2. SELinux無効化
~~~~~~~~~~~~~~~~~~

・ステータス確認

.. code-block:: rst

 # getenforce

★Enforcingの場合

.. code-block:: rst

 # vi /etc/sysconfig/selinux

.. code-block:: bash

 SELINUX=disabled

 ※ Enforcing から disabled へ変更

.. code-block:: rst
 
 # reboot

1.3. タイムゾーンを設定する
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: rst

 # timedatectl status 
 
.. code-block:: bash

 Time zone: Asia/Tokyo (JST, +0900)

★Time zone: Asia/Tokyo 以外の場合

.. code-block:: rst

 # timedatectl set-timezone Asia/Tokyo

1.4. 自分自身のホスト名について名前解決できること
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: rst

 # ping {自ホスト名}

.. code-block:: bash

 ping: {自ホスト名}: 名前またはサービスが不明です

| ★「名前またはサービスが不明です」となる場合
| 
| hostsで指定するなど、名前解決が可能な状態にすること

2. 汎用ツール追加
-----------------

.. note:: 後続の手順で必要になるツールを先にインストールしておく

2.1. wgetインストール
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: rst

 # yum list | grep wget

.. code-block:: bash

 wget.x86_64    1.14-18.el7_6.1    @updates

★インストールされていない場合

.. code-block:: rst

 # yum install -y wget

2.2. gccインストール
~~~~~~~~~~~~~~~~~~~~

.. code-block:: rst

 # yum list | grep gcc

.. code-block:: bash

 gcc.x86_64     4.8.5-36.el7_6.2    @updates

★インストールされていない場合

.. code-block:: rst

 # yum install -y gcc


3. 必須ソフトウェアインストール
-------------------------------

3.1 python v3.6 インストール
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

3.1.1. iusリポジトリの設定
**************************

| ※CentOS のより新しいバージョンのパッケージを提供。
| 1. リポジトリのダウンロード
| 以下のコマンドを実行し、２つrpmファイルを取得する

.. code-block:: rst

 # cd /tmp
 # wget --no-check-certificate https://centos7.iuscommunity.org/ius-release.rpm
 # wget --no-check-certificate https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm

| 2. iusリポジトリのインストール
| 以下のコマンドを実行し、iusリポジトリをインストールする

.. code-block:: rst

 # rpm -Uvh ius-release.rpm epel-release-latest-7.noarch.rpm

| 3. /etc/yum.repos.d/epel.repoの編集

.. code-block:: rst

 # cat /etc/yum.repos.d/epel.repo

.. code-block:: bash

 [epel]
 name=Extra Packages for Enterprise Linux 7 - $basearch
 baseurl=http://download.fedoraproject.org/pub/epel/7/$basearch
 #metalink=https://mirrors.fedoraproject.org/metalink?repo=epel-7&arch=$basearch
 failovermethod=priority
 enabled=1
 gpgcheck=1
 gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-7
 sslverify=0
 
 [epel-debuginfo]
 name=Extra Packages for Enterprise Linux 7 - $basearch - Debug
 #baseurl=http://download.fedoraproject.org/pub/epel/7/$basearch/debug
 metalink=https://mirrors.fedoraproject.org/metalink?repo=epel-debug-7&arch=$basearch
 failovermethod=priority
 enabled=0
 gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-7
 gpgcheck=1

 [epel-source]
 name=Extra Packages for Enterprise Linux 7 - $basearch - Source
 #baseurl=http://download.fedoraproject.org/pub/epel/7/SRPMS
 metalink=https://mirrors.fedoraproject.org/metalink?repo=epel-source-7&arch=$basearch
 failovermethod=priority
 enabled=0
 gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-7
 gpgcheck=1

| [epel]セクションの以下3点
| ・baseurlがコメントアウトされていないこと
| ・metalinkをコメントアウトしていること
| ・sslverify=0を設定していること

| ★上記以外の場合

.. code-block:: rst

 # cp /etc/yum.repos.d/epel.repo /etc/yum.repos.d/20190708_epel.repo
 # vi /etc/yum.repos.d/epel.repo

.. code-block:: bash

 [epel]
 name=Extra Packages for Enterprise Linux 7 - $basearch
 baseurl=http://download.fedoraproject.org/pub/epel/7/$basearch
 #metalink=https://mirrors.fedoraproject.org/metalink?repo=epel-7&arch=$basearch
 failovermethod=priority
 enabled=1
 gpgcheck=1
 gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-7
 sslverify=0

| [epel-debuginfo]、[epel-source]はenabled=0にする。
| 4. /etc/yum.repos.d/epel-testing.repoの編集

.. code-block:: rst

 # cat /etc/yum.repos.d/epel-testing.repo | grep enabled

.. code-block:: bash

 enabled=0
 enabled=0
 enabled=0

★enabled=0以外があった場合

.. code-block:: rst

 # cp /etc/yum.repos.d/epel-testing.repo /etc/yum.repos.d/20190708_epel-testing.repo
 # vi /etc/yum.repos.d/epel-testing.repo

| [epel-testing]、[epel-testing-debuginfo]、[epel-testing-source]セッション全てをenabled=0にする。
| 5. /etc/yum.repos.d/ius-archive.repoの編集

.. code-block:: rst

 # cat /etc/yum.repos.d/ius-archive.repo | grep enabled

.. code-block:: bash

 enabled=0
 enabled=0
 enabled=0

★enabled=0以外があった場合

.. code-block:: rst

 # cp /etc/yum.repos.d/ius-archive.repo /etc/yum.repos.d/20190708_ius-archive.repo
 # vi /etc/yum.repos.d/ius-archive.repo

| [ius-archive]、[ius-archive-debuginfo]、[ius-archive-source]セッション全てをenabled=0にする。
| 6. /etc/yum.repos.d/ius.repoの編集

.. code-block:: rst

 # cat /etc/yum.repos.d/ius.repo

.. code-block:: bash

 [ius]
 name = IUS for Enterprise Linux 7 - $basearch
 baseurl = https://repo.ius.io/7/$basearch/
 enabled = 1
 repo_gpgcheck = 0
 gpgcheck = 1
 gpgkey = file:///etc/pki/rpm-gpg/RPM-GPG-KEY-IUS-7
 sslverify=0

 [ius-debuginfo]
 name=IUS Community Packages for Enterprise Linux 7 - $basearch - Debug
 #baseurl=https://dl.iuscommunity.org/pub/ius/stable/CentOS/7/$basearch/debuginfo
 mirrorlist=https://mirrors.iuscommunity.org/mirrorlist?repo=ius-centos7-debuginfo&arch=$basearch&protocol=http
 failovermethod=priority
 enabled=0
 gpgcheck=1
 gpgkey=file:///etc/pki/rpm-gpg/IUS-COMMUNITY-GPG-KEY
 
 [ius-source]
 name=IUS Community Packages for Enterprise Linux 7 - $basearch - Source
 #baseurl=https://dl.iuscommunity.org/pub/ius/stable/CentOS/7/SRPMS
 mirrorlist=https://mirrors.iuscommunity.org/mirrorlist?repo=ius-centos7-source&arch=source&protocol=http
 failovermethod=priority
 enabled=0
 gpgcheck=1
 gpgkey=file:///etc/pki/rpm-gpg/IUS-COMMUNITY-GPG-KEY

★上記以外の場合

.. code-block:: rst

 # cp /etc/yum.repos.d/ius.repo /etc/yum.repos.d/20190708_ius.repo
 # vi /etc/yum.repos.d/ius.repo

| [ius]セッションをenabled=1に、それ以外のセッション全てをenabled=0にする。
| [ius]セッションにsslverify=0を付与する。
| 7. /etc/yum.repos.d/ius-testing.repo の編集

.. code-block:: rst

 # cat /etc/yum.repos.d/ius-testing.repo | grep enabled

.. code-block:: bash

 enabled=0
 enabled=0
 enabled=0

★enabled=0以外があった場合

.. code-block:: rst

 # cp /etc/yum.repos.d/ius-testing.repo /etc/yum.repos.d/20190708_ius-testing.repo
 # vi /etc/yum.repos.d/ius-testing.repo

| [ius-testing]、[ius-testing-debuginfo]、[ius-testing-source]セッション全てをenabled=0にする。
| 8. yum clean allを実行

.. code-block:: rst

 # yum clean all

| 9. yum updateを実行

.. code-block:: rst

 # yum update
    ～省略～
    Is this ok [y/d/N]: y

.. code-block:: rst

 # yum repolist

.. code-block:: bash

  epel/x86_64
  ius/x86_64

が表示されることを確認する


3.1.2. python v3.6 インストール
*******************************

| 1. yum search python36 を実行し、以下の内容が表示がされること

.. code-block:: rst

 # yum search python36

.. code-block:: bash

 python36u.x86_64
 python36u-libs.x86_64
 python36u-devel.x86_64
 python36u-pip.noarch


| 2. 以下のコマンドを実行し、pythonをインストールする

.. code-block:: rst

 # yum -y install python36u python36u-libs  python36u-devel python36u-pip

| 3. リンクの設定
| 以下のコマンドでリンクを設定する

.. code-block:: rst

 # ls -l /bin/python*

.. code-block:: bash

 /bin/python -> python2

★/bin/python -> python2の場合

.. code-block:: rst

 # ln -s /bin/python3.6 /bin/python3
 # ln -sf /bin/python3 /bin/python
 # ls -l /bin/python*

.. code-block:: bash

 /bin/python -> /bin/python3

3.1.3. pipのバージョン更新
**************************

pip バージョン確認

.. code-block:: rst

 # python3 -m pip --version

.. code-block:: bash

 pip 19.1.1 from /usr/lib/python3.6/site-packages/pip (python 3.6)

★19.1.1でない場合

.. code-block:: rst

 # python3.6 -m pip install --upgrade pip

.. note:: ここから、pip3が実行できるようになる。

3.1.4. pika v1.1.0 インストール
*******************************

| 1. 以下のコマンドを実行し、pikaをインストールする

.. code-block:: rst

 # pip3 install pika

| 2. pip3 listを実行

.. code-block:: rst

 # pip3 list

.. code-block:: bash

     ～省略～
     pika 1.1.0

3.1.5. retry v0.9.2 インストール
********************************

| 1. 以下のコマンドを実行し、retryをインストールする

.. code-block:: rst

 # pip3 install retry

| 2. pip3 listを実行

.. code-block:: rst

 # pip3 list

.. code-block:: bash

     ～省略～
     retry 0.9.2

3.1.6. yumの実行バージョンは2.x系に戻す
***************************************

yum本体

.. code-block:: rst

 # cp /usr/bin/yum /usr/bin/20190708_yum
 # vi /usr/bin/yum

以下の修正をおこなう

.. code-block:: bash

 #!/usr/bin/python → #!/usr/bin/python2.7


利用ライブラリ

.. code-block:: rst

 # cp /usr/libexec/urlgrabber-ext-down /usr/libexec/20190708_urlgrabber-ext-down
 # vi /usr/libexec/urlgrabber-ext-down

以下の修正をおこなう

.. code-block:: bash

 #!/usr/bin/python → #!/usr/bin/python2.7


3.2. memcacheインストール
~~~~~~~~~~~~~~~~~~~~~~~~~

| 1. memcacheをインストールする

.. code-block:: rst

 # yum -y install memcached

| 2. memcacheを起動する。

.. code-block:: rst

 # systemctl status memcached
 # systemctl start memcached
 # systemctl enable memcached


3.3. RabbitMQ Serverインストール
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

| 1. EPELリポジトリからErlangをインストールする

.. code-block:: rst

 # yum install erlang

.. note:: インストールエラーになる場合、何度か実行すると成功します。

| 2. RabbitMQ Serverをインストールする

.. code-block:: rst

 # yum -y install rabbitmq-server --enablerepo=epel

.. note:: インストールエラーになる場合、何度か実行すると成功します。

| 3. rabbitmq_managementを追加する


| 3-1. プラグインリストの確認


.. code-block:: rst

 # rabbitmq-plugins list

.. code-block:: bash

 [ ] amqp_client                       3.3.5
 [ ] cowboy                            0.5.0-rmq3.3.5-git4b93c2d
 [ ] eldap                             3.3.5-gite309de4
 [ ] mochiweb                          2.7.0-rmq3.3.5-git680dba8
 [ ] rabbitmq_amqp1_0                  3.3.5
 [ ] rabbitmq_auth_backend_ldap        3.3.5
 [ ] rabbitmq_auth_mechanism_ssl       3.3.5
 [ ] rabbitmq_consistent_hash_exchange 3.3.5
 [ ] rabbitmq_federation               3.3.5
 [ ] rabbitmq_federation_management    3.3.5
 [ ] rabbitmq_management               3.3.5
 [ ] rabbitmq_management_agent         3.3.5
 [ ] rabbitmq_management_visualiser    3.3.5
 [ ] rabbitmq_mqtt                     3.3.5
 [ ] rabbitmq_shovel                   3.3.5
 [ ] rabbitmq_shovel_management        3.3.5
 [ ] rabbitmq_stomp                    3.3.5
 [ ] rabbitmq_test                     3.3.5
 [ ] rabbitmq_tracing                  3.3.5
 [ ] rabbitmq_web_dispatch             3.3.5
 [ ] rabbitmq_web_stomp                3.3.5
 [ ] rabbitmq_web_stomp_examples       3.3.5
 [ ] sockjs                            0.3.4-rmq3.3.5-git3132eb9
 [ ] webmachine                        1.10.3-rmq3.3.5-gite9359c7


| 3-2. rabbitmq_managementを追加

.. code-block:: rst

 # rabbitmq-plugins enable rabbitmq_management

| 3-3. プラグインリストの確認

.. code-block:: rst

 # rabbitmq-plugins list

.. code-block:: bash

 [e] amqp_client                       3.3.5
 [ ] cowboy                            0.5.0-rmq3.3.5-git4b93c2d
 [ ] eldap                             3.3.5-gite309de4
 [e] mochiweb                          2.7.0-rmq3.3.5-git680dba8
 [ ] rabbitmq_amqp1_0                  3.3.5
 [ ] rabbitmq_auth_backend_ldap        3.3.5
 [ ] rabbitmq_auth_mechanism_ssl       3.3.5
 [ ] rabbitmq_consistent_hash_exchange 3.3.5
 [ ] rabbitmq_federation               3.3.5
 [ ] rabbitmq_federation_management    3.3.5
 [E] rabbitmq_management               3.3.5
 [e] rabbitmq_management_agent         3.3.5
 [ ] rabbitmq_management_visualiser    3.3.5
 [ ] rabbitmq_mqtt                     3.3.5
 [ ] rabbitmq_shovel                   3.3.5
 [ ] rabbitmq_shovel_management        3.3.5
 [ ] rabbitmq_stomp                    3.3.5
 [ ] rabbitmq_test                     3.3.5
 [ ] rabbitmq_tracing                  3.3.5
 [e] rabbitmq_web_dispatch             3.3.5
 [ ] rabbitmq_web_stomp                3.3.5
 [ ] rabbitmq_web_stomp_examples       3.3.5
 [ ] sockjs                            0.3.4-rmq3.3.5-git3132eb9
 [e] webmachine                        1.10.3-rmq3.3.5-gite9359c7

| 4. rabbitmq-serverを起動する

.. code-block:: rst

 # systemctl start rabbitmq-server

| 5. rabbitmq-serverをサービス自動起動有効にする。

.. code-block:: rst

 # systemctl enable rabbitmq-server

| 6. ユーザの作成

.. code-block:: rst

 # rabbitmqctl add_user {RabbitMQユーザ名} {RabbitMQパスワード}

.. note:: RabbitMQユーザ名とRabbitMQパスワードは任意で設定して下さい。

| 7. ユーザの権限

.. code-block:: rst

 # rabbitmqctl set_user_tags {RabbitMQユーザ名} administrator

| 8. ユーザのパーミッション

.. code-block:: rst

 # rabbitmqctl set_permissions -p / {RabbitMQユーザ名} ".*" ".*" ".*"


3.4. MySQLインストール
~~~~~~~~~~~~~~~~~~~~~~

3.4.1. MySQL Serverインストール
*******************************

| 1. リポジトリの取得

.. code-block:: rst

 # cd /tmp
 # wget --no-check-certificate https://dev.mysql.com/get/mysql80-community-release-el7-3.noarch.rpm

| 2. リポジトリの設定

.. code-block:: rst

 # rpm -Uvh mysql80-community-release-el7-3.noarch.rpm

| 3. インストール

.. code-block:: rst

 # yum -y --enablerepo mysql80-community install mysql-server

| 4. 起動と初期パスワードの確認

.. code-block:: rst

 # systemctl status mysqld
 # systemctl start  mysqld
 # systemctl enable mysqld

/var/log/mysqld.logからパスワードを確認

.. code-block:: rst

 # grep -i password /var/log/mysqld.log

.. code-block:: bash

 2019-07-08T01:27:09.721259Z 5 [Note] [MY-010454] [Server] A temporary password is generated for root@localhost: {初期パスワード}
                                                                                                                 ^^^^^^^^^^^^^^^^

| 5. 初期パスワードの変更
| 以下のコマンドでMySQLに接続

.. code-block:: rst

 # mysql -u root -p

.. code-block:: bash

 Enter password: [5で確認したパスワードを入力]

.. tip:: 簡易なパスワードにする場合

.. code-block:: bash

 mysql> ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'passwordPASSWORD@999'; ※ 一時変更用パスワード

 ※一度パスワード変更しないと以降の設定変更ができない
 
 以下がパスワード難易度を下げる設定

 mysql> SET GLOBAL validate_password.length=4;
 mysql> SET GLOBAL validate_password.mixed_case_count=0;
 mysql> SET GLOBAL validate_password.number_count=0;
 mysql> SET GLOBAL validate_password.special_char_count=0;
 mysql> SET GLOBAL validate_password.policy=LOW;


| 設定状態確認

.. code-block:: bash


  mysql> show variables like '%validate_password%';

パスワード変更

.. code-block:: bash

  mysql> ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'hogehoge'; ※hogehoge ここに任意のパスワードを入れる

バージョン確認

.. code-block:: bash

 mysql> status


.. code-block:: bash

 mysql  Ver 8.0.16 for Linux on x86_64 (MySQL Community Server - GPL)

ログアウト

.. code-block:: bash

 mysql> quit

| 6. Mysqlユーザ作成

.. code-block:: rst

 # mysql -u root -phogehoge ※hogehoge 直前の手順で設定した初期パスワード

.. code-block:: bash

 mysql> CREATE DATABASE {データベース名} CHARACTER SET utf8;
 mysql> CREATE USER '{DBユーザ名}' IDENTIFIED BY '{DBパスワード}';
 mysql> GRANT ALL ON {データベース名}.* TO '{DBユーザ名}';

ログアウト

.. code-block:: bash

 mysql> quit


| 7. Mysqlの設定ファイルの変更

.. code-block:: rst

 # cp /etc/my.cnf /etc/20190708_my.cnf
 # vi /etc/my.cnf

.. code-block:: bash

 [mysqld]
 ～ 省略 ～
 # https://dev.mysql.com/doc/refman/8.0/en/server-system-variables.html#sysvar_default_authentication_plugin
 default-authentication-plugin=mysql_native_password

 datadir=/var/lib/mysql
 socket=/var/lib/mysql/mysql.sock
 
 log-error=/var/log/mysqld.log
 pid-file=/var/run/mysqld/mysqld.pid
 
 log_timestamps=SYSTEM
 character-set-server = utf8
 max_connections=100
 sql_mode=NO_ENGINE_SUBSTITUTION,STRICT_TRANS_TABLES
 innodb_buffer_pool_size = 512MB
 innodb_file_per_table
 innodb_log_buffer_size=32M
 innodb_log_file_size=128M
 min_examined_row_limit=100
 key_buffer_size=128M
 join_buffer_size=64M
 max_heap_table_size=32M
 tmp_table_size=32M
 max_sp_recursion_depth=20
 transaction-isolation=READ-COMMITTED

 [client]
 default-character-set=utf8

| 8. Mysqlの再起動

.. code-block:: rst

 # systemctl status mysqld
 # systemctl restart mysqld
 # systemctl status mysqld
 # mysql -u root -phogehoge ※hogehoge 直前の手順で設定した初期パスワード

.. code-block:: bash

 mysql> status
    ～省略～
    Server characterset:    utf8
    Db     characterset:    utf8
    Client characterset:    utf8
    Conn.  characterset:    utf8

ログアウト

.. code-block:: bash

 mysql> quit


3.4.2. mysqlclient インストール
*******************************

| 1. 必要なパッケージをインストール

.. code-block:: rst

 # yum -y --enablerepo mysql80-community install mysql-community-devel

| 2. mysqlclient(django推奨ドライバ)インストール

.. code-block:: rst

 # pip3 install mysqlclient


3.4.3. mysql-connector-pythonインストール
*****************************************

1インストール

.. code-block:: rst

  # pip3 install mysql_connector_python

| 3. pip3 listを実行


.. code-block:: rst
 
 # pip3 list

.. code-block:: bash

    ～省略～
    mysql-connector-python 8.0.16


3.5. Nginxインストール
~~~~~~~~~~~~~~~~~~~~~~

3.5.1. リポジトリの作成
***********************

.. code-block:: rst

 # vi /etc/yum.repos.d/nginx.repo

.. code-block:: bash

 以下を追加
 [nginx]
 name=nginx repo
 baseurl=http://nginx.org/packages/mainline/centos/7/$basearch/
 gpgcheck=0
 enabled=1


yumアップデート

.. code-block:: rst

 # yum update

3.5.2. nginxインストール
************************

.. code-block:: rst

 # yum -y install nginx

.. note:: nginxの起動確認

.. code-block:: rst

 # systemctl status nginx
 # systemctl start nginx


PC端末から、http://IPアドレス へアクセス、画面が表示されること

・サービス停止

.. code-block:: rst

 # systemctl stop nginx


3.6. uWSGIインストール
~~~~~~~~~~~~~~~~~~~~~~

3.6.1. uWSGIインストール
************************

| 1. 以下のコマンドで、uwsgiをインストール

.. code-block:: rst

 # pip3 install uwsgi

| 2. 以下のコマンドでバージョンを確認

.. code-block:: rst

 # uwsgi --version

uWSGIが 2.0.18となっていることを確認

.. note:: サンプルのWSGIアプリケーション作成

.. code-block:: rst

 # mkdir -p /home/centos/work/uwsgi

サンプル用pyファイル作成

.. code-block:: rst

 # vi /home/centos/work/uwsgi/foovar.py

以下を追加

.. code-block:: bash

 # def application(env, start_response):
       start_response('200 OK', [('Content-Type','text/html')])
       return [b"Hello World"]

| ・サンプルWSGIアプリケーションの起動
| 以下のコマンドを実行し、サンプルWSGIアプリケーションを起動する
| 別にTeratermを立ち上げ、rootユーザ以外のユーザで以下を実行。

.. code-block:: rst

 # uwsgi --http :9090 --wsgi-file /home/centos/work/uwsgi/foovar.py

| ・サンプルWSGIアプリケーションの確認
| PC端末から、http://IPアドレス:9090/ へアクセスし、Hello Worldが表示されること
| 確認後、起動したコンソールでCtrl＋Cで サンプルWSGIアプリケーションを一旦終了させる。


3.7. java（openJDK）インストール
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

java（openJDK）インストール

.. code-block:: rst

 # yum -y install java-1.8.0-openjdk java-1.8.0-openjdk-devel

.. code-block:: rst

 # yum list | grep java-1.8.0

.. code-block:: bash

 java-1.8.0-openjdk.x86_64
 java-1.8.0-openjdk-devel.x86_64


3.8. JBoss EAPインストール
~~~~~~~~~~~~~~~~~~~~~~~~~~

| 1. FTPで/tmp 配下に置く
| jboss-eap-7.2.0-installer.jar

| ・Jboss EAPインストール

.. code-block:: rst

 # java -jar /tmp/jboss-eap-7.2.0-installer.jar

以下、対話形式での入力


.. code-block:: bash

 以下で言語を選択してください。 :
 0: English
 1: 中文
 2: Deutsch
 3: francais
 4: 日本語
 5: portugues
 6: espanol
 Please choose [4] :
 4

 継続するには 1 を、終了するには 2 を、再表示するには 3 を押してください。
 1

 インストールパスの選択: [/root/EAP-7.2.0]
 {jbossルートパス}  例) /home/mas/JBoss/EAP-7.2.0
 継続するには 1 を、終了するには 2 を、再表示するには 3 を押してください。
 1

 インストールしたいパッケージを選択してください:
 1    [x] [必須] [Red Hat JBoss Enterprise Application Platform] (30.73 MB)
 2    [x]        [AppClient] (39.72 KB)
 3    [x]        [Docs] (13.65 MB)
 4    [x] [必須] [モジュール] (183.75 MB)
 5    [x] [必須] [Welcome コンテンツ] (2.16 MB)
 Total Size Required: 230.34 MB
 0 を押して選択を確認
 インストールしたいパックを選択してください
 0
 パックの選択完了
 継続するには 1 を、終了するには 2 を、再表示するには 3 を押してください。
 1

 管理ユーザー名: [admin]
 {RHDM管理ユーザー名}  例) admin0000

 管理パスワード: []
 {RHDM管理パスワード}  例) password@1
 管理パスワードを再入力:  [**********]
 {RHDM管理パスワード}  例) password@1
 継続するには 1 を、終了するには 2 を、再表示するには 3 を押してください。
 1

 ランタイム環境の設定
 0  [x] デフォルト設定の実行
 1  [ ] 詳細設定の実行
 入力事項の選択:
 0

 継続するには 1 を、終了するには 2 を、再表示するには 3 を押してください。
 1

 自動インストールスクリプトとプロパティーファイルを生成しますか? (y/n) [n]:
 n

.. note:: 参考

 | ディシジョンマネージャは環境によって作成できるディシジョンテーブル数が変動します。
 | ディシジョンテーブルの最大作成可能数はデフォルトでは4ファイル程度となります。
 | 記載ルール数またはルール自体の複雑度によってディシジョンテーブル作成数が前後する可能性があります。
 | より多くのディシジョンテーブルの作成を実施したい場合はチューニングが必要となります。

.. danger:: 注意

 | ディシジョンテーブルの最大作成数を超えた場合、ディシジョンテーブルのアップロード・プロダクション適用に失敗する可能性があります。
 | 失敗した場合、以下のディレクトリのログを確認してください。
 | /var/log/jboss-eap/console.log
 | OutOfMemoryErrorの障害が発生している場合は再起動コマンドを実行してください。
 | # systemctl restart jboss-eap-rhel.service
 | 再起動後、以下のコマンドを実行して、KIEコンテナーの一覧を確認します。
 | # curl -u [RHDM管理ユーザー名]:[RHDM管理パスワード] -H "accept: application/json" -X GET "http://[IPアドレス]:8080/decision-central/rest/controller/management/servers"
 | 削除したいKIEコンテナーのcontainer-idを指定して以下のコマンドを実行することにより、KIEコンテナーが削除されます。
 | # curl -u [RHDM管理ユーザー名]:[RHDM管理パスワード] -X DELETE "http://[IPアドレス]:8080/decision-central/rest/controller/management/servers/default-kieserver/containers/[container-id]" -H "accept: application/json"
 | ※IPアドレスはRHDMをインストールしたサーバのアドレス

3.9. Decision Managerインストール
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

3.9.1. gitインストール
**********************

gitインストール

.. code-block:: rst

 # yum install git

gitがインストールされたことを確認

.. code-block:: rst

 # git --version

.. code-block:: bash

 git version 1.8.3.1

3.9.2. インストール実行
***********************

| 1. FTPで/tmp 配下に置く
| rhdm-installer-7.3.1.jar

.. code-block:: rst

 # java -jar /tmp/rhdm-installer-7.3.1.jar

以下、対話形式での入力

.. code-block:: bash


 Press 1 to continue, 2 to quit, 3 to redisplay.
 1

 Red Hat JBoss EAP 7.2 or Red Hat JBoss Web Server 5.0 (JWS 5.0.1 or newer is supported). [/root/RHDM-7.3.1/jboss-eap-7.2]
 {jbossルートパス}

 Press 1 to continue, 2 to quit, 3 to redisplay.
 1

 Select the components you want to install:
 1    [x]                 [Decision Central] (275.65 MB)
 2    [x]                 [Decision Server] (94.1 MB)
 Total Size Required: 369.75 MB
 Press 0 to confirm your selections
 0
 Component selection done
 Press 1 to continue, 2 to quit, 3 to redisplay.
 1

 User Name: [rhdmAdmin]
 {RHDM管理ユーザー名}

 Password: []
 {RHDM管理パスワード}
 Confirm Password: [**********]
 {RHDM管理パスワード}
 Press 1 to continue, 2 to quit, 3 to redisplay.
 1

 Would you like to generate an automatic installation script and properties file? (y/n) [n]:
 n

3.10. Mavenインストール
~~~~~~~~~~~~~~~~~~~~~~~

3.10.1. 資材配置
****************

.. code-block:: rst

 # cd /tmp
 # wget https://archive.apache.org/dist/maven/maven-3/3.6.1/binaries/apache-maven-3.6.1-bin.tar.gz
 # tar -xzvf apache-maven-3.6.1-bin.tar.gz
 # mv apache-maven-3.6.1 /opt/
 # cd /opt
 # ln -s /opt/apache-maven-3.6.1 apache-maven
 # ls -l

3.10.2. 環境変数設定
********************

.. code-block:: rst

 # cp /etc/profile /etc/20190708_profile.bk
 # vi /etc/profile

.. code-block:: bash

 export PATH USER LOGNAME MAIL HOSTNAME HISTSIZE HISTCONTROL

以下を追加

.. code-block:: bash

 export M2_HOME=/opt/apache-maven
 export PATH=$PATH:$M2_HOME/bin


設定読み込みなおし

.. code-block:: rst

 # source /etc/profile
 # mvn --version

.. code-block:: bash

 Apache Maven 3.6.1

3.11. Djangoインストール
~~~~~~~~~~~~~~~~~~~~~~~~

以下のコマンドを実行し、Djangoをインストール

.. code-block:: rst

 # pip3 install django==2.2.3 django-crispy-forms django-filter django-pure-pagination
 # pip3 list

.. code-block:: bash

 ※Djangoが表示されていることを確認
 Package                Version
 ---------------------- -------
 Django                 2.2.3
 django-crispy-forms    1.7.2    ← 入力フォームのHTMLをBootstrapに対応させる
 django-filter          2.1.0    ← 検索機能を追加する
 django-pure-pagination 0.3.0    ← 標準のページング機能を高機能にする


requestsモジュールのインストール

.. code-block:: rst

 # pip3 install requests ldap3 pycrypto openpyxl==2.5.14 xlrd configparser fasteners djangorestframework python-memcached django-simple-history pyyaml
 # pip3 list

.. code-block:: bash

 Package                Version
 ---------------------- -------
 certifi                2019.6.16
 chardet                3.0.4
 configparser           3.7.4
 Django                 2.2.3
 django-crispy-forms    1.7.2
 django-filter          2.1.0
 django-pure-pagination 0.3.0
 django-simple-history  2.7.2
 djangorestframework    3.9.4
 et-xmlfile             1.0.1
 fasteners              0.15
 idna                   2.8
 jdcal                  1.4.1
 ldap3                  2.6
 monotonic              1.5
 openpyxl               2.5.14
 pip                    19.1.1
 pyasn1                 0.4.5
 pycrypto               2.6.1
 python-memcached       1.59
 pytz                   2019.1
 PyYAML                 5.1.1
 requests               2.22.0
 setuptools             39.0.1
 six                    1.12.0
 sqlparse               0.3.0
 urllib3                1.25.3
 xlrd                   1.2.0


★pytzがない場合

.. code-block:: rst

 # pip3 install pytz


3.12. OASEインストール
~~~~~~~~~~~~~~~~~~~~~~

3.12.1. OASEソース配置
**********************

| 1. 配置フォルダを作成

.. code-block:: rst

 # mkdir /home/centos  ※配置フォルダは別タスクで修正
 # cd /home/centos

| 2. FTPで/home/centos 配下に[OASE_Ver1.0.tar.gz]を配置

ファイル名はお持ちのファイルに合わせて指定してください。

.. code-block:: rst

 # ll /home/centos

.. code-block:: bash

 -rw-r--r-- 1 root root 3738247  7月  4 20:08 OASE_Ver1.0.tar.gz

.. code-block:: rst

 # tar zxvf OASE_Ver1.0.tar.gz
 # rm OASE_Ver1.0.tar.gz

| 3. OASE settings.pyの設定

.. code-block:: rst

 # cd OASE/oase-root/
 # cp confs/frameworkconfs/settings.py.sample confs/frameworkconfs/settings.py
 # vi confs/frameworkconfs/settings.py

.. code-block:: bash

 HOST_NAME = 'https://xxx.xxx.xxx.xxx'

 (中略)

 EVTIMER_SERVER = {
    "type"     : "cron",
    "protocol" : "https:",
    "location" : "xxx.xxx.xxx.xxx",
    "path"     : "oase_web/event/evtimer/%s/%s/%s/",
 }

| xxx ： webサーバを立ち上げるIPアドレス

.. code-block:: bash

 DATABASES = {
    'default' : {
        'ENGINE'   : 'django.db.backends.mysql',
        'NAME'     : '{データベース名}',
        'USER'     : '{DBユーザ名}',
        'PASSWORD' : '{DBパスワード}',
        'HOST'     : '127.0.0.1',
        'PORT'     : '3306',
    },
 }


3.12.2. DBへマイグレーション
****************************

| 1. マイグレーション実行準備

.. code-block:: rst

 # cd /home/centos/OASE/oase-root/web_app
 # mkdir migrations
 # cd migrations/
 # touch __init__.py

| 2. init_custom.yamlの作成

下記のコマンドにてinit_custom.yamlを作成してください。

.. code-block:: rst

 # cd /home/centos/OASE/oase-root/web_app/fixtures
 # vi init_custom.yaml

| 内容は下記を参考にしてください。  
| また、init_custom.yamlのvalue値は環境によって異なるため適切な値を記入してください。

.. code-block:: rst

 ################################
 # システム設定
 ################################
 - model: web_app.System
   pk: 2
   fields:
     config_name: ルールファイル設置ルートパス
     category: RULE
     config_id: RULEFILE_ROOTPATH
     value: /home/centos/work/rule/
     maintenance_flag: 0
     last_update_timestamp: 2019-07-01T00:00:00+0900
     last_update_user: システム管理者
 
 - model: web_app.System
   pk: 26
   fields:
     config_name: DMリクエスト送信先
     category: DMSETTINGS
     config_id: DM_IPADDRPORT
     value: 
     maintenance_flag: 0
     last_update_timestamp: 2019-07-01T00:00:00+0900
     last_update_user: システム管理者
 
 - model: web_app.System
   pk: 27
   fields:
     config_name: DMユーザID
     category: DMSETTINGS
     config_id: DM_USERID
     value: 
     maintenance_flag: 0
     last_update_timestamp: 2019-07-01T00:00:00+0900
     last_update_user: システム管理者
 
 - model: web_app.System
   pk: 28
   fields:
     config_name: DMパスワード
     category: DMSETTINGS
     config_id: DM_PASSWD
     value: 
     maintenance_flag: 0
     last_update_timestamp: 2019-07-01T00:00:00+0900
     last_update_user: システム管理者
 
 - model: web_app.System
   pk: 29
   fields:
     config_name: 適用君待ち受け情報
     category: APPLYSETTINGS
     config_id: APPLY_IPADDRPORT
     value: 127.0.0.1:50001
     maintenance_flag: 0
     last_update_timestamp: 2019-07-01T00:00:00+0900
     last_update_user: システム管理者
 
 - model: web_app.System
   pk: 31
   fields:
     config_name: OASEメールSMTP
     category: OASE_MAIL
     config_id: OASE_MAIL_SMTP
     value: {"IPADDR":"127.0.0.1","PORT":25,"AUTH":False}
     maintenance_flag: 0
     last_update_timestamp: 2019-07-01T00:00:00+0900
     last_update_user: システム管理者
 
 - model: web_app.System
   pk: 32
   fields:
     config_name: Maven repositoryパス
     category: RULE
     config_id: MAVENREP_PATH
     value: /root/.m2/repository/com/oase/
     maintenance_flag: 0
     last_update_timestamp: 2019-07-01T00:00:00+0900
     last_update_user: システム管理者
 
 - model: web_app.System
   pk: 50
   fields:
     config_name: RabbitMQユーザID
     category: RABBITMQ
     config_id: MQ_USER_ID
     value: 
     maintenance_flag: 0
     last_update_timestamp: 2019-07-01T00:00:00+0900
     last_update_user: システム管理者
 
 - model: web_app.System
   pk: 51
   fields:
     config_name: RabbitMQパスワード
     category: RABBITMQ
     config_id: MQ_PASSWORD
     value: 
     maintenance_flag: 0
     last_update_timestamp: 2019-07-01T00:00:00+0900
     last_update_user: システム管理者
 
 - model: web_app.System
   pk: 52
   fields:
     config_name: RabbitMQIPアドレス
     category: RABBITMQ
     config_id: MQ_IPADDRESS
     # RABBITMQを入れたサーバのIPアドレス
     value: 
     maintenance_flag: 0
     last_update_timestamp: 2019-07-01T00:00:00+0900
     last_update_user: システム管理者
 
 - model: web_app.System
   pk: 53
   fields:
     config_name: RabbitMQキュー名
     category: RABBITMQ
     config_id: MQ_QUEUE_NAME
     # 任意の名称
     value: 
     maintenance_flag: 0
     last_update_timestamp: 2019-07-01T00:00:00+0900
     last_update_user: システム管理者


MQ_PASSWORDのvalue値は以下のコマンドを実行して表示された値を設定して下さい。
password@1の箇所は"3.3. RabbitMQ Serverインストール"で設定した{RabbitMQパスワード}に置き換えてください。

.. code-block:: rst

 # python /home/centos/OASE/tool/encrypter.py 'password@1'

DM_PASSWDのvalue値は以下のコマンドを実行して表示された値を設定して下さい。
password@1の箇所は"3.7. JBoss EAPインストール"で設定した{RHDM管理パスワード}に置き換えてください。

.. code-block:: rst

 # python /home/centos/OASE/tool/encrypter.py 'password@1'


| 3. マイグレーション実行

.. code-block:: rst

 # cd /home/centos/OASE/oase-root
 # python manage.py makemigrations web_app
 # python manage.py migrate
 # python manage.py loaddata init init_custom


| 4. DB確認

.. code-block:: rst

 # mysql -u {DBユーザ名} -p{DBパスワード} {データベース名}

.. code-block:: bash

 mysql> show tables;


4. 各サービスの登録と起動
-------------------------

4.1. Nginx+uWSGI連携
~~~~~~~~~~~~~~~~~~~~

| 1. uwsgi.sock格納フォルダ作成

.. code-block:: rst

 # mkdir /home/uWSGI
 # chmod 755 /home/uWSGI


| 2. uwsgi.log格納フォルダ作成

.. code-block:: rst

 # mkdir /var/log/uwsgi
 # chmod 644 /var/log/uwsgi


| 3. カーネルパラメータ変更

.. code-block:: rst

 # cp -pi /etc/sysctl.conf /etc/sysctl.conf.bk
 # vi /etc/sysctl.conf
 # net.core.somaxconn = 16384
 # less /etc/sysctl.conf
 # sysctl -p


| 4. Nginx設定
| 簡易動作確認用としてソース内(/home/centos/OASE/oase-root/)に証明書ファイルを用意しています。
| こちらを元に説明を続けます。
| 本番運用時には各サーバでの正式な証明書ファイルを使用してください。

.. code-block:: rst

 # cp /etc/nginx/nginx.conf /etc/nginx/20190708_nginx.conf.bk
 # vi /etc/nginx/nginx.conf

.. code-block:: bash

 user  root;
 #user  nginx;
 worker_processes  auto;
 #worker_processes  1;

 worker_rlimit_nofile 65000;

 error_log  /var/log/nginx/error.log warn;
 pid        /var/run/nginx.pid;

 events {
     worker_connections  16000;
 }

以下のファイルを開く

.. code-block:: rst

 # cp /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/20190708_default.conf.bk
 # mv /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/oase.conf
 # vi /etc/nginx/conf.d/oase.conf

.. code-block:: bash

 server {
     listen 80;
     server_name exastro-oase;
     return 301 https://$host$request_uri;
 }

 server {
    listen  443  ssl;

    ssl_certificate  /home/centos/OASE/oase-root/exastro-oase.crt;
    ssl_certificate_key  /home/centos/OASE/oase-root/cakey-nopass.pem;

    ssl_prefer_server_ciphers  on;
    ssl_protocols  TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers  'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128:AES256:AES:DES-CBC3-SHA:HIGH:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK';

    ssl_session_cache    shared:SSL:1m;
    ssl_session_tickets  on;

    location / {
        include uwsgi_params;
        uwsgi_pass unix:///home/uWSGI/uwsgi.sock;
    }

    location = / {
        include uwsgi_params;
        uwsgi_pass unix:///home/uWSGI/uwsgi.sock;
        return 301 /oase_web/top/login;
    }

    location /static {
        alias /home/centos/OASE/oase-root/web_app/static;
    }

    error_page   500 502 503 504  /50x.html;
    location = /50x.html {
        root   /usr/share/nginx/html;
    }
 }

.. note:: default.confがない場合は、viコマンドによりoase.confを作成してください。

| 5. uwsgi.iniの修正

.. code-block:: rst

 # vi /home/centos/OASE/oase-root/uwsgi.ini

.. code-block:: bash

 [uwsgi]
 chdir=/home/centos/OASE/oase-root
 module=web_app
 master=true
 socket=/home/uWSGI/uwsgi.sock
 chmod-socket=666
 wsgi-file=/home/centos/OASE/oase-root/confs/frameworkconfs/wsgi.py
 log-format = [pid: %(pid)|app: -|req: -/-] %(addr) (%(user)) {%(vars) vars in %(pktsize) bytes} [ %(ctime) ] %(method) %(uri) => generated %(rsize) bytes in %(msecs) msecs (%(proto) %(status)) %(headers) headers in %(hsize) bytes (%(switches) switches on core %(core))
 logto=/var/log/uwsgi/uwsgi.log
 processes=4
 threads=2
 listen=16384


| 6. /etc/systemd/system/ 配下に[nginx.service]と[uwsgi.service]を配置

.. code-block:: rst

 # cd /home/centos/OASE/tool/service
 # cp nginx.service /etc/systemd/system/
 # cp uwsgi.service /etc/systemd/system/
 # ll /etc/systemd/system/

.. code-block:: bash

    nginx.service
    uwsgi.service



4.2. JBoss EAP の設定
~~~~~~~~~~~~~~~~~~~~~

| 1. jboss-eap.conf ファイルの起動オプションをカスタマイズ

.. code-block:: rst

 # cd {Jbossルートパス}
 # cp -p bin/init.d/jboss-eap.conf bin/init.d/20190708_jboss-eap.conf.bk
 # vi bin/init.d/jboss-eap.conf

.. code-block:: bash

 ## Location of JDK
 # JAVA_HOME="/usr/lib/jvm/default-java"
 JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk

 ## Location of JBoss EAP
 # JBOSS_HOME="/opt/jboss-eap"
 JBOSS_HOME={jbossルートパス}

 ## The username who should own the process.
 # JBOSS_USER=jboss-eap
 JBOSS_USER=root

 ## The mode JBoss EAP should start, standalone or domain
 JBOSS_MODE=standalone

 ## Configuration for standalone mode
 JBOSS_CONFIG=standalone-full.xml

 ## Location to keep the console log
 JBOSS_CONSOLE_LOG="/var/log/jboss-eap/console.log"

 ## Additionals args to include in startup
 # JBOSS_OPTS="--admin-only -b 127.0.0.1"
 JBOSS_OPTS="-Dfile.encoding=UTF-8 -Djboss.bind.address=0.0.0.0"

| 2. ファイル権限変更

.. code-block:: rst

 # chmod 755 {jbossルートパス}/bin/init.d/jboss-eap.conf

| 3. jboss-eap.confを/etc/default配下にコピー

.. code-block:: rst

 # cp {jbossルートパス}/bin/init.d/jboss-eap.conf /etc/default/

| 4. サービス起動スクリプトを /etc/init.d ディレクトリーにコピーし、実行パーミッションを付与します。

.. code-block:: rst

 # cp {jbossルートパス}/bin/init.d/jboss-eap-rhel.sh /etc/init.d/jboss-eap-rhel.sh
 # chmod +x /etc/init.d/jboss-eap-rhel.sh

| 5. chkconfig サービス管理コマンドを使用して、自動的に起動されるサービスのリストに新しい jboss-eap-rhel.sh サービスを追加します。
 
.. code-block:: rst

 # chkconfig --add jboss-eap-rhel.sh


4.3. OASE用のMaven設定
~~~~~~~~~~~~~~~~~~~~~~

| 1. settings.xmlの修正

.. code-block:: rst

 # cp /opt/apache-maven-3.6.1/conf/settings.xml /opt/apache-maven-3.6.1/conf/20190708_settings.xml
 # vi /opt/apache-maven-3.6.1/conf/settings.xml

以下を追加

.. code-block:: bash

    <proxies>
      <!-- proxy
       | Specification for one proxy, to be used in connecting to the network.
       |
      <proxy>
        <id>optional</id>
        <active>true</active>
        <protocol>http</protocol>
        <username>proxyuser</username>
        <password>proxypass</password>
        <host>proxy.host.net</host>
        <port>80</port>
        <nonProxyHosts>local.net|some.host.com</nonProxyHosts>
      </proxy>
      -->
      *- 追加 ここから -*
      <proxy>
        <id>http_proxy</id>
        <active>true</active>
        <protocol>http</protocol>
        <host>{プロキシサーバのホスト名}</host>
        <nonProxyHosts>{プロキシ対象外のホストまたはIPアドレス}</nonProxyHosts>
        <port>8080</port>
      </proxy>
      *- ここまで -*
    </proxies>

.. note:: nonProxyHostsは | (パイプ)で区切ることで複数記述することができます。

.. code-block:: bash

 既存の上部記述に続けて下部を追記する
    <profile>
      <id>jdk-1.4</id>

      <activation>
        <jdk>1.4</jdk>
      </activation>

      <repositories>
        <repository>
          <id>jdk14</id>
          <name>Repository for JDK 1.4 builds</name>
          <url>http://www.myhost.com/maven/jdk14</url>
          <layout>default</layout>
          <snapshotPolicy>always</snapshotPolicy>
        </repository>
      </repositories>
    </profile>

.. code-block:: bash

 既存の上部記述に続けて下部を追記する
    <profile>
      <id>jboss-ga</id>
      <repositories>
        <repository>
          <id>jboss-ga-repository</id>
          <name>JBoss GA Tech Preview Maven Repository</name>
          <url>https://maven.repository.redhat.com/ga/</url>
          <layout>default</layout>
          <releases>
            <enabled>true</enabled>
            <updatePolicy>never</updatePolicy>
          </releases>
          <snapshots>
            <enabled>false</enabled>
            <updatePolicy>never</updatePolicy>
          </snapshots>
        </repository>
      </repositories>
      <pluginRepositories>
        <pluginRepository>
          <id>jboss-ga-plugin-repository</id>
          <name>JBoss 7 Maven Plugin Repository</name>
          <url>https://maven.repository.redhat.com/ga/</url>
          <layout>default</layout>
          <releases>
            <enabled>true</enabled>
            <updatePolicy>never</updatePolicy>
          </releases>
          <snapshots>
            <enabled>false</enabled>
            <updatePolicy>never</updatePolicy>
          </snapshots>
        </pluginRepository>
      </pluginRepositories>
    </profile>

| 2. /root/.m2/配下にsettings.xmlを作成

.. code-block:: rst

 # mkdir /root/.m2
 # cd /root/.m2
 # vi settings.xml

以下を追加

.. code-block:: bash

    <?xml version="1.0" encoding="UTF-8" standalone="no"?>
    <settings xmlns="http://maven.apache.org/SETTINGS/1.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0 http://maven.apache.org/xsd/settings-1.0.0.xsd">

        <localRepository/>

        <proxies>
          <proxy>
            <id>http_proxy</id>
            <active>true</active>
            <protocol>http</protocol>
            <host>{プロキシサーバのホスト名}</host>
            <nonProxyHosts>{プロキシ対象外のホストまたはIPアドレス}</nonProxyHosts>
            <port>8080</port>
          </proxy>
          <proxy>
            <id>https_proxy</id>
            <active>true</active>
            <protocol>https</protocol>
            <host>{プロキシサーバのホスト名}</host>
            <nonProxyHosts>{プロキシ対象外のホストまたはIPアドレス}</nonProxyHosts>
            <port>8080</port>
          </proxy>
        </proxies>

        <profiles>
            <profile>
                <id>jboss-ga</id>
                <repositories>
                    <repository>
                        <id>jboss-ga-repository</id>
                        <name>JBoss GA Tech Preview Maven Repository</name>
                        <url>file:/root/.m2/repository/</url>
                        <layout>default</layout>
                        <releases>
                            <enabled>true</enabled>
                            <updatePolicy>never</updatePolicy>
                        </releases>
                        <snapshots>
                            <enabled>false</enabled>
                            <updatePolicy>never</updatePolicy>
                        </snapshots>
                    </repository>
                </repositories>
                <pluginRepositories>
                    <pluginRepository>
                        <id>jboss-ga-plugin-repository</id>
                        <name>JBoss 7 Maven Plugin Repository</name>
                        <url>file:/root/.m2/repository/</url>
                        <layout>default</layout>
                        <releases>
                            <enabled>true</enabled>
                            <updatePolicy>never</updatePolicy>
                        </releases>
                        <snapshots>
                            <enabled>false</enabled>
                            <updatePolicy>never</updatePolicy>
                        </snapshots>
                    </pluginRepository>
                </pluginRepositories>
            </profile>
        </profiles>
        <activeProfiles>
            <activeProfile>jboss-ga</activeProfile>
        </activeProfiles>
    </settings>

.. note:: nonProxyHostsは | (パイプ)で区切ることで複数記述することができます。


4.4. Decision Server の設定
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: rst

 # cp {jbossルートパス}/standalone/configuration/standalone-full.xml {jbossルートパス}/standalone/configuration/20190708_standalone-full.xml
 # vi {jbossルートパス}/standalone/configuration/standalone-full.xml

<system-properties> を修正

・before

.. code-block:: bash

 <property name="org.kie.server.controller.user" value="controllerUser"/>
 <property name="org.kie.server.controller.pwd" value="${VAULT::vaulted::controller.password::1}"/>
 <property name="org.kie.server.user" value="controllerUser"/>
 <property name="org.kie.server.pwd" value="${VAULT::vaulted::controller.password::1}"/>

・after

.. code-block:: bash

 <property name="org.kie.server.controller.user" value="{RHDM管理ユーザー名}"/>
 <property name="org.kie.server.controller.pwd" value="{RHDM管理パスワード}"/>
 <property name="org.kie.server.user" value="{RHDM管理ユーザー名}"/>
 <property name="org.kie.server.pwd" value="{RHDM管理パスワード}"/>
 <property name="kie.maven.settings.custom" value="/opt/apache-maven/conf/settings.xml"/>

4.5. oase_env
~~~~~~~~~~~~~
.. code-block:: rst

 # cp /home/centos/OASE/oase-root/confs/backyardconfs/services/oase_env /home/centos/OASE/oase-root/confs/backyardconfs/services/20190708_oase_env.bk
 # vi /home/centos/OASE/oase-root/confs/backyardconfs/services/oase_env

以下を追加

.. code-block:: bash

 # DM settings
 JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk
 PATH=/opt/apache-maven/bin:JAVA_HOME/bin:/usr/bin
 CLASSPATH=JAVA_HOME/jre/lib:JAVA_HOME/lib:JAVA_HOME/lib/tools.jar
 M2_HOME=/opt/apache-maven-3.6.1
 JBOSS_HOME={jbossルートパス}

4.6. OASEサービスの登録
~~~~~~~~~~~~~~~~~~~~~~~

| 1. OASE環境設定ファイルのリンク作成

.. code-block:: rst

 # ll /home/centos/OASE/oase-root/confs/backyardconfs/services/oase_env
 # ln -s /home/centos/OASE/oase-root/confs/backyardconfs/services/oase_env /etc/sysconfig/oase_env

| 2. oase-action.serviceの登録

.. code-block:: rst

 # ll /home/centos/OASE/oase-root/confs/backyardconfs/services/oase_action_env
 # ln -s /home/centos/OASE/oase-root/confs/backyardconfs/services/oase_action_env /etc/sysconfig/oase_action_env

 # ll /home/centos/OASE/oase-root/backyards/action_driver/oase-action.service
 # cp /home/centos/OASE/oase-root/backyards/action_driver/oase-action.service /usr/lib/systemd/system/oase-action.service

| 3. oase-agent.serviceの登録

.. code-block:: rst

 # ll /home/centos/OASE/oase-root/confs/backyardconfs/services/oase_agent_env
 # ln -s /home/centos/OASE/oase-root/confs/backyardconfs/services/oase_agent_env /etc/sysconfig/oase_agent_env

 # ll /home/centos/OASE/oase-root/backyards/agent_driver/oase-agent.service
 # cp /home/centos/OASE/oase-root/backyards/agent_driver/oase-agent.service /usr/lib/systemd/system/oase-agent.service

| 4. oase-apply.serviceの登録

.. code-block:: rst

 # ll /home/centos/OASE/oase-root/confs/backyardconfs/services/oase_apply_env
 # ln -s /home/centos/OASE/oase-root/confs/backyardconfs/services/oase_apply_env /etc/sysconfig/oase_apply_env

 # ll /home/centos/OASE/oase-root/backyards/apply_driver/oase-apply.service
 # cp /home/centos/OASE/oase-root/backyards/apply_driver/oase-apply.service /usr/lib/systemd/system/oase-apply.service

| 5. oase-accept.serviceの登録

.. code-block:: rst

 # ll /home/centos/OASE/oase-root/confs/backyardconfs/services/oase_accept_env
 # ln -s /home/centos/OASE/oase-root/confs/backyardconfs/services/oase_accept_env /etc/sysconfig/oase_accept_env

 # ll /home/centos/OASE/oase-root/backyards/accept_driver/oase-accept.service
 # cp /home/centos/OASE/oase-root/backyards/accept_driver/oase-accept.service /usr/lib/systemd/system/oase-accept.service

| 6. oase-action.serviceの起動

.. code-block:: rst

 # systemctl status oase-action.service
 # systemctl start oase-action.service
 # systemctl enable oase-action.service

| 7. oase-agent.serviceの起動

.. code-block:: rst

 # systemctl status oase-agent.service
 # systemctl start oase-agent.service
 # systemctl enable oase-agent.service

| 8. oase-apply.serviceの起動

.. code-block:: rst

 # systemctl status oase-apply.service
 # systemctl start oase-apply.service
 # systemctl enable oase-apply.service

| 9. oase-accept.serviceの起動

.. code-block:: rst

 # systemctl status oase-accept.service
 # systemctl start oase-accept.service
 # systemctl enable oase-accept.service

| ■各サービスの起動

| 1. JBoss EAPサービス登録と起動

.. code-block:: rst

 # service jboss-eap-rhel start
 # chkconfig jboss-eap-rhel.sh on

| 2. JBoss EAPサービス確認

.. code-block:: rst

 # systemctl status jboss-eap-rhel.service

.. note:: ★下記のサイトが見れることを確認

 http://XXX.XXX.XXX.XXX:PORT/decision-central

 | xxx ： webサーバを立ち上げるIPアドレス
 | PORT： Decision Managerが起動しているPORT番号(default: 8080)

| 3. Nginx サービス再起動

.. code-block:: rst

 # systemctl status nginx
 # systemctl start nginx
 # systemctl enable nginx

| 4. uwsgi サービス再起動

.. code-block:: rst

 # systemctl status uwsgi
 # systemctl start uwsgi
 # systemctl enable uwsgi


| OASEのインストール作業は以上となります。
| 次にドライバインストールを行いますので、「環境構築マニュアル -ドライバインストール編-」をご参照ください。
| 監視ツールと連携を行う場合は「環境構築マニュアル -アダプタインストール編-」をご参照ください。
| ActiveDirectoryを行いたい場合は「環境構築マニュアル -ActiveDirectory編-」をご参照ください。


