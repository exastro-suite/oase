#!/bin/bash
#   Copyright 2019 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
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
#  OASE settings.py 生成ツール
#
############################################################

################################################################################
# main

# create settings.py with sample copy
log "INFO : Create settings.py"

readonly OASE_CONFS_DIR=$(cd "${oase_directory}/OASE/oase-root/confs/frameworkconfs";pwd)
readonly SETTINGS_SAMPLE_FILE=${OASE_CONFS_DIR}/settings.py.sample
readonly OASE_SETTING_FILE=${OASE_CONFS_DIR}/settings.py

# format init_custom.yaml
if [ ! -e $OASE_SETTING_FILE ]; then
    cp $SETTINGS_SAMPLE_FILE $OASE_SETTING_FILE
fi

################################################################################
log "INFO : Start Create Setting.py."
################################################################################
# input contents from anser_file for settings.py

if [ ${oase_session_engine} = "db" ]; then
    sed -i -e "/^SESSION_ENGINE/s/.*/SESSION_ENGINE = 'django.contrib.sessions.backends.db'/g" $OASE_SETTING_FILE
    sed -i -e 's/^SESSION_FILE_PATH/#SESSION_FILE_PATH/g' $OASE_SETTING_FILE

elif [ ${oase_session_engine} = "file" ]; then
    if [ ! -e "${oase_directory}/OASE/oase-root/temp/sessions" ]; then
        log "INFO : create sessions directory."
        mkdir -p $oase_directory/OASE/oase-root/temp/sessions
    fi
    sed -i -e "/^SESSION_ENGINE/s/.*/SESSION_ENGINE = 'django.contrib.sessions.backends.file'/g" $OASE_SETTING_FILE
    sed -i -e 's/^#SESSION_FILE_PATH/SESSION_FILE_PATH/g' $OASE_SETTING_FILE

else
    sed -i -e "/^SESSION_ENGINE/s/.*/SESSION_ENGINE = 'django.contrib.sessions.backends.cache'/g" $OASE_SETTING_FILE
    sed -i -e 's/^SESSION_FILE_PATH/#SESSION_FILE_PATH/g' $OASE_SETTING_FILE
fi

sed -i -e 's/^#EVTIMER_SERVER/EVTIMER_SERVER/g' $OASE_SETTING_FILE
sed -i -e 's/^#    "type"/    "type"/g' $OASE_SETTING_FILE
sed -i -e 's/^#    "protocol"/    "protocol"/g' $OASE_SETTING_FILE
sed -i -e 's/^#    "location"/    "location"/g' $OASE_SETTING_FILE
sed -i -e 's/^#    "path"/    "path"/g' $OASE_SETTING_FILE
sed -i -e 's/^#}/}/g' $OASE_SETTING_FILE

sed -i -e '/^    "location"/s/127.0.0.1/'${ev_location}'/g' $OASE_SETTING_FILE
sed -i -e '/^LANGUAGE_CODE/s/ja/'${oase_language}'/g' $OASE_SETTING_FILE

sed -i -e "/^        'NAME'     :/s/OASE_DB/${db_name}/g" $OASE_SETTING_FILE
sed -i -e "/^        'USER'     :/s/OASE_USER/${db_username}/g" $OASE_SETTING_FILE
sed -i -e "/^        'PASSWORD' :/s/OASE_PASSWD/${db_password}/g" $OASE_SETTING_FILE

################################################################################
log "INFO : Create Setting.py is completed."
################################################################################

################################################################################
# call DB setup shell
log "INFO : Bash DB SETUP Shell"
readonly OASE_DB_SETUP_SHELL=${OASE_INSTALL_BIN_DIR}/oase_db_setup_core.sh

bash $OASE_DB_SETUP_SHELL
RESULT=$?

if [ ${RESULT} -ne 0 ]; then
    log "INFO : Bash DB SETUP Shell is failed."
    exit 1
fi
log "INFO : Bash DB SETUP Shell is completed."
