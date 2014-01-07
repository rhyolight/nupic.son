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

"""Query and functions for Connection."""

from datetime import datetime
from datetime import timedelta
import uuid

from google.appengine.ext import db
from google.appengine.ext import ndb

from django.utils import translation

from melange.logic import connection_message as connection_message_logic
from melange.models import connection as connection_model
from melange.utils import rich_bool


_CONNECTION_EXISTS = translation.ugettext(
    'Connection between %s and %s already exists.')

_INVALID_TOKEN = translation.ugettext(
    'No Connection exists for token %s.')

_CONNECTION_EXPIRED = translation.ugettext(
    'The Connection for the token %s has expired.')

_PROFILE_IS_STUDENT = translation.ugettext(
    'Profile %s is a student.')

_ORG_ROLE_CHANGED = translation.ugettext(
    'Role offered by organization changed to <strong>%s</strong> by %s.')

_ORG_STARTED_CONNECTION = translation.ugettext(
    'Organization started connection by %s and offers %s.')

_USER_STARTED_CONNECTION = translation.ugettext(
    'User started connection and requests role.')

_USER_REQUESTS_ROLE = translation.ugettext(
    'User requests role from organization.')

_USER_DOES_NOT_REQUEST_ROLE = translation.ugettext(
    'User does not request role from organization.')

#: Constant indicating that action has been initiated by an organization.
ORG_ACTION_ORIGIN = 'org_origin'

#: Constant indicating that action has been initiated by a user.
USER_ACTION_ORIGIN = 'user_origin'


def _updateSeenByProperties(connection, action_origin):
  """Updates seen_by_org and seen_by_user properties of the specified
  connection based on the specified origin of the action which has been taken.

  Please note that updated connection entity is not saved in the datastore.

  Args:
    connection: Connection entity.
    action_origin: Origin of the action. Must be one of ORG_ACTION_ORIGIN
      or USER_ACTION_ORIGIN.

  Returns:
    Updated connection entity.
  """
  if action_origin == ORG_ACTION_ORIGIN:
    connection.seen_by_org = True
    connection.seen_by_user = False
  elif action_origin == USER_ACTION_ORIGIN:
    connection.seen_by_org = False
    connection.seen_by_user = True
  else:
    raise ValueError(
        'Invalid value specified as the origin of action: %s' % action_origin)

  return connection


def queryForAncestor(ancestor):
  """Returns a Query object for Connections with the specified ancestor.

  Args:
    ancestor: The specified ancestor key.

  Returns:
    ndb.Query object for the specified parameters.
  """
  return connection_model.Connection.query(ancestor=ancestor)


def queryForOrganizations(org_keys):
  """Returns a query to fetch all connection entities that correspond to the
  specified organizations.

  Args:
    org_keys: List of organization keys.

  Returns:
    db.Query object to fetch all connection entities for the organizations.
  """
  if org_keys:
    return connection_model.Connection.query(
      connection_model.Connection.organization.IN(org_keys))
  else:
    raise ValueError('List of organizations cannot be empty.')


def connectionExists(profile_key, org_key):
  """Check to see whether or not a Connection exists between the specified
  profile and organization.

  Args:
    profile_key: Profile key.
    org_key: Organization key.

  Returns:
    True if a Connection object exists for the given profile and
    organization, else False.
  """
  return bool(connection_model.Connection.query(
      connection_model.Connection.organization == org_key,
      ancestor=profile_key).count(keys_only=True, limit=1))


def canCreateConnection(profile, org_key):
  """Tells whether a connection between the specified profile and organization
  can be created.

  Args:
    profile: profile entity.
    org_key: organization key.

  Returns:
    RichBool whose value is set to True, if a connection can be created.
    Otherwise, RichBool whose value is set to False and extra part is
    a string that represents the reason why it is not possible to create
    a new connection.
  """
  # TODO(daniel): remove when GCI orgs are converted to NDB
  if isinstance(org_key, ndb.Key):
    org_key = org_key.to_old_key()

  if profile.is_student:
    return rich_bool.RichBool(
        False, extra=_PROFILE_IS_STUDENT % profile.link_id)
  elif connectionExists(ndb.Key.from_old_key(profile.key()), org_key):
    return rich_bool.RichBool(
        False, extra=_CONNECTION_EXISTS % (profile.link_id, org_key.name()))
  else:
    return rich_bool.TRUE


def createConnection(profile, org, user_role, org_role):
  """Create a new Connection instance based on the contents of the form
  and the roles provided.

  Args:
    profile: Profile with which to establish the connection.
    org: Organization with which to establish the connection.
    user_role: The user's role for the connection.
    org_role: The org's role for the connection.

  Returns:
      Newly created Connection instance.

  Raises:
      ValueError if a connection exists between the user and organization.
  """
  # TODO(daniel): remove when GCI orgs are converted to NDB
  if isinstance(org, db.Model):
    org_key = org.key()
  elif isinstance(org, ndb.Key):
    org_key = org_key.to_old_key()
  elif isinstance(org, db.Key):
    org_key = org
  elif isinstance(org, ndb.Model):
    org_key = org.key.to_old_key()
  else:
    raise TypeError('Wrong type for org argument: %s' % type(org))

  if connectionExists(ndb.Key.from_old_key(profile.parent_key()), org_key):
    raise ValueError(_CONNECTION_EXISTS % (profile.name(), org.name))

  connection = connection_model.Connection(
      parent=profile, organization=org_key)
  connection.user_role = user_role
  connection.org_role = org_role
  connection.put()

  return connection


def createAnonymousConnection(email, org, org_role):
  """Create a new AnonymousConnection to act as a placeholder so that a
  user can register and enroll with an organization from within a week
  of the date the connection is created.

  Args:
    email: Email address for the user who is receiving the AnonymousConnection.
    org: Organization instance for which the anonymous connection was created.
    org_role: String constant from connection models module. This should
      either be MENTOR_ROLE or ORG_ADMIN_ROLE (constants from module).
  """
  # AnonymousConnection objects will only be considered valid for one week.
  expiration = datetime.today() + timedelta(7)
  token = uuid.uuid4().hex

  connection = connection_model.AnonymousConnection(
      parent=org.key.to_old_key(),
      org_role=org_role,
      token=token,
      expiration_date=expiration,
      email=email
      )
  connection.put()
  return connection

def queryAnonymousConnectionForToken(token):
  """Attempt to retrieve an AnonymousConnection object given a token that
  should have been provided by the url.

  Args:
    token: Token (string representation of UUID) for the AnonymousConnection.

  Returns:
    AnonymousConnection object matching the token or None if it doesn't exist.
  """
  query = connection_model.AnonymousConnection.all()
  query.filter('token', token)
  return query.get()

def activateAnonymousConnection(profile, token):
  """Create a new Connection between the user and an organization from an
  existing AnonymousConnection and removes the latter.

  Args:
    profile: Profile with which to establish the connection.
    token: Token generated for the AnonymousConnection object.

  Returns:
    Newly created Connection object with org_role set to whatever the org
    originally specified and user_role set to NO_ROLE.

  Raises:
    ValueError if the AnonymousConnection does not exist or if it has expired.
  """
  anonymous_connection = queryAnonymousConnectionForToken(token)
  if not anonymous_connection:
    raise ValueError(_INVALID_TOKEN % token)
  if datetime.today() > anonymous_connection.expiration_date:
    anonymous_connection.delete()
    raise ValueError(_CONNECTION_EXPIRED % token)

  org_role = anonymous_connection.org_role
  new_connection = createConnection(
      profile=profile,
      org=anonymous_connection.parent_key(),
      org_role=org_role,
      user_role=connection_model.NO_ROLE
      )
  anonymous_connection.delete()
  return new_connection

def createConnectionMessage(connection_key, content, author_key=None):
  """Create a new ConnectionMessage to represent a message left
  on the specified connection.

  Please note that the created entity is not persisted in the datastore.

  Args:
    connection: connection key.
    content: message content as a string
    author_key: profile key of the user who is the author of the message.
      If set to None, the message is considered auto-generated by the system.

  Returns:
    Newly created ConnectionMessage entity.
  """
  return connection_model.ConnectionMessage(
      parent=connection_key, content=content, author=author_key,
      is_auto_generated=not bool(author_key))


def getConnectionMessages(connection, limit=1000):
  """Returns messages for the specified connection

  Args:
    connection: the specified Connection entity
    limit: maximal number of results to return

  Returns:
    list of messages corresponding to the specified connection
  """
  builder = connection_message_logic.QueryBuilder()
  return builder.addAncestor(connection).setOrder('created').build().fetch(
      limit=limit)


def generateMessageOnStartByUser(connection):
  """Creates auto-generated message after the specified connection is
  started by user.

  Args:
    connection: connection entity.

  Returns:
    newly created connection message.
  """
  message = createConnectionMessage(connection.key(), _USER_STARTED_CONNECTION)
  message.put()

  return message


def generateMessageOnStartByOrg(connection, org_admin):
  """Creates auto-generated message after the specified connection is
  started by the specified organization administrator.

  Args:
    connection: connection entity.
    org_admin: profile entity of organization administrator who started
      the connection.

  Returns:
    newly created connection message.
  """
  content = _ORG_STARTED_CONNECTION % (
      org_admin.name(),
      connection_model.VERBOSE_ROLE_NAMES[connection.org_role])

  message = createConnectionMessage(connection.key(), content)
  message.put()

  return message


def generateMessageOnUpdateByOrg(connection, org_admin, old_org_role):
  """Creates auto-generated message after the specified connection is
  updated by the specified organization administrator.

  Args:
    connection: connection entity.
    org_admin: profile entity of organization administrator who updates
      organization role for the connection.
    old_org_role: previous organization role, before the connection
      is updated.

  Returns:
    newly created connection message or None, if nothing has changed.
  """
  if connection.org_role != old_org_role:
    lines = []
    lines.append(_ORG_ROLE_CHANGED % (connection_model.VERBOSE_ROLE_NAMES[
        connection.org_role], org_admin.name()))

    content = '\n'.join(lines)
    return createConnectionMessage(connection.key(), content)
  else:
    return None


def generateMessageOnUpdateByUser(connection, old_user_role):
  """Creates auto-generated message after the specified connection is
  updated by the connected user.

  Args:
    connection: connection entity.
    old_user_role: previous user role, before the connection is updated.

  Returns:
    newly created connection message or None, if nothing has changed.
  """
  if connection.user_role != old_user_role:
    lines = []
    if connection.user_role == connection_model.NO_ROLE:
      lines.append(_USER_DOES_NOT_REQUEST_ROLE)
    else: # user requests role
      lines.append(_USER_REQUESTS_ROLE)

    content = '\n'.join(lines)
    return createConnectionMessage(connection.key(), content)
  else:
    return None
