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

$( function(){

let $container = $('#container');

/* ツールチップ */
$container.on('mouseenter.tooltipShow', '.tooltip', function(){

    $container.append('<div class="oase-tooltip"><div class="oase-tooltip-text"></div><div class="oase-tooltip-arw"></div></div>');
    
    let $tooltip = $('.oase-tooltip');
    
    let tooltipOffset = $( this ).offset(),
        thisWidthOffset = $( this ).outerWidth() / 2,
        thisHeight = $( this ).outerHeight(),
        tooltipText = '';
        
    if ( $( this ).attr('title') !== undefined ){
        let title = $( this ).attr('title');
        $( this ).removeAttr('title').attr('data-tooltip', title );
    }
    
    if ( $( this ).attr('data-tooltip') !== undefined ){
        tooltipText = $( this ).attr('data-tooltip');
    } else {
        tooltipText = $( this ).find('span').text();
    }
    tooltipText = textEntities( tooltipText );
    $tooltip.find('.oase-tooltip-text').html( tooltipText.replace(/\n/g,'<br>') );
    
    let windowWidth = $( window ).outerWidth(),
        tooltipWidth = $tooltip.outerWidth(),
        tooltipHeight = $tooltip.outerHeight();
    
    let tooltipLeft = tooltipOffset.left + thisWidthOffset - ( tooltipWidth / 2 ),
        tooltipTop = tooltipOffset.top - ( tooltipHeight + 4 ),
        arwLeft = tooltipWidth / 2;
    
    // 左右にあふれているかチェック
    if ( windowWidth < tooltipLeft + tooltipWidth ) {
        arwLeft = arwLeft + ( tooltipLeft + tooltipWidth - windowWidth + 4 );
        tooltipLeft = tooltipLeft - ( tooltipLeft + tooltipWidth - windowWidth + 4 );
    } else if ( 0 > tooltipLeft ) {
        arwLeft = arwLeft + tooltipLeft - 4;
        tooltipLeft = 4;
    }
    
    // 上にあふれるかチェック
    if ( tooltipTop - tooltipHeight < 0 ) {
    
        tooltipTop = tooltipOffset.top + ( thisHeight + 8 );
        $tooltip.addClass('bottom');
    
    }
    
    $tooltip.css({
        'top':  tooltipTop,
        'left': tooltipLeft
    });
    $tooltip.find('.oase-tooltip-arw').css({
        'left': arwLeft
    });
    
    $( this ).on('mouseleave.tooltipHide', function(){
        $( this ).off('mouseenter.tooltipShow mouseleave.tooltipHide');
        $('.oase-tooltip').remove();
    });
        
});



/* input ツールチップ */
$container.on('focus.tooltipShow', '.tooltip-input', function(){

    let $thisInput = $( this );
    $thisInput.after('<div class="oase-tooltip-input"><div class="oase-tooltip-text"></div></div>');
    
    let $tooltip = $('.oase-tooltip-input');
    
    let thisPosition = $thisInput.position(),
        thisWidth = $thisInput.outerWidth(),
        thisHeight = $thisInput.outerHeight(),
        texthtml = '';

    if ( $thisInput.attr('title') !== undefined ){
        let title = $thisInput.attr('title');
        $thisInput.removeAttr('title').attr('data-tooltip', title );
    }
    
    $tooltip.css('width', thisWidth - 4 );
    
    if ( $thisInput.attr('data-tooltip') !== undefined ){
        texthtml = $thisInput.attr('data-tooltip');
    } else {
        texthtml = $thisInput.find('span').text();
    }
    
    $tooltip.find('.oase-tooltip-text').html( texthtml );
    
    $tooltip.css({
        'top':  thisHeight + thisPosition.top - 2,
        'left': thisPosition.left + 2
    }); 
    
    // フォーカスが外れたら・・・
    $thisInput.on('blur.tooltipHide', function(){
        $( this ).off('keypress.textCount keyup.textCount focus.tooltipShow blur.tooltipHide');        
        $tooltip.remove();
    });
        
})

});