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
//  データオブジェクト取得
////////////////////////////////////////////////
var dd_rule_type_data_obj_dict = {};
$(function() {

    dd_rule_type_data_obj_dict = $.parseJSON($('#dd_rule_type_data_obj_dict').val());

    //テストリクエストのルール変更時の処理
    $('#add-datadog-rule-select')
        .focus(function(){
            previous = this.value;
        })
        .change(function(){
            var $this = $(this);
            $this.prop("disabled", true);

            // 前回エラーメッセージ削除
            clearErrorMsg($this.closest('td'));

            // this.value = 選択されたルール種別名に対応するルールID
            refleshRowsDatadog(this.value, 'add');

            $this.prop("disabled", false);
        });

    $('#edit-datadog-rule-select')
        .focus(function(){
            previous = this.value;
        })
        .change(function(){
            var $this   = $(this);
            $this.prop("disabled", true);

            // 前回エラーメッセージ削除
            clearErrorMsg($this.closest('td'));

            // this.value = 選択されたルール種別名に対応するルールID
            refleshRowsDatadog(this.value, 'edit');

            $this.prop("disabled", false);
        });
});

function monitoringDatadogAddModalClose(selector1, selector2) {
    if(monitoringModalClose(selector1, selector2)) {
        refleshRowsDatadog(null, 'add');
    }
}

function monitoringDatadogAddModalChange(selector1, selector2, selector3) {
    if(monitoringModalChange(selector1, selector2, selector3)) {
        refleshRowsDatadog(null, 'add');
    }
}


///////////////////////////////////////////////////////////////////
//
// プルダウンの作成
// mode: 'edit' or 'add'
// matchinfo: 選択されている値
//
///////////////////////////////////////////////////////////////////
function setpullDownDatadog(mode, matchinfo){

    var items = $('#datadog-items').data('datadogitems');
    var datadogAry = items.split(',');

    var option;

    for ( let value of datadogAry ){

        var str = '<option value=' + value + '>' + value + '</option>';

        if ( mode === 'edit' && matchinfo === value ){
            str = '<option value=' + value + ' selected >' + value + '</option>';
        }

        if (!option){
            option = str
        }
        else{
            option += str
        }
    }

    return option;
}


///////////////////////////////////////////////////////////////////
//
// 選択されたルール種別に応じて突合情報の内容を変更
// rule_type_id: ルール種別ID
// mode: 'edit' or 'add'
//
///////////////////////////////////////////////////////////////////
function refleshRowsDatadog(rule_type_id, mode){

    var noneSelector = '#' + mode + '-rule-none-datadog';
    var detailSelector = '#' + mode + '-rule-detail-datadog';
    var detailSelector2 = '#' + mode + '-monitor-detail-datadog';
    var tableIdStr = mode + 'Datadogtable';

    $(noneSelector).hide();
    $(noneSelector).children().remove();
    $(detailSelector).show();
    $(detailSelector2).show();

    // すべての子要素を削除
    var table = document.getElementById(tableIdStr);
    var clone = table.cloneNode( false );
    table.parentNode.replaceChild(clone, table);

    if(!rule_type_id) {
        $(noneSelector).show();
        $(noneSelector).append('<input type="hidden" value="" required>');
        $(detailSelector).hide();
        $(detailSelector2).hide();
    } else {
        // 条件名変換用
        var do_dict = dd_rule_type_data_obj_dict[rule_type_id]['data_obj'];

        //var option = setpullDownDatadog('add','');

        // editの場合の保存済みDatadog項目反映用
        var matchlist = {};
        if(mode == 'edit') {
            var trId  = '#' + $('#viewDatadogDetail').attr('data-recordid');
            matchlist = $(trId).data('matchlist');
        }

        // id = '#' +mode + 'Datadogtable' の下に行追加
        for (key in do_dict){
            // 行追加
            var tr = clone.insertRow( -1 );
            var value = key in matchlist ? matchlist[key] : "";

            // HTML文作成
            var th = '<th id="data-object-id-' + key + '"><div class="cell-inner">' + do_dict[key] + '<sup>*</sup><span class="help tooltip" title="' + getMessage("MOSJA26437", false) + '"><em class="owf owf-question"></em></span></div></th>';
            var td = '<td><div class="cell-inner"><input id="' + mode + '-datadog-' + key + '" data-maxlength="128" data-type="text" class="validation-input" type="text" value="' + value + '" ></div></td>';

            tr.innerHTML = th + td;
        }
    }
}


////////////////////////////////////////////////
//  Datadogの詳細画面にデータをセット
////////////////////////////////////////////////
function setInfoInDatadogDetailView(idName) {

    var trId         = '#' + idName;

    // 権限によるボタン制御
    $('#btnToEditModalDatadog, #btnDelDatadog').prop('disabled', false);
    var editable = $(trId).data('editable');
    if(!editable) {
        $('#btnToEditModalDatadog, #btnDelDatadog').prop('disabled', true);
    }

    var name         = $(trId).data('name');
    var uri          = $(trId).data('uri');
    var proxy        = $(trId).data('proxy');
    var evtime       = $(trId).data('evtime');
    var instance     = $(trId).data('instance');
    var ruletypeid   = $(trId).data('ruletypeid');
    var ruletypename = $(trId).data('ruletypename');
    var matchlist    = $(trId).data('matchlist');
    var updateuser   = $(trId).data('updateuser');
    var timestamp    = $(trId).data('timestamp');

    $('#viewDatadogDetail').attr('data-recordid', idName);
    $('#viewDatadogName').text(name);
    $('#viewDatadogUri').text(uri);
    $('#viewDatadogProxy').text(proxy);
    $('#viewDatadogEventTime').text(evtime);
    $('#viewDatadogInstance').text(instance);
    $('#viewDatadogRuletype').text(ruletypename);
    $('#viewDatadogUpdateuser').text(updateuser);
    $('#viewDatadogTimestamp').text(timestamp);

    setMatchlistDatadog('viewDatadogtable', matchlist, ruletypeid);

    // ルール種別が削除されていた場合エラーを表示
    if(!ruletypeid || ruletypeid <=0) {
        var errorHTML = '<ul class="error-list" name="sub_error">';
        errorHTML += '<li><em class="owf owf-cross"></em>' + getMessage("MOSJA26411", false) + '<span class="tooltip help" data-tooltip="' + getMessage("MOSJA26412", false) + '"><em class="owf owf-question"></em></span></li>';
        errorHTML += '</ul>';
        $('#viewDatadogRuletype').addClass('error');
        $('#viewDatadogRuletype').html( errorHTML );
    }
}


////////////////////////////////////////////////
//  Datadogの編集画面にデータをセット
////////////////////////////////////////////////
function setInfoInDatadogEditView() {

    beforeunloadThroughFlag = false;

    var trId           = '#' + $('#viewDatadogDetail').attr('data-recordid');
    var name           = $(trId).data('name');
    var uri            = $(trId).data('uri');
    var apikey         = $(trId).data('apikey');
    var applicationkey = $(trId).data('applicationkey');
    var proxy          = $(trId).data('proxy');
    var evtime         = $(trId).data('evtime');
    var instance       = $(trId).data('instance');
    var ruletypeid     = $(trId).data('ruletypeid');
    var matchlist      = $(trId).data('matchlist');
    var updateuser     = $(trId).data('updateuser');
    var timestamp      = $(trId).data('timestamp');

    $('#editDatadogName').val(name);
    $('#editDatadogUri').val(uri);
    $('#editDatadogApiKey').val(apikey);
    $('#editDatadogAppKey').val(applicationkey);
    $('#editDatadogProxy').val(proxy);
    $('#editDatadogEventTime').val(evtime);
    $('#editDatadogInstance').val(instance);
    $('#edit-datadog-rule-select').val(ruletypeid);
    if(!ruletypeid || ruletypeid <= 0) {
        renderErrorMsg($('#edit-datadog-rule-select'), getMessage("MOSJA26427", false));
    }
    $('#editDatadogUpdateuser').text(updateuser);
    $('#editDatadogTimestamp').text(timestamp);

    setMatchlistDatadog('editDatadogtable', matchlist, ruletypeid);
}


////////////////////////////////////////////////
//  詳細画面の突合情報欄にテーブルを追加
//  id: 追加対象の詳細画面のテーブルID(view or edit)
////////////////////////////////////////////////
function setMatchlistDatadog(id, matchlist, ruletypeid) {

    // すべての子要素を削除
    var table = document.getElementById(id);
    var clone = table.cloneNode( false );
    table.parentNode.replaceChild(clone, table);

    if(ruletypeid > 0) {
        dataobj = dd_rule_type_data_obj_dict[ruletypeid]['data_obj'];
        Object.keys(dataobj).forEach(function(key) {
            var row = clone.insertRow( -1 );
            var value = key in matchlist ? matchlist[key] : "";
            // HTML文作成
            var th = '<th id="data-object-id-' + key + '"><div class="cell-inner">' + dataobj[key] + '</div></th>';
            var td = '<td></td>';

            // 編集ならinputを有効化
            if (id == 'editDatadogtable'){
                th = '<th id="data-object-id-' + key + '"><div class="cell-inner">' + dataobj[key] + '<sup>*</sup><span class="help tooltip" title="' + getMessage("MOSJA26437", false) + '"><em class="owf owf-question"></em></span></div></th>';
                td = '<td><div class="cell-inner"><input id="edit-datadog-' + key + '" data-maxlength="128" data-type="text" class="validation-input" type="text" value="' + value + '" ></div></td>';
            }

            row.innerHTML = th + td;

            // 詳細表示ならtdにvalueを追加
            if (id == 'viewDatadogtable'){
                row.lastElementChild.append(value);
           }
        });
    }
}


////////////////////////////////////////////////
//  データの保存用 画面上のデータ収集
//  idInfo: データ収集先ID辞書
////////////////////////////////////////////////
function setDatadogInfo(idInfo){

    var adapterInfo = {};

    // 入力データを取得してセット
    adapterInfo["adapter_id"] = 4;
    adapterInfo["datadog_disp_name"] = $(idInfo['datadog_disp_name']).val();
    adapterInfo["uri"] = $(idInfo['uri']).val();
    adapterInfo["api_key"] = $(idInfo['api_key']).val();
    adapterInfo["application_key"] = $(idInfo['application_key']).val();
    adapterInfo["proxy"] = $(idInfo['proxy']).val();
    adapterInfo["evtime"] = $(idInfo['evtime']).val();
    adapterInfo["instance"] = $(idInfo['instance']).val();
    adapterInfo["rule_type_id"] = $(idInfo['rule_type_id']).val();

    var conditionalData = {}; // 条件名、Datadog項目を辞書形式で格納
    $(idInfo['match_list']).each(function(index, element){
        var id          = $(element).find('th').attr("id"); // 条件名
        //var value       = $(element).find('select').val(); // 条件式
        var value       = $(element).find('input').val(); // 条件式

        id = id.replace("data-object-id-", "");
        conditionalData[id] = value;
    });

    adapterInfo['match_list'] = conditionalData;

    return adapterInfo;
}


////////////////////////////////////////////////
//  データの保存(新規)
////////////////////////////////////////////////
function createDatadogAdapterinfo() {

    var btnId = "#btnAddDatadog";

    // ボタン制御 連打防止
    $(btnId).prop("disabled", true);

    // 確認メッセージを表示
    if(!confirm(getMessage("MOSJA00002", false))){
        $(btnId).prop("disabled", false);
        return;
    }

    // データ収集
    var idInfo = getIdInfoDatadog('add');
    var postdata = setDatadogInfo(idInfo);
    postdata['datadog_adapter_id'] = "0";

    // バリデーションチェック
    var objTBody = document.getElementById("tbodyDatadogAdapterInfo");
    validateResult = validateDatadogAdapterData(objTBody, postdata);

    //エラーメッセージを表示
    if(validateResult['errorFlag']){
        renderCreateDatadogErrorMsg(validateResult['errorMsg']);
        return;
    }

    createSomeAdapterInfo(postdata, btnId, renderCreateDatadogErrorMsg);
}


////////////////////////////////////////////////
//  データの保存(更新)
////////////////////////////////////////////////
function updateDatadogAdapterInfo() {

    var btnId = "#btnEditDatadog";

    // ボタン制御 連打防止
    $(btnId).prop("disabled", true);

    // 確認メッセージを表示
    if(!confirm(getMessage("MOSJA26438", false))){
        $(btnId).prop("disabled", false);
        return;
    }

    // データ収集
    var idInfo = getIdInfoDatadog('edit');
    var postdata = setDatadogInfo(idInfo);
    postdata["datadog_adapter_id"] = $('#viewDatadogDetail').attr('data-recordid').replace("datadogadapter-", "");

    // バリデーションチェック
    var objTBody = document.getElementById("tbodyDatadogAdapterInfo");
    validateResult = validateDatadogAdapterData(objTBody, postdata);

    //エラーメッセージを表示
    if(validateResult['errorFlag']){
        renderUpdateDatadogErrorMsg(validateResult['errorMsg']);
        return;
    }

    updateSomeAdapterInfo(postdata, btnId, renderUpdateDatadogErrorMsg);
}


////////////////////////////////////////////////
//  データの保存(削除)
////////////////////////////////////////////////
function deleteDatadogAdapterInfo() {

    var btnId = "#btnDelDatadog";
    $(btnId).prop("disabled", true);

    // 削除レコードの存在確認後に確認メッセージを表示する
    var confirmMsg = getMessage("MOSJA26439", false);
    if(!confirm(confirmMsg)){
        $(btnId).prop("disabled", false);
        return;
    }

    // データ収集
    var strId = $('#viewDatadogDetail').attr('data-recordid');
    var recordId = strId.replace("datadogadapter-", "");
    var postdata = {
            "adapter_id" : 4,
            "record_id" : Number(recordId),
        };

    deleteSomeAdapterInfo(postdata, btnId);
}


////////////////////////////////////////////////
//  バリデーション
////////////////////////////////////////////////
var regexNum = new RegExp(/^[0-9]+$/);
function validateDatadogAdapterData(objTBody, adapterInfo){

    var strID = "";
    var DatadogName     = adapterInfo["datadog_disp_name"];
    var uri             = adapterInfo["uri"];
    var api_key         = adapterInfo["api_key"];
    var application_key = adapterInfo["application_key"];
    var ruletypeid      = adapterInfo["rule_type_id"];
    var proxy           = adapterInfo["proxy"];
    var matchlist       = adapterInfo['match_list'];

    var errorFlag = false;
    var errorMsg = {};
    var chk_DatadogName = {};
    var chk_uri = {};
    var chk_ruletypeid = {};

    // 画面に表示されているDatadogアダプタの名称・ホスト名をすべて保持
    var selector = "";
    if(objTBody != null){
        for(var i = 0; i < objTBody.children.length; i++){
            strID = objTBody.children[i].id.replace("datadogadapter-", "");
            selector = "#" + objTBody.children[i].id;
            // idが取得できた場合
            if(selector != "#") {
                chk_DatadogName[strID]    = $(selector).data('name');
                chk_uri[strID]            = $(selector).data('uri');
                chk_ruletypeid[strID]     = $(selector).data('ruletypeid');
            }
        }
    }

    strID = adapterInfo["datadog_adapter_id"];
    chk_DatadogName[strID] = DatadogName;
    chk_uri[strID] = uri;

    // 検査開始
    errorMsg['datadog_disp_name'] = "";
    errorMsg['uri'] = "";
    errorMsg['proxy'] = "";
    errorMsg['rule_type_id'] = "";

    // adapternameの重複チェック
    var match_line = Object.keys(chk_DatadogName).filter(function(key) {
        if(strID != key && chk_DatadogName[key] == DatadogName){
            return chk_DatadogName[key] === DatadogName;
        }
    });

    if(match_line.length > 0){
        errorMsg["datadog_disp_name"] += getMessage("MOSJA26433", false) + "(MOSJA26433)" + "\n";
        errorFlag = true;
    }

     // rule_type_idの未入力チェック
    if (!ruletypeid || ruletypeid <=0 ) {
        errorMsg["rule_type_id"] += getMessage("MOSJA26427", false) + "(MOSJA26427)" + "\n";
        errorFlag = true;
    }

     // rule_type_idの重複チェック
    match_line = Object.keys(chk_ruletypeid).filter(function(key) {
        if(strID != key && chk_ruletypeid[key] == ruletypeid){
            return chk_ruletypeid[key] == ruletypeid;
        }
    });

    if(match_line.length > 0){
        errorMsg["rule_type_id"] += getMessage("MOSJA26434", false) + "(MOSJA26434)" + "\n";
        errorFlag = true;
    }

    var result = {
        'errorFlag': errorFlag,
        'errorMsg' : errorMsg,
    };

    return result;
}


////////////////////////////////////////////////
// htmlのId情報を連想配列で取得
// mode: 'edit' or 'add'
////////////////////////////////////////////////
function getIdInfoDatadog(mode){

    modalwindowid = "#" + $('#datadog_v1_modal_add_id').val();
    if(mode == 'edit') {
        modalwindowid = "#modal-datadog-edit";
    }

    var idInfo = {
        'modalwindow'     : modalwindowid,
        'datadog_disp_name': "#" + mode + "DatadogName",
        'uri'              : "#" + mode + "DatadogUri",
        'api_key'          : "#" + mode + "DatadogApiKey",
        'application_key'  : "#" + mode + "DatadogAppKey",
        'evtime'           : "#" + mode + "DatadogEventTime",
        'instance'         : "#" + mode + "DatadogInstance",
        'rule_type_id'     : "#" + mode + "-datadog-rule-select",
        'proxy'            : "#" + mode + "DatadogProxy",
        'match_list'       : "#" + mode + "Datadogtable tr",
    };

    return idInfo;
}

var renderCreateDatadogErrorMsg = function(errorMsg) {
    renderDatadogErrorMsg(errorMsg, 'add');
}

var renderUpdateDatadogErrorMsg = function(errorMsg) {
    renderDatadogErrorMsg(errorMsg, 'edit');
}

var renderDatadogErrorMsg = function(errorMsg, mode) {
    alert(getMessage("MOSJA26012", false));

    idInfo = getIdInfoDatadog(mode);

    clearErrorMsg(idInfo['modalwindow']); // 前回エラーを削除

    renderErrorMsg(idInfo['datadog_disp_name'], errorMsg['datadog_disp_name']);
    renderErrorMsg(idInfo['uri'], errorMsg['uri']);
    renderErrorMsg(idInfo['api_key'], errorMsg['api_key']);
    renderErrorMsg(idInfo['application_key'], errorMsg['application_key']);
    renderErrorMsg(idInfo['proxy'], errorMsg['proxy']);
    renderErrorMsg(idInfo['rule_type_id'], errorMsg['rule_type_id']);
    renderErrorMsg(idInfo['evtime'], errorMsg['evtime']);
    renderErrorMsg(idInfo['instance'], errorMsg['instance']);

    //--------------------------------------------
    // Datadog項目へのエラー表示
    //--------------------------------------------
    $(idInfo['match_list']).each(function(index, element){
        var id = $(element).find('input').attr("id");
        var error_key = id.replace(mode + "-","");
        renderErrorMsg( '#' + id, errorMsg[error_key]);
    });
}

