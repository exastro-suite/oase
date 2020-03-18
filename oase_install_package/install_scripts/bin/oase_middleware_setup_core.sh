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
create_nginx_conf() {

cat << EOS > "$NGINX_CONF_FILE"

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


http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    log_format  main  '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                      '\$status \$body_bytes_sent "\$http_referer" '
                      '"\$http_user_agent" "\$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile        on;
    #tcp_nopush     on;

    keepalive_timeout  65;

    #gzip  on;

    include /etc/nginx/conf.d/*.conf;
}
EOS

}

############################################################
create_oase_conf() {

    if [ $# -ne 1 ]; then
        log "ERROR : missing required positional argument"
        log "INFO : Abort installation." 
        exit 1
    fi

cat << EOS > "$OASE_CONF_FILE"
server {
    listen 80;
    server_name exastro-oase;
    return 301 https://\$host\$request_uri;
}

server {
   listen  443  ssl;

   ssl_certificate  $1/exastro-oase.crt;
   ssl_certificate_key  $1/cakey-nopass.pem;

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
       alias ${OASE_ROOT_DIR}/web_app/static;
   }

   error_page   500 502 503 504  /50x.html;
   location = /50x.html {
       root   /usr/share/nginx/html;
   }
}
EOS

}

############################################################
create_uwsgi_ini() {

    if [ $# -ne 2 ]; then
        log "ERROR : missing required positional argument"
        log "INFO : Abort installation." 
        exit 1
    fi
    
    CPU_CORE_COUNT=$(grep physical.id /proc/cpuinfo | sort -u | wc -l)
    PROCESSES=$(expr $CPU_CORE_COUNT \* 2)

cat << EOS > "$UWSGI_INI_FILE"
[uwsgi]
chdir=$1
module=web_app
master=true
socket=$2/uwsgi.sock
chmod-socket=666
wsgi-file=$1/confs/frameworkconfs/wsgi.py
log-format = [pid: %(pid)|app: -|req: -/-] %(addr) (%(user)) {%(vars) vars in %(pktsize) bytes} [ %(ctime) ] %(method) %(uri) => generated %(rsize) bytes in %(msecs) msecs (%(proto) %(status)) %(headers) headers in %(hsize) bytes (%(switches) switches on core %(core))
logto=/var/log/uwsgi/uwsgi.log
processes=$PROCESSES
threads=2
listen=16384
EOS
}

############################################################
create_uwsgi_service() {

    if [ $# -ne 1 ]; then
        log "ERROR : missing required positional argument"
        log "INFO : Abort installation." 
        exit 1
    fi

cat << EOS > "$UWSGI_SERVICE_FILE"
[Unit]
Description=uWSGI
After=syslog.target network.target mysqld.service

[Service]
ExecStart=$1 --ini $UWSGI_INI_FILE
ExecReload=/bin/kill -HUP \$MAINPID
ExecStop=/bin/kill -INT \$MAINPID
Restart=always
Type=notify
StandardError=syslog
NotifyAccess=all

[Install]
WantedBy=multi-user.target
EOS
}

############################################################
create_jboss_conf() {

    if [ $# -ne 1 ]; then
        log "ERROR : missing required positional argument"
        log "INFO : Abort installation." 
        exit 1
    fi

cat << EOS > "$JBOSS_CONF_FILE"
# General configuration for the init.d scripts,
# not necessarily for JBoss EAP itself.
# default location: /etc/default/jboss-eap

## Location of JDK
# JAVA_HOME="/usr/lib/jvm/default-java"
JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk

## Location of JBoss EAP
# JBOSS_HOME="/opt/jboss-eap"
JBOSS_HOME=$1

## The username who should own the process.
# JBOSS_USER=jboss-eap
JBOSS_USER=root

## The mode JBoss EAP should start, standalone or domain
# JBOSS_MODE=standalone
JBOSS_MODE=standalone

## Configuration for standalone mode
# JBOSS_CONFIG=standalone.xml
JBOSS_CONFIG=standalone-full.xml

## Configuration for domain mode
# JBOSS_DOMAIN_CONFIG=domain.xml
# JBOSS_HOST_CONFIG=host-master.xml

## The amount of time to wait for startup
#STARTUP_WAIT=60

## The amount of time to wait for shutdown
#SHUTDOWN_WAIT=60

## Location to keep the console log
# JBOSS_CONSOLE_LOG="/var/log/jboss-eap/console.log"
JBOSS_CONSOLE_LOG="/var/log/jboss-eap/console.log"

## Additionals args to include in startup
# JBOSS_OPTS="--admin-only -b 127.0.0.1"
JBOSS_OPTS="-Dfile.encoding=UTF-8 -Djboss.bind.address=0.0.0.0 -Ddrools.dateformat=\"yyyy-MM-dd HH:mm\""
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
    sed -i -e '/<property name="org.kie.server.pwd" value="${VAULT::vaulted::controller.password::1}"\/>/a \        <property name="kie.maven.settings.custom" value="/opt/apache-maven/conf/settings.xml"\/>' $1

    # change property
    sed -i -e 's/<property name="org.kie.server.controller.user" value="controllerUser"\/>/<property name="org.kie.server.controller.user" value="'${RHDM_ADMINNAME}'"\/>/g' $1
    sed -i -e 's/<property name="org.kie.server.controller.pwd" value="${VAULT::vaulted::controller.password::1}"\/>/<property name="org.kie.server.controller.pwd" value="'${RHDM_PASSWORD}'"\/>/g' $1
    sed -i -e 's/<property name="org.kie.server.user" value="controllerUser"\/>/<property name="org.kie.server.user" value="'${RHDM_ADMINNAME}'"\/>/g' $1
    sed -i -e 's/<property name="org.kie.server.pwd" value="${VAULT::vaulted::controller.password::1}"\/>/<property name="org.kie.server.pwd" value="'${RHDM_PASSWORD}'"\/>/g' $1
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
NGINX_CONF_FILE=/etc/nginx/nginx.conf
OASE_CONF_FILE=/etc/nginx/conf.d/oase.conf
UWSGI_SOCK_DIR=/home/uWSGI
JBOSS_CONF_FILE=/etc/default/jboss-eap.conf

################################################################################
log "INFO : Start changing the settings."
################################################################################

OASE_DIR="${oase_directory}"
JBOSS_ROOT_DIR="${jboss_root_directory}"
OASE_ROOT_DIR="$OASE_DIR"/OASE/oase-root
UWSGI_LOG_DIR=/var/log/uwsgi
UWSGI_INI_FILE="$OASE_ROOT_DIR"/uwsgi.ini
OASE_NGINX_SERVICE_FILE="$OASE_DIR"/OASE/tool/service/nginx.service
SERVICE_FILE_DIR=/etc/systemd/system
NGINX_SERVICE_FILE="$SERVICE_FILE_DIR"/nginx.service
UWSGI_SERVICE_FILE="$SERVICE_FILE_DIR"/uwsgi.service
OASE_JBOSS_EAP_RHEL_SH="$JBOSS_ROOT_DIR"/bin/init.d/jboss-eap-rhel.sh
INITD_DIR=/etc/init.d
JBOSS_EAP_RHEL_SH=$INITD_DIR/jboss-eap-rhel.sh
MAVEN_CONF_SETTINGS_FILE="${M2_HOME}"/conf/settings.xml
M2_SETTINGS_DIR=/root/.m2
M2_SETTINGS_FILE="${M2_SETTINGS_DIR}"/settings.xml
STANDALONE_FULL_FILE="${JBOSS_ROOT_DIR}"/standalone/configuration/standalone-full.xml
RHDM_ADMINNAME=${rhdm_adminname}
RHDM_PASSWORD=${rhdm_password}
OASE_ENV_DIR=${OASE_ROOT_DIR}/confs/backyardconfs/services
OASE_ENV_FILE=${OASE_ENV_DIR}/oase_env


if [ ! -e "$UWSGI_SOCK_DIR" ]; then
    mkdir -m 755 "$UWSGI_SOCK_DIR"
fi

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


# nginx.conf
if [ ! -e "$NGINX_CONF_FILE" ]; then
    log ""$NGINX_CONF_FILE" not exists."
    log "INFO : Abort installation." 
    exit 1
fi

# Check if backup file exists
make_backup_file $NGINX_CONF_FILE $NOW

create_nginx_conf

# oase.conf
if [ -e "$OASE_CONF_FILE" ]; then

    # Check if backup file exists
    make_backup_file $OASE_CONF_FILE $NOW

fi

create_oase_conf "$OASE_ROOT_DIR"

# uwsgi.ini
if [ ! -e "$UWSGI_LOG_DIR" ]; then
    mkdir -p "$UWSGI_LOG_DIR"
fi

if [ -e "$UWSGI_INI_FILE" ]; then

    # Check if backup file exists
    make_backup_file $UWSGI_INI_FILE $NOW

fi

create_uwsgi_ini "$OASE_ROOT_DIR" "$UWSGI_SOCK_DIR"

# nginx.service
if [ ! -e "$OASE_NGINX_SERVICE_FILE" ]; then
    log ""$OASE_NGINX_SERVICE_FILE" not exists."
    log "INFO : Abort installation." 
    exit 1
fi

if [ -e "$NGINX_SERVICE_FILE" ]; then

    # Check if backup file exists
    make_backup_file $NGINX_SERVICE_FILE $NOW

fi

cp -fp "$OASE_NGINX_SERVICE_FILE" "$NGINX_SERVICE_FILE"


# uwsgi.service
if [ -e "$UWSGI_SERVICE_FILE" ]; then

    # Check if backup file exists
    make_backup_file $UWSGI_SERVICE_FILE $NOW

fi

uwsgi_command=`which uwsgi`
create_uwsgi_service "$uwsgi_command"

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
if [ -e "$STANDALONE_FULL_FILE" ]; then

    # Check if backup file exists
    make_backup_file $STANDALONE_FULL_FILE $NOW

fi

edit_standalone_full "$STANDALONE_FULL_FILE"

if [ -e "$JBOSS_CONF_FILE" ]; then

    # Check if backup file exists
    make_backup_file $JBOSS_CONF_FILE $NOW

fi

create_jboss_conf "$JBOSS_ROOT_DIR"
chmod +x "$JBOSS_CONF_FILE"

# jboss-eap-rhel.sh
if [ ! -e "$OASE_JBOSS_EAP_RHEL_SH" ]; then
    log ""$OASE_JBOSS_EAP_RHEL_SH" not exists."
    log "INFO : Abort installation." 
    exit 1
fi

cp -fp "$OASE_JBOSS_EAP_RHEL_SH" "$JBOSS_EAP_RHEL_SH"
chmod +x "$JBOSS_EAP_RHEL_SH"

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

