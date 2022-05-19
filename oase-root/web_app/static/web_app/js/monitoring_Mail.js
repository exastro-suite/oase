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
var mail_rule_type_data_obj_dict = {};
var dd_flg = 0;
$(function() {

    mail_rule_type_data_obj_dict = $.parseJSON($('#mail_rule_type_data_obj_dict').val());

    //テストリクエストのルール変更時の処理
    $('#add-mail-rule-select')
        .focus(function(){
            previous = this.value;
        })
        .change(function(){
            var $this = $(this);
            $this.prop("disabled", true);

            // 前回エラーメッセージ削除
            clearErrorMsg($this.closest('td'));

            // this.value = 選択されたルール種別名に対応するルールID
            refleshRowsMail(this.value, 'add');

            $this.prop("disabled", false);
        });

    $('#edit-mail-rule-select')
        .focus(function(){
            previous = this.value;
        })
        .change(function(){
            var $this   = $(this);
            $this.prop("disabled", true);

            // 前回エラーメッセージ削除
            clearErrorMsg($this.closest('td'));

            // this.value = 選択されたルール種別名に対応するルールID
            refleshRowsMail(this.value, 'edit');

            $this.prop("disabled", false);
        });
});

function monitoringMailAddModalClose(selector1, selector2) {
    if(monitoringModalClose(selector1, selector2)) {
        refleshRowsMail(null, 'add');
    }
}

function monitoringMailAddModalChange(selector1, selector2, selector3) {
    if(monitoringModalChange(selector1, selector2, selector3)) {
        refleshRowsMail(null, 'add');
    }
}


////////////////////////////////////////////////
// 暗号化プロトコルの文字をIdに変換する 
////////////////////////////////////////////////
function getProtocolId(protocol) {

    var result = "";
    if(protocol == "NONE"){
        result = "0";
    }else if(protocol == "SSL"){
        result = "1";
    }else if(protocol == "TLS"){
        result = "2";
    }
    return result;
}


///////////////////////////////////////////////////////////////////
//
// プルダウンの作成
// mode: 'edit' or 'add'
// matchinfo: 選択されている値
//
///////////////////////////////////////////////////////////////////
function setpullDownMail(mode, matchinfo){

    var items = $('#mail-items').data('mailitems');
    var mailAry = items.split(',');

    var option;

    for ( let value of mailAry ){

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
function refleshRowsMail(rule_type_id, mode){

    var noneSelector = '#' + mode + '-rule-none-mail';
    var detailSelector = '#' + mode + '-rule-detail-mail';
    var tableIdStr = mode + 'Mailtable';

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
        var do_dict = mail_rule_type_data_obj_dict[rule_type_id]['data_obj'];

        var option = setpullDownMail('add','');

        // editの場合の保存済みメール項目反映用
        var matchlist = {};
        if(mode == 'edit') {
            var trId  = '#' + $('#viewMailadptDetail').attr('data-recordid');
            matchlist = $(trId).data('matchlist');
        }

        // id = '#' +mode + 'Mailtable' の下に行追加
        for (key in do_dict){
            // 行追加
            var tr = clone.insertRow( -1 );
            var value = key in matchlist ? matchlist[key] : "";

            // HTML文作成
            var th = '<th id="data-object-id-' + key + '"><div class="cell-inner">' + do_dict[key] + '<sup>*</sup><span class="help tooltip" title="' + getMessage("MOSJA26543", false) + '"><em class="owf owf-question"></em></span></div></th>';
            var td = '<td><div class="cell-inner"><div class="select"><select id="' + mode + '-mail-' + key + '"  value="' + value + '" >' + option + '</select></div></div></td>';

            tr.innerHTML = th + td;
        }
    }
}


////////////////////////////////////////////////
//  Mailアダプタの詳細画面にデータをセット
////////////////////////////////////////////////
function setInfoInMailDetailView(idName) {

    var trId         = '#' + idName;

    // 権限によるボタン制御
    $('#btnToEditModalMail, #btnDelMail').prop('disabled', false);
    var editable = $(trId).data('editable');
    if(!editable) {
        $('#btnToEditModalMail, #btnDelMail').prop('disabled', true);
    }

    var name               = $(trId).data('name');
    var encryptionprotocol = $(trId).data('protocol');
    var imapserver         = $(trId).data('imap_server');
    var port               = $(trId).data('port');
    var username           = $(trId).data('user');
    var ruletypeid         = $(trId).data('ruletypeid');
    var ruletypename       = $(trId).data('ruletypename');
    var matchlist          = $(trId).data('matchlist');
    var updateuser         = $(trId).data('updateuser');
    var timestamp          = $(trId).data('timestamp');
    
    $('#viewMailadptDetail').attr('data-recordid', idName);
    $('#viewMailadptName').text(name);
    $('#viewMailadptEncryptionProtocol').text(encryptionprotocol);
    $('#viewMailadptServer').text(imapserver);
    $('#viewMailadptPort').text(port);
    $('#viewMailadptUsername').text(username);
    $('#viewMailadptRuletype').text(ruletypename);
    $('#viewMailadptUpdateuser').text(updateuser);
    $('#viewMailadptTimestamp').text(timestamp);

    setMatchlistMail('viewMailadpttable', matchlist, ruletypeid);

    // ルール種別が削除されていた場合エラーを表示
    if(!ruletypeid || ruletypeid <=0) {
        var errorHTML = '<ul class="error-list" name="sub_error">';
        errorHTML += '<li><em class="owf owf-cross"></em>' + getMessage("MOSJA26510", false) + '<span class="tooltip help" data-tooltip="' + getMessage("MOSJA26511", false) + '"><em class="owf owf-question"></em></span></li>';
        errorHTML += '</ul>';
        $('#viewMailRuletype').addClass('error');
        $('#viewMailRuletype').html( errorHTML );
    }
}


////////////////////////////////////////////////
//  Mailの編集画面にデータをセット
////////////////////////////////////////////////
function setInfoInMailEditView() {

    beforeunloadThroughFlag = false;

    var trId               = '#' + $('#viewMailadptDetail').attr('data-recordid');
    var name               = $(trId).data('name');
    var encryptionprotocol = $(trId).data('protocol');
    var imapserver         = $(trId).data('imap_server');
    var port               = $(trId).data('port');
    var username           = $(trId).data('user');
    var password           = $(trId).data('password');
    var ruletypeid         = $(trId).data('ruletypeid');
    var matchlist          = $(trId).data('matchlist');
    var updateuser         = $(trId).data('updateuser');
    var timestamp          = $(trId).data('timestamp');

    $('#editMailadptName').val(name);
    $('#editMailadptProtocol').val(encryptionprotocol);
    $('#editMailadptServer').val(imapserver);
    $('#editMailadptPort').val(port);    
    $('#editMailadptUsername').val(username);
    $('#editMailadptPassword').val(password);
    $('#edit-mail-rule-select').val(ruletypeid);
    if(!ruletypeid || ruletypeid <= 0) {
        renderErrorMsg($('#edit-mail-rule-select'), getMessage("MOSJA26533", false));
    }
    $('#editMailUpdateuser').text(updateuser);
    $('#editMailTimestamp').text(timestamp);

    setMatchlistMail('editMailtable', matchlist, ruletypeid);
}


////////////////////////////////////////////////
//  詳細画面の突合情報欄にテーブルを追加
//  id: 追加対象の詳細画面のテーブルID(view or edit)
////////////////////////////////////////////////
function setMatchlistMail(id, matchlist, ruletypeid) {

    // すべての子要素を削除
    var table = document.getElementById(id);
    var clone = table.cloneNode( false );
    table.parentNode.replaceChild(clone, table);

    if(ruletypeid > 0) {
        dataobj = mail_rule_type_data_obj_dict[ruletypeid]['data_obj'];
        Object.keys(dataobj).forEach(function(key) {
            var row = clone.insertRow( -1 );
            var value = key in matchlist ? matchlist[key] : "";
            // HTML文作成
            var th = '<th id="data-object-id-' + key + '"><div class="cell-inner">' + dataobj[key] + '</div></th>';
            var td = '<td></td>';
            var option = setpullDownMail('edit',value);

            // 編集ならinputを有効化
            if (id == 'editMailtable'){
                th = '<th id="data-object-id-' + key + '"><div class="cell-inner">' + dataobj[key] + '<sup>*</sup><span class="help tooltip" title="' + getMessage("MOSJA26543", false) + '"><em class="owf owf-question"></em></span></div></th>';
                td = '<td><div class="cell-inner"><div class="select"><select id="edit-mail-' + key + '"  value="' + value + '" >' + option + '</select></div></div></td>';
            }
            row.innerHTML = th + td;

            // 詳細表示ならtdにvalueを追加
            if (id == 'viewMailadpttable'){
                row.lastElementChild.append(value);
           }
 
        });
    }
}


////////////////////////////////////////////////
//  データの保存用 画面上のデータ収集
//  idInfo: データ収集先ID辞書
////////////////////////////////////////////////
function setMailInfo(idInfo){

    var adapterInfo = {};

    // 入力データを取得してセット
    adapterInfo["adapter_id"]     = 5;
    adapterInfo["mail_disp_name"] = $(idInfo['mail_disp_name']).val();
    var protocol = $(idInfo['protocol']).val();
    adapterInfo["protocol"]       = getProtocolId(protocol);
    adapterInfo["imap_server"]    = $(idInfo['imap_server']).val();
    adapterInfo["username"]       = $(idInfo['username']).val();
    adapterInfo["password"]       = $(idInfo['password']).val();
    adapterInfo["port"]           = $(idInfo['port']).val();
    adapterInfo["rule_type_id"]   = $(idInfo['rule_type_id']).val();

    var conditionalData = {}; // 条件名、Mail項目を辞書形式で格納
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
function createMailAdapterinfo() {

    var btnId = "#btnAddMail";

    // ボタン制御 連打防止
    $(btnId).prop("disabled", true);

    // 確認メッセージを表示
    if(!confirm(getMessage("MOSJA00002", false))){
        $(btnId).prop("disabled", false);
        return;
    }

    // データ収集
    var idInfo = getIdInfoMail('add');
    var postdata = setMailInfo(idInfo);
    postdata['mail_adapter_id'] = "0";

    // バリデーションチェック
    var objTBody = document.getElementById("tbodyMailAdapterInfo");
    validateResult = validateMailAdapterData(objTBody, postdata);

    //エラーメッセージを表示
    if(validateResult['errorFlag']){
        renderCreateMailErrorMsg(validateResult['errorMsg']);
        return;
    }

    createSomeAdapterInfo(postdata, btnId, renderCreateMailErrorMsg);
}


////////////////////////////////////////////////
//  データの保存(更新)
////////////////////////////////////////////////
function updateMailAdapterInfo() {

    var btnId = "#btnEditMail";

    // ボタン制御 連打防止
    $(btnId).prop("disabled", true);

    // 確認メッセージを表示
    if(!confirm(getMessage("MOSJA26544", false))){
        $(btnId).prop("disabled", false);
        return;
    }

    // データ収集
    var idInfo = getIdInfoMail('edit');
    var postdata = setMailInfo(idInfo);
    postdata["mail_adapter_id"] = $('#viewMailadptDetail').attr('data-recordid').replace("mailadapter-", "");

    // バリデーションチェック
    var objTBody = document.getElementById("tbodyMailAdapterInfo");
    validateResult = validateMailAdapterData(objTBody, postdata);

    //エラーメッセージを表示
    if(validateResult['errorFlag']){
        renderUpdateMailErrorMsg(validateResult['errorMsg']);
        return;
    }

    updateSomeAdapterInfo(postdata, btnId, renderUpdateMailErrorMsg);
}


////////////////////////////////////////////////
//  データの保存(削除)
////////////////////////////////////////////////
function deleteMailAdapterInfo() {

    var btnId = "#btnDelMail";
    $(btnId).prop("disabled", true);

    // 削除レコードの存在確認後に確認メッセージを表示する
    var confirmMsg = getMessage("MOSJA26545", false);
    if(!confirm(confirmMsg)){
        $(btnId).prop("disabled", false);
        return;
    }

    // データ収集
    var strId = $('#viewMailadptDetail').attr('data-recordid');
    var recordId = strId.replace("mailadapter-", "");
    var postdata = {
            "adapter_id" : 5,
            "record_id" : Number(recordId),
        };

    deleteSomeAdapterInfo(postdata, btnId);
}


////////////////////////////////////////////////
//  バリデーション
////////////////////////////////////////////////
var regexNum = new RegExp(/^[0-9]+$/);
function validateMailAdapterData(objTBody, adapterInfo){

    var strID        = "";
    var mailName     = adapterInfo["mail_disp_name"];
    var protocol     = adapterInfo["protocol"];
    var host         = adapterInfo["imap_server"];
    var port         = adapterInfo["port"];
    var username     = adapterInfo["username"];
    var password     = adapterInfo["password"];
    var ruletypeid   = adapterInfo["rule_type_id"];
    var matchlist    = adapterInfo['match_list'];

    var errorFlag = false;
    var errorMsg = {};
    var chk_mailName = {};
    var chk_host = {};
    var chk_ruletypeid = {};

    // 画面に表示されているMailアダプタの名称・ホスト名をすべて保持
    var selector = "";
    if(objTBody != null){
        for(var i = 0; i < objTBody.children.length; i++){
            strID = objTBody.children[i].id.replace("mailadapter-", "");
            selector = "#" + objTBody.children[i].id;
            // idが取得できた場合
            if(selector != "#") {
                chk_mailName[strID]   = $(selector).data('name');
                chk_host[strID]       = $(selector).data('imap-server');
                chk_ruletypeid[strID] = $(selector).data('ruletypeid');
            }
        }
    }

    strID = adapterInfo["mail_adapter_id"];
    chk_mailName[strID] = mailName;
    chk_host[strID] = host;

    // 検査開始
    errorMsg['mail_disp_name'] = "";
    errorMsg['host']           = "";
    errorMsg['port']           = "";
    errorMsg['protocol']       = "";
    errorMsg['username']       = "";
    errorMsg['password']       = "";
    errorMsg['rule_type_id']   = "";

    // portの入力値チェック（0以上65535以下）
    if(!regexNum.test(port) || 0 > parseInt(port) || parseInt(port) > 65535) {
        errorMsg["port"] += getMessage("MOSJA26526", false) + "\n";
        errorFlag = true;
    }

    // adapternameの重複チェック
    var match_line = Object.keys(chk_mailName).filter(function(key) {
        if(strID != key && chk_mailName[key] == mailName){
            return chk_mailName[key] === mailName;
        }
    });

    if(match_line.length > 0){        // 他のMailアダプタ名と重複しています。修正してください。
        errorMsg["mail_disp_name"] += getMessage("MOSJA26540", false) + "\n";
        errorFlag = true;
    }

    // rule_type_idの未入力チェック
    if (!ruletypeid || ruletypeid <=0 ) {
        errorMsg["rule_type_id"] += getMessage("MOSJA26540", false) + "\n";
        errorFlag = true;
    }

    // hostとrule_type_idの重複チェック
    match_line = Object.keys(chk_host).filter(function(key) {
        if(strID != key && chk_host[key] == host){
            if(chk_ruletypeid[key] == ruletypeid){
                return chk_host[key] === host;
            }
        }
    });

    if(match_line.length > 0){      // URIとディシジョンテーブル名の組み合わせが重複しています。URI、またはディシジョンテーブル名を変更してください。
        errorMsg["host"] += getMessage("MOSJA26541", false) + "\n";
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
function getIdInfoMail(mode){

    modalwindowid = "#" + $('#mail_v1_modal_add_id').val();
    if(mode == 'edit') {
        modalwindowid = "#modal-mail-edit";
    }

    var idInfo = {
        'modalwindow'     : modalwindowid,
        'mail_disp_name'  : "#" + mode + "MailadptName",
        'protocol'        : "#" + mode + "MailadptProtocol",
        'imap_server'     : "#" + mode + "MailadptServer",
        'port'            : "#" + mode + "MailadptPort",
        'username'        : "#" + mode + "MailadptUsername",
        'password'        : "#" + mode + "MailadptPassword",
        'rule_type_id'    : "#" + mode + "-mail-rule-select",
        'match_list'      : "#" + mode + "Mailtable tr",
    };

    return idInfo;
}

var renderCreateMailErrorMsg = function(errorMsg) {
    renderMailErrorMsg(errorMsg, 'add');
}

var renderUpdateMailErrorMsg = function(errorMsg) {
    renderMailErrorMsg(errorMsg, 'edit');
}

var renderMailErrorMsg = function(errorMsg, mode) {
    alert(getMessage("MOSJA26012", false)); // 入力値が正しくありません。\n入力内容を確認してください。

    idInfo = getIdInfoMail(mode);

    clearErrorMsg(idInfo['modalwindow']); // 前回エラーを削除

    renderErrorMsg(idInfo['mail_disp_name'], errorMsg['mail_disp_name']);
    renderErrorMsg(idInfo['protocol'], errorMsg['protocol']);
    renderErrorMsg(idInfo['imap_server'], errorMsg['imap_server']);
    renderErrorMsg(idInfo['port'], errorMsg['port']);
    renderErrorMsg(idInfo['username'], errorMsg['username']);
    renderErrorMsg(idInfo['password'], errorMsg['password']);
    renderErrorMsg(idInfo['rule_type_id'], errorMsg['rule_type_id']);


    //--------------------------------------------
    // Mail項目へのエラー表示
    //--------------------------------------------
    $(idInfo['match_list']).each(function(index, element){
        var id = $(element).find('input').attr("id");
        var error_key = id.replace(mode + "-","");
        renderErrorMsg( '#' + id, errorMsg[error_key]);
    });
}

