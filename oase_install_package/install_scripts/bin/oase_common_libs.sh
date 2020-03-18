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
#    OASE 共通関数シェル
#
############################################################


############################################################################
# 前提条件

if [ -z ${OASE_INSTALL_LOG_FILE} ]; then
    echo "ERROR : Not set variable 'OASE_INSTALL_LOG_FILE', it must be set before"
    return 1
fi

############################################################################
# 共通関数定義

####################
#
# ログ出力
#
####################
function log() {

    local _fname=${BASH_SOURCE[1]##*/}
    echo -e "["`date +"%Y-%m-%d %H:%M:%S"`"] $@ (${_fname}:${BASH_LINENO[0]}:${FUNCNAME[1]})" | tee -a "${OASE_INSTALL_LOG_FILE}"
}

################################################################################
# configuration functions

####################
#
# answerfile読み込み
#
####################
# read setting file
function read_setting_file() {
    log "INFO : Start to read a settingfile" 
    local _setting_file=${1}

    if [ ! -f ${_setting_file} ]; then
        log "ERROR : ${_setting_file} no such file"
        return 1
    fi

    while read line; do
        # convert "foo: bar" to "foo=bar", and keep comment 
        if [[ ! ${line} =~ ^# ]] && [[ -n ${line} ]]; then
            _command=`echo "$line" | sed -E 's/^([^#][^:]*+): *(.*)/\1=\2/'`
            eval export ${_command}
        fi
    done < ${_setting_file}
    log "INFO : Finished to read a settingfile" 

}

#check (oase_answers.txt)-----
function check_answer_vars() {

    log "INFO : Start to check answer vars" 
    local _error_flag=false

    if [ -z "${install_mode}" ]; then
        log "ERROR : install_mode should be enter to value(Install or Uninstall)"
        _error_flag=true
    fi

    #################################
    ### oase_deployment_core.sh 用
    if [ -z "${oase_directory}" ]; then
        log "ERROR : oase_directory should be enter to value"
        _error_flag=true
    fi

    if [[ "${oase_directory}" != "/"* ]]; then
        log "ERROR : Enter the absolute path in oase_directory"
        _error_flag=true
    fi

    #################################
    ### oase_db_setup_core.sh 用
    # config_id: OASE_SESSION_ENGINE
    if [ -z "${oase_session_engine}" ]; then
        log "ERROR : oase_session_engine should be enter to hostname"
        _error_flag=true
    fi

    # config_id: EV_LOCATION
    if [ -z "${ev_location}" ]; then
        log "ERROR : ev_location should be enter to ev_location"
        _error_flag=true
    fi

    # config_id: OASE_LANGUAGE
    if [ -z "${oase_language}" ]; then
        log "ERROR : oase_language should be enter to language"
        _error_flag=true
    fi

    #################################
    ### oase_db_setup_core.sh 用
    # config_id: RULEFILE_ROOTPATH
    if [ -z "${rulefile_rootpath}" ]; then
        log "ERROR : rulefile_rootpath should be enter to rootpath"
        _error_flag=true
    fi

    # config_id: DM_IPADDRPORT
    if [ -z "${dm_ipaddrport}" ]; then
        log "ERROR : dm_ipaddrport should be enter to DM IP address & port"
        _error_flag=true
    fi

    # config_id: DM_USERID
    if [ -z "${rhdm_adminname}" ]; then
        log "ERROR : rhdm_adminname should be enter to RHDM Administrator name"
        _error_flag=true
    fi

    # config_id: DM_PASSWD
    if [ -z "${rhdm_password}" ]; then
        log "ERROR : rhdm_password should be enter to RHDM Administrator password"
        _error_flag=true
    fi

    # config_id: APPLY_IPADDRPORT
    if [ -z "${apply_ipaddrport}" ]; then
        log "ERROR : apply_ipaddrport should be enter to APPLY IP address & port"
        _error_flag=true
    fi

    # config_id: OASE_MAIL_SMTP
    if [ -z "${oasemail_smtp}" ]; then
        log "ERROR : oasemail_smtp should be enter to APPLY IP address & port"
        _error_flag=true
    fi

    # config_id: MAVENREP_PATH
    if [ -z "${mavenrep_path}" ]; then
        log "ERROR : mavenrep_path should be enter to MAVEN repository path"
        _error_flag=true
    fi

    # config_id: MQ_USER_ID
    if [ -z "${RabbitMQ_username}" ]; then
        log "ERROR : RabbitMQ_username should be enter to  RabbitMQ username"
        _error_flag=true
    fi

    # config_id: MQ_PASSWORD
    if [ -z "${RabbitMQ_password}" ]; then
        log "ERROR : RabbitMQ_password should be enter to  RabbitMQ password"
        _error_flag=true
    fi

    # config_id: MQ_IPADDRESS
    if [ -z "${RabbitMQ_ipaddr}" ]; then
        log "ERROR : RabbitMQ_ipaddr should be enter to  RabbitMQ IP address"
        _error_flag=true
    fi

    # config_id: MQ_QUEUE_NAME
    if [ -z "${RabbitMQ_queuename}" ]; then
        log "ERROR : RabbitMQ_queuename should be enter to  RabbitMQ Queue name"
        _error_flag=true
    fi

    # MySQL root password
    if [ -z "${db_root_password}" ]; then
        log "ERROR : db_root_password should be enter to  MySQL root password."
        _error_flag=true
    fi

    # MySQL database name
    if [ -z "${db_name}" ]; then
        log "ERROR : db_name should be enter to  MySQL database name."
        _error_flag=true
    fi

    # MySQL username
    if [ -z "${db_username}" ]; then
        log "ERROR : db_username should be enter to  MySQL username."
        _error_flag=true
    fi

    # MySQL user's password
    if [ -z "${db_password}" ]; then
        log "ERROR : db_password should be enter to  MySQL user password"
        _error_flag=true
    fi

    #################################
    ### oase_uninstall_core.sh 用
    # config_id: db_erase
    if [ -z "${db_erase}" ]; then
        log "ERROR : db_erase should be enter to value(erase or leave)"
        _error_flag=true
    fi

    if ${_error_flag}; then
        log "ERROR : Something is wrong with the answerfile"
        exit 1
    fi
    log "INFO : Finished to check answer vars" 
}

# answerfile読み込み
function read_answerfile() {
    log "INFO : Start to read the answerfile"
    local _answerfile_path="${1}"

    if [ -z ${_answerfile_path} ]; then
        log "ERROR : Failure. Need parameter"
        return 1
    fi

    read_setting_file "${_answerfile_path}"
    if [ $? -gt 0 ]; then
        log "ERROR : Failed to read the answerfile. path=${_answerfile_path}"
        return 1
    fi

    check_answer_vars
    if [ $? -gt 0 ]; then
        log "ERROR : Something is wrong with the answerfile"
        return 1
    fi
    log "INFO : Finished to read the answerfile"  
}

############################################################################
# 共通関数export
export -f log
export -f read_answerfile
