// Copyright 2019 NEC Corporation
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// 
//     http://www.apache.org/licenses/LICENSE-2.0
// 
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//

//////////////////////////////////////////////////////////////////////
//
//  【テンプレートバージョン】
//
//  【特記事項】
//
//
//////////////////////////////////////////////////////////////////////
let ruleTypeName       = "";
let rulemanage_id      = 0;
let rule_type_id       = 0;
let rule_table_name    = "";
let operationstatus_id = 0;
let rule_ids_stg       = [];


//////////////////////////////////////////////////////////////////////
//  ポーリング処理
//////////////////////////////////////////////////////////////////////
let timerID = null;
let resultFlg = null;

$(function() {

    $('#files')
        .css({
            'position': 'absolute',//デフォルトのファイル選択ボタンを遥か彼方に表示
            'top': '-9999px'
            //'display': 'inline-block'
        })
        .change(function() {
            let val = $(this).val();
            let path = val.replace(/\\/g, '/');
            //let match = path.lastIndexOf('/');
            $('#filename').css("display","inline-block");
            $('#filename').val(match !== -1 ? val.substring(match + 1) : val);
        });

    $('#filename').bind('keyup, keydown, keypress', function() {
        return false;
    });

    $('#filename, #btn').click(function() {
        $('#files').trigger('click');
    });

    //プロダクション適用ボタン活性化
    $('.staging-select').each(function(i, e){
      if( $('#staging_sts_'+ $(this).data('rule-manage-id') + ' option:selected').val() === 24){
          $('#pro_teki_'+$(this).data('rule-manage-id')).prop("disabled", false);
      }
    });

    // ステージングのイベント定義
    onloadStaging();

});


//////////////////////////////////////////////////////////////////////
//  ステージング一覧イベント定義
//////////////////////////////////////////////////////////////////////
function onloadStaging() {

    //ステージング適用 運用ステータス変更時の処理
    $('#stagingTable')
        .on('focus','[id^=staging_sts]' ,function() {
            previous = this.value;
        })
        .on('change','[id^=staging_sts]', function() {
            let $this = $(this);
            $this.prop("disabled", true);

            if(confirm(getMessage("MOSJA12128", false))) {
                let data = {
                    "status" : this.value,
                    "rule_manage_id" : $this.attr('data-rule-manage-id'),
                    "csrfmiddlewaretoken" : document.getElementsByName("csrfmiddlewaretoken")[0].value
                };

                $.ajax({
                    type : "POST",
                    url  : "rule/change_status",
                    data : data,
                    dataType : "json",
                })
                .done(function(respdata){
                    alert(respdata.msg);
                    if(respdata.err_flg === 0) {
                        window.location.href = 'rule';
                    }
                })
                .fail(function(respdata, stscode, resp){
                    alert(getMessage('MOSJA00014', false));
                    $this.prop("disabled", false);
                    if(stscode === "error") {
                        window.location.href = "/oase_web/top/logout";
                    }
                });
            }
            else{
                this.value = previous;
                $this.prop("disabled", false);
                return false;
            }
        });


    let trTgtId = "trTgtId";

    //テストリクエストのルール変更時の処理
    $('#selTgtRuleType')
        .focus(function(){
            previous = this.value;
        })
        .change(function(){
            let $this   = $(this);
            let evethis = this;
            $this.prop("disabled", true);
            $('#rule-none').hide();
            $('#rule-detail').prop('hidden', false);

            // 選択されたルール種別名に対応するルールID
            let ruleManageId = this.value;

            let token = null;
            if(document.cookie && document.cookie !== "") {
                let cookies = document.cookie.split(";");
                for(let i = 0; i < cookies.length; i++) {
                    let c = jQuery.trim(cookies[i]);
                    if(c.substring(0, "csrftoken".length + 1) === "csrftoken=") {
                        token = decodeURIComponent(c.substring("csrftoken".length + 1));
                        break;
                    }
                }
            }

            let rule_manage_id      = rulemanage_id;
            let operation_status_id = operationstatus_id;
            let runFlg              = null;
            let stg_flag            = $.inArray(rule_type_id, rule_ids_stg);
            let data;

            if(operation_status_id < 24 && resultFlg === 1 && 0 <= stg_flag ) {
                if(confirm(getMessage("MOSJA12129", false))) {
                    data = {
                        "status" : "24", // 検証完了
                        "rule_manage_id" : rule_manage_id,
                        "csrfmiddlewaretoken" : token
                    };
                } else {
                    data = {
                        "status" : "22", // 検証実施中
                        "rule_manage_id" : rule_manage_id,
                        "csrfmiddlewaretoken" : token
                    };
                }

                runFlg = 1;

                $.ajax({
                    type : "POST",
                    url  : "rule/change_status",
                    data : data,
                    dataType : "json",
                })
                .done(function(respdata){
                    alert(respdata.msg);
                    if(respdata.err_flg !== 0){
                        window.location.href = 'rule';
                    } else {

                        if(confirm(getMessage("MOSJA12130", false))) {

                            let data_details = {
                                "rule_manage_id"      : ruleManageId,
                                "csrfmiddlewaretoken" : token
                            };

                            $.ajax({
                                type : "POST",
                                url  : "rule/get_record",
                                data : data_details,
                                dataType : "json",
                            })
                            .done(function(respdata) {

                                if(respdata.err_flg !== 0){
                                    alert(respdata.msg);
                                    window.location.href = 'rule';
                                } else {

                                    // ルール種別名取得しておく
                                    ruleTypeName = $('[id=selTgtRuleType] option:selected').text();

                                    // polling停止
                                    clearPollingTimer();

                                    // 2回目以降の変更は直前のデータを消す
                                    let beforeObj = document.getElementById(trTgtId);

                                    if(beforeObj !== null) {
                                        beforeObj.parentNode.removeChild(beforeObj);
                                    }

                                    rulemanage_id      = ruleManageId;
                                    rule_type_id       = respdata["data"]["rule_type_id"];
                                    rule_table_name    = respdata["data"]["rule_table_name"];
                                    operationstatus_id = respdata["data"]["operation_status_id"];
                                    rule_ids_stg       = respdata["data"]["rule_ids_stg"];

                                    $("#rule_type_name").text(respdata["data"]["rule_type_name"]);
                                    $("#rule_file_name").text(respdata["data"]["filename"]);
                                    $("#operation_status").text(respdata["data"]["operation_status_str"]);
                                    $("#system_status").text(respdata["data"]["system_status_str"]);
                                    $("#last_update_user").text(respdata["data"]["last_update_user_name"]);
                                    $("#last_update_timestamp").text(respdata["data"]["last_update_timestamp"]);

                                    $("#btnLogDownload").prop("disabled", true);
                                    $("#btnPseudoCall").prop("disabled", false);
                                    $("#btnClear").prop("disabled", false);
                                    $("#logClear").prop("disabled", false);
                                    $("#btnFileClear").prop("disabled", false);
                                    $("#btnExcelDownload").prop("disabled", false);
                                    $("#btnFileSelect").prop("disabled", false);


                                    // 前回のテストリクエスト設定をクリア
                                    $('table[id^="ruleType_"]').hide();

                                    $('#ruleType_' + respdata["data"]["rule_type_id"]).show();
                                    $this.prop("disabled", false);


                                    // クリア
                                    let textareas = document.getElementsByTagName("textarea");
                                    for (let i = 0; i < textareas.length; i++) {
                                        textareas[i].value = "";
                                    }
                                    let logs = document.getElementById("log-area");
                                    logs.innerHTML = "";
                                    resultFlg = null;
                                }
                            })
                            .fail(function(respdata, stscode, resp) {
                                alert(getMessage('MOSJA00014', false));
                                if(stscode === "error") {
                                    window.location.href = "/oase_web/top/logout";
                                }
                            });
                        } else{
                            evethis.value = previous;
                            $this.prop("disabled", false);
                            resultFlg = null;
                            return false;
                        }
                    }
                })
                .fail(function(respdata, stscode, resp){
                    alert(getMessage('MOSJA00014', false));
                    if(stscode === "error") {
                        window.location.href = "/oase_web/top/logout";
                    }
                });
            }

            if ( runFlg !== 1 ){

                let choice = false;
                // 初回ルール種別選択時にはメッセージを出さない
                if(previous){
                    choice = confirm(getMessage("MOSJA12130", false));
                } else {
                    choice = true;
                }

                if(choice === true) {

                    previous = this.value;

                    let data_details = {
                        "rule_manage_id"      : ruleManageId,
                        "csrfmiddlewaretoken" : token
                    };

                    $.ajax({
                        type : "POST",
                        url  : "rule/get_record",
                        data : data_details,
                        dataType : "json",
                    })
                    .done(function(respdata) {

                        if(respdata.err_flg !== 0){
                            alert(respdata.msg);
                            window.location.href = 'rule';
                        } else {

                            // ルール種別名取得しておく
                            ruleTypeName = $('[id=selTgtRuleType] option:selected').text();

                            // polling停止
                            clearPollingTimer();

                            // 2回目以降の変更は直前のデータを消す
                            let beforeObj = document.getElementById(trTgtId);
                            if(beforeObj !== null) {
                                beforeObj.parentNode.removeChild(beforeObj);
                            }

                            rulemanage_id      = ruleManageId;
                            rule_type_id       = respdata["data"]["rule_type_id"];
                            rule_table_name    = respdata["data"]["rule_table_name"];
                            operationstatus_id = respdata["data"]["operation_status_id"];
                            rule_ids_stg       = respdata["data"]["rule_ids_stg"];

                            $("#rule_type_name").text(respdata["data"]["rule_type_name"]);
                            $("#rule_file_name").text(respdata["data"]["filename"]);
                            $("#operation_status").text(respdata["data"]["operation_status_str"]);
                            $("#system_status").text(respdata["data"]["system_status_str"]);
                            $("#last_update_user").text(respdata["data"]["last_update_user_name"]);
                            $("#last_update_timestamp").text(respdata["data"]["last_update_timestamp"]);

                            $("#btnLogDownload").prop("disabled", true);
                            $("#btnPseudoCall").prop("disabled", false);
                            $("#btnClear").prop("disabled", false);
                            $("#logClear").prop("disabled", false);
                            $("#btnFileClear").prop("disabled", false);
                            $("#btnExcelDownload").prop("disabled", false);
                            $("#btnFileSelect").prop("disabled", false);

                            resultFlg = null;

                            // 前回のテストリクエスト設定をクリア
                            $('table[id^="ruleType_"]').hide();

                            $('#ruleType_' + respdata["data"]["rule_type_id"]).show();
                            $this.prop("disabled", false);

                            // クリア
                            let textareas = document.getElementsByTagName("textarea");
                            for (let i = 0; i < textareas.length; i++) {
                                textareas[i].value = "";
                            }
                            let logs = document.getElementById("log-area");
                            logs.innerHTML = "";
                        }
                    })
                    .fail(function(respdata, stscode, resp) {
                        alert(getMessage('MOSJA00014', false));
                        if(stscode === "error") {
                            window.location.href = "/oase_web/top/logout";
                        }
                    });
                } else {
                    this.value = previous;
                    $this.prop("disabled", false);
                    return false;
                }
            }
        });

}


//////////////////////////////////////////////////////////////////////
//  テストリクエストボタン押下制御
//////////////////////////////////////////////////////////////////////
function chkEnableTestRequestBtn() {

    // ステージング件数が0件時は、何も処理をしない
    if(!($('#selTgtRuleType').length)) {
        return;
    }

    // テストリクエスト可能なルールが存在しない場合は、何も処理をしない
    if($('#selTgtRuleType').children('option').length <= 0) {
        return;
    }

    // ボタンを活性化する
    let html = '';

    html += '<a href="#modal_staging_pseudo" class="modalOpen" onClick="modalTabOpen(\'#modal-tab\');stopAutoReload();">';
    html += '<button class="tooltip test oase-button" title="' + getMessage('MOSJA12157', false) + '">';
    html += '<em class="owf owf-check"></em><span>' + getMessage('MOSJA12035', false) + '</span>';
    html += '</button>';
    html += '</a>';

    $('#liTestRequest').html(html);
}


//////////////////////////////////////////////////////////////////////
//  アップロードファイル選択時処理
//////////////////////////////////////////////////////////////////////
function selectFile(obj) {

    let objectValue = obj.value;
    let selectFile = getMessage("MOSJA12073", false);
    if(objectValue) {
        let fileExtension = objectValue.substring(objectValue.lastIndexOf(".")+1, objectValue.length);
        let validArray = ["xls", "xlsx"];
        if($.inArray(fileExtension, validArray) === -1) {
            let alertMsg = getMessage("MOSJA12131", false).replace("{}",fileExtension) + getMessage("MOSJA12132", false).replace("{0}",validArray[0]).replace("{1}",validArray[1]) + getMessage("MOSJA12133", false)
            alert(alertMsg);
            obj.value = "";
            $("#filename").text(selectFile);
            $("#btnUpload").prop("disabled", true);
        }
        else{
            $("#filename").text(obj.files[0].name);
            $("#btnUpload").prop("disabled", false);
        }
    }
    else {
        $("#filename").text(selectFile);
        $("#btnUpload").prop("disabled", true);
    }
}


//////////////////////////////////////////////////////////////////////
//  選択ファイルのアップロード処理
//////////////////////////////////////////////////////////////////////
function uploadRuleFile() {
    $("#btnUpload").prop("disabled", true);

    if(confirm(getMessage("MOSJA12134", false))) {
        let strURL = $("#frmUpload").attr("action");
        let data = new FormData($("#frmUpload").get(0));

        $.ajax({
            url    : strURL,
            method : "POST",
            data   : data,
            processData : false,
            contentType : false
        })
        .done(function(respdata) {
            let resp = JSON.parse(respdata);
            alert(resp.msg);
            location.href = "rule";
        })
        .fail(function(respdata, stscode, resp) {
            alert(getMessage("MOSJA03007", false));
            if(stscode === "error") {
                window.location.href = "/oase_web/top/logout";
            }
        });

        $("#btnUpload").prop("disabled", false);
        return;
    }
    else {
        $("#btnUpload").prop("disabled", false);
        return;
    }
}

////////////////////////////////////////////////
//  インターバル処理
////////////////////////////////////////////////
function pollingRuleStatus(ruleID, traceID) {
    let token = null;
    if(document.cookie && document.cookie !== "") {
        let cookies = document.cookie.split(";");
        for(let i = 0; i < cookies.length; i++) {
            let c = jQuery.trim(cookies[i]);
            if(c.substring(0, "csrftoken".length + 1) === "csrftoken=") {
                token = decodeURIComponent(c.substring("csrftoken".length + 1));
                break;
            }
        }
    }

    if(token) {
        let data = {
            "csrfmiddlewaretoken" : token
        };

        $.ajax({
            type : "POST",
            url  : "rule/polling/" + ruleID + "/" + traceID + "/",
            data : data,
            dataType : "json",
        })
        .done(function(respdata){pollingSuccess(respdata, ruleID, traceID);})
        .fail(function(respdata, stscode, resp){
            if(stscode === "error") {
                window.location.href = "/oase_web/top/logout";
            }
        });
    }
}

function pollingRuleStatus_Bulk(ruleID, a_traceID, recept, filename) {

    let token = null;
    if(document.cookie && document.cookie !== "") {
        let cookies = document.cookie.split(";");
        for(let i = 0; i < cookies.length; i++) {
            let c = jQuery.trim(cookies[i]);
            if(c.substring(0, "csrftoken".length + 1) === "csrftoken=") {
                token = decodeURIComponent(c.substring("csrftoken".length + 1));
                break;
            }
        }
    }

    let a_dicTraceList = new Array();
    for(let i = 0; i < a_traceID.length; i++) {
        dicTrace = {};
        dicTrace["id"]  = a_traceID[i].id;
        dicTrace["row"] = a_traceID[i].row;

        a_dicTraceList.push(dicTrace);
    }

    let strTraceInfo = JSON.stringify(a_dicTraceList);

    if(token) {
        let data = {
            "csrfmiddlewaretoken" : token,
            "recept"    : recept,
            "filename"  : filename,
            "trace_ids" : strTraceInfo
        };

        $.ajax({
            type : "POST",
            url  : "rule/polling/bulk/" + ruleID + "/",
            data : data,
            dataType : "json",
        })
        .done(function(respdata){pollingSuccess_Bulk(respdata, ruleID);})
        .fail(function(respdata, stscode, resp){
            if(stscode === "error") {
                window.location.href = "/oase_web/top/logout";
            }
        });
    }
}


////////////////////////////////////////////////
//  ポーリング結果正常
function pollingSuccess(respdata, ruleID, traceID) {

    let resp = JSON.parse(JSON.stringify(respdata));
    let selectFile = getMessage("MOSJA12073", false);
    $("#log-area").val(resp.msg);

    // 処理中の場合はポーリング継続
    if(parseInt(resp.is_finish) === 0) {
        startPollingTimer(ruleID, resp.trace_id);
    }
    // ステージング検証が正常終了の場合は、フラグ立てる
    else if(parseInt(resp.is_finish) < 0) {
        $("#btnLogDownload").prop("disabled", false);
        $("#btnClear").prop("disabled", false);
        $("#btnFileClear").prop("disabled", false);
        $("#btnFileSelect").prop("disabled", false);
        $("#btnPseudoCall").prop("disabled", false);
        document.getElementById("fileRequest").value = "";
        $("#testreqFilename").text(selectFile);
        $("#logClear").prop("disabled", false);
        resultFlg = 1;
    }
    // ステージング検証が異常終了の場合は、テストリクエスト実行ボタンを有効化
    else if(parseInt(resp.is_finish) > 0) {
        $("#btnLogDownload").prop("disabled", false);
        $("#btnClear").prop("disabled", false);
        $("#btnFileClear").prop("disabled", false);
        $("#btnFileSelect").prop("disabled", false);
        $("#btnPseudoCall").prop("disabled", false);
        document.getElementById("fileRequest").value = "";
        $("#testreqFilename").text(selectFile);
        $("#logClear").prop("disabled", false);

        resultFlg = null;
    }
}

function pollingSuccess_Bulk(respdata, ruleID) {

    let resp = JSON.parse(JSON.stringify(respdata));
    $("#log-area").val(resp.msg);

    // 処理中の場合はポーリング継続
    if(parseInt(resp.is_finish) === 0) {
        startPollingTimer_Bulk(ruleID, resp.trace, resp.recept, resp.filename);
    }
    // ステージング検証が正常終了の場合は、フラグ立てる
    else if(parseInt(resp.is_finish) < 0) {
        $("#btnFileSelect").prop("disabled", false);
        $("#btnLogDownload").prop("disabled", false);
        $("#btnClear").prop("disabled", false);
        $("#btnFileClear").prop("disabled", false);
        $("#btnPseudoCall").prop("disabled", false);
        $("#logClear").prop("disabled", false);
        resultFlg = 1;
    }
    // ステージング検証が異常終了の場合は、テストリクエスト実行ボタンを有効化
    else if(parseInt(resp.is_finish) > 0) {
        $("#btnFileSelect").prop("disabled", false);
        $("#btnLogDownload").prop("disabled", false);
        $("#btnPseudoCall").prop("disabled", false);
        $("#btnClear").prop("disabled", false);
        $("#btnFileClear").prop("disabled", false);
        $("#logClear").prop("disabled", false);
        resultFlg = null;
    }
}


////////////////////////////////////////////////
//  ポーリング結果異常
function pollingError(respdata, ruleID, traceID) {
    let resp = JSON.parse(JSON.stringify(respdata));
    $("#log-area").val(resp.msg);

    if(parseInt(resp.is_finish) > 0) {
        $("#btnLogDownload").prop("disabled", false);
        $("#btnPseudoCall").prop("disabled", false);
        $("#btnClear").prop("disabled", false);
        $("#btnFileClear").prop("disabled", false);
        $("#btnFileSelect").prop("disabled", false);
        document.getElementById("fileRequest").value = "";
        $("#testreqFilename").text(getMessage("MOSJA12073", false));

    }
}

////////////////////////////////////////////////
//  ポーリングタイマー開始
function startPollingTimer(ruleID, traceID) {

    let POLLING_INTERVAL = 5; // 秒

    clearPollingTimer()
    timerID = setTimeout(function(){
        pollingRuleStatus(ruleID, traceID);
    }, POLLING_INTERVAL * 1000);
}

function startPollingTimer_Bulk(ruleID, a_traceID, recept, filename) {

    let POLLING_INTERVAL = 10; // 秒

    clearPollingTimer()
    timerID = setTimeout(function(){
        pollingRuleStatus_Bulk(ruleID, a_traceID, recept, filename);
    }, POLLING_INTERVAL * 1000);
}

////////////////////////////////////////////////
//  ポーリングタイマー停止
function clearPollingTimer() {
    if(timerID !== null) {
        clearTimeout(timerID);
    }
}

//////////////////////////////////////////////////////////////////////
//  テストリクエスト結果ダウンロード処理
//////////////////////////////////////////////////////////////////////
//  ダウンロードボタン押下
function downloadLogAction() {

    $("#btnLogDownload").prop("disabled", true);

    let content = $("#log-area").val();
    content = content.replace(/(<br>|<br \/>)/gi, '\n');
    content = content.replace(/&nbsp;/g, ' ');

    let blob = new Blob([ content ], { "type" : "text/plain" });
    let dl = document.getElementById('btnLogDownload');
    let eventDate = dl.dataset.eventDate.replace(/-|\s|:/g, '');

    let fileName = ruleTypeName + '_' + eventDate + '.txt';

    // ブラウザ判定用
    let agent = window.navigator.userAgent.toLowerCase();
    let aTag;
    if (window.navigator.msSaveBlob) {
        // IE
        window.navigator.msSaveBlob(blob, fileName);
    } else if (agent.indexOf('firefox') !== -1) {
        // Firefox
        aTag = document.createElement("a");
        aTag.download = fileName;
        aTag.href = window.URL.createObjectURL(blob);
        document.body.appendChild(aTag);
        aTag.click();
        document.body.removeChild(aTag);
    } else if ((agent.indexOf('chrome') !== -1) && (agent.indexOf('edge') === -1)  && (agent.indexOf('opr') === -1)) {
        // Chrome
        aTag = document.createElement("a");
        aTag.download = fileName;
        aTag.href = window.URL.createObjectURL(blob);
        aTag.click();
    }

    $("#btnLogDownload").prop("disabled", false);
}


//////////////////////////////////////////////////////////////////////
//  Excelダウンロード処理(ステージング)
//////////////////////////////////////////////////////////////////////
//  ダウンロードボタン押下
function downloadStagingAction(pk) {

    $("#btnStagingDl" + pk).prop("disabled", true);

    let url = 'rule/download/' + pk + '/';

    downloadAjaxExcel("#btnStagingDl" + pk, url);

}


//////////////////////////////////////////////////////////////////////
//  Excelダウンロード処理(プロダクション)
//////////////////////////////////////////////////////////////////////
//  ダウンロードボタン押下
function downloadProAction(pk) {

    $("#btnProDl" + pk).prop("disabled", true);

    let url = 'rule/download/' + pk + '/';

    downloadAjaxExcel("#btnProDl" + pk, url);

}


//////////////////////////////////////////////////////////////////////
//  Excelダウンロード処理(プロダクション適用履歴)
//////////////////////////////////////////////////////////////////////
//  ダウンロードボタン押下
function downloadRuleHistoryAction(pk) {

    $("#btnDl" + pk).prop("disabled", true);

    let url = 'rule/download/' + pk + '/';

    downloadAjaxExcel("#btnDl" + pk, url);

}


//////////////////////////////////////////////////////////////////////
//  テストリクエストExcelダウンロード処理
//////////////////////////////////////////////////////////////////////
//  ダウンロードボタン押下
function downloadExcel() {

    $("#btnExcelDownload").prop("disabled", true);

    let rulemanageid    = rulemanage_id;
    let testrequestflag = rulemanageid + '_testrequest';
    let url = 'rule/download/' + testrequestflag + '/';

    downloadAjaxExcel("#btnExcelDownload", url);

}


//////////////////////////////////////////////////////////////////////
//  アップロード選択時処理(テストリクエストExcel)
//////////////////////////////////////////////////////////////////////
function selectTestreqFile(obj) {

    let objectValue = obj.value;
    if(objectValue) {
        let fileExtension = objectValue.substring(objectValue.lastIndexOf(".")+1, objectValue.length);
        let validArray = ["xls", "xlsx"];
        if($.inArray(fileExtension, validArray) === -1) {
            let alertMsg = getMessage("MOSJA12131", false).replace("{}",fileExtension) + getMessage("MOSJA12132", false).replace("{0}",validArray[0]).replace("{1}",validArray[1]) + getMessage("MOSJA12133", false)
            alert(alertMsg);

            obj.value = "";
            $("#btnPseudoCall").prop("disabled", true);
            document.getElementById("fileRequest").value = "";
            $("#testreqFilename").text(getMessage("MOSJA12073", false));
        }
        else{
            $("#testreqFilename").text(obj.files[0].name);
            $("#btnPseudoCall").prop("disabled", false);
        }
    }
}

//////////////////////////////////////////////////////////////////////
//  テストリクエスト実行時処理
//////////////////////////////////////////////////////////////////////
//  実行ボタン押下
function pseudoCall() {

  //ページ移動の注意を無視
  //beforeunloadThroughFlag = true;

  $("#btnPseudoCall").prop("disabled", true);
  $("#btnLogDownload").prop("disabled", false);

  //単発テスト or 一括リクエスト判定
  if($('#single-test').hasClass('open')){

    if(!confirm(getMessage("MOSJA12135", false))) {
        $("#btnPseudoCall").prop("disabled", false);
        return;
    }

    let ruleID = rulemanage_id;

    $("#btnClear").prop("disabled", true);
    document.getElementById("fileRequest").value = "";
    $("#testreqFilename").text(getMessage("MOSJA12073", false));

    let material = document.getElementById("log-area");
    material.style.display = "block";

    let ruleTypeId = rule_type_id;
    let ruleTable  = rule_table_name;
    let url = "rule/pseudo_request/" + rule_type_id;

    let inputElements = $('#ruleType_' + ruleTypeId).find('.condition-input');
    let inputDataArray = []
    inputElements.each(function(i, elem) {
        inputDataArray.push(elem.value);
    });

    // 暫定対応：イベント発生日時の扱いどうするの？
    let eventToTime = $('#ruleType_' + ruleTypeId).find('input')[0].value;

    let dl = document.getElementById("btnLogDownload");
    dl.dataset.eventDate = eventToTime;

    let eventData = {"ruletable": ruleTable, "requesttype": "2", "eventdatetime": eventToTime, "eventinfo": inputDataArray};
    let data = {
        "json_str" : JSON.stringify(eventData),
        "csrfmiddlewaretoken" : document.getElementsByName("csrfmiddlewaretoken")[0].value
    };

    $.ajax({
        type : "POST",
        url  : url,
        data : data,
        dataType : "json",
    })
    .done(function(respdata){ pseudoSuccess(respdata, ruleID); })
    .fail(function(respdata, stscode, resp){
        if(stscode === "error") {
            window.location.href = "/oase_web/top/logout";
        }
        $("#btnPseudoCall").prop("disabled", false);
        $("#btnClear").prop("disabled", false);
    });

    return false;

  //  選択ファイルのアップロードとテストリクエスト処理
  }else if($('#bulk-tests').hasClass('open')){

    if(confirm(getMessage("MOSJA12136", false))) {

        let ruleID = rulemanage_id;

        let dl = document.getElementById("btnLogDownload");
        let dt = new Date();
        let year = dt.getFullYear();
        let month = ("0"+(dt.getMonth()+1)).slice(-2);
        let day = ("0"+(dt.getDate())).slice(-2);
        let hours = ("0"+(dt.getHours())).slice(-2);
        let minutes = ("0"+(dt.getMinutes())).slice(-2);
        let seconds = ("0"+(dt.getSeconds())).slice(-2);

        dl.dataset.eventDate = getMessage("MOSJA12137", false) + String(year) + String(month) + String(day) + String(hours) + String(minutes) + String(seconds);

        $("#btnFileSelect").prop("disabled", true);
        $("#btnFileClear").prop("disabled", false);

        let textareas = document.getElementsByTagName("textarea");
        for (let i = 0; i < textareas.length; i++) {
            textareas[i].value = "";
        }


        let material = document.getElementById("log-area");
        material.style.display = "block";

        let strURL = $("#frmBulkPseudoCall").attr("action");
        strURL = strURL + "/" + rule_type_id + '/';
        let data = new FormData($("#frmBulkPseudoCall").get(0));

        $.ajax({
            url    : strURL,
            method : "POST",
            data   : data,
            processData : false,
            contentType : false
        })
        .done(function(respdata){
            let resp = JSON.parse(respdata);
            alert(resp.msg);
            $("#log-area").val(resp.log_msg);
            if(resp.result === 'OK'){
                pseudoSuccess_Bulk(respdata, ruleID);
            } else {
                $("#btnFileSelect").prop("disabled", false);
                $("#btnExcelDownload").prop("disabled", false);
                $("#btnPseudoCall").prop("disabled", false);
                $("#btnFileClear").prop("disabled", false);
            }
        })
        .fail(function(respdata, stscode, resp){
            if(stscode === "error") {
                window.location.href = "/oase_web/top/logout";
            }
        });
    }else{
        $("#btnPseudoCall").prop("disabled", false);
        return;
    }
  }else{
    console.log("else");
  }
}
//////////////////////////////////////////////////////////////////////
//  テストリクエストクリア処理
//////////////////////////////////////////////////////////////////////
//  クリアボタン押下

//labelクリア
function ConditionClear() {
    $("#btnLogDownload").prop("disabled", true);
    let conditions = document.getElementsByClassName("condition-input");
    for (let i = 0; i < conditions.length; i++) {
        conditions[i].value = "";
    }
}
//ログクリア
function LogClear(){
    $("#btnLogDownload").prop("disabled", true);
    $("#log-area").val("");
}

//選択中のファイルクリア
function FileClear(){
    $("#fileRequest").val("");
    $("#testreqFilename").text(getMessage("MOSJA12073", false));
}


////////////////////////////////////////////////
//  実行結果正常
function pseudoSuccess(respdata, ruleID) {

    let resp = JSON.parse(JSON.stringify(respdata));
    alert(resp.msg);
    $("#log-area").val(resp.log_msg);
    // リクエストが正常に受け付けられた場合は、ポーリングタイマーをセット
    if(parseInt(resp.err_flg) === 0) {
        startPollingTimer(ruleID, resp.trace_id);
    }
    // リクエストが異常の場合は、テストリクエスト実行ボタンを有効化
    else {
        $("#btnPseudoCall").prop("disabled", false);
        $("#btnClear").prop("disabled", false);
    }
}

function pseudoSuccess_Bulk(respdata, ruleID) {

    let resp = JSON.parse(respdata);

    $("#log-area").val(resp.log_msg);
    // リクエストが正常に受け付けられた場合は、ポーリングタイマーをセット
    if(resp.result === 'OK') {
        startPollingTimer_Bulk(ruleID, resp.trace, resp.recept, resp.filename);
    }
    // リクエストが異常の場合は、テストリクエスト実行ボタンを有効化
    else {
        $("#btnExcelDownload").prop("disabled", false);
        $("#btnPseudoCall").prop("disabled", false);
        $("#btnFileClear").prop("disabled", false);
        $("#btnFileSelect").prop("disabled", false);
    }
}


////////////////////////////////////////////////
//  擬似呼画面閉じる処理
function pseudoDialogClosing() {

    $("#btnClose").prop("disabled", true);
    $("#btnCloseIcon").prop("disabled", true);

    // ポーリングタイマー停止
    clearPollingTimer()

    let token = null;
    if(document.cookie && document.cookie !== "") {
        let cookies = document.cookie.split(";");
        for(let i = 0; i < cookies.length; i++) {
            let c = jQuery.trim(cookies[i]);
            if(c.substring(0, "csrftoken".length + 1) === "csrftoken=") {
                token = decodeURIComponent(c.substring("csrftoken".length + 1));
                break;
            }
        }
    }

    let rule_manage_id = rulemanage_id;
    let operation_status_id = operationstatus_id;
    let stg_flag            = $.inArray(rule_type_id, rule_ids_stg);
    let data;

    if(operation_status_id < 24 && resultFlg === 1 && 0 <= stg_flag ) {
        if(confirm(getMessage("MOSJA12129", false))) {
            data = {
                "status" : "24", // 検証完了
                "rule_manage_id" : rule_manage_id,
                "csrfmiddlewaretoken" : token
            };

        } else {
            data = {
                "status" : "22", // 検証実施中
                "rule_manage_id" : rule_manage_id,
                "csrfmiddlewaretoken" : token
            };
        }

        $.ajax({
            type : "POST",
            url  : "rule/change_status",
            data : data,
            dataType : "json",
        })
        .done(function(respdata){
            alert(respdata.msg);
            if(respdata.err_flg === 0) {
                beforeunloadThroughFlag = true;
                window.location.href = 'rule';
            }
        })
        .fail(function(respdata, stscode, resp){
            alert(getMessage('MOSJA00014', false));
            if(stscode === "error") {
                window.location.href = "/oase_web/top/logout";
            }
        })
        .always(function(respdata) {
            $("#btnClose").prop("disabled", false);
            $("#btnCloseIcon").prop("disabled", false);
        });
    }else{
        beforeunloadThroughFlag = true;
        window.location.href = 'rule';
    }


}

//////////////////////////////////////////////////////////////////////
//  過去を含め表示ボタンの実装
//  件数更新
//////////////////////////////////////////////////////////////////////
$(function() {
    // 件数更新
    tableRowCount('staging');
    tableRowCount('production');

    // 過去を含め表示ボタン押下時(ステージング)
    $(document).on('click', '#show-sta-history', function(){
        $(".s_history").toggleClass("display-none");
        $(".s_history").toggleClass("filter_hide_list");
        pagingTable(1, 'staging');
    });
    // 過去を含め表示ボタン押下時(プロダクション)
    $(document).on('click', '#show-pro-history', function(){
        $(".tr-switchback").toggleClass("display-none");
        $(".tr-switchback").toggleClass("filter-hide-list");
        pagingTable(1, 'production');
    });
});



//////////////////////////////////////////////////////////////////////
//  適用ルールの切り戻し画面 表示情報取得
//////////////////////////////////////////////////////////////////////
function switchbackData(ruleID) {
    let tableArray = [];
    tableArray.push($('#switchback'+ruleID+' .rule-type div').text());
    tableArray.push($('#switchback'+ruleID+' .rule-file div').text());
    tableArray.push($('#switchback'+ruleID+' .last-update-user div').text());
    tableArray.push($('#switchback'+ruleID+' .last-modified time').text());

    $('#modal-switch-back td div').each(function(index, element){
        $(element).text(tableArray[index]);
    })

    //rule_manage_idを子画面に渡す
    $('#btnSwitchBack').data('rule_manage_id', ruleID);
}
//////////////////////////////////////////////////////////////////////
//  適用ルールの切り戻し処理
//////////////////////////////////////////////////////////////////////
function switchBack() {
    let ruleID = $('#btnSwitchBack').data('rule_manage_id');

    $("#btnSwitchBack").prop("disabled", true);

    let confirmMsg = getMessage("MOSJA12138", false).replace("{}", $('#switchback'+ruleID+' .rule-type div').text());

    if(!confirm(confirmMsg)) {
        $("#btnSwitchBack").prop("disabled", false);
        return;
    }

    let strURL = "rule/switchback/" + ruleID + "/";
    let data   = {
        "csrfmiddlewaretoken" : document.getElementsByName("csrfmiddlewaretoken")[0].value
    };

    $.ajax({
        type : "POST",
        url  : strURL,
        data : data,
        dataType : "json",
    })
    .done(function(respdata) {
        let resp = JSON.parse(JSON.stringify(respdata));
        alert(resp.msg);

        if(resp.result === "OK") {
            location.href = "rule";
        }
    })
    .fail(function(respdata, stscode, resp) {
        alert(getMessage('MOSJA00014', false));
        if(stscode === "error") {
            window.location.href = "/oase_web/top/logout";
        }
    })
    .always(function(respdata) {
        $("#btnSwitchBack").prop("disabled", false);
    });
}


//////////////////////////////////////////////////////////////////////
//  ルール適用処理
//////////////////////////////////////////////////////////////////////
function applyRule(ruleID, requestTypeID) {
    $("#pro_teki_" + ruleID.toString()).prop("disabled", true);

    if(!confirm(getMessage("MOSJA12139",false))) {
        $("#pro_teki_" + ruleID.toString()).prop("disabled", false);
        return;
    }

    $("#btnStagingDl" + ruleID.toString()).prop("disabled", true);

    stopAutoReload();

    let strURL = "rule/apply/" + ruleID.toString() + "/" + requestTypeID.toString() + "/";
    let data   = {
        "csrfmiddlewaretoken" : document.getElementsByName("csrfmiddlewaretoken")[0].value
    };

    $.ajax({
        type : "GET",
        url  : strURL,
        dataType : "json",
    })
    .done(function(respdata) {
        let resp = JSON.parse(JSON.stringify(respdata));
        alert(resp.msg);

        if(resp.result === "OK") {
            location.href = "rule";
        }
    })
    .fail(function(respdata, stscode, resp) {
        alert(getMessage('MOSJA00014', false));
        if(stscode === "error") {
            window.location.href = "/oase_web/top/logout";
        }
    })
    .always(function(respdata) {
        $("#pro_teki_" + ruleID.toString()).prop("disabled", false);
        $("#btnStagingDl" + ruleID.toString()).prop("disabled", false);
    });

    startAutoReload();
}

/* ************************************************** *
 *
 * リロード関連メソッド
 *
 * ************************************************** */

// 自動リロード用変数
let autoReload = null;
let autoReloadStaging = null;
let autoReloadProduction = null;

//////////////////////////////////////////////////////////////////////
// リロードが必要な作業ステータスがあるか調べる
// [引数]
// selector : ルール画面のテーブルのレコードのセレクタ
// ステージング適用、プロダクション適用共通
//////////////////////////////////////////////////////////////////////
function needReload(selector){
    let statusId = -1;
    let result = false;
    let reloadTriggerIds = [1, 3, 11, 13, 21, 31];// Defs.RULE_SYS_STATUS参照

    $(selector).each(function(i,e){
        $(this).find('td').each(function(j, el){
            // 作業ステータス(ルールステータスid)を取得
            if(j===4){
                statusId = $(this).data('rulestatusid');
                // 更新すべきidが含まれていたらresultを更新してループを抜ける
                if(reloadTriggerIds.indexOf(statusId) >= 0){
                    result = true;
                    return false;
                }
            }
        });
        // 1つでも見つかっていればループを抜ける
        if(result){
            return false;
        }
    });
    return result;
}

//////////////////////////////////////////////////////////////////////
// リロード共通部分
//
// requesttypeId: production === 1, staging === 2
//////////////////////////////////////////////////////////////////////
function Reload(requesttypeId, selectorList){

    let type = "staging";
    let type2 = "#show-stg-history > .tr-switchback";

    if (requesttypeId === 1){
        type = "production";
        type2 ="#show-pro-history > .tr-switchback";
    }else{
        requesttypeId = 2;
    }

    let data = {
        "filters": {},
        "csrfmiddlewaretoken": document.getElementsByName("csrfmiddlewaretoken")[0].value
    }

    $.ajax({
        type : "POST",
        url  : 'rule/data/' + type,
        data : data,
    })
    .done(function(respdata, stscode, res) {
        let out_html = $($.parseHTML(respdata));

        // selectorで指定されたDOMを、out_htmlのDOMで上書きする。
        $.each(selectorList, function (index, value){
            console.log(value);
            $(value).html(out_html.filter(value)[0].innerHTML);
        });

        $(type2).addClass("display-none");
        $(type2).addClass("filter-hide-list");

        // 「過去を含め表示」をリセットする
        $('#show-sta-history, #show-pro-history').removeClass('on');

        //ページングリセット
        pagingTable(requesttypeId, type);

        // 読み込みマークを消す
        $('.oase-table-load').removeClass('loading');

        // ステージングの場合、イベントを再定義
        if(requesttypeId === 2){
            onloadStaging();
            chkEnableTestRequestBtn();
        }
    })
    .fail(function(respdata, stscode, res) {
        alert(getMessage("MOSJA12140",false));
        window.location.href = "/oase_web/top/logout";
    })
    .always(function(respdata) {
        // staging/production どちらのリロードフラグも立っていなければ停止
        if(!needReload('#stagingTable tr') && !needReload('#productionTable tr')){
            stopAutoReload();
        }
    });
}


//////////////////////////////////////////////////////////////////////
// 作業ステータスに応じてリロードする　ステージング用
//////////////////////////////////////////////////////////////////////
function ReloadStaging(selector){

    // リロードフラグが立っていなければ何もしない
    if(!needReload(selector)){
        return;
    }

    let selectors = ["#stagingTableOuter", "#modal-tab"];
    Reload(2, selectors);
}

//////////////////////////////////////////////////////////////////////
// 作業ステータスに応じてリロードする プロダクション用
//////////////////////////////////////////////////////////////////////
function ReloadProduction(selector){

    // リロードフラグが立っていなければ何もしない
    if(!needReload(selector)){
        return;
    }

    let selectors = ["#productionTableOuter"];
    Reload(1, selectors);
}


//////////////////////////////////////////////////////////////////////
// 自動リロード機能を停止させる
//////////////////////////////////////////////////////////////////////
function stopAutoReload(){
    clearInterval(autoReloadStaging);
    clearInterval(autoReloadProduction);
    footerPollingTimerStop();
}

//////////////////////////////////////////////////////////////////////
// 自動リロード機能を発火させる
//////////////////////////////////////////////////////////////////////
function startAutoReload(){
    // 5000ミリ秒毎にリロード
    let interval = 5000;
    let stagingTableSelector = '#stagingTable tr';
    let productionTableSelector = '#productionTable tr';
    autoReloadStaging = setInterval(function(){ReloadStaging(stagingTableSelector)}, interval);
    autoReloadProduction = setInterval(function(){ReloadProduction(productionTableSelector)}, interval);

    // staging/production どちらかのリロードフラグが立っていればアニメーション実行
    if(needReload(stagingTableSelector) || needReload(productionTableSelector)){
        footerPollingTimerStart();
    }
}

//　読み込み時に自動リロード機能発火
$(function() {
    // タイマーバー表示
    footerPollingTimer();
    // clickイベント追加(スタートorストップ)
    $('.oase-polling-switch .oase-button').on('click', function(){
        if ( $( this ).is('.on') ) {
            stopAutoReload();
        } else {
            startAutoReload();
        }
    });
    startAutoReload();
});

//////////////////////////////////////////////////////////////////////
// ページング
//////////////////////////////////////////////////////////////////////
function pagingTable(pageNum, mode) {

  let oaseTable = $('#' + mode + 'Table');
  let oaseFooter = $('#' + mode + 'Footer');
  let pagingPageCount = oaseTable.find('tbody tr:not([class*="filter-hide-"])').length;
  let pagingEnd = oaseFooter.find('.rowShowNum').val();

  // select.val()が取得できない場合がある
  if ( pagingEnd === undefined ) pagingEnd = 50;

  // 最大ページ数
  let pagingMax = Math.ceil( pagingPageCount / pagingEnd );

  // 表示されたページと最大ページ数の比較
  if ( pageNum >= pagingMax ) {
    pageNum = pagingMax;
    oaseFooter.find('.pagingNext').prop('disabled', true );
  } else {
    oaseFooter.find('.pagingNext').prop('disabled', false );
  }

  // 表示ページが１以下の場合
  if ( pageNum <= 1 ) {
    pageNum = 1;
    oaseFooter.find('.pagingPrev').prop('disabled', true );
  } else {
    oaseFooter.find('.pagingPrev').prop('disabled', false );
  }

  let pagingStart = ( pageNum - 1 ) * pagingEnd - 1;

  oaseFooter.find('.pagingNow').val( pageNum );
  oaseFooter.find('.pagingMax').text( pagingMax );

  if ( pagingStart === -1 ) {
      oaseTable.find('tr:not([class*="filter-hide-"]):lt(' + pagingEnd + ')').removeClass('paging-hide');
  } else {
      oaseTable.find('tr:not([class*="filter-hide-"]):gt(' + pagingStart + '):lt(' + pagingEnd + ')').removeClass('paging-hide');
  }

  tableRowCount(mode);

}

//////////////////////////////////////////////////////////////////////
// 行数カウントの更新
//////////////////////////////////////////////////////////////////////
function tableRowCount(mode) {
  $('#' + mode + 'Table').each( function(){
    let rowCount = $('#' + mode + 'Table').find('tbody tr:not([class*="filter-hide-"])').length;
    $('#' + mode + 'Footer').find('.rowCount').text( rowCount );
  });
}
