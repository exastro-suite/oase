![Exastro-OASE-logo2-rgb](https://user-images.githubusercontent.com/83527822/137485693-20c8eb39-4588-4fce-ad0c-4a6f96cacd86.png)
# Exastro Operation Autonomy Support Engine 🏝

[![download](https://img.shields.io/github/downloads/exastro-suite/oase/total.svg)](https://github.com/exastro-suite/oase/releases)
[![stars](https://img.shields.io/github/stars/exastro-suite/oase)](https://github.com/exastro-suite/oase)
[![Open issue](https://img.shields.io/github/issues/exastro-suite/oase)](https://github.com/exastro-suite/oase/issues)
[![Closed issue](https://img.shields.io/github/issues-closed/exastro-suite/oase)](https://github.com/exastro-suite/oase/issues)
[![LICENSE](https://img.shields.io/github/license/exastro-suite/oase.svg)](https://github.com/exastro-suite/oase/blob/master/LICENSE )

[[日本語](./README_ja.md)]

---

Exastro **O**peration **A**utonomy **S**upport **E**ngine (Exastro **OASE**) is an open source to support system operation, especially monitoring operator work in case of failure in the system.

I hope you a meaningful and creative time 🏄

---

## Features

- ⚙**Automate Operation** Automatically sorts and deals with monitoring events.
- 👫**Cooperation function** Integration with various monitoring applications and handling software.
- 📈**Interface** Beautiful graphs, spreadsheets for rule management.

### Monitoring applications that can be integrated

You can receive alert messages by either pull type or push type.
Pull type can be used only with pre-defined monitoring adapters, but it can be used with many more monitoring applications by using RESTfull API.

#### **Pull** type (with adapter)

- [**Zabbix**](https://github.com/zabbix/zabbix)
- [**Grafana**](https://github.com/grafana/grafana)
- [**Prometheus**](https://github.com/prometheus/prometheus)
#### **Push** type (without adapter)

- [**RESTful API**](https://exastro-suite.github.io/oase-docs/OASE_documents_ja/html/api/01_events_request.html)

### Automation software that can be integrated

- [**Exastro IT Automation**](https://github.com/exastro-suite/it-automation)
<!--
- [**ServiceNow Workflow**](https://www.servicenow.com/)
-->

### Incident Management

By linking with ITSM of [ServiceNow](https://www.servicenow.com/), you can perform incident management such as creating incident and closing.

<!--
By linking with [ServiceNow](https://www.servicenow.com/)'s ITSM, it is possible to manage a series of incidents from incident origination, processing, processing completion, and closing.
-->

<!--
### Authentication Management
By linking with [ServiceNow](https://www.servicenow.com/)'s ITSM, it is possible to link with approval flows such as permission and rejection of actions.
-->
## Installation

Installation instructions can be found below, but if you want to know more, check out the [community site](https://exastro-suite.github.io/oase-docs/learn_ja.html#introduction).

### Operating requirements

It will run in one of the following environments.

|<img src="https://img.shields.io/badge/-CentOS-A1077C.svg?logo=centos&style=flat">|<img src="https://img.shields.io/badge/-RedHat- EE0000.svg?logo=red-hat&style=flat">|<img src="https://img.shields.io/badge/-Docker-FFFFFF.svg?logo=docker&style=flat">|
|----|----|----|
|CentOS 7| Red Hat Enterprise Linux 7 or 8|x86_64|

### 🐳 Docker 🐷

The Docker version is the easiest way to use the OASE.

1. You can use Exastro OASE instantly with Docker.

    ```bash
    docker run --privileged --add-host=exastro-oase:127.0.0.1 -d -p 8080:80 -p 10443:443 --name exastro-oase exastro/oase 
    ```

2. access Exastro OASE

    http://oase.exasmple.com:8080

### 🗿 Traditional method 🐶

Choose this option if you need customization or if you cannot use a container environment.

1. Install the necessary packages for the installation.

    ```bash
    # You will need GCC and Wget
    yum install -y gcc wget
    ```

2. Download and extract the release materials.

    ```bash
    # Change the directory to work in
    cd /tmp

    # Put the version to be downloaded into a variable.
    # OASE_VER=X.X.X
    #X.X.X
    # Example: 1.4.0
    OASE_VER=1.4.0

    # Download the materials
    wget "https://github.com/exastro-suite/oase/releases/download/v${OASE_VER}/exastro-oase-${OASE_VER}.tar.gz"

    # Extract the material
    tar zxvf . /exastro-oase-${OASE_VER}.tar.gz -C /tmp
    ```

3. write the installation configuration file (oase_answers.txt).

    Please refer to the [manual](https://exastro-suite.github.io/oase-docs/OASE_documents_ja/html/settings/installation.html) for how to write the installation configuration file.

    ```bash
    # Edit the installation configuration file with an editor
    vi /tmp/oase/oase_install_package/install_scripts/oase_answers.txt
    ```

4. run the installation

    After running the installer, the installation will take about 15 to 30 minutes.

    ```bash
    # Run installer
    cd /tmp/oase/oase_install_package/install_scripts
    sh oase_installer.sh
    ```

5. Access Exastro OASE.

    http://oase.exasmple.com
## Learn more

For more information, you can find learning materials and instructions for use on the community site.

## Development

### Languages and Frameworks

|[<img src="https://img.shields.io/badge/-Python-F9DC3E.svg?logo=python&style=flat">](https://www.python.org/) | [<img src="https://img.shields.io/badge/-Django-092E20.svg?logo=django&style=flat">](https://www.djangoproject.com/)| [<img src="https://img.shields.io/badge/-OpenJDK-007396.svg?logo=Java&style=flat">](https://www.djangoproject.com/)| [<img src="https://img.shields.io/badge/Maven-C71A36.svg?logo=apachemaven&style=flat">](https://www.djangoproject.com/)|
|----|----|----|----|
|Python 3.6.8|Django 2.2.3|Java 1.8.0|Apache Maven 3.6.1|
