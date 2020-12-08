=================================
インストール手順(Docker版)
=================================

| Docker版OASEのインストール手順を下記に示します。
| コンテナ起動後、すぐにOASEを体験いただくことが可能です。

.. note:: お手持ちのDocker環境が必要となります。

1. Dockerコンテナの起動
-----------------------

.. code-block:: rst

 # docker run --privileged --add-host=exastro-oase:127.0.0.1 -d -p 10443:443 --name exastro02 exastro/oase:x.x.x

.. note:: ポート番号(10443)とバージョン(x.x.x)は適宜変更してください。

コンテナ起動後に下記のURLにアクセスしてください。

| \https://[Docker-Host-IP]:10443/

