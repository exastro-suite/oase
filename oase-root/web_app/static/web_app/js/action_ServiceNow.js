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

////////////////////////////////////////////////
//  ServiceNowdriverを追加する
////////////////////////////////////////////////
function addServiceNowDriver( driver_id ) {

    var btnId = "#btnAddServiceNow";
    $(btnId).prop("disabled", true);

    var confirmMsg = getMessage("MOSJA27001", false);
    // 確認メッセージを表示
    if(!confirm(confirmMsg)){
        $(btnId).prop("disabled", false);
        return;
    }

    var idInfo = {
        'servicenow_disp_name':'#addServiceNowName',
        'hostname':'#addServiceNowHostname',
        'protocol':'#addServiceNowProtocol',
        'port':'#addServiceNowPort',
        'username':'#addServiceNowUsername',
        'password':'#addServiceNowPass1',
        'proxy':'#addServiceNowProxy',
    }
    var ope ="1";
    var drvInfo = {};

    setServiceNowInfo(drvInfo, idInfo);
    drvInfo["ope"] = ope;
    drvInfo["servicenow_driver_id"] = "0";

    // バリデーションチェック
    var tbody = "tbodyActionInfo" + driver_id;
    var objTBody = document.getElementById(tbody);
    error = validateBeforeSave(objTBody, ope, drvInfo);

    // エラー表示
    if(error['errorFlag']){
        clearErrorMsg();
        renderServiceNowErrorMsg(error['errorMsg'], idInfo, 'add');
        return;
    }
    post(drvInfo, btnId, renderServiceNowErrorMsg, 'add');
}

////////////////////////////////////////////////
// 各レコードのエラーメッセージを調べて
// エラーメッセージがあったらセルの下に表示する 
////////////////////////////////////////////////
var renderServiceNowErrorMsg = function(errorMsg, idInfo, mode)
{
    alert(getMessage("MOSJA23014", false));

    if((typeof idInfo == 'undefined') || (idInfo == null)) {
        idInfo = {
            'servicenow_disp_name' : '#' + mode + 'ServiceNowName',
            'hostname'             : '#' + mode + 'ServiceNowHostname',
            'protocol'             : '#' + mode + 'ServiceNowProtocol',
            'port'                 : '#' + mode + 'ServiceNowPort',
            'username'             : '#' + mode + 'ServiceNowUsername',
            'password'             : '#' + mode + 'ServiceNowPass1',
            'proxy'                : '#' + mode + 'ServiceNowProxy',
        }
    }

    clearErrorMsg();// 前回エラーを削除
    renderErrorMsg(idInfo['servicenow_disp_name'], errorMsg['servicenow_disp_name']);
    renderErrorMsg(idInfo['hostname'], errorMsg['hostname']);
    renderErrorMsg(idInfo['port'], errorMsg['port']);
    renderErrorMsg(idInfo['protocol'], errorMsg['protocol']);
    renderErrorMsg(idInfo['username'], errorMsg['username']);
    renderErrorMsg(idInfo['password'], errorMsg['password']);
    renderErrorMsg(idInfo['proxy'], errorMsg['proxy']);
}

var regexNum = new RegExp(/^[0-9]+$/);
function validateBeforeSave(objTBody, ope, drvInfo) {

    var strID = "";
    var servicenowName = drvInfo["servicenow_disp_name"];
    var hostname = drvInfo["hostname"];
    var protocol = drvInfo["protocol"];
    var port = drvInfo["port"];
    var username = drvInfo["username"];
    var password = drvInfo["password"];
    var proxy = drvInfo["proxy"];
    var errorFlag = false;
    var errorMsg = {};
    var chk_servicenowName = {};
    var chk_host = {};


    // 編集画面に表示されているドライバの名称をすべて保持
    var selector = "";
    if(objTBody != null) {
        for(var i = 0; i < objTBody.children.length; i++){
            strID = objTBody.children[i].id.replace("servicenowdriver-","");
            selector = "#" + objTBody.children[i].id;
            if(selector != "#") {
                chk_servicenowName[strID] = $(selector).data('name');
                chk_host[strID] = $(selector).data('hostname');
            }
        }
    }

    // "更新"なら上書き、"追加"ならリストに追加される
    strID = drvInfo["servicenow_driver_id"];
    chk_servicenowName[strID] = servicenowName;
    chk_host[strID] = hostname;

    // 検査開始
    errorMsg['servicenow_disp_name'] = "";
    errorMsg['hostname'] = "";
    errorMsg['port'] = "";
    errorMsg['username'] = "";
    errorMsg['password'] = "";
    errorMsg['proxy'] = "";

    if(!regexNum.test(port) || 0 > parseInt(port) || parseInt(port) > 65535) {
        errorMsg["port"] += getMessage("MOSJA27409", true) + "\n";
        errorFlag = true;
    }

    // drivernameの重複チェック
    var match_line = Object.keys(chk_servicenowName).filter(function(key) {
        if(strID != key && chk_servicenowName[key] == servicenowName){
            return chk_servicenowName[key] === servicenowName;
        }
    });

    if(match_line.length > 0){
        errorMsg["servicenow_disp_name"] += getMessage("MOSJA27416", true) + "\n";
        errorFlag = true;
    }

    // hostnameの重複チェック
    match_line = Object.keys(chk_host).filter(function(key) {
        if(strID != key && chk_host[key] == hostname){
            return chk_host[key] === hostname;
        }
    });
    if(match_line.length > 0){
        errorMsg["hostname"] += getMessage("MOSEN27418", true) + "\n";
        errorFlag = true;
    }

    result = {
        'errorFlag': errorFlag,
        'errorMsg' : errorMsg,
    }

    return result;
}

////////////////////////////////////////////////
//  詳細画面に表示されたservicenowを編集する
////////////////////////////////////////////////
function updateServiceNowDriver( driver_id ) {

    var btnId ="#btnUpdServiceNow";
    $(btnId).prop("disabled", true);

    var confirmMsg = getMessage("MOSJA27001", false);

    // 確認メッセージを表示
    if(!confirm(confirmMsg)){
        $(btnId).prop("disabled", false);
        return;
    }

    var idInfo = {
        'servicenow_disp_name':'#editServiceNowName',
        'hostname':'#editServiceNowHostname',
        'protocol':'#editServiceNowProtocol',
        'port':'#editServiceNowPort',
        'username':'#editServiceNowUsername',
        'password':'#editServiceNowPass1',
        'proxy':'#editServiceNowProxy',
    }
    var drvInfo = {};
    var ope = "2";

    setServiceNowInfo(drvInfo, idInfo);
    drvInfo["ope"] = ope;
    drvInfo["servicenow_driver_id"] = $('#viewServiceNowDetail').attr('data-recordid').replace("servicenowdriver-", "");

    // バリデーションチェック
    var tbody = "tbodyActionInfo" + driver_id;
    var objTBody = document.getElementById(tbody);
    error = validateBeforeSave(objTBody, ope, drvInfo);

    // エラーメッセージ表示
    if(error['errorFlag']){
        clearErrorMsg();
        renderServiceNowErrorMsg(error['errorMsg'], idInfo, 'edit');
        return;
    }

    post(drvInfo, btnId, renderServiceNowErrorMsg, 'edit');

}

////////////////////////////////////////////////
// servicenow driverを削除する
////////////////////////////////////////////////
function deleteServiceNowDriver() {

    var btnId ="#btnDelServiceNow";
    $(btnId).prop("disabled", true);

    var confirmMsg = getMessage("MOSJA27026", false);

    // 削除レコードの存在確認後に確認メッセージを表示する
    if(!confirm(confirmMsg)){
        $(btnId).prop("disabled", false);
        return;
    }

    var strId = $('#viewServiceNowDetail').attr('data-recordid');
    var servicenowDrvId = strId.replace("servicenowdriver-", "");
    var drvInfo = {
            "ope" : "3",
            "driver_id" : "3",
            "servicenow_driver_id" : servicenowDrvId,
        };
    post(drvInfo, btnId, renderNoError, '');

}

////////////////////////////////////////////////
//  dataを取得して連想配列にセット 
////////////////////////////////////////////////
function setServiceNowInfo(drvInfo, idInfo) {

    // 編集画面から値取得
    var servicenowName = $(idInfo['servicenow_disp_name']).val();
    var hostname = $(idInfo['hostname']).val();
    var protocol = $(idInfo['protocol']).val();
    var port = $(idInfo['port']).val();
    var username = $(idInfo['username']).val();
    var password = $(idInfo['password']).val();
    var proxy = $(idInfo['proxy']).val();

    drvInfo["driver_id"] = "3";
    drvInfo["servicenow_disp_name"] = servicenowName;
    drvInfo["hostname"] = hostname;
    drvInfo["protocol"] = protocol;
    drvInfo["port"] = String(port);
    drvInfo["username"] = username;
    drvInfo["password"] = password;
    drvInfo["proxy"] = proxy;
}

////////////////////////////////////////////////
//  詳細画面にデータをセット
////////////////////////////////////////////////
function setInfoInServiceNowDetailView(idName) {

    var trId = '#' + idName;
    var name = $(trId).data('name');
    var hostname = $(trId).data('hostname');
    var protocol = $(trId).data('protocol');
    var port = $(trId).data('port');
    var username = $(trId).data('username');
    var password = $(trId).data('password');
    var proxy = $(trId).data('proxy');
    var updateuser = $(trId).data('updateuser');
    var timestamp = $(trId).data('timestamp');

    $('#viewServiceNowDetail').attr('data-recordid', idName);
    $('#viewServiceNowName').text(name);
    $('#viewServiceNowHostName').text(hostname);
    $('#viewServiceNowProtocol').text(protocol);
    $('#viewServiceNowPort').text(port);
    $('#viewServiceNowUsername').text(username);
    $('#viewServiceNowProxy').text(proxy);
    $('#viewServiceNowUpdateuser').text(updateuser);
    $('#viewServiceNowTimestamp').text(timestamp);

}

////////////////////////////////////////////////
//  ServiceNowの編集画面にデータをセット
////////////////////////////////////////////////
function setInfoInServiceNowEditView() {

    beforeunloadThroughFlag = false;

    var trId = '#' + $('#viewServiceNowDetail').attr('data-recordid');
    var name = $(trId).data('name');
    var protocol = $(trId).data('protocol');
    var hostname = $(trId).data('hostname');
    var port = $(trId).data('port');
    var username = $(trId).data('username');
    var password = $(trId).data('password');
    var proxy = $(trId).data('proxy');
    var updateuser = $(trId).data('updateuser');
    var timestamp = $(trId).data('timestamp');

    $('#editServiceNowName').val(name);
    $('#editServiceNowProtocol').val(protocol);
    $('#editServiceNowHostname').val(hostname);
    $('#editServiceNowPort').val(port);
    $('#editServiceNowUsername').val(username);
    $('#editServiceNowPass1').val(password);
    $('#editServiceNowProxy').val(proxy);
    $('#editServiceNowUpdateuser').text(updateuser);
    $('#editServiceNowTimestamp').text(timestamp);

}
