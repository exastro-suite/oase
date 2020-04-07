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

// フォーカス対象の要素
let focusElement = 'a, input, select, textarea, button';

// Tab移動でフォーカスする要素の制限
function tabFocusControl( $element ) {

  // objectチェック
  if ( $.type( $element ) !== 'object' ) $element = $( $element );
  
  $( focusElement ).attr('tabindex', -1 );
  $element.find( focusElement ).removeAttr('tabindex');
  
}

// 全てのtabindex=-1を消す
function tabFocusControlClear() {

  $('[tabindex="-1"]').removeAttr('tabindex');

}

// モーダルを開く
function modalOpen( element ){

  tabFocusControl( element );
  $('.oase-modal-overlay').fadeIn( 300 );
  $( element ).addClass('modal-open').show();
  
  // .server-errorがある場合はフォーカスをスキップする
  if( !$( element ).find('.server-error').length ) {
    // モーダルの中の最初の要素（クローズボタン以外）にフォーカスを当てる
    $( element ).find( focusElement ).not('.oase-modal-close').eq(0).focus();
  }
}

// タブ型モーダルを開く
function modalTabOpen( element, openTabNum ){
  
  let $tab = $( element );

  if ( !openTabNum ) openTabNum = 0;
  $('.oase-modal-overlay').fadeIn( 300 );
  $tab.addClass('modal-open').show();
  
  $tab.find('.oase-modal-tab-block').each( function( index ){
    $( this ).css({'left': index * 100 + '%' });
  });
  modalTabMove( element, openTabNum );

}

function modalBlockTabOpen( ID, openTabNum ) {

   let $blockTab = $( ID );
   
   $blockTab.find('.oase-modal-block-tab-menu button.open').removeClass('open');
   $blockTab.find('.oase-modal-block-tab-menu button').eq( openTabNum ).addClass('open');
   
   $blockTab.find('.oase-modal-block-tab-block.open').removeClass('open');
   $blockTab.find('.oase-modal-block-tab-block').eq( openTabNum ).addClass('open');

}


// タブ型モーダル　タブの移動
function modalTabMove( element, openTabNum ){

  let $tab = $( element ),
      openTabBlock = openTabNum * -100,
      tabMoveSpeed = 300;
  
  if ( !openTabNum ) openTabNum = 0;
  let object = $tab.find('.oase-modal-tab-block').eq( openTabNum ).add( $tab.find('.oase-modal-tab-menu') );
  tabFocusControl( object );
  $tab.find('.oase-modal-tab-menu button.open').removeClass('open');
  $tab.find('.oase-modal-tab-menu button').eq( openTabNum ).addClass('open').attr('tabindex', -1 );
  
  $tab.find('.oase-modal-tab-block').each( function(){
    $( this ).stop( 0, 1 ).animate({'left': openTabBlock + '%' }, tabMoveSpeed );
    openTabBlock = openTabBlock + 100;
  });
  
  // .server-errorがある場合はフォーカスをスキップする
  if( !$( element ).find('.server-error').length ) {
    // アニメーション後に最初の要素にフォーカスを当てる
    setTimeout( function(){
      $tab.find('.oase-modal-tab-block').eq( openTabNum ).find( focusElement ).eq(0).focus();
    }, tabMoveSpeed );
  }

}

// モーダルを閉じる
function modalClose( element ){

  let $modal = $( element );
  
  /* モーダル内に変更があるかチェック */
  if ( $modal.find('.change-value').length && beforeunloadThroughFlag === false ){
    if ( !confirm(getMessage("MOSJA00209", false)) ) {
      return false;
    }
  }
  beforeunloadThroughFlag = false;
  
  tabFocusControlClear();
  
  $modal.find('*[data-initial-value]').removeAttr('data-initial-value');
  $modal.find('.change-value').removeClass('change-value');
  $modal.find('.server-error').removeClass('server-error');
  $modal.addClass('modal-close');
  $('.oase-modal-overlay').fadeOut( 300 );
  
  setTimeout(function(){
    $('.modal-close').removeClass('modal-close');
    $modal.removeClass('modal-open').hide();
  }, 300 );
  
  return true;
}

// モーダルを切り替える
function modalChange( closeElement, openElement ){

  let $closeModal = $( closeElement );
  
  tabFocusControlClear();
  tabFocusControl( openElement );
  
  /* モーダル内に変更があるかチェック */
  if ( $closeModal.find('.change-value').length && beforeunloadThroughFlag === false ){
    if ( !confirm(getMessage("MOSJA00209", false)) ) {
      return false;
    }
  }
  beforeunloadThroughFlag = false;
  
  $closeModal.find('*[data-initial-value]').removeAttr('data-initial-value');
  $closeModal.find('.change-value').removeClass('change-value');
  $closeModal.find('.server-error').removeClass('server-error');
  $closeModal.addClass('modal-change');
  
  setTimeout(function(){
    $( openElement ).addClass('modal-open').show();
    if( $( openElement ).is('.oase-modal-tab') ) {
      $( openElement ).find('.oase-modal-tab-block').each( function( index ){
        $( this ).css({'left': index * 100 + '%' });
      });
      modalTabMove( openElement, 0 );
    } else {
      $( openElement ).find( focusElement ).not('.oase-modal-close').eq(0).focus();
    }
  }, 200 );
  
  setTimeout(function(){
    $('.modal-change').removeClass('modal-change');
    $closeModal.removeClass('modal-open').hide();
  }, 300 );

  return true;
}




// 確認画面を開く
function confirmOpen( element ){

  tabFocusControl( element );
  $('.oase-confirm-overlay').fadeIn( 300 );
  $( element ).addClass('confirm-open').show();

}

// 確認画面を閉じる
function confirmClose( element, returnElement ){

  let confirm = $( element );
  
  tabFocusControlClear();
  
  confirm.addClass('confirm-close');
  $('.oase-confirm-overlay').fadeOut( 300 );
  
  setTimeout(function(){
    $('.confirm-close').removeClass('confirm-close');
    confirm.removeClass('confirm-open').hide();
    tabFocusControl( returnElement );
  }, 300 );

}
