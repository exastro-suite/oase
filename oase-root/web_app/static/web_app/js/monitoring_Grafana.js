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
var gra_rule_type_data_obj_dict = {};
$(function() {

    gra_rule_type_data_obj_dict = $.parseJSON($('#gra_rule_type_data_obj_dict').val());

    //テストリクエストのルール変更時の処理
    $('#add-grafana-rule-select')
        .focus(function(){
            previous = this.value;
        })
        .change(function(){
            var $this = $(this);
            $this.prop("disabled", true);

            // 前回エラーメッセージ削除
            clearErrorMsg($this.closest('td'));

            // this.value = 選択されたルール種別名に対応するルールID
            refleshRowsGrafana(this.value, 'add');

            $this.prop("disabled", false);
        });

    $('#edit-grafana-rule-select')
        .focus(function(){
            previous = this.value;
        })
        .change(function(){
            var $this   = $(this);
            $this.prop("disabled", true);

            // 前回エラーメッセージ削除
            clearErrorMsg($this.closest('td'));

            // this.value = 選択されたルール種別名に対応するルールID
            refleshRowsGrafana(this.value, 'edit');

            $this.prop("disabled", false);
        });
});

function monitoringGrafanaAddModalClose(selector1, selector2) {
    if(monitoringModalClose(selector1, selector2)) {
        refleshRowsGrafana(null, 'add');
    }
}

function monitoringGrafanaAddModalChange(selector1, selector2, selector3) {
    if(monitoringModalChange(selector1, selector2, selector3)) {
        refleshRowsGrafana(null, 'add');
    }
}


///////////////////////////////////////////////////////////////////
//
// プルダウンの作成
// mode: 'edit' or 'add'
// matchinfo: 選択されている値
//
///////////////////////////////////////////////////////////////////
function setpullDownGrafana(mode, matchinfo){

    var items = $('#grafana-items').data('garafanaitems');
    var grafanaAry = items.split(',');

    var option;

    for ( let value of grafanaAry ){

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
function refleshRowsGrafana(rule_type_id, mode){

    var noneSelector = '#' + mode + '-rule-none-grafana';
    var detailSelector = '#' + mode + '-rule-detail-grafana';
    var detailSelector2 = '#' + mode + '-monitor-detail-grafana';
    var tableIdStr = mode + 'Grafanatable';

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
        var do_dict = pro_rule_type_data_obj_dict[rule_type_id]['data_obj'];

        //var option = setpullDownGrafana('add','');

        // editの場合の保存済みGrafana項目反映用
        var matchlist = {};
        if(mode == 'edit') {
            var trId  = '#' + $('#viewGrafanaDetail').attr('data-recordid');
            matchlist = $(trId).data('matchlist');
        }

        // id = '#' +mode + 'Grafanatable' の下に行追加
        for (key in do_dict){
            // 行追加
            var tr = clone.insertRow( -1 );
            var value = key in matchlist ? matchlist[key] : "";

            // HTML文作成
            var th = '<th id="data-object-id-' + key + '"><div class="cell-inner">' + do_dict[key] + '<sup>*</sup><span class="help tooltip" title="' + getMessage("MOSJA26317", false) + '"><em class="owf owf-question"></em></span></div></th>';
            var td = '<td><div class="cell-inner"><input id="' + mode + '-grafana-' + key + '" data-maxlength="128" data-type="text" class="validation-input" type="text" value="' + value + '" ></div></td>';

            tr.innerHTML = th + td;
        }
    }
}


////////////////////////////////////////////////
//  Grafanaの詳細画面にデータをセット
////////////////////////////////////////////////
function setInfoInGrafanaDetailView(idName) {

    var trId         = '#' + idName;

    // 権限によるボタン制御
    $('#btnToEditModalGrafana, #btnDelGrafana').prop('disabled', false);
    var editable = $(trId).data('editable');
    if(!editable) {
        $('#btnToEditModalGrafana, #btnDelGrafana').prop('disabled', true);
    }

    var name         = $(trId).data('name');
    var uri          = $(trId).data('uri');
    var username     = $(trId).data('username');
    var evtime       = $(trId).data('evtime');
    var instance     = $(trId).data('instance');
    var ruletypeid   = $(trId).data('ruletypeid');
    var ruletypename = $(trId).data('ruletypename');
    var matchlist    = $(trId).data('matchlist');
    var updateuser   = $(trId).data('updateuser');
    var timestamp    = $(trId).data('timestamp');

    $('#viewGrafanaDetail').attr('data-recordid', idName);
    $('#viewGrafanaName').text(name);
    $('#viewGrafanaUri').text(uri);
    $('#viewGrafanaUsername').text(username);
    $('#viewGrafanaEventTime').text(evtime);
    $('#viewGrafanaInstance').text(instance);
    $('#viewGrafanaRuletype').text(ruletypename);
    $('#viewGrafanaUpdateuser').text(updateuser);
    $('#viewGrafanaTimestamp').text(timestamp);

    setMatchlistGrafana('viewGrafanatable', matchlist, ruletypeid);

    // ルール種別が削除されていた場合エラーを表示
    if(!ruletypeid || ruletypeid <=0) {
        var errorHTML = '<ul class="error-list" name="sub_error">';
        errorHTML += '<li><em class="owf owf-cross"></em>' + getMessage("MOSJA26304", false) + '<span class="tooltip help" data-tooltip="' + getMessage("MOSJA26305", false) + '"><em class="owf owf-question"></em></span></li>';
        errorHTML += '</ul>';
        $('#viewGrafanaRuletype').addClass('error');
        $('#viewGrafanaRuletype').html( errorHTML );
    }
}


////////////////////////////////////////////////
//  Grafanaの編集画面にデータをセット
////////////////////////////////////////////////
function setInfoInGrafanaEditView() {

    beforeunloadThroughFlag = false;

    var trId         = '#' + $('#viewGrafanaDetail').attr('data-recordid');
    var name         = $(trId).data('name');
    var uri          = $(trId).data('uri');
    var username     = $(trId).data('username');
    var password     = $(trId).data('password');
    var evtime       = $(trId).data('evtime');
    var instance     = $(trId).data('instance');
    var ruletypeid   = $(trId).data('ruletypeid');
    var matchlist    = $(trId).data('matchlist');
    var updateuser   = $(trId).data('updateuser');
    var timestamp    = $(trId).data('timestamp');

    $('#editGrafanaName').val(name);
    $('#editGrafanaUri').val(uri);
    $('#editGrafanaUsername').val(username);
    $('#editGrafanaPassword').val(password);
    $('#editGrafanaEventTime').val(evtime);
    $('#editGrafanaInstance').val(instance);
    $('#edit-grafana-rule-select').val(ruletypeid);
    if(!ruletypeid || ruletypeid <= 0) {
        renderErrorMsg($('#edit-grafana-rule-select'), getMessage("MOSJA26323", false));
    }
    $('#editGrafanaUpdateuser').text(updateuser);
    $('#editGrafanaTimestamp').text(timestamp);

    setMatchlistGrafana('editGrafanatable', matchlist, ruletypeid);
}


////////////////////////////////////////////////
//  詳細画面の突合情報欄にテーブルを追加
//  id: 追加対象の詳細画面のテーブルID(view or edit)
////////////////////////////////////////////////
function setMatchlistGrafana(id, matchlist, ruletypeid) {

    // すべての子要素を削除
    var table = document.getElementById(id);
    var clone = table.cloneNode( false );
    table.parentNode.replaceChild(clone, table);

    if(ruletypeid > 0) {
        dataobj = gra_rule_type_data_obj_dict[ruletypeid]['data_obj'];
        Object.keys(dataobj).forEach(function(key) {
            var row = clone.insertRow( -1 );
            var value = key in matchlist ? matchlist[key] : "";
            // HTML文作成
            var th = '<th id="data-object-id-' + key + '"><div class="cell-inner">' + dataobj[key] + '</div></th>';
            var td = '<td></td>';

            // 編集ならinputを有効化
            if (id == 'editGrafanatable'){
                th = '<th id="data-object-id-' + key + '"><div class="cell-inner">' + dataobj[key] + '<sup>*</sup><span class="help tooltip" title="' + getMessage("MOSJA26317", false) + '"><em class="owf owf-question"></em></span></div></th>';
                td = '<td><div class="cell-inner"><input id="edit-grafana-' + key + '" data-maxlength="128" data-type="text" class="validation-input" type="text" value="' + value + '" ></div></td>';
            }

            row.innerHTML = th + td;

            // 詳細表示ならtdにvalueを追加
            if (id == 'viewGrafanatable'){
                row.lastElementChild.append(value);
           }
 
        });
    }
}


////////////////////////////////////////////////
//  データの保存用 画面上のデータ収集
//  idInfo: データ収集先ID辞書
////////////////////////////////////////////////
function setGrafanaInfo(idInfo){

    var adapterInfo = {};

    // 入力データを取得してセット
    adapterInfo["adapter_id"] = 3;
    adapterInfo["grafana_disp_name"] = $(idInfo['grafana_disp_name']).val();
    adapterInfo["uri"] = $(idInfo['uri']).val();
    adapterInfo["username"] = $(idInfo['username']).val();
    adapterInfo["password"] = $(idInfo['password']).val();
    adapterInfo["evtime"] = $(idInfo['evtime']).val();
    adapterInfo["instance"] = $(idInfo['instance']).val();
    adapterInfo["rule_type_id"] = $(idInfo['rule_type_id']).val();

    var conditionalData = {}; // 条件名、Grafana項目を辞書形式で格納
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
function createGrafanaAdapterinfo() {

    var btnId = "#btnAddGrafana";

    // ボタン制御 連打防止
    $(btnId).prop("disabled", true);

    // 確認メッセージを表示
    if(!confirm(getMessage("MOSJA00002", false))){
        $(btnId).prop("disabled", false);
        return;
    }

    // データ収集
    var idInfo = getIdInfoGrafana('add');
    var postdata = setGrafanaInfo(idInfo);
    postdata['grafana_adapter_id'] = "0";

    // バリデーションチェック
    var objTBody = document.getElementById("tbodyGrafanaAdapterInfo");
    validateResult = validateGrafanaAdapterData(objTBody, postdata);

    //エラーメッセージを表示
    if(validateResult['errorFlag']){
        renderCreateGrafanaErrorMsg(validateResult['errorMsg']);
        return;
    }

    createSomeAdapterInfo(postdata, btnId, renderCreateGrafanaErrorMsg);
}


////////////////////////////////////////////////
//  データの保存(更新)
////////////////////////////////////////////////
function updateGrafanaAdapterInfo() {

    var btnId = "#btnEditGrafana";

    // ボタン制御 連打防止
    $(btnId).prop("disabled", true);

    // 確認メッセージを表示
    if(!confirm(getMessage("MOSJA26324", false))){
        $(btnId).prop("disabled", false);
        return;
    }

    // データ収集
    var idInfo = getIdInfoGrafana('edit');
    var postdata = setGrafanaInfo(idInfo);
    postdata["grafana_adapter_id"] = $('#viewGrafanaDetail').attr('data-recordid').replace("grafanaadapter-", "");

    // バリデーションチェック
    var objTBody = document.getElementById("tbodyGrafanaAdapterInfo");
    validateResult = validateGrafanaAdapterData(objTBody, postdata);

    //エラーメッセージを表示
    if(validateResult['errorFlag']){
        renderUpdateGrafanaErrorMsg(validateResult['errorMsg']);
        return;
    }

    updateSomeAdapterInfo(postdata, btnId, renderUpdateGrafanaErrorMsg);
}


////////////////////////////////////////////////
//  データの保存(削除)
////////////////////////////////////////////////
function deleteGrafanaAdapterInfo() {

    var btnId = "#btnDelGrafana";
    $(btnId).prop("disabled", true);

    // 削除レコードの存在確認後に確認メッセージを表示する
    var confirmMsg = getMessage("MOSJA26325", false);
    if(!confirm(confirmMsg)){
        $(btnId).prop("disabled", false);
        return;
    }

    // データ収集
    var strId = $('#viewGrafanaDetail').attr('data-recordid');
    var recordId = strId.replace("grafanaadapter-", "");
    var postdata = {
            "adapter_id" : 3,
            "record_id" : Number(recordId),
        };

    deleteSomeAdapterInfo(postdata, btnId);
}


////////////////////////////////////////////////
//  バリデーション
////////////////////////////////////////////////
var regexNum = new RegExp(/^[0-9]+$/);
function validateGrafanaAdapterData(objTBody, adapterInfo){

    var strID = "";
    var GrafanaName  = adapterInfo["grafana_disp_name"];
    var uri          = adapterInfo["uri"];
    var username     = adapterInfo["username"];
    var password     = adapterInfo["password"];
    var ruletypeid   = adapterInfo["rule_type_id"];
    var matchlist    = adapterInfo['match_list'];

    var errorFlag = false;
    var errorMsg = {};
    var chk_GrafanaName = {};
    var chk_uri = {};
    var chk_ruletypeid = {};

    // 画面に表示されているGrafanaアダプタの名称・ホスト名をすべて保持
    var selector = "";
    if(objTBody != null){
        for(var i = 0; i < objTBody.children.length; i++){
            strID = objTBody.children[i].id.replace("grafanaadapter-", "");
            selector = "#" + objTBody.children[i].id;
            // idが取得できた場合
            if(selector != "#") {
                chk_GrafanaName[strID]    = $(selector).data('name');
                chk_uri[strID]            = $(selector).data('uri');
                chk_ruletypeid[strID]     = $(selector).data('ruletypeid');
            }
        }
    }

    strID = adapterInfo["grafana_adapter_id"];
    chk_GrafanaName[strID] = GrafanaName;
    chk_uri[strID] = uri;

    // 検査開始
    errorMsg['grafana_disp_name'] = "";
    errorMsg['uri'] = "";
    errorMsg['username'] = "";
    errorMsg['password'] = "";
    errorMsg['rule_type_id'] = "";

    // adapternameの重複チェック
    var match_line = Object.keys(chk_GrafanaName).filter(function(key) {
        if(strID != key && chk_GrafanaName[key] == GrafanaName){
            return chk_GrafanaName[key] === GrafanaName;
        }
    });

    if(match_line.length > 0){
        errorMsg["grafana_disp_name"] += getMessage("MOSJA26315", false) + "\n";
        errorFlag = true;
    }

    // rule_type_idの未入力チェック
    if (!ruletypeid || ruletypeid <=0 ) {
        errorMsg["rule_type_id"] += getMessage("MOSJA26315", false) + "\n";
        errorFlag = true;
    }

    // uriとrule_type_idの重複チェック
    match_line = Object.keys(chk_uri).filter(function(key) {
        if(strID != key && chk_uri[key] == uri){
            if(chk_ruletypeid[key] == ruletypeid){
                return chk_uri[key] === uri;
            }
        }
    });

    if(match_line.length > 0){
        errorMsg["uri"] += getMessage("MOSJA26316", false) + "\n";
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
function getIdInfoGrafana(mode){

    modalwindowid = "#" + $('#grafana_v1_modal_add_id').val();
    if(mode == 'edit') {
        modalwindowid = "#modal-grafana-edit";
    }

    var idInfo = {
        'modalwindow'     : modalwindowid,
        'grafana_disp_name': "#" + mode + "GrafanaName",
        'uri'              : "#" + mode + "GrafanaUri",
        'username'         : "#" + mode + "GrafanaUsername",
        'password'         : "#" + mode + "GrafanaPassword",
        'evtime'           : "#" + mode + "GrafanaEventTime",
        'instance'         : "#" + mode + "GrafanaInstance",
        'rule_type_id'     : "#" + mode + "-grafana-rule-select",
        'match_list'       : "#" + mode + "Grafanatable tr",
    };

    return idInfo;
}

var renderCreateGrafanaErrorMsg = function(errorMsg) {
    renderGrafanaErrorMsg(errorMsg, 'add');
}

var renderUpdateGrafanaErrorMsg = function(errorMsg) {
    renderGrafanaErrorMsg(errorMsg, 'edit');
}

var renderGrafanaErrorMsg = function(errorMsg, mode) {
    alert(getMessage("MOSJA26012", false));

    idInfo = getIdInfoGrafana(mode);

    clearErrorMsg(idInfo['modalwindow']); // 前回エラーを削除

    renderErrorMsg(idInfo['grafana_disp_name'], errorMsg['grafana_disp_name']);
    renderErrorMsg(idInfo['uri'], errorMsg['uri']);
    renderErrorMsg(idInfo['username'], errorMsg['username']);
    renderErrorMsg(idInfo['password'], errorMsg['password']);
    renderErrorMsg(idInfo['rule_type_id'], errorMsg['rule_type_id']);
    renderErrorMsg(idInfo['evtime'], errorMsg['evtime']);
    renderErrorMsg(idInfo['instance'], errorMsg['instance']);

    //--------------------------------------------
    // Grafana項目へのエラー表示
    //--------------------------------------------
    $(idInfo['match_list']).each(function(index, element){
        var id = $(element).find('input').attr("id");
        var error_key = id.replace(mode + "-","");
        renderErrorMsg( '#' + id, errorMsg[error_key]);
    });
}

