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

"""Query and functions for Connection.
"""

from melange.logic import connection_message as connection_message_logic
from melange.models.connection import Connection
from melange.models.connection import ConnectionMessage

CONNECTION_EXISTS_ERROR = \
    "Connection between %s and %s already exists."

def queryForAncestor(ancestor, keys_only=False):
  """Returns a Query object for Connections with the specified ancestor.
  """
  return Connection.all(keys_only=keys_only).ancestor(ancestor)

def queryForAncestorAndOrganization(ancestor, organization, keys_only=False):
  """Returns a Query object for Connections with the specified ancestor and
  Organization.
  """
  query = Connection.all(keys_only=keys_only).ancestor(ancestor)
  query.filter('organization', organization)
  return query

def connectionExists(profile, organization):
  """Check to see whether or not a Connection exists between a user and
  an organization.

  Args:
    profile: Profile instance (parent) for the connection.
    organization: Organization for the connection.

  Returns:
    True if a Connection object exists for the given User and
    Organization, else False.
  """
  query = queryForAncestorAndOrganization(profile, organization, True)
  return query.count(limit=1) > 0

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
  if connectionExists(profile.parent_key(), org):
    raise ValueError(CONNECTION_EXISTS_ERROR % (profile.name(), org.name))

  connection = Connection(parent=profile, organization=org)
  connection.user_role = user_role
  connection.org_role = org_role
  connection.put()

  return connection

def createConnectionMessage(connection, author, content, auto_generated=False):
  """Create a new ConnectionMessage to represent a message left
  on a Connection entity.

  Args:
    connection: Connection on which the message was left.
    author: Profile of the user leaving the message.
    content: String content of the message.
    auto_generated: True if the message was system-generated, False if the
        message contains a user-provided message,

  Returns:
    Newly created ConnectionMessage entity.
  """
  message = ConnectionMessage(parent=connection)
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