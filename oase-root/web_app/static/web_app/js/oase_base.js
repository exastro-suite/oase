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

﻿//////////////////////////////////////////////
//// 定数 
//////////////////////////////////////////////////
OPE_NOTHING = 0;
OPE_INSERT  = 1;
OPE_UPDATE  = 2;
OPE_DELETE  = 3;
OPELIST_ADD = [[OPE_NOTHING, ''], [OPE_INSERT, '追加'], ];
OPELIST_MOD = [[OPE_NOTHING, ''], [OPE_UPDATE, '更新'], [OPE_DELETE, '削除'], ];
// 言語設定変数
// let lang_mode = document.getElementById('lang').innerHTML;


//////////////////////////////////////////////
//  詳細画面の表示制御
////////////////////////////////////////////////
function openDialog(id)
{
    document.getElementById(id).style.display = "block";
}

function closeDialog(id)
{
    document.getElementById(id).style.display = "none";
}
   
function logout(){
    let choice = confirm(getMessage("MOSJA00202", false));
    if(choice === true) {
        window.location.href = "/oase_web/top/logout";
    }
}
////////////////////////////////////////////////
////  編集モードへ移行する
//////////////////////////////////////////////////
function _changeModeToEdit(url, btnId) {

    $(btnId).prop("disabled", true);
    window.location.href = url;
}
////////////////////////////////////////////////
////  キャンセル処理
//////////////////////////////////////////////////
function _cancel(url, btnId, msg)
{
    $(btnId).prop("disabled", true);
    let choice = true;

    // 変更が有れば確認する
    if($('.change-value').length)
    {
        choice = confirm(msg);
    }
    // trueならキャンセルする
    if(choice) {
       beforeunloadThroughFlag = true;
       window.location.href = url;
       return true;
    }

    $(btnId).prop("disabled", false);
}

////////////////////////////////////////////////
//  リセット処理
////////////////////////////////////////////////
function _reset(formId, btnId, msg)
{

    $(btnId).prop("disabled", true);
    let choice = false;

    // 変更が無ければメッセージは表示しない
    if($('.change-value').length){
        choice = confirm(msg);
    }

    if(choice){
        beforeunloadThroughFlag = true;
        $(formId).submit();
    }

    $(btnId).prop("disabled", false);
}


/**
 * DOM読み込み後に実行される（画面表示時の初期設定）
 *
 */
$(function(){

    // .sub_menu は廃止予定
    $(".sub-menu-data, .sub_menu, .sub-menu-header").on('click', '.modalOpen', function(){
        let navClass = $(this).attr("class");
        let href = $(this).attr("href");

        $(href).fadeIn();
        $(this).addClass("open");
        return false;
    });

    $(".sub-menu-data, .sub_menu, .sub-menu-header").on('click', '.modalClose', function(){
        let parentsID = $(this).parents(".modal").attr("id");

        $(this).parents(".modal").fadeOut();
        $(".modalOpen").removeClass("open");
        return false;
    });

    /**
     * 選択中のメニュータイトルにactiveクラスを付与する。
     */
    let activeUrl = location.pathname.split("/")[2];

    // 個人設定のときはメニュー選択エフェクトなし
    if( location.pathname.split("/")[3] !== "personal_config"){
        $("li").removeClass("active");
        $("."+activeUrl).addClass("active");
    }

    /**
     * アコーディオン制御
     */
    //.mainの中のdiv要素がクリックされたら
    $('#container dt.collapsible').click(function() {

        //クリックされた.tabの中のdiv要素に隣接するdiv要素が開いたり閉じたりする。
        $('+dd', this).slideToggle("fast");

        //▲▼切り替える
        let $span = $(this).children('span');
        if($span.hasClass('collapsed')) {
            $span.removeClass('collapsed');
            $span.addClass('expanded');
        }
        else if($span.hasClass('expanded')) {
            $span.removeClass('expanded');
            $span.addClass('collapsed');
        }
    });
});



////////////////////////////////////////////////
//  message_id処理
////////////////////////////////////////////////
function getMessage(msgid, showMsgFlag){
    let msg = "";
    let lang_mode = $('#lang').html();

    //存在するメッセージidか否かを判定
    if(msgid in Ary){
        //言語設定値が設定されている場合、言語を変換
        // if ((get_lang_mode.indexof('EN') !== -1) || ( get_lang_mode.indexof('JA') !== -1)){
        if (lang_mode === 'EN' || lang_mode === 'JA'){
            msgid = changeLang(msgid, lang_mode);
        }
        msg = (Ary[msgid]);

        //必要に応じメッセージIDを付ける
        if(showMsgFlag){
            msg = msg +"(" + msgid +")";
        }
    }
    else{
        msg =  msgid  + " not found.";
    }
    
    return msg;
}

function changeLang(msgid, lang){

    if(lang === 'EN'){
        msgid = msgid.replace('MOSJA', 'MOSEN');
    }

    return msgid;
}