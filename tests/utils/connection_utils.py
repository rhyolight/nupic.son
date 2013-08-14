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

""" Utilities to manipulate Connection data."""

from melange.models import connection as connection_model
from melange.models import connection_message as connection_message_model

from soc.modules.seeder.logic.seeder import logic as seeder_logic


def seed_new_connection(profile, organization, **kwargs):
  """Seeds and returns a new GSoCConnection entity with the specified
  properties.

  Args:
    profile: Profile entity for the connection
    organization: Organization entity for the connection

  Returns:
    the newly seeded GSoCConnection entity
  """
  properties = {
      'parent': profile,
      'organization': organization,
      'org_role' : connection_model.NO_ROLE,
      'user_role' : connection_model.NO_ROLE
      }
  properties.update(kwargs)
  
  return seeder_logic.seed(connection_model.Connection, properties,
      recurse=False, auto_seed_optional_properties=True)


def seed_new_connection_message(connection, **kwargs):
  """Seeds and returns a new GSoCConnectionMassage entity for the specified
  connection and other properties.

  Args:
    connection: Connection entity to seed a message for

  Returns:
    the newly seeded GSoCConnectionMessage entity
  """

  properties = {
      'parent': connection
      }
  properties.update(kwargs)

  return seeder_logic.seed(connection_message_model.ConnectionMessage,
      properties, recurse=False, auto_seed_optional_properties=True)
