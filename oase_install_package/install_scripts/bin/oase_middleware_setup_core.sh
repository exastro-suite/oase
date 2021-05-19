#!/bin/bash
#   Copyright 2019 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
############################################################
#
# 【概要】
#    設定変更用ツール
#
############################################################

############################################################
# configuration functions

############################################################

create_oase_conf() {

cat << EOS > "$OASE_CONF_FILE"
LoadModule wsgi_module modules/mod_wsgi-py36.cpython-36m-x86_64-linux-gnu.so

WSGIPassAuthorization On
WSGIPythonPath ${oase_directory}/OASE/oase-root
WSGIScriptAlias / ${oase_directory}/OASE/oase-root/confs/frameworkconfs/wsgi.py
<Directory "${oase_directory}/OASE/oase-root/confs/frameworkconfs">
  <Files wsgi.py>
    Require all granted
  </Files>
</Directory>

Alias /static ${oase_directory}/OASE/oase-root/web_app/static
<Directory "${oase_directory}/OASE/oase-root/web_app/static">
  Require all granted
</Directory>

<VirtualHost *:443 >
  ServerName $OASE_DOMAIN
  ServerAlias *
  DocumentRoot ${oase_directory}/OASE/oase-root
  RedirectMatch ^/$ /oase_web/top/login

  ErrorLog   logs/oase-ssl-error_log
  CustomLog  logs/oase-ssl-access_log combined env=!no_log

  SSLEngine  on
  SSLCertificateFile /etc/pki/tls/certs/$CERTIFICATE_FILE
  SSLCertificateKeyFile /etc/pki/tls/certs/$PRIVATE_KEY_FILE
</VirtualHost>

<VirtualHost *:80 >
  ServerName any
  DocumentRoot ${oase_directory}/OASE/oase-root
  RedirectMatch ^/$ /oase_web/top/login

  ErrorLog   logs/oase-error_log
  CustomLog  logs/oase-access_log combined env=!no_log

  <Location / >
    Require all granted
  </Location>
</VirtualHost>

EOS

}


############################################################
create_drools_service() {

    if [ $# -ne 1 ]; then
        log "ERROR : missing required positional argument"
        log "INFO : Abort installation." 
        exit 1
    fi

cat << EOS > "$DROOLS_SERVICE_FILE"
[Unit]
Description=Drools
After=syslog.target network.target

[Service]
ExecStart=$1/wildfly-14.0.1.Final/bin/standalone.sh -c standalone-full.xml -Djboss.bind.address=0.0.0.0
ExecReload=/bin/kill -HUP $MAINPID
ExecStop=/bin/kill $MAINPID

[Install]
WantedBy=multi-user.target
EOS
}


############################################################
create_maven_conf_settings() {

if [ $# -ne 1 ]; then
    log "ERROR : missing required positional argument"
    log "INFO : Abort installation." 
    exit 1
fi

INSERT_STRING="\    <profile>\n" # 先頭バックスラッシュはインデントをいれるため
INSERT_STRING=$INSERT_STRING"      <id>jboss-ga</id>\n"
INSERT_STRING=$INSERT_STRING"      <repositories>\n"
INSERT_STRING=$INSERT_STRING"        <repository>\n"
INSERT_STRING=$INSERT_STRING"          <id>jboss-ga-repository</id>\n"
INSERT_STRING=$INSERT_STRING"          <name>JBoss GA Tech Preview Maven Repository</name>\n"
INSERT_STRING=$INSERT_STRING"          <url>https://maven.repository.redhat.com/ga/</url>\n"
INSERT_STRING=$INSERT_STRING"          <layout>default</layout>\n"
INSERT_STRING=$INSERT_STRING"          <releases>\n"
INSERT_STRING=$INSERT_STRING"            <enabled>true</enabled>\n"
INSERT_STRING=$INSERT_STRING"            <updatePolicy>never</updatePolicy>\n"
INSERT_STRING=$INSERT_STRING"          </releases>\n"
INSERT_STRING=$INSERT_STRING"          <snapshots>\n"
INSERT_STRING=$INSERT_STRING"            <enabled>false</enabled>\n"
INSERT_STRING=$INSERT_STRING"            <updatePolicy>never</updatePolicy>\n"
INSERT_STRING=$INSERT_STRING"          </snapshots>\n"
INSERT_STRING=$INSERT_STRING"        </repository>\n"
INSERT_STRING=$INSERT_STRING"      </repositories>\n"
INSERT_STRING=$INSERT_STRING"      <pluginRepositories>\n"
INSERT_STRING=$INSERT_STRING"        <pluginRepository>\n"
INSERT_STRING=$INSERT_STRING"          <id>jboss-ga-plugin-repository</id>\n"
INSERT_STRING=$INSERT_STRING"          <name>JBoss 7 Maven Plugin Repository</name>\n"
INSERT_STRING=$INSERT_STRING"          <url>https://maven.repository.redhat.com/ga/</url>\n"
INSERT_STRING=$INSERT_STRING"          <layout>default</layout>\n"
INSERT_STRING=$INSERT_STRING"          <releases>\n"
INSERT_STRING=$INSERT_STRING"            <enabled>true</enabled>\n"
INSERT_STRING=$INSERT_STRING"            <updatePolicy>never</updatePolicy>\n"
INSERT_STRING=$INSERT_STRING"          </releases>\n"
INSERT_STRING=$INSERT_STRING"          <snapshots>\n"
INSERT_STRING=$INSERT_STRING"            <enabled>false</enabled>\n"
INSERT_STRING=$INSERT_STRING"            <updatePolicy>never</updatePolicy>\n"
INSERT_STRING=$INSERT_STRING"          </snapshots>\n"
INSERT_STRING=$INSERT_STRING"        </pluginRepository>\n"
INSERT_STRING=$INSERT_STRING"      </pluginRepositories>\n"
INSERT_STRING=$INSERT_STRING"    </profile>"

# jboss設定用<profile>タグを挿入
SEARCH_STRING="  <profiles>"
line1=(`grep $SEARCH_STRING -n "$MAVEN_CONF_SETTINGS_FILE" | cut -d ":" -f 1`)

sed -i -e  "${line1}a ${INSERT_STRING}" $MAVEN_CONF_SETTINGS_FILE

}

############################################################
create_m2_settings() {
    if [ $# -ne 1 ]; then
        log "ERROR : missing required positional argument"
        log "INFO : Abort installation." 
        exit 1
    fi
# xml編集
cat << EOS > "$M2_SETTINGS_FILE"
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0 http://maven.apache.org/xsd/settings-1.0.0.xsd">

    <localRepository/>
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
EOS
}

############################################################
edit_standalone_full() {

    if [ $# -ne 1 ]; then
        log "ERROR : missing required positional argument"
        log "INFO : Abort installation." 
        exit 1
    fi

    # insert property
    sed -i -e '/<\/extensions>/a \    <system-properties>' $1
    sed -i -e '/<system-properties>/a \        <property name="org.kie.server.controller" value="http://localhost:8080/decision-central/rest/controller"\/>' $1
    sed -i -e '/<property name="org.kie.server.controller" value=/a \        <property name="org.kie.server.controller.user" value="'${RHDM_ADMINNAME}'"\/>' $1
    sed -i -e '/<property name="org.kie.server.controller.user" value="'${RHDM_ADMINNAME}'"\/>/a \        <property name="org.kie.server.controller.pwd" value="'${RHDM_PASSWORD}'"\/>' $1
    sed -i -e '/<property name="org.kie.server.controller.pwd" value="'${RHDM_PASSWORD}'"\/>/a \        <property name="org.kie.server.id" value="default-kieserver"\/>' $1
    sed -i -e '/<property name="org.kie.server.id" value="default-kieserver"\/>/a \        <property name="org.kie.server.location" value="http://localhost:8080/kie-server/services/rest/server"\/>' $1
    sed -i -e '/<property name="org.kie.server.location" value=/a \        <property name="org.kie.server.user" value="'${RHDM_ADMINNAME}'"\/>' $1
    sed -i -e '/<property name="org.kie.server.user" value="'${RHDM_ADMINNAME}'"\/>/a \        <property name="org.kie.server.pwd" value="'${RHDM_PASSWORD}'"\/>' $1
    sed -i -e '/<property name="org.kie.server.pwd" value="'${RHDM_PASSWORD}'"\/>/a \    <\/system-properties>' $1
}

############################################################
edit_oase_env() {

    if [ $# -ne 1 ]; then
        log "ERROR : missing required positional argument"
        log "INFO : Abort installation." 
        exit 1
    fi

    local python_module=`which python3`

    sed -i -e 's@^PYTHON_MODULE=.*$@PYTHON_MODULE='${python_module}'@' $1
    sed -i -e 's@^OASE_ROOT_DIR=.*$@OASE_ROOT_DIR='${OASE_ROOT_DIR}'@' $1
    sed -i -e 's@^JBOSS_HOME=.*$@JBOSS_HOME='${JBOSS_ROOT_DIR}'@' $1
}
################################################################################
make_backup_file() {

    if [ $# -ne 2 ]; then
        log "ERROR : missing required positional argument"
        log "INFO : Abort installation." 
        exit 1
    fi

    local _bk_file_name=$1.oase_bk

    if [ -e $_bk_file_name ]; then
        log "INFO : $_bk_file_name exists."
        result=$(cp -fp $1 $_bk_file_name$2 2>&1)
    else
        log "INFO : First backup $1"
        result=$(cp -fp $1 $_bk_file_name 2>&1)
    fi
    
    if [ $? -eq 1 ]; then
        log "ERROR : $result."
        log "INFO : Abort installation." 
        exit 1
    fi

    return 0

}

################################################################################
# main
NOW=$(date "+_%Y%m%d%H%M%S")

OASE_BIN_DIR=$(cd $(dirname $0);pwd)
OASE_INSTALL_SCRIPTS_DIR=$(cd $(dirname $OASE_BIN_DIR);pwd)
OASE_ANSWER_FILE=$OASE_INSTALL_SCRIPTS_DIR/oase_answers.txt

KERNEL_PARAM_FILE=/etc/sysctl.conf
OASE_CONF_FILE=/etc/httpd/conf.d/oase.conf
JBOSS_CONF_FILE=/etc/default/jboss-eap.conf

################################################################################
log "INFO : Start changing the settings."
################################################################################

OASE_DIR="${oase_directory}"
JBOSS_ROOT_DIR="${jboss_root_directory}"
OASE_ROOT_DIR="$OASE_DIR"/OASE/oase-root
SERVICE_FILE_DIR=/etc/systemd/system
OASE_JBOSS_EAP_RHEL_SH="$JBOSS_ROOT_DIR"/bin/init.d/jboss-eap-rhel.sh
INITD_DIR=/etc/init.d
JBOSS_EAP_RHEL_SH=$INITD_DIR/jboss-eap-rhel.sh
MAVEN_CONF_SETTINGS_FILE="${M2_HOME}"/conf/settings.xml
M2_SETTINGS_DIR=/root/.m2
M2_SETTINGS_FILE="${M2_SETTINGS_DIR}"/settings.xml
STANDALONE_FULL_FILE="${JBOSS_ROOT_DIR}"/wildfly-14.0.1.Final/standalone/configuration/standalone-full.xml
RHDM_ADMINNAME=${rhdm_adminname}
RHDM_PASSWORD=${rhdm_password}
OASE_ENV_DIR=${OASE_ROOT_DIR}/confs/backyardconfs/services
OASE_ENV_FILE=${OASE_ENV_DIR}/oase_env
DROOLS_SERVICE_FILE=/lib/systemd/system/drools.service
CERTIFICATE_PATH=${certificate_path}
PRIVATE_KEY_PATH=${private_key_path}
OASE_DOMAIN=${oase_domain}

# sysctl.conf
if [ ! -e "$KERNEL_PARAM_FILE" ]; then
    log ""$KERNEL_PARAM_FILE" not exists."
    log "INFO : Abort installation." 
    exit 1
fi

# Check if backup file exists
make_backup_file $KERNEL_PARAM_FILE $NOW

grep net.core.somaxconn "$KERNEL_PARAM_FILE" >/dev/null 2>&1
if [ $? -eq 1 ]; then
    echo net.core.somaxconn = 16384 >> "$KERNEL_PARAM_FILE"
else
    sed -i -e "/^net.core.somaxconn/s/.*/net.core.somaxconn = 16384/g" $KERNEL_PARAM_FILE
fi
sysctl -p >/dev/null 2>&1


# 秘密鍵と証明書のファイル名を取得(OASE自己証明書を作成する場合は証明書署名要求ファイル名も設定)
if [ "$CERTIFICATE_PATH" != "" -a "$PRIVATE_KEY_PATH" != "" ]; then
    CERTIFICATE_FILE=$(echo $(basename ${CERTIFICATE_PATH})) >/dev/null 2>&1
    PRIVATE_KEY_FILE=$(echo $(basename ${PRIVATE_KEY_PATH})) >/dev/null 2>&1
else
    CERTIFICATE_FILE="$OASE_DOMAIN.crt"
    PRIVATE_KEY_FILE="$OASE_DOMAIN.key"
    CSR_FILE="$OASE_DOMAIN.csr"
    echo "subjectAltName=DNS:$OASE_DOMAIN" > /tmp/san.txt
fi

if [ "${CERTIFICATE_PATH}" != "" -a "${PRIVATE_KEY_PATH}" != "" ]; then
    # CERTIFICATE_PATH と PRIVATE_KEY_PATH がoase_answers.txtに両方入力されている場合は、ユーザー指定の証明書・秘密鍵を設置
    # ユーザー指定証明書・秘密鍵設置
    if test -e "${CERTIFICATE_PATH}" ; then
        if test -e "${PRIVATE_KEY_PATH}" ; then
            # 両方の指定のパスにファイルが存在する場合のみ/etc/pki/tls/certs/にファイルをコピー
            cp -p "${CERTIFICATE_PATH}" /etc/pki/tls/certs/ >/dev/null 2>&1
            cp -p "${PRIVATE_KEY_PATH}" /etc/pki/tls/certs/ >/dev/null 2>&1
        else
            # 指定のパスにファイルがない場合は異常終了
            log "ERORR : ${PRIVATE_KEY_PATH} does not be found."
            log "INFO : Abort installation."
            rm -f /tmp/san.txt >/dev/null 2>&1
            exit 1
        fi
    else
        # 指定のパスにファイルがない場合は異常終了
        log "ERORR : ${CERTIFICATE_PATH} does not be found."
        log "INFO : Abort installation."
        rm -f /tmp/san.txt >/dev/null 2>&1
        exit 1
    fi
elif [ "${CERTIFICATE_PATH}" = "" -a "${PRIVATE_KEY_PATH}" = "" ]; then
    # CERTIFICATE_PATH と PRIVATE_KEY_PATH がどちらも入力されていない場合は、OASEで作成する自己証明書・秘密鍵を設置
    # 秘密鍵を生成
    openssl genrsa 2048 > /tmp/"$PRIVATE_KEY_FILE" 2>> "$OASE_INSTALL_LOG_FILE"
    # 証明書署名要求を生成
    expect -c "
    set timeout -1
    spawn openssl req -new -key /tmp/${PRIVATE_KEY_FILE} -out /tmp/${CSR_FILE}
    expect \"Country Name\"
    send \"JP\\r\"
    expect \"State or Province Name\"
    send \"\\r\"
    expect \"Locality Name\"
    send \"\\r\"
    expect \"Organization Name\"
    send \"\\r\"
    expect \"Organizational Unit Name\"
    send \"\\r\"
    expect \"Common Name\"
    send \"${OASE_DOMAIN}\\r\"
    expect \"Email Address\"
    send \"\\r\"
    expect \"A challenge password\"
    send \"\\r\"
    expect \"An optional company name\"
    send \"\\r\"
    interact
    " >> "$OASE_INSTALL_LOG_FILE" 2>&1
    # サーバ証明書を生成
    openssl x509 -days 3650 -req -signkey /tmp/"$PRIVATE_KEY_FILE" -extfile /tmp/san.txt < /tmp/"$CSR_FILE" > /tmp/"$CERTIFICATE_FILE" 2>> "$OASE_INSTALL_LOG_FILE"
    # 作成した証明書署名要求を削除
    rm -f /tmp/"$CSR_FILE" >/dev/null 2>&1
    rm -f /tmp/san.txt >/dev/null 2>&1
    mv /tmp/"$PRIVATE_KEY_FILE" /etc/pki/tls/certs/ >/dev/null 2>&1
    mv /tmp/"$CERTIFICATE_FILE" /etc/pki/tls/certs/ >/dev/null 2>&1
else
    # CERTIFICATE_PATH と PRIVATE_KEY_PATH どちらか一方だけ入力されている場合は異常終了
    if [ "${CERTIFICATE_PATH}" = "" ]; then
        log "ERORR : Should be Enter [certificate_path]."
        log 'INFO : Abort installation.'
        rm -f /tmp/san.txt >/dev/null 2>&1
        exit 1
    elif [ "${PRIVATE_KEY_PATH}" = "" ]; then
        log "ERORR : Should be Enter [private_key_path]."
        log 'INFO : Abort installation.'
        rm -f /tmp/san.txt >/dev/null 2>&1
        exit 1
    fi
fi

# /etc/pki/tls/certs/ に秘密鍵とサーバ証明書が設置できたかをチェック
if ! test -e /etc/pki/tls/certs/"$PRIVATE_KEY_FILE" ; then
    log "WARNING : Failed to place /etc/pki/tls/certs/$PRIVATE_KEY_FILE."
fi
if ! test -e /etc/pki/tls/certs/"$CERTIFICATE_FILE" ; then
    log "WARNING : Failed to place /etc/pki/tls/certs/$CERTIFICATE_FILE."
fi


# oase.conf
if [ -e "$OASE_CONF_FILE" ]; then

    # Check if backup file exists
    make_backup_file $OASE_CONF_FILE $NOW

fi

create_oase_conf

# maven conf settings
if [ -e "$MAVEN_CONF_SETTINGS_FILE" ]; then

    # Check if backup file exists
    make_backup_file $MAVEN_CONF_SETTINGS_FILE $NOW

fi

grep jboss-ga-repository "$MAVEN_CONF_SETTINGS_FILE" >/dev/null 2>&1
if [ $? -eq 1 ]; then
    create_maven_conf_settings "$MAVEN_CONF_SETTINGS_FILE"
fi

# .m2 settings
if [ ! -e "$M2_SETTINGS_DIR" ]; then
    mkdir $M2_SETTINGS_DIR
elif [ -e "$M2_SETTINGS_FILE" ]; then

    # Check if backup file exists
    make_backup_file $M2_SETTINGS_FILE $NOW

fi

create_m2_settings "$M2_SETTINGS_FILE"

# Decision Server settings
if [ ! -e "$STANDALONE_FULL_FILE".oase_bk ]; then
    if [ -e "$STANDALONE_FULL_FILE" ]; then

        # Check if backup file exists
        make_backup_file $STANDALONE_FULL_FILE $NOW

    fi

    edit_standalone_full "$STANDALONE_FULL_FILE"
fi

if [ -e "$JBOSS_CONF_FILE" ]; then

    # Check if backup file exists
    make_backup_file $JBOSS_CONF_FILE $NOW

fi

if [ -e "$DROOLS_SERVICE_FILE" ]; then

    # Check if backup file exists
    make_backup_file $DROOLS_SERVICE_FILE $NOW
fi

create_drools_service "$JBOSS_ROOT_DIR"

# drools.service
if [ ! -e "$DROOLS_SERVICE_FILE" ]; then
    log ""$DROOLS_SERVICE_FILE" not exists."
    log "INFO : Abort installation." 
    exit 1
fi

# oase_env settings
if [ ! -e "$OASE_ENV_DIR" ]; then
    mkdir $OASE_ENV_DIR
elif [ -e "$OASE_ENV_FILE" ]; then

    # Check if backup file exists
    make_backup_file $OASE_ENV_FILE $NOW

fi

edit_oase_env "$OASE_ENV_FILE"



log "INFO : Red Hat Decision Manager service startup completed."

################################################################################
log "INFO : Configuration change is complete."
################################################################################

