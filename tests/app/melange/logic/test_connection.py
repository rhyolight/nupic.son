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

from google.appengine.ext import db

from datetime import datetime
from datetime import timedelta
import mock
import unittest

from nose.plugins import skip

from melange.logic import connection as connection_logic
from melange.models import connection as connection_model
from soc.models import organization as org_model
from soc.models import profile as profile_model
from soc.models.program import Program
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests import profile_utils
from tests.utils import connection_utils
from tests.program_utils import ProgramHelper


TEST_MESSAGE_CONTENT = 'Test Message Content'

class ConnectionTest(unittest.TestCase):
  """Base class for this module to encapsulate a setUp method that will
  initialize data common to each of the test classes in this module.
  """
  def setUp(self):
    self.program = seeder_logic.seed(Program)
    
    self.profile_helper = profile_utils.ProfileHelper(
        self.program, dev_test=False)
    user = profile_utils.seedUser()
    profile_properties = {'link_id': user.link_id, 'student_info': None,
        'user': user,'parent': user, 'scope': self.program,
        'status': 'active','email': user.account.email(),
        'program': self.program,'mentor_for': [], 'org_admin_for': [],
        'is_org_admin': False, 'is_mentor': False, 'is_student': False
        }
    self.profile = self.profile_helper.seed(
        profile_model.Profile, profile_properties)
    
    self.program_helper = ProgramHelper()
    org_properties = {
        'scope': self.program, 'status': 'active',
        'scoring_disabled': False, 'max_score': 5,
        'home': None, 'program': self.program,
        }
    self.org = self.program_helper.seed(org_model.Organization, org_properties)
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
    # TODO(daniel): this test fails sometimes when run locally on my machine
    raise skip.SkipTest()
    self.connection.delete()
    connection_logic.createConnection(
        profile=self.profile, org=self.org,
        user_role=connection_model.NO_ROLE,
        org_role=connection_model.MENTOR_ROLE,
        )
    new_connection = connection_model.Connection.all().get()
    self.assertEqual(self.profile.key(), new_connection.parent().key())
    self.assertEqual(self.org.key(), new_connection.organization.key())
    self.assertEqual(connection_model.NO_ROLE, new_connection.user_role)
    self.assertEqual(connection_model.MENTOR_ROLE, new_connection.org_role)
    
    # Also test to ensure that a connection will not be created if a logically
    # equivalent connection already exists.
    self.assertRaises(
        ValueError, connection_logic.createConnection,
        profile=self.profile, org=self.org, 
        user_role=connection_model.NO_ROLE,
        org_role=connection_model.NO_ROLE
        )

class CreateConnectionMessageTest(ConnectionTest):
  """Unit tests for the createConnectionMessage function."""
  
  def testCreateMessage(self):
    """Tests that a message with an author is created properly."""
    # seed connection message
    connection_logic.createConnectionMessage(
        self.connection, TEST_MESSAGE_CONTENT, author_key=self.profile.key())

    message = connection_model.ConnectionMessage.all().ancestor(
        self.connection).get()
    self.assertEqual(message.parent_key(), self.connection.key())
    self.assertEqual(message.content, TEST_MESSAGE_CONTENT)
    self.assertEqual(message.author.key(), self.profile.key())
    self.assertFalse(message.is_auto_generated)

  def testCreateAutogeneratedMessage(self):
    """Tests that a message with no author is created properly."""
    # seed connection message
    connection_logic.createConnectionMessage(
        self.connection.key(), TEST_MESSAGE_CONTENT)

    message = connection_model.ConnectionMessage.all().ancestor(
        self.connection).get()
    self.assertEqual(message.parent_key(), self.connection.key())
    self.assertEqual(message.content, TEST_MESSAGE_CONTENT)
    self.assertIsNone(message.author)
    self.assertTrue(message.is_auto_generated)


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


class QueryForOrganizationAdminTest(unittest.TestCase):
  """Unit tests for queryForOrganizationAdmin function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    # seed a few organizations
    self.first_org = seeder_logic.seed(org_model.Organization)
    self.second_org = seeder_logic.seed(org_model.Organization)
    self.third_org = seeder_logic.seed(org_model.Organization)

    # seed a few profiles
    first_profile = seeder_logic.seed(profile_model.Profile)
    second_profile = seeder_logic.seed(profile_model.Profile)

    self.first_connection = connection_utils.seed_new_connection(
        first_profile, self.first_org)
    self.second_connection = connection_utils.seed_new_connection(
        second_profile, self.first_org)
    self.third_connection = connection_utils.seed_new_connection(
        first_profile, self.second_org)
    #connection_utils.seed_new_connection(third_profile, third_org)

  def testForMentor(self):
    """Tests that no connections are fetched for user who is a mentor only."""
    properties = {
        'is_org_admin': False,
        'is_mentor': True,
        'mentor_for': [self.first_org.key()],
        'org_admin_for': []
        }
    profile = seeder_logic.seed(profile_model.Profile, properties=properties)
    query = connection_logic.queryForOrganizationAdmin(profile)

    # exhaust the query to check what entities are fetched
    connections = query.fetch(1000)

    # check that correct connections are returned
    self.assertListEqual(connections, [])

  def testForOrgAdminForOneOrg(self):
    """Tests for organization admin for one orgs."""
    properties = {
        'is_org_admin': True,
        'is_mentor': True,
        'mentor_for': [self.first_org.key()],
        'org_admin_for': [self.first_org.key()]
        }
    profile = seeder_logic.seed(profile_model.Profile, properties=properties)
    query = connection_logic.queryForOrganizationAdmin(profile)

    # exhaust the query to check what entities are fetched
    connections = query.fetch(1000)

    # check that correct connections are returned
    self.assertEqual(len(connections), 2)
    self.assertIn(
        self.first_connection.key(),
        [connection.key() for connection in connections])
    self.assertIn(
        self.second_connection.key(),
        [connection.key() for connection in connections])

  def testForOrgAdminForManyOrgs(self):
    """Tests for organization admin for many orgs."""
    properties = {
        'is_org_admin': True,
        'is_mentor': True,
        'mentor_for': [self.first_org.key(), self.second_org.key()],
        'org_admin_for': [self.first_org.key(), self.second_org.key()]
        }
    profile = seeder_logic.seed(profile_model.Profile, properties=properties)
    query = connection_logic.queryForOrganizationAdmin(profile)

    # exhaust the query to check what entities are fetched
    connections = query.fetch(1000)

    # check that correct connections are returned
    self.assertEqual(len(connections), 3)
    self.assertIn(
        self.first_connection.key(),
        [connection.key() for connection in connections])
    self.assertIn(
        self.second_connection.key(),
        [connection.key() for connection in connections])
    self.assertIn(
        self.third_connection.key(),
        [connection.key() for connection in connections])


class CanCreateConnectionTest(unittest.TestCase):
  """Unit tests for canCreateConnection function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.profile = seeder_logic.seed(profile_model.Profile)
    self.org = seeder_logic.seed(org_model.Organization)

  def testForStudent(self):
    """Tests that a student profile cannot create a connection."""
    # make the profile a student
    self.profile.is_student = True

    result = connection_logic.canCreateConnection(self.profile, self.org.key())
    self.assertFalse(result)
    self.assertEqual(
        result.extra, 
        connection_logic._PROFILE_IS_STUDENT % self.profile.link_id)

  @mock.patch.object(connection_logic, 'connectionExists', return_value=True)
  def testForExistingConnection(self, mock_func):
    """Tests that a non-student profile with connection cannot create one."""
    # profile is not a student
    self.profile.is_student = False

    result = connection_logic.canCreateConnection(self.profile, self.org.key())
    self.assertFalse(result)
    self.assertEqual(
        result.extra, connection_logic._CONNECTION_EXISTS % (
            self.profile.link_id, self.org.key().name()))

  def testForNonExistingConnection(self):
    """Tests that a non-student profile with no connection can create one."""
    # profile is not a student
    self.profile.is_student = False

    result = connection_logic.canCreateConnection(self.profile, self.org.key())
    self.assertTrue(result)


class GenerateMessageOnStartByUserTest(unittest.TestCase):
  """Unit tests for generateMessageOnStartByUser function."""

  def testMessageIsCreated(self):
    """Tests that correct message is returned by the function."""
    # seed a connection and create a message
    connection = seeder_logic.seed(connection_model.Connection)
    message = connection_logic.generateMessageOnStartByUser(connection)

    self.assertEqual(message.parent_key(), connection.key())
    self.assertEqual(message.content, connection_logic._USER_STARTED_CONNECTION)
    self.assertTrue(message.is_auto_generated)


class GenerateMessageOnStartByOrgTest(unittest.TestCase):
  """Unit tests for generateMessageOnStartByOrg function."""

  def testMessageIsCreated(self):
    """Tests that correct message is returned by the function."""
    # seed a connection, org admin's profile and create a message
    connection = seeder_logic.seed(connection_model.Connection)
    org_admin = seeder_logic.seed(profile_model.Profile)
    message = connection_logic.generateMessageOnStartByOrg(
        connection, org_admin)

    self.assertEqual(message.parent_key(), connection.key())
    self.assertEqual(
        message.content, connection_logic._ORG_STARTED_CONNECTION % (
            org_admin.name(),
            connection_model.VERBOSE_ROLE_NAMES[connection.org_role]))
    self.assertTrue(message.is_auto_generated)

class CreateAnonymousConnectionTest(ConnectionTest):
  """Unit test for createAnonymousConnection function."""

  def testCreateAnonymousConnection(self):
    """Test that an AnonymousConnection can be created successfully."""
    connection_logic.createAnonymousConnection(org=self.org,
        org_role=connection_model.MENTOR_ROLE)
    expected_expiration =  datetime.today() + timedelta(7)

    connection = connection_model.AnonymousConnection.all().get()
    self.assertEquals(expected_expiration.date(),
        connection.expiration_date.date())
    self.assertEquals(connection_model.MENTOR_ROLE, connection.org_role)


class QueryAnonymousConnectionTest(ConnectionTest):
  """Unit test for the queryAnonymousConnectionForToken function."""

  def testQueryInvalidToken(self):
    """Test that the function will fail to fetch any AnonymousConnections
    given a token that does not correspond to any objects.
    """
    connection = connection_logic.queryAnonymousConnectionForToken('bad_token')
    self.assertIsNone(connection)

  def testQueryForAnonymousConnection(self):
    """Test that the function will correctly fetch AnonymousConnection objects
    given a valid token."""
    connection_logic.createAnonymousConnection(org=self.org,
        org_role=connection_model.MENTOR_ROLE)
    token = connection_model.AnonymousConnection.all().get().token
    connection = connection_logic.queryAnonymousConnectionForToken(token)
    self.assertIsNotNone(connection)

class ActivateAnonymousConnectionTest(ConnectionTest):
  """Unit test for actions related to the activateAnonymousConnection
  function."""

  def testInvalidToken(self):
     """Test that the function will raise an error if the token does not
     correspond to an AnonymousConnection object."""
     token = "bad_token"
     self.assertRaises(
         ValueError,
         connection_logic.activateAnonymousConnection,
         profile=self.profile,
         token=token
         )

  def testExpiredConnection(self):
    """Test that a user is prevented from activating a Connection that was
    created more than a week ago."""
    connection_logic.createAnonymousConnection(
        org=self.org, org_role=connection_model.ORG_ADMIN_ROLE)
    # Cause the anonymous connection to "expire."
    anonymous_connection = connection_model.AnonymousConnection.all().get()
    anonymous_connection.expiration_date = datetime.today() - timedelta(1)
    anonymous_connection.put()

    self.assertRaises(
         ValueError,
         connection_logic.activateAnonymousConnection,
         profile=self.profile,
         token=anonymous_connection.token
         )

  def testSuccessfulActivation(self):
    """Test that given a valid token and date, an AnonymousConnection will be
    used to activate a new Connection for the user."""
    self.connection.delete()
    connection_logic.createAnonymousConnection(
        org=self.org, org_role=connection_model.ORG_ADMIN_ROLE)
    anonymous_connection = connection_model.AnonymousConnection.all().get()

    connection_logic.activateAnonymousConnection(profile=self.profile,
        token=anonymous_connection.token)
    query = connection_model.Connection.all().ancestor(self.profile)
    query.filter('org_role =', connection_model.ORG_ADMIN_ROLE)
    connection = query.get()

    self.assertEquals(connection.user_role, connection_model.NO_ROLE)
    self.assertEquals(connection.organization.key(), self.org.key())
    anonymous_connection = connection_model.AnonymousConnection.all().get()
    self.assertIsNone(anonymous_connection)
