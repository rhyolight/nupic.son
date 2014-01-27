# Copyright 2014 the Melange authors.
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

"""MapReduce scripts that convert user entities to the new User model."""

import logging

from google.appengine.ext import ndb

from mapreduce import operation

from melange.models import user as user_model

from soc.models.user import User
from soc.modules.gci.models.program import GCIProgram
from soc.modules.gsoc.models.program import GSoCProgram


@ndb.transactional
def _createUserTxn(new_user):
  """Persists the specified user in the datastore."""
  new_user.put()


def convertUser(user_key):
  """Converts the specified user by creating a new user entity that inherits
  from the newly added NDB model.

  Args:
    user_key: User key.
  """
  user = User.get(user_key)

  entity_id = user.key().name()
  account_id = user.user_id

  if user.status == 'valid':
    status = user_model.Status.ACTIVE
  elif user.status == 'invalid':
    status = user_model.Status.BANNED
  else:
    operation.counters.Increment('Bad status')
    logging.warning(
        'Invalid status %s for user %s', user.status, user.key().name())
    return

  host_for = []
  for sponsor_key in user.host_for:
    host_for.extend(map(
        ndb.Key.from_old_key,
        GSoCProgram.all(keys_only=True)
            .filter('sponsor', sponsor_key).fetch(1000)))
    host_for.extend(map(
        ndb.Key.from_old_key,
        GCIProgram.all(keys_only=True)
            .filter('sponsor', sponsor_key).fetch(1000)))

  account = user.account

  new_user = user_model.User(
      id=entity_id, account_id=account_id, status=status, host_for=host_for,
      account=account)
  _createUserTxn(new_user)
