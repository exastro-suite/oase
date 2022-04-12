// JavaScript Document

(function() {

const ex = {};
ex.defaultData = {}
ex.data = {};

// リストフィルタの最大option数
ex.filterListMax = 1000;

/* ------------------------------ *\
    スクリプト読み込み
\* ------------------------------ */
importScripts('oase-function.js');
const fn = new exFunction();

/* ------------------------------ *\
    Workerイベント
\* ------------------------------ */
self.addEventListener('message', function( m ){

    ex.message = m.data;
    ex.page = ex.message.config.table.page;
    ex.onePageNum = ex.message.config.table.onePageNum;
    ex.dataKey = ex.message.config.table.dataKey;
    ex.url = ex.message.config.table.url;
    ex.pollingTime = ex.message.config.table.pollingTime;

    if ( ex.message.config.table.sort ) {
        ex.sortKey = ex.message.config.table.sort.key;
        ex.sortOrder = ex.message.config.table.sort.order;
    }
    if ( ex.message.config.table.pin ) {
        ex.pinID = ex.message.config.table.pin.id;
        ex.pinKey = ex.message.config.table.pin.key;
    }

    switch ( ex.message.type ) {
        case 'start':
            update();
        break;
        case 'stop':
        break;
        case 'page':
            postData();
        break;
        case 'filter':
        case 'sort':
            setData();
            postData();
        break;
        case 'pollingUpdate':
            clearTimeout( ex.pollingTimerID );
            pagingStatus();
            polling();
        break;
        case 'pin':
            pagingStatus();
        break;
        case 'list':
            self.postMessage({
                'list': list( ex.message.option ),
                'type': 'list'
            });
        break;
    }
});

/* ------------------------------ *\
    更新する
\* ------------------------------ */
function update() {
    loadData( ex.url ).then( function() {
        setData();
        postData();
        polling();
    });
}

/* ------------------------------ *\
    ポーリング
\* ------------------------------ */
function polling() {
    if ( ex.pollingTime && ex.pollingTime > 0 ) {
        ex.pollingTimerID = setTimeout( function() {
            loadData( ex.url ).then( function() {
                setData();
                postData('polling');
                polling();
            });
        }, ex.pollingTime );
    }
}

/* ------------------------------ *\
    Filter list
\* ------------------------------ */
function list( target ) {
    const a = {},
          dd = ex.defaultData[ex.dataKey],
          l = dd.length;
    a[target] = [];
    for ( let i = 0; i < l; i++ ) {
        if ( ex.filterListMax <= a[target].length ) break;
        const d = dotKey( target.split('.'), dd[i] );
        if ( d ) {
            if ( a[target].indexOf( d ) === -1 ) {
                a[target].push(d);
            }
        }
    }
    return a;
}

/* ------------------------------ *\
    ページングデータを送る
\* ------------------------------ */
function postData( type ) {
    if ( !type ) type = 'page';
    pagingStatus();
    const r = {
        'type': type,
        'page': ex.page,
        'rowNum': ex.rowNum,
        'allNum': ex.allNum,
        'pageNum': ex.pageNum,
        'rows': getPage()
    };
    self.postMessage( r );
}

/* ------------------------------ *\
    ページングステータス
\* ------------------------------ */
function pagingStatus() {
    ex.allNum = ex.defaultData[ ex.dataKey ].length;
    ex.rowNum = ex.data[ ex.dataKey ].length;
    ex.pageNum = Math.ceil( ex.rowNum / ex.onePageNum );
    // ピン止めがある場合そのページをセット
    const pinNum = checkPinNum();
    if ( pinNum ) {
        ex.page = Math.ceil( ( pinNum + 1 ) / ex.onePageNum );
    }    
    if ( ex.page <= 0 ) ex.page = 1;
    if ( ex.page > ex.pageNum ) ex.page = ex.pageNum;
    ex.start = ( ex.rowNum === 0 )? ex.rowNum: ex.onePageNum * ( ex.page - 1 ),
    ex.end = ( ex.rowNum > ex.start + ex.onePageNum - 1 )? ex.start + ex.onePageNum: ex.rowNum;
}

/* ------------------------------ *\
    データ読み込み
\* ------------------------------ */
function loadData( url ){
    return new Promise( function( resolve, reject ) {

        fetch(url)
            .then((response) => {
                if (response.ok) {
                    return response.json();
                } else {
                    throw Error();
                }
            })
            .then((data) => {
                ex.defaultData[ ex.dataKey ] = data;
                resolve();
            })
            .catch(error => {
                reject( error );
            });
    });
}

/* ------------------------------ *\
    キー配列から値を返す
\* ------------------------------ */
function dotKey( keys, value ) {
    const l = keys.length;
    if ( l === 1 ) {
        return value[keys[0]];
    } else if ( l === 2 ) {
        return value[keys[0]][keys[1]];
    } else if ( l === 3 ) {
        return value[keys[0]][keys[1]][keys[2]];
    } else {
        return '';
    }
}

/* ------------------------------ *\
    ソート
\* ------------------------------ */
function sort() {
    if ( ex.sortOrder ) {
        const o = ex.sortOrder,
              k = ex.sortKey.split('.');
        ex.data[ ex.dataKey ].sort( function( a, b ) {
            let va = dotKey( k, a ), vb = dotKey( k, b );

            va = ( typeof va === 'number' && isFinite( va ) )?
                va: String( va ).toLowerCase(),
            vb = ( typeof vb === 'number' && isFinite( vb ) )?
                vb: String( vb ).toLowerCase();
            if ( va < vb) {
                return ( o === 'asc')? -1: 1;
            } else if ( va > vb ) {
                return ( o === 'asc')? 1: -1;
            } else {
              return 0;
            }
        });
    }
}

/* ------------------------------ *\
    ピン止めがどこか
\* ------------------------------ */
function checkPinNum() {
    if ( ex.pinKey && ex.pinID ) {
        const d = ex.data[ ex.dataKey ],
              l = d.length;
        for ( let i = 0; i < l; i++ ) {
            if ( String( d[i][ex.pinKey] ) === String( ex.pinID ) ) {
                return i;
            }
        }
    }
    return undefined;
}

/* ------------------------------ *\
    データをセット
\* ------------------------------ */
function setData() {
    const col = ex.message.config.col,
          l = col.length;
    if ( !ex.data[ ex.dataKey ] ) ex.data[ ex.dataKey ] = [];
    ex.data[ ex.dataKey ] = ex.defaultData[ ex.dataKey ].filter( function( row ) {
        const matchFlag = [];
        for ( let i = 0; i < l; i++ ) {
            if ( col[i].filter ) {
                const f = col[i].filter,
                      filterFlag = [];
                for ( const key in f ) {
                    const k = f[key].key.split('.'),
                          v = dotKey( k, row );
                    switch ( key ) {
                        // 文字列フィルタ
                        case 'text': {
                            if ( fn.isset( f[key].value ) && f[key].value !== '') {
                                const o = f[key].option,
                                      fv = f[key].value;
                                // 否定の場合は判定を反転する
                                const trueFlag = ( o.negative === 0 )? 'true': 'false',
                                      falseFlag = ( o.negative === 0 )? 'false': 'true';
                                if ( o.regexp === 1 ) {
                                    // 正規表現あり
                                    const regex = ( o.ignoreCase === 1 )?
                                        new RegExp( fv, 'g'):
                                        new RegExp( fv, 'gi');
                                    regex.test( v )?
                                        filterFlag.push( trueFlag ):
                                        filterFlag.push( falseFlag );
                                } else {
                                    // 正規表現なし
                                    if ( o.exactMatch === 1 ) {
                                        // 完全一致
                                        if ( o.ignoreCase === 1 ) {
                                            ( fv === v )?
                                                filterFlag.push( trueFlag ):
                                                filterFlag.push( falseFlag );
                                        } else {
                                            ( fv.toLowerCase() === v.toLowerCase() )?
                                                filterFlag.push( trueFlag ):
                                                filterFlag.push( falseFlag );
                                        }
                                    } else {
                                        // 部分一致
                                        if ( o.ignoreCase === 1 ) {
                                            ( v.indexOf( fv ) !== -1 )?
                                                filterFlag.push( trueFlag ):
                                                filterFlag.push( falseFlag );
                                        } else {
                                            ( v.toLowerCase().indexOf( fv.toLowerCase() ) !== -1 )?
                                                filterFlag.push( trueFlag ):
                                                filterFlag.push( falseFlag );
                                        }
                                    }
                                }
                            }
                        } break;
                        // リストフィルタ
                        case 'list': {
                            if ( fn.isset( f[key].value ) && f[key].value.length > 0 ) {
                                 ( f[key].value.indexOf( v ) !== -1 )?
                                    filterFlag.push('true'):
                                    filterFlag.push('false');
                            }
                        } break;
                        // 日時フィルタ
                        case 'date': {
                            if ( fn.isset( f[key].value ) && f[key].value.length > 0 ) {
                                const a = ( f[key].value[0] )? f[key].value[0]: '',
                                      b = ( f[key].value[1] )? f[key].value[1]: '';
                                 switch ( f[key].option ) {
                                    case '0':
                                        ( a <= v && v <= b )?
                                            filterFlag.push('true'):
                                            filterFlag.push('false');
                                    break;
                                    case '1':
                                        ( a <= v )?
                                            filterFlag.push('true'):
                                            filterFlag.push('false');
                                    break;
                                    case '2':
                                        ( a >= v )?
                                            filterFlag.push('true'):
                                            filterFlag.push('false');
                                    break;
                                 }
                            }
                        } break;
                    }
                }
                // 項目ごと
                matchFlag.push( ( filterFlag.indexOf('false') === -1 )? 'true': 'false');
            }
        }
        // 1行全て
        if ( matchFlag.indexOf('false') === -1 ) {
          return true;
        } else {
          return false;
        }
    });
    sort();
}

/* ------------------------------ *\
    表示範囲を返す
\* ------------------------------ */
function getPage() {
    return ex.data[ ex.dataKey ].slice( ex.start, ex.end );
}

/* ------------------------------ *\
    ダミーデータ作成
\* ------------------------------ */
let timeCounter = 0;
function dummyData( rowNum ){
    const dummy = [];

    const statusPattern = [
        ['完了(正常終了)', 'complete', 'owf-check'],
        ['強制終了', 'error', 'owf-cross'],
        ['処理中', 'running', 'owf-gear'],
        ['承認待ち', 'attention', 'owf-stop'],
        ['処理済み', 'addressed', 'owf-square'],
        ['アクション実行エラー', 'attention', 'owf-attention'],
        ['抑止済', 'prevent', 'owf-prevent'],
        ['未知', 'unknown', 'owf-question'],
    ];
    const requestNamePattern = [
        'プロダクション',
        'ステージング',
        'ステージングステージングステージング'
    ];

    if ( ex.message.config.table.dummyType === 'request') {
        for ( let i = 0; i < rowNum; i++ ) {
            const status = Math.floor( Math.random() * statusPattern.length );
            const requestName = Math.floor( Math.random() * requestNamePattern.length );
            const date = new Date();
            date.setMinutes( date.getMinutes() + date.getTimezoneOffset() + ( timeCounter ) );
            const traceID = `TOS_${fn.date( date, 'yyyyMMddHHmmss')}ffffff_NNNNNNNNNN`;

            dummy[i] = {
                "trace_id"               : traceID,
                "rule_name"              : "ディシジョンテーブル名" + ( timeCounter++ ),
                "request_name"           : requestNamePattern[requestName],
                "request_reception_time" : fn.date( date, 'yyyy-MM-ddTHH:mm:ss.SSSZ'),
                "event_info"             : "{\"EVENT_INFO\": [\"1\"]}",
                "event_to_time"          : fn.date( date, 'yyyy-MM-ddTHH:mm:ss.SSSZ'),
                "class_info"             : {
                    "status"      : statusPattern[status][1],
                    "name"        : statusPattern[status][2],
                    "description" : statusPattern[status][0],
                }
            }
        }
    } else {
        const can_updatePattern = [
            [1,2,3],[2,2,2],[3,3,3],[1,1,1],[0,0,0]
        ];
        const status2Pattern = [6,2008,1,0];
        const retry_statusPattern = [null, 6, 2008, 0, 1];
        const incidentPattern = ['ハードウェアの故障','Error','コンダクター','メール','これはテストです'];
        const handlingPattern = ['ITAによる対処','Handling','起票','通知','テスト'];
        const driverPattern = ['ITA(ver1)','ServiceNow(ver1)','mail(ver1)'];
        const actPattern = ['アクションドライバープロシージャ','システム管理者','Kato Keita'];

        for ( let i = 0; i < rowNum; i++ ) {
            const status = Math.floor( Math.random() * statusPattern.length );

            const disuse_flag = String( Math.floor( Math.random() * 2 ) );
            const can_update = Math.floor( Math.random() * can_updatePattern.length );

            const date = new Date();
            date.setMinutes( date.getMinutes() + date.getTimezoneOffset() + ( timeCounter ) );

            const status2 = Math.floor( Math.random() * status2Pattern.length );
            const retry_status = Math.floor( Math.random() * retry_statusPattern.length );
            const inciden = Math.floor( Math.random() * incidentPattern.length );
            const handling = Math.floor( Math.random() * handlingPattern.length );
            const driver = Math.floor( Math.random() * driverPattern.length );
            const act = Math.floor( Math.random() * actPattern.length );

            dummy[i] = {
                "pk"                : timeCounter,
                "response_id"       : timeCounter,
                "execution_order"   : timeCounter,
                "disuse_flag"       : disuse_flag,
                "can_update"        : can_updatePattern[can_update],
                "rule_type_id"      : 1,
                "rule_type_name"    : "ディシジョンテーブル名" + ( timeCounter++ ),
                "rule_name"         : "ルール名" + ( timeCounter ),
                "incident_happened" : incidentPattern[inciden],
                "handling_summary"  : handlingPattern[handling],
                "driver_name"       : driverPattern[driver],
                "status"            : status2Pattern[status2],
                "retry_status"      : retry_statusPattern[retry_status],
                "class_info"             : {
                    "status"      : statusPattern[status][1],
                    "name"        : statusPattern[status][2],
                    "description" : statusPattern[status][0],
                },
                "action_start_time"     : fn.date( date, 'yyyy-MM-ddTHH:mm:ss.SSSZ'),
                "last_update_timestamp" : fn.date( date, 'yyyy-MM-ddTHH:mm:ss.SSSZ'),
                "last_act_user"         : actPattern[act]
            }
        }
    }

    return dummy;
}

}());
