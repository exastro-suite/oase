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

(function ( $ ) {

// Date Picker HTML - JavaScript Heredoc
let datePickerHTML = ( function(){/*

<div class="oase-datepicker">
<div class="oase-datepicker-inner">

<div class="oase-datepicker-calender">
<div class="oase-datepicker-calender-header">
<table class="form">
<tr>
<th><button class="calender-move prev"><em class="owf owf-minus"></em></button></th>
<td><input class="date-year" type="number" value="0"></td>
<td><input class="date-month" type="number" value="0"></td>
<th><button class="calender-move next"><em class="owf owf-plus"></em></button></th>
</tr>
</table>
</div>
<div class="oase-datepicker-calender-body"></div>
</div>

<div class="oase-datepicker-datetime">
<table class="form">
<tr>
<th>H</th><td>
<div class="select">
<select class="date-h">
<option value="00">00</option><option value="01">01</option><option value="02">02</option><option value="03">03</option><option value="04">04</option><option value="05">05</option><option value="06">06</option><option value="07">07</option><option value="08">08</option><option value="09">09</option><option value="10">10</option><option value="11">11</option><option value="12">12</option><option value="13">13</option><option value="14">14</option><option value="15">15</option><option value="16">16</option><option value="17">17</option><option value="18">18</option><option value="19">19</option><option value="20">20</option><option value="21">21</option><option value="22">22</option><option value="23">23</option>
</select>
</div>
</td>
<th>M</th><td>
<div class="select">
<select class="date-m">
<option value="00">00</option><option value="01">01</option><option value="02">02</option><option value="03">03</option><option value="04">04</option><option value="05">05</option><option value="06">06</option><option value="07">07</option><option value="08">08</option><option value="09">09</option><option value="10">10</option><option value="11">11</option><option value="12">12</option><option value="13">13</option><option value="14">14</option><option value="15">15</option><option value="16">16</option><option value="17">17</option><option value="18">18</option><option value="19">19</option><option value="20">20</option><option value="21">21</option><option value="22">22</option><option value="23">23</option><option value="24">24</option><option value="25">25</option><option value="26">26</option><option value="27">27</option><option value="28">28</option><option value="29">29</option><option value="30">30</option><option value="31">31</option><option value="32">32</option><option value="33">33</option><option value="34">34</option><option value="35">35</option><option value="36">36</option><option value="37">37</option><option value="38">38</option><option value="39">39</option><option value="40">40</option><option value="41">41</option><option value="42">42</option><option value="43">43</option><option value="44">44</option><option value="45">45</option><option value="46">46</option><option value="47">47</option><option value="48">48</option><option value="49">49</option><option value="50">50</option><option value="51">51</option><option value="52">52</option><option value="53">53</option><option value="54">54</option><option value="55">55</option><option value="56">56</option><option value="57">57</option><option value="58">58</option><option value="59">59</option>
</select>
</div>
</td>
<th>S</th><td>
<div class="select">
<select class="date-s">
<option value="00">00</option><option value="01">01</option><option value="02">02</option><option value="03">03</option><option value="04">04</option><option value="05">05</option><option value="06">06</option><option value="07">07</option><option value="08">08</option><option value="09">09</option><option value="10">10</option><option value="11">11</option><option value="12">12</option><option value="13">13</option><option value="14">14</option><option value="15">15</option><option value="16">16</option><option value="17">17</option><option value="18">18</option><option value="19">19</option><option value="20">20</option><option value="21">21</option><option value="22">22</option><option value="23">23</option><option value="24">24</option><option value="25">25</option><option value="26">26</option><option value="27">27</option><option value="28">28</option><option value="29">29</option><option value="30">30</option><option value="31">31</option><option value="32">32</option><option value="33">33</option><option value="34">34</option><option value="35">35</option><option value="36">36</option><option value="37">37</option><option value="38">38</option><option value="39">39</option><option value="40">40</option><option value="41">41</option><option value="42">42</option><option value="43">43</option><option value="44">44</option><option value="45">45</option><option value="46">46</option><option value="47">47</option><option value="48">48</option><option value="49">49</option><option value="50">50</option><option value="51">51</option><option value="52">52</option><option value="53">53</option><option value="54">54</option><option value="55">55</option><option value="56">56</option><option value="57">57</option><option value="58">58</option><option value="59">59</option>
</select>
</div>
</td>
</tr>
</table>
</div>

<div class="oase-datepicker-button">
<table class="menu">
<tr><td><button class="oase-mini-button close"><em class="owf owf-cross"></em><span>{0}</span></button></td><td><button class="oase-mini-button clear">{1}</button></td></tr>
</table>
</div>

</div>

</div>
*/}).toString().match(/[^]*\/\*([^]*)\*\/\}$/)[1];

datePickerHTML = datePickerHTML.replace(/\{0\}/, getMessage("MOSJA00070", false) );
datePickerHTML = datePickerHTML.replace(/\{1\}/, getMessage("MOSJA00208", false) );

// Date Picker Calender
let datePickerCalender = function( year, month ){

    // Today
    let thisDate = new Date();
    let today = thisDate.getDate();
    let selectedDay = today;
    if( !year ) year = thisDate.getFullYear();
    if( !month ) month = thisDate.getMonth() + 1;

    let thisCheckDate = new Date( thisDate.getFullYear(), thisDate.getMonth(), 1 );
    let showCheckDate = new Date( year, ( month - 1), 1 );

    if ( thisCheckDate.getTime() !== showCheckDate.getTime() ) {
        today = 0;
        selectedDay = 1;
    }

    month = month - 1;
    let startDate = new Date(year, month, 1);
    let endDate  = new Date(year, month + 1 , 0);
    let startDay = startDate.getDay();
    let endDay = endDate.getDate();
    let textSkip = true;
    let textDate = 1;
    let textTd ='';
    let addClass ='';
    let tableBody ='<table class="calendar-table">\n' +
    '<thead>\n'  +
    '<tr><th class="sun">SUN</th><th>MON</th><th>TUE</th><th>WED</th><th>THU</th><th>FRI</th><th class="sat">SAT</th></tr>\n' +
    '</thead>\n' +
    '<tbody class="calendar-body">'; // HTML



    for (let row = 0; row < 6; row++){
    let tr = '<tr class="week">';

    for (let col = 0; col < 7; col++) {

    if (row === 0 && startDay === col){
        textSkip = false;
    }
    if (textDate > endDay) {
        textSkip = true;
    }
    if (textDate >= endDay) {
        row++;
    }

    if( textSkip ) {
        addClass = 'off';
        textTd = '';
    } else {
        addClass = 'on';
        textTd = '<span class="num">' + textDate + '</span>';

        if( today === textDate ) {
            addClass += ' today';
        }
        if ( selectedDay === textDate ) {
            textTd = '<span class="num select-date">' + textDate + '</span>';
        }

        textDate++;
    }

    let td = '<td class="'+addClass+'">'+textTd+'</td>';

    tr += td;
    }
    tr += '</tr>';
    tableBody += tr;
    }
    tableBody += '</tbody>\n' +
    '</table>';

    $('.date-year').val( year );
    $('.date-month').val( month + 1 );

    return(tableBody);

}
 




$.fn.oaseDatePicker = function() {

$( this ).on('focus', function(){
if( $('.oase-datepicker').length > 0 ) $('.oase-datepicker').remove();


$('#container').append( datePickerHTML );
let $datePicker = $('.oase-datepicker'),
    $datePickerCalender = $('.oase-datepicker-calender-body');

let $focusObj = $( this );
let inputOffset = $focusObj.offset(),
    inputHeight = $focusObj.outerHeight(),
    windowWidth = $( window ).outerWidth(),
    datePickerWidth = $datePicker.outerWidth();

$datePickerCalender.html( datePickerCalender() );

if ( windowWidth > inputOffset.left + datePickerWidth ) {
$datePicker.css({
    'top':  inputOffset.top + inputHeight -1,
    'left': inputOffset.left
});
} else {
$datePicker.css({
    'top':  inputOffset.top + inputHeight -1,
    'right': 0
});
}

// value変更
let changeDate = function() {

let year = $datePicker.find('.date-year').val(),
    month = ( 0 + $datePicker.find('.date-month').val() ).slice(-2),
    day = ( 0 + $datePicker.find('.select-date').text() ).slice(-2),
    HH = ( 0 + $datePicker.find('.date-h').val() ).slice(-2),
    mm = ( 0 + $datePicker.find('.date-m').val() ).slice(-2),
    ss = ( 0 + $datePicker.find('.date-s').val() ).slice(-2);

$focusObj.val( year + '/' + month + '/' + day + ' ' + HH + ':' + mm + ':' + ss );

}

// 日付変更
$datePicker.on('click', '.num', function(){

    $('.select-date').removeClass('select-date');
    $( this ).addClass('select-date');    
    changeDate();

});

// 時間変更
$datePicker.on('change', 'select', function(){

    changeDate();

});

// 年月変更
$datePicker.find('.calender-move').on('click', function(){

let moveYear = $('.date-year').val(),
    moveMonth = $('.date-month').val();

    if ( $( this ).is('.prev') ) {
        moveMonth--;
        if( moveMonth < 1 ) {
            moveMonth = 12;
            moveYear--;
        }
    } else {
        moveMonth++;
        if( moveMonth > 12 ) {
            moveMonth = 1;
            moveYear++;
        }
    }
    $datePickerCalender.html( datePickerCalender( moveYear, moveMonth ) );

});

// 年月直接入力制限
$datePicker.find('.date-year, .date-month').on('change', function(){

    let moveYear = $('.date-year').val(),
        moveMonth = $('.date-month').val();

    if ( moveMonth > 12 ) moveMonth = 12;
    if ( moveMonth < 1 )  moveMonth = 1;
    if ( moveYear > 2099 ) moveYear = 2099;
    if ( moveYear < 2001 )  moveYear = 2001;
    $datePickerCalender.html( datePickerCalender( moveYear, moveMonth ) );

});

// ボタンメニュー
$datePicker.find('.menu button').on('click', function(){

     if ( $( this ).is('.close') ) {
        $datePicker.remove();
    } else {
        $focusObj.val('');
    }
    
});

});

return this;
};
}( jQuery ));
