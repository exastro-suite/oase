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
############################################################
#
# 【概要】
#    バージョンアップツール
#
############################################################

#-----関数定義ここから-----
############################################################
# ログ出力
# @param    $1    string    ログに出力する文字列
# @return   なし
############################################################
log() {
    echo "["`date +"%Y-%m-%d %H:%M:%S"`"] $1" | tee -a "$LOG_FILE"
}

############################################################
# 記入漏れをチェック
# @param    なし
# @return   なし
############################################################
func_answer_format_check() {
    #空白でないかチェック用
    if [ "$key" = "" -o "$val" = "" ]; then
        ANSWER_ERR_FLG=1
        log "ERROR : The format of Answer-file is incorrect.(key:$key)"
        log "INFO : Abort version up."
        ERR_FLG="false"
        func_exit_and_delete_file
    fi
    #$keyの値が正しいかチェック用
    FORMAT_CHECK_CNT=$((FORMAT_CHECK_CNT+1))
}

############################################################
# バージョンの大小チェック
# @param    バージョン1,バージョン2
# @return   0: バージョン1 < バージョン2
#           1: バージョン1 = バージョン2
#           2: バージョン1 > バージョン2
############################################################
func_compare_version() {
    VERSION1=$1
    VERSION2=$2
    VERSION1_SPLIT=(${VERSION1//./ })
    VERSION2_SPLIT=(${VERSION2//./ })

    if  [ ${VERSION1_SPLIT[0]} -lt ${VERSION2_SPLIT[0]} ] ; then
        echo 0
    elif  [ ${VERSION1_SPLIT[0]} -gt ${VERSION2_SPLIT[0]} ] ; then
        echo 2
    else
        if  [ ${VERSION1_SPLIT[1]} -lt ${VERSION2_SPLIT[1]} ] ; then
            echo 0
        elif  [ ${VERSION1_SPLIT[1]} -gt ${VERSION2_SPLIT[1]} ] ; then
            echo 2
        else
            if  [ ${VERSION1_SPLIT[2]} -lt ${VERSION2_SPLIT[2]} ] ; then
                echo 0
            elif  [ ${VERSION1_SPLIT[2]} -gt ${VERSION2_SPLIT[2]} ] ; then
                echo 2
            else
                echo 1
            fi
        fi
    fi
}

############################################################
# サービス起動
# @param    なし
# @return   なし
############################################################
func_start_service() {

    systemctl status httpd >> "$LOG_FILE" 2>&1
    if [ $? -eq 3 ]; then
        systemctl start httpd
    fi
    systemctl status nginx >> "$LOG_FILE" 2>&1
    if [ $? -eq 3 ]; then
        systemctl start nginx
        systemctl start uwsgi
    fi

    #OASEのサービス起動する
    cd /usr/lib/systemd/system
    systemctl start oase-action.service
    systemctl start oase-agent.service
    systemctl start oase-apply.service
    systemctl start oase-accept.service

    # ディレクトリ移動
    cd ${BASE_DIR}
}

############################################################
# 全角文字をチェック
# @param    なし
# @return   なし
############################################################
setting_file_format_check() {
    if [ `echo "$LINE" | LANG=C grep -v '^[[:cntrl:][:print:]]*$'` ];then
        log "ERROR : Double-byte characters cannot be used in the setting files"
        log "Applicable line : $LINE"
        ERR_FLG="false"
        func_exit_and_delete_file
    fi
}

############################################################
# yum install
# @param    $1     string       ライブラリ名(例:MariaDB)
# @return   なし
############################################################
yum_install() {
    echo "----------Installation[$@]----------" >> "$LOG_FILE" 2>&1
    #Installation
    yum install -y "$@" >> "$LOG_FILE" 2>&1

    #Check installation
    for key in $@; do
        echo "----------Check installation[$key]----------" >> "$LOG_FILE" 2>&1
        yum install -y "$key" >> "$LOG_FILE" 2>&1
        if [ $? != 0 ]; then
            log "ERROR:Installation failed[$key]"
            ERR_FLG="false"
            func_exit_and_delete_file
        fi
    done
}

############################################################
# yum mariadb_repository
# @param    $1     string       YUM_REPO_PACKAGE_MARIADB
# @return   なし
############################################################
mariadb_repository() {
    #Not used for offline installation
    echo repo
    if [ "${oase_os}" == "CentOS7" -o "${oase_os}" == "RHEL7" -o "${oase_os}" == "RHEL8" ]; then
        local repo=$1

        curl -sS "$repo" | bash >> "$LOG_FILE" 2>&1

        # Check Creating repository
        create_repo_check mariadb >> "$LOG_FILE" 2>&1
        if [ $? -ne 0 ]; then
            log "ERROR:Failed to get repository"
            ERR_FLG="false"
            func_exit_and_delete_file
        fi

        yum clean all >> "$LOG_FILE" 2>&1
    fi
}

############################################################
# func_exit_and_delete_file
# @param    $1    string    削除するファイル
# @return   なし
############################################################
func_exit_and_delete_file() {
    if test -e /tmp/ita_answers.txt ; then
        rm -rf /tmp/ita_answers.txt
    fi
    if test -e /tmp/ita_repolist.txt ; then
        rm -rf /tmp/ita_repolist.txt
    fi
    if test -e /tmp/san.txt ; then
        rm -rf /tmp/san.txt
    fi
    if [ -e /tmp/pear ]; then
        rm -rf /tmp/pear
    fi

    if [ "$ERR_FLG" = "true" ]; then
        exit 0
    else
        exit 1
    fi
}

############################################################
# check_result
# @param    $1    string    チェック結果
#           $2    string    チェック項目
# @return   なし
############################################################
check_result() {
    if [ $1 -ne 0 ]; then
        log "ERROR : $2."
        exit 1
    fi
}

############################################################
# create_repo_check
# @param    $1    string    リポジトリ
# @return   なし
############################################################
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

#-----関数定義ここまで-----

# yum install packages
declare -A YUM_PACKAGE;
if [ "${exec_mode}" == "1" ]; then
    YUM_PACKAGE=(
        ["httpd"]="${YUM_PACKAGE_APACHE[${REPOSITORY}]}"
        ["rabbitmq-server"]="${YUM_PACKAGE_RABBIT[${REPOSITORY}]}"
        ["erlang"]="erlang"
        ["python"]="${YUM_PACKAGE_PYTHON[${REPOSITORY}]}"
        ["expect"]="expect"
        ["mariadb"]="MariaDB MariaDB-server MariaDB-devel MariaDB-shared"
        ["java"]="java-1.8.0-openjdk java-1.8.0-openjdk-devel"
    )
else
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
fi

# yum repository package (for mariadb)
declare -A YUM_REPO_PACKAGE_MARIADB;
YUM_REPO_PACKAGE_MARIADB=(
    ["RHEL7"]="https://downloads.mariadb.com/MariaDB/mariadb_repo_setup"
    ["RHEL8"]="https://downloads.mariadb.com/MariaDB/mariadb_repo_setup"
    ["CentOS7"]="https://downloads.mariadb.com/MariaDB/mariadb_repo_setup"
    ["yum_all"]=""
)

#インストール済みフラグ
BASE_FLG=0

#インストール済みフラグ配列
INSTALLED_FLG_LIST=(
    BASE_FLG
)

#リリースファイル設置作成関数用配列
#リリースファイルを設置するドライバのリリースファイル名を記載する
RELEASE_PLASE=(
    oase_base
)

#ディレクトリ変数定義
BASE_DIR=$(cd $(dirname dirname $0); pwd)
BIN_DIR="$BASE_DIR/bin"
LIST_DIR="$BASE_DIR/list"
SQL_DIR="$BASE_DIR/sql"
LOG_DIR="$BASE_DIR/logs"
VERSION_UP_DIR="$BASE_DIR/version_up"
LOG_FILE="$LOG_DIR/oase_version_up.log"
ANSWER_FILE="$BASE_DIR/oase_answers.txt"
SOURCE_DIR="${BASE_DIR}/../../oase-root"

#log用ディレクトリ作成
if [ ! -e "$LOG_DIR" ]; then
    mkdir -m 755 "$LOG_DIR"
fi

############################################################
log 'INFO : -----MODE[VERSIONUP] START-----'
############################################################

############################################################
log 'INFO : Authorization check.'
############################################################
if [ ${EUID:-${UID}} -ne 0 ]; then
    log "ERROR : Execute with root authority."
    log "INFO : Abort version up."
    ERR_FLG="false"
    func_exit_and_delete_file
fi

############################################################
log 'INFO : Reading answer-file.'
############################################################

#answersファイルの存在を確認
if ! test -e "$ANSWER_FILE" ; then
    log "ERROR : Answer-file does not be found."
    log "INFO : Abort version up."
    ERR_FLG="false"
    func_exit_and_delete_file
fi

#answersファイルの内容を格納する変数を定義
COPY_ANSWER_FILE="/tmp/oase_answers.txt"
OASE_DIRECTORY=''
OASE_LANGUAGE=''
DB_ROOT_PASSWORD=''
DB_NAME=''
DB_USERNAME=''
DB_PASSWORD=''
#answersファイルのフォーマットチェック用変数リセット
FORMAT_CHECK_CNT='' 

# oase_answers.txtを/tmpにコピー
rm -f "$COPY_ANSWER_FILE" 2>> "$LOG_FILE"
cp "$ANSWER_FILE" "$COPY_ANSWER_FILE" 2>> "$LOG_FILE"
# 空行を削除
sed -i -e '/^$/d' "$COPY_ANSWER_FILE" 2>> "$LOG_FILE"
# BOMを削除
sed -i -e '1s/^\xef\xbb\xbf//' "$COPY_ANSWER_FILE" 2>> "$LOG_FILE"
# 末尾に改行を追加
echo "$(cat "$COPY_ANSWER_FILE")" 1> "$COPY_ANSWER_FILE" 2>> "$LOG_FILE"

#answersファイル読み込み
ANSWERS_TEXT=$(cat "$COPY_ANSWER_FILE")

#IFSバックアップ
SRC_IFS="$IFS"
#IFSに"\n"をセット
IFS="
"
for LINE in $ANSWERS_TEXT;do
    if [ "$(echo "$LINE"|grep -E '^[^#: ]+:[ ]*[^ ]+[ ]*$')" != "" ];then
        setting_file_format_check
        key="$(echo "$LINE" | sed 's/[[:space:]]*$//' | sed -E "s/^([^:]+):[[:space:]]*(.+)$/\1/")"
        val="$(echo "$LINE" | sed 's/[[:space:]]*$//' | sed -E "s/^([^:]+):[[:space:]]*(.+)$/\2/")"

        #OASE用のディレクトリ取得
        if [ "$key" = 'oase_directory' ]; then
            if [[ "$val" != "/"* ]]; then
                log "ERROR : Enter the absolute path in $key."
                log "INFO : Abort version up."
                ERR_FLG="false"
                func_exit_and_delete_file
            fi
            func_answer_format_check
            OASE_DIRECTORY="$val"
        fi
    fi
done

#IFSリストア
IFS="$SRC_IFS"

#作業用アンサーファイルの削除
if ! test -e /tmp/oase_answers.txt ; then
    rm -rf /tmp/oase_answers.txt
fi

#アンサーファイルの内容が読み取れているか
if [ "$FORMAT_CHECK_CNT" != 1 ]; then
    log "ERROR : The format of Answer-file is incorrect."
    log "INFO : Abort version up."
    ERR_FLG="false"
    func_exit_and_delete_file
fi

#現在のOASEバージョンを取得
NOW_VERSION_FILE="${OASE_DIRECTORY}/OASE/oase-root/libs/release/oase_base"
if [[ ! -e ${NOW_VERSION_FILE} ]]; then
    log "INFO : OASE is not installed in [${OASE_DIRECTORY}]."

    #OASE1.1.1には"oase_base"がないため作成
    mkdir -p "${OASE_DIRECTORY}/OASE/oase-root/libs/release" 2>> "$LOG_FILE"
    if [ $? != 0 ]; then
        log "INFO : Abort version up."
        ERR_FLG="false"
        func_exit_and_delete_file]
    fi
    touch "${OASE_DIRECTORY}/OASE/oase-root/libs/release/oase_base"
    echo "Exastro Operation Autonomy Support Engine Base functions version 1.1.1" > "${OASE_DIRECTORY}/OASE/oase-root/libs/release/oase_base"
fi
NOW_VERSION=`cat ${NOW_VERSION_FILE} | cut -d " " -f 9 | sed -e "s/[\r\n]\+//g"`

############################################################
log 'INFO : Version check.'
############################################################
#現在のOASEバージョンの形式チェック
if ! [[ ${NOW_VERSION} =~ [0-9]+\.[0-9]+\.[0-9]+ ]] ; then
    log "ERROR : [${NOW_VERSION_FILE}] is incorrect."
    log "INFO : Abort version up."
    ERR_FLG="false"
    func_exit_and_delete_file
fi

#現在のOASEバージョンが1.1.1以降であることをチェック
#RTN=`func_compare_version ${NOW_VERSION} 1.1.1`
#if [ "${RTN}" -eq 0 ] ; then
#    log "ERROR : Version up is support with 1.4.0 or later.The installed OASE version is [${NOW_VERSION}]."
#    log "INFO : Abort version up."
#    ERR_FLG="false"
#    func_exit_and_delete_file
#fi

#インストーラのOASEバージョンを取得
INSTALLER_VERSION_FILE="${BASE_DIR}/../OASE/oase-releasefiles/oase_base"
if ! test -e ${INSTALLER_VERSION_FILE} ; then
    log "ERROR : [${INSTALLER_VERSION_FILE}] does not be found."
    log "INFO : Abort version up."
    ERR_FLG="false"
    func_exit_and_delete_file
fi
INSTALLER_VERSION=`cat ${INSTALLER_VERSION_FILE} | cut -d " " -f 9 | sed -e "s/[\r\n]\+//g"`

#インストーラのOASEバージョンの形式チェック
if ! [[ ${INSTALLER_VERSION} =~ [0-9]+\.[0-9]+\.[0-9]+ ]] ; then
    log "ERROR : [${INSTALLER_VERSION_FILE}] is incorrect."
    log "INFO : Abort version up."
    ERR_FLG="false"
    func_exit_and_delete_file
fi

#現在のOASEバージョンがインストーラのOASEバージョンよりも低いことのチェック
RTN=`func_compare_version ${NOW_VERSION} ${INSTALLER_VERSION}`
if [ "${RTN}" -eq 1 ] || [ "${RTN}" -eq 2 ] ; then
    log "ERROR : The installed OASE has been version up."
    log "INFO : Abort version up."
    ERR_FLG="false"
    func_exit_and_delete_file
fi

#インストールされているドライバの確認
BASE_FLG=1

############################################################
log 'INFO : Stopping Apache.'
############################################################
#Apacheを停止する
#systemctl stop httpd
systemctl status httpd >> "$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
    systemctl stop httpd
fi
systemctl status nginx >> "$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
    systemctl stop nginx
    systemctl stop uwsgi
fi

############################################################
log 'INFO : Stopping OASE services.'
############################################################
#OASEのサービスを停止する
cd /usr/lib/systemd/system
systemctl stop oase-action.service
systemctl stop oase-agent.service
systemctl stop oase-apply.service
systemctl stop oase-accept.service


# ディレクトリ移動
cd ${BASE_DIR}


#バージョンアップリストの確認
VERSION_UP_LIST_FILE="${VERSION_UP_DIR}/version_up.list"
if ! test -e ${VERSION_UP_LIST_FILE} ; then
    log "ERROR : [${VERSION_UP_LIST_FILE}] does not be found."
    log "INFO : Abort version up."
    func_start_service
    ERR_FLG="false"
    func_exit_and_delete_file
fi

#ライブラリのインストール（install_mode = Versionup_All の時のみ）
if [ "${install_mode}" = "Versionup_All" ] ; then
    #リポジトリを有効にする
    if [ "${oase_os}" == "RHEL7" ]; then
        yum list installed | grep -e python3-devel.x86_64 -e python3-libs.x86_64 -e python3-pip.noarch >> "$LOG_FILE" 2>&1
        if [ $? -eq 1 ]; then
            yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm >> "$LOG_FILE" 2>&1
            subscription-manager repos --enable rhel-7-server-optional-rpms >> "$LOG_FILE" 2>&1
            subscription-manager repos --enable rhel-server-rhscl-7-rpms >> "$LOG_FILE" 2>&1
            yum_install ${YUM_PACKAGE["python"]} >> "$LOG_FILE" 2>&1
        else
            echo "install skip python3-devel.x86_64 python3-libs.x86_64 python3-pip.noarch" >> "$LOG_FILE" 2>&1
        fi
    elif [ "${oase_os}" == "RHEL8" ]; then
        yum list installed | grep -c -e python3-devel.x86_64 -e python3-libs.x86_64 -e python3-pip.noarch >> "$LOG_FILE" 2>&1
        if [ $? -lt 3 ]; then
            yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm >> "$LOG_FILE" 2>&1
            #yum-config-manager --enable rhel-8-server-optional-rpms >> "$LOG_FILE" 2>&1
            yum_install ${YUM_PACKAGE["python_rhel8"]} >> "$LOG_FILE" 2>&1
        else
            echo "install skip python3-devel.x86_64 python3-libs.x86_64 python3-pip.noarch" >> "$LOG_FILE" 2>&1
        fi
    elif [ "${oase_os}" == "CentOS7" ]; then
        yum list installed | grep -e python36u.x86_64 -e python36u-libs.x86_64 -e python36u-devel.x86_64 -e python36u-pip.noarch >> "$LOG_FILE" 2>&1
        if [ $? -eq 1 ]; then
            yum install -y epel-release >> "$LOG_FILE" 2>&1
            yum-config-manager --enable epel >> "$LOG_FILE" 2>&1
            yum_install ${YUM_PACKAGE["python"]} >> "$LOG_FILE" 2>&1
        else
            echo "install skip python36u python36u-libs  python36u-devel python36u-pip" >> "$LOG_FILE" 2>&1
        fi
    fi

    #バージョンアップリストに記載されているバージョンごとにライブラリのインストールを行う
    EXEC_VERSION=${NOW_VERSION}
    while read LIST_VERSION || [ -n "${LIST_VERSION}" ] ; do

        #処理対象のOASEバージョンがインストーラのOASEバージョンよりも低いことのチェック
        RTN=`func_compare_version ${EXEC_VERSION} ${LIST_VERSION}`
        if [ "${RTN}" -eq 1 ] || [ "${RTN}" -eq 2 ] ; then
            continue
        fi

        #インストール済みのドライバごとの処理を行う
        for VAL in ${INSTALLED_FLG_LIST[@]}; do
            if [ ${!VAL} -eq 1 ] ; then
                DRIVER=`echo ${VAL} | cut -d "_" -f 1 | sed 's/^ \(.*\) $/\1/'`

                #YAMLライブラリのインストール
                YUM_LIB_FILE="${VERSION_UP_DIR}/${LIST_VERSION}/${DRIVER,,}_lib_yum.txt"
                if test -e ${YUM_LIB_FILE} ; then
                    YUM_LIB_LIST=`cat ${YUM_LIB_FILE}`

                    ############################################################
                    log "INFO : Installation yum library [${YUM_LIB_LIST}]"
                    ############################################################
                    #Check installation
                    for key in $YUM_LIB_LIST; do
                        echo "----------Installation[$key]----------" >> "$LOG_FILE" 2>&1
                        yum install -y "$key" >> "$LOG_FILE" 2>&1
                        if [ $? != 0 ]; then
                            log "ERROR : Installation failed [$key]"
                            log "INFO : Abort version up."
                            func_start_service
                            ERR_FLG="false"
                            func_exit_and_delete_file
                        fi
                    done
                fi

                #pipライブラリのインストール(pip or pip3)
                if [ "${oase_os}" == "RHEL8" ]; then
                    PIP3_LIB_FILE="${VERSION_UP_DIR}/${LIST_VERSION}/${DRIVER,,}_lib_pip3.txt"
                    if test -e ${PIP3_LIB_FILE} ; then
                        PIP3_LIB_LIST=`cat ${PIP3_LIB_FILE}`

                        ############################################################
                        log "INFO : Installation pip3 library [${PIP3_LIB_LIST}]"
                        ############################################################
                        pip3 install ${PIP3_LIB_LIST} >> "$LOG_FILE" 2>&1

                        #Check installation
                        for key in $PIP3_LIB_LIST; do
                            echo "----------Installation[$key]----------" >> "$LOG_FILE" 2>&1
                            key_name="$(echo "$key" | sed -E "s/^([^:]+)==]*(.+)$/\1/")"
                            pip3 list --format=legacy | grep "$key_name" >> "$LOG_FILE" 2>&1
                            if [ $? != 0 ]; then
                                log "ERROR : Installation failed [$key]"
                                log "INFO : Abort version up."
                                func_start_service
                                ERR_FLG="false"
                                func_exit_and_delete_file
                            fi
                        done
                    fi
                else
                    PIP_LIB_FILE="${VERSION_UP_DIR}/${LIST_VERSION}/${DRIVER,,}_lib_pip.txt"
                    if test -e ${PIP_LIB_FILE} ; then
                        PIP_LIB_LIST=`cat ${PIP_LIB_FILE}`

                        ############################################################
                        log "INFO : Installation pip library [${PIP_LIB_LIST}]"
                        ############################################################
                        pip install ${PIP_LIB_LIST} >> "$LOG_FILE" 2>&1

                        #Check installation
                        for key in $PIP_LIB_LIST; do
                            echo "----------Installation[$key]----------" >> "$LOG_FILE" 2>&1
                            key_name="$(echo "$key" | sed -E "s/^([^:]+)==]*(.+)$/\1/")"
                            pip list | grep "$key_name" >> "$LOG_FILE" 2>&1
                            if [ $? != 0 ]; then
                                log "ERROR : Installation failed [$key]"
                                log "INFO : Abort version up."
                                func_start_service
                                ERR_FLG="false"
                                func_exit_and_delete_file
                            fi
                        done
                    fi
                fi
            fi
        done
        EXEC_VERSION=${LIST_VERSION}
    done < ${VERSION_UP_LIST_FILE}

#    #DB対応
#    rpm -qa | grep -i mysql
#    if [ $? == 0 ]; then
#        log "INFO : Migration from mysql to maridb."
#        systemctl stop mysqld.service >> "$LOG_FILE" 2>&1
#        yum -y remove mysql* >> "$LOG_FILE" 2>&1
#
#        # make log directory
#        if [ ! -e /var/log/mariadb ]; then
#            mkdir -p -m 777 /var/log/mariadb >> "$LOG_FILE" 2>&1
#        fi
#        mariadb_repository ${YUM_REPO_PACKAGE_MARIADB[${oase_os}]}
#        echo marai
#        yum install -y MariaDB MariaDB-server MariaDB-devel MariaDB-shared >> "$LOG_FILE" 2>&1
#
#        systemctl enable mariadb >> "$LOG_FILE" 2>&1
#        systemctl start mariadb >> "$LOG_FILE" 2>&1
#    fi
#
#    #webサーバ対応
#    yum list installed | grep "nginx" >> "$LOG_FILE" 2>&1
#    if [ $? == 0 ]; then
#        log "INFO : Migration from nginx to apache."
#        systemctl stop nginx >> "$LOG_FILE" 2>&1
#
#        yum list installed | grep "httpd" >> "$LOG_FILE" 2>&1
#        if [ $? -eq 1 ]; then
#            yum -y install ${YUM_PACKAGE["httpd"]} >> "$LOG_FILE" 2>&1
#        else
#            echo "install skip httpd" >> "$LOG_FILE" 2>&1
#        fi
#
#        yum list installed | grep "httpd-devel" >> "$LOG_FILE" 2>&1
#        if [ $? -eq 1 ]; then
#            yum -y install ${YUM_PACKAGE["httpd-devel"]} >> "$LOG_FILE" 2>&1
#        else
#            echo "install skip httpd-devel" >> "$LOG_FILE" 2>&1
#        fi
#        httpd_pash=`find / -type f | grep -E "*mod_wsgi-py*"` >> "$LOG_FILE" 2>&1
#        cp $httpd_pash /usr/lib64/httpd/modules >> "$LOG_FILE" 2>&1
#    fi
#    systemctl enable mariadb >> "$LOG_FILE" 2>&1
#    systemctl start mariadb >> "$LOG_FILE" 2>&1
fi

############################################################
log "INFO : Updating sources."
############################################################
#OASEの資材を入れ替える
cp -rp ${SOURCE_DIR} ${OASE_DIRECTORY}/OASE

EXEC_VERSION=${NOW_VERSION}
while read LIST_VERSION || [ -n "${LIST_VERSION}" ] ; do

    ##処理対象のOASEバージョンがインストーラのOASEバージョンよりも低いことのチェック
    RTN=`func_compare_version ${EXEC_VERSION} ${LIST_VERSION}`
    if [ "${RTN}" -eq 1 ] || [ "${RTN}" -eq 2 ] ; then
        continue
    fi

    #マイグレーションを実施
    OASE_WEBAPP_DIR=$(cd $OASE_DIRECTORY/OASE/oase-root/web_app/;pwd)

    cd $(dirname $OASE_WEBAPP_DIR)
    migrate_log=$(python manage.py makemigrations web_app 2>> "$LOG_FILE") >> "$LOG_FILE" 2>&1
    check_result $? "$migrate_log" >> "$LOG_FILE" 2>&1

    log "INFO : $migrate_log" >> "$LOG_FILE" 2>&1

    migrate_log=$(python manage.py migrate 2>> "$LOG_FILE") >> "$LOG_FILE" 2>&1
    check_result $? "$migrate_log" >> "$LOG_FILE" 2>&1

    log "INFO : $migrate_log." >> "$LOG_FILE" 2>&1

    if [ ! -e $OASE_INSTALL_PACKAGE_DIR/SQL/OASE"${LIST_VERSION}".sql ] ; then
        log "INFO : ${LIST_VERSION}.sql does not exist." >> "$LOG_FILE" 2>&1

    else
        OASE_UNIQUE_DELETE_FILE=$OASE_INSTALL_PACKAGE_DIR/SQL/OASE"${LIST_VERSION}".sql >> "$LOG_FILE" 2>&1
        migrate_log=$(echo "source $OASE_UNIQUE_DELETE_FILE" | mysql -u ${db_username} -p${db_password} ${db_name}  2>> "$LOG_FILE")
        check_result $? "$migrate_log" >> "$LOG_FILE" 2>&1

        log "INFO : $migrate_log." >> "$LOG_FILE" 2>&1
    fi

    if [ ! -e $OASE_INSTALL_PACKAGE_DIR/SQL/fixtures"${LIST_VERSION}".yaml ] ; then
        log "INFO : ${LIST_VERSION}.yaml does not exist." >> "$LOG_FILE" 2>&1

    else
        migrate_log=$(python manage.py loaddata $OASE_INSTALL_PACKAGE_DIR/SQL/fixtures"${LIST_VERSION}".yaml 2>> "$LOG_FILE")
        check_result $? "$migrate_log" >> "$LOG_FILE" 2>&1

        log "INFO : $migrate_log." >> "$LOG_FILE" 2>&1
    fi

    cd - > /dev/null 2>&1
    EXEC_VERSION=${LIST_VERSION}
done < ${VERSION_UP_LIST_FILE}

#ディレクトリ、ファイルの権限を777に変更する
MOD_777_FILE="${LIST_DIR}/777_list.txt"
if test -e ${MOD_777_FILE} ; then
    while read LINE; do
        chmod -- 777 "${OASE_DIRECTORY}/${LINE}"
    done < ${MOD_777_FILE}
fi

#ディレクトリ、ファイルの権限を755に変更する
MOD_755_FILE="${LIST_DIR}/755_list.txt"
if test -e ${MOD_755_FILE} ; then
    while read LINE; do
        chmod -- 755 "${OASE_DIRECTORY}/${LINE}"
    done < ${MOD_755_FILE}
fi

#リリースファイルを変更する
for VAL in ${RELEASE_PLASE[@]}; do
    DRIVER=`echo ${VAL} | cut -d "_" -f 2 | sed 's/^ \(.*\) $/\1/'`
    FLG=`echo ${DRIVER^^} | cut -d "-" -f 1 | sed 's/^ \(.*\) $/\1/'`_FLG
    if [ ${!FLG} -eq 1 ] ; then
        if [[ ! -e ${BASE_DIR}/../OASE/oase-releasefiles/${VAL} ]] ; then
            mkdir -p ${OASE_DIRECTORY}/OASE/oase-root/libs/release >> "$LOG_FILE" 2>&1
        fi
        cp -p "${BASE_DIR}/../OASE/oase-releasefiles/${VAL}" "${OASE_DIRECTORY}/OASE/oase-root/libs/release/${VAL}" >> "$LOG_FILE" 2>&1
    fi
done

############################################################
log "INFO : Start Apache and OASE services."
############################################################
#サービスを起動する
systemctl daemon-reload
func_start_service

############################################################
log "INFO : Version up completed from [${NOW_VERSION}] to [${INSTALLER_VERSION}]."
############################################################
