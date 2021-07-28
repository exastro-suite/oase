////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Dashboard
// 
////////////////////////////////////////////////////////////////////////////////////////////////////
function dashBoard(){}
dashBoard.prototype = {
  /* ------------------------------ *\
     Commonデータ
  \* ------------------------------ */
  'widgetInfo': {},
  'widgetPosition': [],
  'maxColumn': 12,
  'widgetCount': 0,
  'widgetBlankCount': 0,
  /* ------------------------------ *\
     Widgetデータ
  \* ------------------------------ */
  'widgetData': {
    /*
    widgetID: {
      'widget_id': widgetID,
      'name': widget name（class名などに使用）,
      'display_name': Widgetの名称,
      'description': Widgetの説明,
      'colspan': デフォルト列数,
      'rowspan': デフォルト行数,
      'unique': 複数設置可能か？1:NG,0:OK
    }
    */
    '1': {
      'widget_id': '1',
      'name': 'known',
      'display_name': '既知事象',
      'description': '既知事象の件数を円グラフで表示します。',
      'colspan': '2',
      'rowspan': '1',
      'unique': '1'
    },
    '2': {
      'widget_id': '2',
      'name': 'unknown',
      'display_name': '未知事象',
      'description': '未知事象の件数を円グラフで表示します。',
      'colspan': '2',
      'rowspan': '1',
      'unique': '1'
    },
    '3': {
      'widget_id': '3',
      'name': 'known-unknown',
      'display_name': '既知・未知事象（日）',
      'description': '既知・未知事象(日)の件数を円グラフで表示します。',
      'colspan': '2',
      'rowspan': '1',
      'unique': '1'
    },
    '21': {
      'widget_id': '21',
      'name': 'known-unknown-date',
      'display_name': '時間帯別',
      'description': '既知・未知事象（時間帯別）の件数を棒グラフで表示します。',
      'colspan': '6',
      'rowspan': '1',
      'unique': '1'
    },
    '22': {
      'widget_id': '22',
      'name': 'known-unknown-day',
      'display_name': '日別',
      'description': '既知・未知事象（日別）の件数を棒グラフで表示します。',
      'colspan': '6',
      'rowspan': '1',
      'unique': '1'
    },
    '9999': {
      'widget_id': '9999',
      'name': 'test',
      'display_name': 'テストWidget',
      'description': 'テスト用Widget',
      'colspan': '3',
      'rowspan': '4',
      'unique': '0'
    }
  },
  /* ------------------------------ *\
     初期設定
  \* ------------------------------ */
  'setup': function( target, widgetInfo ){
    const db = this;
    if ( widgetInfo !== undefined ) db.widgetInfo = widgetInfo;  
    db.$window = $( window );
    db.$body = $('body'),
    db.$main = $('.oase-main'),
    db.$db = $( target );
    db.$style = $('<style/>', {'class': 'dashboard-grid-style'});
    db.$dbBody = $('<div/>', {'class': 'dashboard-body'});
    
    db.$dbBody.append( $('<div/>', {'class': 'dashboard-loading'}));
    db.$db.append( db.$style, db.$dbBody );
    db.addModal();
    
    db.setWidget();
    db.widgetMove();
    
    // Blank追加用
    db.$dbBody.append('<div class="add-blank"></div>');
    
    // メニューボタンの設定
    db.$main.find('.oase-button').on('click', function(){
      const type = $( this ).attr('data-button');
      switch( type ) {
        case 'edit':
          db.editMode();
          break;
        case 'add':
          db.$addModal.find('.oase-modal-body').html( db.widgetAddList() );
          modalOpen('#add-widget');
          break;
        case 'save':
          
          break;
        case 'reset':
          
          break;
        case 'cancel':
          location.reload();
          break;
      }
    });
    
    // Widgetボタンの設定
     db.$db.on('click', '.widget-edit-button', function(){
      const $b = $( this ),
            $w = $b.closest('.widget-grid'),
            setID = $w.attr('id'),
            type = $b.attr('data-type');
      switch( type ) {
        case 'edit':
          db.$editModal.find('.oase-modal-body').html( db.widgetEditList( setID ) );
          modalOpen('#edit-widget');
          break;
        case 'delete':
          if ( confirm('Widgetを削除しますか？') ) {
            db.deleteWidget( setID );
          }
          break;
      }
     });
    
  },
  /* ------------------------------ *\
     Widget初期配置
  \* ------------------------------ */
  'setWidget': function(){
    const db = this;
    // Widget情報が無ければ初期値を読み込む
    db.newWidgetInfo();
         
    let wa = '<div class="dashboard-area">';
    
    const wi = db.widgetInfo,
          wp = db.widgetPosition;
    for ( const key in wi ) {
    
      // Widget HTML
      wa += db.widgetHTML( key, wi[key] );
            
      // 位置情報
      const r = Number( wi[key]['row'] ),
            c = Number( wi[key]['col'] ),
            rs = Number( wi[key]['rowspan'] ),
            cs = Number( wi[key]['colspan'] );
      for ( let j = 0; j < rs; j++ ) {
        if ( wp[r+j] === undefined ) wp[r+j] = [];
        for ( let k = 0; k < cs; k++ ) {
          let column = c + k;
          if ( column > db.maxColumn ) break;
          wp[r+j][column] = key;
        }
      }
    }
    
    wa += db.paddingblankHTML(); // 隙間をBlankで埋める    
    wa += '</div>';
    
    db.$dbBody.html( wa );
    db.updatePosition();
    
        
  },
  /* ------------------------------ *\
     位置情報更新
  \* ------------------------------ */
  'updatePosition': function(){
    const db = this,
          wp = db.widgetPosition,
          ws = [];
    if ( wp !== undefined ) {
      const rows = wp.length;
      for ( let i = 0; i < rows; i++ ) {
        if ( wp[i] !== undefined ) {
          ws.push('"' + wp[i].join(' ') + '"');
        }
      } 
    }
    // Grid style
    const gs = '.dashboard-area{'
    + 'grid-template-areas:' + ws.join(' ') + ';}';
    db.$style.html( gs );
  },
  /* ------------------------------ *\
     Widget配置ID
  \* ------------------------------ */
  'newSetId': function(){
    const db = this,
          setIdList = Object.keys( db.widgetInfo ),
          whileFlag = true;
    // 重複がないかチェックする
    let setID = 'w' + db.widgetCount++;
    while( whileFlag ) {
      if ( setIdList.indexOf( setID ) === -1 ) break;
      setID = 'w' + db.widgetCount++;
    }  
    return setID;
  },
  /* ------------------------------ *\
     Widget Blank ID
  \* ------------------------------ */
  'newBlankId': function(){
    return 'b' + this.widgetBlankCount++;
  },
  /* ------------------------------ *\
     WidgetInfo初期化（初期表示設定）
  \* ------------------------------ */
  'newWidgetInfo': function(){
    const db = this;
    db.widgetInfo = {};
    
    // 初期配置 Widget [ WidgetID, 行, 列, rowspan, colspan ]
    const initialWidget = [
      [3,0,0,2,2],
      [1,0,2,2,2],
      [2,0,4,2,2],
      [21,0,6,1,6],
      [22,1,6,1,6]
    ];
    
    const wi = db.widgetInfo,
          initialWidgetLength = initialWidget.length;
    for ( let i = 0; i < initialWidgetLength; i++ ) {
      const setID = db.newSetId();
      wi[setID] = $.extend( true, {}, db.widgetData[ initialWidget[i][0] ] );
      wi[setID]['row'] = String( initialWidget[i][1] );
      wi[setID]['col'] = String( initialWidget[i][2] );
      wi[setID]['rowspan'] = String( initialWidget[i][3] );
      wi[setID]['colspan'] = String( initialWidget[i][4] );
    }
  },
  /* ------------------------------ *\
     Widget HTML
  \* ------------------------------ */
  'widgetHTML': function( widgetSetID, widgetData ){
    const db = this;
    let widgetHTML = ''
    + '<div id="' + widgetSetID + '" '
        + 'style="grid-area:' + widgetSetID + '" '
        + 'class="widget-grid" '
        + 'data-widget-id="' + widgetData['widget_id'] + '" '
        + 'data-widget-display="' + widgetData['display'] + '" '
        + 'data-widget-title="' + widgetData['title'] + '" '
        + 'data-widget-background="' + widgetData['background'] + '" '
        + 'data-rowspan="' + widgetData['rowspan'] + '" '
        + 'data-colspan="' + widgetData['colspan'] + '">'
      + '<div class="widget">'
        + '<div class="widget-header">'
          + '<div class="widget-move-knob"></div>'
          + '<div class="widget-name"><span class="widget-name-inner">' + db.textEntities( widgetData['display_name'] ) + '</span>'
            + '<div class="widget-edit-menu">'
              + '<ul class="widget-edit-menu-list">'
                + '<li class="widget-edit-menu-item"><button class="widget-edit-button widget-edit" data-type="edit"><em class="owf owf-edit"></em></button></li>'
                + '<li class="widget-edit-menu-item"><button class="widget-edit-button widget-delete" data-type="delete"><em class="owf owf-cross"></em></button></li>'
              + '</ul>'
            + '</div>'
          + '</div>'
        + '</div>'
        + '<div class="widget-body">'
          + db.widget( widgetData['widget_id'], 'setup' )
        + '</div>'
      + '</div>'
    + '</div>';
    
    return widgetHTML;
  },
  /* ------------------------------ *\
     Widget Loading HTML
  \* ------------------------------ */
  'loadingHTML': function(){
    return '<div class="widget-loading"></div>';
  },  
  /* ------------------------------ *\
     Widget Blank HTML
  \* ------------------------------ */
  'blankHTML': function( blankID ){
    return '<div id="' + blankID + '" style="grid-area:' + blankID + '" class="widget-blank-grid" data-rowspan="1" data-colspan="1">'
      + '<div class="widget-blank"></div>'
    + '</div>';
  },
  /* ------------------------------ *\
     Position undefinde分のBlankHTML
  \* ------------------------------ */
  'paddingblankHTML': function(){
    const db = this,
          wp = db.widgetPosition,
          rows = wp.length;
    let blankHTML = '';
    for ( let i = 0; i < rows; i++ ) {
      if ( wp[i] === undefined ) wp[i] = [];
      for ( let j = 0; j < db.maxColumn; j++ ) {
        if ( wp[i][j] === undefined ) {
          const blankID = db.newBlankId();
          wp[i][j] = blankID;
          blankHTML += db.blankHTML( blankID );
        }
      }
    }
    return blankHTML;
  },
  /* ------------------------------ *\
     位置情報のundefinedをBlankで埋める
  \* ------------------------------ */
  'paddingblank': function(){
    const db = this;
    db.$dbBody.find('.dashboard-area').append( db.paddingblankHTML() );
    db.updatePosition();
  },
  /* ------------------------------ *\
     Widgetを削除する
  \* ------------------------------ */
  'deleteWidget': function( setID ){
    const db = this;
    $('#' + setID ).remove();
    db.widgetPositionDelete( setID );
    db.paddingblank();
    delete db.widgetInfo[ setID ];
  },
  /* ------------------------------ *\
     CSS gridが使えるかチェック
  \* ------------------------------ */
  'checkCssGrid': function(){
    const $checkDiv = $('<div/>');
    $checkDiv.css('display', 'grid');
    return ( $checkDiv.css('display') !== 'grid')? false: true;
  },

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  モード変更
// 
////////////////////////////////////////////////////////////////////////////////////////////////////

  /* ------------------------------ *\
     閲覧から編集モードへ
  \* ------------------------------ */
  'editMode': function(){
    const db = this;
    
    // 上下にBlank行を追加する
    db.widgetPosition.unshift([]);
    db.widgetPosition.push([]);
    db.paddingblank();
    db.updatePosition();
    
    db.editblankEvent();
    
    db.$main.attr('data-mode', 'edit');
    
  },
  
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  Widget追加・編集
// 
////////////////////////////////////////////////////////////////////////////////////////////////////
  
  /* ------------------------------ *\
     モーダルをセット
  \* ------------------------------ */
  'addModal': function(){
    const db = this;
    db.$addModal = $('<div/>', {
      'class': 'oase-modal',
      'id': 'add-widget'
    }).append(''
    + '<div class="oase-modal-main">'
      + '<div class="oase-modal-inner">'
        + '<div class="oase-modal-content">'
          + '<div class="oase-modal-header">'
            + '<div class="oase-modal-title"><em class="owf owf-plus"></em> Widgetの追加</div>'
          + '</div>'
          + '<div class="oase-modal-body"></div>'
          + '<div class="oase-modal-footer">'
            + '<ul class="oase-button-group">'
              + '<li><button class="oase-button" data-button="cancel"><em class="owf owf-cross"></em><span>キャンセル</span></button></li>'
              + '<li><button class="oase-button" data-button="ok"><em class="owf owf-plus"></em><span>決定</span></button></li>'
            + '</ul>'
          + '</div>'
        + '</div>'
      + '</div>'
    + '</div>'
    );
    
    db.$editModal = $('<div/>', {
      'class': 'oase-modal',
      'id': 'edit-widget',
      'widget': ''
    }).append(''
    + '<div class="oase-modal-main">'
      + '<div class="oase-modal-inner">'
        + '<div class="oase-modal-content">'
          + '<div class="oase-modal-header">'
            + '<div class="oase-modal-title"><em class="owf owf-plus"></em> Widgetの編集</div>'
          + '</div>'
          + '<div class="oase-modal-body"></div>'
          + '<div class="oase-modal-footer">'
            + '<ul class="oase-button-group">'
              + '<li><button class="oase-button" data-button="cancel"><em class="owf owf-cross"></em><span>キャンセル</span></button></li>'
              + '<li><button class="oase-button" data-button="ok"><em class="owf owf-check"></em><span>決定</span></button></li>'
            + '</ul>'
          + '</div>'
        + '</div>'
      + '</div>'
    + '</div>'
    );
    db.$body.append( db.$addModal, db.$editModal, '<div class="oase-modal-overlay"></div>');
    
    db.$addModal.find('.oase-button').on('click', function(){
      const type = $( this ).attr('data-button'),
            widgetID = db.$addModal.find('.widget-select-radio:checked').val();
      switch( type ) {
        case 'ok':
          db.addWidget( widgetID );
          modalClose('#add-widget');
          break;
        case 'cancel':
          modalClose('#add-widget');
          break;
      }
    });
    
    db.$editModal.find('.oase-button').on('click', function(){
      const type = $( this ).attr('data-button');
      switch( type ) {
        case 'ok':
          
          break;
        case 'cancel':
          modalClose('#edit-widget');
          break;
      }
    });
    
  },
  /* ------------------------------ *\
     Widget追加リスト
  \* ------------------------------ */
  'widgetAddList': function() {
    const db = this,
          widgetList = db.widgetData;
    let widgetSelectHTML = '<div class="oase-modal-block"><h3>Widgetの選択</h3><div class="widget-select"><table class="widget-select-table"><tbody>';

    for ( let key in widgetList ) {
      
        // ユニークチェック
        let uniqueClass =  '';
        if ( widgetList[key]['unique'] === '1' ) {
          if ( db.$dbBody.find('.widget-grid[data-widget-id="' + key + '"]').length ) {
            uniqueClass =  ' disabled';
          }
        }
        widgetSelectHTML += ''
          + '<tr class="widget-select-row' + uniqueClass + '">'
            + '<th class="widget-select-name">'
              + '<label class="widget-select-label"><input class="widget-select-radio" type="radio" name="widget-radio" value="' + widgetList[key]['widget_id'] + '"' + uniqueClass + '>' + widgetList[key]['display_name'] + '</label>'
            + '</th>'
            +'<td class="widget-select-description">' + widgetList[key]['description'] + '</td>'
          + '</tr>'

    }
    widgetSelectHTML += '</tbody></table></div></div>'

    const $WidgetAdd = $( widgetSelectHTML );

    // 行クリックで選択
    $WidgetAdd.find('.widget-select-table').on('click', '.widget-select-row', function(){
      const $radio = $( this ).find('.widget-select-radio');
      if ( !$radio.is(':disabled') ) {
        $radio.prop('checked', true );
      }
    });

    return $WidgetAdd;
  },
  /* ------------------------------ *\
     設置可能なBlankを調べる
  \* ------------------------------ */
  'checkSetBlank': function( setID ){
    const db = this,
          wi = db.widgetInfo[ setID ],
          wp = db.widgetPosition,
          rows = wp.length;
    for ( let i = 0; i < rows; i++ ) {
      const cols = wp[i].length;
      for ( let j = 0; j < cols; j++ ) {
        if ( wp[i][j].match(/^b/) ) {
          const rowspan = wi.rowspan,
                colspan = wi.colspan;
          // 基準位置からrowspan,colspan分すべてBlankかチェックする
          const blankCheck = function(){
            for ( let k = 0; k < rowspan; k++ ) {
              const rowPlus = i + k;
              if ( wp[rowPlus] === undefined ) return true;
              for ( let l = 0; l < colspan; l++ ) {
                const colPlus = j + l;
                if ( colPlus >= db.maxColumn ||
                  ( wp[rowPlus][colPlus] !== undefined && wp[rowPlus][colPlus].match(/^w/))) {
                  return false;
                }
              }
            }
            return true;
          }
          if ( blankCheck() ) {
            return wp[i][j];
          }
        }
      }
    }
    // 設置不可
    return false;
  },
  /* ------------------------------ *\
     Widget追加
  \* ------------------------------ */
  'addWidget': function( widgetID ) {
    const db = this,
          wd = db.widgetData[widgetID],
          wi = db.widgetInfo,
          setID = db.newSetId(),
          $widget = $( db.widgetHTML( setID, wd ) );
    
    wi[setID] = $.extend( true, {}, wd );
    const targetBlankID = db.checkSetBlank( setID );
    
    if ( targetBlankID !== false ) {
      db.widgetPositionChange( targetBlankID, setID );
    } else {
      // 設置可能な場所がない場合新しい行に設置する
      db.setWidgetSpan( db.widgetPosition.length, 0, setID );
    }
    db.paddingblank();
    
    db.$dbBody.find('.dashboard-area').append( $widget );
    db.updatePosition();
    
    // 追加したWidgetまでスクロールする
    const scrollTop = $widget.position().top + db.$dbBody.scrollTop();
    db.$dbBody.animate({ scrollTop: scrollTop }, 300, 'swing');
  },
  /* ------------------------------ *\
     Widget編集リスト
  \* ------------------------------ */
  'widgetEditList': function( setID ) {
    const db = this,
          widgetList = db.widgetData,
          widget = db.widgetInfo[ setID ],
          widgetID = widget['widget_id'];

    let editHTML = '<div class="oase-config-body"><table><tr>'
            + '<th><div class="cell-inner">列サイズ</div></th>'
            + '<td class="input-number"><div class="cell-inner"><label><input type="number" value="7" min="1" max="12"><span>列</span></label></div></td>'
          + '</tr><tr>'
            + '<th><div class="cell-inner">行サイズ</div></th>'
            + '<td class="input-number"><div class="cell-inner"><label><input type="number" value="7" min="1" max="6"><span>行</span></label></div></td>'
          + '</tr></table></div>'
    db.widget( widgetID, 'edit');

    return $( editHTML );
  },

  
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  Widget移動
// 
////////////////////////////////////////////////////////////////////////////////////////////////////
  
  /* ------------------------------ *\
     移動可能なBlankをチェックする
  \* ------------------------------ */
  'checkMovableBlank': function( setID ){
    const db = this,
          wi = db.widgetInfo[ setID ],
          wp = db.widgetPosition,
          rows = wp.length;
    for ( let i = 0; i < rows; i++ ) {
      const cols = wp[i].length;
      for ( let j = 0; j < cols; j++ ) {
        if ( wp[i][j].match(/^b/) ) {
          const rowspan = wi.rowspan,
                colspan = wi.colspan;
          // 基準位置からrowspan,colspan分すべてBlankかチェックする
          const blankCheck = function(){
            for ( let k = 0; k < rowspan; k++ ) {
              const rowPlus = i + k;
              if ( wp[rowPlus] === undefined ) return false;
              for ( let l = 0; l < colspan; l++ ) {
                const colPlus = j + l;
                if ( colPlus >= db.maxColumn ||
                  ( wp[rowPlus][colPlus] !== undefined && wp[rowPlus][colPlus].match(/^w/))) {
                  return false;
                }
              }
            }
            return true;
          }
          if ( blankCheck() ) {
            $('#' + wp[i][j] ).addClass('movable-blank');
          }
        }
      }
    }
  },
  /* ------------------------------ *\
     SetIDから位置を返す
  \* ------------------------------ */
  'getWidgetPosition': function( setID ){
    const db = this,
          wp = db.widgetPosition,
          rows = wp.length;
    for ( let i = 0; i < rows; i++ ) {
      const cols = wp[i].length;
      for ( let j = 0; j < cols; j++ ) {
        if ( wp[i][j] === setID ) {
          return [ i, j ];
        }
      }
    }
    return undefined;
  },  
  /* ------------------------------ *\
     位置情報から指定のsetIDをundefinedに
  \* ------------------------------ */
  'widgetPositionDelete': function( setID ) {
    const db = this,
          wp = db.widgetPosition,
          rows = wp.length;
    for ( let i = 0; i < rows; i++ ) {
      const cols = wp[i].length;
      for ( let j= 0; j < cols; j++ ) {
        if ( wp[i][j] === setID ) wp[i][j] = undefined;
      }
    }
  },
  /* ------------------------------ *\
     指定blankにWidgetをセットする
  \* ------------------------------ */
  'widgetPositionChange': function( blankID, setID ){
    const p = this.getWidgetPosition( blankID );
    this.setWidgetSpan( p[0], p[1], setID );
  },
  /* ------------------------------ *\
     指定位置からrow,col分埋める
  \* ------------------------------ */
  'setWidgetSpan': function( row, col, setID ){
    const db = this,
          wp = db.widgetPosition,
          wd = db.widgetInfo[ setID ],
          rs = wd.rowspan,
          cs = wd.colspan;
    for ( let i = 0; i < rs; i++ ) {
      const rp = row + i;
      if ( wp[rp] === undefined ) wp[rp] = [];
      for ( let j = 0; j < cs; j++ ) {
        const cp = col + j;
        if ( cp > db.maxColumn ) break;
        // 対象がBlankの場合要素を削除する
        const checkID = wp[rp][cp];
        if ( checkID !== undefined && checkID.match(/^b/) ) {
          $('#' + checkID ).remove();
        }
        wp[rp][cp] = setID;
      }
    }
  },
  /* ------------------------------ *\
     Widget移動イベント
  \* ------------------------------ */
  'widgetMove': function(){
    const db = this;
    db.$dbBody.on('mousedown', '.widget-move-knob', function( e ){
      const $window = $( window ),
            $dbBody = db.$dbBody,
            $widget = $( this ).closest('.widget-grid'),
            setID = $widget.attr('id'),
            widgetData = db.widgetInfo[ setID ],
            widgetWidth = $widget.outerWidth(),
            widgetHeight = $widget.outerHeight(),
            initialID = 'b' + db.widgetBlankCount,
            positionTop = e.pageY - $window.scrollTop(),
            positionLeft = e.pageX - $window.scrollLeft();
      let targetID = setID;
      
      db.onScrollEvent();
      db.editblankEventOff(); // Blank周りのイベントオフ
      db.deselection(); // 選択の解除
      db.widgetPositionDelete( setID ); // 位置情報を削除
      db.paddingblank(); // 隙間をBlankに 
      db.checkMovableBlank( setID ); // 移動可能部分のチェック

      $widget.addClass('widget-move').css({
        'left': 0,
        'top': 0,
        'transform': 'translate3d(' + positionLeft + 'px,' + positionTop + 'px,0)',
        'width': widgetWidth,
        'height': widgetHeight
      });

      // Rowspanが1の場合は置き換わるブランクの高さを調整する
      const $initialBlank = $('#' + initialID ).find('.widget-blank');
      if ( widgetData['rowspan'] === '1' ) {
        $initialBlank.css('height', widgetHeight + 'px');
      }
      
      $dbBody.find('.movable-blank').on({
        'mouseenter.widgetMove': function(){ targetID = $( this ).attr('id'); },
        'mouseleave.widgetMove': function(){ targetID = initialID; }
      });

      $window.on({
        'mousemove.widgetMove': function( e ){
          const movePositionTop = e.pageY - $window.scrollTop(),
                movePositionLeft = e.pageX - $window.scrollLeft();
          $widget.css({
            'transform': 'translate3d(' + movePositionLeft + 'px,' + movePositionTop + 'px,0)'
          });
        },
        'mouseup.widgetMove': function(){
          $window.off('mousemove.widgetMove mouseup.widgetMove');
          $dbBody.find('.movable-blank')
            .off('mouseenter.widgetMove mouseleave.widgetMove').removeClass('movable-blank');
          $widget.removeClass('widget-move').attr('style', 'grid-area:' + setID );
          $initialBlank.removeAttr('style');
          
          db.offScrollEvent();
          db.widgetPositionChange( targetID, setID ); // 対象と位置を入れ替える
          db.updatePosition(); // 位置情報更新
          db.editblankEvent(); // Blank周りのイベントセット
        }
      });
    });  
  },
  
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   枠外移動スクロール
// 
////////////////////////////////////////////////////////////////////////////////////////////////////

  'scrollTimer': false,
  
  'onScrollEvent': function() {
    const db = this,
          scrollSpeed = 80,
          scrollFrame = 1000 / 15;
    let vertical, horizontal;
    
    const dashboardScroll = function() {
      if ( db.scrollTimer === false ) {
        db.scrollTimer = setInterval( function() {
          const scrollTop = db.$dbBody.scrollTop(),
                scrollLeft = db.$dbBody.scrollLeft(),
                scrollVertical = ( vertical === 'bottom')? scrollSpeed : -scrollSpeed,
                scrollHorizontal = ( horizontal === 'right')? scrollSpeed : -scrollSpeed;
          db.$dbBody.stop(0,0).animate({
            scrollTop : scrollTop + scrollVertical,
            scrollLeft : scrollLeft + scrollHorizontal
          }, scrollSpeed, 'linear');
        }, scrollFrame );
      }
    };
    
    db.$window.on('mousemove.dashboardScroll', function( e ){
      // 上下左右判定
      const width = db.$dbBody.outerWidth(),
            height = db.$dbBody.outerHeight(),
            offsetLeft = db.$dbBody.offset().left,
            offsetTop = db.$dbBody.offset().top;
      if ( e.pageY < offsetTop ) vertical = 'top';
      if ( e.pageY > offsetTop + height ) vertical = 'bottom';
      if ( e.pageX < offsetLeft ) horizontal = 'left';
      if ( e.pageX > offsetLeft + width ) horizontal = 'right';
      
      if ( $( e.target ).closest('.dashboard-body').length ) {
        clearInterval( db.scrollTimer );
        db.scrollTimer = false;
      } else {
        dashboardScroll();
      }
    });
  },
  'offScrollEvent': function() {
    const db = this;
    db.$window.off('mousemove.dashboardScroll');
    clearInterval( db.scrollTimer );
    db.scrollTimer = false;
  },

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Blank追加・削除
// 
////////////////////////////////////////////////////////////////////////////////////////////////////
  
  /* ------------------------------ *\
     Blank追加・削除イベントの追加
  \* ------------------------------ */
  'editblankEvent': function() {
    const db = this;
  
    let blankAddTopBottomFlag = '',
        blankAddWidgetSetID = '';
    
    // +Blank barを非表示
    const addWidgetBarHide = function() {
        db.$dbBody.find('.add-blank').removeAttr('style');
        db.$dbBody.find('.widget-grid, .widget-blank-grid').off('mousemove.blank');
        blankAddTopBottomFlag = '';
        blankAddWidgetSetID = '';
    };
    
    db.$dbBody.on({
      'mouseenter.blank': function(){
        const $widget = $( this ),
              $blankBar = db.$dbBody.find('.add-blank'),
              $area = $widget.closest('.dashboard-area'),
              setID = $widget.attr('id'),
              rowspan = Number( $widget.attr('data-rowspan') ),
              widgetHeight = $widget.outerHeight(),
              barWidth = $area.outerWidth(),
              barLeft = $area.position().left,
              barTop = $widget.position().top,
              wp = db.widgetPosition,
              position = db.getWidgetPosition( setID ),
              row = position[0],
              colLength = wp[row].length,
              barShowArea = 8,
              areaPadding = 8,
              scrollTop = db.$dbBody.scrollTop(),
              scrollLeft = db.$dbBody.scrollLeft();
        
        if ( blankAddWidgetSetID !== setID ) {
          blankAddWidgetSetID = setID;
          blankAddTopBottomFlag = '';
        }
        
        // 行すべてがBlankの場合削除可能とする
        if ( wp.length > 1 && wp[row].join('').indexOf('w') === -1 ) {
          for ( let i = 0; i < colLength; i++ ) {
            $('#' + wp[row][i] ).addClass('remove-blank owf');
          }
        }
        
        // Widgetの上か下かそれ以外
        const middleBarHide = function() {
          $blankBar.css('display', 'none');
        }
        const topBottomBarSet = function( direction ){
          const topBottomNum = ( direction === 'top')? -1 : rowspan,
                topBottomAdd = ( direction === 'top')? 0 : rowspan,
                topBottomPositionTop = ( direction === 'top')?
                  barTop - areaPadding + scrollTop :
                  barTop - areaPadding + scrollTop + widgetHeight;

          let addFlag = true;
          for ( let i = 0; i < colLength; i++ ) {
            const currentCol = wp[row][i],
                  checkRow = wp[row+topBottomNum];
            if ( checkRow !== undefined ) {
              if ( currentCol === checkRow[i] ) {
                addFlag = false;
                break;
              }
            }
          }

          if ( addFlag === true ) {
            $blankBar.css({
              'display': 'block',
              'width': barWidth - ( areaPadding * 2 ),
              'left': barLeft + areaPadding + scrollLeft,
              'top': topBottomPositionTop
            }).attr({
              'data-row': row + topBottomAdd
            });
          } else {
            middleBarHide();
          }
        };
        $widget.on('mousemove.blank', function( e ){
          if ( e.pageY - $widget.offset().top > widgetHeight - barShowArea ) {
            if ( blankAddTopBottomFlag !== 'bottom') {
              blankAddTopBottomFlag = 'bottom';
              topBottomBarSet( blankAddTopBottomFlag );
            }
          } else if ( e.pageY - $widget.offset().top < barShowArea ) {
            if ( blankAddTopBottomFlag !== 'top') {
              blankAddTopBottomFlag = 'top';
              topBottomBarSet( blankAddTopBottomFlag );
            }
          } else {
            if ( blankAddTopBottomFlag !== 'middle') {
              blankAddTopBottomFlag = 'middle';
              middleBarHide();
            }
          }
        }); 
      },
      'mouseleave.blank': function(){
        $( this ).off('mousemove.blank');
        db.$dbBody.find('.remove-blank').removeClass('remove-blank owf');
      }
    }, '.widget-grid, .widget-blank-grid');
    
    // 枠の外に出たら消す
    db.$dbBody.on({
      'mouseleave.blankbar': function(){
        addWidgetBarHide();
      },
      'mousemove.blankbar': function( e ){
        if ( e.target.className === 'dashboard-body' ||
             e.target.className === 'dashboard-area' ) {
          addWidgetBarHide();
        }
      }
    });
    
    // Blankを追加
    db.$dbBody.on('click.blankadd', '.add-blank', function(){
      const $addBlank = $( this ),
            row = $addBlank.attr('data-row'),
            scrollTop = db.$dbBody.scrollTop();

      db.widgetPosition.splice( row, 0, []);
      db.paddingblank();
      db.updatePosition();
      
      // スクロール位置をBlank追加前と同じにする
      db.$dbBody.scrollTop( scrollTop );
    });

    // Blankを削除
    db.$dbBody.on('click.blankremove', '.remove-blank', function(){
      const $blank = $( this ),
            setID = $blank.attr('id'),
            position = db.getWidgetPosition( setID ),
            row = position[0],
            colLength = db.widgetPosition[row].length;

      for ( let i = 0; i < colLength; i++ ) {  
        $('#' + db.widgetPosition[row][i] ).remove();
      }
      db.widgetPosition.splice( row, 1 );
      addWidgetBarHide();
      db.updatePosition();
    });

  },
  /* ------------------------------ *\
     Blank追加・削除イベントの削除
  \* ------------------------------ */
  'editblankEventOff': function() {
    const db = this;
    db.$dbBody.off('mouseenter.blank mouseleave.blank mouseleave.blankbar mousemove.blankbar click.blankadd click.blankremove');
  }, 
  
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   その他
// 
////////////////////////////////////////////////////////////////////////////////////////////////////
  
  /* ------------------------------ *\
     選択を解除する
  \* ------------------------------ */
  'deselection': function() {
    getSelection().removeAllRanges();
  },
  /* ------------------------------ *\
     テキストエンティティ化
  \* ------------------------------ */
  'textEntities': function( text ) {
    const entities = [
      ['&', 'amp'],
      ['\"', 'quot'],
      ['\'', 'apos'],
      ['<', 'lt'],
      ['>', 'gt'],
    ];
    if ( text !== undefined && text !== null && typeof text === 'string') {
      for ( var i = 0; i < entities.length; i++ ) {
        text = text.replace( new RegExp( entities[i][0], 'g'), '&' + entities[i][1] + ';' );
      }
    }
    return text;
  },
  /* ------------------------------ *\
     日時フォーマット
  \* ------------------------------ */
  'formatDate': function( date, format ) {
    // yyyy/MM/dd HH:mm:ss.sss
    format = format.replace(/yyyy/g, date.getFullYear());
    format = format.replace(/MM/g, ('0' + (date.getMonth() + 1)).slice(-2));
    format = format.replace(/dd/g, ('0' + date.getDate()).slice(-2));
    format = format.replace(/HH/g, ('0' + date.getHours()).slice(-2));
    format = format.replace(/mm/g, ('0' + date.getMinutes()).slice(-2));
    format = format.replace(/ss/g, ('0' + date.getSeconds()).slice(-2));
    format = format.replace(/SSS/g, ('00' + date.getMilliseconds()).slice(-3));
    return format;
  },
  /* ------------------------------ *\
     変数チェック
  \* ------------------------------ */
  'isset': function( data ) {
    return ( data === undefined || data === null || data === '')? false: true;
  },
  /* ------------------------------ *\
     ログ
  \* ------------------------------ */
  'log': function() {
    const argumentslength = arguments.length;
    for ( let i = 0; i < argumentslength; i++ ) {
      window.console.log( arguments[i] );
    }
  },
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   円グラフ
// 
////////////////////////////////////////////////////////////////////////////////////////////////////

  /* ------------------------------ *\
     円グラフを作成する
  \* ------------------------------ */
  'pieChart': function( widgetID, title, pieChartData ){
    const db = this,
          $db = db.$db;
    
    const xmlns = 'http://www.w3.org/2000/svg',
          radius = 50,  // 円グラフ半径
          strokeWidth = 20,  // 円グラフ線幅
          circumference = radius * 2 * Math.PI, // 円周（半径×２×円周率）
          cxcy = radius + strokeWidth,
          viewBox = cxcy * 2,
          viewBoxAttr = '0 0 ' + viewBox + ' ' + viewBox;
    
    // 円グラフ
    const $pieChartSvg = $( document.createElementNS( xmlns, 'svg') );
    $pieChartSvg.attr('class','pie-chart-svg').get(0).setAttribute('viewBox', viewBoxAttr );
    
    // 装飾
    const $pieChartSvgDecoration = $( document.createElementNS( xmlns, 'svg') );
    $pieChartSvgDecoration.attr('class','pie-chart-decoratio-svg').get(0).setAttribute('viewBox', viewBoxAttr );
    $pieChartSvgDecoration.html(
      '<circle cx="' + cxcy + '" cy="' + cxcy + '" r="' + ( cxcy - 5 ) + '" class="pie-chart-circle-outside"></circle>'
      + '<circle cx="' + cxcy + '" cy="' + cxcy + '" r="' + ( cxcy - 15 - strokeWidth ) + '" class="pie-chart-circle-inside"></circle>'
    );
    
    // 割合表示
    const $pieChartRatioSvg = $( document.createElementNS( xmlns, 'svg') );
    $pieChartRatioSvg.attr('class','pie-chart-ratio-svg').get(0).setAttribute('viewBox', viewBoxAttr );
    
    const outSideNamber = [];
    let totalNumber = 0,
        serialWidthNumber = 0,
        serialAngleNumber = -90,
        outsideGroupCheck = 0,
        outsideGroupNumber = -1,
        checkGroupText = '';
    
    // 合計値
    for ( let key in pieChartData ) {
      totalNumber += pieChartData[key][1];
    }
    
    // Table
    let tableHTML = ''
    + '<div class="db-table-wrap">'
      + '<table class="db-table">'
        + '<tbody>';
    for ( let key in pieChartData ) {
      tableHTML += ''
          + '<tr class="db-row" data-type="' + pieChartData[key][0] + '">'
            + '<th class="db-cell"><div class="db-cell-i">'
              + '<span class="db-usage usage-' + pieChartData[key][0] + '"></span>' + key
            + '</div></th>'
            + '<td class="db-cell"><div class="db-cell-i">'
              + pieChartData[key][1]
            + '</div></td>';
      switch( widgetID ) {
        case 1:
        case 2:
          tableHTML += '<td class="db-cell db-cell-button"><button class="tooltip detail oase-mini-button"><em class="owf owf-details"></em><span style="display: none;">詳細表示</span></button></td></tr>';
          break;
      }
      tableHTML += '</tr>'
    }
    tableHTML += ''
        + '</tbody>'
      + '</table>'
    + '</div>';
    
    for ( let key in pieChartData ) {
      const $pieChartCircle = $( document.createElementNS( xmlns, 'circle') ),
            $pieChartText = $( document.createElementNS( xmlns, 'text') );
      
      // 割合・幅の計算
      const className = 'circle-' + pieChartData[key][0],
            number = pieChartData[key][1],
            ratio = number / totalNumber,
            angle = 360 * ratio;
      
      // 幅
      let   ratioWidth = Math.round( circumference * ratio * 1000 ) / 1000;
      if ( serialWidthNumber + ratioWidth > circumference ) ratioWidth = circumference - serialWidthNumber;
      const remainingWidth =  Math.round( ( circumference - ( serialWidthNumber + ratioWidth ) ) * 1000 ) / 1000;

      // stroke-dasharrayの形に整える
      let strokeDasharray = '';
      if ( serialWidthNumber === 0 ) {
        strokeDasharray = ratioWidth + ' '+ remainingWidth + ' 0 0';
      } else {
        strokeDasharray = '0 ' + serialWidthNumber + ' ' + ratioWidth + ' '+ remainingWidth;
      }
      
      // 属性登録
      $pieChartCircle.attr({
        'cx': cxcy,
        'cy': cxcy,
        'r': radius,
        'class': 'pie-chart-circle ' + className,
        'style': 'stroke-dasharray:0 0 0 '+ circumference,
        'data-style': strokeDasharray,
        'data-type': pieChartData[key][0]
      });
      
      // 追加
      $pieChartSvg.append( $pieChartCircle );
      
      // 割合追加
      if ( ratio > 0 ) {
        const textAngle = serialAngleNumber + ( angle / 2 ),
              centerPosition = db.anglePiePosition( cxcy, cxcy, radius, textAngle );
        let ratioClass = 'pie-chart-ratio ' + className,
            x = centerPosition[0],
            y = centerPosition[1];
        
        const displayRatio = Math.round( ratio * 1000 ) / 10;
        
        // 特定値以下の場合は表示の調整をする
        if ( displayRatio < 2.5 ) {
          if ( outsideGroupCheck === 0 ) {
            checkGroupText += '@'; // グループフラグ
            outsideGroupNumber++;
            outSideNamber[outsideGroupNumber] = new Array();
          }
          outsideGroupCheck = 1;
          outSideNamber[outsideGroupNumber].push( [ratioClass,textAngle,displayRatio] );
        } else {
          // 30%以下の場合グループを分けない
          if ( displayRatio > 30 ) {
            outsideGroupCheck = 0;
            checkGroupText += 'X';
          }
          if ( displayRatio < 10 ) {
            ratioClass += ' rotate';
            let rotateAngle = textAngle;
            if ( textAngle > 90 ) rotateAngle = rotateAngle + 180;
            $pieChartText.attr('transform', 'rotate('+rotateAngle+','+x+','+y+')' );
             y += 1.5; //ベースライン調整
          } else {
             y += 2.5;
          }
          $pieChartText.html( displayRatio + '<tspan class="ratio-space"> </tspan><tspan class="ratio-mark">%</tspan>').attr({
            'x': x,
            'y': y,
            'text-anchor': 'middle',
            'class': ratioClass
          });
          $pieChartRatioSvg.append( $pieChartText );
        }
      }

      // スタート幅
      serialWidthNumber += ratioWidth;
      serialAngleNumber += angle;
      if ( serialWidthNumber > circumference ) serialWidthNumber = circumference;
    }
    // 2.5%以下は外側に表示する
    let outSideGroupLength = outSideNamber.length;
    if ( outSideNamber.length > 0 ) {
      // 最初と最後が繋がる場合、最初のグループを最後に結合する
      if ( checkGroupText.length > 2 && checkGroupText.slice( 0, 1 ) === '@' && checkGroupText.slice( -1 ) === '@' ) {
        outSideNamber[ outSideGroupLength - 1] = outSideNamber[ outSideGroupLength - 1].concat( outSideNamber[0] );
        outSideNamber.shift();
        outSideGroupLength = outSideNamber.length;
      }
      for ( let i = 0; i < outSideGroupLength; i++ ) {
        const outSideNamberLength = outSideNamber[i].length;
        if ( outSideNamberLength > 0 ) {
          const maxOutWidth = 14;
          // 配列の真ん中から処理する
          let arrayNumber = Math.floor( ( outSideNamberLength - 1 ) / 2 );
          for ( let j = 0; j < outSideNamberLength; j++ ) {
            arrayNumber = ( ( j + 1 ) % 2 !== 0 )? arrayNumber - j: arrayNumber + j; 
            if ( outSideNamber[i][arrayNumber] !== undefined ) {
              const $pieChartText = $( document.createElementNS( xmlns, 'text') ),
                    $pieChartLine = $( document.createElementNS( xmlns, 'line') ),
                    count = Math.floor( j / 2 ),
                    position = radius + maxOutWidth;
              let textAnchor = 'middle',
                  ratioClass = outSideNamber[i][arrayNumber][0]  + ' outside',
                  angle = outSideNamber[i][arrayNumber][1],
                  ratio = outSideNamber[i][arrayNumber][2],
                  newAngle = angle,
                  lineStartPositionAngle,
                  rotetaNumber,
                  verticalPositionNumber = 0;

              // 横位置調整
              const setAngle = 16 * count + 8,
                    setLineAngle = ( Number.isInteger( ratio ) )? 4: 6;
              if ( ( j + 1 ) % 2 !== 0 ) {
                newAngle -= setAngle;
                lineStartPositionAngle = newAngle + setLineAngle;
              } else {
                newAngle += setAngle;
                lineStartPositionAngle = newAngle - setLineAngle;
              }

              if ( newAngle > 0 && newAngle < 180 ) {
                verticalPositionNumber = 4;
                rotetaNumber = newAngle + 270;
              } else {
                rotetaNumber = newAngle + 90;
              }

              const outsidePosition = db.anglePiePosition( cxcy, cxcy, position, newAngle ),
                    x = outsidePosition[0],
                    y = outsidePosition[1],
                    lineStartPosition = db.anglePiePosition( cxcy, cxcy, position, lineStartPositionAngle ),
                    x1 = lineStartPosition[0],
                    y1 = lineStartPosition[1],
                    lineEndPosition = db.anglePiePosition( cxcy, cxcy, radius + strokeWidth / 2 - 2, angle ),
                    x2 = lineEndPosition[0],
                    y2 = lineEndPosition[1];

              $pieChartLine.attr({
                'x1': x1,
                'y1': y1,
                'x2': x2,
                'y2': y2,
                'class': 'pie-chart-ratio-line'
              });
              $pieChartText.html( ratio + '<tspan class="ratio-space"> </tspan><tspan class="ratio-mark">%</tspan>' ).attr({
                'x': x,
                'y': y + verticalPositionNumber,
                'text-anchor': textAnchor,
                'class': ratioClass,
                'transform': 'rotate(' + rotetaNumber + ',' + x + ',' +y + ')'
              });
              $pieChartRatioSvg.append( $pieChartText, $pieChartLine );
            }
          }
        }
      }
    }
    
    // テキスト
    const $pieChartTotalSvg = $( document.createElementNS( xmlns, 'svg') );
    $pieChartTotalSvg.get(0).setAttribute('viewBox', '0 0 ' + viewBox + ' ' + viewBox );
    $pieChartTotalSvg.attr('class','pie-chart-total-svg');

    const $pieChartName = $( document.createElementNS( xmlns, 'text') ).text( title ).attr({
      'class': 'pie-chart-total-name', 'x': '50%', 'y': '35%',
    });
    const $pieChartNumber = $( document.createElementNS( xmlns, 'text') ).text( totalNumber ).attr({
      'class': 'pie-chart-total-number', 'x': '50%', 'y': '50%',
    });
    const $pieChartTotal = $( document.createElementNS( xmlns, 'text') ).text('Total').attr({
      'class': 'pie-chart-total-text', 'x': '50%', 'y': '60%',
    });  
    $pieChartTotalSvg.append( $pieChartName, $pieChartNumber, $pieChartTotal );
    
    // SVG / HTML set
    const $pieChartHTML = $('<div class="pie-chart"><div class="pie-chart-inner"></div></div>' + tableHTML );
    $pieChartHTML.find('.pie-chart-inner').append( $pieChartSvgDecoration, $pieChartTotalSvg, $pieChartSvg, $pieChartRatioSvg );

    $db.find('.widget-grid[data-widget-id="' + widgetID + '"]').find('.widget-body').html( $pieChartHTML );
    
    // 円グラフアニメーション
    $pieChartSvg.ready( function(){
      setTimeout( function() {
        const $circles = $pieChartSvg.find('.pie-chart-circle'),
              circleLength = $circles.length;
        let circleAnimationCount = 0;
        $pieChartRatioSvg.css('opacity','1');
        $circles.each( function(){
          const $circle = $( this );
          if ( $circle.attr('data-style') !== undefined ) {
            $circle.attr('style', ''
              + 'stroke-dasharray:' + $circle.attr('data-style') + ';'
              + 'stroke-width: ' + strokeWidth + 'px;');
          }
        }).on({
          'transitionend webkitTransitionEnd': function() {
            // 全てのアニメーションが終わったら
            circleAnimationCount++;
            if ( circleAnimationCount >= circleLength ) {
              $pieChartHTML.removeClass('start');
              // 円グラフホバー
              $circles.on({
                'mouseenter': function(){
                  const $enter = $( this ),
                        dataType = $enter.attr('data-type');
                  if ( dataType !== undefined ) {
                    $enter.closest('.widget-body').find('tr[data-type="' + dataType + '"]').addClass('emphasis');
                    $enter.css('stroke-width', strokeWidth * 1.2 );
                  }
                },
                'mouseleave': function(){
                  const $leave = $( this ),
                        dataType = $leave.attr('data-type');
                  if ( dataType !== undefined ) {
                    $leave.css('stroke-width', strokeWidth );
                    $leave.closest('.widget-body').find('.emphasis').removeClass('emphasis');
                  }
                }
              });
              // Tableグラフホバー
              $pieChartHTML.find('.db-row').on({
                'mouseenter': function(){
                  const $enter = $( this ),
                        dataType = $enter.attr('data-type');
                  $enter.addClass('emphasis');
                  if ( dataType !== undefined ) {
                    $enter.closest('.widget-body').find('.pie-chart-circle.circle-' + dataType ).css('stroke-width', strokeWidth * 1.2 );
                  }
                },
                'mouseleave': function(){
                  const $leave = $( this ),
                        dataType = $leave.attr('data-type');
                  $leave.removeClass('emphasis');
                  if ( dataType !== undefined ) {
                    $leave.closest('.widget-body').find('.pie-chart-circle.circle-' + dataType ).css('stroke-width', strokeWidth );
                  }
                }
              });
            }        
          }
        });

      }, 100 );
    });
    
  },
  /* ------------------------------ *\
     角度から位置を求める
  \* ------------------------------ */
  'anglePiePosition': function( x1, y1, r, a ) {
    const x2 = x1 + r * Math.cos( a * ( Math.PI / 180 ) ),
          y2 = y1 + r * Math.sin( a * ( Math.PI / 180 ) );
    return [ x2, y2 ];
  },
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   既知・未知 積み上げグラフ
// 
////////////////////////////////////////////////////////////////////////////////////////////////////

  /* ------------------------------ *\
     積み上げグラフを作成する
  \* ------------------------------ */
  'stackedGraph': function( widgetID, usage, stackedGraphData ){
    const db = this,
          $db = db.$db,
          $sg = $db.find('.widget-grid[data-widget-id="' + widgetID + '"]').find('.widget-body'),
          sgLength = stackedGraphData.length;
    
    // 件数によってクラスを変更する
    let sgClass = '';
    
    
    
    
    let sgHTML = '<div class="stacked-graph' + sgClass + '">';
    
    // 合計値と最大値
    let sgTotla = [],
        sgMax = 0;
    for ( let i = 0; i < sgLength; i++ ) {
      const itemLength = stackedGraphData[i].length;
      for ( let j = 2; j < itemLength; j++ ) {
        if ( sgTotla[i] === undefined ) sgTotla[i] = 0;
        sgTotla[i] += stackedGraphData[i][j];
      }
      if ( sgTotla[i] > sgMax ) sgMax = sgTotla[i];
    }
    
    // グラフ縦軸
    const digit = String( sgMax ).length, // 桁数
          digitNumber = Math.pow( 5, digit - 1 ), // 縦軸の数
          graphMaxNumber = Math.ceil( sgMax / digitNumber ) * digitNumber; // グラフ最大値
    
    sgHTML += '<ol class="stacked-graph-vertical-axis">';
    const verticalAxisLength = graphMaxNumber / digitNumber;
    for( let i = 0; i <= verticalAxisLength; i++ ) {
      sgHTML += '<li class="stacked-graph-vertical-axis-item">' + ( i * digitNumber ) + '</li>';
    }
    sgHTML += '</ol>';

    // グラフ本体
    sgHTML += '<ol class="stacked-graph-horizontal-axis">';
    for ( let i = 0; i < sgLength; i++ ) {
      const sum = sgTotla[i],
            sumPer = Math.round( sum / graphMaxNumber * 100 ),
            itemLength = stackedGraphData[i].length;
            
      sgHTML += ''
      + '<li class="stacked-graph-item">'
        + '<dl class="stacked-graph-item-inner" data-id="' + i + '">'
          + '<dt class="stacked-graph-item-title"><span class="day-number">' + stackedGraphData[i][1] + '</span></dt>'
          + '<dd class="stacked-graph-bar">';      
      if ( sum !== 0 ) {
        sgHTML += '<ul class="stacked-graph-bar-group" data-style="' + sumPer + '%">';
        for ( let j = 2; j < itemLength; j++ ) {
          const itemPer = Math.round( stackedGraphData[i][j] / sum * 100 );
          sgHTML += '<li class="stacked-graph-bar-item stacked-graph-bar-' + usage[j][0] + '" style="height: ' + itemPer + '%"></li>';
        }
        sgHTML += '</ul>';
      }
      sgHTML += ''
          + '</dd>'
        + '</dl>'
      + '</li>';
    }
    sgHTML += '</ol></div></div><div class="stacked-graph-popup"></div>';

    sgHTML += '</div>';
    $sg.html( sgHTML );
    
    setTimeout( function() {
      // アニメーション開始
      $sg.find('.stacked-graph-bar-group').each( function(){
        const $bar = $( this );
        $bar.attr('style', 'height:' + $bar.attr('data-style') );
      });
      
      // 棒グラフ詳細表示
      $sg.find('.stacked-graph-item-inner').on({
        'mouseenter': function() {
          const $bar = $( this ),
                $pop = $sg.find('.stacked-graph-popup'),
                dataID = $bar.attr('data-id'),
                resultData = stackedGraphData[dataID],
                resultLength = resultData.length,
                total = sgTotla[dataID];
          
          const resultRow = function( c, u, n ){
            return ''
            + '<tr class="db-row">'
              + '<th class="db-cell"><div class="db-cell-i">'
                + '<span class="db-usage usage-' + c + '"></span>' + u
              + '</div></th>'
              + '<td class="db-cell"><div class="db-cell-i"">'
                + n
              + '</div></td></tr>';
          };
          
          const setResult = function(){
              // Table
              let tableHTML = ''
                + '<div class="stacked-graph-popup-close"></div>'
                + '<div class="stacked-graph-popup-date">' + resultData[0] + '</div>'
                + '<div class="db-table-wrap"><table class="db-table"><tbody>';
              
              for ( let i = 2; i < resultLength; i++ ) {
                tableHTML += resultRow( usage[i][0], usage[i][1], resultData[i] );
              }
              tableHTML += resultRow( 'total', '合計', total );

              tableHTML += '</tbody></table></div>';
              $pop.html( tableHTML );
              $pop.find('.stacked-graph-popup-close').on('click', function(){
                $pop.removeClass('fixed').html('').hide();
              });
          };

          const setPopPosition = function( pageX, pageY ) {
              const $window = db.$window,
                    scrollTop = $window.scrollTop(),
                    scrollLeft = $window.scrollLeft(),
                    windowWidth = $window.width(),
                    popupWidth = $pop.outerWidth();

              let leftPosition = pageX - scrollLeft;

              // 右側チェック
              if ( leftPosition + ( popupWidth / 2 ) > windowWidth ) {
                leftPosition = leftPosition - (( leftPosition + ( popupWidth / 2 ) ) - windowWidth );
              }
              // 左側チェック
              if ( leftPosition - ( popupWidth / 2 ) < 0 ) {
                leftPosition = popupWidth / 2;
              }

              $pop.show().css({
                'left': leftPosition,
                'top': pageY - scrollTop - 16
              });
          };

          $bar.on('click.stackedGraphPopup', function( e ){
            if ( $pop.is('.fixed') ) {
              setPopPosition( e.pageX, e.pageY );
              setResult();
            }
            $pop.toggleClass('fixed');
          });

          db.$window.on('mousemove.stackedGraphPopup', function( e ) {
            const $target = $( e.target ).closest('.stacked-graph-item');
            if ( $target.length ) {
              let y = 0;
              if ( $target.find('.stacked-graph-bar-group').length ) {
                y = $target.find('.stacked-graph-bar-group').offset().top;
              } else {
                y = $target.find('.stacked-graph-item-title').offset().top;
              }
              if ( !$pop.is('.fixed') ) {
                setPopPosition( e.pageX, y );
                setResult();
              }
            }            
          });
        },
        'mouseleave': function() {
          $('.stacked-graph-popup').not('.fixed').html('').hide();
          $( this ).off('click.stackedGraphPopup');
          db.$window.off('mousemove.stackedGraphPopup');
        }
      });
    }, 100 );
  },

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Widget
// 
////////////////////////////////////////////////////////////////////////////////////////////////////
  'widget': function( widgetID, mode ){
    const db = this;
    
    const widget = {
      /*
      widgetID: {
        'setup': {
          widget本体
        },
        'edit': {
          個別設定項目
        }
      }
      */
      '1': {
        'setup': function(){
          setTimeout( function(){
          db.pieChart( 1, 'Known', {
            'rule1': ['known1',35],
            'rule2': ['known2',30],
            'rule3': ['known3',25],
            'rule4': ['known4',20],
            'rule5': ['known5',2],
            'その他': ['known6',60],
          });
          }, 10 );
          return db.loadingHTML();
        }
      },
      '2': {
        'setup': function(){
          setTimeout( function(){
          db.pieChart( 2, 'Unknown', {
            'rule1': ['unknown1',35],
            'rule2': ['unknown2',30],
            'rule3': ['unknown3',25],
            'rule4': ['unknown4',20],
            'rule5': ['unknown5',2],
            'その他': ['unknown6',60],
          });
          }, 10 );
          return db.loadingHTML();
        }
      },
      '3': {
        'setup': function(){
          setTimeout( function(){
          db.pieChart( 3, 'Known/Unknown', {
            '既知事象': ['known1',50],
            '未知事象': ['unknown1',55]
          });
          }, 10 );
          return db.loadingHTML();
        }
      },
      '21': {
        'setup': function(){
            db.request_widget_data(21);
            return;
        }
      },
      '22': {
        'setup': function(){
          setTimeout( function(){
          db.stackedGraph( 22,
            [
              ['time', '時間'],
              ['time', '時間'],
              ['known', '既知事象'],
              ['unknown', '未知事象']
            ],
            [
              ['0時','0',0,0],
              ['1時','1',1,1],
              ['2時','2',2,1],
              ['3時','3',3,2],
              ['4時','4',4,2],
              ['5時','5',5,3],
              ['6時','6',6,3],
              ['7時','7',7,4],
              ['8時','8',8,4],
              ['9時','9',9,5],
              ['10時','10',10,5],
              ['11時','11',11,5],
              ['12時','12',15,7],
              ['13時','13',11,6],
              ['14時','14',10,5],
              ['15時','15',9,5],
              ['16時','16',8,4],
              ['17時','17',7,4],
              ['18時','18',6,3],
              ['19時','19',5,3],
              ['20時','20',4,2],
              ['21時','21',3,2],
              ['22時','22',2,1],
              ['23時','23',1,1]
            ]
          );
          }, 10 );
          return db.loadingHTML();
        }
      }
    };
    
    if ( widget[ widgetID ] !== undefined && widget[ widgetID ][ mode ] !== undefined ) {
      return widget[ widgetID ][ mode ]();
    } else {
      window.console.warn('Widget undefined.');
    }
  },

  'request_widget_data': function( widgetID ) {
      $.ajax({
          type : "GET",
          url  : "/oase_web/top/dashboard/data/" + widgetID.toString() + "/",
          dataType : "json",
      })
      .done(function(respdata) {
          setTimeout(
            function(){
              db.stackedGraph( respdata.id, respdata.usage, respdata.data );
            }, 10
          );
          db.loadingHTML();
      });
  }
};












