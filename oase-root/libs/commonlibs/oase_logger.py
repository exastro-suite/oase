# Copyright 2019 NEC Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


"""
[概要]
    OASEログ出力ライブラリ

"""


import time
import sys
import os
import inspect
import traceback
import pytz
import datetime
from logging import DEBUG, WARNING
from logging import getLogger
from logging import Formatter
from logging.handlers import TimedRotatingFileHandler

my_path = os.path.dirname(os.path.abspath(__file__))
tmp_path = my_path.split('oase-root')
root_dir_path = tmp_path[0] + 'oase-root'
sys.path.append(root_dir_path)

from libs.commonlibs import define as defs
from libs.messages.oase_logid import OASELogID
from web_app.models.models import System


class OaseLoggerFormatter(Formatter):

    converter = datetime.datetime.utcfromtimestamp

    def formatTime(self, record, datefmt=None):

        if not datefmt:
            datefmt = '%Y/%m/%d %H:%M:%S.%f'

        ct = self.converter(record.created)
        ct = ct.strftime(datefmt)

        return ct


class OaseLogger:
    """
    [概要]
        OASEロガー

        ※ローテ時間とサイズの組み合わせによっては、監視用ログとDEBUG用ログとのログ保存状況がズレるので注意
    """

    __instance = None

    def __new__(cls):

        raise Exception('not allowed')

    @classmethod
    def __internal_new__(cls):

        return super().__new__(cls)

    @classmethod
    def get_instance(cls):

        if not cls.__instance:
            cls.__instance = cls.__internal_new__()
            cls.__instance.__init_instance()

        return cls.__instance

    def __init_instance(self):
        """
        [概要]
            インスタンス初期設定(≒コンストラクタ)

        [引数]
            なし
        """

        ##############################################################
        # 初期値
        #   logger_name        : ロガー名称
        #   log_file_path      : ログファイルのパス
        #   log_backup_count   : ログファイル世代数    (基本省略 14:   14)
        #   log_when           : ログローテの単位      (基本省略 MIDNIGHT : 0:00更新)
        #   log_interval       : ログローテのサイクル  (基本省略 1 :  1日)
        #   debug_log_max_bytes: ログローテのサイズ制限(基本省略 10000000: 10MB)
        ##############################################################
        fullpath = os.path.abspath(inspect.currentframe().f_back.f_back.f_code.co_filename)
        logger_name, log_file_path, log_backup_count = OaseLogger.get_settings(fullpath)
        log_when = 'MIDNIGHT'
        log_interval = 1
        debug_log_max_bytes = 10000000

        try:
            # エラー時の内容記録変数
            self.__last_error_message = ""

            #---------------------------
            #出力フォーマット設定
            #---------------------------
            observational_formatter = OaseLoggerFormatter(
                fmt='[%(asctime)s][%(logtype)s][%(logid)s] %(message)s',
                datefmt='%Y/%m/%d %H:%M:%S.%f'
            )
            debug_formatter = OaseLoggerFormatter(
                fmt='[%(asctime)s][%(logtype)s][%(logid)s][%(uid)s(%(sid)s)] (%(name)s) file:%(srcfilename)s func:%(srcfunc)s line:%(srcline)s %(message)s',
                datefmt='%Y/%m/%d %H:%M:%S.%f'
            )

            #---------------------------
            #ロガーのファイル用ハンドラを作成
            #---------------------------
            observational_handler = TimedRotatingFileHandler(
                filename=log_file_path, when=log_when, interval=log_interval,
                backupCount=log_backup_count, encoding='utf-8'
            )
            observational_handler.setFormatter(observational_formatter)
            observational_handler.setLevel(WARNING)

            dir_name, base_name = os.path.split(log_file_path)
            debug_dir_name = dir_name + '/debug'
            debug_log_file_path = os.path.join(debug_dir_name, base_name)
            if not os.path.exists(debug_dir_name):
                os.mkdir(debug_dir_name)
            debug_handler = EnhancedRotatingFileHandler(
                filename=debug_log_file_path, when=log_when, interval=log_interval,
                backup_count=log_backup_count, encoding='utf-8', max_bytes=debug_log_max_bytes
            )
            debug_handler.setFormatter(debug_formatter)
            debug_handler.setLevel(DEBUG)

            #---------------------------
            #ロガー作成
            #---------------------------
            parent_logger = getLogger(logger_name)
            parent_logger.propagate = True
            self.__logger = getLogger(logger_name + '.debug')
            self.__logger.propagate = True

            #---------------------------
            #ハンドラをロガーに追加
            #---------------------------
            if not parent_logger.hasHandlers():
                parent_logger.addHandler(observational_handler)
                parent_logger.setLevel(WARNING)
                self.__logger.addHandler(debug_handler)
                self.__logger.setLevel(DEBUG)

        except Exception as ex:
            # エラー時の内容記録
            self.__last_error_message = str(ex)
            raise

    def system_log(self, log_id, *args, request=None):
        """
        [概要]
            システムレベルログ

        [引数]
            log_id: ログID
            *args:  ログIDに対応したメッセージに {} がある場合、{} を置き換える値の変数列

        [戻り値]
            

        """

        self.__last_error_message = ""

        log_message = self._get_logmessage(log_id, *args)

        caller_frame = inspect.currentframe().f_back
        srcfilename = os.path.abspath(caller_frame.f_code.co_filename)
        srcfunc = caller_frame.f_code.co_name
        srcline = caller_frame.f_lineno
        uid = 0
        sid = '-'
        if request and hasattr(request, 'user') and hasattr(request.user, 'user_id'):
            uid = request.user.user_id
        if request and hasattr(request, 'session') and hasattr(request.session, 'session_key'):
            sid = request.session.session_key

        ids = {'logtype':'system', 'logid':log_id, 'uid':uid, 'sid':sid, 'srcfilename':srcfilename, 'srcfunc':srcfunc, 'srcline':srcline}
        try:
            if log_id[3] == 'E' or log_id[3] == 'M':
                self.__logger.error(log_message, extra=ids)
            else:
                self.__logger.debug(log_message, extra=ids)
        except Exception as ex:
            # エラー時の内容記録
            self.__last_error_message = str(ex)

    def user_log(self, log_id, *args, request=None):
        """
        [概要]
            ユーザレベルログ

        [引数]
            log_id: ログID
            *args:  ログIDに対応したメッセージに {} がある場合、{} を置き換える値の変数列

        [戻り値]
            
        """

        self.__last_error_message = ""

        log_message = self._get_logmessage(log_id, *args)

        caller_frame = inspect.currentframe().f_back
        srcfilename = os.path.abspath(caller_frame.f_code.co_filename)
        srcfunc = caller_frame.f_code.co_name
        srcline = caller_frame.f_lineno
        uid = 0
        sid = '-'
        if request and hasattr(request, 'user') and hasattr(request.user, 'user_id'):
            uid = request.user.user_id
        if request and hasattr(request, 'session') and hasattr(request.session, 'session_key'):
            sid = request.session.session_key

        ids = {'logtype':'user  ', 'logid':log_id, 'uid':uid, 'sid':sid, 'srcfilename':srcfilename, 'srcfunc':srcfunc, 'srcline':srcline}
        try:
            if log_id[3] == 'E':
                self.__logger.error(log_message, extra=ids)
            else:
                self.__logger.debug(log_message, extra=ids)
        except Exception as ex:
            # エラー時の内容記録
            self.__last_error_message = str(ex)

    def logic_log(self, log_id, *args, request=None):
        """
        [概要]
            ロジックレベルログ

        [引数]
            log_id: ログID
            *args:  ログIDに対応したメッセージに {} がある場合、{} を置き換える値の変数列

        [戻り値]
            
        """

        self.__last_error_message = ""

        log_message = self._get_logmessage(log_id, *args)

        caller_frame = inspect.currentframe().f_back
        srcfilename = os.path.abspath(caller_frame.f_code.co_filename)
        srcfunc = caller_frame.f_code.co_name
        srcline = caller_frame.f_lineno
        uid = 0
        sid = '-'
        if request and hasattr(request, 'user') and hasattr(request.user, 'user_id'):
            uid = request.user.user_id
        if request and hasattr(request, 'session') and hasattr(request.session, 'session_key'):
            sid = request.session.session_key

        ids = {'logtype':'logic ', 'logid':log_id, 'uid':uid, 'sid':sid, 'srcfilename':srcfilename, 'srcfunc':srcfunc, 'srcline':srcline}
        try:
            self.__logger.debug(log_message, extra=ids)
        except Exception as ex:
            # エラー時の内容記録
            self.__last_error_message = str(ex)

    def _get_logmessage(self, log_id, *args):
        """
        [概要]
            エラー取得

        [引数]
            なし

        [戻り値]
            
        """

        try:
            if log_id in OASELogID.Ary:
                log_message = OASELogID.Ary[log_id].format(*args)
            else:
                log_message = '■■■ Message is not found.(ID[' + log_id + '])'
                # エラー時の内容記録
                self.__last_error_message = log_message
        except Exception as ex:
            log_message = '■■■ Failed to edit message.(ID[' + log_id + '])'
            # エラー時の内容記録
            self.__last_error_message = log_message

        return log_message

    @classmethod
    def get_settings(self, fullpath):

        tmp_path = fullpath.split('oase-root')
        root_dir_path = tmp_path[0] + 'oase-root'

        # backyards
        if 'backyards' in fullpath:
            basename = os.path.basename(fullpath)
            filename, _ = os.path.splitext(basename)

            # oase_action_sub -> oase_action として判定する
            if filename.endswith("_sub"):
                filename = filename[:-4]

            # monitoring系は1つのlogにまとめる
            if 'monitoring' in filename:
                filename = 'oase_monitoring'

            log_file_path = root_dir_path + '/logs/backyardlogs/' + filename + '/' + filename + '.log'
            system_config_id = defs.SYSTEM_SETTINGS.LOG_PERIOD[filename]

            try:
                log_backup_count = int(System.objects.get(config_id=system_config_id).value)
            except:
                print('Failed to get Setting.')
                log_backup_count = 14

        else:
            filename = 'webaplog'

            log_file_path = root_dir_path + '/logs/webaplogs/webap.log'

            log_backup_count = 14 # TODO

        return (filename, log_file_path, log_backup_count)

    def get_last_error(self):
        """
        [概要]
            エラー取得

        [引数]
            なし

        [戻り値]
            
        """

        return self.__last_error_message


"""
時間＋バイトサイズでのログローテーション

引用元:
https://stackoverflow.com/questions/6167587/the-logging-handlers-how-to-rollover-after-time-or-maxbytes
"""
class EnhancedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, filename, when='h', interval=1, backup_count=0, encoding=None, delay=0, utc=0, max_bytes=0):
        """
        This is just a combination of TimedRotatingFileHandler and RotatingFileHandler
        (adds max_bytes to TimedRotatingFileHandler)
        """

        TimedRotatingFileHandler.__init__(self, filename, when, interval, backup_count, encoding, delay, utc)
        self.max_bytes = max_bytes

    def shouldRollover(self, record):
        """
        Determine if rollover should occur.

        Basically, see if the supplied record would cause the file to exceed
        the size limit we have.

        we are also comparing times
        """
        if self.stream is None:                 # delay was set...
            self.stream = self._open()
        if self.max_bytes > 0:                   # are we rolling over?
            msg = "%s\n" % self.format(record)
            self.stream.seek(0, 2)  #due to non-posix-compliant Windows feature
            if self.stream.tell() + len(msg) >= self.max_bytes:
                return 1
        t = int(time.time())
        if t >= self.rolloverAt:
            return 1
        #print "No need to rollover: %d, %d" % (t, self.rolloverAt)
        return 0

    def doRollover(self):
        """
        do a rollover; in this case, a date/time stamp is appended to the filename
        when the rollover happens.  However, you want the file to be named for the
        start of the interval, not the current time.  If there is a backup count,
        then we have to get a list of matching filenames, sort them and remove
        the one with the oldest suffix.
        """
        if self.stream:
            self.stream.close()
        # get the time that this sequence started at and make it a TimeTuple
        current_time = int(time.time())
        dst_now = time.localtime(current_time)[-1]
        t = self.rolloverAt - self.interval
        if self.utc:
            time_tuple = time.gmtime(t)
        else:
            time_tuple = time.localtime(t)
            dst_then = time_tuple[-1]
            if dst_now != dst_then:
                if dst_now:
                    addend = 3600
                else:
                    addend = -3600
                time_tuple = time.localtime(t + addend)
        dfn = self.baseFilename + "." + time.strftime(self.suffix, time_tuple)

        if self.backupCount > 0:
            cnt = 1
            dfn2 = "%s.%03d" % (dfn, cnt)
            while os.path.exists(dfn2):
                dfn2 = "%s.%03d" % (dfn, cnt)
                cnt += 1
            os.rename(self.baseFilename, dfn2)
            for s in self.get_files_to_delete():
                os.remove(s)
        else:
            if os.path.exists(dfn):
                os.remove(dfn)
            os.rename(self.baseFilename, dfn)
        #print "%s -> %s" % (self.baseFilename, dfn)
        self.mode = 'w'
        self.stream = self._open()
        new_rollover_at = self.computeRollover(current_time)
        while new_rollover_at <= current_time:
            new_rollover_at = new_rollover_at + self.interval
        #If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dst_at_rollover = time.localtime(new_rollover_at)[-1]
            if dst_now != dst_at_rollover:
                if not dst_now:  # DST kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:           # DST bows out before next rollover, so we need to add an hour
                    addend = 3600
                new_rollover_at += addend
        self.rolloverAt = new_rollover_at

    def get_files_to_delete(self): # ...これもoverride対象だが、、、、
        """
        Determine the files to delete when rolling over.

        More specific than the earlier method, which just used glob.glob().
        """
        dir_name, base_name = os.path.split(self.baseFilename)
        file_names = os.listdir(dir_name)
        result = []
        target_holder = {}
        prefix = base_name + "."
        plen = len(prefix)
        for file_name in file_names:
            if file_name[:plen] == prefix:
                suffix = file_name[plen:-4]
                if self.extMatch.match(suffix):
                    if not suffix in target_holder:
                        target_holder[suffix] = []
                    target_holder[suffix].append(os.path.join(dir_name, file_name))
        target_keys = list(target_holder.keys())
        target_keys.sort()
        if len(target_keys) < self.backupCount:
            result = []
        else:
            delete_keys = target_keys[:len(target_keys) - self.backupCount]
            for key in delete_keys:
                result.extend(target_holder[key])
        return result
