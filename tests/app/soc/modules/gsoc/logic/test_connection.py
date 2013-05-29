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
  
  def setUp(self):
    program = seeder_logic.seed(GSoCProgram)
    
    profile_helper = GSoCProfileHelper(program, None)
    self.user = profile_helper.createUser()
    self.profile = profile_helper.createProfile()
    
    self.org = GSoCProgramHelper().createNewOrg(override={'program' : program})
    self.connection = connection_utils.seed_new_connection(self.user, self.org)
  
  def testConnectionExists(self):
    """Tests that existing GSoCConnection objects between Profiles and
    Organizations can be fetched with this helper.
    """
    self.assertTrue(
      connection_logic.connectionExists(self.profile.parent(), self.org)
      ) 
    self.connection.delete()
    self.assertFalse(
      connection_logic.connectionExists(self.profile.parent(), self.org)
      )
  
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
