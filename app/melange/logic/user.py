# Copyright 2013 the Melange authors.
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

"""Logic for users."""

from google.appengine.api import users as users_api
from google.appengine.ext import ndb

from django.utils import translation

from melange.models import user as user_model
from melange.utils import rich_bool


_ACCOUNT_NOT_LOGGED_IN = translation.ugettext(
    'User may be registered only for a user logged in with Google Account.')

_USER_EXISTS_FOR_USERNAME = translation.ugettext(
    'User already exists for username %s.')

def createUser(username, host_for=None):
  """Creates a new User entity for the specified username for the currently
  logged in account.

  Please note that there should be one-one relationship between Google Accounts
  and User entities. This function, however, does not check if User entity does
  not exist for the account. Therefore, the callers should try to make sure that
  this function will not create a duplicate User entity.

  This function will raise an error, if it is not called from within
  a transaction.

  Args:
    username: A string containing username.
    host_for: A list of program keys for which the user has a program
      administrator role.

  Returns:
    RichBool whose value is set to True if user has been successfully created.
    In that case, extra part points to the newly created user entity. Otherwise,
    RichBool whose value is set to False and extra part is a string that
    represents the reason why the action could not be completed.
    """
  if not ndb.in_transaction():
    raise RuntimeError('This function must be called from within a transaction')

  account = users_api.get_current_user()
  if not account:
    return rich_bool.RichBool(False, _ACCOUNT_NOT_LOGGED_IN)
  elif user_model.User.get_by_id(username):
    # there is already a user with the specified username
    return rich_bool.RichBool(False, _USER_EXISTS_FOR_USERNAME % username)
  else:
    host_for = host_for or []
    user = user_model.User(
        id=username, account_id=account.user_id(), host_for=host_for)
    user.put()
    return rich_bool.RichBool(True, user)


def getByCurrentAccount():
  """Returns user_model.User entity associated with Google account of
  the current user.

  Please note that this function executes a non-ancestor query, so it cannot
  be safely used within transactions.

  Returns:
    user_model.User entity for the current account or None, if no entity has
    ever been created for this user.
  """
  account = users_api.get_current_user()
  return None if not account else user_model.User.query(
       user_model.User.account_id == account.user_id()).get()


def isHostForProgram(user, program_key):
  """Tells whether the specified user is a host for the specified program.

  If no user entity is supplied, it is considered as not a program host.

  Args:
    user: User entity.
    program_key: Program key.

  Returns:
    True if the specified user is a host for the specified program.
    False, otherwise.
  """
  return user and ndb.Key.from_old_key(program_key) in user.host_for


def getHostsForProgram(program_key):
  """Returns all users who are hosts for the specified program.

  Args:
    program_key: Program key.

  Returns:
    A list of user entities representing program administrators.
  """
  query = user_model.User.query(
      user_model.User.host_for == ndb.Key.from_old_key(program_key))
  return query.fetch(1000)
