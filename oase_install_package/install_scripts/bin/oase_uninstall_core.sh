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
#    OASEアンインストールツール
#
############################################################


################################################################################
# global variables

readonly OASE_BACKUP_FILE_SUFFIX='.oase_bk'
readonly OASE_UNINSTALING_FILE_SUFFIX='.oase_during_uninstallation'

JBOSS_ROOT_DIR="${jboss_root_directory}"
JBOSS_CONF_FILE="${JBOSS_ROOT_DIR}"/wildfly-14.0.1.Final/bin/standalone.conf
STANDALONE_FULL_FILE="${JBOSS_ROOT_DIR}"/wildfly-14.0.1.Final/standalone/configuration/standalone-full.xml

KERNEL_PARAM_FILE=/etc/sysctl.conf
OASE_CONF_FILE=/etc/httpd/conf.d/oase.conf

MAVEN_CONF_SETTINGS_FILE=/opt/apache-maven/conf/settings.xml
M2_SETTINGS_DIR=/root/.m2
M2_SETTINGS_FILE="${M2_SETTINGS_DIR}"/settings.xml

NOW_STRING=$(date "+_%Y%m%d%H%M%S")

################################################################################
# functions

function disable_service() {
    log "INFO : Start to disable service"

    local _error_flag=false

    for _service in $@; do
        log "INFO : Start to stop ${_service}"
        systemctl stop ${_service}
        if [ $? -gt 0 ]; then
            log "ERROR : Failed to stop ${_service}"
            _error_flag=true
        else
            log "INFO : Finished to stop ${_service}"
        fi

        log "INFO : Start to disable ${_service}"
        systemctl disable ${_service}
        if [ $? -gt 0 ]; then
            log "ERROR : Failed to disable ${_service}"
            _error_flag=true
        else
            log "INFO : Finished to disable ${_service}"
        fi
    done

    if ${_error_flag}; then
        log "ERROR : Failed to disable service"
        return 1
    else
        log "INFO : Finished to disable service"
        return 0
    fi
}

function repair_conffile() {

    # "[対象のファイル名].oase_bk"が存在するか判定, 無ければERROR
    # 対象ファイルを"[対象のファイル名].oase_bk_%Y%m%d%H%M%S"にリネームしてバックアップ
    # "[対象のファイル名].oase_bk"から".oase_bk"取りインストーラー実行前の状態に戻す

    if [ $# -ne 1 ]; then
        log "ERROR : missing required positional argument"
        return 1
    fi

    local _error_flag=false
    local _conffile="${1}"
    local _conffile_backup="${_conffile}${OASE_BACKUP_FILE_SUFFIX}"
    local _conffile_now="${_conffile_backup}${NOW_STRING}"

    log "INFO : Start to repair conf file. ${_conffile}"

    if [ ! -f "${_conffile_backup}" ]; then
        log "ERROR : Missing ${_conffile_backup}"
        return 1
    fi

    result=$(mv ${_conffile} ${_conffile_now} 2>&1)
    if [ $? -gt 0 ]; then
        log "ERROR : ${result}"
        _error_flag=true
    fi

    result=$(mv ${_conffile_backup} ${_conffile} 2>&1)
    if [ $? -gt 0 ]; then
        log "ERROR : ${result}"
        _error_flag=true
    fi

    if ${_error_flag}; then
        log "ERROR : Faild to repair conf file. ${_conffile}"
        return 1
    else
        log "INFO : Finished to repair conf file. ${_conffile}"
        return 0
    fi
}

function remove_file() {

    # バックアップ不要?

    if [ $# -ne 1 ]; then
        log "ERROR : missing required positional argument"
        return 1
    fi

    local _target_file=${1}

    log "INFO : Start to remove ${_target_file}"

    /bin/rm -f ${_target_file}

    if [ $? -gt 0 ]; then
        log "ERROR : Failed to remove oase directory (${_target_file})"
        return 1
    else
        log "INFO : Finished to remove ${_target_file}"
    fi

    return 0
}

function remove_directory() {

    if [ $# -ne 1 ]; then
        log "ERROR : missing required positional argument"
        return 1
    fi

    local _target_dir=${1}

    log "INFO : Start to remove ${_target_dir}"

    /bin/rm -rf ${_target_dir} 

    if [ $? -gt 0 ]; then
        log "ERROR : Failed to remove oase directory (${_target_dir})"
        return 1
    else
        log "INFO : Finished to remove ${_target_dir}"
    fi

    return 0
}

function delete_middleware_confs() {
    log "INFO : Start to delete middleware confs"

    local _error_flag=false

    # /etc/profile (maven用)
    repair_conffile '/etc/profile'
    if [ $? -gt 0 ]; then
        _error_flag=true
    fi

    /bin/rm -f "${OASE_CONF_FILE}"
    if [ $? -gt 0 ]; then
        _error_flag=true
    fi

    # decision server
    repair_conffile "${JBOSS_CONF_FILE}"
    if [ $? -gt 0 ]; then
        _error_flag=true
    fi

    repair_conffile "${STANDALONE_FULL_FILE}"
    if [ $? -gt 0 ]; then
        _error_flag=true
    fi

    repair_conffile "${MAVEN_CONF_SETTINGS_FILE}"
    if [ $? -gt 0 ]; then
        _error_flag=true
    fi

    /bin/rm -f "${M2_SETTINGS_FILE}"
    if [ $? -gt 0 ]; then
        _error_flag=true
    fi

    if ${_error_flag}; then
        log "ERROR : Failed to delete middleware confs"
        return 1
    else
        log "INFO : Finished to delete middleware confs"
        return 0
    fi
}

function delete_service() {
    log "INFO : Start to delete service"

    local _error_flag=false

    local _systemd_dir=$1

    for _service in $@; do
        if [ ${_service} = ${_systemd_dir} ]; then
            continue # $1だけ飛ばす
        fi
        log "INFO : Start to remove ${_service}.service"
        local _original_file=${_systemd_dir}/${_service}.service
        /bin/rm -f ${_original_file}
        if [ $? -gt 0 ]; then
            log "ERROR : Failed to remove ${_service}.service"
            _error_flag=true
        else
            log "INFO : Finished to remove ${_service}.service"
        fi
    done

    log "INFO : Start to execute daemon-reload"
    systemctl daemon-reload
    if [ $? -gt 0 ]; then
        log "ERROR : Failed to execute daemon-reload"
        _error_flag=true
    else
        log "INFO : Finished to execute daemon-reload"
    fi

    if ${_error_flag}; then
        log "ERROR : Failed to delete service"
        return 1
    else
        log "INFO : Finished to delete service"
        return 0
    fi
}

function delete_oase_service() {
    log "INFO : Start to delete oase service"

    local _OASE_SERVICES='oase-apply oase-agent oase-action oase-accept'
    local _error_flag=false

    disable_service ${_OASE_SERVICES}
    if [ $? -gt 0 ]; then
        _error_flag=true
    fi

    delete_service '/usr/lib/systemd/system' ${_OASE_SERVICES}
    if [ $? -gt 0 ]; then
        _error_flag=true
    fi

    if ${_error_flag}; then
        log "ERROR : Failed to delete oase service"
        return 1
    else
        log "INFO : Finished to delete oase service"
        return 0
    fi
}

function delete_oase_env() {
    log "INFO : Start to delete oase env"

    local _OASE_ENV_FILES='oase_env oase_apply_env oase_agent_env oase_action_env oase_accept_env'
    local _error_flag=false

    for _oase_env in ${_OASE_ENV_FILES}; do
        log "INFO : Start to unlink /etc/sysconfig/${_oase_env}"
        unlink /etc/sysconfig/${_oase_env}
        if [ $? -gt 0 ]; then
            log "ERROR : Failed to unlink ${_oase_env}"
            _error_flag=true
        else
            log "INFO : Finished to unlink /etc/sysconfig/${_oase_env}"
        fi
    done

    if ${_error_flag}; then
        log "ERROR : Failed to delete oase env"
        return 1
    else
        log "INFO : Finished to delete oase env"
        return 0
    fi
}

function drop_oase_db() {
    log "INFO : Start to drop oaseDB"
    local _error_flag=false

    log "INFO : Start to drop database"
    mysql -u root -p${db_root_password} -e "DROP DATABASE IF EXISTS ${db_name};"
    if [ $? -gt 0 ]; then
        log "ERROR : Failed to drop database"
        _error_flag=true    
    fi

    log "INFO : Start to drop user"
    mysql -u root -p${db_root_password} -e "DROP USER IF EXISTS ${db_username}@'localhost';"
    if [ $? -gt 0 ]; then
        log "ERROR : Failed to drop user"
        _error_flag=true
    fi

    if ${_error_flag}; then
        log "ERROR : Failed to drop oaseDB"
        return 1
    else
        log "INFO : Finished to drop oaseDB"
        return 0
    fi
}

function delete_oase_contents() {
    log "INFO : Start to delete oase contents"

    answer_oase_dir="${oase_directory}"
    target_dir=$(cd ${answer_oase_dir} && pwd)

    if [ "${target_dir}" = '/' -o "${answer_oase_dir}" = '' ]; then
        log "ERROR : Failed to remove oase directory (invalid parameter:${answer_oase_dir})"
        return 1
    fi

    if [ ! -d "${target_dir}" ]; then
        log "ERROR : Failed to remove oase directory (not exists ${target_dir})"
        return 1
    fi

    remove_directory "${target_dir}"

    if [ $? -gt 0 ]; then
        log "ERROR : Failed to delete oase contents"
        return 1
    else
        log "INFO : Finished to delete oase contents"
        return 0
    fi
}


function delete_server_certificate() {
    log "INFO : Start to delete server certificate"

    if [ "$certificate_path" != "" -a "$private_key_path" != "" ]; then
        CRT_FILE=$(echo $(basename ${certificate_path}))
        KEY_FILE=$(echo $(basename ${private_key_path}))
    else
        CRT_FILE="$oase_domain.crt"
        KEY_FILE="$oase_domain.key"
    fi

    if [ -e /etc/pki/tls/certs/"$CRT_FILE" ]; then
        rm -f /etc/pki/tls/certs/"$CRT_FILE"
    fi

    if [ -e /etc/pki/tls/certs/"$KEY_FILE" ]; then
        rm -f /etc/pki/tls/certs/"$KEY_FILE"
    fi

    if [ -e /etc/pki/tls/certs/"$CRT_FILE" ]; then
        log "WARNING : Failed to delete ${CRT_FILE}."
    fi

    if [ -e /etc/pki/tls/certs/"$KEY_FILE" ]; then
        log "WARNING : Failed to delete ${KEY_FILE}."
    fi

}

################################################################################
# main

#-----------------------------------------------------------
# uninstall開始
#-----------------------------------------------------------
log 'INFO : -----MODE[UNINSTALL] START-----'

error_flag=false

#----------------------------------------
# 各種 middleware サービス停止
#----------------------------------------
disable_service 'httpd drools rabbitmq-server'
if [ $? -gt 0 ]; then
    error_flag=true
fi

delete_service '/usr/lib/systemd/system' 'drools'
if [ $? -gt 0 ]; then
    error_flag=true
fi

#----------------------------------------
# 各種 middleware 設定ファイル削除
#----------------------------------------
delete_middleware_confs
if [ $? -gt 0 ]; then
    error_flag=true
fi

#----------------------------------------
# OASEサービス削除 / oase_env系削除
#----------------------------------------
delete_oase_service
if [ $? -gt 0 ]; then
    # エラー処理
    log 'ERROR : Failed to delete oase services.'
    error_flag=true
fi

delete_oase_env
if [ $? -gt 0 ]; then
    # エラー処理
    log 'ERROR : Failed to delete oase_env files.'
    error_flag=true
fi

#----------------------------------------
# 既存DB削除
#----------------------------------------
if [ ${db_erase} = 'erase' ]; then
    drop_oase_db
    if [ $? -gt 0 ]; then
        error_flag=true
    fi
fi

#----------------------------------------
# OASEソース削除
#----------------------------------------
delete_oase_contents
if [ $? -gt 0 ]; then
    error_flag=true
fi

#----------------------------------------
# サーバ証明書削除
#----------------------------------------
delete_server_certificate
if [ $? -gt 0 ]; then
    error_flag=true
fi

#-----------------------------------------------------------
# uninstall処理終了
#-----------------------------------------------------------
if ${error_flag}; then
    log 'ERROR : Uninstallation is incompleted!'
    log "        -> Check logfile ${OASE_INSTALL_LOG_FILE}"
    exit 1
else
    log 'INFO : Uninstallation is completed!'
    exit 0
fi
