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
  セッション
  ユーザー認証情報を保持する

[引数]


[戻り値]


"""




from django.contrib.sessions.backends.base import SessionBase


class SessionStore(SessionBase):

    def __init__(self, session_key=None):
        self._session_namespace = "__SESSION_NAMESPACE__"
        super(SessionStore, self).__init__(session_key)


    def load(self):
        data = memcache.get(self.session_key, namespace=self._session_namespace)
        if data:
            return data

        else:
            self.create()
            return {}


    def exists(self, session_key):
        data = memcache.get(session_key, namespace=self._session_namespace)
        if data:
            return True

        else:
            return False


    def create(self):
        while True:
            self.session_key = self._get_new_session_key()
            try:
                self.save(must_create=True)

            except CreateError:

                continue

            self.modified = True
            self._session_cache = {}

            return


    def save(self, must_create=False):
        if must_create:
            is_success = memcache.add(
                self.session_key,
                self._get_session(no_load=must_create),
                time=self.get_expiry_age(),
                namespace=self._session_namespace
            )

        else:
            is_success = memcache.set(
                self.session_key,
                self._get_session(no_load=must_create),
                time=self.get_expiry_age(),
                namespace=self._session_namespace
            )

        if not is_success:
            raise CreateError


    def delete(self, session_key=None):
        if session_key is None:
            if self._session_key is None:
                return
            session_key = self._session_key

        memecache.delete(
            session_key,
            seconds=300,
            namespace=self._session_namespace
        )


