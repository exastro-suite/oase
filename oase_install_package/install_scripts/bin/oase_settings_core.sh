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
#    OASE環境設定ツール
#
############################################################
readonly OASE_SETUP_SCRIPT=${OASE_INSTALL_BIN_DIR}/oase_app_setup_core.sh
readonly MIDDLEWAER_SETUP_SCRIPT=${OASE_INSTALL_BIN_DIR}/oase_middleware_setup_core.sh
readonly SERVICE_SETUP_SCRIPT=${OASE_INSTALL_BIN_DIR}/oase_service_setup_core.sh

# OASE app setup
################################################################################
log "INFO : Start OASE app setup."
################################################################################
bash ${OASE_SETUP_SCRIPT}

################################################################################
if [ $? -gt 0 ]; then
  log "ERROR : OASE app setup failure."
  exit 1
else
  log "INFO : OASE app setup is completed."
fi
################################################################################


# middleware setup
################################################################################
log "INFO : Start middleware setup."
################################################################################
bash ${MIDDLEWAER_SETUP_SCRIPT}

################################################################################
if [ $? -gt 0 ]; then
  log "ERROR : Middleware setup failure."
  exit 1
else
  log "INFO : Middleware setup is completed."
fi
################################################################################


# service setup
################################################################################
log "INFO : Start service setup."
################################################################################
bash ${SERVICE_SETUP_SCRIPT}

################################################################################
if [ $? -gt 0 ]; then
  log "ERROR : service setup failure."
  exit 1
else
  log "INFO : service setup is completed."
fi
################################################################################
