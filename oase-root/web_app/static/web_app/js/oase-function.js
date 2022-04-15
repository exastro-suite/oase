// JavaScript Document

function exFunction(){}

exFunction.prototype = {
    // 正確な型
    'typeof': function( value ) {
        return Object.prototype.toString.call( value ).slice( 8, -1 ).toLowerCase();
    },
    // エスケープ
    'escape': function( value, brFlag, spaceFlag ) {
        brFlag = ( brFlag === undefined )? false: true;
        spaceFlag = ( spaceFlag === undefined )? false: true;
        const entities = [
            ['&', 'amp'],
            ['\"', 'quot'],
            ['\'', 'apos'],
            ['<', 'lt'],
            ['>', 'gt'],
            ['\\(', '#040'],
            ['\\)', '#041'],
            ['\\[', '#091'],
            ['\\]', '#093']
        ];
        if ( value !== undefined && value !== null && this.typeof( value ) === 'string') {
            for ( var i = 0; i < entities.length; i++ ) {
                value = value.replace( new RegExp( entities[i][0], 'g'), `&${entities[i][1]};`);
            }
            value = value.replace( new RegExp(/\\/, 'g'), `&#092;`);
            if ( brFlag ) value = value.replace(/\r?\n/g, '<br>');
            if ( spaceFlag ) value = value.replace(/^\s+|\s+$/g, '');
        } else {
            value = undefined;
        }
        return value;
    },
    //
    'val': function( value, change ) {
        return ( this.isset( value ) && value !== '')? value: change;
    },
    // 日付フォーマット
    'date': function( date, format ) {
        if ( date ) {
            const d = new Date(date);
            format = format.replace(/yyyy/g, d.getFullYear());
            format = format.replace(/MM/g, ('0' + (d.getMonth() + 1)).slice(-2));
            format = format.replace(/dd/g, ('0' + d.getDate()).slice(-2));
            format = format.replace(/HH/g, ('0' + d.getHours()).slice(-2));
            format = format.replace(/mm/g, ('0' + d.getMinutes()).slice(-2));
            format = format.replace(/ss/g, ('0' + d.getSeconds()).slice(-2));
            format = format.replace(/SSS/g, ('00' + d.getMilliseconds()).slice(-3));
            return format;
        } else {
            return '';
        }
    },
    // 時刻をOASE内の形式に変換する
    'oaseDate': function( date ) {
        if ( date ) {
            date = new Date( date );
            date.setMinutes( date.getMinutes() + date.getTimezoneOffset() );
            date = this.date( date, 'yyyy-MM-ddTHH:mm:ss.SSSZ' );
            return date;
        } else {
            return '';
        }
    },
    // 変数チェック
    'isset': function( value ) {
        return ( value === undefined || value === null )? false: true;
    },
    // 選択を解除
    'deselection': function() {
        if ( window.getSelection ) {
            window.getSelection().removeAllRanges();
        }
    },
    // スクロールバーの幅
    'scrollBarWidth': function( element ) {
        return element.offsetWidth - element.clientWidth;
    },
    // 横スクロールできる量
    'scrollMaxX': function( element ) {
        return element.scrollWidth - element.clientWidth;
    },
    // 縦スクロールできる量
    'scrollMaxY': function( element ) {
        return element.scrollHeight - element.clientHeight;
    },
    // URLから指定のパラメータの取得
    'getParameter': function ( name ) {
        const url = window.location.href,
              regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
              results = regex.exec( url );
        if( !results ) return null;
        return decodeURIComponent( results[2] );
    },
    // URLから全てのパラメータの取得
    'getAllParameter': function () {
        const parameters = window.location.search.substr(1).split('&'),
              parameterLength = parameters.length,
              parameterObject = {};
        for ( let i = 0; i < parameterLength; i++ ) {
          const keyValue = parameters[i].split('=');
          parameterObject[ keyValue[0] ] = decodeURIComponent( keyValue[1] );
        }
        return parameterObject;
    },
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Web Storage
// 
////////////////////////////////////////////////////////////////////////////////////////////////////
    'ws': {
        'check': function( type ) {
            const storage = ( type === 'local')? localStorage:
                        ( type === 'session')? sessionStorage:
                        undefined;
            try {
                const storage = window[type],
                x = '__storage_test__';
                storage.setItem( x, x );
                storage.removeItem( x );
                return true;
            }
            catch( e ) {
                return e instanceof DOMException && (
                // everything except Firefox
                e.code === 22 ||
                // Firefox
                e.code === 1014 ||
                // test name field too, because code might not be present
                // everything except Firefox
                e.name === 'QuotaExceededError' ||
                // Firefox
                e.name === 'NS_ERROR_DOM_QUOTA_REACHED') &&
                // acknowledge QuotaExceededError only if there's something already stored
                storage.length !== 0;
            }
        },
        'set': function( key, value, type ){
            if ( type === undefined ) type = 'local';
            const storage = ( type === 'local')? localStorage: ( type === 'session')? sessionStorage: undefined;
            if ( storage !== undefined ) {
                try {
                    storage.setItem( key, JSON.stringify( value ) );
                } catch( e ) {
                    window.console.error('Web storage error: setItem( ' + key + ' ) / ' + e.message );
                    storage.removeItem( key );
                }
            } else {
                return false;
            }
        },
        'get': function( key, type ){
            if ( type === undefined ) type = 'local';
            const storage = ( type === 'local')? localStorage: ( type === 'session')? sessionStorage: undefined;
            if ( storage !== undefined ) {
                if ( storage.getItem( key ) !== null  ) {
                    return JSON.parse( storage.getItem( key ) );
                } else {
                    return false;
                }
            } else {
                return false;
            }
        },
        'remove': function( key, type ){
            if ( type === undefined ) type = 'local';
            const storage = ( type === 'local')? localStorage: ( type === 'session')? sessionStorage: undefined;
            if ( storage !== undefined ) {
                storage.removeItem( key )
            } else {
                return false;
            }
        }
    }
};
