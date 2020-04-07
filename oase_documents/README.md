# OASEマニュアル

OASEのマニュアルを作るためのプロジェクト

###### 実行コマンド
基本的なコマンド http://127.0.0.1:8000に許可
```
cd OASE_documents/
sphinx-autobuild . _build/html
```

-H0　で全てのアクセスを許可。 -p<portno> でポートを指定できる。
```
cd OASE_documents/
sphinx-autobuild . _build/html -H0 -p<portno>
```
sphinx-autobuild . _build/html -H0 -p8033

終了するにはCtrl+Cを入力

###### 使用ツール
Sphinx 3.0.0.dev20190702
sphinx-autobuild 0.7.1
