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
#    OASE資材展開用ツール
#
############################################################

################################################################################
# configuration functions

readonly OASE_DIRECTORY="${oase_directory}"
readonly OASE_PACKAGE=$OASE_INSTALL_PACKAGE_DIR/OASE/oase-contents/OASE.tar.gz

################################################################################
# main

################################################################################
log "INFO : Start material deployment."
################################################################################

################################################################################
log "INFO : Create directory to place OASE."
################################################################################
if ! test -d "$OASE_DIRECTORY" ; then
    mkdir -p "$OASE_DIRECTORY"
    if ! test -d "$OASE_DIRECTORY" ; then
        log "ERROR : Failed to make $OASE_DIRECTORY directory."
        exit 1
    fi
else
    log "INFO : $OASE_DIRECTORY already exists."
fi

if [ ! -e "$OASE_PACKAGE" ]; then
    log "$OASE_PACKAGE not exists."
    exit 1
fi

cp -fp "$OASE_PACKAGE" "$OASE_DIRECTORY"

cd "$OASE_DIRECTORY"
tar -zxf "$OASE_DIRECTORY"/OASE.tar.gz
rm -f "$OASE_DIRECTORY"/OASE.tar.gz


if ! test -e "$OASE_INSTALL_SCRIPTS_DIR/list/777R_list.txt" ; then
    log "INFO : 777_list.txt does not be found."

else
    while read LINE; do
        chmod -R 777 "$OASE_DIRECTORY"/OASE"$LINE"
        LINE_1="${LINE%\/*}"
        LINE_2="${LINE##*/}"
        RES=`ls -l "$OASE_DIRECTORY"/OASE"$LINE_1" 2> /dev/null | grep -- "$LINE_2" | grep rwxrwxrwx`
        if [ "${#RES}" -eq 0 ]; then
            log "WARNING : Failed to place $LINE."
        fi
    done < "$OASE_INSTALL_SCRIPTS_DIR/list/777R_list.txt"

fi

yum list installed | grep "httpd" > /dev/null
if [ $? -eq 0 ]; then
    mkdir /exastro/OASE/oase-root/logs/webaplogs/debug
    touch /exastro/OASE/oase-root/logs/webaplogs/webap.log
    touch /exastro/OASE/oase-root/logs/webaplogs/debug/webap.log
    chown -R apache:apache /exastro/OASE/oase-root/logs/webaplogs/
fi


################################################################################
log "INFO : Material deployment is completed."
################################################################################

