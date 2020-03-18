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
 * OASE COMMON JavaScript
 *
 *
 * ************************************************** */



/* ************************************************** *
 *
 * グローバル変数
 *
 * ************************************************** */
 
// true の場合、[.change-value]が存在してもページ移動時に警告を出さない
let beforeunloadThroughFlag = false;

// true の場合、必須エラー表示をスキップする
let inputErrorThroughFlag = false;

// true の場合、バリデーションチェックをスキップする
let inputValidationThroughFlag = false;

$(function(){

/* ************************************************** *
 *
 * Form Change Check
 *
 * ************************************************** */

  // 保存ボタンにaddClass .save ＆ disabled

let save_conditions = 'button:contains("' + getMessage("MOSJA00021", false) + '"), button:contains("' + getMessage("MOSJA00204", false) + '")';
$(save_conditions).addClass('save').prop('disabled', true );

// ボタン操作でフォーカスが外れる場合は必須エラー表示をスキップさせる
$('.oase-main').on({
  'mouseenter' : function() {
    inputErrorThroughFlag = true;
  },
  'mouseleave' : function() {
    inputErrorThroughFlag = false;
  }
},'button');

/* ************************************************** *
 * 初めてフォーカスが当たった時、初期値を保存し、
 * フォーカスが外れた時、変更があった場合にclass[change-value] */
 
// チェックする要素
let checkForm = 'input[type="text"], input[type="number"], input[type="password"], select, textarea';
// 除外する要素
let exclusionForm = '.execution-log, .filter *, .oase-table-footer *, .staging-select, .ignore-change-value';

$('.oase-main').on({

  'focus' : function() {

    let $focus = $( this );
    let value = $focus.val();
    
    if ( value === null ) value = '';

    if ( !$focus.is( exclusionForm ) ) {
      // 初期値、attr[data-initial-value]を追加
      if ( $focus.attr('data-initial-value') === undefined ) {
        $focus.attr('data-initial-value', value );
      }
    }

  },
  
  'input change' : function() {

    let $focus = $( this );
    let value = $focus.val();
    
    if ( value === null ) value = '';
    
    if ( !$focus.is( exclusionForm ) ) {
    
      value = value.replace(/^\s+|\s+$/g, '');

      if ( $focus.attr('data-initial-value') !== undefined ) {
        // 初期値と変わった場合にclass[change-value]を付ける
        if ( value !== $focus.attr('data-initial-value') ) {
          $focus.addClass('change-value');
        } else {
          $focus.removeClass('change-value');
        }
      }
    }
    
    saveButtonJudgment( $( this ) );
    
  }

}, checkForm );

/* ************************************************** *
 * 読み込み時にinput[type="number"]は初期値を保存しておく */

$('input[type="number"]').each( function(){
  
  let $input = $( this );

  let value = $input.val();
  if ( value === null ) value = '';

  $input.attr('data-initial-value', value );

});

/* ************************************************** *
 * Radioボタン 変更チェック */
 
// チェックする要素
let checkRadio = 'input[type="radio"]';

$('.oase-main').on({

  'focus' : function() {

    let name = $( this ).attr('name');
    let $focus = $( checkRadio ).filter('[name="' + name + '"]');

    if( $( this ).attr('data-initial-value') === undefined ) {
      $focus.attr('data-initial-value', 'off');
      $focus.filter(':checked').attr('data-initial-value', 'on');
    }

  },
  
  'change' : function() {

    let name = $( this ).attr('name');
    let $focus = $( checkRadio ).filter('[name="' + name + '"]');

    if ( $( this ).attr('data-initial-value') === 'on' ) {
      $focus.filter('[data-initial-value="on"]').removeClass('change-value');
    } else {
      $focus.filter('[data-initial-value="on"]').addClass('change-value');
    }
    
    saveButtonJudgment( $( this ) );
    
  }

}, checkRadio );

/* ************************************************** *
 * checkbox 変更チェック */
 
// チェックする要素
let checkCheckbox = 'input[type="checkbox"]';

$('.oase-main').on({

  'focus' : function() {
    let $focus = $( this );
    if ( $focus.attr('data-initial-value') === undefined ) {
      let value = ( $focus.prop('checked') ) ? 'on' : 'off';
      $focus.attr('data-initial-value', value );
    }
  },

  'change' : function() {
    let $focus = $( this );
    if ( $focus.attr('data-initial-value') !== undefined ) {
      // 初期値と変わった場合にclass[change-value]を付ける
      let value = ( $focus.prop('checked') ) ? 'on' : 'off';
      if ( value !== $focus.attr('data-initial-value') ) {
        $focus.addClass('change-value');
      } else {
        $focus.removeClass('change-value');
      }
    }
    
    saveButtonJudgment( $( this ) );
    
  }

}, checkCheckbox );

/* ************************************************** *
 * 変更がある場合（.change-value）ウインドウを閉じる時に確認する */

$( window ).on('beforeunload', function(){

  if ( $('.change-value').length && beforeunloadThroughFlag === false ) {
      return getMessage("MOSJA00205", false);
  }
  
});

/* ************************************************** *
 * パスワード可視化 */

let passwordShowFocusFlag = false;

$('.password-show').on({

  'touchstart mouseenter' : function() {

    let $passwordInput = $( this ).prevAll('input[type="password"]');

    $passwordInput.attr('type', 'text');
    $passwordInput.attr('readonly', true);

    // for IE
    if(ie11Check()) {
      // フォーカスが当たっていた場合、フラグをオンにしフォーカスを外す
      if( $passwordInput.is(':focus') ){
        passwordShowFocusFlag = true;
        $passwordInput.select();
        let endPoint = $passwordInput.get(0).selectionEnd;
        $passwordInput.get(0).setSelectionRange(endPoint, endPoint);
      }
    }
  },

  'touchend mouseleave' : function(){

    let $passwordInput = $( this ).prevAll('input[type="text"]');

    $passwordInput.attr('type', 'password');
    $passwordInput.attr('readonly', false);

    // for IE
    if(ie11Check()) {
      // フォーカスを当てなおす
      if( passwordShowFocusFlag === true ){
        $passwordInput.select();
        let endPoint = $passwordInput.get(0).selectionEnd;
        $passwordInput.get(0).setSelectionRange(endPoint, endPoint);
        passwordShowFocusFlag = false;
      }
    }
  }

});

/* ************************************************** *
 * ボタンスイッチ切り替え */
 
$('.oase-main').on('click', '.oase-button.switch', function(){
  $( this ).toggleClass('on');
});

});/* / $function */





$( window ).on('load', function() {

/* ************************************************** *
 *
 * Title Menu Overflow Check
 *
 * ************************************************** */

/* ************************************************** *
 * タイトルメニューがウインドウサイズの変更で隠れる場合、切り替える */
 
let $checkMenu = $('.oase-main-header, .oase-section-title'),
    overflowHTML = '<div class="overflowMenuButton"><button class="oase-mini-button tooltip" title="' + getMessage("MOSJA00206", false) + '"><em class="owf owf-select"></em></button></div>';

let menuOverflowCheck = function() {

$checkMenu.each( function(){
  let $thisElement = $( this );
  let parentHeight = $thisElement.outerHeight(),
      childHeight = $thisElement.children().outerHeight();
  if ( parentHeight < childHeight ) {
    $thisElement.addClass('overflowMenu');
    $thisElement.children().append( overflowHTML );
    $thisElement.find('.overflowMenuButton').on('click', function(){
      $( this ).prevAll('.oase-main-menu, .oase-section-title-menu').toggleClass('menuOpen');
    });
  }
});

}
let menuOverflowReset = function() {
  $('.overflowMenu').removeClass('overflowMenu');
  $('.overflowMenuButton').remove();
}

/* ************************************************** *
 *
 * タブ切り替えレイアウト
 *
 * ************************************************** */

let tabLayout = function() {

  if ( $('.oase-tab-table').length ) {

    let openTabNum = 0,
        openTab = getParam('opentab');

    if ( openTab ) openTabNum = $('[id^=' + openTab + ']').index('section');
    if ( openTabNum === -1 ) openTabNum = 0;

    $('.oase-tab-menu a').eq( openTabNum ).addClass('open');
    $('section').eq( openTabNum ).addClass('open');

    $('.oase-tab-menu a').on('click', function( e ){
      e.preventDefault();

      let $openTab = $( $( this ).addClass('open').attr('href') );

      $('.oase-tab-menu a.open, section.open').removeClass('open');

      $openTab.add( this ).addClass('open');

      tableThFixedReset();
      tableThFixed();

    });

  }
  
}

/* ************************************************** *
 *
 * 上下分割・左右分割レイアウト切り替え
 *
 * ************************************************** */

let divisionLayout = function() {

  if ( $('.division-2').length || $('.division-vertical2').length ){
    
    // section h2 取得
    let sectionTitle = [];
    $('.oase-section-title-table h2').each( function(){
      sectionTitle.push( $( this ).text() );
    });
    /* レイアウト切り替えメニュー 追加HTML */
    let layoutChangeMenu = ''
    + '  <div class="oase-layout-change-menu">'
    + '    <ul>'
    + '      <li><input id="vertical" type="radio" name="layout" value="division-vertical2"><label class="tooltip" title="' + getMessage("MOSJA12052", false) + '" for="vertical"><span></span>  </label></li>'
    + '      <li><input id="horizontal" type="radio" name="layout" value="division-2" checked><label class="tooltip" title="' + getMessage("MOSJA12053", false) + '" for="horizontal"><span></span></label></li>'
    + '      <li><input id="section1" type="radio" name="layout" value="section1"><label class="tooltip" title="' + sectionTitle[0] + '" for="section1"><span></span></label></li>'
    + '      <li><input id="section2" type="radio" name="layout" value="section2"><label class="tooltip" title="' + sectionTitle[1] + '" for="section2"><span></span></label></li>'
    + '    </ul>'
    + '  </div>';

    // サイズ変更用要素の追加
    $('.division-2 section:eq(0)').append('<div class="sizeChange"></div>')

    // フッターにメニューを追加
    $('.oase-footer-switch').append( layoutChangeMenu );

    $('.oase-layout-change-menu input[name="layout"]').on('change', function(){

      let layoutType = $( this ).val();

      $('.oase-main').removeClass('division-2 division-vertical2 section1 section2').addClass( layoutType );

      $.when(

        menuOverflowReset(),
        tableThFixedReset()

      ).done( function(){

        menuOverflowCheck();
        tableThFixed();

      });

    });

    $('.sizeChange').on('mousedown', function( mouseDownE ){

      let $section1 = $('section').eq( 0 ),
          $section2 = $('section').eq( 1 ),
          initialPoint = mouseDownE.clientY,
          movePoint = 0,
          minHeight = 184,
          newSection1Height = 0,
          newSection2Height = 0;

      // 高さを一旦固定値に
      $('section').each( function(){
        $( this ).css('height', $( this ).outerHeight() );
      });

      let initialSection1Height = newSection1Height = $section1.outerHeight(),
          initialSection2Height = newSection2Height = $section2.outerHeight();

      let initialHeight = initialSection1Height + initialSection2Height;

      $( window ).on({

        'mousemove.sizeChange' : function( mouseMoveE ){

          movePoint = mouseMoveE.clientY - initialPoint;

          if ( initialSection1Height + movePoint > minHeight && initialSection2Height - movePoint > minHeight ) {
            newSection1Height = initialSection1Height + movePoint;
            $section1.css('height', newSection1Height );
            newSection2Height = initialSection2Height - movePoint;
            $section2.css('height', newSection2Height );
          }
        },

        'mouseup.sizeChange' : function(){
          $( window ).off('mousemove.sizeChange mouseup.sizeChange');
          // 高さを割合に戻す
          $section1.css('height', newSection1Height / initialHeight * 100 + '%' );
          $section2.css('height', newSection2Height / initialHeight * 100 + '%' );
        }
      });   

    });

  }

}

/* ************************************************** *
 *
 * Window Resize Event
 *
 * ************************************************** */

let windowResizeTimer = false,
    windowResizeFlag = false;

$( window ).on('resize', function() {

if ( windowResizeTimer !== false ) {
  clearTimeout( windowResizeTimer );
}

if ( windowResizeFlag === false ) {
/* ************************************************** *
* Window Resize Start */

menuOverflowReset();
tableThFixedReset();

}

windowResizeTimer = setTimeout( function() {
/* ************************************************** *
* Window Resize End */

menuOverflowCheck();
tableThFixed();

}, 200);

});/* / $window resize */

/* ************************************************** *
 *
 * 画面初期設定
 *
 * ************************************************** */
 
$.when(

  tabLayout(),
  tableInitialize()

).done( function(){

  tableThFixed();
  tableRowCount();
  menuOverflowCheck();
  divisionLayout();

});

});/* / window.load */








/* ************************************************** *
 *
 * IE11チェック
 *
 * ************************************************** */
function ie11Check() {
  let ua = window.navigator.userAgent.toLowerCase();
  return ( ua.indexOf('trident/7') !== -1 );
}
/* ************************************************** *
 *
 * Edgeチェック
 *
 * ************************************************** */
function edgeCheck() {
  let ua = window.navigator.userAgent.toLowerCase();
  return ( ua.indexOf('edge') !== -1 );
}
/* ************************************************** *
 *
 * table th 固定
 *
 * ************************************************** */
function tableThFixedReset() {
  $('.oase-table').css('visibility', 'hidden').find('thead th, .cell-inner').css('width','');
}
function tableThFixed() {
  $('.oase-table').addClass('resize');
  if ( ie11Check() ) {
    $('.oase-table-header-fixed').each( function() {
    
      $( this ).css('padding-right', 17 );
      
      let $parentTable = $( this ).prevAll().find('thead'); 
      $( this ).find('th').each( function( i ) {
        let thWidth = $parentTable.find('th').eq( i ).innerWidth();
        $parentTable.find('th').eq( i ).css('width', thWidth ).find('.cell-inner').css('width', thWidth );
        $( this ).css('width', thWidth ).find('.cell-inner').css('width', thWidth );
      });
      
      let scrollLeft = $( this ).closest('.oase-table-inner').scrollLeft();
      $( this ).children().scrollLeft( scrollLeft );
      
    });
  } else {
    $('.oase-table thead th').each( function(){
      let thWidth = $( this ).innerWidth();
      $( this ).css('width', thWidth ).find('.cell-inner').css('width', thWidth );
    });
  }
  $('.oase-table').removeClass('resize').css('visibility', 'visible');
}
/* ************************************************** *
 *
 * 特定のパラメータを取得
 *
 * ************************************************** */
function getParam( name ) {
  
  let url = window.location.href,
      regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)");
  
  let results = regex.exec( url );

  if( !results ) return null;
  return decodeURIComponent( results[2] );
}
/* ************************************************** *
 *
 * タグエスケープ
 *
 * ************************************************** */
function textEntities( text ) {

  let entities = [
        ['&', 'amp'],
        ['\"', 'quot'],
        ['\'', 'apos'],
        ['<', 'lt'],
        ['>', 'gt'],
      ];

  for ( let i = 0; i < entities.length; i++ ) {
    text = text.replace( new RegExp( entities[i][0], 'g'), '&' + entities[i][1] + ';' );
  }
  text = text.replace(/^\s+|\s+$/g, '');
  return text;

}
/* ************************************************** *
 *
 * ヒアドキュメントっぽく
 *
 * ************************************************** */
function heredocHTML( text ) {
  return text.toString().match(/[^]*\/\*([^]*)\*\/\}$/)[1];
}
/* ************************************************** *
 *
 * beforeunloadThroughFlagのセッター
 *
 * ************************************************** */
function setbeforeunloadThroughFlag(value) {
    beforeunloadThroughFlag = value;
}
/* ************************************************** *
 *
 * 保存ボタンの disabled 制御
 *
 * ************************************************** */
function saveButtonJudgment( $checkElm ) {

  setTimeout( function(){
    // チェックする領域
    let $checkArea, $saveButton,
        requiredAllFlg = true,
        configFlg = false;
    if ( $checkElm.closest('.oase-modal').length ) {
      // モーダル
      $checkArea = $checkElm.closest('.oase-modal');
      $saveButton = $checkArea.find('button.save');
    } else if ( $checkElm.closest('.oase-table').length ) {
      // 基本画面
      $checkArea = $checkElm.closest('section');
      $saveButton = $checkArea.closest('.oase-main').find('.oase-main-header button.save');
    } else if ( $checkElm.closest('.oase-config-body').length ) {
      $checkArea = $checkElm.closest('section');
      $saveButton = $checkArea.find('button.save');
      configFlg = true;
    } else {
      return false;
    }      

    if ( $saveButton.length ) {
      if ( configFlg === false ) {
        // 必須項目チェック
        $checkArea.find('[required]').each( function(){
          // ダミー要素の中はチェックしない
          if ( !$( this ).is('[id$="_dummy"] *') ) {
            if( !$( this ).val() ) {
              requiredAllFlg = false;
              return false;
            }
          }
        });

        // .error-listが無い + .change-valueが1以上 + 必須項目が全て入力済で保存ボタン活性化
        if ( $checkArea.find('.error-list').length === 0 && 
             $checkArea.find('.change-value').length >= 1 && 
             requiredAllFlg === true ) {
          $saveButton.prop('disabled', false );
        } else {
          $saveButton.prop('disabled', true );
        }
        
        /*window.console.log(
        'ERROR-LIST:' + $checkArea.find('.error-list').length
        + ' | CHANGE-VALUE:' + $checkArea.find('.change-value').length
        + ' | REQUIRED-ALL:' + requiredAllFlg );*/

      } else {

        // 設定画面チェック
        let blankCount = 0;    

        if ( $checkArea.is('#oase-config-user-email,#oase-config-user-password,#oase-config-active-directory') ) {
          $checkArea.find('input').not('[type="hidden"],:hidden').each( function(){
            if( $( this ).val() === '' ) blankCount++;
          });
        }

        // change-value＋エラー無し＋空白無しで保存ボタン活性化
        if ( !$checkArea.find('.error-list').not('[type="hidden"],:hidden').length
              && $checkArea.find('.change-value').not('[type="hidden"],:hidden').length
              && blankCount === 0 ) {
          $checkArea.find('.oase-config-footer button').prop('disabled', false );
        } else {
          $checkArea.find('.oase-config-footer button').prop('disabled', true );
        }

      } 
    }
  }, 10 );

}
/* ************************************************** *
 *
 * Polling Timer
 *
 * ************************************************** */
function footerPollingTimer() {
  let pollingTimerHTML = heredocHTML ( function(){/*
  <div class="oase-polling-switch">
    <button class="tooltip oase-button switch" title="{0}">
      <em class="owf owf-update"></em><span>{0}</span><span class="on-off"></span>
    </button>
  </div>*/});
  pollingTimerHTML = pollingTimerHTML.replace(/\{0\}/g, getMessage("MOSJA12054", false));
  $('.oase-footer-switch').prepend( pollingTimerHTML );
}
function footerPollingTimerStart() {
  $('.oase-polling-switch .oase-button').addClass('on');
}
function footerPollingTimerStop() {
  $('.oase-polling-switch .oase-button').removeClass('on');
}
