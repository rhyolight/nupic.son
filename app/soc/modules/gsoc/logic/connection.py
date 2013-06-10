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

"""Query and functions for GSoCConnection.
"""

from soc.logic import exceptions
from soc.modules.gsoc.logic import connection_message as connection_message_logic
from soc.modules.gsoc.models.connection import GSoCConnection
from soc.modules.gsoc.models.connection_message import GSoCConnectionMessage

CONNECTION_EXISTS_ERROR = \
    "Connection between %s and %s already exists."

def queryForAncestor(ancestor, keys_only=False):
  """Returns a Query object for Connections with the specified ancestor.
  """
  return GSoCConnection.all(keys_only=keys_only).ancestor(ancestor)


def queryForAncestorAndOrganization(ancestor, organization, keys_only=False):
  """Returns a Query object for Connections with the specified ancestor and
  Organization.
  """
  query = GSoCConnection.all(keys_only=keys_only).ancestor(ancestor)
  query.filter('organization', organization)
  return query

def connectionExists(user, organization):
  """Check to see whether or not a Connection exists between a user and
  an organization.

  Args:
    user: User instance for the connection
    organization: GSoCOrganization for the connection.

  Returns:
    True if a GSoCConnection object exists for the given User and
    Organization, else False.
  """
  query = queryForAncestorAndOrganization(user, organization, True)
  return query.count(limit=1) > 0

def createConnection(profile, org, user_state, org_state, role):
  """Create a new GSoCConnection instance based on the contents of the form
  and the roles provided.

  Args:
    profile: GSoCProfile with which to establish the connection.
    org: Organization with which to establish the connection.
    user_state: The user's response state for the connection.
    org_state: The org's response state for the connection.
    role: Role to offer the user (see soc.models.Connection for opts).

  Returns:
      Newly created GSoCConnection instance.

  Raises:
      AccessViolation if a connection exists between the user and organization.
  """
  if connectionExists(profile.parent_key(), org):
    raise exceptions.AccessViolation(
        CONNECTION_EXISTS_ERROR % (profile.name(), org.name()))

  connection = GSoCConnection(
      parent=profile.parent(), organization=org
      )
  connection.user_state = user_state
  connection.org_state = org_state
  connection.role = role
  connection.put()

  return connection

def createConnectionMessage(connection, author, content, auto_generated=False):
  """Create a new GSoCConnectionMessage to represent a message left
  on a GSoCConnection entity.

  Args:
    connection: GSoCConnection on which the message was left.
    author: Profile of the user leaving the message.
    content: String content of the message.
    auto_generated: True if the message was system-generated, False if the
        message contains a user-provided message,

  Returns:
    Newly created GSoCConnectionMessage entity.
  """
  message = GSoCConnectionMessage(parent=connection)
  message.content = content
  if auto_generated:
    message.is_auto_generated = True
  else:
    message.author = author
  message.put()

  return message

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