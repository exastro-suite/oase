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
#    環境構築ツール(オンラインインストール用)
#
############################################################
# global variables

readonly OASE_INSTALL_SCRIPTS_DIR=$(cd $(dirname $0);pwd)
readonly OASE_INSTALL_PACKAGE_DIR=$(cd $(dirname ${OASE_INSTALL_SCRIPTS_DIR});pwd)
readonly OASE_PKG_ROOT_DIR=$(cd $(dirname ${OASE_INSTALL_PACKAGE_DIR});pwd)
readonly OASE_INSTALL_BIN_DIR=${OASE_INSTALL_SCRIPTS_DIR}/bin
readonly OASE_INSTALL_LOGS_DIR=${OASE_INSTALL_SCRIPTS_DIR}/logs
readonly OASE_ANSWER_FILE=${OASE_INSTALL_SCRIPTS_DIR}/oase_answers.txt
readonly OASE_COMMON_LIBS=${OASE_INSTALL_BIN_DIR}/oase_common_libs.sh
readonly OASE_INSTALL_LOG_FILE=${OASE_INSTALL_LOGS_DIR}/oase_install.log

export OASE_INSTALL_SCRIPTS_DIR
export OASE_INSTALL_PACKAGE_DIR
export OASE_PKG_ROOT_DIR
export OASE_INSTALL_BIN_DIR
export OASE_INSTALL_LOG_FILE

################################################################################
# functions
function oase_install() {
    log "INFO : Start to install"

    bash ${OASE_INSTALL_BIN_DIR}/oase_deployment_core.sh
    if [ $? -ne 0 ]; then
        log "ERROR : Failed to execute ${OASE_INSTALL_BIN_DIR}/oase_deployment_core.sh"
        return 1
    fi

    bash ${OASE_INSTALL_BIN_DIR}/oase_settings_core.sh
    if [ $? -ne 0 ]; then
        log "ERROR : Failed to execute ${OASE_INSTALL_BIN_DIR}/oase_settings_core.sh"
        return 1
    fi
    log "INFO : Finished to install"
}

function oase_uninstall() {
    log "INFO : Start to uninstall"

    bash ${OASE_INSTALL_BIN_DIR}/oase_uninstall_core.sh
    if [ $? -ne 0 ]; then
        log "ERROR : Failed to execute ${OASE_INSTALL_BIN_DIR}/oase_uninstall_core.sh"
        return 1
    fi
    log "INFO : Finished to uninstall"
}

################################################################################
# main

if [ ! -e ${OASE_INSTALL_LOGS_DIR} ]; then
    echo "INFO : Start to create the install log's directory" 
    mkdir ${OASE_INSTALL_LOGS_DIR}
    if [ $? -gt 0 ]; then
        echo "ERROR : Faild to create the log directory. ${OASE_INSTALL_LOGS_DIR}" 
        return 1
    fi
    echo "INFO : Finished to create the install log's directory"
fi
if [ ! -f ${OASE_INSTALL_LOG_FILE} ]; then
    echo "INFO : Start to create the installation log file" 
    touch ${OASE_INSTALL_LOG_FILE}
    if [ $? -gt 0 ]; then
        echo "ERROR : Faild to create the installation log. ${OASE_INSTALL_LOG_FILE}" 
        return 1
    fi
    echo "INFO : Finished to create the installation log file"
fi

#-----------------------------------------------------------
# 各shスクリプトの有無を確認
#-----------------------------------------------------------
_some_var=`cat << EOF
    ${OASE_INSTALL_BIN_DIR}/oase_common_libs.sh
    ${OASE_INSTALL_BIN_DIR}/oase_deployment_core.sh
    ${OASE_INSTALL_BIN_DIR}/oase_settings_core.sh
        ${OASE_INSTALL_BIN_DIR}/oase_app_setup_core.sh
            ${OASE_INSTALL_BIN_DIR}/oase_db_setup_core.sh
        ${OASE_INSTALL_BIN_DIR}/oase_middleware_setup_core.sh
        ${OASE_INSTALL_BIN_DIR}/oase_service_setup_core.sh
    ${OASE_INSTALL_BIN_DIR}/oase_uninstall_core.sh
EOF`

for _some_sh in ${_some_var};do
    if [ ! -f ${_some_sh} ]; then
        echo "ERROR : ${_some_sh} no such file"
        exit 1
    fi
done

#-----------------------------------------------------------
# 共通処理の読み込み
#-----------------------------------------------------------
echo "INFO : Start to read ${OASE_COMMON_LIBS}"
source ${OASE_COMMON_LIBS}
if [ $? -ne 0 ]; then
    echo "ERROR : Failed to read ${OASE_COMMON_LIBS}"
    exit 1
fi
log "INFO : Finished to read ${OASE_COMMON_LIBS}" 

log "#####################################"
log "INFO : oase_online_install.sh start"
log "#####################################"

#-----------------------------------------------------------
# answerfileの読み込み
#-----------------------------------------------------------
if [ ! -f ${OASE_ANSWER_FILE} ]; then
    log "ERROR : ${OASE_ANSWER_FILE} no such file"
    exit 1
fi

read_answerfile ${OASE_ANSWER_FILE}
if [ $? -ne 0 ]; then
    log "ERROR : Failed to read ${OASE_ANSWER_FILE}"
    exit 1
fi

#-----------------------------------------------------------
# 子プロセス呼び出し
#-----------------------------------------------------------
if [ ${install_mode} = "Install" ]; then
    log "INFO : Mode=Install Selected"
    oase_install
    if [ $? -ne 0 ]; then
        log "#####################################"
        log "ERROR : Install Failed"
        log "#####################################\n"
        exit 1
    fi

    log "#####################################"
    log "INFO : Install Finished"
    log "#####################################\n"
    exit 0

elif [ ${install_mode} = "Uninstall" ]; then
    log "INFO : Mode=Uninstall Selected"
    oase_uninstall
    if [ $? -ne 0 ]; then
        log "#####################################"
        log "ERROR : Uninstall Failed"
        log "#####################################\n"
        exit 1
    fi

    log "#####################################"
    log "INFO : Uninstall Finished"
    log "#####################################\n"
    exit 0

else
    log "ERROR : 'install_mode' should be set. (Install or Uninstall)"
    exit 1
fi
