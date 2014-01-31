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


class NewUser(user_model.User):
  pass

@ndb.transactional
def _createUserTxn(new_user):
  """Persists the specified user in the datastore."""
  new_user.put()


def convertUser(user_key):
  """Converts the specified user by creating a new user entity that inherits
  from the newly added NewUser model.

  Args:
    user_key: User key.
  """
  user = User.get(user_key)

  entity_id = user.key().name()
  account_id = user.user_id or 'unset'

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

  new_user = NewUser(
      id=entity_id, account_id=account_id, status=status, host_for=host_for,
      account=account)
  _createUserTxn(new_user)

# TODO(nathaniel): Remove the suppression on the following line when
# https://bitbucket.org/logilab/pylint.org/issue/6/false-positive-no
# is fixed.
@ndb.transactional(xg=True)  # pylint: disable=no-value-for-parameter
def newUserToUser(new_user_key):
  """Converts the specified new user to a user.

  Args:
    new_user_key: NewUser key.
  """
  new_user_key = ndb.Key.from_old_key(new_user_key)
  new_user = new_user_key.get()
  user = user_model.User(id=new_user.key.id(), **new_user.to_dict())
  user.put()
