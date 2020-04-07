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
 * OASE Input Validation Check JavaScript
 *
 *
 * ************************************************** */

$( function(){

let $container = $('#container');

let $counter, inputWidth, parentWidth, inputposition, focusValue,
    maxlength, minlength, inputType, wordCount, wordCountHtml;

let wordArray, updataCount;

$container.on('focus.validationCheck', '.validation-input', function(){

if( inputValidationThroughFlag === false ) {

    let $thisInput = $( this );
    
    // input要素判定
    if( $thisInput.is('input, textarea') ) {

      // カウント表示用要素の追加
      $thisInput.after('<div class="oase-word-count"></div>');
      $counter = $('.oase-word-count');

      inputWidth = $thisInput.innerWidth(),
      parentWidth = $thisInput.parent().innerWidth(),
      inputposition = $thisInput.position(),
      focusValue = $thisInput.val(),
      maxlength = 0,
      minlength = 0,
      inputType = $thisInput.attr('data-type'),
      wordCount = 0,
      wordCountHtml = '';

      // 文字数カウント用に文字列を配列化（サロゲートペア対応）
      wordArray = function( str ){
          return str.match(/[\uD800-\uDBFF][\uDC00-\uDFFF]|[^\uD800-\uDFFF]/g) || [];
      }

      // 文字数を更新
       updataCount = function(){
          wordCount = wordArray( $thisInput.val() ).length;

          wordCountHtml = '';
          if ( maxlength !== 0 ) {
              wordCountHtml = ' / ' + maxlength;
          }

          if ( ( maxlength !== 0 && maxlength < wordCount ) || ( minlength !== 0 && minlength > wordCount ) ) {
              wordCountHtml = '<span class="over">' + wordCount + '</span>' + wordCountHtml;
          } else {
              wordCountHtml = wordCount + wordCountHtml;
          }

          $counter.html( wordCountHtml );
      }

      // 最大文字数を取得
      if ( $thisInput.attr('data-maxlength') !== undefined ) {
          maxlength = $thisInput.attr('data-maxlength');
      }

      // 最小文字数を取得
      if ( $thisInput.attr('data-minlength') !== undefined ) {
          minlength = $thisInput.attr('data-minlength');
      }

      updataCount();
      $counter.css({
          'top':  -$counter.height() + inputposition.top + 1,
          'right': parentWidth - inputWidth - inputposition.left
      });

      // keypress keyupで文字数カウント
      $thisInput.on('keypress.wordCount keyup.wordCount' , function(){
          updataCount();
      });
    
    }

    // フォーカスが外れたら・・・
    $thisInput.on('blur.validationCheck', function(){

        let $blurInput = $( this );
        $blurInput.off('keypress.wordCount keyup.wordCount focus.validationCheck blur.validationCheck');

        let value = $blurInput.val(),
            errorList = [],
            checkType = [];
        if( $thisInput.is('input, textarea') ) {

          /* input or textarea */
           
          $counter.remove();

          /* ************************************************** *
           * 自動処理ここから */

          // 頭尾のスペースは削除する
          value = value.replace(/^\s+|\s+$/g, '');

          $blurInput.val( value );
          updataCount();

          let noinputError = getMessage('MOSJA00095', false); //未入力エラー
          let inputError = getMessage('MOSJA00098', false); //入力エラー
          let formatError = getMessage('MOSJA00218', false); //形式エラー
          let reservedError = getMessage('MOSJA00219', false); //予約語エラー
          let initialError = getMessage('MOSJA00220', false); //頭文字エラー
          let overError = getMessage('MOSJA00221', false); //文字数オーバー
          let lessError = getMessage('MOSJA00222', false); //文字数不足
          let noselectError = getMessage('MOSJA00223', false); //未選択エラー

          /* 自動処理ここまで *
           * ************************************************** */

          // 変更がなければ基本チェックをスルーする
          if ( focusValue !== value ) {

            // エラー表示削除
            $blurInput.closest('.cell-inner').find('.error-list').remove();
            $blurInput.closest('th, td').removeClass('error');

            /* ************************************************** *
             * 基本チェックここから */
            
            // ログインID
            checkType = ['loginID'];
            if ( checkType.indexOf( inputType ) !== -1 ) {
              if ( value.search(/^[a-zA-Z0-9.@_\-]+$/) === -1 && value !== '' ) {
                errorList.push([inputError, getMessage('MOSJA00224', false)]);
              }
            }
            // メールアドレス
            checkType = ['mail'];
            if ( checkType.indexOf( inputType ) !== -1 ) {
              if ( value.search(/^([\w!#$%&'*+\-\/=?^`{|}~]+(\.[\w!#$%&'*+\-\/=?^`{|}~]+)*|"([\w!#$%&'*+\-\/=?^`{|}~. ()<>\[\]:;@,]|\\[\\"])+")@(([a-zA-Z\d\-]+\.)+[a-zA-Z]+|\[(\d{1,3}(\.\d{1,3}){3}|IPv6:[\da-fA-F]{0,4}(:[\da-fA-F]{0,4}){1,5}(:\d{1,3}(\.\d{1,3}){3}|(:[\da-fA-F]{0,4}){0,2}))\])$/) === -1 && value !== '' ) {
                errorList.push([formatError, getMessage('MOSJA00225', false)]);
              }
            }
            // 複数メールアドレス
            checkType = ['multiaddress'];
            if ( checkType.indexOf( inputType ) !== -1 ) {
              let errorFlag = false;
              let multiMailValue = value.split(';');
              multiMailValue.forEach(function(mail) {
                mail = mail.trim();
                if ( mail.search(/^([\w!#$%&'*+\-\/=?^`{|}~]+(\.[\w!#$%&'*+\-\/=?^`{|}~]+)*|"([\w!#$%&'*+\-\/=?^`{|}~. ()<>\[\]:;@,]|\\[\\"])+")@(([a-zA-Z\d\-]+\.)+[a-zA-Z]+|\[(\d{1,3}(\.\d{1,3}){3}|IPv6:[\da-fA-F]{0,4}(:[\da-fA-F]{0,4}){1,5}(:\d{1,3}(\.\d{1,3}){3}|(:[\da-fA-F]{0,4}){0,2}))\])$/) === -1 && value !== '' ) {
                  errorFlag = true;
                  return false; // = break;
                }
              });
              if ( errorFlag ) {
                errorList.push([formatError, getMessage('MOSJA00225', false)]);
              }
            }
            // IPアドレス
            checkType = ['ip'];
            if ( checkType.indexOf( inputType ) !== -1 ) {
              if ( value.search(/^(([\*]|[1-9]?[0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.){3}([1-9]?[\*0-9]|1[0-9][\*0-9]|2[0-4][\*0-9]|25[\*0-5])$/) === -1 && value !== '' ) {
                errorList.push([formatError, getMessage('MOSJA00226', false)]);
              }
            }
            // サロゲートペアが含まれているか
            checkType = ['text'];
            if ( checkType.indexOf( inputType ) !== -1 ) {
              if ( value.search(/[\uD800-\uDBFF][\uDC00-\uDFFF]/) !== -1 ) {
                  // サロゲートペア抽出
                  let surrogatePair = '';
                  value.match(/[\uD800-\uDBFF][\uDC00-\uDFFF]/g).forEach( function( value ){
                    if ( surrogatePair.indexOf( value ) === -1 ) {
                      surrogatePair += '[' + value + ']';
                    }
                  });
                  let surrogateError = getMessage('MOSJA00227', false).replace("{}", surrogatePair);
                  errorList.push([inputError, surrogateError]);
              }
            }
            // oase password
            checkType = ['password'];
            if ( checkType.indexOf( inputType ) !== -1 ) {
              if ( value.search(/^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!#$%&()*+,-./;<=>?@\[\]^_{}|~]).{8,}$/) === -1 && value !== '' ) {
                errorList.push([formatError,getMessage('MOSJA00228', false)]);
              }
            }
            // 予約語が含まれているか
            checkType = ['ruleTableName'];
            if ( checkType.indexOf( inputType ) !== -1 ) {
              // 予約語
              let reservedWord = /~abstract$|^assert$|^boolean$|^break$|^byte$|^case$|^catch$|^char$|^class$|^const$|^continue$|^default$|^do$|^double$|^else$|^enum$|^extends$|^final$|^finally$|^float$|^for$|^goto$|^if$|^implements$|^import$|^instanceof$|^int$|^interface$|^long$|^native$|^new$|^package$|^private$|^protected$|^public$|^return$|^short$|^static$|^strictfp$|^super$|^switch$|^synchrnized$|^this$|^throw$|^throws$|^transient$|^try$|^void$|^volatile$|^while$|^true$|^false$|^null$/;
              if ( value.match( reservedWord )) {
                  let reservedErrorMsg = getMessage('MOSJA00229', false).replace("{}",value);
                  errorList.push([reservedError, reservedErrorMsg]);
              }
            }
            // 頭文字が数字になっているか
            checkType = ['ruleTableName'];
            if ( checkType.indexOf( inputType ) !== -1 ) {
              if ( value.search(/^[0-9]/) !== -1) {
                  errorList.push([initialError, getMessage('MOSJA00230', false)]);
              }
            }
            // 英数字以外が含まれているか
            checkType = ['ruleTableName'];
            if ( checkType.indexOf( inputType ) !== -1 ) {
              if ( value.search(/^[a-zA-Z0-9]+$/) === -1 && value !== '' ) {
                  errorList.push([inputError, getMessage('MOSJA00231', false)]);
              }
            }

            // 全角文字がふくまれているか
            checkType = [];
            if ( checkType.indexOf( inputType ) !== -1 ) {
              if ( value.search(/[\u3040-\u30ff]/) !== -1) {
                errorList.push([inputError, getMessage('MOSJA00232', false)]);
              }
            }
            // 半角カタカナがふくまれているか
            checkType = [];
            if ( checkType.indexOf( inputType ) !== -1 ) {
              if ( value.search(/[\uff65-\uff9f]/) !== -1) {
                errorList.push([inputError, getMessage('MOSJA00233', false)]);
              }
            }
            // 文字数がオーバーしているか
            if ( maxlength !== 0 ) {
              if ( maxlength < wordCount ) {
                  let overErrorMsg = getMessage('MOSJA00234', false).replace("{0}",wordCount-maxlength).replace("{1}",maxlength);
                  errorList.push([overError, overErrorMsg]);
              }
            }
            // 文字数がショートしているか
            if ( minlength !== 0 ) {
              if ( minlength > wordCount && wordCount !== 0 ) {
                  let lessErrorMsg = getMessage('MOSJA00235', false).replace("{0}",minlength-wordCount).replace("{1}",minlength);
                  errorList.push([lessError, lessErrorMsg]);
              }
            }

            }

          /* 基本チェックここまで *
           * ************************************************** */

          /* ************************************************** *
          * システム設定画面ここから */

            // メール通知先ログインID
            checkType = ['loginIDs'];
            if ( checkType.indexOf( inputType ) !== -1 ) {
              // 使用不可文字の判定
              if ( value.search(/^[a-zA-Z0-9.@_\-,]+$/) === -1 && value !== '' ) {
                errorList.push([inputError, getMessage('MOSJA00224', false)]);
              }
              
              let inputLoginIds = []
              // カンマがある場合
              if (value.indexOf(',') !== -1) {
                inputLoginIds = value.split(',');
              }
              else {
                inputLoginIds[0] = value;
              }
              if(inputLoginIds !== "" ){
                for (let i=0; i<inputLoginIds.length; i++){
                  loginId = inputLoginIds[i];
                  // 0文字以上32文字以内で入力されているか
                  if(loginId.length <= 0 || loginId.length > 32 ) {
                    errorList.push([inputError, getMessage('MOSJA09000', false)]); 
                  }
                }
              }
            }

            // AD連携時刻が00～23で入力されているか 
            checkType = ['adLinkageTimer'];
            if ( checkType.indexOf( inputType ) !== -1 ) {
              let resArray = value.split(",");

              for( i=0; i<resArray.length; i++ ) {
                if ( resArray[i].length !== 2 && value !== '' ) {
                    errorList.push([inputError, getMessage('MOSJA09001', false)]);
                }
                else {
                    data = resArray[i].match(/^([01]?[0-9]|2[0-3])$/);
                    if( !data && value !== '' ) {
                        errorList.push([inputError, getMessage('MOSJA09001', false)]);
                    }
                }
              }
            }
          /* システム設定画面ここまで *
          * ************************************************** */

          /* ************************************************** *
          * システム設定画面ここから */
            // サロゲートペアが含まれているか
            checkType = ['condition_name'];
            if ( checkType.indexOf( inputType ) !== -1 ) {
              if ( value.search(/[\uD800-\uDBFF][\uDC00-\uDFFF]/) !== -1 ) {
                  // サロゲートペア抽出
                  let surrogatePair = '';
                  value.match(/[\uD800-\uDBFF][\uDC00-\uDFFF]/g).forEach( function( value ){
                    if ( surrogatePair.indexOf( value ) === -1 ) {
                      surrogatePair += '[' + value + ']';
                    }
                  });
                  let surrogatePairErrorMsg = getMessage('MOSJA00227', false).replace("{}",surrogatePair);
                  errorList.push([inputError, surrogatePairErrorMsg]);
              }
            }
            // 記号チェック
            checkType = ['condition_name'];
            if ( checkType.indexOf( inputType ) !== -1 ) {
              if ( value.search(/[\u0021-\u002F]|[\u003A-\u0040]|[\u005B-\u0060]|[\u007B-\u007E]|[\uFF01-\uFF0F]|[\uFF1A-\uFF20]|[\uFF3B-\uFF40]|[\uFF5B-\uFF5E]/) !== -1 ) {
                errorList.push([inputError, getMessage('MOSJA00106', false)]);
              }
            }

          // 必須チェック
          if ( inputErrorThroughFlag === false ) {
            let requiredFlg = ( $thisInput.attr('required') === undefined ) ? false : true;
            if ( requiredFlg && value === '' ) {
                errorList.push([noinputError, getMessage('MOSJA00003', false)]);
            }
          }
        
        } else if( $thisInput.is('select') ) {
        
          /* select */
        
          // エラー表示削除
          $blurInput.closest('.cell-inner').find('.error-list').remove();
          $blurInput.closest('th, td').removeClass('error');
          
          // select選択チェック
          if ( inputErrorThroughFlag === false ) {
            let requiredSelectFlg = ( $thisInput.attr('required') === undefined ) ? false : true;
            if ( requiredSelectFlg && value === null ) {
              errorList.push([noselectError, getMessage('MOSJA00015', false)]);
            }
          }
          
        }

        // エラーがあれば表示する
        if ( errorList[0] ) {
          $blurInput.closest('.cell-inner').find('.error-list').remove();
          $blurInput.closest('th, td').addClass('error');
          let errorHTML = '<ul class="error-list">';
            errorList.forEach( function( value ){
              errorHTML += '<li><em class="owf owf-cross"></em>' + value[0] + '<span class="tooltip help" title="' + value[1] + '"><em class="owf owf-question"></em></span></li>';
            });
            errorHTML += '</ul>';
          $blurInput.closest('.cell-inner').append( errorHTML );
        }

    });

} // inputValidationThroughFlag

});

});
