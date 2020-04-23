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

// グローバル
let id = "";

////////////////////////////////////////////////
//  編集モードへ移行する
//  tbodyID(string) : tbodyのid
//  formId(string)  : postするformのId
////////////////////////////////////////////////
function changeModeToEdit(tbodyId, formId) {

    $("#btnEdt").prop("disabled", true);

    var tblData = document.getElementById(tbodyId);
    var editForm = document.getElementById(formId);
    var pkList = {};
    pkList["pk"] = {};
    pkList["pk"]["LIST"] = new Array();

    if(tblData){
        for (var i = 0, r = tblData.rows.length; i < r; i++) {
            pkList["pk"]["LIST"].push(tblData.rows[i].id);
        }
    }
    // csrf_token の次にあるinput要素のvalueにデータを挿入
    editForm.children[1].value = JSON.stringify(pkList);

    editForm.submit();

}

////////////////////////////////////////////////
//  リストへ行追加（編集モード）
////////////////////////////////////////////////
function addList(tbodyID, dummyID){

    var objTBody  = document.getElementById(tbodyID);
    var objDummy  = document.getElementById(dummyID);
    var objTrAdd  = objDummy.cloneNode(true);
    var objTr     = objTBody.rows[objTBody.rows.length - 1];
    var iRowCount = objTBody.rows.length;
    var strID     = "";

    iRowCount++;
    strID = "New" + iRowCount.toString();
    objTrAdd.style.display = "";
    objTrAdd.id = strID;

    //  リスト追加
    objTBody.insertBefore(objTrAdd, objDummy);
    objTr = objTBody.rows[objTBody.rows.length - 2];
    objTr.classList.remove('filter-hide-list');
    objTr.classList.remove('paging-hide');
    objTr.classList.add('added-row');

    var sugFunc = 'setUserGroup("hid' + strID + '");';

    //  更新メニューを追加
    objTr.cells[1].children[0].children[0].id = "selModify" + strID;
    objTr.cells[2].children[0].children[0].id = "ita_driver_name" + strID;
    objTr.cells[3].children[0].children[0].id = "menu_id" + strID;
    objTr.cells[4].children[0].children[0].id = "parameter_name" + strID;
    objTr.cells[5].children[0].children[0].id = "order" + strID;
    objTr.cells[6].children[0].children[0].id = "conditional_name" + strID;
    objTr.cells[7].children[0].children[0].id = "extraction_method1" + strID;
    objTr.cells[8].children[0].children[0].id = "extraction_method2" + strID;

    tableRowCount();
}

////////////////////////////////////////////////
//  キャンセル処理
////////////////////////////////////////////////
function cancel(version){
    $("#btnCan").prop("disabled", true);
    var choice = true;

    // 変更が有れば確認する
    if($('.change-value').length)
    {
        choice = confirm(getMessage("MOSJA27006", false));
    }

    // trueならキャンセルする
    if(choice) {
        beforeunloadThroughFlag = true;
        window.location.href = '/oase_web/system/paramsheet/' + String( version );
        return true;
    }
    $("#btnCan").prop("disabled", false);
}

////////////////////////////////////////////////
//  リセット処理
////////////////////////////////////////////////
function reset() {
    // 変更が無ければメッセージは表示しない
    if($('.change-value').length == 0)
    {
        return true;
    }

    $("#btnRes").prop("disabled", true);

    if(confirm(getMessage("MOSJA27325", false)))
    {
        beforeunloadThroughFlag = true;
        $('#toResetForm').submit();
    }
    $("#btnRes").prop("disabled", false);
}

////////////////////////////////////////////////
//  保存前処理
////////////////////////////////////////////////
function submitAnalysisData(tbodyID) {
    var objTBody = document.getElementById(tbodyID);
    var strID = "";
    var obj = null;
    var ItaDriverID = null;

    var dataList = new Array();
    var strOpe = "";
    var strMatchID = "";
    var strItaDriverID = "";
    var strMenuID = "";
    var strParameterName = "";
    var strOrder = "";
    var strConditionalName = "";
    var strExtractionMethod1 = "";
    var strExtractionMethod2 = "";

    var errorFlag = false;
    var errItaDriverID = {};
    var errMenuID = {};
    var errParameterName = {};
    var errOrder =  {};
    var errConditionalName = {};
    var errExtractionMethod1 = {};
    var errExtractionMethod2 = {};

    $("#btnUpd").prop("disabled", true);

    // 保存確認メッセージ
    if(!confirm(getMessage("MOSJA00002", false))){
        $("#btnUpd").prop("disabled", false);
        return;
    }

    // 前回エラー表記削除
    $('.error').removeClass('error');
    $('.error-list').remove();

    // バリデーションクリア
    var tableTrArray = objTBody.getElementsByTagName("tr");
    Array.prototype.forEach.call(tableTrArray, function(objTr) {
        if(objTr.id != null && objTr.id != "" && objTr.id != "parameter_dummy") {
            objErrorCell = objTr.getElementsByClassName("error-icon-area")[0];

            objTr.classList.remove("error-row");
            var removeChildren = objErrorCell.getElementsByClassName("error-exists");
            Array.prototype.forEach.call(removeChildren, function(objChild) {
                objErrorCell.removeChild(objChild);
            });
        }
    });

    for(var i = 0; i<objTBody.rows.length; i++) {
        strID = objTBody.rows[i].id;
        if(!strID || strID == "parameter_dummy") {
            continue;
        }

        obj = document.getElementById("selModify" + strID);
        strOpe = obj.options[obj.selectedIndex].value;

        // 更新しない場合除外
        if(parseInt(strOpe) <= 0) {
            continue;
        }

        strMatchID = "0";
        if(strID.indexOf("New") != 0) {
            strMatchID = strID;
        }

        if(strOpe == 1) {
            ItaDriverID = document.getElementById("ita_driver_name" + strID);
            strItaDriverID = ItaDriverID.children["0"].value;
        } else {
            strItaDriverID = document.getElementById("ita_driver_name" + strID).value;
        }
        if(strOpe == 1) {
            MenuID = document.getElementById("menu_id" + strID);
            strMenuID = MenuID.children["0"].value;
        } else {
            strMenuID = document.getElementById("menu_id" + strID).value;
        }
        strParameterName = document.getElementById("parameter_name" + strID).value;
        strOrder = document.getElementById("order" + strID).value;
        strConditionalName = document.getElementById("conditional_name" + strID).value;
        strExtractionMethod1 = document.getElementById("extraction_method1" + strID).value;
        strExtractionMethod2 = document.getElementById("extraction_method2" + strID).value;

        errItaDriverID[strID] = '';
        errMenuID[strID] = '';
        errParameterName[strID] = '';
        errOrder[strID] =  '';
        errConditionalName[strID] = '';
        errExtractionMethod1[strID] = '';
        errExtractionMethod2[strID] = '';

        if(strItaDriverID == "0") {
            errItaDriverID[strID] += getMessage("MOSJA27315", true) + "\n";
        }
        if(strMenuID == "") {
            errMenuID[strID] += getMessage("MOSJA27317", true) + "\n";
        }
        if(strParameterName == "") {
            errParameterName[strID] += getMessage("MOSJA27318", true) + "\n";
        }
        if(strOrder == "") {
            errOrder[strID] += getMessage("MOSJA27320", true) + "\n";
        }
        if(strConditionalName == "") {
            errConditionalName[strID] += getMessage("MOSJA27321", true) + "\n";
        }
        if(strParameterName.length > 256) {
            errParameterName[strID] += getMessage("MOSJA27319", true) + "\n";
        }
        if(strConditionalName.length > 32) {
            errConditionalName[strID] += getMessage("MOSJA27322", true) + "\n";
        }
        if(strExtractionMethod1.length > 512) {
            errExtractionMethod1[strID] += getMessage("MOSJA27323", true) + "\n";
        }
        if(strExtractionMethod2.length > 512) {
            errExtractionMethod2[strID] += getMessage("MOSJA27324", true) + "\n";
        }

        if(errItaDriverID[strID] != ""){
            errorFlag = true;
        }else if(errMenuID[strID] != ""){
            errorFlag = true;
        }else if(errParameterName[strID] != ""){
            errorFlag = true;
        }else if(errOrder[strID] != ""){
            errorFlag = true;
        }else if(errConditionalName[strID] != ""){
            errorFlag = true;
        }else if(errExtractionMethod1[strID] != ""){
            errorFlag = true;
        }else if(errExtractionMethod2[strID] != ""){
            errorFlag = true;
        }

        dataInfo = {};
        dataInfo["ope"] = strOpe;
        dataInfo["match_id"] = strMatchID;
        dataInfo["ita_driver_id"] = strItaDriverID;
        dataInfo["menu_id"] = strMenuID;
        dataInfo["parameter_name"] = strParameterName;
        dataInfo["order"] = strOrder;
        dataInfo["conditional_name"] = strConditionalName;
        dataInfo["extraction_method1"] = strExtractionMethod1;
        dataInfo["extraction_method2"] = strExtractionMethod2;
        dataInfo["row_id"] = strID;
        dataList.push(dataInfo);
    }

    if(errorFlag) {
        alert(getMessage("MOSJA27326", true));

        Object.keys(errItaDriverID).forEach(function(rowId) {
            errorStr = errItaDriverID[rowId];

            if(!errorStr || errorStr.length == 0) {
                return true;
            }

            // 今回エラーを表記
            $errInput = $('#' + 'ita_driver_name' + rowId);
            $errInput.parents('th, td').addClass('error');
            var errorHTML = '<ul class="error-list">';
            errorHTML += '<li><em class="owf owf-cross"></em>' + getMessage("MOSJA00026", false) + '<span class="tooltip help" title="' + errorStr + '"><em class="owf owf-question"></em></span></li>';
            errorHTML += '</ul>';
            $errInput.after( errorHTML );
        });

        Object.keys(errMenuID).forEach(function(rowId) {
            errorStr = errMenuID[rowId];

            if(!errorStr || errorStr.length == 0) {
                return true;
            }

            // 今回エラーを表記
            $errInput = $('#' + 'menu_id' + rowId);
            $errInput.parents('th, td').addClass('error');
            var errorHTML = '<ul class="error-list">';
            errorHTML += '<li><em class="owf owf-cross"></em>' + getMessage("MOSJA00026", false) + '<span class="tooltip help" title="' + errorStr + '"><em class="owf owf-question"></em></span></li>';
            errorHTML += '</ul>';
            $errInput.after( errorHTML );
        });

        Object.keys(errParameterName).forEach(function(rowId) {
            errorStr = errParameterName[rowId];

            if(!errorStr || errorStr.length == 0) {
                return true;
            }

            // 今回エラーを表記
            $errInput = $('#' + 'parameter_name' + rowId);
            $errInput.parents('th, td').addClass('error');
            var errorHTML = '<ul class="error-list">';
            errorHTML += '<li><em class="owf owf-cross"></em>' + getMessage("MOSJA00026", false) + '<span class="tooltip help" title="' + errorStr + '"><em class="owf owf-question"></em></span></li>';
            errorHTML += '</ul>';
            $errInput.after( errorHTML );
        });

        Object.keys(errOrder).forEach(function(rowId) {
            errorStr = errOrder[rowId];

            if(!errorStr || errorStr.length == 0) {
                return true;
            }

            // 今回エラーを表記
            $errInput = $('#' + 'order' + rowId);
            $errInput.parents('th, td').addClass('error');
            var errorHTML = '<ul class="error-list">';
            errorHTML += '<li><em class="owf owf-cross"></em>' + getMessage("MOSJA00026", false) + '<span class="tooltip help" title="' + errorStr + '"><em class="owf owf-question"></em></span></li>';
            errorHTML += '</ul>';
            $errInput.after( errorHTML );
        });

        Object.keys(errConditionalName).forEach(function(rowId) {
            errorStr = errConditionalName[rowId];

            if(!errorStr || errorStr.length == 0) {
                return true;
            }

            // 今回エラーを表記
            $errInput = $('#' + 'conditional_name' + rowId);
            $errInput.parents('th, td').addClass('error');
            var errorHTML = '<ul class="error-list">';
            errorHTML += '<li><em class="owf owf-cross"></em>' + getMessage("MOSJA00026", false) + '<span class="tooltip help" title="' + errorStr + '"><em class="owf owf-question"></em></span></li>';
            errorHTML += '</ul>';
            $errInput.after( errorHTML );
        });

        Object.keys(errExtractionMethod1).forEach(function(rowId) {
            errorStr = errExtractionMethod1[rowId];

            if(!errorStr || errorStr.length == 0) {
                return true;
            }

            // 今回エラーを表記
            $errInput = $('#' + 'extraction_method1' + rowId);
            $errInput.parents('th, td').addClass('error');
            var errorHTML = '<ul class="error-list">';
            errorHTML += '<li><em class="owf owf-cross"></em>' + getMessage("MOSJA00026", false) + '<span class="tooltip help" title="' + errorStr + '"><em class="owf owf-question"></em></span></li>';
            errorHTML += '</ul>';
            $errInput.after( errorHTML );
        });

        Object.keys(errExtractionMethod2).forEach(function(rowId) {
            errorStr = errExtractionMethod2[rowId];

            if(!errorStr || errorStr.length == 0) {
                return true;
            }

            // 今回エラーを表記
            $errInput = $('#' + 'extraction_method2' + rowId);
            $errInput.parents('th, td').addClass('error');
            var errorHTML = '<ul class="error-list">';
            errorHTML += '<li><em class="owf owf-cross"></em>' + getMessage("MOSJA00026", false) + '<span class="tooltip help" title="' + errorStr + '"><em class="owf owf-question"></em></span></li>';
            errorHTML += '</ul>';
            $errInput.after( errorHTML );
        });

        tableThFixedReset();
        tableThFixed();

        return;
    }

    if(dataList.length == 0) {
        alert(getMessage("MOSJA27327", true));
        return;
    }

    var jstr = JSON.stringify({"json_str":dataList});
    document.getElementById("hidJsonStr").value = jstr;

    var objForm = document.getElementById("formAnalysisData");
    objForm.submit();
}

function submitAction(url) {

    // 前回エラー表記削除
    $('.error').removeClass('error');
    $('.error-list').remove();

    $.ajax({
        type : "POST",
        url  : url,
        data : $("#formAnalysisData").serialize(),
        dataType: "json",
    })
    .done(function(response_json) {
        if(response_json.status == 'success') {
            alert(getMessage("MOSJA00011", false));
            beforeunloadThroughFlag = true;
            $("#btnUpd").prop("disabled", false);
            location.href = response_json.redirect_url;
        }
        else {
            if(response_json.msg == "")
                alert(getMessage("MOSJA27326", true));
            else
                alert(response_json.msg);

            beforeunloadThroughFlag = true;
            errorMsg = response_json.error_msg

            Object.keys(errorMsg).forEach(function(rowId) {
                errorStr = errorMsg[rowId];
                errItaDriverID = errorStr['ita_driver_id'];
                errMenuID = errorStr['menu_id'];
                errParameterName = errorStr['parameter_name'];
                errOrder = errorStr['order'];
                errConditionalName = errorStr['conditional_name'];
                errExtractionMethod1 = errorStr['extraction_method1'];
                errExtractionMethod2 = errorStr['extraction_method2'];

                if(errItaDriverID && errItaDriverID.length > 0) {
                    // 今回エラーを表記
                    $errInput = $('#' + 'ita_driver_name' + rowId);
                    $errInput.parents('th, td').addClass('error');
                    var errorHTML = '<ul class="error-list" name="sub_error">';
                    errorHTML += '<li><em class="owf owf-cross"></em>' + getMessage("MOSJA00026", false) + '<span class="tooltip help" title="' + errItaDriverID + '"><em class="owf owf-question"></em></span></li>';
                    errorHTML += '</ul>';
                    $errInput.after( errorHTML );
                }

                if(errMenuID && errMenuID.length > 0) {
                    // 今回エラーを表記
                    $errInput = $('#' + 'menu_id' + rowId);
                    $errInput.parents('th, td').addClass('error');
                    var errorHTML = '<ul class="error-list" name="sub_error">';
                    errorHTML += '<li><em class="owf owf-cross"></em>' + getMessage("MOSJA00026", false) + '<span class="tooltip help" title="' + errMenuID + '"><em class="owf owf-question"></em></span></li>';
                    errorHTML += '</ul>';
                    $errInput.after( errorHTML );
                }

                if(errParameterName && errParameterName.length > 0) {
                    // 今回エラーを表記
                    $errInput = $('#' + 'parameter_name' + rowId);
                    $errInput.parents('th, td').addClass('error');
                    var errorHTML = '<ul class="error-list" name="sub_error">';
                    errorHTML += '<li><em class="owf owf-cross"></em>' + getMessage("MOSJA00026", false) + '<span class="tooltip help" title="' + errParameterName + '"><em class="owf owf-question"></em></span></li>';
                    errorHTML += '</ul>';
                    $errInput.after( errorHTML );
                }

                if(errOrder && errOrder.length > 0) {
                    // 今回エラーを表記
                    $errInput = $('#' + 'order' + rowId);
                    $errInput.parents('th, td').addClass('error');
                    var errorHTML = '<ul class="error-list" name="sub_error">';
                    errorHTML += '<li><em class="owf owf-cross"></em>' + getMessage("MOSJA00026", false) + '<span class="tooltip help" title="' + errOrder + '"><em class="owf owf-question"></em></span></li>';
                    errorHTML += '</ul>';
                    $errInput.after( errorHTML );
                }

                if(errConditionalName && errConditionalName.length > 0) {
                    // 今回エラーを表記
                    $errInput = $('#' + 'conditional_name' + rowId);
                    $errInput.parents('th, td').addClass('error');
                    var errorHTML = '<ul class="error-list" name="sub_error">';
                    errorHTML += '<li><em class="owf owf-cross"></em>' + getMessage("MOSJA00026", false) + '<span class="tooltip help" title="' + errConditionalName + '"><em class="owf owf-question"></em></span></li>';
                    errorHTML += '</ul>';
                    $errInput.after( errorHTML );
                }

                if(errExtractionMethod1 && errExtractionMethod1.length > 0) {
                    // 今回エラーを表記
                    $errInput = $('#' + 'extraction_method1' + rowId);
                    $errInput.parents('th, td').addClass('error');
                    var errorHTML = '<ul class="error-list" name="sub_error">';
                    errorHTML += '<li><em class="owf owf-cross"></em>' + getMessage("MOSJA00026", false) + '<span class="tooltip help" title="' + errExtractionMethod1 + '"><em class="owf owf-question"></em></span></li>';
                    errorHTML += '</ul>';
                    $errInput.after( errorHTML );
                }

                if(errExtractionMethod2 && errExtractionMethod2.length > 0) {
                    // 今回エラーを表記
                    $errInput = $('#' + 'extraction_method2' + rowId);
                    $errInput.parents('th, td').addClass('error');
                    var errorHTML = '<ul class="error-list" name="sub_error">';
                    errorHTML += '<li><em class="owf owf-cross"></em>' + getMessage("MOSJA00026", false) + '<span class="tooltip help" title="' + errExtractionMethod2 + '"><em class="owf owf-question"></em></span></li>';
                    errorHTML += '</ul>';
                    $errInput.after( errorHTML );
                }
            });

            tableThFixedReset();
            tableThFixed();
        }
    })
    .fail(function(respdata, stscode, resp) {
        if(stscode == "error") {
            beforeunloadThroughFlag = true;
            window.location.href = "/oase_web/top/logout";
        } else {
            alert(getMessage("MOSJA27328", true) + "\n" + respdata.responseText);
            beforeunloadThroughFlag = true;
        }
    });
}

////////////////////////////////////////////////
//  メニューグループ：メニューのプルダウン処理
////////////////////////////////////////////////
function SelectMenuName(obj) {
    let ita_driver_id = obj.value;

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

    version = document.getElementById("action_version");
    temp = obj.id
    if ( temp == "" ){
        temp = obj.offsetParent.id
    }
    temp = temp.substr(15)
    id = "menu_id" + temp

    parent = document.getElementById(id);

    while(parent.lastChild){
        parent.removeChild(parent.lastChild);
    }

    if(!temp.indexOf('New')){
        div = document.getElementById(id);
        select = document.createElement("select");
        div.appendChild(select);
        div = document.getElementById(id);
        option = document.createElement("option");
        div.children[0].appendChild(option);

    } else {
        select = document.getElementById(id);
        option = document.createElement("option");
        select.appendChild(option);
    }

    let data = {
        "version" : version.innerText,
        "ita_driver_id" : ita_driver_id,
        "csrfmiddlewaretoken" : token
    };

    $.ajax({
        type : "POST",
        url  : "/oase_web/system/paramsheet/select/",
        data : data,
        dataType : "json",
    })
    .done(function(response_json) {
        if(response_json.status == 'success') {

            index = id.substr(7)
            i = 0
            if(!index.indexOf('New')){
                for (let [key, value] of Object.entries(response_json.menu_info)) {
                    div = document.getElementById(id);
                    option = document.createElement("option");
                    div.children[0].appendChild(option);
                    div.children[0][i+1].value = key;
                    div.children[0][i+1].innerText = value;
                    i = i + 1;
                }
            } else {
                for (let [key, value] of Object.entries(response_json.menu_info)) {
                    select = document.getElementById(id);
                    option = document.createElement("option");
                    select.appendChild(option);
                    select.children[i+1].value = key;
                    select.children[i+1].innerText = value;
                    i = i + 1;
                }
            }
        } else {
            if(response_json.msg == ""){
                alert(getMessage("MOSJA27330", true));
            } else {
                alert(response_json.msg);
            }

            window.location.href = "/oase_web/top/logout";
        }
    })
    .fail(function(respdata, stscode, resp) {
        alert(getMessage("MOSJA03007", false));
        if(stscode === "error") {
            window.location.href = "/oase_web/top/logout";
        }
    });
}
