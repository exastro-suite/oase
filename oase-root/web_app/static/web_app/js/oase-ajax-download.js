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

// JavaScript Document

/* ************************************************** *
 *
 *
 * OASE AJAX DOWNLOAD JavaScript
 *
 *
 * ************************************************** */



/* ************************************************** *
 *
 * グローバル変数
 *
 * ************************************************** */
 


/* ************************************************** *
 *
 * ダウンロード処理(エクセル)
 *
 * ************************************************** */
function downloadAjaxExcel(btnId, url) {

  ajaxData = {
    type: 'GET',
    url: url,
    dataType: 'binary',
    xhrFields: {responseType : 'blob'},
  }

  downloadAjaxAction(btnId, ajaxData);
}


/* ************************************************** *
 *
 * ダウンロード処理(テキスト)
 *
 * ************************************************** */
function downloadAjaxText(btnId, url) {

  ajaxData = {
    type: 'GET',
    url: url,
  }

  downloadAjaxAction(btnId, ajaxData);
}


/* ************************************************** *
 *
 * ajaxを使用したダウンロード処理
 *
 * ************************************************** */
function downloadAjaxAction(btnId, ajaxData) {
  $.ajax(
      ajaxData
    )
  .done(function(data, status, jqXHR) {

    let contentTypeHeader = jqXHR.getResponseHeader("Content-Type");
    let blob = new Blob([ data ], { "type" : contentTypeHeader });
    let disposition = jqXHR.getResponseHeader('Content-Disposition');
    if (disposition && disposition.indexOf('attachment') !== -1) {
      let fileNameRegex = /filename[^;=\n]*=(UTF-8(['"]*))?(.*)/;
      // matches[0]:マッチした文字列
      // 以降の各要素は、括弧指定にそれぞれマッチした文字列が格納されている.
      let matches = fileNameRegex.exec(disposition);
      if (matches !== null && matches[3]) {
        // ファイル名部分を抜き出す
        fileName = decodeURI(matches[3].replace(/['"]/g, ''));
      }
    }

    // ブラウザ判定用
    let agent = window.navigator.userAgent.toLowerCase();
    if (window.navigator.msSaveBlob) { 
      // IE
      window.navigator.msSaveBlob(blob, fileName); 
    } else if (agent.indexOf('firefox') !== -1) {
      // Firefox
      let aTag = document.createElement("a");
      aTag.download = fileName;
      aTag.href = window.URL.createObjectURL(blob);
      document.body.appendChild(aTag);
      aTag.click();
      document.body.removeChild(aTag);
    } else if ((agent.indexOf('chrome') !== -1) && (agent.indexOf('edge') === -1)  && (agent.indexOf('opr') === -1)) {
      // Chrome
      let aTag = document.createElement("a");
      aTag.download = fileName;
      aTag.href = window.URL.createObjectURL(blob);
      aTag.click();
    }
  })
  .fail(function(data, status, jqXHR) {
    alert(getMessage("MOSJA00203", false));
    window.location.href = "/oase_web/top/logout";
  })
  .always(function(respdata) {
    $(btnId).prop("disabled", false);
  });
}





