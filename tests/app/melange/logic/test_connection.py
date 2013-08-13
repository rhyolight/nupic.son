# Copyright 2011 the Melange authors.
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

"""Tests for soc.modules.gsoc.logic.connection."""

import unittest

from melange.request import exception
from melange.logic import connection as connection_logic
from melange.models import connection
from melange.models.connection_message import ConnectionMessage
from soc.models.organization import Organization
from soc.models.profile import Profile
from soc.models.program import Program
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests.utils import connection_utils
from tests.profile_utils import ProfileHelper
from tests.program_utils import ProgramHelper

class ConnectionTest(unittest.TestCase):
  """Base class for this module to encapsulate a setUp method that will
  initialize data common to each of the test classes in this module.
  """
  def setUp(self):
    self.program = seeder_logic.seed(Program)
    
    self.profile_helper = ProfileHelper(self.program, dev_test=False)
    user = self.profile_helper.createUser()
    profile_properties = {'link_id': user.link_id, 'student_info': None,
        'user': user,'parent': user, 'scope': self.program,
        'status': 'active','email': user.account.email(),
        'program': self.program,'mentor_for': [], 'org_admin_for': [],
        'is_org_admin': False, 'is_mentor': False, 'is_student': False
        }
    self.profile = self.profile_helper.seed(Profile, profile_properties)
    
    self.program_helper = ProgramHelper()
    org_properties = {
        'scope': self.program, 'status': 'active',
        'scoring_disabled': False, 'max_score': 5,
        'home': None, 'program': self.program,
        }
    self.org = self.program_helper.seed(Organization, org_properties)
    self.connection = connection_utils.seed_new_connection(self.profile, self.org)

class ConnectionExistsTest(ConnectionTest): 
  """Unit tests for the connection_logic.connectionExists function."""

  def testConnectionExists(self):
    """Tests that existing Connection objects between Profiles and
    Organizations can be fetched with this helper.
    """
    self.assertTrue(
      connection_logic.connectionExists(self.profile, self.org))
    self.connection.delete()
    self.assertFalse(
      connection_logic.connectionExists(self.profile, self.org))

class CreateConnectionTest(ConnectionTest):
  """Unit tests for the connection_logic.createConnection function."""
  
  def testCreateConnection(self):
    """Tests that a Connection object can be generated successfully.
    """
    self.connection.delete()
    connection_logic.createConnection(
        profile=self.profile, org=self.org,
        user_role=connection.NO_ROLE,
        org_role=connection.MENTOR_ROLE,
        )
    new_connection = connection.Connection.all().get()
    self.assertEqual(self.profile.key(), new_connection.parent().key())
    self.assertEqual(self.org.key(), new_connection.organization.key())
    self.assertEqual(connection.NO_ROLE, new_connection.user_role)
    self.assertEqual(connection.MENTOR_ROLE, new_connection.org_role)
    
    # Also test to ensure that a connection will not be created if a logically
    # equivalent connection already exists.
    self.assertRaises(
        ValueError, connection_logic.createConnection,
        profile=self.profile, org=self.org, 
        user_role=connection.NO_ROLE,
        org_role=connection.NO_ROLE
        )

class CreateConnectionMessageTest(ConnectionTest):
  """Unit tests for the connection_logic.createConnectionMessage function."""
  
  def testCreateConnectionMessage(self):
    """Tests that a onnectionMessage can be added to an existing
    GSoCConnection object.
    """
    message = connection_logic.createConnectionMessage(
        connection=self.connection,
        author=self.profile,
        content='Test message!'
        )
    message = ConnectionMessage.all().ancestor(self.connection).get()
    self.assertTrue(isinstance(message, ConnectionMessage))
    self.assertEqual(self.profile.key(), message.author.key())
    self.assertEqual('Test message!', message.content)

class GetConnectionMessagesTest(ConnectionTest):
  """Unit tests for the connection_logic.getConnectionMessage function."""
  
  def testGetConnectionMessages(self):
    """Tests that all messages affiliated with a given Connection will
    be returned by the query in connection logic.
    """
    # create a couple of messages for the connection
    message1 = connection_utils.seed_new_connection_message(
        self.connection, author=self.profile)
    message2 = connection_utils.seed_new_connection_message(
        self.connection, author=self.profile)

    # create another organization and a connection
    organization2 = self.program_helper.createNewOrg(
        {'program' : self.program})
    connection2 = connection_utils.seed_new_connection(
      self.profile, organization2)

    # create a few messages for the other connection
    for _ in range(10):
      connection_utils.seed_new_connection_message(
          connection2, author=self.profile)

    # check that correct messages are returned
    messages = connection_logic.getConnectionMessages(self.connection)
    expected_keys = set([message1.key(), message2.key()])
    actual_keys = set([m.key() for m in messages])
    self.assertEqual(actual_keys, expected_keys)
