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

/* -------------------------------------------------- *\

   OASE Table

\* -------------------------------------------------- */

/*
   行の追加
   table = 追加する対象テーブル
   html = 追加するHTML
   maxLength = 行数制限
*/
function tableRowAdd( table, html, maxLength, focusFlg ) {

  let $elem        = $( table ).find('tbody'),
      $html        = $( html );
  let trLength     = $elem.find('tr').length;

  if ( !maxLength ) maxLength = -1;
  if ( focusFlg === null ) focusFlg = true;
  
  // maxLengthを超えた場合はアラートを出す
  if ( maxLength <= trLength && maxLength !== -1 ) {
    alert(getMessage("MOSJA00210", false));
    return false;
  }
  
  // 要素を追加
  $elem.append( $html );
  
  // 要素の追加を待ち、最初のインプットにフォーカスを当てる
  if ( focusFlg === true ) {
    $html.ready( function(){
      $html.addClass('change-value').find('input[type="text"]:eq(0)').focus();
      tableRowCount();
      saveButtonJudgment( $elem );
    });
  }
  
}
/*
   行の削除
   thisElem = this
*/
function tableRowRemove( thisElem ) {

  let $tr = $( thisElem ).closest('tr'),
      $table = $( thisElem ).closest('table');
  
  // 変更があるかチェック
  if ( $tr.find('.change-value').length ) {
     if ( !confirm(getMessage("MOSJA00211", false)) ) return false;
  }
  
  $tr.remove();
  tableRowCount();
  saveButtonJudgment( $table );
  
}
/*
   行数カウントの更新
*/
function tableRowCount() {
  $('.oase-table').each( function(){
    let rowCount = $( this ).find('tbody tr:not([class*="filter-hide-"])').length;
    $( this ).find('.rowCount').text( rowCount );
  });
}
/*
   .oase-tableの初期設定
*/
function tableInitialize() {

// スクロール初期化
$('.oase-table').scrollTop(0);

// Windowサイズ変更でフィルターメニューを消す
let offFilterMenu = function() {
    $('.oase-filter-switch.on').removeClass('on');
    $('.oase-filter-menu').hide();
}
let windowResizeTimer = false,
    windowResizeFlag = false;
$( window ).on('resize', function() {
    if ( windowResizeFlag === false ) {
        offFilterMenu();
        $('.oase-datepicker').remove();
        windowResizeFlag = true;
    }
    if ( windowResizeTimer !== false ) {
        clearTimeout( windowResizeTimer );
    }
    windowResizeTimer = setTimeout( function() {
        windowResizeFlag = false;
    }, 200);
});

// 要素外をクリックで消す
$( document ).on('mousedown', function( e ){
    if ( $('.oase-datepicker').length ) {
        if ( !$( e.target ).closest('.oase-datepicker, .oase-filter-menu input').length ) {
            $('.oase-datepicker').remove();
        }
    } else {
        if ( !$( e.target ).closest('.oase-filter-menu, .oase-datepicker, .oase-filter-switch').length ) {
            offFilterMenu();
        }
    }
});

/* ************************************************** *
 *
 * OASE Table Main
 *
 * ************************************************** */

/* ************************************************** *
 * テーブルごとに処理 */
$('.oase-table').each( function(){

let $oaseTable = $( this );
let $oaseTableHead = $oaseTable.find('thead'),
    $oaseTableBody = $oaseTable.find('tbody'),
    $filter = $( this ).find('table');

// IE11の場合固定用table作成
if( ie11Check() ) {
  let $ie11FixedTableHeader = $('<div class="oase-table-header-fixed"><div class="oase-table-header-fixed-inner"><table><thead>' + $oaseTableHead.html() + '</thead></table></div></div>');
  $oaseTable.find('.oase-table-inner').append( $ie11FixedTableHeader );
  $oaseTableHead = $oaseTable.find('.oase-table-header-fixed thead');
  $oaseTable.find('.oase-table-inner').on('scroll', function(){
      $oaseTable.find('.oase-table-header-fixed-inner').scrollLeft( $( this ).scrollLeft() );
  });
}

/* 表示されている行数をカウント */
let showCount = function(){
    return $oaseTableBody.find('tr:not([class*="filter-hide-"])').length;
}

/* 正規表現を使わない全置換 */
let replaceAll = function( str, before, after ) {
    return str.split( before ).join( after );
}

/* スクロール */
let tableScroll = function( scrollDirection ) {
    if ( scrollDirection === 'top' ) {
        $oaseTable.find('.oase-table-inner').scrollTop( 0 );
    } else {
        let tableBottom = $filter.outerHeight();
        $oaseTable.find('.oase-table-inner').scrollTop( tableBottom );
    }
}

/* アニメーションスクロール */
let tableAnimationScroll = function( scrollDirection ) {
    if ( scrollDirection === 'top' ) {
        $oaseTable.find('.oase-table-inner').animate({scrollTop: 0 }, 300 );
    } else {
        let tableBottom = $filter.outerHeight() - $oaseTable.find('.oase-table-inner').outerHeight() + 1;
        $oaseTable.find('.oase-table-inner').animate({scrollTop: tableBottom }, 300 );
    }
}

/* ************************************************** *
 * ページング */
 
let pagingPageNum = 1,
    pagingFlag = ( $oaseTable.find('.rowShowNum').length ) ? true : false;
let pagingTable = function( pageNum ) {

  tableScroll('top');

  let pagingPageCount = showCount();
  let pagingEnd = $oaseTable.find('.rowShowNum').val();

  // select.val()が取得できない場合がある
  if ( pagingEnd === undefined ) pagingEnd = 50;

  // 最大ページ数
  let pagingMax = Math.ceil( pagingPageCount / pagingEnd );

  // 表示されたページと最大ページ数の比較
  if ( pageNum >= pagingMax ) {
    pageNum = pagingMax;
    $oaseTable.find('.pagingNext').prop('disabled', true );
  } else {
    $oaseTable.find('.pagingNext').prop('disabled', false );
  }

  // 表示ページが１以下の場合
  if ( pageNum <= 1 ) {
    pageNum = 1;
    $oaseTable.find('.pagingPrev').prop('disabled', true );
  } else {
    $oaseTable.find('.pagingPrev').prop('disabled', false );
  }

  let pagingStart = ( pageNum - 1 ) * pagingEnd - 1;

  $oaseTable.find('.pagingNow').val( pageNum );
  $oaseTable.find('.pagingMax').text( pagingMax );
  $oaseTableBody.find('tr:not([class*="filter-hide-"])').addClass('paging-hide');

  if ( pagingStart === -1 ) {
      $oaseTableBody.find('tr:not([class*="filter-hide-"]):lt(' + pagingEnd + ')').removeClass('paging-hide');
  } else {
      $oaseTableBody.find('tr:not([class*="filter-hide-"]):gt(' + pagingStart + '):lt(' + pagingEnd + ')').removeClass('paging-hide');
  }

  pagingStart = pagingStart + pagingEnd;
  pagingPageNum = pageNum;

}

/* ページングリセット */
let pagingReset = function() {
  if ( pagingFlag ) {
    pagingPageNum = 1;
    pagingTable( pagingPageNum );
    tableScroll('top');
    tableRowCount();
  }
}

// ページング初期設定
pagingReset();
if ( pagingFlag ) {
  $oaseTable.find('.pagingPrev').on('click', function(){ pagingTable( pagingPageNum - 1 ) });
  $oaseTable.find('.pagingNext').on('click', function(){ pagingTable( pagingPageNum + 1 ) });
  $oaseTable.find('.rowShowNum').on('change', function(){ pagingTable( 1 ) });
  $oaseTable.find('.pagingNow').on('change', function(){ pagingTable( $( this ).val() ) });
}

/* フォーム各種操作 */
$oaseTable.find('.scrollTop').on('click', function(){ tableAnimationScroll('top'); });
$oaseTable.find('.scrollBottom').on('click', function(){ tableAnimationScroll(); });

/* フィルター・ソート 初期設定 */
let filterHtml = '';
let filterHtmlMenu = '<div class="oase-filter-menu">';
filterHtmlMenu += '<ul class="oase-filter-tab-menu">';

let filterHtmlSelectMenu = '<li><a href="#filter-select"><em class="owf owf-select"></em></a></li>'; 
let filterHtmlSelect = '<div class="oase-filter-tab-body filter-select">';
filterHtmlSelect += '<select size="4" multiple></select>';
filterHtmlSelect += '</div>';

let filterHtmlTextMenu = '<li><a href="#filter-text"><em class="owf owf-loupe"></em></a></li>';
let filterHtmlText = '<div class="oase-filter-tab-body filter-text">';
filterHtmlText += '<input type="text" placeholder="&#xe903; Text"><button><em class="owf owf-update"></em></button>';
filterHtmlText += '<ul>';
filterHtmlText += '<li><label class="regexp"><input type="checkbox" checked>' + getMessage("MOSJA00212", false) + '</label></li>';
filterHtmlText += '<li><label class="ignore-case"><input type="checkbox" checked>' + getMessage("MOSJA00213", false) + '</label></li>';
filterHtmlText += '<li><label class="point-up"><input type="checkbox" checked>' + getMessage("MOSJA00214", false) + '</label></li>';
filterHtmlText += '<li><label class="negative"><input type="checkbox">否定</label></li>';
filterHtmlText += '</ul>';
filterHtmlText += '</div>';

let filterHtmlDateMenu = '<li><a href="#filter-date"><em class="owf owf-date"></em></a></li>';
let filterHtmlDate = '<div class="oase-filter-tab-body filter-date">';
filterHtmlDate += '<dl><dt>A</dt><dd><input type="input" class="date-a" placeholder="0000/00/00 00:00:00"></dd>';
filterHtmlDate += '<dt>B</dt><dd><input type="input" class="date-b" placeholder="0000/00/00 00:00:00"></dd></dl>';
filterHtmlDate += '<div class="select"><select class="date-select"><option value="date01" selected>' + getMessage("MOSJA00215", false) + '</option><option value="date02">' + getMessage("MOSJA00216", false) + '</option><option value="date03">' + getMessage("MOSJA00217", false) + '</option></select></div><button><em class="owf owf-update"></em></button>';
filterHtmlDate += '</div>';

/* ************************************************** *
 * th.filter セルごとにフィルタの設定を行う */

$oaseTableHead.find('.filter').each( function(){

  /* フィルタタイプごとにHTMLを作成 */
  let filterType = $( this ).attr('filter-type');
  switch ( filterType ) {
    case 'text': filterHtml = filterHtmlMenu + filterHtmlTextMenu + '</ul>' + filterHtmlText; break;
    case 'select': filterHtml = filterHtmlMenu + filterHtmlSelectMenu + '</ul>' + filterHtmlSelect; break;
    case 'date': filterHtml = filterHtmlMenu + filterHtmlDateMenu + filterHtmlTextMenu + '</ul>' + filterHtmlDate + filterHtmlText; break;
    case 'common': filterHtml = filterHtmlMenu + filterHtmlSelectMenu + filterHtmlTextMenu + '</ul>' + filterHtmlSelect + filterHtmlText; break;
  }
  filterHtml += '</div>';
  
  $( this ).children('.cell-inner').prepend('<div class="oase-filter-switch menu"><em class="owf owf-filter-on"></em></div><div class="oase-filter-switch clear"><em class="owf owf-filter-off"></em></div>');
  $( this ).append( filterHtml );

  /* タブ初期化 */
  $( this ).find('.oase-filter-tab-menu li:first-child a, .oase-filter-menu > .oase-filter-tab-body:eq(0)').addClass('selected');

  /* ************************************************** *
   * 列の内容から<option>リストを作成 */

  let filterSelectArray = [],
      filterCol = $( this ).parent('tr').children('th').index( this );

  $oaseTableBody.find('tr').each( function() {

    let filterText = '',
        $cell = $( this ).find('th,td').eq( filterCol );

    if ( $cell.find('select').length ) {
      // <select>
      $cell.find('option').each( function(){
        filterText = textEntities( $( this ).text() );
        if( filterSelectArray.indexOf( filterText ) === -1 && filterText ) {
          filterSelectArray.push( filterText );
        }
      });
    } else if ( $cell.find('ul').length ) {
      $cell.find('li').each( function(){
        filterText = textEntities( $( this ).text() );
        if( filterSelectArray.indexOf( filterText ) === -1 && filterText ) {
          filterSelectArray.push( filterText );
        }
      });
    } else {
      if ( $cell.find('input').length ) {
        // <input>
        filterText = textEntities( $cell.find('input').val() );
      } else if ( $cell.is('.status') ) {
        // .status（状態）
        filterText = textEntities( $cell.find('span.tooltip span').text() );
      } else {
        // その他 テキスト
        filterText = textEntities( $cell.text() );
      }
      if( filterSelectArray.indexOf( filterText ) === -1 && filterText ) {
        filterSelectArray.push( filterText );
      }
    }

  });

  // 追加した内容をソートする
  filterSelectArray.sort( function( a,b ){
    return ( a.toLowerCase() > b.toLowerCase() ? 1 : -1 );
  });
  
  // 追加された内容が5以下の場合はスクロールバーを表示させない
  if ( filterSelectArray.length <= 5 ) {
    $( this ).find('.filter-select select').addClass('no-scrollbar');  
  }

  // <select>に<option>を追加
  let optionHTML = '';
  for ( let num in filterSelectArray ) {
    optionHTML += '<option value="' + filterSelectArray[num] + '">' + filterSelectArray[num] + '</option>';
  }
  $( this ).find('.filter-select select').append( optionHTML );

});



/* ************************************************** *
 *
 *    列のソート !! 処理が重いので件数に注意する !!
 *
 * ************************************************** */

$oaseTableHead.find('.sort .cell-inner').on('click', function(){

  //console.time('Sort');
  
  $oaseTable.find('.oase-table-load').addClass('loading');
  
  let $objThis = $( this );
  
  setTimeout ( function(){ 

    let clickCol = $objThis.parents('tr').find('th').index( $objThis.parents('th') );
    let $sort = $oaseTableHead.find('th:eq(' + clickCol + ')'),
        $trObj = $oaseTableBody.find('tr'),
        sortType = 'asc';
    
    if ( $sort.is('.asc') ) {
      $('.asc, .desc').removeClass('asc desc');
      $sort.addClass('desc');
      sortType = 'desc';
    } else {
      $('.asc, .desc').removeClass('asc desc');
      $sort.addClass('asc');
      sortType = 'asc';
    }
    
    // ソート
    let sortHtml = $trObj.sort( function( a, b ){
    
      let aText, bText;
      let $a = $( a ).children().eq( clickCol ),
          $b = $( b ).children().eq( clickCol );

      if ( $a.find('input[type="text"]').length ){
          aText = $a.find('input[type="text"]').val();
          bText = $b.find('input[type="text"]').val();
      } else if( $a.find('select').length ){
          aText = $a.find('option:selected').val();
          bText = $b.find('option:selected').val();      
      } else if( $a.find('time').length ){
          aText = $a.find('time').attr('datetime').replace(/-|:|T|/g,'');
          bText = $b.find('time').attr('datetime').replace(/-|:|T|/g,'');
      } else {
          aText = $a.text();
          bText = $b.text();
      }
      
      if( !aText ) aText = '';
      if( !bText ) bText = '';

      if ( sortType === 'asc' ) {
        return ( aText > bText ? 1 : -1 );
      } else {
        return ( aText < bText ? 1 : -1 );
      }
      
    });
    
    $oaseTableBody.html( sortHtml );
    pagingReset();

    $('.oase-table-load').removeClass('loading');
    
    //console.timeEnd('Sort');
    
  }, 10 );

});



/* フィルター用タブ切り替え */
$('.oase-filter-tab-menu a').on('click',function(e){
    e.preventDefault();
    let $thisTab = $( this ).parents('.oase-filter-menu'),
        clickTab = $( this ).attr('href');

    clickTab = clickTab.replace('#','.');

    $thisTab.find('.selected').removeClass('selected');
    $( this ).addClass('selected');
    $thisTab.find( clickTab ).addClass('selected');
});

/* フィルタメニュー開閉 */
$oaseTableHead.find('.oase-filter-switch').on('click', function( e ){
    e.stopPropagation();

    let clickFilterLabel = $( this ).parents('th').attr('filter-label');
    let $filterHead = $oaseTableHead.find('.' + clickFilterLabel ),
        $filterBody = $oaseTableBody.find('.' + clickFilterLabel );
    let filterWidth = $filterHead.find('.cell-inner').outerWidth() - 8;
    
    if ( $( this ).is('.menu') ) {
    
    let filterMenuFixed = $( this ).offset(),
        filterSwitchHeight = $( this ).outerHeight();

    if( $( this ).is('.on') ) {
    
        $( this ).removeClass('on');
        $filterHead.find('.oase-filter-menu').hide();
           
    } else {
        $( this ).addClass('on');
        $filterHead.find('.oase-filter-menu').css('position', 'fixed').show();
        $filterHead.find('.oase-filter-menu').css({
            'width' : filterWidth,
            'position': 'fixed',
            'top' : filterMenuFixed.top + filterSwitchHeight,
            'left' : filterMenuFixed.left,
            'z-index' : 300
        });
    }
    
    } else {
        // フィルタクリア
        $( this ).hide();
        $filterHead.find('.oase-filter-menu').hide();
        $filterHead.find('.oase-filter-switch.on').removeClass('on');
        
        let filterOffCol = $( this ).parents('tr').find('th').index( $( this ).parents('th') );
        $('.filter-hide-' + filterOffCol ).removeClass('filter-hide-' + filterOffCol );

        $filterHead.find('.filter-select select').prop('selectedIndex', -1 );
        $filterHead.find('.filter-text input').val('');
        $filterBody.find('.search-text').contents().unwrap();
        $filterBody.find('.list-filter-on').removeClass('list-filter-on');
        $filterBody.removeClass('all-show');
        pagingReset();
        
    }
    
});



/* ************************************************** *
 *
 *    フィルタリング
 *
 * ************************************************** */

let filtering = function( $thisObj ) {

  let clickFilterLabel = $thisObj.parents('th').attr('filter-label');

  let $filterHead = $oaseTableHead.find('.' + clickFilterLabel ),
      $filterBody = $oaseTableBody.find('.' + clickFilterLabel );

  let selectCol = $thisObj.parents('tr').find('th').index( $thisObj.parents('th') );
  
  $('.filter-hide-' + selectCol ).removeClass('filter-hide-' + selectCol );
  $filterBody.find('.search-text').contents().unwrap();

  if( $thisObj.is('.filter-text button, .filter-text input') ) {

    /* ************************************************** *
     * Text */
    $filterHead.find('.filter-select select').prop('selectedIndex', -1 );
    let select = $filterHead.find('.filter-text input').val();

    if ( select !== '' ) {
      
      let regExp,
          regExpFlg = $filterHead.find('.regexp input').prop("checked"),
          ignoreCaseFlg = $filterHead.find('.ignore-case input').prop("checked"),
          negativeFlg = $filterHead.find('.negative input').prop("checked"),
          pointUpFlg = $filterHead.find('.point-up input').prop("checked");
      
      if ( regExpFlg === true ) {
        try {
          // 小文字・大文字を区別するか？
          if ( ignoreCaseFlg === true ) {
            regExp = new RegExp( select, "g");
          } else {
            regExp = new RegExp( select, "gi");
          }
        } catch( e ) {
          // 無効な正規表現の場合はフラグをオフにし、入力を空白にする
          select = '';
          regExpFlg = false;
        }
      }      
      
      $filterBody.each( function(){
      
        let $obj = $( this ).find('.cell-inner');
            
        if ( $obj.children().is('time') ) {
          $obj = $( this ).find('time');
        }
        
        let text = $obj.text();
        
        if ( select !== '' ) {
          if ( regExpFlg === true ) {
            // 正規表現 ON
            if (
              ( text.search( regExp ) !== -1 && negativeFlg === false ) ||
              ( text.search( regExp ) === -1 && negativeFlg === true )
            ) {
              // 検索単語強調
              if ( pointUpFlg === true ) {
                text = textEntities( text.replace( regExp, '[oase-point-up]$&[/oase-point-up]') );
                text = replaceAll( text, '[oase-point-up]', '<span class="search-text">');
                text = replaceAll( text, '[/oase-point-up]', '</span>');
                $obj.html( text );
              }
            } else {
              $( this ).parent('tr').addClass('filter-hide-' + selectCol );
            }
          } else {
            // 正規表現 OFF
            if (
              ( text.indexOf( select ) !== -1 && negativeFlg === false ) ||
              ( text.indexOf( select ) === -1 && negativeFlg === true )
            ) {
              // 検索単語強調
              if ( pointUpFlg === true ) {
                select = textEntities( select );
                text = textEntities( text );
                text = replaceAll( text, select, '<span class="search-text">' + select + '</span>');
                $obj.html( text );
              }
            } else {
              $( this ).parent('tr').addClass('filter-hide-' + selectCol );
            }
          }
        }
      });

    }

  } else if( $thisObj.is('.filter-date button') ) {
  
    /* ************************************************** *
     * Date */
    let filterDateA = $filterHead.find('.filter-date .date-a').val().replace(/\/| |:/g,''),
        filterDateB = $filterHead.find('.filter-date .date-b').val().replace(/\/| |:/g,''),
        filterType = $filterHead.find('.filter-date .date-select').val();

    $filterBody.each( function(){
    
      let datetime = $( this ).find('time').attr('datetime').replace(/-|:|T|/g,'');
      
      if ( filterType === 'date01' ) {
        // A から B
        if ( filterDateA > datetime || filterDateB < datetime ){
          $( this ).parent('tr').addClass('filter-hide-' + selectCol );    
        }
      } else if ( filterType === 'date02' ) {
        // A 以降
        if ( filterDateA > datetime ){
          $( this ).parent('tr').addClass('filter-hide-' + selectCol );    
        }
      } else if ( filterType === 'date03' ) {
        // A 以前
        if ( filterDateA < datetime ){
          $( this ).parent('tr').addClass('filter-hide-' + selectCol );    
        }
      }
    });

  } else {

    /* ************************************************** *
     * Select */
    let selectText = $filterHead.find('.filter-select select').val();
    
    selectText.forEach( function( value, index ) {
      selectText[ index ] = textEntities( value );
    });

    if ( selectText.length > 0 ) {
      $filterBody.each( function() {

        let $cell = $( this );

        // フィルタ対象がリストかそれ以外か
        if ( $cell.find('ul').length ) {
        
          let textFlag = false;
        
          $cell.find('li').each( function(){
            let cellText = textEntities( $( this ).text() );
            for ( let i = 0; i < selectText.length; i++ ) {
              if ( selectText.indexOf( cellText ) !== -1 ){
                $( this ).addClass('list-filter-on');
                textFlag = true;
              } else {
                $( this ).removeClass('list-filter-on');
              }
            }
          });
          
          // リストが全て表示されているかチェック
          if ( !$cell.find('li:hidden').length ) {
            $cell.addClass('all-show');
          } else {
            $cell.removeClass('all-show');
          }

          if ( textFlag === false ) {
            $cell.parent('tr').addClass('filter-hide-' + selectCol );
          }
        
        } else {
        
          let text = '';

          if ( $cell.find('select').length ) {
            text = $cell.find('option:selected').text();
          } else if ( $cell.find('input').length ) {
            text = $cell.find('input').val();
          } else {
            text = $cell.text();
          }
          text = textEntities( text );
          // console.log( text + ' / ' + selectText[0] );

          if ( selectText.indexOf( text ) === -1 ){
            $cell.parent('tr').addClass('filter-hide-' + selectCol );
          }

        }

      });
    }
  }

  /* ************************************************** *
   * フィルタされてるかチェック */
 
  if ( $('.filter-hide-' + selectCol ).length > 0 || $filterBody.find('.search-text' ).length > 0 || $filterBody.find('.list-filter-on' ).length > 0 ) {
      $filterHead.find('.oase-filter-switch.clear').show();
  } else {
      $filterHead.find('.oase-filter-switch.clear').hide();
  }

  $('.oase-table-load').removeClass('loading');
  pagingReset();

}



/* ************************************************** *
 * テキストフィルタメニュー */
 
$('.regexp, .negative').find('input').on('change', function(){
  let $this = $( this ),
      $clickCheck = $this.parents('.filter-text'),
      targetInput = $this.closest('label').is('.regexp') ? '.ignore-case' : '.point-up';
  if( targetInput === '.ignore-case' ) {
  // チェックで有効
    if ( $this.prop('checked') === true ) {
        $clickCheck.find( targetInput ).removeClass('disabled').find('input').prop("disabled", false );
    } else {
        $clickCheck.find( targetInput ).addClass('disabled').find('input').prop("disabled", true );
    }
  } else {
    // チェックで無効
    if ( $this.prop('checked') === false ) {
        $clickCheck.find( targetInput ).removeClass('disabled').find('input').prop("disabled", false );
    } else {
        $clickCheck.find( targetInput ).addClass('disabled').find('input').prop("disabled", true );
    }
  }
});



/* ************************************************** *
 * フィルタイベント */
let filterAct = function( $thisObj ){
  $oaseTable.find('.oase-table-load').addClass('loading');
  setTimeout ( function(){ filtering( $thisObj ); }, 10 );
}
$oaseTableHead.find('.filter-select select').on('change', function(){
  filterAct( $( this ) );
});
$oaseTableHead.find('.filter-text button, .filter-date button').on('click', function(){
  filterAct( $( this ) );
});
$oaseTableHead.find('.filter-text input').on('keypress', function(e){
  if ( e.which === 13 ) {
    filterAct( $( this ) );
  }
});

});

$('.filter-date input').oaseDatePicker();
$('.loading').removeClass('loading');

}/* / tableInitialize() */