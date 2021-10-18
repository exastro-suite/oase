![Exastro-OASE-logo2-rgb](https://user-images.githubusercontent.com/83527822/137485693-20c8eb39-4588-4fce-ad0c-4a6f96cacd86.png)

# Exastro Operation Autonomy Support Engine 🏝

[![download](https://img.shields.io/github/downloads/exastro-suite/oase/total.svg)](https://github.com/exastro-suite/oase/releases)
[![stars](https://img.shields.io/github/stars/exastro-suite/oase)](https://github.com/exastro-suite/oase)
[![Open issue](https://img.shields.io/github/issues/exastro-suite/oase)](https://github.com/exastro-suite/oase/issues)
[![Closed issue](https://img.shields.io/github/issues-closed/exastro-suite/oase)](https://github.com/exastro-suite/oase/issues)
[![LICENSE](https://img.shields.io/github/license/exastro-suite/oase.svg)](https://github.com/exastro-suite/oase/blob/master/LICENSE)

[[English](./README.md)]

---

Exastro **O**peration **A**utonomy **S**upport **E**ngine (Exastro **OASE**)は、システム運用、特に、システムにおける障害発生時の監視オペレーター業務を支援するためのオープンソースです。

有意義でクリエイティブな時間を過ごせますように🏄

---

## 特徴

- ⚙**オペレーションの自動化** 監視イベントの仕分けを自動で行い対処します。
- 👫**連携機能** 様々な、監視アプリケーション、対処ソフトウェアとの連携が可能です。
- 📈**インターフェース** 美しいグラフ、ルールの管理にはスプレッドシートが利用できます。

### 連携可能な監視アプリケーション

Pull型とPush型のどちらかの方法でアラートメッセージを受け取る事ができます。
Pull型は予め用意された監視アダプタのみ利用可能ですが、RESTfull API を利用することで更に多くの監視アプリケーションとの連携が可能になります。

#### Pull型(アダプタ使用)

- [**Zabbix**](https://github.com/zabbix/zabbix)
- [**Grafana**](https://github.com/grafana/grafana)
- [**Prometheus**](https://github.com/prometheus/prometheus)

#### Push型(アダプタ不使用)

- [**RESTful API**](https://exastro-suite.github.io/oase-docs/OASE_documents_ja/html/api/01_events_request.html)

### 連携可能な対処ソフトウェア

- [**Exastro IT Automation**](https://github.com/exastro-suite/it-automation)
- [**ServiceNowワークフロー**](https://www.servicenow.com/)

### インシデント管理

[ServiceNow](https://www.servicenow.com/)のITSMと連携することで、インシデント起票・処理中・処理完了・クローズまでの一連のインシデント管理ができます。

### 認証管理

[ServiceNow](https://www.servicenow.com/)のITSMと連携することで、対処の許可や却下といった承認フローと連携できます。

## インストール

インストール方法は下記にも記載していますが、もっと知りたければ[コミュニティサイト](https://exastro-suite.github.io/oase-docs/learn_ja.html#introduction)を確認してください。

### 動作要件

以下のいずれかの環境で稼働します。

|<img src="https://img.shields.io/badge/-CentOS-A1077C.svg?logo=centos&style=flat">|<img src="https://img.shields.io/badge/-RedHat-EE0000.svg?logo=red-hat&style=flat">|<img src="https://img.shields.io/badge/-Docker-FFFFFF.svg?logo=docker&style=flat">|
|----|----|----|
|CentOS 7| Red Hat Enterprise Linux 7 or 8|x86_64|

### 🐳 Docker版 🐷

Docker 版は OASE を使用するの最も簡単な方法です。

1. Docker を利用すれば即座に Exastro OASE を利用できます。

    ```bash
    docker run --privileged --add-host=exastro-oase:127.0.0.1 -d -p 8080:80 -p 10443:443 --name exastro-oase exastro/oase 
    ```

2. Exastro OASE にアクセスします

    http://oase.exasmple.com:8080

### 🗿 伝統的な方法 🐶

カスタマイズが必要な場合や、コンテナ環境が使えない場合はこちらを選択してください。

1. インストールに必要なパッケージをインストールします。

    ```bash
    # GCC と Wget が必要です
    yum install -y gcc wget
    ```

2. リリース資材のダウンロードと展開をします。

    ```bash
    # 作業のためにディレクトリを変更します
    cd /tmp

    # ダウンロードするバージョンを変数に入れます
    # OASE_VER=X.X.X
    #
    # 例) 1.4.0 の場合
    OASE_VER=1.4.0

    # 資材をダウンロードします
    wget "https://github.com/exastro-suite/oase/releases/download/v${OASE_VER}/exastro-oase-${OASE_VER}.tar.gz"

    # 資材を展開します
    tar zxvf ./exastro-oase-${OASE_VER}.tar.gz -C /tmp
    ```

3. インストール設定ファイル(oase_answers.txt)を記載します。

    インストール設定ファイルの書き方は[マニュアル](https://exastro-suite.github.io/oase-docs/OASE_documents_ja/html/settings/installation.html)を参考にしてください。

    ```bash
    # エディタでインストール設定ファイルを編集します
    vi /tmp/oase/oase_install_package/install_scripts/oase_answers.txt
    ```

4. インストールを実行

    インストーラを実行すると15分～30分ぐらいでインストールが可能になります。

    ```bash
    # インストーラーを実行します
    cd /tmp/oase/oase_install_package/install_scripts
    sh oase_installer.sh
    ```

5. Exastro OASE にアクセスします。

    http://oase.exasmple.com

## もっと詳しく OASE について知る

詳しくは、コミュニティサイトに学習用教材や使用方法を掲載しています。

## 開発

### 言語・フレームワーク

|[<img src="https://img.shields.io/badge/-Python-F9DC3E.svg?logo=python&style=flat">](https://www.python.org/) | [<img src="https://img.shields.io/badge/-Django-092E20.svg?logo=django&style=flat">](https://www.djangoproject.com/)| [<img src="https://img.shields.io/badge/-OpenJDK-007396.svg?logo=Java&style=flat">](https://www.djangoproject.com/)| [<img src="https://img.shields.io/badge/Maven-C71A36.svg?logo=apachemaven&style=flat">](https://www.djangoproject.com/)|
|----|----|----|----|
|Python 3.6.8|Django 2.2.3|Java 1.8.0|Apache Maven 3.6.1|
