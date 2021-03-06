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

from datetime import datetime
from datetime import timedelta
import mock
import unittest

from melange.logic import connection as connection_logic
from melange.models import connection as connection_model

from tests import org_utils
from tests import profile_utils
from tests import program_utils
from tests import timeline_utils
from tests.utils import connection_utils


TEST_MESSAGE_CONTENT = 'Test Message Content'

class ConnectionExistsTest(unittest.TestCase):
  """Unit tests for the connectionExists function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.program = program_utils.seedProgram()
    self.profile = profile_utils.seedNDBProfile(self.program.key())
    self.org = org_utils.seedOrganization(self.program.key())

  def testConnectionExists(self):
    """Tests that True is returned if connection does exist."""
    # seed a connection
    connection_utils.seed_new_connection(self.profile.key, self.org.key)
    self.assertTrue(
      connection_logic.connectionExists(self.profile.key, self.org.key))

  def testConnectionDoesNotExist(self):
    """Tests that False is returned if connection does not exist."""
    # seed a connection between the org and another profile
    other_profile = profile_utils.seedNDBProfile(self.program.key())
    connection_utils.seed_new_connection(other_profile.key, self.org.key)

    # seed a connection between the profile and another org
    other_org = org_utils.seedOrganization(self.program.key())
    connection_utils.seed_new_connection(self.profile.key, other_org.key)

    self.assertFalse(
      connection_logic.connectionExists(self.profile.key, self.org.key))


class ConnectionForProfileAndOrganizationTest(unittest.TestCase):
  """Unit tests for the connectionForProfileAndOrganization function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.program = program_utils.seedProgram()
    self.profile = profile_utils.seedNDBProfile(self.program.key())
    self.org = org_utils.seedOrganization(self.program.key())

  def testConnectionExists(self):
    """Tests that connection is returned if it exists."""
    # seed a connection
    connection = connection_utils.seed_new_connection(
        self.profile.key, self.org.key)
    self.assertEqual(
        connection_logic.connectionForProfileAndOrganization(
            self.profile.key, self.org.key), connection)

  def testConnectionDoesNotExist(self):
    """Tests that None is returned if connection does not exist."""
    # seed a connection between the org and another profile
    other_profile = profile_utils.seedNDBProfile(self.program.key())
    connection_utils.seed_new_connection(other_profile.key, self.org.key)

    # seed a connection between the profile and another org
    other_org = org_utils.seedOrganization(self.program.key())
    connection_utils.seed_new_connection(self.profile.key, other_org.key)

    self.assertIsNone(
        connection_logic.connectionForProfileAndOrganization(
            self.profile.key, self.org.key))


class CreateConnectionTest(unittest.TestCase):
  """Unit tests for the createConnection function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    program = program_utils.seedProgram()
    self.profile = profile_utils.seedNDBProfile(program.key())
    self.org = org_utils.seedOrganization(program.key())

  def testCreateConnection(self):
    """Tests that a connection object can be created successfully."""
    connection_logic.createConnection(
        self.profile, self.org.key, connection_model.NO_ROLE,
        connection_model.MENTOR_ROLE)

    # check that connection is created and persisted
    connection = connection_model.Connection.query(
        connection_model.Connection.organization == self.org.key,
        ancestor=self.profile.key).get()
    self.assertIsNotNone(connection)
    self.assertEqual(connection_model.NO_ROLE, connection.user_role)
    self.assertEqual(connection_model.MENTOR_ROLE, connection.org_role)

    # also test to ensure that a connection will not be created
    # if one already exists
    with self.assertRaises(ValueError):
      connection_logic.createConnection(
          self.profile, self.org.key,
          connection_model.NO_ROLE, connection_model.NO_ROLE)


class CreateConnectionMessageTest(unittest.TestCase):
  """Unit tests for the createConnectionMessage function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    program = program_utils.seedProgram()
    self.profile = profile_utils.seedNDBProfile(program.key())
    org = org_utils.seedOrganization(program.key())
    self.connection = connection_utils.seed_new_connection(
        self.profile.key, org.key)

  def testCreateMessageWithAuthor(self):
    """Tests that a message with an author is created properly."""
    message = connection_logic.createConnectionMessage(
        self.connection.key, TEST_MESSAGE_CONTENT,
        author_key=self.profile.key)

    self.assertIsNotNone(message)
    self.assertEqual(message.key.parent(), self.connection.key)
    self.assertEqual(message.content, TEST_MESSAGE_CONTENT)
    self.assertEqual(message.author, self.profile.key)
    self.assertFalse(message.is_auto_generated)

  def testCreateAutogeneratedMessage(self):
    """Tests that a message with no author is created properly."""
    message = connection_logic.createConnectionMessage(
        self.connection.key, TEST_MESSAGE_CONTENT)

    self.assertIsNotNone(message)
    self.assertEqual(message.key.parent(), self.connection.key)
    self.assertEqual(message.content, TEST_MESSAGE_CONTENT)
    self.assertIsNone(message.author)
    self.assertTrue(message.is_auto_generated)


class GetConnectionMessagesTest(unittest.TestCase):
  """Unit tests for the getConnectionMessages function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.program = program_utils.seedProgram()
    self.profile = profile_utils.seedNDBProfile(self.program.key())
    org = org_utils.seedOrganization(self.program.key())
    self.connection = connection_utils.seed_new_connection(
        self.profile.key, org.key)

  def testCorrectMessagesReturned(self):
    """Tests that correct messages are returned."""
    # seed a couple of messages for the connection
    message1 = connection_utils.seed_new_connection_message(
        self.connection.key, author=self.profile.key)
    message2 = connection_utils.seed_new_connection_message(self.connection.key)

    # seed another organization and a connection
    other_org = org_utils.seedOrganization(self.program.key())
    other_connection = connection_utils.seed_new_connection(
      self.profile.key, other_org.key)

    # create a few messages for the other connection
    for _ in range(4):
      connection_utils.seed_new_connection_message(
          other_connection.key, author=self.profile.key)

    # check that only correct messages are returned
    messages = connection_logic.getConnectionMessages(self.connection.key)
    expected_keys = set([message1.key, message2.key])
    actual_keys = set([message.key for message in messages])
    self.assertEqual(actual_keys, expected_keys)

  def testMessagesOrdered(self):
    """Tests that the returned messages are ordered by creation date."""
    # seed a couple of messages for the connection
    message1 = connection_utils.seed_new_connection_message(
        self.connection.key, created=datetime.now())
    message2 = connection_utils.seed_new_connection_message(
        self.connection.key, created=timeline_utils.past(delta=100))
    message3 = connection_utils.seed_new_connection_message(
        self.connection.key, created=timeline_utils.past(delta=50))

    messages = connection_logic.getConnectionMessages(self.connection.key)
    self.assertListEqual([message2, message3, message1], messages)


class QueryForAncestorTest(unittest.TestCase):
  """Unit tests for queryForAncestor function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.program = program_utils.seedProgram()
    # seed a few organizations
    self.first_org = org_utils.seedOrganization(self.program.key())
    self.second_org = org_utils.seedOrganization(self.program.key())
    self.third_org = org_utils.seedOrganization(self.program.key())

    # seed a few profiles
    self.profile = profile_utils.seedNDBProfile(self.program.key())
    self.other_profile = profile_utils.seedNDBProfile(self.program.key())

    self.first_connection = connection_utils.seed_new_connection(
        self.profile.key, self.first_org.key)
    self.second_connection = connection_utils.seed_new_connection(
        self.other_profile.key, self.first_org.key)
    self.third_connection = connection_utils.seed_new_connection(
        self.profile.key, self.second_org.key)

  def testForAncestor(self):
    """Tests that proper connections are returned."""
    query = connection_logic.queryForAncestor(self.profile.key)
    # exhaust the query to check what entities are fetched
    connections = query.fetch(1000)
    self.assertSetEqual(
        set(connection.key for connection in connections),
        set([self.first_connection.key, self.third_connection.key]))

    query = connection_logic.queryForAncestor(self.other_profile.key)
    # exhaust the query to check what entities are fetched
    connections = query.fetch(1000)
    self.assertSetEqual(
        set(connection.key for connection in connections),
        set([self.second_connection.key]))

    third_profile = profile_utils.seedNDBProfile(self.program.key())
    query = connection_logic.queryForAncestor(third_profile.key)
    # exhaust the query to check what entities are fetched
    connections = query.fetch(1000)
    self.assertSetEqual(set(connections), set())


class QueryForOrganizationsTest(unittest.TestCase):
  """Unit tests for queryForOrganizations function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    program = program_utils.seedProgram()
    # seed a few organizations
    self.first_org = org_utils.seedOrganization(program.key())
    self.second_org = org_utils.seedOrganization(program.key())
    self.third_org = org_utils.seedOrganization(program.key())

    # seed a few profiles
    first_profile = profile_utils.seedNDBProfile(program.key())
    second_profile = profile_utils.seedNDBProfile(program.key())

    self.first_connection = connection_utils.seed_new_connection(
        first_profile.key, self.first_org.key)
    self.second_connection = connection_utils.seed_new_connection(
        second_profile.key, self.first_org.key)
    self.third_connection = connection_utils.seed_new_connection(
        first_profile.key, self.second_org.key)

  def testForEmptyList(self):
    """Tests that an error is raised for an empty list of organizations."""
    with self.assertRaises(ValueError):
      connection_logic.queryForOrganizations([])

  def testForListOfOrgs(self):
    """Tests that proper connections are returned."""
    query = connection_logic.queryForOrganizations([self.first_org.key])
    # exhaust the query to check what entities are fetched
    connections = query.fetch(1000)
    self.assertSetEqual(
        set(connection.key for connection in connections),
        set([self.first_connection.key, self.second_connection.key]))

    query = connection_logic.queryForOrganizations([self.second_org.key])
    # exhaust the query to check what entities are fetched
    connections = query.fetch(1000)
    self.assertSetEqual(
        set(connection.key for connection in connections),
        set([self.third_connection.key]))

    query = connection_logic.queryForOrganizations([self.third_org.key])
    # exhaust the query to check what entities are fetched
    connections = query.fetch(1000)
    self.assertSetEqual(
        set(connection.key for connection in connections), set())

    query = connection_logic.queryForOrganizations(
        [self.first_org.key, self.second_org.key, self.third_org.key])
    # exhaust the query to check what entities are fetched
    connections = query.fetch(1000)
    self.assertSetEqual(
        set(connection.key for connection in connections),
        set([self.first_connection.key, self.second_connection.key,
            self.third_connection.key]))

class CanCreateConnectionTest(unittest.TestCase):
  """Unit tests for canCreateConnection function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    program = program_utils.seedProgram()
    self.profile = profile_utils.seedNDBProfile(program.key())
    self.org = org_utils.seedOrganization(program.key())

  def testForStudent(self):
    """Tests that a student profile cannot create a connection."""
    # make the profile a student
    self.profile.student_data = profile_utils.seedStudentData()

    result = connection_logic.canCreateConnection(self.profile, self.org.key)
    self.assertFalse(result)
    self.assertEqual(
        result.extra,
        connection_logic._PROFILE_IS_STUDENT % self.profile.profile_id)

  @mock.patch.object(connection_logic, 'connectionExists', return_value=True)
  def testForExistingConnection(self, mock_func):
    """Tests that a non-student profile with connection cannot create one."""
    result = connection_logic.canCreateConnection(self.profile, self.org.key)
    self.assertFalse(result)
    self.assertEqual(
        result.extra, connection_logic._CONNECTION_EXISTS % (
            self.profile.profile_id, self.org.key.id()))

  def testForNonExistingConnection(self):
    """Tests that a non-student profile with no connection can create one."""
    result = connection_logic.canCreateConnection(self.profile, self.org.key)
    self.assertTrue(result)


class GenerateMessageOnStartByUserTest(unittest.TestCase):
  """Unit tests for generateMessageOnStartByUser function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    program = program_utils.seedProgram()
    profile = profile_utils.seedNDBProfile(program.key())
    org = org_utils.seedOrganization(program.key())
    self.connection = connection_utils.seed_new_connection(profile.key, org.key)

  def testMessageIsCreated(self):
    """Tests that correct message is returned by the function."""
    message = connection_logic.generateMessageOnStartByUser(self.connection.key)

    self.assertEqual(message.key.parent(), self.connection.key)
    self.assertEqual(message.content, connection_logic._USER_STARTED_CONNECTION)
    self.assertTrue(message.is_auto_generated)


class GenerateMessageOnStartByOrgTest(unittest.TestCase):
  """Unit tests for generateMessageOnStartByOrg function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    program = program_utils.seedProgram()
    profile = profile_utils.seedNDBProfile(program.key())
    org = org_utils.seedOrganization(program.key())
    self.connection = connection_utils.seed_new_connection(profile.key, org.key)
    self.org_admin = profile_utils.seedNDBProfile(
        program.key(), admin_for=[org.key])

  def testMessageIsCreated(self):
    """Tests that correct message is returned by the function."""
    message = connection_logic.generateMessageOnStartByOrg(
        self.connection, self.org_admin)

    self.assertEqual(message.key.parent(), self.connection.key)
    self.assertEqual(
        message.content, connection_logic._ORG_STARTED_CONNECTION % (
            self.org_admin.public_name,
            connection_model.VERBOSE_ROLE_NAMES[self.connection.org_role]))
    self.assertTrue(message.is_auto_generated)

class CreateAnonymousConnectionTest(unittest.TestCase):
  """Unit test for createAnonymousConnection function."""

  def testCreateAnonymousConnection(self):
    """Test that an AnonymousConnection can be created successfully."""
    program = program_utils.seedProgram()
    org = org_utils.seedSOCOrganization(program.key())

    connection_logic.createAnonymousConnection(org=org,
        org_role=connection_model.MENTOR_ROLE, email='person@test.com')
    expected_expiration = datetime.today() + timedelta(7)

    connection = connection_model.AnonymousConnection.all().get()
    self.assertEquals(expected_expiration.date(),
        connection.expiration_date.date())
    self.assertEquals(connection_model.MENTOR_ROLE, connection.org_role)
    self.assertEquals('person@test.com', connection.email)


class QueryAnonymousConnectionTest(unittest.TestCase):
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
    program = program_utils.seedProgram()
    org = org_utils.seedOrganization(program.key())

    connection_logic.createAnonymousConnection(org=org,
        org_role=connection_model.MENTOR_ROLE, email='person@test.com')
    token = connection_model.AnonymousConnection.all().get().token
    connection = connection_logic.queryAnonymousConnectionForToken(token)
    self.assertIsNotNone(connection)

class ActivateAnonymousConnectionTest(unittest.TestCase):
  """Unit test for actions related to the activateAnonymousConnection
  function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.program = program_utils.seedProgram()

  def testInvalidToken(self):
    """Test that the function will raise an error if the token does not
    correspond to an AnonymousConnection object."""
    profile = profile_utils.seedNDBProfile(self.program.key())
    with self.assertRaises(ValueError):
      connection_logic.activateAnonymousConnection(profile, 'bad token')

  def testExpiredConnection(self):
    """Test that a user is prevented from activating a Connection that was
    created more than a week ago."""
    org = org_utils.seedOrganization(self.program.key())
    profile = profile_utils.seedNDBProfile(self.program.key())

    connection_logic.createAnonymousConnection(
        org=org, org_role=connection_model.ORG_ADMIN_ROLE,
        email='test@example.com')
    # Cause the anonymous connection to "expire."
    anonymous_connection = connection_model.AnonymousConnection.all().get()
    anonymous_connection.expiration_date = datetime.today() - timedelta(1)
    anonymous_connection.put()

    with self.assertRaises(ValueError):
      connection_logic.activateAnonymousConnection(profile, 'bad token')

  def testSuccessfulActivation(self):
    """Test that given a valid token and date, an AnonymousConnection will be
    used to activate a new Connection for the user."""
    org = org_utils.seedOrganization(self.program.key())
    profile = profile_utils.seedNDBProfile(self.program.key())

    connection_logic.createAnonymousConnection(
        'test@example.com', org, connection_model.ORG_ADMIN_ROLE)

    anonymous_connection = connection_model.AnonymousConnection.all().get()

    connection_logic.activateAnonymousConnection(
        profile, anonymous_connection.token)

    query = connection_model.Connection.query(
        connection_model.Connection.org_role == connection_model.ORG_ADMIN_ROLE,
        ancestor=profile.key)
    connection = query.get()

    self.assertEquals(connection.user_role, connection_model.NO_ROLE)
    self.assertEquals(connection.organization, org.key)

    anonymous_connection = connection_model.AnonymousConnection.all().get()
    self.assertIsNone(anonymous_connection)
