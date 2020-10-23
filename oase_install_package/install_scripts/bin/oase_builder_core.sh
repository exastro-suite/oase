#!/bin/bash
#   Copyright 2020 NEC Corporation
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
#############################################################
#
# 【概要】
#    ・OASE環境構築に必要なライブラリを収集
#    ・OASE環境を構築
#
#
#############################################################

################################################################################
# generic functions (should have no dependencies on global variables)

log() {
    echo "["`date +"%Y-%m-%d %H:%M:%S"`"] $1" | tee -a "$OASE_INSTALL_LOG_FILE"
}

func_exit() {
    if [ -e /tmp/pear ]; then
        rm -rf /tmp/pear >> "$OASE_INSTALL_LOG_FILE" 2>&1
    fi
    exit
}

backup_suffix() {
    echo "."`date +%Y%m%d-%H%M%S.bak`
}

list_yum_package() {
    local dst_dir=$1

    if [ -d $dst_dir ]; then
        find $dst_dir -type f | grep -E '\.rpm$' | tr "\n" " "
    fi
}

list_pip_package() {
    local dst_dir=$1

    if [ -d $dst_dir ]; then
        find $dst_dir -type f | grep -E '\.(whl|tar.gz)$' | tr "\n" " "
    fi
}

yum_install() {
    #if [ "${MODE}" == "remote" -o "$LINUX_OS" == "RHEL7" -o "$LINUX_OS" == "CentOS7" ]; then
    #    if [ $# -gt 0 ]; then
    echo "----------Installation[$@]----------" >> "$OASE_INSTALL_LOG_FILE" 2>&1
    #Installation
    yum install -y "$@" >> "$OASE_INSTALL_LOG_FILE" 2>&1

    #Check installation
    for key in $@; do
        echo "----------Check installation[$key]----------" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        yum install -y "$key" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        if [ $? != 0 ]; then
            log "ERROR:Installation failed[$key]"
            func_exit
        fi
    done
    #    fi
    #fi
}


yum_package_check() {
    if [ $# -gt 0 ];then
        for key in $@; do
            echo "----------Check Installed packages[$key]----------" >> "$OASE_INSTALL_LOG_FILE" 2>&1
            yum list installed | grep "$key" >> "$OASE_INSTALL_LOG_FILE" 2>&1
            if [ $? -ne 0 ]; then
                log "ERROR:Package not installed [$key]"
                func_exit
            fi
        done
    fi
}


create_repo_check(){
    if [ $# -gt 0 ];then
        for key in $@; do
            echo "----------Check Creation repository[$key]----------" >> "$OASE_INSTALL_LOG_FILE" 2>&1
            yum repolist | grep "$key" >> "$OASE_INSTALL_LOG_FILE" 2>&1
            if [ $? -eq 0 ]; then
                echo "Successful repository acquisition" >> "$OASE_INSTALL_LOG_FILE" 2>&1
            else
                return 1
            fi
        done
    fi
}


yum_repository() {
    if [ $# -gt 0 ]; then
        local repo=$1

        # no repo to be installed if the first argument starts "-".
        if [[ "$repo" =~ ^[^-] ]]; then
            if [ "$LINUX_OS" == "RHEL7" ]; then
                rpm -ivh "$repo" >> "$OASE_INSTALL_LOG_FILE" 2>&1
            else
                yum install -y "$repo" >> "$OASE_INSTALL_LOG_FILE" 2>&1
            fi

            # Check Creating repository
            if [[ "$repo" =~ .*epel-release.* ]]; then
                create_repo_check epel >> "$OASE_INSTALL_LOG_FILE" 2>&1
            elif [[ "$repo" =~ .*remi-release-7.* ]]; then
                create_repo_check remi-safe >> "$OASE_INSTALL_LOG_FILE" 2>&1
            fi
            if [ $? -ne 0 ]; then
                log "ERROR:Failed to get repository"
                func_exit
            fi

            shift
        fi

        if [ $# -gt 0 ]; then
            if [ "${LINUX_OS}" == "CentOS7" -o "${LINUX_OS}" == "RHEL7" ]; then
                yum-config-manager "$@" >> "$OASE_INSTALL_LOG_FILE" 2>&1
            elif [ "${LINUX_OS}" == "CentOS8" -o "${LINUX_OS}" == "RHEL8" ]; then
                dnf config-manager "$@" >> "$OASE_INSTALL_LOG_FILE" 2>&1
            fi

            # Check Creating repository
            if [ "${REPOSITORY}" != "yum_all" ]; then
               case "${linux_os}" in
                    "CentOS7") create_repo_check remi-php72 >> "$OASE_INSTALL_LOG_FILE" 2>&1 ;;
                    "RHEL7") create_repo_check remi-php72 rhel-7-server-optional-rpms  >> "$OASE_INSTALL_LOG_FILE" 2>&1 ;;
                    "RHEL7_AWS") create_repo_check remi-php72 rhui-rhel-7-server-rhui-optional-rpms  >> "$OASE_INSTALL_LOG_FILE" 2>&1 ;;
                    "CentOS8") create_repo_check PowerTools >> "$OASE_INSTALL_LOG_FILE" 2>&1 ;;
                    "RHEL8") create_repo_check codeready-builder-for-rhel-8 >> "$OASE_INSTALL_LOG_FILE" 2>&1 ;;
                    "RHEL8_AWS") create_repo_check codeready-builder-for-rhel-8-rhui-rpms >> "$OASE_INSTALL_LOG_FILE" 2>&1 ;;
                esac 
                if [ $? -ne 0 ]; then
                   log "ERROR:Failed to get repository"
                    func_exit
                fi
            fi
            yum clean all >> "$OASE_INSTALL_LOG_FILE" 2>&1
        fi
    fi
}


################################################################################
# configuration functions

# create local yum repository
configure_yum_env() {

    #mirror list is Japan only.
    if [ ! -e /etc/yum/pluginconf.d/fastestmirror.conf ]; then
        if [ "$LINUX_OS" == "RHEL7" ]; then
            yum --enablerepo=rhel-7-server-optional-rpms install -y yum-plugin-fastestmirror >> "$OASE_INSTALL_LOG_FILE" 2>&1
            ls /etc/yum/pluginconf.d/fastestmirror.conf >> "$OASE_INSTALL_LOG_FILE" 2>&1 | xargs grep "include_only=.jp" >> "$OASE_INSTALL_LOG_FILE" 2>&1

            if [ $? -ne 0 ]; then
                sed -i '$a\include_only=.jp' /etc/yum/pluginconf.d/fastestmirror.conf >> "$OASE_INSTALL_LOG_FILE" 2>&1
            fi
        fi
    fi

    # install yum-utils and createrepo
    #if [ "${LINUX_OS}" == "CentOS7" -o "${LINUX_OS}" == "RHEL7" ]; then
    #    log "yum-utils and createrepo install"
    #    if [ "${MODE}" == "remote" ]; then
    #        yum_install ${YUM__ENV_PACKAGE}
    #    fi
    #    yum_package_check yum-utils createrepo
    #fi

    #if [ "${MODE}" == "remote" ]; then
    #    yum_repository ${YUM_REPO_PACKAGE["yum-env-enable-repo"]}
    #    yum_repository ${YUM_REPO_PACKAGE["yum-env-disable-repo"]}
    #fi
    #yum clean all >> "$OASE_INSTALL_LOG_FILE" 2>&1
}


# python
configure_python() {
    # package
    #-----------------------------------------------------------
    # directory

    YUM_ENV_PACKAGE_LOCAL_DIR="${LOCAL_DIR["yum"]}/yum-env"
    YUM_ALL_PACKAGE_LOCAL_DIR="${LOCAL_DIR["yum"]}/yum_all"

    YUM_ENV_PACKAGE_DOWNLOAD_DIR="${DOWNLOAD_DIR["yum"]}/yum-env"
    YUM_ALL_PACKAGE_DOWNLOAD_DIR="${DOWNLOAD_DIR["yum"]}/yum_all"

    #-----------------------------------------------------------

    # install some packages
    yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm >> "$OASE_INSTALL_LOG_FILE" 2>&1
    yum-config-manager --enable rhel-7-server-optional-rpms >> "$OASE_INSTALL_LOG_FILE" 2>&1
    yum_install ${YUM_PACKAGE["python"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1

    # python link
    ln -s /bin/python3.6 /bin/python3 >> "$OASE_INSTALL_LOG_FILE" 2>&1
    ln -sf /bin/python3 /bin/python >> "$OASE_INSTALL_LOG_FILE" 2>&1
    python3.6 -m pip install --upgrade pip >> "$OASE_INSTALL_LOG_FILE" 2>&1

    # pika
    pip3 install pika >> "$OASE_INSTALL_LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        log "ERROR:Installation failed pika"
        func_exit
    fi

    # retry
    pip3 install retry >> "$OASE_INSTALL_LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        log "ERROR:Installation failed retry"
        func_exit
    fi

    #!/usr/bin/python → #!/usr/bin/python2.7
    cp /usr/bin/yum /usr/bin/old_yum
    sed  -i -e 's/python/python2.7/' /usr/bin/yum

    cp /usr/libexec/urlgrabber-ext-down /usr/libexec/old_urlgrabber-ext-down
    sed  -i -e 's/python/python2.7/' /usr/libexec/urlgrabber-ext-down

}

# memcache
configure_memcache() {
    # install some packages
    yum_install ${YUM_PACKAGE["memcached"]}
    # Check installation httpd packages
    yum_package_check ${YUM_PACKAGE["memcached"]}

    # enable and start memcached
    #--------CentOS7/8,RHEL7/8--------
    systemctl enable memcached >> "$OASE_INSTALL_LOG_FILE" 2>&1

}

# RabbitMQ Server
configure_rabbitmq() {
    # install some packages
    yum_install ${YUM_PACKAGE["erlang"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1
    # Check installation erlang packages
    yum_package_check ${YUM_PACKAGE["erlang"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1

    # install some packages
    #yum_install ${YUM_PACKAGE["rabbitmq-server"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1
    yum -y install rabbitmq-server --enablerepo=epel >> "$OASE_INSTALL_LOG_FILE" 2>&1

    # Check installation RabbitMQ packages
    #yum_package_check ${YUM_PACKAGE["rabbitmq-server"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1
    yum list installed | grep rabbitmq-server >> "$OASE_INSTALL_LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        log "ERROR:Package not installed rabbitmq-server"
        func_exit
    fi

    rabbitmq-plugins list >> "$OASE_INSTALL_LOG_FILE" 2>&1

    # enable and start rabbitmq management
    #--------CentOS7/8,RHEL7/8--------
    rabbitmq-plugins enable rabbitmq_management >> "$OASE_INSTALL_LOG_FILE" 2>&1

    rabbitmq-plugins list >> "$OASE_INSTALL_LOG_FILE" 2>&1

    # enable and start rabbitmq server
    #--------CentOS7/8,RHEL7/8--------
    systemctl start rabbitmq-server >> "$OASE_INSTALL_LOG_FILE" 2>&1
    systemctl enable rabbitmq-server >> "$OASE_INSTALL_LOG_FILE" 2>&1

    # user add
    rabbitmqctl add_user ${RabbitMQ_username} ${RabbitMQ_password} >> "$OASE_INSTALL_LOG_FILE" 2>&1

    # user chmod
    rabbitmqctl set_user_tags ${RabbitMQ_username} administrator >> "$OASE_INSTALL_LOG_FILE" 2>&1
    rabbitmqctl set_permissions -p / ${RabbitMQ_username} ".*" ".*" ".*" >> "$OASE_INSTALL_LOG_FILE" 2>&1

}

# MySQL Server
configure_mysql() {
    #repo get
    cd /tmp
    wget --no-check-certificate https://dev.mysql.com/get/mysql80-community-release-el7-3.noarch.rpm >> "$OASE_INSTALL_LOG_FILE" 2>&1
    rpm -Uvh mysql80-community-release-el7-3.noarch.rpm >> "$OASE_INSTALL_LOG_FILE" 2>&1

    # install some packages
    yum -y --enablerepo mysql80-community install ${YUM_PACKAGE["mysql-server"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1
    # Check installation erlang packages
    yum_package_check ${YUM_PACKAGE["mysql"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1

    # enable and start mysql server
    systemctl start  mysqld >> "$OASE_INSTALL_LOG_FILE" 2>&1
    systemctl enable  mysqld >> "$OASE_INSTALL_LOG_FILE" 2>&1

    # initial password change
    #mysql_password=`cat /var/log/mysqld.log | grep "A temporary password is generated for" | cut -f 4 -d ":"`
    mysql_password=`cat /var/log/mysqld.log | grep "A temporary password is generated for" | awk '{print substr($0, index($0, "root@localhost:"))}' | sed -e 's/root@localhost: //'` >> "$OASE_INSTALL_LOG_FILE" 2>&1

    yum -y install ${YUM_PACKAGE["expect"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1
    yum_package_check ${YUM_PACKAGE["expect"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1

    expect -c "
        set timeout -1
        spawn mysql -u root -p
        expect \"Enter password:\"
        send \""${mysql_password}\\r"\"
        expect \"mysql>\"
        send \"ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'passwordPASSWORD@999';\\r\"
        expect \"mysql>\"
        send \"SET GLOBAL validate_password.length=4;\\r\"
        expect \"mysql>\"
        send \"SET GLOBAL validate_password.mixed_case_count=0;\\r\"
        expect \"mysql>\"
        send \"SET GLOBAL validate_password.number_count=0;\\r\"
        expect \"mysql>\"
        send \"SET GLOBAL validate_password.special_char_count=0;\\r\"
        expect \"mysql>\"
        send \"SET GLOBAL validate_password.policy=LOW;\\r\"
        expect \"mysql>\"
        send \"show variables like '%validate_password%';\\r\"
        expect \"mysql>\"
        send \"ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${db_root_password}';\\r\"
        expect \"mysql>\"
        send \"status\\r\"
        expect \"mysql>\"
        send \"quit\\r\"
    " >> "$OASE_INSTALL_LOG_FILE" 2>&1
    
    # user add
    #expect -c "
    #    set timeout -1
    #    spawn mysql -u root -p
    #    expect \"Enter password:\"
    #    send \""${db_root_password}\\r"\"
    #    expect \"mysql>\"
    #    send \"CREATE DATABASE ${db_name} CHARACTER SET utf8;\\r\"
    #    expect \"mysql>\"
    #    send \"CREATE USER ${db_username} IDENTIFIED BY '${db_password}';\\r\"
    #    expect \"mysql>\"
    #    send \"GRANT ALL ON ${db_name}.* TO ${db_username};\\r\"
    #    expect \"mysql>\"
    #    send \"quit\\r\"
    #" >> "$OASE_INSTALL_LOG_FILE" 2>&1
    
    mv /etc/my.cnf /etc/old_my.cnf >> "$OASE_INSTALL_LOG_FILE" 2>&1
    cat << EOS > "/etc/my.cnf"
# For advice on how to change settings please see
# http://dev.mysql.com/doc/refman/8.0/en/server-configuration-defaults.html

[mysqld]
#
# Remove leading # and set to the amount of RAM for the most important data
# cache in MySQL. Start at 70% of total RAM for dedicated server, else 10%.
# innodb_buffer_pool_size = 128M
#
# Remove the leading "# " to disable binary logging
# Binary logging captures changes between backups and is enabled by
# default. It's default setting is log_bin=binlog
# disable_log_bin
#
# Remove leading # to set options mainly useful for reporting servers.
# The server defaults are faster for transactions and fast SELECTs.
# Adjust sizes as needed, experiment to find the optimal values.
# join_buffer_size = 128M
# sort_buffer_size = 2M
# read_rnd_buffer_size = 2M
#
# Remove leading # to revert to previous value for default_authentication_plugin,
# this will increase compatibility with older clients. For background, see:
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
EOS
    
    #mysql restart
    systemctl restart mysqld  >> "$OASE_INSTALL_LOG_FILE" 2>&1
    
    #mysqlclient install
    yum -y --enablerepo mysql80-community install ${YUM_PACKAGE["mysql-community-devel"]}  >> "$OASE_INSTALL_LOG_FILE" 2>&1
    
    # Check installation  mysql-community-devel packages
    yum_package_check ${YUM_PACKAGE["mysql-community-devel"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1
    
    #pip install mysqlclient
    pip install mysqlclient >> "$OASE_INSTALL_LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        log "ERROR:Installation failed mysqlclient"
        func_exit
    fi
    
    #pip install mysql_connector_python
    pip install mysql_connector_python >> "$OASE_INSTALL_LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        log "ERROR:Installation failed mysql_connector_python"
        func_exit
    fi
    
    pip3 list >> "$OASE_INSTALL_LOG_FILE" 2>&1
}

#Nginx install
configure_nginx(){

    yum -y install ${YUM_PACKAGE["nginx"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1
    # Check installation  nginx packages
    yum_package_check ${YUM_PACKAGE["nginx"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1
    
    systemctl start nginx >> "$OASE_INSTALL_LOG_FILE" 2>&1
    systemctl stop nginx >> "$OASE_INSTALL_LOG_FILE" 2>&1
}

#uWSGI install and setting
configure_uwsgi(){
    #pip install uwsgi
    pip install uwsgi >> "$OASE_INSTALL_LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        log "ERROR:Installation failed uwsgi"
        func_exit
    fi
    
    uwsgi --version >> "$OASE_INSTALL_LOG_FILE" 2>&1
}

#JAVA install
configure_java(){
    #openjdk install
    yum -y install ${YUM_PACKAGE["java"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1
    # Check installation  java packages
    yum_package_check ${YUM_PACKAGE["java"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1
    yum list | grep java-1.8.0 >> "$OASE_INSTALL_LOG_FILE" 2>&1
}

#Drools install
configure_drools(){
    #WildFly install
    mkdir -p ${wildfly_root_directory} >> "$OASE_INSTALL_LOG_FILE" 2>&1
    cd ${wildfly_root_directory} >> "$OASE_INSTALL_LOG_FILE" 2>&1
    wget https://download.jboss.org/wildfly/14.0.1.Final/wildfly-14.0.1.Final.tar.gz >> "$OASE_INSTALL_LOG_FILE" 2>&1
    tar -xzvf wildfly-14.0.1.Final.tar.gz >> "$OASE_INSTALL_LOG_FILE" 2>&1

    #Owner change
    chown -R root:root wildfly-14.0.1.Final
    rm -f wildfly-14.0.1.Final.tar.gz

    #Business entral Workbench WildFly 14 War install
    cd ${wildfly_root_directory}/wildfly-14.0.1.Final/standalone/deployments >> "$OASE_INSTALL_LOG_FILE" 2>&1
    wget https://download.jboss.org/drools/release/7.22.0.Final/business-central-7.22.0.Final-wildfly14.war >> "$OASE_INSTALL_LOG_FILE" 2>&1

    #Kie server install
    cd ${wildfly_root_directory}/wildfly-14.0.1.Final/standalone/deployments >> "$OASE_INSTALL_LOG_FILE" 2>&1
    wget https://repo1.maven.org/maven2/org/kie/server/kie-server/7.22.0.Final/kie-server-7.22.0.Final-ee8.war >> "$OASE_INSTALL_LOG_FILE" 2>&1

    cd ${wildfly_root_directory}/wildfly-14.0.1.Final/standalone/deployments
    mv business-central-7.22.0.Final-wildfly14.war decision-central.war
    mv kie-server-7.22.0.Final-ee8.war kie-server.war

    #wildfly user add
    cd ${wildfly_root_directory}/wildfly-14.0.1.Final/bin
    expect -c "
        set timeout -1
        spawn ./add-user.sh
        expect \"(a):\"
        send \"b\\r\"
        expect \"Username :\"
        send \""${drools_adminname}\\r"\"
        expect \"Password :\"
        send \""${drools_password}\\r"\"
        expect \"Re-enter Password :\"
        send \""${drools_password}\\r"\"
        expect \"What groups do you want this user to belong to\"
        send \"admin,kie-server,rest-all\\r\"
        expect \"Is this correct yes/no?\"
        send \"yes\\r\"
        expect \"yes/no?\"
        send \"yes\\r\"
    " >> "$OASE_INSTALL_LOG_FILE" 2>&1

    # standalone.conf書き換え
    cd ${wildfly_root_directory}/wildfly-14.0.1.Final/bin >> "$OASE_INSTALL_LOG_FILE" 2>&1
    mv standalone.conf standalone.conf.oase_bk
    cat << EOS > "standalone.conf"
## -*- shell-script -*- ######################################################
##                                                                          ##
##  WildFly bootstrap Script Configuration                                  ##
##                                                                          ##
##############################################################################

#
# This file is optional; it may be removed if not needed.
#

#
# Specify the maximum file descriptor limit, use "max" or "maximum" to use
# the default, as queried by the system.
#
# Defaults to "maximum"
#
#MAX_FD="maximum"

#
# Specify the profiler configuration file to load.
#
# Default is to not load profiler configuration file.
#
#PROFILER=""

#
# Specify the location of the Java home directory.  If set then $JAVA will
# be defined to $JAVA_HOME/bin/java, else $JAVA will be "java".
#
#JAVA_HOME="/opt/java/jdk"

# tell linux glibc how many memory pools can be created that are used by malloc
# MALLOC_ARENA_MAX="5"

#
# Specify the exact Java VM executable to use.
#
#JAVA=""

if [ "x$JBOSS_MODULES_SYSTEM_PKGS" = "x" ]; then
   JBOSS_MODULES_SYSTEM_PKGS="org.jboss.byteman"
fi

# Uncomment the following line to prevent manipulation of JVM options
# by shell scripts.
#
#PRESERVE_JAVA_OPTS=true

#
# Specify options to pass to the Java VM.
#
if [ "x$JAVA_OPTS" = "x" ]; then
   JAVA_OPTS="-Xms64m -Xmx1024m -XX:MetaspaceSize=96M -XX:MaxMetaspaceSize=1024m -Djava.net.preferIPv4Stack=true"
   JAVA_OPTS="$JAVA_OPTS -Djboss.modules.system.pkgs=$JBOSS_MODULES_SYSTEM_PKGS -Djava.awt.headless=true"
else
   echo "JAVA_OPTS already set in environment; overriding default settings with values: $JAVA_OPTS"
fi

# Sample JPDA settings for remote socket debugging
#JAVA_OPTS="$JAVA_OPTS -agentlib:jdwp=transport=dt_socket,address=8787,server=y,suspend=n"

# Sample JPDA settings for shared memory debugging
#JAVA_OPTS="$JAVA_OPTS -agentlib:jdwp=transport=dt_shmem,server=y,suspend=n,address=jboss"

# Uncomment to not use JBoss Modules lockless mode
#JAVA_OPTS="$JAVA_OPTS -Djboss.modules.lockless=false"

# Uncomment to gather JBoss Modules metrics
#JAVA_OPTS="$JAVA_OPTS -Djboss.modules.metrics=true"

# Uncomment to enable the experimental JDK 11 support for ByteBuddy
# ByteBuddy is the default bytecode provider of Hibernate ORM
#JAVA_OPTS="$JAVA_OPTS -Dnet.bytebuddy.experimental=true"

# Uncomment this to run with a security manager enabled
# SECMGR="true"

# Uncomment this in order to be able to run WildFly on FreeBSD
# when you get "epoll_create function not implemented" message in dmesg output
#JAVA_OPTS="$JAVA_OPTS -Djava.nio.channels.spi.SelectorProvider=sun.nio.ch.PollSelectorProvider"

# Uncomment this out to control garbage collection logging
# GC_LOG="true"
EOS
}

#Maven install
configure_maven(){
    cd /tmp >> "$OASE_INSTALL_LOG_FILE" 2>&1
    wget https://archive.apache.org/dist/maven/maven-3/3.6.1/binaries/apache-maven-3.6.1-bin.tar.gz >> "$OASE_INSTALL_LOG_FILE" 2>&1
    tar -xzvf apache-maven-3.6.1-bin.tar.gz >> "$OASE_INSTALL_LOG_FILE" 2>&1

    mv apache-maven-3.6.1 /opt/ >> "$OASE_INSTALL_LOG_FILE" 2>&1
    cd /opt >> "$OASE_INSTALL_LOG_FILE" 2>&1
    ln -s /opt/apache-maven-3.6.1 apache-maven >> "$OASE_INSTALL_LOG_FILE" 2>&1

    cp /etc/profile /etc/old_profile.bk >> "$OASE_INSTALL_LOG_FILE" 2>&1
    sed -i -e '$a export M2_HOME=/opt/apache-maven' /etc/profile >> "$OASE_INSTALL_LOG_FILE" 2>&1
    sed -i -e '$a export PATH=$PATH:$M2_HOME/bin' /etc/profile >> "$OASE_INSTALL_LOG_FILE" 2>&1

    source /etc/profile >> "$OASE_INSTALL_LOG_FILE" 2>&1
    mvn --version >> "$OASE_INSTALL_LOG_FILE" 2>&1

    MAVEN_DIRECTORY=/root/.m2/repository
    MAVEN_PACKAGE=$OASE_INSTALL_PACKAGE_DIR/OASE/oase-contents/oase_maven.tar.gz

    mkdir -p "$MAVEN_DIRECTORY" >> "$OASE_INSTALL_LOG_FILE" 2>&1
    cp -fp "$MAVEN_PACKAGE" "$MAVEN_DIRECTORY" >> "$OASE_INSTALL_LOG_FILE" 2>&1
    cd "$MAVEN_DIRECTORY" >> "$OASE_INSTALL_LOG_FILE" 2>&1
    tar -zxvf oase_maven.tar.gz >> "$OASE_INSTALL_LOG_FILE" 2>&1
    rm -f oase_maven.tar.gz
}

#Django install
configure_django(){
    # django
    pip3 install django==2.2.3 django-crispy-forms django-filter django-pure-pagination >> "$OASE_INSTALL_LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        log "ERROR:Installation failed django==2.2.3 django-crispy-forms django-filter django-pure-pagination"
        func_exit
    fi

    # requests
    pip3 install requests ldap3 pycrypto openpyxl==2.5.14 xlrd configparser fasteners djangorestframework python-memcached django-simple-history pyyaml >> "$OASE_INSTALL_LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        log "ERROR:Installation failed requests ldap3 pycrypto openpyxl==2.5.14 xlrd configparser fasteners djangorestframework python-memcached django-simple-history pyyaml"
        func_exit
    fi

    #pytz
    pip3 list | grep pytz >> "$OASE_INSTALL_LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        pip3 install pytz >> "$OASE_INSTALL_LOG_FILE" 2>&1
        if [ $? -ne 0 ]; then
            log "ERROR:Installation failed pytz"
            func_exit
        fi
    fi

    pip list >> "$OASE_INSTALL_LOG_FILE" 2>&1
}

###############################################################################
# make OASE

make_oase() {

    # configure_yum_env() will setup repository.
    log "INFO : Set up repository"
    configure_yum_env

    # offline install(RHEL8 or CentOS8)
    #if [ "$LINUX_OS" == "RHEL8" -o "$LINUX_OS" == "CentOS8" ]; then
    #    if [ "${MODE}" == "local" ]; then
    #        log "RPM install"
    #        install_rpm
    #    fi
    #fi

    log "INFO : python3.6 install"
    configure_python

    log "INFO : memcache setting"
    configure_memcache

    log "INFO : RabbitMQ Server"
    configure_rabbitmq

    log "INFO : MySQL install and setting"
    configure_mysql

    log "INFO : nginx install"
    configure_nginx

    log "INFO : uwsgi install"
    configure_uwsgi

    log "INFO : JAVA install"
    configure_java

    log "INFO : drools instal"
    configure_drools
    
    log "INFO : Maven install"
    configure_maven
    
    log "INFO : Django install"
    configure_django

}


################################################################################
# main

#yum update

# answerfile読み込み
#read_answerfile
#
#if [ "$ACTION" == "Install" ]; then
#    if [ "$exec_mode" == 2 ]; then
#        log "==========[START OASE BUILDER OFFLINE]=========="
#        END_MESSAGE="==========[END OASE BUILDER OFFLINE]=========="
#        
#    elif [ "$exec_mode" == 3 ]; then
MODE="remote"
LINUX_OS='RHEL7'
REPOSITORY="${LINUX_OS}"

# yum package (for yum)
declare -A YUM_PACKAGE_YUM_ENV;
YUM_PACKAGE_YUM_ENV=(
    ["remote"]="yum-utils createrepo"
)

# yum first install packages
YUM__ENV_PACKAGE="${YUM_PACKAGE_YUM_ENV[${MODE}]}"

# yum install packages
declare -A YUM_PACKAGE;
YUM_PACKAGE=(
    ["httpd"]="httpd mod_ssl"
    ["rabbitmq-server"]="rabbitmq-server --enablerepo=epel"
    ["memcached"]="memcached"
    ["erlang"]="erlang"
    ["python"]="python36 python36-libs python36-devel python36-pip"
    ["git"]="git"
    ["ansible"]="sshpass expect nc"
    ["mysql-server"]="mysql-server"
    ["mysql"]="mysql"
    ["expect"]="expect"
    ["mysql-community-devel"]="mysql-community-devel"
    ["nginx"]="nginx"
    ["java"]="java-1.8.0-openjdk java-1.8.0-openjdk-devel"
)

#if [ "$ACTION" == "Install" ]; then
#    if [ "$exec_mode" == 2 ]; then
#        log "==========[START ITA BUILDER OFFLINE]=========="
#        END_MESSAGE="==========[END ITA BUILDER OFFLINE]=========="
#        
#    elif [ "$exec_mode" == 3 ]; then
#        log "==========[START ITA BUILDER ONLINE]=========="
#        END_MESSAGE="==========[END ITA BUILDER ONLINE]=========="
#    fi
#    
#    make_ita
#elif [ "$ACTION" == "Download" ]; then
#    log "==========[START ITA GATHER LIBRARY]=========="
#    END_MESSAGE="==========[END ITA GATHER LIBRARY]=========="
#    download
#else
#    log "Unknown parameter \"$ACTION\"" | tee -a "$ITA_BUILDER_LOG_FILE"
#fi

log "==========[START OASE BUILDER ONLINE]=========="
END_MESSAGE="==========[END OASE BUILDER ONLINE]=========="
make_oase

log "$END_MESSAGE"

func_exit
