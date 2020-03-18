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
#    OASEサービス登録ツール
#
############################################################

create_symboliclink_oase_env(){
    if [ $# -ne 2 ]; then
        log "ERROR : missing required positional argument"
        log "INFO : Abort installation."
        exit 1
    fi
    log "INFO : set symboliclink $2." 
    ln -fs $1 $2
}

create_symboliclink(){
    if [ $# -ne 4 ]; then
        log "ERROR : missing required positional argument"
        log "INFO : Abort installation."
        exit 1
    fi
    log "INFO : set symboliclink $2." 
    ln -fs $1 $2    
    log "INFO : set service file $4." 
    cp -fp $3 $4
}

run_systemctl() {
        log "INFO : start ${1}." 

    if [ $# -ne 1 ]; then
        log "ERROR : missing required positional argument"
        log "INFO : Abort installation." 
        exit 1
    fi

    result=$(systemctl daemon-reload 2>&1)
    if [ $? -ne 0 ]; then
        log "ERROR : $result."
        log "INFO : Abort installation." 
        exit 1
    fi

    result=$(systemctl start $1 2>&1)
    if [ $? -ne 0 ]; then
        log "ERROR : $result."
        log "INFO : Abort installation." 
        exit 1
    fi

    result=$(systemctl enable $1 2>&1)
    if [ $? -ne 0 ]; then
        log "ERROR : $result."
        log "INFO : Abort installation." 
        exit 1
    fi

    return 0

}

################################################################################
# main
################################################################################
log "INFO : Start registration."
################################################################################

OASE_DIR="${oase_directory}"
OASE_ROOT_DIR="$OASE_DIR"/OASE/oase-root
OASE_ENV_DIR=${OASE_ROOT_DIR}/confs/backyardconfs/services
OASE_ENV_FILE=${OASE_ENV_DIR}/oase_env
OASE_ACTION_ENV_FILE=${OASE_ENV_DIR}/oase_action_env
OASE_AGENT_ENV_FILE=${OASE_ENV_DIR}/oase_agent_env
OASE_APPLY_ENV_FILE=${OASE_ENV_DIR}/oase_apply_env
OASE_ACCEPT_ENV_FILE=${OASE_ENV_DIR}/oase_accept_env
SYSCONFIG_FILE_DIR=/etc/sysconfig
SYSCONFIG_ENV_FILE=${SYSCONFIG_FILE_DIR}/oase_env
SYSCONFIG_ACTION_ENV_FILE=${SYSCONFIG_FILE_DIR}/oase_action_env
SYSCONFIG_AGENT_ENV_FILE=${SYSCONFIG_FILE_DIR}/oase_agent_env
SYSCONFIG_APPLY_ENV_FILE=${SYSCONFIG_FILE_DIR}/oase_apply_env
SYSCONFIG_ACCEPT_ENV_FILE=${SYSCONFIG_FILE_DIR}/oase_accept_env
OASE_BACKYARDS_DIR=${OASE_ROOT_DIR}/backyards
OASE_ACTION_SERVICE=${OASE_BACKYARDS_DIR}/action_driver/oase-action.service
OASE_AGENT_SERVICE=${OASE_BACKYARDS_DIR}/agent_driver/oase-agent.service
OASE_APPLY_SERVICE=${OASE_BACKYARDS_DIR}/apply_driver/oase-apply.service
OASE_ACCEPT_SERVICE=${OASE_BACKYARDS_DIR}/accept_driver/oase-accept.service
SERVICE_FILE_DIR=/usr/lib/systemd/system
SERVICE_ACTION_SERVICE=${SERVICE_FILE_DIR}/oase-action.service
SERVICE_AGENT_SERVICE=${SERVICE_FILE_DIR}/oase-agent.service
SERVICE_APPLY_SERVICE=${SERVICE_FILE_DIR}/oase-apply.service
SERVICE_ACCEPT_SERVICE=${SERVICE_FILE_DIR}/oase-accept.service


# OASE環境設定ファイルのリンク作成
if [ ! -e "$OASE_ENV_FILE" ]; then
    log "ERROR : $OASE_ENV_FILE not exists."
    log "INFO : Abort installation."
    exit 1
fi
create_symboliclink_oase_env  "$OASE_ENV_FILE" "$SYSCONFIG_ENV_FILE"


# oase-action.serviceの登録
if [ ! -e "$OASE_ACTION_ENV_FILE" ]; then
    log "ERROR : $OASE_ACTION_ENV_FILE not exists."
    log "INFO : Abort installation."
    exit 1
fi

if [ ! -e "$OASE_ACTION_SERVICE" ]; then
    log "ERROR : $OASE_ACTION_SERVICE not exists."
    log "INFO : Abort installation."
    exit 1
fi

create_symboliclink "$OASE_ACTION_ENV_FILE" "$SYSCONFIG_ACTION_ENV_FILE" "$OASE_ACTION_SERVICE" "$SERVICE_ACTION_SERVICE"

if [ ! -e "$SERVICE_ACTION_SERVICE" ]; then
    log "ERROR : $SERVICE_ACTION_SERVICE not exists."
    log "INFO : Abort installation."
    exit 1
fi


# oase-agent.serviceの登録
if [ ! -e "$OASE_AGENT_ENV_FILE" ]; then
    log "ERROR : $OASE_AGENT_ENV_FILE not exists."
    log "INFO : Abort installation."
    exit 1
fi

if [ ! -e "$OASE_AGENT_SERVICE" ]; then
    log "ERROR : $OASE_AGENT_SERVICE not exists."
    log "INFO : Abort installation."
    exit 1
fi

create_symboliclink "$OASE_AGENT_ENV_FILE" "$SYSCONFIG_AGENT_ENV_FILE" "$OASE_AGENT_SERVICE" "$SERVICE_AGENT_SERVICE"

if [ ! -e "$SERVICE_AGENT_SERVICE" ]; then
    log "ERROR : $SERVICE_AGENT_SERVICE not exists."
    log "INFO : Abort installation."
    exit 1
fi


# oase-apply.serviceの登録
if [ ! -e "$OASE_APPLY_ENV_FILE" ]; then
    log "ERROR : $OASE_APPLY_ENV_FILE not exists."
    log "INFO : Abort installation."
    exit 1
fi

if [ ! -e "$OASE_APPLY_SERVICE" ]; then
    log "ERROR : $OASE_APPLY_SERVICE not exists."
    log "INFO : Abort installation."
    exit 1
fi

create_symboliclink "$OASE_APPLY_ENV_FILE" "$SYSCONFIG_APPLY_ENV_FILE" "$OASE_APPLY_SERVICE" "$SERVICE_APPLY_SERVICE"

if [ ! -e "$SERVICE_APPLY_SERVICE" ]; then
    log "ERROR : $SERVICE_APPLY_SERVICE not exists."
    log "INFO : Abort installation."
    exit 1
fi


# oase-accept.serviceの登録
if [ ! -e "$OASE_ACCEPT_ENV_FILE" ]; then
    log "ERROR : $OASE_ACCEPT_ENV_FILE not exists."
    log "INFO : Abort installation."
    exit 1
fi

if [ ! -e "$OASE_ACCEPT_SERVICE" ]; then
    log "ERROR : $OASE_ACCEPT_SERVICE not exists."
    log "INFO : Abort installation."
    exit 1
fi

create_symboliclink "$OASE_ACCEPT_ENV_FILE" "$SYSCONFIG_ACCEPT_ENV_FILE" "$OASE_ACCEPT_SERVICE" "$SERVICE_ACCEPT_SERVICE"

if [ ! -e "$SERVICE_ACCEPT_SERVICE" ]; then
    log "ERROR : $SERVICE_ACCEPT_SERVICE not exists."
    log "INFO : Abort installation."
    exit 1
fi

# start services
run_systemctl nginx.service
run_systemctl uwsgi.service
run_systemctl oase-action.service
run_systemctl oase-agent.service
run_systemctl oase-apply.service
run_systemctl oase-accept.service

# jboss-eap-rhel service start
log "INFO : Start Red Hat Decision Manager service"
result=$(chkconfig --add jboss-eap-rhel.sh 2>&1)
if [ $? -ne 0 ]; then
    log "ERROR : $result"
    log "INFO : Abort installation." 
    exit 1
fi

result=$(service jboss-eap-rhel start 2>&1)
if [ $? -ne 0 ]; then
    log "ERROR : $result"
    log "INFO : Abort installation." 
    exit 1
fi

result=$(chkconfig jboss-eap-rhel.sh on  2>&1)
if [ $? -ne 0 ]; then
    log "ERROR : $result"
    log "INFO : Abort installation." 
    exit 1
fi


################################################################################
log "INFO : Registration is complete."
################################################################################
