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

   OASE Rule Table

\* -------------------------------------------------- */

$( function() {

// drag clone用の要素を追加
$('.oase-modal').prepend('<div class="oase-modal-drag"></div>');

// ルールテーブルごとに処理をする
$('.oase-modal-rule-table').each( function(){

let $ruleTable = $( this );





// ルール順番入れ替え
$ruleTable.on('mousedown', 'td.move', function( e ){

e.preventDefault();
// 左クリック判定
if ( e.which === 1 ) {

let scrollTop = $('.oase-modal-body').scrollTop(),
    windowHeight = $( window ).outerHeight(),
    scrollTimer = false;

let $tableBox = $ruleTable.find('.oase-modal-rule-table-inner'),
    $trObj = $( this ).parent('tr');

$trObj.find('th, td').each( function(){
    $( this ).css('width', $( this ).outerWidth() );
});

let trPastIndex = 0,
    moveFlag = false,
    mouseDirection = 1,
    mousePastPosition = 0,
    trHeight = $trObj.outerHeight(),
    trOffset = $trObj.offset();

let selected = $trObj.find('option:selected').val();
let trClone = $trObj.clone( false ).addClass('drag-move').css({
  'top': trOffset.top,
  'left': trOffset.left
});


$trObj.addClass('hide');
$('.oase-modal-drag').html( trClone )
  .wrapInner('<div class="oase-modal-rule-table"></div>').find('select').val( selected );

let clearMove = function(){
    $('.hide').removeClass('hide');
    $('.drag-move').remove();
    $tableBox.off();
    $trObj.find('th, td').css('width', 'auto');
    $('.oase-modal-clone').html('')
    clearInterval( scrollTimer );
    scrollTimer = false;
}

$tableBox.on('mouseup mouseleave', function(){

    clearMove();

}).on('mousemove', function( e ){

let trCurrentIndex = $tableBox.find('tbody tr:hover').index(),
    mousePositionY = e.clientY - ( trHeight / 2 ),
    mouseCurrentPosition = e.clientY;

/*
if ( mouseCurrentPosition > windowHeight - 200 ) {

if ( scrollTimer === false ) {
scrollTimer = setInterval ( function(){
scrollTop = scrollTop + 1;
$('.oase-modal-rule-table-inner').scrollTop( scrollTop );
}, 10 );
}

} else if ( mouseCurrentPosition < 200 ) {

if ( scrollTimer === false ) {
scrollTimer = setInterval ( function(){
scrollTop = scrollTop - 1;
$('.oase-modal-rule-table-inner').scrollTop( scrollTop );
}, 10 );
}

} else {

clearInterval( scrollTimer );
scrollTimer = false;

}
*/

$('.drag-move').css({
'top': mousePositionY,
'left': trOffset.left
});

if ( trCurrentIndex !== -1 ) {

    if ( mouseCurrentPosition > mousePastPosition ) {
        if ( mouseDirection !== 1 ) {
            mouseDirection = 1;
            moveFlag = false;
        }
    } else if ( mouseCurrentPosition < mousePastPosition ) {
        if ( mouseDirection !== 2 ) {
            mouseDirection = 2;
            moveFlag = false;
        }
    }
    mousePastPosition = mouseCurrentPosition;
    
    if ( trPastIndex !== trCurrentIndex ){
        moveFlag = false;
    }
    if ( trPastIndex <= trCurrentIndex && mouseDirection === 1 && moveFlag === false ) {
        $tableBox.find('tbody tr').eq( trCurrentIndex ).after( $trObj );
        moveFlag = true;
    } else if ( trPastIndex >= trCurrentIndex && mouseDirection === 2 && moveFlag === false ) {
        $tableBox.find('tbody tr').eq( trCurrentIndex ).before( $trObj );
        moveFlag = true;
    }
    trPastIndex = trCurrentIndex;
}

});

}

});

});

});