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
var pro_rule_type_data_obj_dict = {};
$(function() {

    pro_rule_type_data_obj_dict = $.parseJSON($('#pro_rule_type_data_obj_dict').val());

    //テストリクエストのルール変更時の処理
    $('#add-prometheus-rule-select')
        .focus(function(){
            previous = this.value;
        })
        .change(function(){
            var $this = $(this);
            $this.prop("disabled", true);

            // 前回エラーメッセージ削除
            clearErrorMsg($this.closest('td'));

            // this.value = 選択されたルール種別名に対応するルールID
            refleshRowsPrometheus(this.value, 'add');

            $this.prop("disabled", false);
        });

    $('#edit-prometheus-rule-select')
        .focus(function(){
            previous = this.value;
        })
        .change(function(){
            var $this   = $(this);
            $this.prop("disabled", true);

            // 前回エラーメッセージ削除
            clearErrorMsg($this.closest('td'));

            // this.value = 選択されたルール種別名に対応するルールID
            refleshRowsPrometheus(this.value, 'edit');

            $this.prop("disabled", false);
        });
});

function monitoringPrometheusAddModalClose(selector1, selector2) {
    if(monitoringModalClose(selector1, selector2)) {
        refleshRowsPrometheus(null, 'add');
    }
}

function monitoringPrometheusAddModalChange(selector1, selector2, selector3) {
    if(monitoringModalChange(selector1, selector2, selector3)) {
        refleshRowsPrometheus(null, 'add');
    }
}

///////////////////////////////////////////////////////////////////
//
// プルダウンの作成
// mode: 'edit' or 'add'
// matchinfo: 選択されている値
//
///////////////////////////////////////////////////////////////////
function setpullDownPrometheus(mode, matchinfo){

    var items = $('#prometheus-items').data('prometheusitems');
    var prometheusAry = items.split(',');

    var option;

    for ( let value of prometheusAry ){

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
function refleshRowsPrometheus(rule_type_id, mode){

    var noneSelector = '#' + mode + '-rule-none-prometheus';
    var detailSelector = '#' + mode + '-rule-detail-prometheus';
    var tableIdStr = mode + 'Prometheustable';

    $(noneSelector).hide();
    $(noneSelector).children().remove();
    $(detailSelector).show();

    // すべての子要素を削除
    var table = document.getElementById(tableIdStr);
    var clone = table.cloneNode( false );
    table.parentNode.replaceChild(clone, table);

    if(!rule_type_id) {
        $(noneSelector).show();
        $(noneSelector).append('<input type="hidden" value="" required>');
        $(detailSelector).hide();
    } else {
        // 条件名変換用
        var do_dict = pro_rule_type_data_obj_dict[rule_type_id]['data_obj'];

        var option = setpullDownPrometheus('add','');

        // editの場合の保存済みPrometheus項目反映用
        var matchlist = {};
        if(mode == 'edit') {
            var trId  = '#' + $('#viewPrometheusDetail').attr('data-recordid');
            matchlist = $(trId).data('matchlist');
        }

        // id = '#' +mode + 'Prometheustable' の下に行追加
        for (key in do_dict){
            // 行追加
            var tr = clone.insertRow( -1 );
            var value = key in matchlist ? matchlist[key] : "";

            // HTML文作成
            var th = '<th id="data-object-id-' + key + '"><div class="cell-inner">' + do_dict[key] + '<sup>*</sup><span class="help tooltip" title="' + getMessage("MOSJA26214", false) + '"><em class="owf owf-question"></em></span></div></th>';
            var td = '<td><div class="cell-inner"><div class="select"><select id="' + mode + '-prometheus-' + key + '"  value="' + value + '" >' + option + '</select></div></div></td>';

            tr.innerHTML = th + td;
        }
    }
}

////////////////////////////////////////////////
//  Prometheusの詳細画面にデータをセット
////////////////////////////////////////////////
function setInfoInPrometheusDetailView(idName) {

    var trId         = '#' + idName;

    // 権限によるボタン制御
    $('#btnToEditModalPrometheus, #btnDelPrometheus').prop('disabled', false);
    var editable = $(trId).data('editable');
    if(!editable) {
        $('#btnToEditModalPrometheus, #btnDelPrometheus').prop('disabled', true);
    }

    var name         = $(trId).data('name');
    var uri          = $(trId).data('uri');
    var username     = $(trId).data('username');
    var ruletypeid   = $(trId).data('ruletypeid');
    var ruletypename = $(trId).data('ruletypename');
    var matchlist    = $(trId).data('matchlist');
    var updateuser   = $(trId).data('updateuser');
    var timestamp    = $(trId).data('timestamp');

    $('#viewPrometheusDetail').attr('data-recordid', idName);
    $('#viewPrometheusName').text(name);
    $('#viewPrometheusUri').text(uri);
    $('#viewPrometheusUsername').text(username);
    $('#viewPrometheusRuletype').text(ruletypename);
    $('#viewPrometheusUpdateuser').text(updateuser);
    $('#viewPrometheusTimestamp').text(timestamp);

    setMatchlistPrometheus('viewPrometheustable', matchlist, ruletypeid);

    // ルール種別が削除されていた場合エラーを表示
    if(!ruletypeid || ruletypeid <=0) {
        var errorHTML = '<ul class="error-list" name="sub_error">';
        errorHTML += '<li><em class="owf owf-cross"></em>' + getMessage("MOSJA26211", false) + '<span class="tooltip help" data-tooltip="' + getMessage("MOSJA26212", false) + '"><em class="owf owf-question"></em></span></li>';
        errorHTML += '</ul>';
        $('#viewPrometheusRuletype').addClass('error');
        $('#viewPrometheusRuletype').html( errorHTML );
    }
}


////////////////////////////////////////////////
//  Prometheusの編集画面にデータをセット
////////////////////////////////////////////////
function setInfoInPrometheusEditView() {

    beforeunloadThroughFlag = false;

    var trId         = '#' + $('#viewPrometheusDetail').attr('data-recordid');
    var name         = $(trId).data('name');
    var uri          = $(trId).data('uri');
    var username     = $(trId).data('username');
    var password     = $(trId).data('password');
    var ruletypeid   = $(trId).data('ruletypeid');
    var matchlist    = $(trId).data('matchlist');
    var updateuser   = $(trId).data('updateuser');
    var timestamp    = $(trId).data('timestamp');

    $('#editPrometheusName').val(name);
    $('#editPrometheusUri').val(uri);
    $('#editPrometheusUsername').val(username);
    $('#editPrometheusPass').val(password);
    $('#edit-prometheus-rule-select').val(ruletypeid);
    if(!ruletypeid || ruletypeid <= 0) {
        renderErrorMsg($('#edit-prometheus-rule-select'), getMessage("MOSJA26215", false));
    }
    $('#editPrometheusUpdateuser').text(updateuser);
    $('#editPrometheusTimestamp').text(timestamp);

    setMatchlistPrometheus('editPrometheustable', matchlist, ruletypeid);
}


////////////////////////////////////////////////
//  詳細画面の突合情報欄にテーブルを追加
//  id: 追加対象の詳細画面のテーブルID(view or edit)
////////////////////////////////////////////////
function setMatchlistPrometheus(id, matchlist, ruletypeid) {

    // すべての子要素を削除
    var table = document.getElementById(id);
    var clone = table.cloneNode( false );
    table.parentNode.replaceChild(clone, table);

    if(ruletypeid > 0) {
        dataobj = pro_rule_type_data_obj_dict[ruletypeid]['data_obj'];
        Object.keys(dataobj).forEach(function(key) {
            var row = clone.insertRow( -1 );
            var value = key in matchlist ? matchlist[key] : "";
            // HTML文作成
            var th = '<th id="data-object-id-' + key + '"><div class="cell-inner">' + dataobj[key] + '</div></th>';
            var td = '<td></td>';
            var option = setpullDownPrometheus('edit',value);

            // 編集ならinputを有効化
            if (id == 'editPrometheustable'){
                th = '<th id="data-object-id-' + key + '"><div class="cell-inner">' + dataobj[key] + '<sup>*</sup><span class="help tooltip" title="' + getMessage("MOSJA26214", false) + '"><em class="owf owf-question"></em></span></div></th>';
                td = '<td><div class="cell-inner"><div class="select"><select id="edit-prometheus-' + key + '"  value="' + value + '" >' + option + '</select></div></div></td>';
            }

            row.innerHTML = th + td;

            // 詳細表示ならtdにvalueを追加
            if (id == 'viewPrometheustable'){
                row.lastElementChild.append(value);
           }
 
        });
    }
}


////////////////////////////////////////////////
//  データの保存用 画面上のデータ収集
//  idInfo: データ収集先ID辞書
////////////////////////////////////////////////
function setPrometheusInfo(idInfo){

    var adapterInfo = {};

    // 入力データを取得してセット
    adapterInfo["adapter_id"] = 2;
    adapterInfo["prometheus_disp_name"] = $(idInfo['prometheus_disp_name']).val();
    adapterInfo["uri"] = $(idInfo['uri']).val();
    adapterInfo["username"] = $(idInfo['username']).val();
    adapterInfo["password"] = $(idInfo['password']).val();
    adapterInfo["rule_type_id"] = $(idInfo['rule_type_id']).val();

    var conditionalData = {}; // 条件名、Prometheus項目を辞書形式で格納
    $(idInfo['match_list']).each(function(index, element){
        var id          = $(element).find('th').attr("id"); // 条件名
        var value       = $(element).find('select').val(); // 条件式

        id = id.replace("data-object-id-", "");
        conditionalData[id] = value;
    });

    adapterInfo['match_list'] = conditionalData;

    return adapterInfo;
}


////////////////////////////////////////////////
//  データの保存(新規)
////////////////////////////////////////////////
function createPrometheusAdapterinfo() {

    var btnId = "#btnAddPrometheus";

    // ボタン制御 連打防止
    $(btnId).prop("disabled", true);

    // 確認メッセージを表示
    if(!confirm(getMessage("MOSJA00002", false))){
        $(btnId).prop("disabled", false);
        return;
    }

    // データ収集
    var idInfo = getIdInfoPrometheus('add');
    var postdata = setPrometheusInfo(idInfo);
    postdata['prometheus_adapter_id'] = "0";

    // バリデーションチェック
    var objTBody = document.getElementById("tbodyPrometheusAdapterInfo");
    validateResult = validatePrometheusAdapterData(objTBody, postdata);

    //エラーメッセージを表示
    if(validateResult['errorFlag']){
        renderCreatePrometheusErrorMsg(validateResult['errorMsg']);
        return;
    }

    createSomeAdapterInfo(postdata, btnId, renderCreatePrometheusErrorMsg);
}

////////////////////////////////////////////////
//  データの保存(更新)
////////////////////////////////////////////////
function updatePrometheusAdapterInfo() {

    var btnId = "#btnEditPrometheus";

    // ボタン制御 連打防止
    $(btnId).prop("disabled", true);

    // 確認メッセージを表示
    if(!confirm(getMessage("MOSJA26216", false))){
        $(btnId).prop("disabled", false);
        return;
    }

    // データ収集
    var idInfo = getIdInfoPrometheus('edit');
    var postdata = setPrometheusInfo(idInfo);
    postdata["prometheus_adapter_id"] = $('#viewPrometheusDetail').attr('data-recordid').replace("prometheusadapter-", "");

    // バリデーションチェック
    var objTBody = document.getElementById("tbodyPrometheusAdapterInfo");
    validateResult = validatePrometheusAdapterData(objTBody, postdata);

    //エラーメッセージを表示
    if(validateResult['errorFlag']){
        renderUpdatePrometheusErrorMsg(validateResult['errorMsg']);
        return;
    }

    updateSomeAdapterInfo(postdata, btnId, renderUpdatePrometheusErrorMsg);
}


////////////////////////////////////////////////
//  データの保存(削除)
////////////////////////////////////////////////
function deletePrometheusAdapterInfo() {

    var btnId = "#btnDelPrometheus";
    $(btnId).prop("disabled", true);

    // 削除レコードの存在確認後に確認メッセージを表示する
    var confirmMsg = getMessage("MOSJA26239", false);
    if(!confirm(confirmMsg)){
        $(btnId).prop("disabled", false);
        return;
    }

    // データ収集
    var strId = $('#viewPrometheusDetail').attr('data-recordid');
    var recordId = strId.replace("prometheusadapter-", "");
    var postdata = {
            "adapter_id" : 2,
            "record_id" : Number(recordId),
        };

    deleteSomeAdapterInfo(postdata, btnId);
}


////////////////////////////////////////////////
//  バリデーション
////////////////////////////////////////////////
var regexNum = new RegExp(/^[0-9]+$/);
function validatePrometheusAdapterData(objTBody, adapterInfo){

    var strID = "";
    var PrometheusName   = adapterInfo["prometheus_disp_name"];
    var uri          = adapterInfo["uri"];
    var username     = adapterInfo["username"];
    var password     = adapterInfo["password"];
    var ruletypeid   = adapterInfo["rule_type_id"];
    var matchlist    = adapterInfo['match_list'];

    var errorFlag = false;
    var errorMsg = {};
    var chk_PrometheusName = {};
    var chk_uri = {};
    var chk_ruletypeid = {};

    // 画面に表示されているPrometheusアダプタの名称・ホスト名をすべて保持
    var selector = "";
    if(objTBody != null){
        for(var i = 0; i < objTBody.children.length; i++){
            strID = objTBody.children[i].id.replace("prometheusadapter-", "");
            selector = "#" + objTBody.children[i].id;
            // idが取得できた場合
            if(selector != "#") {
                chk_PrometheusName[strID] = $(selector).data('name');
                chk_uri[strID]       = $(selector).data('uri');
                chk_ruletypeid[strID] = $(selector).data('ruletypeid');
            }
        }
    }

    strID = adapterInfo["prometheus_adapter_id"];
    chk_PrometheusName[strID] = PrometheusName;
    chk_uri[strID] = uri;

    // 検査開始
    errorMsg['prometheus_disp_name'] = "";
    errorMsg['uri'] = "";
    errorMsg['username'] = "";
    errorMsg['password'] = "";
    errorMsg['rule_type_id'] = "";

    // adapternameの重複チェック
    var match_line = Object.keys(chk_PrometheusName).filter(function(key) {
        if(strID != key && chk_PrometheusName[key] == PrometheusName){
            return chk_PrometheusName[key] === PrometheusName;
        }
    });

    if(match_line.length > 0){
        errorMsg["prometheus_disp_name"] += getMessage("MOSJA26217", false) + "\n";
        errorFlag = true;
    }

    // rule_type_idの未入力チェック
    if (!ruletypeid || ruletypeid <=0 ) {
        errorMsg["rule_type_id"] += getMessage("MOSJA26217", false) + "\n";
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
        errorMsg["uri"] += getMessage("MOSJA26218", false) + "\n";
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
function getIdInfoPrometheus(mode){

    modalwindowid = "#" + $('#prometheus_v1_modal_add_id').val();
    if(mode == 'edit') {
        modalwindowid = "#modal-prometheus-edit";
    }

    var idInfo = {
        'modalwindow'     : modalwindowid,
        'prometheus_disp_name': "#" + mode + "PrometheusName",
        'uri'             : "#" + mode + "PrometheusUri",
        'username'        : "#" + mode + "PrometheusUsername",
        'password'        : "#" + mode + "PrometheusPass",
        'rule_type_id'    : "#" + mode + "-prometheus-rule-select",
        'match_list'      : "#" + mode + "Prometheustable tr",
    };

    return idInfo;
}

var renderCreatePrometheusErrorMsg = function(errorMsg) {
    renderPrometheusErrorMsg(errorMsg, 'add');
}

var renderUpdatePrometheusErrorMsg = function(errorMsg) {
    renderPrometheusErrorMsg(errorMsg, 'edit');
}

var renderPrometheusErrorMsg = function(errorMsg, mode) {
    alert(getMessage("MOSJA26012", false));

    idInfo = getIdInfoPrometheus(mode);

    clearErrorMsg(idInfo['modalwindow']); // 前回エラーを削除

    renderErrorMsg(idInfo['prometheus_disp_name'], errorMsg['prometheus_disp_name']);
    renderErrorMsg(idInfo['uri'], errorMsg['uri']);
    renderErrorMsg(idInfo['username'], errorMsg['username']);
    renderErrorMsg(idInfo['password'], errorMsg['password']);
    renderErrorMsg(idInfo['rule_type_id'], errorMsg['rule_type_id']);

    //--------------------------------------------
    // Prometheus項目へのエラー表示
    //--------------------------------------------
    $(idInfo['match_list']).each(function(index, element){
        var id = $(element).find('input').attr("id");
        var error_key = id.replace(mode + "-","");
        renderErrorMsg( '#' + id, errorMsg[error_key]);
    });
}

