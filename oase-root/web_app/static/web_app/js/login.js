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

function login_auth(strID){
    let strQuery = location.search;

    document.getElementById(strID).action += strQuery;
    document.getElementById(strID).submit();
}

$(function(){
    $(document).on('keypress','#password',function(e){
        if(window.event.keyCode === 13){
            $("#login").click(); 
        }
    });

    $('.oase-login-form dd.open-pass').on('click', function( e ){
        e.preventDefault();
    }).on('touchstart mouseenter', function(e){
        e.preventDefault();
        $('#password').attr('type','text');
        $( this ).addClass('hover');
        $( this ).find('i.owf-eye-close').removeClass('owf-eye-close').addClass('owf-eye-open');
    }).on('touchend mouseleave', function(){
        $('#password').attr('type','password');
        $( this ).removeClass('hover');
        $( this ).find('i.owf-eye-open').removeClass('owf-eye-open').addClass('owf-eye-close');
    });
});
