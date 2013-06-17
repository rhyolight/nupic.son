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

from soc.logic import exceptions
from soc.models import connection
from soc.modules.gsoc.logic import connection as connection_logic
from soc.modules.gsoc.models.connection import GSoCConnection
from soc.modules.gsoc.models.connection_message import GSoCConnectionMessage
from soc.modules.gsoc.models.program import GSoCProgram
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests.utils import connection_utils
from tests.profile_utils import GSoCProfileHelper
from tests.program_utils import GSoCProgramHelper
from tests.test_utils import GSoCTestCase

class ConnectionTest(unittest.TestCase):
  """Base class for this module to encapsulate a setUp method that will
  initialize data common to each of the test classes in this module.
  """
  def setUp(self):
    self.program = seeder_logic.seed(GSoCProgram)
    
    self.profile_helper = GSoCProfileHelper(self.program, dev_test=False)
    self.user = self.profile_helper.createUser()
    self.profile = self.profile_helper.createProfile()
    
    self.program_helper = GSoCProgramHelper()
    self.org = self.program_helper.createNewOrg(
      override={'program' : self.program})
    self.connection = connection_utils.seed_new_connection(self.user, self.org)

class ConnectionExistsTest(ConnectionTest): 
  """Unit tests for the connection_logic.connectionExists function."""

  def testConnectionExists(self):
    """Tests that existing GSoCConnection objects between Profiles and
    Organizations can be fetched with this helper.
    """
    self.assertTrue(
      connection_logic.connectionExists(self.profile.parent(), self.org)) 
    self.connection.delete()
    self.assertFalse(
      connection_logic.connectionExists(self.profile.parent(), self.org))

class CreateConnectionTest(ConnectionTest):
  """Unit tests for the connection_logic.createConnection function."""
  
  def testCreateConnection(self):
    """Tests that a GSoCConnection object can be generated successfully.
    """
    self.connection.delete()
    connection_logic.createConnection(
        profile=self.profile, org=self.org,
        user_state=connection.STATE_ACCEPTED,
        org_state=connection.STATE_UNREPLIED,
        role=connection.MENTOR_ROLE
        )
    new_connection = GSoCConnection.all().get()
    self.assertEqual(self.user.key(), new_connection.parent().key())
    self.assertEqual(self.org.key(), new_connection.organization.key())
    self.assertEqual(connection.STATE_ACCEPTED, new_connection.user_state)
    self.assertEqual(connection.STATE_UNREPLIED, new_connection.org_state)
    self.assertEqual(connection.MENTOR_ROLE, new_connection.role)
    
    # Also test to ensure that a connection will not be created if a logically
    # equivalent connection already exists.
    self.assertRaises(
        exceptions.AccessViolation, connection_logic.createConnection,
        profile=self.profile, org=self.org, 
        user_state=connection.STATE_UNREPLIED, 
        org_state=connection.STATE_UNREPLIED,
        role=connection.MENTOR_ROLE
        )

class CreateConnectionMessageTest(ConnectionTest):
  """Unit tests for the connection_logic.createConnectionMessage function."""
  
  def testCreateConnectionMessage(self):
    """Tests that a GSoCConnectionMessage can be added to an existing
    GSoCConnection object.
    """
    message = connection_logic.createConnectionMessage(
        connection=self.connection,
        author=self.profile,
        content='Test message!'
        )
    message = GSoCConnectionMessage.all().ancestor(self.connection).get()
    self.assertTrue(isinstance(message, GSoCConnectionMessage))
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
      self.user, organization2)

    # create a few messages for the other connection
    for _ in range(10):
      connection_utils.seed_new_connection_message(
          connection2, author=self.profile)

    # check that correct messages are returned
    messages = connection_logic.getConnectionMessages(self.connection)
    expected_keys = set(message1.key(), message2.key())
    actual_keys = set([m.key() for m in messages])
    self.assertEqual(actual_keys, expected_keys)
