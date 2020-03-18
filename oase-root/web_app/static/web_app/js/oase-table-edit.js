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

    // 変更があった場合更新に変更する。
    $('.oase-main').on('change', 'input, textarea', function(){

        let $parentTr = $( this ).parents('tr');

        // 変更チェック後に判定させるため、少し遅らせる
        setTimeout( function(){
            if ( $parentTr.find('.change-value').length ) {
                $parentTr.find('select.update option[value="2"]').prop('selected', true ).change();
            } else {
                $parentTr.find('select.update option[value="0"]').prop('selected', true ).change();
            }
        }, 10 );

    });

    // 選択したoptionによってクラスを付け替える
    $('.oase-main').on('change', 'select.update', function(){
        let $parentTr = $( this ).parents('tr'),
            value = $( this ).val();
        $parentTr.removeClass();
        if ( value === 2 ) $parentTr.addClass('update');
        if ( value === 3 ) $parentTr.addClass('delete');
    });

    // 所属グループ数を制限する
    $('td.group ul').each( function(){

        let $groupList = $( this ),
            maxGroup = 5;

        let listCount = $groupList.find('li').length;

        if ( listCount > maxGroup ) {
            $groupList.after('<div class="all tooltip" title="' + getMessage("MOSJA23035", false) + '">…</div>');
            $groupList.find('li:gt(' + ( maxGroup - 1 ) + ')').hide();

            $groupList.closest('tbody').on('click', '.all', function(){
                let listHTML = $groupList.find('li').clone().wrapInner('<span />').show();
                $('#modal-group-list .group-list').html( listHTML );
                modalOpen('#modal-group-list');

                let userName = textEntities( $(this).closest('tr').children("td")[0].innerText );

                if( userName !== ""){
                    document.getElementById('userGroupUserName').innerHTML = userName;
                }else{
                    let gid  = $(this).offsetParent()[0].children[0].id;
                    userName = textEntities( document.getElementById('user_name'+gid.slice(3)).defaultValue );
                    document.getElementById('userGroupUserName').innerHTML = userName;
                }
            });
        }
    });
});
