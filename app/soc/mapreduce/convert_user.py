# Copyright 2012 the Melange authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""User updating MapReduce.

This MapReduce updates user accounts to have complete email
addresses (including @gmail.com for gmail users) and sets the
user_id attribute of User objects if it is missing.
"""


import logging

from google.appengine.ext import db

from mapreduce import operation

from soc.models.user import User
from soc.logic import accounts


MISSING_USER = 'missing_user'
MISSING_USER_SECOND = 'missing_user_second'
MISSING_USER_ID = 'missing_user_id'
IGNORED_USER = 'ignored_user'
CONVERTED_USER = 'converted_user'


def convert_user_txn(user_key):
  user = db.get(user_key)

  if not user:
    logging.error("Missing user for key '%r'." % user_key)
    return MISSING_USER

  normalized = accounts.denormalizeAccount(user.account)

  if (user.account.email() == normalized.email() and
      user.user_id == user.account.user_id()):
     return IGNORED_USER

  user.account = normalized
  user.put()

  user = db.get(user_key)

  if not user:
    logging.error("Missing user second time around for key '%s'." % user_key)
    return MISSING_USER_SECOND

  if not user.account.user_id():
    logging.error("Missing user_id around for key '%s'." % user_key)
    return MISSING_USER_ID

  user.user_id = user.account.user_id()
  user.put()

  if not user.user_id:
    return MISSING_USER_ID

  return CONVERTED_USER


def process(user_key):
  result = db.run_in_transaction(convert_user_txn, user_key)
  yield operation.counters.Increment(result)
