=================================
1 監視アダプタインストール
=================================

| 本章では、監視アダプタ画面をご利用頂くために、必要なインストールについて説明します。


1.1 監視アダプタ資材の解凍
==========================

インストール資材の下記ディレクトリに移動し、
ご利用頂く監視アダプタの資材の解凍を実施してください。

::

 cd oase/oase_install_package/OASE/oase-contents
 tar zxf ZABBIX_Adapter.tar.gz
 tar zxf Prometheus_Adapter.tar.gz
 tar zxf Grafana_Adapter.tar.gz
 tar zxf Datadog_Adapter.tar.gz


1.2 インストールコマンドの形式
==============================

下記の情報で インストールコマンドを実行します。
OASE本体をインストールされた際のoase-root直下で実施します。


1.2.1 インストールコマンド
--------------------------

::

 python3 manage.py adapter_installer -p [pluginsパス] -i [インストール対象ID]

**例）zabbixアダプタインストール例**

::

 python3 manage.py adapter_installer -p /root/oase/oase_install_package/OASE/oase-contents/plugins -i 1

.. note::
   ご利用頂く監視アダプタの資材を任意のディレクトリに格納頂き、解凍する必要があります。


1.2.2 オプション
--------------------------
オプションについては次の表のとおりです。

.. csv-table:: 表 1.1.2 オプション定義
   :header: No.,オプション,説明
   :widths: 5, 20, 40

   1, -p, pluginsパスを指定します。
   2, -i, インストール対象IDを指定します。


1.2.3 インストール対象ID
--------------------------
インストール対象IDについては次の表のとおりです。

.. csv-table:: 表 1.1.3 インストール対象ID定義
   :header: No.,ID,説明
   :widths: 5, 20, 40

   1, 1, zabbixアダプタをインストールします。
   2, 2, Prometheusアダプタをインストールします。
   3, 3, Grafanaアダプタをインストールします。
   4, 4, Datadogアダプタをインストールします。

