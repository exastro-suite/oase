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
//  入力値バリデーションチェック
////////////////////////////////////////////////
$( function(){
    beforeunloadThroughFlag = false;
});

////////////////////////////////////////////////
//  未入力エラー処理
////////////////////////////////////////////////
function nonInput(tag, errorTitle, errorMessage){
    tag.parents('th, td').addClass('error');
    var errorHTML = '<ul class="error-list"><li><em class="owf owf-cross"></em>' + errorTitle + '<span class="tooltip help" title="' + errorMessage + '"><em class="owf owf-question"></em></span></li></ul>';
        tag.after( errorHTML );
    if( tag = $("#rule_type_name")){
        tag.addClass("server-error");
    }
}

////////////////////////////////////////////////
// 新規追加画面の表示
////////////////////////////////////////////////
function showNewTable(){

    // モーダル画面のタイトル初期化
    $("#modal-title-new").text(getMessage('MOSJA00090', false));
    // 初期化
    $("#provider_name").val("");
    $("#auth_type").val("");
    $("#logo").val("");
    $("#visible_flag").val("");
    $("#clientid").val("");
    $("#clientsecret").val("");
    $("#authorizationuri").val("");
    $("#accesstokenuri").val("");
    $("#resourceowneruri").val("");
    $("#scope").val("");
    $("#id").val("");
    $("#name").val("");
    $("#email").val("");
    $("#imageurl").val("");
    $("#proxy").val("");

    // バリデーションエラー初期化
    $(".error-list").remove();
    $("td").removeClass("error");
}

////////////////////////////////////////////////
//  DB登録 (新規登録)
////////////////////////////////////////////////
function submitTableData(){

    var ssoInfo = {};

    // ボタン制御 連打防止
    $("#btnAdd").prop("disabled", true);
    if(confirm(getMessage('MOSJA00002',false)) == true){
        ssoInfo["provider_name"]    = $("#provider_name").val();
        ssoInfo["auth_type"]        = $("#auth_type").val();
        ssoInfo["logo"]             = $("#logo").val();
        ssoInfo["visible_flag"]     = $("#visible_flag").val();
        ssoInfo["clientid"]         = $("#clientid").val();
        ssoInfo["clientsecret"]     = $("#clientsecret").val();
        ssoInfo["authorizationuri"] = $("#authorizationuri").val();
        ssoInfo["accesstokenuri"]   = $("#accesstokenuri").val();
        ssoInfo["resourceowneruri"] = $("#resourceowneruri").val();
        ssoInfo["scope"]            = $("#scope").val();
        ssoInfo["id"]               = $("#id").val();
        ssoInfo["name"]             = $("#name").val();
        ssoInfo["email"]            = $("#email").val();
        ssoInfo["imageurl"]         = $("#imageurl").val();
        ssoInfo["proxy"]            = $("#proxy").val();

        // 登録情報をjson形式に変換し、任意のvalueにセットする。
        var jstr = JSON.stringify({"sso_info": ssoInfo});
        $("#add_record").val(jstr);

        // formにセットした登録情報をサーバーに送る
        document.getElementById("formSsoData").submit();
    } else {
        $("#btnAdd").prop("disabled", false);
    }
}

function submitAction(){

    // 前回エラー表記削除
    $('.error').removeClass('error');
    $('.error-list').remove();

    $.ajax({
        type : "POST",
        url  : "sso_info/modify",
        data : $("#formSsoData").serialize(),
        dataType: "json",
    })
    .done(function(response_json) {
        if(response_json.status == 'success') {
            alert(getMessage('MOSJA00011', false));
            beforeunloadThroughFlag = true;//ページ移動の注意を無視
            $("#btnAdd").prop("disabled", false);
            location.href = response_json.redirect_url;
        }
        else {
            alert(getMessage('MOSJA00005', true) + "\n");

            // 基本情報エラー処理
            errorMsg = response_json.error_top;
            Object.keys(errorMsg).forEach(function(id) {
                errorStr = errorMsg[id];
                if(!errorStr || errorStr.length == 0) {
                    return true;
                }
                // エラークラスを付与
                nonInput($("#"+id), getMessage('MOSJA00097', false), errorMsg[id]);
            });
            $("#btnAdd").prop("disabled", true);
        }
    })
    .fail(function(respdata, stscode, resp) {
        if(stscode == "error") {
            alert(getMessage('MOSJA00014', false));
            $("#btnAdd").prop("disabled", false);
            window.location.href = "/oase_web/top/logout";
        } else {
            alert(getMessage('MOSJA00014', false) + "\n" + respdata.responseText);
            $("#btnAdd").prop("disabled", false);
        }
    });
}

////////////////////////////////////////////////
//  詳細画面の表示制御
////////////////////////////////////////////////
function showDetail(
    pk,
    provider_name,
    auth_type,
    logo,
    visible_flag,
    clientid,
    clientsecret,
    authorizationuri,
    accesstokenuri,
    resourceowneruri,
    scope,
    id,
    name,
    email,
    imageurl,
    proxy)
{

    var ssoBasicInfoData = [];
    var ssoAttriInfoData = [];

    $("#hidSsoId2").val(pk);

    ssoBasicInfoData.push(provider_name);
    $("#hid-provider-name").val(provider_name);

    if( auth_type == 0 ) {
        ssoBasicInfoData.push(getMessage("MOSJA28011", false));
    } else {
        ssoBasicInfoData.push("");
    }

    ssoBasicInfoData.push(logo);

    if( visible_flag == 0 ) {
        ssoBasicInfoData.push(getMessage("MOSJA28015", false));
    } else {
        ssoBasicInfoData.push(getMessage("MOSJA28016", false));
    }

    ssoAttriInfoData.push(clientid);
    ssoAttriInfoData.push(clientsecret);
    ssoAttriInfoData.push(authorizationuri);
    ssoAttriInfoData.push(accesstokenuri);
    ssoAttriInfoData.push(resourceowneruri);
    ssoAttriInfoData.push(scope);
    ssoAttriInfoData.push(id);
    ssoAttriInfoData.push(name);
    ssoAttriInfoData.push(email);
    ssoAttriInfoData.push(imageurl);
    ssoAttriInfoData.push(proxy);

    // SSO基本情報埋め込み
    $("#sso-basic-info td div").each(function(index, element){
        $(element).text(ssoBasicInfoData[index]);
    });

    // SSO属性情報埋め込み
    $("#sso-attri-info td div").each(function(index, element){
        $(element).text(ssoAttriInfoData[index]);
    });
}

////////////////////////////////////////////////
// 詳細画面の削除ボタン制御
////////////////////////////////////////////////
function deleteTable(){
    $("#btnDelSso").prop("disabled", true);
    var ssoInfoID = $("#hidSsoId2").val();
    ssoInfoID     = ssoInfoID.substr(3);

    //valueに値をセット
    $("#add_record2").val(ssoInfoID);
    $("#operate").val("delete");

    //formにセットした登録情報をサーバーに送る
    document.getElementById("formSsoData2").submit();
}

////////////////////////////////////////////////
// 詳細画面の編集ボタン制御
////////////////////////////////////////////////
function showEditTable() {

    // 詳細画面からデータ取得
    var ssoBasicInfoData = [];
    $("#sso-basic-info td div").each(function(index, element){
        ssoBasicInfoData.push($(element).text());
    });

    $("#edit-provider-name").val(ssoBasicInfoData[0]);

    if(ssoBasicInfoData[1] == getMessage("MOSJA28011", false)){
        $("#edit-auth-type").val("0");
    }

    $("#edit-logo").text(ssoBasicInfoData[2]);

    if(ssoBasicInfoData[3] == getMessage("MOSJA28015", false)){
        $("#edit-visible-flag").val("0");
    } else {
        $("#edit-visible-flag").val("1");
    }

    var ssoAttriInfoData = [];
    $("#sso-attri-info td div").each(function(index, element){
        ssoAttriInfoData.push($(element).text());
    });

    $("#edit-clientid").val(ssoAttriInfoData[0]);
    $("#edit-clientsecret").val(ssoAttriInfoData[1]);
    $("#edit-authorizationur").val(ssoAttriInfoData[2]);
    $("#edit-accesstokenuri").val(ssoAttriInfoData[3]);
    $("#edit-resourceowneruri").val(ssoAttriInfoData[4]);
    $("#edit-scope").val(ssoAttriInfoData[5]);
    $("#edit-id").val(ssoAttriInfoData[6]);
    $("#edit-name").val(ssoAttriInfoData[7]);
    $("#edit-email").val(ssoAttriInfoData[8]);
    $("#edit-imageurl").val(ssoAttriInfoData[9]);
    $("#edit-proxy").val(ssoAttriInfoData[10]);
}

// 編集画面閉じたとき
function closeEdit() {
    // バリデーションエラー
    $(".error-list").remove();
    $("td").removeClass("error");
}

////////////////////////////////////////////////
//  DB登録 (更新)
////////////////////////////////////////////////
function submitTableData2(){

    var ssoInfo = {};

    $("#btnUpd").prop("disabled", true);
    if(confirm(getMessage('MOSJA28035', false)) == true){
        ssoInfo["provider_name"] = $("#edit-provider-name").val();
        ssoInfo["auth_type"] = $("#edit-auth-type").val();
        ssoInfo["logo"] = $("#edit-logo").val();
        ssoInfo["visible_flag"] = $("#edit-visible-flag").val();
        ssoInfo["clientid"] = $("#edit-clientid").val();
        ssoInfo["clientsecret"] = $("#edit-clientsecret").val();
        ssoInfo["authorizationuri"] = $("#edit-authorizationur").val();
        ssoInfo["accesstokenuri"] = $("#edit-accesstokenuri").val();
        ssoInfo["resourceowneruri"] = $("#edit-resourceowneruri").val();
        ssoInfo["scope"] = $("#edit-scope").val();
        ssoInfo["id"] = $("#edit-id").val();
        ssoInfo["name"] = $("#edit-name").val();
        ssoInfo["email"] = $("#edit-email").val();
        ssoInfo["imageurl"] = $("#edit-imageurl").val();
        ssoInfo["proxy"] = $("#edit-proxy").val();

        // 登録情報をjson形式に変換し、任意のvalueにセットする。
        var jstr = JSON.stringify({"sso_info": ssoInfo});
        $("#add-record2").val(jstr);
        $("#operate").val("save");

        // formにセットした登録情報をサーバーに送る
        document.getElementById("formSsoData2").submit();
    } else {
        $("#btnUpd").prop("disabled", false);
    }
}

function submitAction2(){

    // 前回エラー表記削除
    $('.error').removeClass('error');
    $('.error-list').remove();

    var operate = $("#operate").val();
    if( operate == "save" ){
        //保存時のアクション
        var ssoId = $("#hidSsoId2").val();

        $.ajax({
            type : "POST",
            url  : "sso_info/modify/" + ssoId + "/",
            data : $("#formSsoData2").serialize(),
            dataType: "json",
        })
        .done(function(response_json) {
            if(response_json.status == 'success') {
               alert(getMessage('MOSJA00011', false));
               beforeunloadThroughFlag = true;//ページ移動の注意を無視
               $("#btnUpd").prop("disabled", false);
                location.href = response_json.redirect_url;
            }
            else {
                alert(response_json.error_msg);

                // 基本情報エラー処理
                errorMsg = response_json.error_top;
                Object.keys(errorMsg).forEach(function(id) {
                    errorStr = errorMsg[id];

                    if(!errorStr || errorStr.length == 0) {
                        return true;
                    }
                    // エラークラスを付与
                    errid = id.replace(/_/g, "-");
                    nonInput($("#edit-"+errid), getMessage('MOSJA00097', false), errorMsg[id]);
                });
                $("#btnUpd").prop("disabled", false);
            }
        })
        .fail(function(respdata, stscode, resp) {
            if(stscode == "error") {
                alert(getMessage('MOSJA00014', false));
                $("#btnUpd").prop("disabled", false);
                window.location.href = "/oase_web/top/logout";
            } else {
                alert(getMessage('MOSJA00014', false) + "\n" + respdata.responseText);
                $("#btnUpd").prop("disabled", false);
            }
        });
    }

    if( operate == "delete" ){
      //削除時のアクション
      var ssoInfoID        = $("#hidSsoId2").val();
      var providerName = $("#hid-provider-name").val();
      message = getMessage('MOSJA28069', false)
      message = message.replace(/provider_name/g, providerName);

      if(confirm(message) == true){
            $.ajax({
                type : "POST",
                url  : "sso_info/delete_sso/" + ssoInfoID + "/",
                data : $("#formSsoData2").serialize(),
                dataType: "json",
            })
            .done(function(response_json) {
                if(response_json.status == 'success') {
                    alert(getMessage('MOSJA00200', false));
                    $("#btnDelAccess").prop("disabled", false);
                    location.href = response_json.redirect_url;
                }
                else {
                    alert(response_json.error_msg);
                    $("#btnDelSso").prop("disabled", false);
                }
            })
            .fail(function(respdata, stscode, resp) {
                if(stscode == "error") {
                    alert(getMessage('MOSJA00014', false));
                    $("#btnDelSso").prop("disabled", false);
                    window.location.href = "/oase_web/top/logout";
                } else {
                    alert(getMessage('MOSJA00014', false) + "\n" + respdata.responseText);
                    $("#btnDelSso").prop("disabled", false);
                }
            });
      } else {
            $("#btnDelSso").prop("disabled", false);
      }
    }
}
