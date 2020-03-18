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

function setRangeLowerValue( range ) {
  let $range = ( range instanceof jQuery )? range : $( range );
  let max = $range.attr('max'),
      min = $range.attr('min'),
      value = $range.val();
  $range.nextAll('.range-lower').width( (( value - min ) / ( max - min )) * 100 + '%' );
  $range.nextAll('.range-thumb').css('left', (( value - min ) / ( max - min )) * 100 + '%' );
}



// 有効・無効スイッチ
let switchChange = function( change ) {

  let selector = '#input-switch7';
  let value = $(selector).val();

  let switchElement = $( change ).attr('data-switch');
  if ( $( switchElement ).is('input') ) {
    if( $( switchElement ).is(':disabled') ) {
      $( switchElement ).prop('disabled', false );
      $( switchElement + '-range' ).prop('disabled', false );
    } else {
      $( switchElement ).prop('disabled', true );
      $( switchElement + '-range' ).prop('disabled', true );
    }
  } else {
    $( switchElement ).slideToggle( 0 );
    if ( parseInt(value) === 0){
      $(selector).val('1');
    }
    if ( parseInt(value) === 1){
      $(selector).val('0');
    }
  }
}

$(function(){

//////////////////////////////////////////////////
// input [ Number & Range ]

  // input range initialize
  let $inputRange = $('input[type="range"]'),
      rangeStepValue = 0,
      rangeMouseDownFlg = false;
  
  $inputRange.after('<div class="range-lower" /><div class="range-thumb" /><div class="range-tooltip" />')
  .each( function(){
    setRangeLowerValue( this );
  });

  $inputRange.on('input change', function(){

    $( this ).closest('tr').find('input[type="number"]').val( $( this ).val() ).change();
    setRangeLowerValue( this );

  }).on('mousemove', function( e ){
    // マウスホバーした位置の値を表示する
    let $range = $( this );
    
    let rangeWidth = $range.outerWidth(),
        rangeXp = e.pageX - $range.offset().left,
        rangeMin = Number( $range.attr('min') ),
        rangeMax = Number( $range.attr('max') ),
        rangeStep = 1;
    
    // IE11とEdgeは座標を四捨五入する
    if( ie11Check() || edgeCheck() ) {
        rangeWidth = Math.round( rangeWidth ),
        rangeXp = Math.round( e.pageX ) - Math.round( $range.offset().left );
    }
    
    if ( $range.data('step') !== undefined ) rangeStep = $range.data('step');
            
    let rangeValue = Math.round( ( rangeMax - rangeMin ) * ( rangeXp / rangeWidth ) + rangeMin ),
        rangePosition = rangeXp / rangeWidth * 100;
    
    // 数値をrangeStepの倍数にする
    rangeStepValue = Math.round( rangeValue / rangeStep ) * rangeStep;
    // 両端の値調整
    if( rangeStepValue <= 0 ) rangeStepValue = rangeMin;
    if( rangeWidth - rangeXp <= 1 ) rangeStepValue = rangeMax;
    // 数値を表示
    if( rangeValue >= rangeMin && rangeValue <= rangeMax ) {
      if( rangePosition < 0 ) rangePosition = 0;
      if( rangePosition > 100 ) rangePosition = 100;
      $range.nextAll('.range-tooltip')
        .text( rangeStepValue )
        .css({'left': e.pageX, 'top': $range.offset().top - 12 });
    }  
    // mousedownしていたら値変更
    if( rangeMouseDownFlg && $range.val !== rangeStepValue ) {
    
      $range.closest('.range').addClass('move');
      
      // 処理を間引く
      let rangeSetTimer = false;
      clearTimeout(rangeSetTimer);
      rangeSetTimer = setTimeout(function() {
        $range.val( rangeStepValue ).change();
      }, 100 );
    
    }
  
  }).on('mousedown', function( e ){
    e.preventDefault();
    rangeMouseDownFlg = true;
    $( this ).val( rangeStepValue ).change().focus();
  }).on('mouseup', function(){
    rangeMouseDownFlg = false;
    $( this ).closest('.range').removeClass('move');
    $( this ).blur();
  }).on('mouseenter', function(){
    $( this ).nextAll('.range-tooltip').show();
  }).on('mouseleave', function(){
    rangeMouseDownFlg = false;
    $( this ).closest('.range').removeClass('move');
    $( this ).blur().nextAll('.range-tooltip').hide();
  });


  $('input[type="number"]').on('focus click', function(){

    // クリック、フォーカスで選択状態に
    $( this ).select();

  }).on('keydown', function( e ){

    let k = e.keyCode;

    // 上下で+-
    if( k === 38 || k === 40 ) {
    
      e.preventDefault();
      
      let $num = $( this );
      let val = Number( $num.val() );
      
      if( e.ctrlKey ) {
        if( k === 38 ) val += 10;
        if( k === 40 ) val -= 10;
      } else {
        if( k === 38 ) val++;
        if( k === 40 ) val--;
      }
      $num.val( val ).change();
    
    }
    
    // 小数点を入力させない
    if( k === 110 || k === 190 ) e.preventDefault();
  
  }).on('input change',function(){

    let $num = $( this );
    let val = $num.val(),
        min = Number( $num.attr('min') ),
        max = Number( $num.attr('max') );

    // 半角数字以外は消す
    val = Number( val.replace(/(?!^)-|[^-0-9]+/g, '') );

    // min, max, 空白調整
    if( !isNaN( max ) && val > max ) val = max;
    if( !isNaN( min ) && ( val < min || val == '' ) ) val = min;

    // 値を更新
    $num.val( val );

    // Rangeを更新
    let $range = $( this ).closest('tr').find('input[type="range"]');
    $range.val( $( this ).val() );
    setRangeLowerValue( $range );

  });


  // タブメニュー操作
  $('.oase-config-menu a').eq(0).addClass('open');
  
  let configSection = $('.oase-config section');
  
  configSection.hide();
  configSection.eq(0).show();

  $('.oase-config-menu a').on('click', function( e ){
    e.preventDefault();
    let openSystemSection = $( this ).attr('href');
    
    $('.oase-config-menu a.open').removeClass('open');
    $( this ).addClass('open');
    configSection.hide();
    $( openSystemSection ).show();    
    
  });

  // メール通知先ログインID表示制御 参照or編集時
  changeMailForm($("#nd").data('value'));

  // Active Directory連携 ON/OFFによる項目表示制御
  let value = $('#input-switch7').val();
  if ( parseInt(value) === 1){
    $( '.active-directory-setting' ).slideToggle( 0 );
  }

  $('.config-switch-input').on('click', function(){
    switchChange( this );
  });

  
  // 入力のリセット
  $('button.reset').on('click', function(){

    if ( confirm(getMessage("MOSJA00207", false)) ) {
   
      let $config = $( this ).closest('section');

      $config.find('.change-value').each( function(){
      
        let $input = $( this );
        let initialValue = $input.attr('data-initial-value');
        if ( initialValue === undefined ) initialValue = '';
        
        if( $input.is('[type="checkbox"]') ) {
          // チェックボックス
          if ( initialValue === 'on' ) {
            $input.prop('checked', true );
          } else {
            $input.prop('checked', false );
          }
          // 切り替えボタン
          if( $input.is('.config-switch-input') ) {
            switchChange( $input );
          }
        } else if ( $input.is('tr') ) {
          // 追加行
          $input.remove();
        } else if( $input.is('[type="number"]') ) {
          // ナンバー
          $input.val( initialValue );
          let $range = $input.closest('tr').find('[type="range"]');
          $range.val( initialValue );
          setRangeLowerValue( $range );
        } else if( $input.attr("id") === "nd" ) {
          // メール種別種別、メール通知先ログインID制御
          $input.val( initialValue );
          changeMailForm( initialValue );
        } else {
          // その他
          $input.val( initialValue );
        }
        $input.removeClass('change-value');
      });
      
      $config.find('.oase-config-footer button').prop('disabled', true );
      
    }
    
  });

});

////////////////////////////////////////////////
// 選択されたメール通知タイプを取得し、表示制御する
//////////////////////////////////////////////////
function controlMailForm(){
  value = document.getElementById("nd").value;
  changeMailForm(value);
}
        

////////////////////////////////////////////
// メール通知タイプの選択肢による表示制御
////////////////////////////////////////////
function changeMailForm(value){
  if (parseInt(value) === 0 || parseInt(value) === 1) {
    $("#notification-destination-name").hide();
    $("#notification-destination-value").hide();
  }else if (parseInt(value) === 2 ){
    $("#notification-destination-name").show();
    $("#notification-destination-value").show();
  }

}

////////////////////////////////////////////
// システム設定をidを指定してリセットする
////////////////////////////////////////////
function resetSystemConfig(selector){
  
  let $config = $( selector );

  $config.find('.change-value').each( function(){
  
    let $input = $( this );
    let initialValue = $input.attr('data-initial-value');
    if ( initialValue === undefined ) initialValue = '';
    
    if( $input.is('[type="checkbox"]') ) {
      // チェックボックス
      if ( initialValue === 'on' ) {
        $input.prop('checked', true );
      } else {
        $input.prop('checked', false );
      }
      // 切り替えボタン
      if( $input.is('.config-switch-input') ) {
        switchChange( $input );
      }
    } else if ( $input.is('tr') ) {
      // 追加行
      $input.remove();
    } else if( $input.is('[type="number"]') ) {
      // ナンバー
      $input.val( initialValue );
      let $range = $input.closest('tr').find('[type="range"]');
      $range.val( initialValue );
      setRangeLowerValue( $range );
    } else if( $input.attr("id") === "nd" ) {
      // メール種別種別、メール通知先ログインID制御
      $input.val( initialValue );
      changeMailForm( initialValue );
    } else {
      // その他
      $input.val( initialValue );
    }
    $input.removeClass('change-value');
  });
  
  // td要素のエラーも全て削除
  $('td').removeClass('error');
  $config.find('.error-list').remove();
  $config.find('.oase-config-footer button').prop('disabled', true );
  
}

//////////////////////////////////////////////
// システム設定 の"全てリセット"ボタンの実行
//////////////////////////////////////////////
function pageReset() {
  let section_ids = [
    '#oase-config-log',
    '#oase-config-authentication',
    '#oase-config-password',
    '#oase-config-active-directory',
  ]

  // 変更がなければ何もしない
  if($(document).find('.change-value').length === 0){
    return;
  }

  if ( confirm(getMessage("MOSJA00207", false)) ) {
    section_ids.map(resetSystemConfig);
  }
}

function saveBtnOn(){
  $( '#actdir' ).prop('disabled', false );
}
