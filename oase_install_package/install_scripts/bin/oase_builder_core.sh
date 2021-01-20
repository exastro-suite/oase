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

error_check() {
    DOWNLOAD_CHK=`echo $?`
    if [ $DOWNLOAD_CHK -ne 0 ]; then
        log "ERROR:Stop installation"
        exit
    fi
}

yum_repository() {
    if [ $# -gt 0 ]; then
        local repo=$1

        # no repo to be installed if the first argument starts "-".
        if [[ "$repo" =~ ^[^-] ]]; then
            if [ "$oase_os" == "RHEL7" ]; then
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
            if [ "${oase_os}" == "CentOS7" -o "${oase_os}" == "RHEL7" ]; then
                yum-config-manager "$@" >> "$OASE_INSTALL_LOG_FILE" 2>&1
            elif [ "${oase_os}" == "CentOS8" -o "${oase_os}" == "RHEL8" ]; then
                dnf config-manager "$@" >> "$OASE_INSTALL_LOG_FILE" 2>&1
            fi

            # Check Creating repository
            case "${oase_os}" in
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
    fi
}

# enable mariadb repository
mariadb_repository() {
    #Not used for offline installation
    if [ "${oase_os}" == "CentOS7" -o "${oase_os}" == "RHEL7" -o "${oase_os}" == "RHEL8" ]; then
        local repo=$1

        curl -sS "$repo" | bash >> "$OASE_INSTALL_LOG_FILE" 2>&1

        # Check Creating repository
        create_repo_check mariadb >> "$OASE_INSTALL_LOG_FILE" 2>&1
        if [ $? -ne 0 ]; then
            log "ERROR:Failed to get repository"
            func_exit
        fi

        yum clean all >> "$OASE_INSTALL_LOG_FILE" 2>&1
    fi
}

################################################################################
# configuration functions

# create local yum repository
configure_yum_env() {

    #mirror list is Japan only.
    if [ ! -e /etc/yum/pluginconf.d/fastestmirror.conf ]; then
        if [ "$oase_os" == "RHEL7" ]; then
            yum --enablerepo=rhel-7-server-optional-rpms install -y yum-plugin-fastestmirror >> "$OASE_INSTALL_LOG_FILE" 2>&1
            ls /etc/yum/pluginconf.d/fastestmirror.conf >> "$OASE_INSTALL_LOG_FILE" 2>&1 | xargs grep "include_only=.jp" >> "$OASE_INSTALL_LOG_FILE" 2>&1

            if [ $? -ne 0 ]; then
                sed -i '$a\include_only=.jp' /etc/yum/pluginconf.d/fastestmirror.conf >> "$OASE_INSTALL_LOG_FILE" 2>&1
            fi
        fi
    fi
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
    if [ "${oase_os}" == "RHEL7" ]; then
        yum list installed | grep -e python3-devel.x86_64 -e python3-libs.x86_64 -e python3-pip.noarch >> "$OASE_INSTALL_LOG_FILE" 2>&1
        if [ $? -eq 1 ]; then
            yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm >> "$OASE_INSTALL_LOG_FILE" 2>&1
            yum-config-manager --enable rhel-7-server-optional-rpms >> "$OASE_INSTALL_LOG_FILE" 2>&1
            yum_install ${YUM_PACKAGE["python"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1
        else
            echo "install skip python3-devel.x86_64 python3-libs.x86_64 python3-pip.noarch" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        fi
    elif [ "${oase_os}" == "RHEL8" ]; then
        yum list installed | grep -c -e python3-devel.x86_64 -e python3-libs.x86_64 -e python3-pip.noarch >> "$OASE_INSTALL_LOG_FILE" 2>&1
        if [ $? -lt 3 ]; then
            yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm >> "$OASE_INSTALL_LOG_FILE" 2>&1
            #yum-config-manager --enable rhel-8-server-optional-rpms >> "$OASE_INSTALL_LOG_FILE" 2>&1
            yum_install ${YUM_PACKAGE["python_rhel8"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1
        else
            echo "install skip python3-devel.x86_64 python3-libs.x86_64 python3-pip.noarch" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        fi
    elif [ "${oase_os}" == "CentOS7" ]; then
        yum list installed | grep -e python36u.x86_64 -e python36u-libs.x86_64 -e python36u-devel.x86_64 -e python36u-pip.noarch >> "$OASE_INSTALL_LOG_FILE" 2>&1
        if [ $? -eq 1 ]; then
            yum install -y epel-release >> "$OASE_INSTALL_LOG_FILE" 2>&1
            yum-config-manager --enable epel >> "$OASE_INSTALL_LOG_FILE" 2>&1
            yum_install ${YUM_PACKAGE["python"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1
        else
            echo "install skip python36u python36u-libs  python36u-devel python36u-pip" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        fi
    fi

    # python link
    ln -s /bin/python3.6 /bin/python3 >> "$OASE_INSTALL_LOG_FILE" 2>&1
    ln -sf /bin/python3 /bin/python >> "$OASE_INSTALL_LOG_FILE" 2>&1
    if [ "${oase_os}" == "RHEL8" ]; then
        python3.6 -m pip3 install --upgrade pip >> "$OASE_INSTALL_LOG_FILE" 2>&1
    else
        python3.6 -m pip install --upgrade pip >> "$OASE_INSTALL_LOG_FILE" 2>&1
    fi

    # pika
    if [ "${oase_os}" == "RHEL8" ]; then
        pip3 list --format=legacy | grep pika >> "$OASE_INSTALL_LOG_FILE" 2>&1
        if [ $? -eq 1 ]; then
            pip3 install pika >> "$OASE_INSTALL_LOG_FILE" 2>&1
            if [ $? -ne 0 ]; then
                log "ERROR:Installation failed pika"
                func_exit
            fi
        else
            echo "install skip pika" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        fi
    else
        pip list | grep pika >> "$OASE_INSTALL_LOG_FILE" 2>&1
        if [ $? -eq 1 ]; then
            pip install pika >> "$OASE_INSTALL_LOG_FILE" 2>&1
            if [ $? -ne 0 ]; then
                log "ERROR:Installation failed pika"
                func_exit
            fi
        else
            echo "install skip pika" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        fi
    fi

    # retry
    if [ "${oase_os}" == "RHEL8" ]; then
        pip3 list --format=legacy | grep retry >> "$OASE_INSTALL_LOG_FILE" 2>&1
        if [ $? -eq 1 ]; then
            pip3 install retry >> "$OASE_INSTALL_LOG_FILE" 2>&1
            if [ $? -ne 0 ]; then
                log "ERROR:Installation failed retry"
                func_exit
            fi
        else
            echo "install skip retry" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        fi
    else
        pip list | grep retry >> "$OASE_INSTALL_LOG_FILE" 2>&1
        if [ $? -eq 1 ]; then
            pip install retry >> "$OASE_INSTALL_LOG_FILE" 2>&1
            if [ $? -ne 0 ]; then
                log "ERROR:Installation failed retry"
                func_exit
            fi
        else
            echo "install skip retry" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        fi
    fi

    if [ "${oase_os}" != "RHEL8" ]; then
        #!/usr/bin/python → #!/usr/bin/python2.7
        grep "python2.7" /usr/bin/yum >> "$OASE_INSTALL_LOG_FILE" 2>&1
        if [ $? -eq 1 ]; then
            cp /usr/bin/yum /usr/bin/old_yum
            sed  -i -e 's/python/python2.7/' /usr/bin/yum
        fi

        grep "python2.7" /usr/libexec/urlgrabber-ext-down >> "$OASE_INSTALL_LOG_FILE" 2>&1
        if [ $? -eq 1 ]; then
            cp /usr/libexec/urlgrabber-ext-down /usr/libexec/old_urlgrabber-ext-down
            sed  -i -e 's/python/python2.7/' /usr/libexec/urlgrabber-ext-down
        fi
    fi

}

# RabbitMQ Server
configure_rabbitmq() {
    # install some packages
    yum list installed | grep "erlang" >> "$OASE_INSTALL_LOG_FILE" 2>&1
    if [ $? -eq 1 ]; then
        yum_install ${YUM_PACKAGE["erlang"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1
    else
        echo "install skip erlang" >> "$OASE_INSTALL_LOG_FILE" 2>&1
    fi

    # Check installation erlang packages
    yum_package_check ${YUM_PACKAGE["erlang"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1

    # install some packages
    yum list installed | grep "rabbitmq-server" >> "$OASE_INSTALL_LOG_FILE" 2>&1
    rabbimq_flg=$?
    if [ $rabbimq_flg -eq 1 ]; then
        if [ "${oase_os}" == "RHEL8" ]; then
            curl -s https://packagecloud.io/install/repositories/rabbitmq/rabbitmq-server/script.rpm.sh | sudo bash >> "$OASE_INSTALL_LOG_FILE" 2>&1
            yum makecache -y --disablerepo='*' --enablerepo='rabbitmq_rabbitmq-server' >> "$OASE_INSTALL_LOG_FILE" 2>&1
            yum -y install rabbitmq-server >> "$OASE_INSTALL_LOG_FILE" 2>&1
        else
            yum -y install rabbitmq-server --enablerepo=epel >> "$OASE_INSTALL_LOG_FILE" 2>&1
        fi
    else
        SKIP_ARRAY+=("rabbitmq-server")
        echo "install skip rabbitmq-server" >> "$OASE_INSTALL_LOG_FILE" 2>&1
    fi

    # Check installation RabbitMQ packages
    yum list installed | grep rabbitmq-server >> "$OASE_INSTALL_LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        log "ERROR:Package not installed rabbitmq-server"
        func_exit
    fi

    # skip setting
    if [ $rabbimq_flg -eq 1 ]; then
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
    fi

}

# MariaDB
configure_mariadb() {

    # expect setting
    yum list installed | grep "expect" >> "$OASE_INSTALL_LOG_FILE" 2>&1
    if [ $? -eq 1 ]; then
        yum -y install ${YUM_PACKAGE["expect"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1
    else
        echo "install skip expect" >> "$OASE_INSTALL_LOG_FILE" 2>&1
    fi
    yum_package_check ${YUM_PACKAGE["expect"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1

    # make log directory
    if [ ! -e /var/log/mariadb ]; then
        mkdir -p -m 777 /var/log/mariadb >> "$OASE_INSTALL_LOG_FILE" 2>&1
    fi

    #Confirm whether it is installed
    yum list installed mariadb-server >> "$OASE_INSTALL_LOG_FILE" 2>&1
    if [ $? == 0 ]; then
        log "MariaDB has already been installed."
        SKIP_ARRAY+=("mariadb-server")

        systemctl enable mariadb >> "$OASE_INSTALL_LOG_FILE" 2>&1
        error_check
        systemctl start mariadb >> "$OASE_INSTALL_LOG_FILE" 2>&1
        error_check

        #Confirm whether root password has been changed
        mysql -uroot -p$db_root_password -e "show databases" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        if [ $? == 0 ]; then
            log "Root password of MariaDB is already setting."
        else
            expect -c "
                set timeout -1
                spawn mysql_secure_installation
                expect \"Enter current password for root \\(enter for none\\):\"
                send \"\\r\"
                expect -re \"Switch to unix_socket authentication.* $\"
                send \"\\r\"
                expect -re \"Change the root password\\?.* $\"
                send \"\\r\"
                expect \"New password:\"
                send \""${db_root_password}\\r"\"
                expect \"Re-enter new password:\"
                send \""${db_root_password}\\r"\"
                expect -re \"Remove anonymous users\\?.* $\"
                send \"Y\\r\"
                expect -re \"Disallow root login remotely\\?.* $\"
                send \"Y\\r\"
                expect -re \"Remove test database and access to it\\?.* $\"
                send \"Y\\r\"
                expect -re \"Reload privilege tables now\\?.* $\"
                send \"Y\\r\"
            " >> "$OASE_INSTALL_LOG_FILE" 2>&1

            #server.cnf
            servercon

            # restart MariaDB Server
            #--------CentOS7/8,RHEL7/8--------
            systemctl restart mariadb >> "$OASE_INSTALL_LOG_FILE" 2>&1
            error_check
        fi

    else
        # enable MariaDB repository
        mariadb_repository ${YUM_REPO_PACKAGE_MARIADB[${oase_os}]}

        # install some packages
        echo "----------Installation[MariaDB]----------" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        #Installation
        yum install -y MariaDB MariaDB-server MariaDB-devel MariaDB-shared >> "$OASE_INSTALL_LOG_FILE" 2>&1

        #Check installation
        if [ $? != 0 ]; then
            log "ERROR:Installation failed[MariaDB]"
            func_exit
        fi

        yum_package_check MariaDB MariaDB-server

        # enable and start (initialize) MariaDB Server
        #--------CentOS7,RHEL7--------
        systemctl enable mariadb >> "$OASE_INSTALL_LOG_FILE" 2>&1
        error_check
        systemctl start mariadb >> "$OASE_INSTALL_LOG_FILE" 2>&1
        error_check

        expect -c "
            set timeout -1
            spawn mysql_secure_installation
            expect \"Enter current password for root \\(enter for none\\):\"
            send \"\\r\"
            expect -re \"Switch to unix_socket authentication.* $\"
            send \"n\\r\"
            expect -re \"Change the root password\\?.* $\"
            send \"Y\\r\"
            expect \"New password:\"
            send \""${db_root_password}\\r"\"
            expect \"Re-enter new password:\"
            send \""${db_root_password}\\r"\"
            expect -re \"Remove anonymous users\\?.* $\"
            send \"Y\\r\"
            expect -re \"Disallow root login remotely\\?.* $\"
            send \"Y\\r\"
            expect -re \"Remove test database and access to it\\?.* $\"
            send \"Y\\r\"
            expect -re \"Reload privilege tables now\\?.* $\"
            send \"Y\\r\"
        " >> "$OASE_INSTALL_LOG_FILE" 2>&1

        #server.cnf
        servercon

        # restart MariaDB Server
        #--------CentOS7,RHEL7--------
        systemctl restart mariadb >> "$OASE_INSTALL_LOG_FILE" 2>&1
        error_check

        #pip install mysqlclient
        if [ "${oase_os}" == "RHEL8" ]; then
            pip3 list --format=legacy | grep mysqlclient >> "$OASE_INSTALL_LOG_FILE" 2>&1
        else
            pip list | grep mysqlclient >> "$OASE_INSTALL_LOG_FILE" 2>&1
        fi
        if [ $? -eq 1 ]; then
            if [ "${oase_os}" == "RHEL8" ]; then
                pip3 install mysqlclient >> "$OASE_INSTALL_LOG_FILE" 2>&1
            else
                pip install mysqlclient==2.0.1 >> "$OASE_INSTALL_LOG_FILE" 2>&1
            fi
            if [ $? -ne 0 ]; then
                log "ERROR:Installation failed mysqlclient"
                func_exit
            fi
        else
            SKIP_ARRAY+=("mysqlclient")
            echo "install skip mysqlclient" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        fi
    fi

}

#Apache install and setting
configure_apache(){

    yum list installed | grep "httpd" >> "$OASE_INSTALL_LOG_FILE" 2>&1
    if [ $? -eq 1 ]; then
        yum -y install ${YUM_PACKAGE["httpd"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1
    else
        echo "install skip httpd" >> "$OASE_INSTALL_LOG_FILE" 2>&1
    fi

    # Check installation  httpd packages
    yum_package_check ${YUM_PACKAGE["httpd"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1

    # mod_wsgi setting
    if [ "${oase_os}" == "RHEL8" ]; then
        yum list installed | grep "redhat-rpm-config" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        if [ $? -eq 1 ]; then
            yum install -y redhat-rpm-config >> "$OASE_INSTALL_LOG_FILE" 2>&1
        else
            echo "install skip redhat-rpm-config" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        fi

        yum list installed | grep "mod_ssl" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        if [ $? -eq 1 ]; then
            yum install -y mod_ssl >> "$OASE_INSTALL_LOG_FILE" 2>&1
        else
            echo "install skip mod_ssl" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        fi

        pip3 list --format=legacy | grep mod_wsgi >> "$OASE_INSTALL_LOG_FILE" 2>&1
    else
        yum list installed | grep "mod_ssl" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        if [ $? -eq 1 ]; then
            yum install -y mod_ssl >> "$OASE_INSTALL_LOG_FILE" 2>&1
        else
            echo "install skip mod_ssl" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        fi

        pip list | grep mod_wsgi >> "$OASE_INSTALL_LOG_FILE" 2>&1
    fi
    if [ $? -eq 1 ]; then
        if [ "${oase_os}" == "RHEL8" ]; then
            pip3 install mod_wsgi >> "$OASE_INSTALL_LOG_FILE" 2>&1
        else
            pip install mod_wsgi >> "$OASE_INSTALL_LOG_FILE" 2>&1
        fi
        if [ $? -ne 0 ]; then
            log "ERROR:Installation failed mod_wsgi"
            func_exit
        fi
        httpd_pash=`find / -type f | grep -E "*mod_wsgi-py*"` >> "$OASE_INSTALL_LOG_FILE" 2>&1
        cp $httpd_pash /usr/lib64/httpd/modules >> "$OASE_INSTALL_LOG_FILE" 2>&1
    else
        echo "install skip mod_wsgi" >> "$OASE_INSTALL_LOG_FILE" 2>&1
    fi

}

#JAVA install
configure_java(){
    #openjdk install
    yum list installed | grep -e "java-1.8.0-openjdk" | grep -v "java-1.8.0-openjdk-headless.x86_64" >> "$OASE_INSTALL_LOG_FILE" 2>&1
    if [ $? -eq 1 ]; then
        yum -y install ${YUM_PACKAGE["java"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1
    else
        echo "install skip java-1.8.0-openjdk java-1.8.0-openjdk-devel" >> "$OASE_INSTALL_LOG_FILE" 2>&1
    fi

    # Check installation  java packages
    yum_package_check ${YUM_PACKAGE["java"]} >> "$OASE_INSTALL_LOG_FILE" 2>&1
    yum list | grep java-1.8.0 >> "$OASE_INSTALL_LOG_FILE" 2>&1
}

#Drools install
configure_drools(){
    #WildFly install
    if [ -d ${jboss_root_directory} ]; then
        echo "install skip RHDM" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        return
    fi

    mkdir -p ${jboss_root_directory} >> "$OASE_INSTALL_LOG_FILE" 2>&1
    cd ${jboss_root_directory} >> "$OASE_INSTALL_LOG_FILE" 2>&1
    wget https://download.jboss.org/wildfly/14.0.1.Final/wildfly-14.0.1.Final.tar.gz >> "$OASE_INSTALL_LOG_FILE" 2>&1
    tar -xzvf wildfly-14.0.1.Final.tar.gz >> "$OASE_INSTALL_LOG_FILE" 2>&1

    #Owner change
    chown -R root:root wildfly-14.0.1.Final
    rm -f wildfly-14.0.1.Final.tar.gz

    #Business entral Workbench WildFly 14 War install
    cd ${jboss_root_directory}/wildfly-14.0.1.Final/standalone/deployments >> "$OASE_INSTALL_LOG_FILE" 2>&1
    wget https://download.jboss.org/drools/release/7.22.0.Final/business-central-7.22.0.Final-wildfly14.war >> "$OASE_INSTALL_LOG_FILE" 2>&1

    #Kie server install
    cd ${jboss_root_directory}/wildfly-14.0.1.Final/standalone/deployments >> "$OASE_INSTALL_LOG_FILE" 2>&1
    wget https://repo1.maven.org/maven2/org/kie/server/kie-server/7.22.0.Final/kie-server-7.22.0.Final-ee8.war >> "$OASE_INSTALL_LOG_FILE" 2>&1

    cd ${jboss_root_directory}/wildfly-14.0.1.Final/standalone/deployments
    mv business-central-7.22.0.Final-wildfly14.war decision-central.war
    mv kie-server-7.22.0.Final-ee8.war kie-server.war

    #wildfly user add
    cd ${jboss_root_directory}/wildfly-14.0.1.Final/bin
    expect -c "
        set timeout -1
        spawn ./add-user.sh
        expect \"(a):\"
        send \"b\\r\"
        expect \"Username :\"
        send \""${rhdm_adminname}\\r"\"
        expect \"Password :\"
        send \""${rhdm_password}\\r"\"
        expect \"Re-enter Password :\"
        send \""${rhdm_password}\\r"\"
        expect \"What groups do you want this user to belong to\"
        send \"admin,kie-server,rest-all\\r\"
        expect \"Is this correct yes/no?\"
        send \"yes\\r\"
        expect \"yes/no?\"
        send \"yes\\r\"
    " >> "$OASE_INSTALL_LOG_FILE" 2>&1

    # standalone.conf書き換え
    standalone_conf
}

#Maven install
configure_maven(){
    if [ -e /opt/apache-maven-3.6.1 ]; then
        echo "install skip Maven" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        return
    fi

    cd /tmp >> "$OASE_INSTALL_LOG_FILE" 2>&1
    wget https://archive.apache.org/dist/maven/maven-3/3.6.1/binaries/apache-maven-3.6.1-bin.tar.gz >> "$OASE_INSTALL_LOG_FILE" 2>&1
    tar -xzvf apache-maven-3.6.1-bin.tar.gz >> "$OASE_INSTALL_LOG_FILE" 2>&1

    mv apache-maven-3.6.1 /opt/ >> "$OASE_INSTALL_LOG_FILE" 2>&1
    cd /opt >> "$OASE_INSTALL_LOG_FILE" 2>&1
    ln -s /opt/apache-maven-3.6.1 apache-maven >> "$OASE_INSTALL_LOG_FILE" 2>&1

    cp /etc/profile /etc/old_profile.bk >> "$OASE_INSTALL_LOG_FILE" 2>&1

    grep "M2_HOME" /etc/profile >> "$OASE_INSTALL_LOG_FILE" 2>&1
    if [ $? -eq 1 ]; then
        sed -i -e '$a export M2_HOME=/opt/apache-maven' /etc/profile >> "$OASE_INSTALL_LOG_FILE" 2>&1
        sed -i -e '$a export PATH=$PATH:$M2_HOME/bin' /etc/profile >> "$OASE_INSTALL_LOG_FILE" 2>&1
    fi

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
    if [ "${oase_os}" == "RHEL8" ]; then
        pip_list=`pip3 list --format=legacy | grep -c -e "django==2.2.3" -e "django-crispy-forms" -e "django-filter"` >> "$OASE_INSTALL_LOG_FILE" 2>&1
    else
        pip_list=`pip list | grep -c -e "django==2.2.3" -e "django-crispy-forms" -e "django-filter"` >> "$OASE_INSTALL_LOG_FILE" 2>&1
    fi
    if [ $pip_list -lt 3 ]; then
        if [ "${oase_os}" == "RHEL8" ]; then
            pip3 install django==2.2.3 django-crispy-forms django-filter >> "$OASE_INSTALL_LOG_FILE" 2>&1
        else
            pip install django==2.2.3 django-crispy-forms django-filter >> "$OASE_INSTALL_LOG_FILE" 2>&1
        fi
        if [ $? -ne 0 ]; then
            log "ERROR:Installation failed django==2.2.3 django-crispy-forms django-filter"
            func_exit
        fi
    else
        echo "install skip django==2.2.3 django-crispy-forms django-filter" >> "$OASE_INSTALL_LOG_FILE" 2>&1
    fi

    # requests
    if [ "${oase_os}" == "RHEL8" ]; then
        pip_list=`pip3 list --format=legacy | grep -c -e "requests" -e "ldap3" -e "pycrypto" -e "openpyxl" -e "xlrd" -e "configparser" -e "fasteners" -e "djangorestframework" -e "django-simple-history" -e "pyyaml"` >> "$OASE_INSTALL_LOG_FILE" 2>&1
    else
        pip_list=`pip list | grep -c -e "requests" -e "ldap3" -e "pycrypto" -e "openpyxl" -e "xlrd" -e "configparser" -e "fasteners" -e "djangorestframework" -e "django-simple-history" -e "pyyaml"` >> "$OASE_INSTALL_LOG_FILE" 2>&1
    fi
    if [ $pip_list -lt 11 ]; then
        if [ "${oase_os}" == "RHEL8" ]; then
            pip3 install requests ldap3 pycrypto openpyxl==2.5.14 xlrd==1.2.0 configparser fasteners djangorestframework  django-simple-history pyyaml >> "$OASE_INSTALL_LOG_FILE" 2>&1
        else
            pip install requests ldap3 pycrypto openpyxl==2.5.14 xlrd==1.2.0 configparser fasteners djangorestframework django-simple-history pyyaml >> "$OASE_INSTALL_LOG_FILE" 2>&1
        fi
        if [ $? -ne 0 ]; then
            log "ERROR:Installation failed requests ldap3 pycrypto openpyxl==2.5.14 xlrd==1.2.0 configparser fasteners djangorestframework django-simple-history pyyaml"
            func_exit
        fi
    else
        echo "install skip requests ldap3 pycrypto openpyxl xlrd configparser fasteners djangorestframework django-simple-history pyyaml" >> "$OASE_INSTALL_LOG_FILE" 2>&1
    fi

    #pytz
    if [ "${oase_os}" == "RHEL8" ]; then
        pip3 list --format=legacy | grep "pytz" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        if [ $? -eq 1 ]; then
            pip3 list --format=legacy | grep pytz >> "$OASE_INSTALL_LOG_FILE" 2>&1
            if [ $? -ne 0 ]; then
                pip3 install pytz >> "$OASE_INSTALL_LOG_FILE" 2>&1
                if [ $? -ne 0 ]; then
                    log "ERROR:Installation failed pytz"
                    func_exit
                fi
            fi
        else
            echo "install skip pytz" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        fi

        pip3 list --format=legacy >> "$OASE_INSTALL_LOG_FILE" 2>&1
    else
        pip list | grep "pytz" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        if [ $? -eq 1 ]; then
            pip list | grep pytz >> "$OASE_INSTALL_LOG_FILE" 2>&1
            if [ $? -ne 0 ]; then
                pip install pytz >> "$OASE_INSTALL_LOG_FILE" 2>&1
                if [ $? -ne 0 ]; then
                    log "ERROR:Installation failed pytz"
                    func_exit
                fi
            fi
        else
            echo "install skip pytz" >> "$OASE_INSTALL_LOG_FILE" 2>&1
        fi

        pip list >> "$OASE_INSTALL_LOG_FILE" 2>&1
    fi
}

#servercof setting
servercon() {
    mv /etc/my.cnf.d/server.cnf /etc/my.cnf.d/old_server.cnf >> "$OASE_INSTALL_LOG_FILE" 2>&1
    cat << EOS > "/etc/my.cnf.d/server.cnf"
#
# These groups are read by MariaDB server.
# Use it for options that only the server (but not clients) should see
#
# See the examples of server my.cnf files in /usr/share/mysql/
#

# this is read by the standalone daemon and embedded servers
[server]

# this is only for the mysqld standalone daemon
[mysqld]
datadir=/var/lib/mysql
socket=/var/lib/mysql/mysql.sock
symbolic-links=0
log-error=/var/log/mariadb/mariadb.log

skip-character-set-client-handshake
explicit_defaults_for_timestamp = true
transaction-isolation=READ-COMMITTED
innodb_buffer_pool_size = 512MB
innodb_log_buffer_size=64M
innodb_log_file_size=256M
min_examined_row_limit=100
join_buffer_size=128M
query_cache_size=512M
query_cache_type=1
max_heap_table_size=64M
tmp_table_size=64M
mrr_buffer_size=64M
max_connections=256


#
# * Galera-related settings
#
[galera]
# Mandatory settings
#wsrep_on=ON
#wsrep_provider=
#wsrep_cluster_address=
#binlog_format=row
#default_storage_engine=InnoDB
#innodb_autoinc_lock_mode=2
#
# Allow server to accept connections on all interfaces.
#
#bind-address=0.0.0.0
#
# Optional setting
#wsrep_slave_threads=1
#innodb_flush_log_at_trx_commit=0

# this is only for embedded server
[embedded]

# This group is only read by MariaDB servers, not by MySQL.
# If you use the same .cnf file for MySQL and MariaDB,
# you can put MariaDB-only options here
[mariadb]
disable_unix_socket
character-set-server = utf8

# This group is only read by MariaDB-10.5 servers.
# If you use the same .cnf file for MariaDB of different versions,
# use this group for options that older servers don't understand
[mariadb-10.5]

EOS

}

#standalone.conf setting
standalone_conf() {
    cd ${jboss_root_directory}/wildfly-14.0.1.Final/bin >> "$OASE_INSTALL_LOG_FILE" 2>&1
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

    log "INFO : RabbitMQ Server"
    configure_rabbitmq

    log "INFO : MariaDB install and setting"
    configure_mariadb

    log "INFO : apache install"
    configure_apache

    log "INFO : JAVA install"
    configure_java

    log "INFO : RHDM instal"
    configure_drools

    log "INFO : Maven install"
    configure_maven

    log "INFO : Django install"
    configure_django

}

################################################################################
# base

# yum repository package (for mariadb)
declare -A YUM_REPO_PACKAGE_MARIADB;
YUM_REPO_PACKAGE_MARIADB=(
    ["RHEL7"]="https://downloads.mariadb.com/MariaDB/mariadb_repo_setup"
    ["RHEL8"]="https://downloads.mariadb.com/MariaDB/mariadb_repo_setup"
    ["CentOS7"]="https://downloads.mariadb.com/MariaDB/mariadb_repo_setup"
)

################################################################################
# main

MODE="remote"
#LINUX_OS='RHEL7'
#REPOSITORY="${LINUX_OS}"

YUM_PACKAGE_YUM_ENV=(
    ["remote"]="yum-utils createrepo"
)

# yum first install packages
YUM__ENV_PACKAGE="${YUM_PACKAGE_YUM_ENV[${MODE}]}"

# yum install packages
declare -A YUM_PACKAGE;
YUM_PACKAGE=(
    ["httpd"]="httpd httpd-devel"
    ["rabbitmq-server"]="rabbitmq-server --enablerepo=epel"
    ["erlang"]="erlang"
    ["python"]="python36 python36-libs python36-devel python36-pip"
    ["python_rhel8"]="python3 python3-libs python3-devel python3-pip"
    ["git"]="git"
    ["ansible"]="sshpass expect nc"
    ["mysql-server"]="mysql-server"
    ["mysql"]="mysql"
    ["expect"]="expect"
    ["mysql-community-devel"]="mysql-community-devel"
    ["java"]="java-1.8.0-openjdk java-1.8.0-openjdk-devel"
)

log "==========[START OASE BUILDER ONLINE]=========="
END_MESSAGE="==========[END OASE BUILDER ONLINE]=========="

make_oase

log "$END_MESSAGE"

if [ -e /tmp/pear ]; then
    rm -rf /tmp/pear >> "$OASE_INSTALL_LOG_FILE" 2>&1
fi
