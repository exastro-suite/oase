#!/bin/sh
#
######################################################################
##
##  【スクリプトファイル名】
##      ky_loopcall-python-procedure.sh
##
##  【概要】
##      pythonでコーディングされたプロシージャファイルを無限ループする
##      無限ループの停止条件は以下。
##      ・ロックファイルが存在しない場合
##      ・pythonプロシージャからの戻り値が「1」の場合
##        (pythonプロシージャは警告終了の場合に戻り値「2」を返却するが
##         その場合は無限ループを継続する)
##
##  【特記事項】
##      <<引数>>
##       I   $1  ロックファイル
##               (ファイルが存在する限り無限ループする仕様)
##       I   $2  pythonモジュール(フルパス)
##       I   $3  pythonプロシージャ(フルパス)
##       I   $4  ログ出力ディレクトリ(フルパス)
##       I   $5  インターバル(＝ループ間隔(sec)) ※0以上を指定
##       I   $6  ログレベル ※「DEBUG」 or 「NORMAL」
##      <<返却値>>
##       0      正常終了
##       その他 異常終了(異常行数)
##
######################################################################
#----------------------------------------------------#
# パラメータ設定
#----------------------------------------------------#
LOCK=${0}
PYTHON_MODULE=${1}
PYTHON_PROCEDURE=${3}
LOG_DIR=${4}
RUN_INTERVAL=${5}
LOG_LEVEL=${6}
echo "${4}"
echo "${5}"
echo "${6}"

#----------------------------------------------------#
# PROCESS名を取得
#----------------------------------------------------#
PROCESS_NAME=`basename ${0}`

#----------------------------------------------------#
# PYTHON_PROCEDURE名を取得
#----------------------------------------------------#
PYTHON_PROCEDURE_NAME=`basename ${PYTHON_PROCEDURE}`

#----------------------------------------------------#
# ログファイル名を作成
#----------------------------------------------------#
# スクリプトファイル名から拡張子を削除
LOG_NAME_PREFIX=${PROCESS_NAME%.*}

#----------------------------------------------------#
# グローバル変数宣言
#----------------------------------------------------#
export LOG_DIR
export LOG_NAME_PREFIX
export LOG_LEVEL
export PROCESS_NAME
export PYTHON_PROCEDURE_NAME
export PYTHON_MODULE
export RUN_INTERVAL

#----------------------------------------------------#
# ログ出力＆プロセス終了ファンクション
#
# [動作]
# 本ファンクションは2つの役割を持つ。
#   ・ログ出力
#   ・プロセス終了
# ログレベルと終了コードにより動作が確定される。
# [終了コード] [ログレベル] ⇒ [プロセス終了] [ログ出力]
#  -1           NORMAL      ⇒  ×             ×
#  -1           DEBUG/TRACE ⇒  ×             ○
#  -1以外       NORMAL      ⇒  ○             ○
#  -1以外       DEBUG/TRACE ⇒  ○             ○
#----------------------------------------------------#
function commonFunction
{
    # パラメータ格納
    P_RetCode=$1    # 終了コード
                    # ("-1"の場合は終了しない。またLOG_LEVELが'NORMAL'の場合はログを出さない)
    P_Message=$2    # メッセージ本文
    
    if    [ ${P_RetCode} -ne -1 -o "${LOG_LEVEL}" = 'DEBUG' ] \
       || [ ${P_RetCode} -ne -1 -o "${LOG_LEVEL}" = 'TRACE' ]
    then
        # ログファイル名を作成
        LOG_NAME=${LOG_DIR}"/"${LOG_NAME_PREFIX}"_"`date '+%Y%m%d'`".log"
        
        # メッセージ出力
        MESSAGE="["`date '+%Y/%m/%d %H:%M:%S'`"][${PROCESS_NAME}][${PYTHON_PROCEDURE_NAME}][$$]${P_Message}"
        echo ${MESSAGE} >> ${LOG_NAME}
    fi
    
    if [ ${P_RetCode} -ne -1 ]
    then
        MESSAGE="["`date '+%Y/%m/%d %H:%M:%S'`"][${PROCESS_NAME}][${PYTHON_PROCEDURE_NAME}][$$]Process Abort(Error:[Line]${P_RetCode})"
        echo ${MESSAGE} >> ${LOG_NAME}
        exit ${P_RetCode}
    fi
}

#----------------------------------------------------#
# 開始メッセージ
#----------------------------------------------------#
commonFunction -1 "Process : Start"

#----------------------------------------------------#
# 多重起動防止
#----------------------------------------------------#
COMM="$0 $*"
if [ $$ != `pgrep -fo "${COMM}"` ]
then
    commonFunction ${LINENO} "Process : Multiple start-up prevention check NG"
fi
commonFunction -1 "Process : Multiple start-up prevention check OK"

#----------------------------------------------------#
# PYTHONプロシージャ実行
#----------------------------------------------------#
error_flag=0
commonFunction -1 "Loop : Start"

while :
do
    # ロックファイル存在確認
    if [ ! -f ${LOCK} ]
    then
        commonFunction -1 "Loop : Break(Lock-file removed)"
        RET_CD=0
        break
    fi
    # PYTHONプロシージャ実行
    commonFunction -1 "PYTHON-Procedure : Execute"
    ${PYTHON_MODULE} ${PYTHON_PROCEDURE}
    RET_CD=$?
    if [ ${RET_CD} -eq 1 ]
    then
        commonFunction -1 "PYTHON-Procedure : Abort(Error：[code]${RET_CD})"
        error_flag=1
        break
    fi
    commonFunction -1 "PYTHON-Procedure : Result OK"
    
    # インターバル(sec)だけスリープ
    sleep ${RUN_INTERVAL}
done

if [ ${error_flag} -eq 0 ]
then
    commonFunction -1 "Loop : Finish"
    commonFunction -1 "Process : Finish"
    exit 0
else
    commonFunction ${LINENO} "Loop : Abort"
fi

