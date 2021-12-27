=================================
インストール手順(Docker版)
=================================

| Docker版OASEのインストール手順を下記に示します。
| コンテナ起動後、すぐにOASEを体験いただくことが可能です。

.. note:: お手持ちのDocker環境が必要となります。

1. Dockerコンテナの起動
-----------------------

.. code-block:: rst

 # docker run --hostname="exastro-oase" --privileged --add-host=exastro-oase:127.0.0.1 -d -p 8080:80 -p 10443:443 --name exastro01 exastro/oase:x.x.x-ja

.. note:: 
   | ポート番号(8080,10443)とバージョン(x.x.x)は適宜変更してください。
   | 英語版をご利用になる場合は、バージョンに-enを付与してください。(x.x.x-en)

コンテナ起動後に下記のURLにアクセスしてください。

| \https://[Docker-Host-IP]:10443/

