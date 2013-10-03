# Copyright 2008 the Melange authors.
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

"""User (Model) query functions."""

from google.appengine.api import users
from google.appengine.runtime import apiproxy_errors

from melange.request import exception
from soc.logic import accounts
from soc.models import user as user_model


MELANGE_DELETED_USER = 'melange_deleted_user'

def isFormerAccount(account):
  """Returns true if account is a former account of some User.
  """
  return user_model.User.all().filter('former_accounts', account).count() > 0


def forCurrentAccount():
  """Retrieves the user entity for the currently logged in account.

  Also Updates the user entity's unique identifier. getCurrentUser() should
  be favored over this method.

  If there is no user logged in, or they have no valid associated User
  entity, None is returned.
  """
  account = accounts.getCurrentAccount()

  if not account:
    return None

  user_ent = forAccount(account)

  if user_ent and not user_ent.user_id and account.user_id():
    # update the user id that was added to GAE after Melange was launched
    try:
      user_ent.user_id = account.user_id()
      user_ent.put()
    except apiproxy_errors.CapabilityDisabledError:
      # readonly mode, that's fine
      pass

  return user_ent


def forCurrentUserId():
  """Retrieves the user entity for the currently logged in user id.

  If there is no user logged in, or they have no valid associated User
  entity, None is returned.
  """
  user_id = accounts.getCurrentUserId()

  if not user_id:
    return None

  user_ent = forUserId(user_id)

  current_account = accounts.getCurrentAccount()
  if user_ent and (str(user_ent.account) != str(current_account)):
    # The account of the user has changed, we use this account to send system
    # emails to.
    try:
      user_ent.account = current_account
      user_ent.put()
    except apiproxy_errors.CapabilityDisabledError:
      # readonly mode, that's fine
      pass

  return user_ent


def current():
  """Retrieves the user entity for the currently logged in user.

  Returns:
    The User entity of the logged in user or None if not available.
  """
  # look up with the unique id first
  user_ent = forCurrentUserId()

  if user_ent:
    return user_ent

  # look up using the account address thereby setting the unique id
  return forCurrentAccount()


def forAccount(account):
  """Retrieves the user entity for the specified account.

  If there is no user logged in, or they have no valid associated User
  entity, None is returned.
  """
  if not account:
    raise exception.BadRequest(message="Missing argument 'account'")

  account = accounts.normalizeAccount(account)

  q = user_model.User.all()
  q.filter('account', account)
  q.filter('status', 'valid')
  return q.get()


def forUserId(user_id):
  """Retrieves the user entity for the specified user id.

  If there is no user logged in, or they have no valid associated User
  entity, None is returned.
  """
  if not user_id:
    raise exception.BadRequest(message="Missing argument 'user_id'")

  q = user_model.User.all()
  q.filter('user_id', user_id)
  q.filter('status', 'valid')
  return q.get()


def isDeveloper(account=None, user=None):
  """Returns true iff the specified user is a Developer.

  Args:
    account: if not supplied, defaults to the current account
    user: if not specified, defaults to the current user
  """
  current = accounts.getCurrentAccount()

  if not account:
    # default account to the current logged in account
    account = current

  if account and (not user):
    # default user to the current logged in user
    user = forAccount(account)

  # pylint: disable=E1103
  if user and user.is_developer:
    return True

  if account and (account == current):
    return users.is_current_user_admin()


def getOrCreateDummyMelangeDeletedUser():
  """Fetches or creates the dummy melange deleted user entity.
  """
  q = user_model.User.all().filter('link_id', MELANGE_DELETED_USER)
  user_ent = q.get()

  # If the requested user does not exist, create one.
  if not user_ent:
    account = users.User(email=MELANGE_DELETED_USER)
    user_ent = user_model.User(
        key_name=MELANGE_DELETED_USER, account=account,
        link_id=MELANGE_DELETED_USER)
    user_ent.put()

  return user_ent
