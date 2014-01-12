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

""" Utilities to manipulate connection data."""

from melange.models import connection as connection_model


def seed_new_connection(profile_key, org_key, **kwargs):
  """Seeds a new connection.

  Args:
    profile_key: Profile key for the connection.
    org_key: Organization key for the connection.

  Returns:
    The newly seeded connection entity.
  """
  properties = {
      'organization': org_key,
      'org_role' : connection_model.NO_ROLE,
      'user_role' : connection_model.NO_ROLE
      }
  properties.update(kwargs)

  connection = connection_model.Connection(parent=profile_key, **properties)
  connection.put()
  return connection


def seed_new_connection_message(connection_key, **kwargs):
  """Seeds and returns a new connection message entity for the specified
  connection and other properties.

  Args:
    connection_key: Connection key to seed a message for.

  Returns:
    The newly seeded connection message entity.
  """
  message = connection_model.ConnectionMessage(parent=connection_key, **kwargs)
  message.put()
  return message

