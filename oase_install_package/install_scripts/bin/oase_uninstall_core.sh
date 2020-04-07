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

JBOSS_CONF_FILE=/etc/default/jboss-eap.conf
JBOSS_ROOT_DIR="${jboss_root_directory}"
STANDALONE_FULL_FILE="${JBOSS_ROOT_DIR}"/standalone/configuration/standalone-full.xml

KERNEL_PARAM_FILE=/etc/sysctl.conf
NGINX_CONF_FILE=/etc/nginx/nginx.conf
OASE_CONF_FILE=/etc/nginx/conf.d/oase.conf
UWSGI_SOCK_DIR=/home/uWSGI
INITD_DIR=/etc/init.d

NOW_STRING=$(date "+_%Y%m%d%H%M%S")

################################################################################
# functions

function disable_service() {
    log "INFO : Start to disable service"

    local _error_flag=false

    # TODO parallel化？
    for _service in $@; do
        log "INFO : Start to stop ${_service}"
        systemctl stop ${_service}
        if [ $? -gt 0 ]; then
            log "ERROR : Failed to stop ${_service}"
            _error_flag=true
        else
            log "INFO : Finished to stop ${_service}"
        fi

        if [ ${_service} = jboss-eap-rhel ]; then
            log "INFO : Start to delete ${_service}.sh"
            chkconfig --del ${_service}.sh
            if [ $? -gt 0 ]; then
                log "ERROR : Failed to delete ${_service}.sh"
            else
                log "INFO : Finished to delete ${_service}.sh"
            fi
        else
            log "INFO : Start to disable ${_service}"
            systemctl disable ${_service}
            if [ $? -gt 0 ]; then
                log "ERROR : Failed to disable ${_service}"
                _error_flag=true
            else
                log "INFO : Finished to disable ${_service}"
            fi
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

    # 環境操作のため今は対象外（環境含めたインストールの際に復活させる）
    # # /etc/profile (maven用)
    # repair_conffile '/etc/profile' 'repair_command_etc_profile'
    # if [ $? -gt 0 ]; then
    #     _error_flag=true
    # fi

    # /etc/sysctl.conf (uwsgi用)
    repair_conffile "${KERNEL_PARAM_FILE}"
    if [ $? -gt 0 ]; then
        _error_flag=true
    fi

    remove_directory "${UWSGI_SOCK_DIR}"
    if [ $? -gt 0 ]; then
        _error_flag=true
    fi

    # nginx
    repair_conffile "${NGINX_CONF_FILE}"
    if [ $? -gt 0 ]; then
        _error_flag=true
    fi

    repair_conffile "${OASE_CONF_FILE}"
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

    remove_file "${INITD_DIR}/jboss-eap-rhel.sh"
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
    # TODO parallel化？
    for _service in $@; do
        if [ ${_service} = ${_systemd_dir} ]; then
            continue # $1だけ飛ばす
        fi
        log "INFO : Start to remove ${_service}.service"
        local _original_file=${_systemd_dir}/${_service}.service
        local _backup_file=${_original_file}${OASE_BACKUP_FILE_SUFFIX}${NOW_STRING}
        /bin/mv ${_original_file} ${_backup_file}
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
    mysql -u root -p${db_root_password} -e "DROP USER IF EXISTS ${db_username}@'%';"
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
disable_service 'nginx uwsgi jboss-eap-rhel'
if [ $? -gt 0 ]; then
    error_flag=true
fi

delete_service '/etc/systemd/system' 'nginx uwsgi'
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
