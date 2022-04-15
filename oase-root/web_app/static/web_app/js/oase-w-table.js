// JavaScript Document

function exTable(){
    this.fn = new exFunction();
    this.ww = new Worker('../../static/web_app/js/oase-w-table-worker.js');
}
exTable.prototype = {
/* ------------------------------ *\
    文字列
\* ------------------------------ */
    's': {
        'number': getMessage('MOSJA00022', false),
        'onePageDisplay': getMessage('MOSJA00023', false),
        'autoUpdate': getMessage('MOSJA00137', false),
        'scrollTop': getMessage('MOSJA00024', false),
        'scrollBottom': getMessage('MOSJA00025', false),
        'regexp': getMessage('MOSJA00212', false),
        'exactMatch': getMessage('MOSJA00138', false),
        'ignoreCase': getMessage('MOSJA00213', false),
        'pointUp': getMessage('MOSJA00214', false),
        'negative': getMessage('MOSJA00302', false),
        'filterList': getMessage('MOSJA00139', false),
        'filterText': getMessage('MOSJA00140', false),
        'filterDate': getMessage('MOSJA00141', false),
        'filterClear': getMessage('MOSJA00142', false),
        'filterDate1': getMessage('MOSJA00215', false),
        'filterDate2': getMessage('MOSJA00216', false),
        'filterDate3': getMessage('MOSJA00217', false)
    },
/* ------------------------------ *\
    target: tableをセットする対象
    config: 行列設定
    data: 行データ
    convert: 行データ変換用 function
    option: {
        page: 最初に表示するページ
        onePageNum: １頁に表示するページ数（10,25,50,100）
    }  
\* ------------------------------ */
    'setup': function( target, config, data, convert, option ) {
        if ( typeof jQuery === undefined ) return;
    
        const ex = this;
        ex.target = target;
        ex.convert = convert;
        ex.config = $.extend( true, [], config );
        ex.data = $.extend( true, [], data );
        ex.dataInit = $.extend( true, [], data );
        ex.option = ( option !== undefined )? $.extend( true, [], option ): {};
        
        // strage check
        const pn = ex.fn.ws.get('pageNum'),
              pt = ex.fn.ws.get('pollingTime');
        if ( pn !== false ) ex.config.table.onePageNum = pn;
        if ( pt !== false ) ex.config.table.pollingTime = pt;

        ex.$ = {};
        ex.$.target = $( target );
        ex.$.target.html(`
        <div class="exTable starting">
            <div class="et">
                <table class="et-t">
                    <thead class="et-h"></thead>
                    <tbody class="et-b"></tbody>
                </table>
            </div>
            <style class="ets"></style>
        </div>
        `);   
        
        ex.$.exTable = ex.$.target.find('.exTable');
        ex.$.et = ex.$.target.find('.et');
        ex.$.table = ex.$.target.find('.et-t');
        ex.$.thead = ex.$.target.find('.et-h');
        ex.$.tbody = ex.$.target.find('.et-b');
        
        ex.$.style = ex.$.target.find('.ets');
        
        ex.config.table.page = ( ex.config.table.page )? ex.config.table.page: 1;
        ex.config.table.onePageNum = ( ex.config.table.onePageNum )? ex.config.table.onePageNum: 50;
        
        ex.setHead();
        ex.setFooter();
        ex.setStyle();
        
        ex.evtFilter();
        ex.evtPinning();
        ex.evtSort();
        if ( ex.config.table.sort ) ex.setSort( ex.config.table.sort.key, ex.config.table.sort.order );
        
        ex.evtWorker();
        ex.postWorker('start');
        
        ex.workStart();
        
    },
/* ------------------------------ *\
    Workerイベント
\* ------------------------------ */
    'evtWorker': function() {
        const ex = this;
        ex.ww.addEventListener('message', function( m ){
            
            ex.message = m.data;
            
            if ( ex.message.type === 'list') {
                ex.filterList = ex.message.list;
                $( window ).trigger('filterList');
            } else {
                const update = function() {
                    ex.config.table.page = ex.message.page;
                    ex.rowNum = ex.message.rowNum;
                    ex.allNum = ex.message.allNum;
                    ex.pageNum = ex.message.pageNum;
                    ex.setBody( ex.message.rows );
                    ex.setPagingStatus();
                };

                switch ( ex.message.type ) {
                    case 'page':
                        ex.disabledFilter( false );
                        update();
                    break;
                    case 'polling':
                        if ( ex.workCheck() ) {
                            update();
                        }
                    break;
                }

                if ( ex.message.type !== 'polling' ) {
                    ex.workEnd();
                }
            }

        });
    },
/* ------------------------------ *\
    Worker post message
\* ------------------------------ */
    'postWorker': function( type, option ) {
        const ex = this;
        
        if ( !type ) type = 'page';
        if ( type !== 'pin' && type !== 'pollingUpdate' && type !== 'list') {
            if ( type !== 'sort' ) ex.clearPinning();
            ex.workStart();
        }
        ex.ww.postMessage({
            'type': type,
            'config': ex.config,
            'option': option
        });
    },
/* ------------------------------ *\
    thead
\* ------------------------------ */
    'setHead': function() {
        const ex = this,
              th = ex.config,
              l = th.col.length,
              h = [];
        for ( let i = 0; i < l; i++ ) {
            h.push( ex.getTh( th.col[i], i ) );
        }
        ex.$.thead.html(`<tr class="et-r">${h.join('')}</tr>`);
    },
/* ------------------------------ *\
    style
\* ------------------------------ */
    'setStyle': function() {
        const ex = this;
        let style = '';
        
        // Col style
        const c = ex.config.col,
              cl = c.length;
        for ( let i = 0; i < cl; i++ ) {
            if ( c[i].align ) {
                style += `.et-b .et-c.${c[i].className}{text-align:${c[i].align}}`;
            }
            if ( ex.config.table.grid && c[i].className ) {
                style += `.et-c.${c[i].className}{grid-area:${c[i].className};}`;
            }
        }
        
        // grid
        if ( ex.config.table.grid ) {
            const g = ex.config.table.grid;
            ex.$.exTable.addClass('et-grid')
            style += '.exTable .et-r{';
            for ( const k in g ) {
                style += `${k}:${g[k]};`;
            }
            style += '}';
        }     
        
        ex.$.style.html(`<style>${style}</style>`);
    },
/* ------------------------------ *\
    tbody
\* ------------------------------ */
    'setBody': function( tb ) {
        const ex = this,
              hd = ex.config;

        if ( tb.length > 0 ) {
            //ex.setPagingStatus();
            const l = tb.length;
            const rh = [];
            for( let i = 0; i < l; i++ ) {
                const bd = ex.convert( tb[i] ),
                      cl = bd.col.length,
                      ch = [];
                for ( let j = 0; j < cl; j++ ) {
                    ch.push( ex.getTd( hd.col[j], bd.col[j], i ) );
                }
                // Config row
                const configLength = hd.row.length,
                      attr = [],
                      rowClass = ['et-r'];
                for ( let j = 0; j < configLength; j++ ) {
                    if ( hd.row[j] === 'class') {
                        rowClass.push( bd.row[j] );
                    } else {
                        attr.push(`${hd.row[j]}="${bd.row[j]}"`);
                    }
                }
                attr.push(`class="${rowClass.join(' ')}"`);
                rh.push(`<tr ${attr.join(' ')}>${ch.join('')}</tr>`);
            }
            ex.$.tbody.html( rh.join('') );
            // ピン止め
            if ( ex.config.table.pin.id ) {
                const pinID = ex.config.table.pin.id,
                      $et = ex.$.exTable.find('.et'),
                      $pin = ex.$.tbody.find(`.et-r[data-id="${pinID}"]`),
                      headerHeight = ex.$.exTable.find('.et-h').outerHeight(),
                      rowHeight = $pin.outerHeight(),
                      scrollTop = $et.scrollTop(),
                      tableHeight = $et.outerHeight() - headerHeight,
                      positionTop = $pin.position().top - headerHeight;
                $pin.addClass('et-pinning');
                
                // 画面内にスクロールする
                if ( scrollTop < positionTop - tableHeight + rowHeight + 16 ) {
                    $et.stop(0,0).animate({'scrollTop': positionTop - tableHeight + rowHeight + 16 }, 100 );
                } else if ( scrollTop > positionTop ) {
                    $et.stop(0,0).animate({'scrollTop': positionTop }, 100 );
                }
            }
        } else {
            ex.$.tbody.html('');
        }
        ex.checkFilter();
    },
/* ------------------------------ *\
    footer
\* ------------------------------ */
    'setFooter': function() {
        const ex = this;
        
        const onPageNumList = {
            '10': 10,
            '25': 25,
            '50': 50,
            '100': 100
        };
        const autoUpdateList = {
            'OFF': 0,
            '1s' : 1000,
            '5s' : 5000,
            '10s': 10000,
            '30s': 30000,
            '1m' : 60000,
            '2m' : 120000,
            '5m' : 300000,
            '10m': 600000,
            '30m': 1800000,
            '1h' : 3600000,
        };
        const option = function( list ){
            const a = [];
            for ( const key in list ) {
                a.push(`<option value="${list[key]}">${key}</option>`);
            }
            return a.join('');
        };
        ex.$.exTable.append(`
        <div class="etf oase-table-footer">
            <div class="etf-b">
                <dl class="etf-bm">
                    <dt class="etf-bh">${ex.s.number}</dt>
                    <dd class="etf-bb"><span class="etf-rowNum">0</span></dd>
                </dl>
            </div>
            <div class="etf-b">
                <dl class="etf-bm">
                    <dt class="etf-bh">${ex.s.onePageDisplay}</dt>
                    <dd class="etf-bb">
                        <select class="etf-se etf-i etf-onePageDisplay">
                            ${option(onPageNumList)}
                        </select>
                    </dd>
                </dl>
            </div>
            <div class="etf-b">
                <dl class="etf-bm">
                    <dt class="etf-bh"><span class=""></span>${ex.s.autoUpdate}</dt>
                    <dd class="etf-bb">
                        <select class="etf-se etf-i etf-autoUpdate">
                            ${option(autoUpdateList)}
                        </select>
                    </dd>
                </dl>
            </div>
            <div class="etf-b etf-pageMove etf-separate">
                <div class="etf-bi"><button class="etf-bt etf-bt-first owf owf-up-on" data-button="first"></button></div>
                <div class="etf-bi"><button class="etf-bt owf owf-minus" data-button="prev"></button></div>
                <div class="etf-bi etf-pageWrap">
                    <div class="etf-pageInner">
                        <input type="number" class="etf-ip etf-i etf-page" value="0">
                        <div class="etf-pageWidth">0</div>
                    </div>
                </div>
                <div class="etf-bi"><span class="etf-last">/ 0</span></div>
                <div class="etf-bi"><button class="etf-bt owf owf-plus" data-button="next"></button></div>
                <div class="etf-bi"><button class="etf-bt etf-bt-end owf owf-down-on" data-button="end"></button></div>
            </div>
            <div class="etf-b etf-separate">
                <div class="etf-bi"><button class="tooltip etf-bt owf owf-up-on" data-button="top" data-tooltip="${ex.s.scrollTop}"></button></div>
                <div class="etf-bi"><button class="tooltip etf-bt owf owf-down-on" data-button="bottom" data-tooltip="${ex.s.scrollBottom}"></button></div>
            </div>
        </div>
        `);
        ex.$.footer = ex.$.exTable.find('.etf');
        ex.$.rowNum = ex.$.footer.find('.etf-rowNum');
        ex.$.onePageDisplay = ex.$.footer.find('.etf-onePageDisplay');
        ex.$.autoUpdate = ex.$.footer.find('.etf-autoUpdate');
        ex.$.page = ex.$.footer.find('.etf-page');
        ex.$.pageWidth = ex.$.footer.find('.etf-pageWidth');
        ex.$.lastPage = ex.$.footer.find('.etf-last');
        
        ex.$.onePageDisplay.val( ex.config.table.onePageNum );
        ex.$.autoUpdate.val( ex.config.table.pollingTime );
        
        ex.evtPaging();
    },
/* ------------------------------ *\
    ページングイベント
\* ------------------------------ */
    'evtPaging': function() {
        const ex = this;
        // ページ移動
        ex.$.pagePrev = ex.$.footer.find('.etf-bt[data-button="prev"], .etf-bt[data-button="first"]');
        ex.$.pageNext = ex.$.footer.find('.etf-bt[data-button="next"], .etf-bt[data-button="end"]');

        ex.$.footer.find('.etf-bt').on('click', function(){
            if ( ex.workCheck() ) {
                const $b = $( this ),
                      b = $b.attr('data-button');
                switch ( b ) {
                    case 'first':
                        ex.config.table.page = 1;
                    break;
                    case 'end':
                        ex.config.table.page = ex.pageNum;
                    break;
                    case 'prev':
                        ex.config.table.page--;
                    break;
                    case 'next':
                        ex.config.table.page++;
                    break;
                    case 'top':
                        ex.$.exTable.find('.et').stop(0,0).animate({'scrollTop': 0}, 200 );
                    break;
                    case 'bottom': {
                        const scrollMax = ex.fn.scrollMaxY( ex.$.et.get(0) );
                        ex.$.exTable.find('.et').stop(0,0).animate({'scrollTop': scrollMax }, 200 );
                    } break;
                }
                ex.postWorker();
            }
        });
        // ページ入力移動
        ex.$.page.on({
            'input': function() {
                ex.$.pageWidth.text( $( this ).val() );
            },
            'change': function() {
                ex.config.table.page = Number( $( this ).val() );
                if ( ex.workCheck() ) {
                    ex.postWorker();
                }
            },
            'blur': function() {
                $( this ).val( ex.config.table.page );
            }
        });
        // マウスホイールでページ移動
        const mousewheelevent = ('onwheel' in document )? 'wheel': ('onmousewheel' in document )? 'mousewheel': 'DOMMouseScroll';
        ex.$.footer.find('.etf-pageMove').on( mousewheelevent, function(e) {
            e.preventDefault();
            if ( ex.workCheck() ) {
                const delta = e.originalEvent.deltaY? - ( e.originalEvent.deltaY ):
                    e.originalEvent.wheelDelta ? e.originalEvent.wheelDelta: - ( e.originalEvent.detail );

                if ( e.buttons === 0 ) {
                    if ( delta < 0 ){
                        ex.config.table.page++;
                    } else {
                        ex.config.table.page--;
                    }
                    ex.postWorker();
            }
            }
        });
        // 表示するページ数変更
        ex.$.footer.find('.etf-onePageDisplay').on('change', function() {
            const p = Number( $( this ).val() );
            ex.config.table.onePageNum = p;
            ex.fn.ws.set('pageNum', p );
            if ( ex.workCheck() ) {
                ex.postWorker();
            } 
        });
        // ポーリングタイム変更
        ex.$.footer.find('.etf-autoUpdate').on('change', function() {
            const t = Number( $( this ).val() );
            ex.config.table.pollingTime = t;
            ex.fn.ws.set('pollingTime', t );
            ex.postWorker('pollingUpdate');
        });
    },
/* ------------------------------ *\
    ページングステータス
\* ------------------------------ */
    'setPagingStatus': function() {
        const ex = this,
              p = ex.config.table.page;
        // フォーカスが当たってる場合は更新しない
        if ( !ex.$.page.is(':focus') ) {
            ex.$.page.val( p );
            ex.$.pageWidth.text( p );
        }
        ex.$.lastPage.text(`/ ${ex.pageNum.toLocaleString()}`);
        // 件数
        if ( ex.rowNum !== ex.allNum ) {
            ex.$.rowNum.html(`<span class="etf-filterNum">${ex.rowNum.toLocaleString()}</span><span class="etf-allNum"> / ${ex.allNum.toLocaleString()}</span>`);
        } else {
            ex.$.rowNum.text( ex.rowNum.toLocaleString() );
        }
        // ページングボタンチェック
        if ( p <= 1 ) {
            ex.$.pagePrev.prop('disabled', true );
        } else {
            ex.$.pagePrev.prop('disabled', false );
        }
        if ( p >= ex.pageNum ) {
            ex.$.pageNext.prop('disabled', true );
        } else {
            ex.$.pageNext.prop('disabled', false );
        }
    },
/* ------------------------------ *\
    th
\* ------------------------------ */
    'getTh': function( hd, num  ) {
        const className = ['et-th', 'et-c'],
              attr = [],
              inner = [];
        filter = getMessage('MOSJA00143', false);
        className.push(`et-th-${hd.type}`);
        if ( hd.className ) className.push( hd.className );
        if ( hd.sort ) {
            className.push('et-sort');
            attr.push(`data-sort-key="${hd.sort}"`);
        }
        if ( hd.tooltip ) {
            className.push('tooltip');
            attr.push(`data-tooltip="${hd.tooltip}"`);
        }
        if ( hd.filter ) inner.push(`<div class="tooltip et-filter owf owf-filter-on" data-tooltip="${filter}"></div>`);
        inner.push(`<div class="et-ci">${hd.heading}</div>`);
        
        attr.push(`class="${className.join(' ')}"`);
        return `<th ${attr.join(' ')} data-col="${num}">${inner.join('')}</th>`;
    },
/* ------------------------------ *\
    td
\* ------------------------------ */
    'getTd': function( hd, bd, num ) {
        const ex = this,
              className = ['et-tb', 'et-c'];
        let b;
        
        className.push(`et-tb-${hd.type}`);
        if ( hd.className ) className.push( hd.className );
        switch ( hd.type ) {
            case 'icon':
                b = `<span class="tooltip"><em class="owf ${bd.name}"></em><span>${bd.description}</span></span>`;
            break;
            case 'text':
                if ( hd.filter && hd.filter.text && hd.filter.text.value
                    && hd.filter.text.option && hd.filter.text.option.pointUp === 1 ) {
                    // フィルタ強調
                    const val = ex.fn.escape( hd.filter.text.value ),
                          reg = new RegExp( `(${val})`, 'gi');
                    bd = ex.fn.escape( bd );
                    b = bd.replace( reg, '<span class="highlight">$1</span>');
                } else {
                    b = bd;
                }
            break;
            case 'date':
                b = ex.fn.date( bd, hd.format );
            break;
            case 'operationMenu': {
                const l = bd.length,
                      li = [];
                for ( let i = 0; i < l; i++ ) {
                    li.push(`<li class="et-opi">${ex.getButton(bd[i])}</li>`);
                }
                b = `<ul class="et-opl">${li.join('')}</ul>`;
            } break;
        }
        return `<td class="${className.join(' ')}" data-col="${num}"><div class="et-ci">${b}</div></td>`;
    },
/* ------------------------------ *\
    ボタン
\* ------------------------------ */
    'getButton': function( bd ) {
        const c = ['et-opb', 'oase-mini-button'],
              a = ['type="button"', `data-type="${bd.type}"`, `id="${bd.id}"`];
        if ( bd.tooltip ) {
            c.push('tooltip');
            a.push(`data-tooltip="${bd.tooltip}"`)
        }
        if ( bd.disabled ) {
            a.push(`disabled`);
        }
        a.push(`class="${c.join(' ')}"`);
        return `<button ${a.join(' ')}><em class="owf owf-${bd.icon}"></em></button>`;
    },
/* ------------------------------ *\
    ソートイベント
\* ------------------------------ */
    'evtSort': function() {
        const ex = this;
        ex.$.thead.on('click', '.et-sort', function() {
            if ( ex.workCheck() ) {
                const $s = $( this ),
                      key = $s.attr('data-sort-key');
                const sortType = function( s ) {
                    if ( s === 'asc' || s === undefined ) {
                        s = 'desc';
                    } else if ( s === 'desc') {
                        s = 'asc';
                    }
                    return s;
                };
                ex.setSort( key, sortType( $s.attr('data-sort') ) );
                ex.postWorker('sort');
            }
        });
    },
/* ------------------------------ *\
    ソート状態をセット
\* ------------------------------ */
    'setSort': function( key, order ){
        const ex = this;
        if ( !ex.fn.isset( order ) ) order = 'desc';
        ex.$.thead.find('.et-th').removeAttr('data-sort');
        ex.$.thead.find(`.et-th[data-sort-key="${key}"]`).attr('data-sort', order );
        ex.config.table.sort.key = key;
        ex.config.table.sort.order = order;
    },
/* ------------------------------ *\
    読み込み開始
\* ------------------------------ */
    'workStart': function() {
        const ex = this;
        ex.workFlag = false;
        ex.$.exTable.addClass('working');
    },
/* ------------------------------ *\
    読み込み完了
\* ------------------------------ */
    'workEnd': function() {
        const ex = this;
        ex.workFlag = true;
        ex.$.exTable.removeClass('working starting');
    },
/* ------------------------------ *\
    作業中か確認
\* ------------------------------ */
    'workCheck': function() {
        return this.workFlag;
    },
/* ------------------------------ *\
    行をピン止め
\* ------------------------------ */
    'evtPinning': function() {
        const ex = this;
        
        if ( ex.config.table.pin ) {
            ex.$.tbody.on('click', '.status', function(){
                const $r = $( this ).closest('.et-r'),
                      id = $r.attr('data-id');

                if ( $r.is('.et-pinning') ) {
                    $r.removeClass('et-pinning');
                    ex.$.tbody.removeClass('et-b-pinning');
                    ex.config.table.pin.id = undefined;
                } else {
                    ex.$.tbody.find('.et-pinning').removeClass('et-pinning');
                    $r.addClass('et-pinning');
                    ex.$.tbody.addClass('et-b-pinning');
                    ex.config.table.pin.id = id;
                }
                ex.postWorker('pin');
            });
        }
        
    },
/* ------------------------------ *\
    ピン止め解除
\* ------------------------------ */
    'clearPinning': function() {
        const ex = this;
        ex.$.tbody.find('.et-pinning').removeClass('et-pinning');
        ex.$.tbody.removeClass('et-b-pinning');
        ex.config.table.pin.id = undefined;
    },
/* ------------------------------ *\
    フィルタイベント
\* ------------------------------ */
    'evtFilter': function() {
        const ex = this;
        
        ex.$.filter = $('<div class="et-f filter"/>');
        ex.$.exTable.append( ex.$.filter );
        
        ex.$.thead.on('click', '.et-filter', function( e ){
            e.stopPropagation();
            const $f = ex.$.filter;
            if ( ex.workCheck() ) {
                const $b = $( this ),
                      $w = $( window );
                
                const close = function() {
                    $f.empty();
                    $w.off('mousedown.filter');
                    $b.removeClass('open');
                };

                if ( !$b.is('.open') ) {
                    const $c = $b.closest('.et-c'),
                          num = $c.attr('data-col'),
                          c = ex.config.col[num];
                    
                    ex.$.thead.find('.et-filter.open').removeClass('open');
                    $b.addClass('open');
                    $f.html( ex.getFilter( num ) );
                    
                    // Tab
                    $f.find('.et-fm-a').eq(0).addClass('selected');
                    $f.find('.et-fb').eq(0).addClass('selected');
                    
                    $f.find('.et-fm-a').on('click', function(e){
                        e.preventDefault();
                        const $tab = $( this ),
                              target = $tab.attr('href');
                        
                        $f.find('.et-fm-a.selected, .et-fb.selected').removeClass('selected');
                        $tab.add( $( target ) ).addClass('selected');                        
                    });
                    
                    // テキストフィルタ
                    const $t = $f.find('#filter-text');
                    const textFilter = function( value ) {
                        c.filter.text.value = ( value !== '')? value: undefined;
                        // Option
                        $t.find('.et-fb-c').each(function(){
                            const $c = $( this ),
                                  t = $c.attr('data-type'),
                                  s = ( $c.prop('checked') )? 1: 0;
                            c.filter.text.option[t] = s;
                        });
                        ex.postWorker('filter');
                    };
                    if ( $t.length ) {
                        $t.find('.et-fb-t').on({
                            'change': function() {
                                if ( ex.workCheck() ) {
                                    textFilter( $( this ).val() );                                
                                }
                            }
                        });
                        $t.find('.et-fb-c[data-type="regexp"]').on({
                            'change': function() {
                                const $exactMatch = $f.find('.et-fb-c[data-type="exactMatch"]'),
                                      check = $( this ).prop('checked');
                                if ( check ) {
                                    $exactMatch.addClass('disabled').prop('disabled', true );
                                    $exactMatch.closest('label').attr('disabled', '');
                                } else {
                                    $exactMatch.removeClass('disabled').prop('disabled', false );
                                    $exactMatch.closest('label').removeAttr('disabled');
                                }
                            }
                        });
                    }
                    // セレクトフィルタ
                    const $l = $f.find('#filter-list');
                    if ( $l.length ) {
                        const target = ex.fn.val( c.filter.list.key, '');
                        $w.one('filterList', function() {
                            const list = ex.filterList[target];
                            if ( list ) {
                                $l.removeClass('load-wait');
                                const o = [],
                                      l = list.length;
                                for ( let i = 0; i < l; i++ ) {
                                    o.push(`<option value="${list[i]}">${list[i]}</option>`);
                                }
                                const $fl = $(`<select class="et-fb-s" multiple>${o.join('')}</select>`);
                                $fl.val( c.filter.list.value );
                                $fl.on('change', function() {
                                    ex.disabledFilter( true );
                                    c.filter.list.value = $fl.val();
                                    ex.postWorker('filter');
                                });
                                $l.html( $fl );
                            }
                        });
                        ex.postWorker('list', target );
                    }

                    // 日時フィルタ
                    const $d = $f.find('#filter-date');
                    const dateFilter = function() {
                        const values = [
                            ex.fn.val( $d.find('.et-fb-t.date-a').val(), ''),
                            ex.fn.val( $d.find('.et-fb-t.date-b').val(), '')
                        ];
                        // 入力された時間をUTCタイムに変換する
                        const l = values.length;
                        for ( let i = 0; i < l; i++ ) {
                            if ( values[i] ) values[i] = ex.fn.oaseDate( values[i] );
                        }
                        c.filter.date.value = values;
                        c.filter.date.option = $d.find('.date-select').val();
                        ex.postWorker('filter');
                    };
                    if ( $d.length ) {
                        // データピッカー
                        $f.find('.date-a, .date-b').oaseDatePicker();
                        // A to B select
                        const ab = ( c.filter.date.option )? c.filter.date.option: '0';
                        $d.find('.date-select').val( ab );
                    }
                    
                    // フィルタクリア
                    $f.find('.et-fm-c').on('click', function(){
                        if ( ex.workCheck() ) {
                            $(this).mouseleave()
                            for ( const key in c.filter ) {
                                c.filter[key].value = undefined;
                            }
                            close();
                            ex.postWorker('filter');
                        }
                    });
                    
                    // ボタン
                    $f.find('.et-fb-b').on('click', function() {
                        const $b = $( this ),
                              t = $b.attr('data-type');
                        switch ( t ) {
                            case 'text':
                                textFilter( $f.find('.et-fb-t').val() );
                            break;
                            case 'date':
                                dateFilter();
                            break;
                        } 
                    });

                    $w.on('mousedown.filter', function( we ) {
                        if ( !$( we.target ).closest('.et-f, .et-filter, .oase-datepicker').length ) close();
                    });
                    
                    // フィルタ位置
                    const left = $c.position().left,
                          top = $c.position().top + $c.outerHeight(),
                          scrollBarWidth = ex.fn.scrollBarWidth( ex.$.et.get(0) );
                    if ( $f.outerWidth() + left > ex.$.thead.outerWidth() ) {
                        $f.css({'right': scrollBarWidth, 'top': top, 'left': 'auto'});
                    } else {
                        $f.css({'left': left, 'top': top, 'right': 'auto'});
                    }
                } else {
                    close();
                }
            }
        });
    },
/* ------------------------------ *\
    フィルタDisabled処理
\* ------------------------------ */
    'disabledFilter': function( flag ) {
        const ex = this;
        if ( ex.$.filter ) {
            const input = 'input, select',
                  $focus = $(':focus');
            if ( flag && $focus.length ) {
                ex.$.focus = $focus;
            } else if ( flag ) {
                ex.$.focus = undefined;
            }
            ex.$.filter.find( input ).not('.disabled').prop('disabled', flag );
            if ( !flag && $focus.length ) {
                ex.$.focus = undefined;
            } else if ( !flag && ex.$.focus ) {
                ex.$.focus.focus();
            }    
        }
    },
/* ------------------------------ *\
    フィルタチェック
\* ------------------------------ */
    'checkFilter': function() {
        const ex = this,
              c = ex.config.col,
              l = c.length;
        for ( let i = 0; i < l; i++ ) {
            if ( c[i].filter ) {
                const $f = ex.$.thead.find(`.et-th[data-col="${i}"]`).find('.et-filter'),
                      s = [];
                for ( const key in c[i].filter ) {
                    const f = c[i].filter[key];
                    if ( ex.fn.isset( f.value ) && f.value !== '' && f.value.length > 0 ) s.push('1');
                }
                if ( s.indexOf('1') !== -1 ) {
                    $f.addClass('set');
                } else {
                    $f.removeClass('set');
                }
            }
        }        
    },
/* ------------------------------ *\
    フィルタHTML
\* ------------------------------ */
    'getFilter': function( num ) {
        const ex = this,
              c = ex.config.col[num];
        
        const menu = [],
              filter = [];
        
        if ( c.filter ) {
            for ( const key in c.filter ) {
                const f = c.filter[key];
                switch ( key ) {
                    case 'text': {
                        menu.push(`<li class="et-fm-li"><a class="tooltip et-fm-a" href="#filter-text" data-tooltip="${ex.s.filterText}"><em class="owf owf-loupe"></em></a></li>`);
                        
                        const option = [];
                        for ( const o in f.option ) {
                            const checked = ( f.option[o] === 1 )? ' checked': '',
                                  disabled = ( o === 'exactMatch' && f.option.regexp === 1 )? ' disabled': '';
                            option.push(`<li class="et-fb-li"><label${disabled}><input class="et-fb-c" data-type="${o}" type="checkbox"${checked}${disabled}>${ex.s[o]}</label></li>`);
                        }
                        const v = ex.fn.val( ex.fn.escape( f.value ), '');
                        filter.push(`
                        <div id="filter-text" class="et-fb">
                            <input class="et-fb-t" type="text" value="${v}" placeholder="Text"><button class="et-fb-b" data-type="text"><em class="owf owf-update"></em></button>
                            <ul class="et-fb-ul">${option.join('')}</ul>
                        </div>
                        `);
                    } break;
                    case 'date': {
                        if ( !f.value ) f.value = [];
                        const a = ex.fn.date( ex.fn.val( ex.fn.escape( f.value[0] ), ''), 'yyyy/MM/dd HH:mm:ss'),
                              b = ex.fn.date( ex.fn.val( ex.fn.escape( f.value[1] ), ''), 'yyyy/MM/dd HH:mm:ss');
                        menu.push(`<li class="et-fm-li"><a class="tooltip et-fm-a" href="#filter-date" data-tooltip="${ex.s.filterDate}"><em class="owf owf-date"></em></a></li>`);
                        
                        filter.push(`<div id="filter-date" class="et-fb">
                            <dl class="et-fb-dl">
                                <dt class="et-fb-dt">A</dt>
                                <dd class="et-fb-dd"><input value="${a}" type="input" class="et-fb-t date-a" placeholder="0000/00/00 00:00:00"></dd>
                                <dt class="et-fb-dt">B</dt>
                                <dd class="et-fb-dd"><input value="${b}" type="input" class="et-fb-t date-b" placeholder="0000/00/00 00:00:00"></dd>
                            </dl>
                            <select class="date-select">
                                <option value="0">${ex.s.filterDate1}</option>
                                <option value="1">${ex.s.filterDate2}</option>
                                <option value="2">${ex.s.filterDate3}</option>
                            </select><button class="et-fb-b" data-type="date"><em class="owf owf-update"></em></button>
                        </div>`);
                    } break;
                    case 'list': {
                        menu.push(`<li class="et-fm-li"><a class="tooltip et-fm-a" href="#filter-list" data-tooltip="${ex.s.filterList}"><em class="owf owf-select"></em></a></li>`);
                        filter.push(`<div id="filter-list" class="et-fb"></div>`);
                    } break;
                }
            }
            menu.push(`<li class="et-fm-li"><em class="tooltip owf owf-filter-off et-fm-c" data-tooltip="${ex.s.filterClear}"></em></li>`);
            return $(`
            <ul class="et-fm-ul">
                ${menu.join('')}
            </ul>
            ${filter.join('')}
            `);
        }
    }
};