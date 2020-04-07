// JavaScript Document

$(function(){

$('#menuButton').on('click', function(){
  $('#sideMenu').toggleClass('on');
});

/*
Page Top Link
*/
$( window ).scroll( function(){
  if ( $( this ).scrollTop() > $( this ).height() ){
    $('#pageTopLink').addClass('on');
  } else {
    $('#pageTopLink').removeClass('on');
  }
});


});

$( window ).on('load', function(){

  /*
  Anker scroll
  */
  var anlerScroll = function( hash ) {
    var speed = 300,
    fixedMenuheight =  $('#header').height() + $('#toolbar').height();
    var target = $ ( hash == '#' || hash == '' ? 'html' : hash );
    var position = target.offset().top - fixedMenuheight - 16;
    $('body, html').animate({ scrollTop : position }, speed, 'swing' );
  }

  // Page Open
  var hash = location.hash;
  if ( hash ){
    $('body,html').scrollTop( 0 );
    anlerScroll( hash );
  }

  // Click Event
  $('a[href^="#"]').on('touchstart click', function( e ){
    e.preventDefault();
    }).on('touchend mouseup', function( e ){
    e.preventDefault();
    if ( e.which !== 3 ) {
      anlerScroll( $( this ).attr('href') );
    }
  });

});