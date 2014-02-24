# Copyright 2014 the Melange authors.
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

"""Unit tests for connection related views."""

import mock
import unittest

from soc.modules.gsoc.views.helper import request_data

from melange.logic import connection as connection_logic
from melange.models import connection as connection_model
from melange.models import organization as org_model
from melange.request import access
from melange.request import exception
from melange.views import connection as connection_view

from summerofcode.views import connection as soc_connection_view
from summerofcode.views.helper import urls

from tests import org_utils
from tests import profile_utils
from tests import program_utils
from tests import test_utils
from tests.utils import connection_utils


_TEST_MESSAGE_CONTENT = 'Test message content'

def _getStartAsOrgUrl(org):
  """Returns URL to 'Start Connection As Organization' page for
  the specified organization.

  Args:
    org: Organization entity.

  Returns:
    The URL to 'Start Connection As Organization' page.
  """
  return '/gsoc/connection/start/org/%s' % org.key.id()


def _getStartAsUserUrl(org):
  """Returns URL to 'Start Connection As User' page for
  the specified organization.

  Args:
    org: Organization entity.

  Returns:
    The URL to 'Start Connection As Organization' page.
  """
  return '/gsoc/connection/start/user/%s' % org.key.id()


def _getManageAsUserUrl(connection):
  """Returns URL to 'Manage Connection As User' page for the specified
  connection entity.

  Args:
    connection: connection entity.

  Returns:
    The URL to 'Manage Connection As User' for the specified connection.
  """
  return '/gsoc/connection/manage/user/%s/%s' % (
      connection.key.parent().id(), connection.key.id())


def _getListConnectionsForOrgAdminUrl(profile):
  """Returns URL to 'List Connections For Org Admin' page for the specified
  profile entity.

  Args:
    profile: profile entity.

  Returns:
    The URL to 'List Connection For Org Admin' for the specified profile.
  """
  return '/gsoc/connection/list/org/%s' % profile.key.id()


def _getListForUserUrl(program):
  """Returns URL to 'List Connections For User' page for the specified user.

  Args:
    program: Program entity.

  Returns:
    URL to 'List Connections For User' page.
  """
  return '/gsoc/connection/list/user/%s' % program.key().name()


def _getPickOrganizationToConnectUrl(program):
  """Returns URL to 'Pick Organization To Connect' page for the specified user.

  Args:
    program: Program entity.

  Returns:
    URL to 'List Connections For User' page.
  """
  return '/gsoc/connection/pick/%s' % program.key().name()


def _getManageAsOrgUrl(connection):
  """Returns URL to 'Manage Connection As Org' page for the specified
  connection entity.

  Args:
    connection: connection entity.

  Returns:
    The URL to 'Manage Connection As Org' for the specified connection.
  """
  return '/gsoc/connection/manage/org/%s/%s' % (
      connection.key.parent().id(), connection.key.id())


def _getMarkAsSeenByOrgUrl(connection):
  """Returns URL to 'Mark Connection As Seen By Org' handler for the specified
  connection entity.

  Args:
    connection: connection entity.

  Returns:
    The URL to 'Mark Connection As Seen By Org' for the specified connection.
  """
  return '/gsoc/connection/mark_as_seen/org/%s/%s' % (
      connection.key.parent().id(), connection.key.id())


def _getMarkAsSeenByUserUrl(connection):
  """Returns URL to 'Mark Connection As Seen By User' handler for the specified
  connection entity.

  Args:
    connection: connection entity.

  Returns:
    The URL to 'Mark Connection As Seen By User' for the specified connection.
  """
  return '/gci/connection/mark_as_seen/user/%s/%s' % (
      connection.key.parent().id(), connection.key.id())


class NoConnectionExistsAccessCheckerTest(unittest.TestCase):
  """Unit tests for NoConnectionExistsAccessChecker class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    sponsor = program_utils.seedSponsor()
    program = program_utils.seedGSoCProgram(sponsor_key=sponsor.key())
    self.organization = org_utils.seedSOCOrganization(program.key())

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    self.profile = profile_utils.seedNDBProfile(program.key(), user=user)

    kwargs = {
        'sponsor': sponsor.key().name(),
        'program': program.program_id,
        'organization': self.organization.org_id,
        }
    self.data = request_data.RequestData(None, None, kwargs)

  def testNoConnectionExists(self):
    """Tests that access is granted if no connection exists."""
    access_checker = (
        connection_view.NoConnectionExistsAccessChecker(urls.UrlNames))
    access_checker.checkAccess(self.data, None)

  def testConnectionExists(self):
    """Tests that access is denied if connection already exists."""
    # seed a connection between the profile and organization
    connection_utils.seed_new_connection(
        self.profile.key, self.organization.key)

    access_checker = (
        connection_view.NoConnectionExistsAccessChecker(urls.UrlNames))
    with self.assertRaises(exception.Redirect):
      access_checker.checkAccess(self.data, None)


class StartConnectionAsOrgTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for StartConnectionAsOrg class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()
    self.org.status = org_model.Status.ACCEPTED
    self.org.put()

  def _assertPageTemplatesUsed(self, response):
    """Asserts that all templates for the tested page are used."""
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/form_base.html')

  def testPageLoads(self):
    """Tests that page loads properly."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[self.org.key])

    response = self.get(_getStartAsOrgUrl(self.org))
    self.assertResponseOK(response)
    self._assertPageTemplatesUsed(response)

  def testConnectionStartedForNonStudent(self):
    """Tests that connection is created successfully for non-students."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile = profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[self.org.key])

    first_profile = profile_utils.seedNDBProfile(self.program.key())
    second_profile = profile_utils.seedNDBProfile(self.program.key())

    post_data = {
        'role': connection_model.MENTOR_ROLE,
        'users': '%s, %s' % (
            first_profile.profile_id, second_profile.profile_id)
        }
    response = self.post(_getStartAsOrgUrl(self.org), post_data)
    self.assertResponseRedirect(
        response, _getListConnectionsForOrgAdminUrl(profile))

    # check that connection with the first profile is created
    connection = connection_model.Connection.query(
        connection_model.Connection.organization == self.org.key,
        ancestor=first_profile.key).get()
    self.assertIsNotNone(connection)
    self.assertEqual(connection.org_role, connection_model.MENTOR_ROLE)
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)

    # check that auto-generated message is created
    message = connection_model.ConnectionMessage.query(
        ancestor=connection.key).get()
    self.assertIsNotNone(message)
    self.assertTrue(message.is_auto_generated)
    self.assertEqual(
        message.content,
        connection_logic._ORG_STARTED_CONNECTION % (
            profile.public_name,
            connection_model.VERBOSE_ROLE_NAMES[connection_model.MENTOR_ROLE]))

    # check that an email to the user has been sent
    self.assertEmailSent(to=first_profile.contact.email)

    # check that connection with the second profile is created
    connection = connection_model.Connection.query(
        connection_model.Connection.organization == self.org.key,
        ancestor=second_profile.key).get()
    self.assertIsNotNone(connection)
    self.assertEqual(connection.org_role, connection_model.MENTOR_ROLE)
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)

    # check that an email to the user has been sent
    self.assertEmailSent(to=second_profile.contact.email)

  def testConnectionNotStartedForStudent(self):
    """Tests that connection is not created for a student."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[self.org.key])

    profile = profile_utils.seedNDBStudent(self.program)

    post_data = {
        'role': connection_model.MENTOR_ROLE,
        'users': '%s' % profile.profile_id
        }
    response = self.post(_getStartAsOrgUrl(self.org), post_data)
    self.assertResponseBadRequest(response)

    # check that no connection has been created
    connection = connection_model.Connection.query(
        connection_model.Connection.organization == self.org.key,
        ancestor=profile.key).get()
    self.assertIsNone(connection)


class StartConnectionAsUserTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for ShowConnectionAsUser class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()
    self.org.status = org_model.Status.ACCEPTED
    self.org.put()

  def testConnectionExists(self):
    """Tests that exception is raised when connection already exists."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile = profile_utils.seedNDBProfile(self.program.key(), user=user)
    connection = connection_utils.seed_new_connection(profile.key, self.org.key)

    # check that user is redirected when a connection exists
    response = self.get(_getStartAsUserUrl(self.org))
    self.assertResponseRedirect(response, _getManageAsUserUrl(connection))

    # check that bad request is raised when a connection already exists
    # on POST request after access checker concludes
    with mock.patch.object(
        soc_connection_view.START_CONNECTION_AS_USER, 'access_checker',
        new=access.ALL_ALLOWED_ACCESS_CHECKER):
      response = self.post(_getStartAsUserUrl(self.org))
      self.assertResponseBadRequest(response)

  def testStudentProfile(self):
    """Tests that exception is raised when student profile starts connection."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBStudent(self.program, user=user)

    # check that user is forbidden to access the page
    response = self.get(_getStartAsUserUrl(self.org))
    self.assertResponseForbidden(response)

    # check that bad request is raised on POST request
    # even when access checker gets through
    with mock.patch.object(
        soc_connection_view.START_CONNECTION_AS_USER, 'access_checker',
        new=access.ALL_ALLOWED_ACCESS_CHECKER):
      response = self.post(_getStartAsUserUrl(self.org))
      self.assertResponseBadRequest(response)

  def testNonStudentProfile(self):
    """Tests that connection is created for a non-student profile."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile = profile_utils.seedNDBProfile(self.program.key(), user=user)

    # seed an admin for the organization
    org_admin = profile_utils.seedNDBProfile(
        self.program.key(), admin_for=[self.org.key])

    post_data = {'role': connection_model.ROLE}
    response = self.post(_getStartAsUserUrl(self.org), post_data)

    # check that a new connection is created
    connection = connection_model.Connection.query(
        connection_model.Connection.organization == self.org.key,
        ancestor=profile.key).get()
    self.assertIsNotNone(connection)
    self.assertEqual(connection.org_role, connection_model.NO_ROLE)
    self.assertEqual(connection.user_role, connection_model.ROLE)

    # check that auto-generated message is created
    message = connection_model.ConnectionMessage.query(
        ancestor=connection.key).get()
    self.assertIsNotNone(message)
    self.assertTrue(message.is_auto_generated)
    self.assertEqual(
        message.content,
        connection_logic._USER_STARTED_CONNECTION)

    # check that a message has been sent to the organization admin
    self.assertEmailSent(to=org_admin.contact.email)

    # check that the user is redirected to 'Manage Connection' page
    self.assertResponseRedirect(response, _getManageAsUserUrl(connection))


class ManageConnectionAsOrgTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for ManageConnectionAsOrg class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

    # seed a profile for a connected user
    profile = profile_utils.seedNDBProfile(self.program.key())

    self.connection = connection_utils.seed_new_connection(
        profile.key, self.org.key)

  def testPageLoads(self):
    """Tests that page loads properly."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[self.org.key])

    response = self.get(_getManageAsOrgUrl(self.connection))
    self.assertResponseOK(response)

  def testSendNewMessage(self):
    """Tests that sending a new connection message works."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile = profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[self.org.key])

    last_modified = self.connection.last_modified

    post_data = {
        connection_view.MESSAGE_FORM_NAME: '',
        'content': _TEST_MESSAGE_CONTENT,
        }
    response = self.post(_getManageAsOrgUrl(self.connection), post_data)
    self.assertResponseRedirect(response, _getManageAsOrgUrl(self.connection))

    # check that a new message is created
    query = connection_model.ConnectionMessage.query(
        ancestor=self.connection.key)
    message = query.get()
    self.assertIsNotNone(message)
    self.assertEqual(message.content, _TEST_MESSAGE_CONTENT)
    self.assertFalse(message.is_auto_generated)
    self.assertEqual(message.author, profile.key)

    # check that last_modified property is updated
    self.assertGreater(self.connection.key.get().last_modified, last_modified)


class ManageConnectionAsUserTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for ManageConnectionAsUser class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile = profile_utils.seedNDBProfile(self.program.key(), user=user)
    self.connection = connection_utils.seed_new_connection(
        profile.key, self.org.key)

  def testPageLoads(self):
    """Tests that page loads properly."""
    response = self.get(_getManageAsUserUrl(self.connection))
    self.assertResponseOK(response)

  def testSendNewMessage(self):
    """Tests that sending a new connection message works."""
    last_modified = self.connection.last_modified

    post_data = {
        connection_view.MESSAGE_FORM_NAME: '',
        'content': _TEST_MESSAGE_CONTENT,
        }
    response = self.post(_getManageAsUserUrl(self.connection), post_data)
    self.assertResponseRedirect(response, _getManageAsUserUrl(self.connection))

    # check that a new message is created
    query = connection_model.ConnectionMessage.query(
        ancestor=self.connection.key)
    message = query.get()
    self.assertIsNotNone(message)
    self.assertEqual(message.content, _TEST_MESSAGE_CONTENT)
    self.assertFalse(message.is_auto_generated)
    self.assertEqual(message.author, self.connection.key.parent())

    # check that last_modified property is updated
    self.assertGreater(self.connection.key.get().last_modified, last_modified)


class ListConnectionsForUserTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for ListConnectionsForUser class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

  def _assertPageTemplatesUsed(self, response):
    """Asserts that all templates for the tested page are used."""
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response,
        'summerofcode/connection/connection_list.html')
    self.assertTemplateUsed(response,
        'summerofcode/_list_component.html')

  def testPageLoads(self):
    """Tests that page loads properly."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(self.program.key(), user=user)

    response = self.get(_getListForUserUrl(self.program))
    self.assertResponseOK(response)
    self._assertPageTemplatesUsed(response)

  def testListData(self):
    """Tests that correct list data is loaded."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile = profile_utils.seedNDBProfile(self.program.key(), user=user)

    first_org = org_utils.seedSOCOrganization(
        self.program.key(), status=org_model.Status.ACCEPTED)
    connection_utils.seed_new_connection(profile.key, first_org.key)

    other_org = org_utils.seedSOCOrganization(
        self.program.key(), status=org_model.Status.ACCEPTED)
    connection_utils.seed_new_connection(profile.key, other_org.key)

    list_data = self.getListData(_getListForUserUrl(self.program), 0)

    # check that all two connections are listed
    self.assertEqual(len(list_data), 2)


class PickOrganizationToConnectPageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for PickOrganizationToConnectPage class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

  def testPageLoads(self):
    """Tests that the page loads properly."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(self.program.key(), user=user)

    response = self.get(_getPickOrganizationToConnectUrl(self.program))
    self.assertResponseOK(response)

  def testListDataLoads(self):
    """Tests that the list data loads properly."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(self.program.key(), user=user)

    # the org is already accepted
    self.org.status = org_model.Status.ACCEPTED
    self.org.put()

    list_data = self.getListData(
        _getPickOrganizationToConnectUrl(self.program), 0)

    # check that the organization is listed
    self.assertEqual(len(list_data), 1)


_NUMBER_OF_CONNECTIONS_FOR_MAIN_ORG = 3
_NUMBER_OF_CONNECTIONS_FOR_SECOND_ORG = 2
_NUMBER_OF_CONNECTIONS_FOR_THIRD_ORG = 5

class OrgAdminConnectionListTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for OrgAdminConnectionList class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

  def testPageLoads(self):
    """Tests that page loads properly."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile = profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[self.org.key])

    url = _getListConnectionsForOrgAdminUrl(profile)
    response = self.get(url)
    self.assertResponseOK(response)

  def testListData(self):
    """Tests that all connections for orgs administrated by user are listed."""
    # seed another organization which is administrated by the user
    second_org = org_utils.seedSOCOrganization(self.program.key())

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile = profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        admin_for=[self.org.key, second_org.key])

    # seed a few connections for first organization
    for _ in range(_NUMBER_OF_CONNECTIONS_FOR_MAIN_ORG):
      other_profile = profile_utils.seedNDBProfile(self.program.key())
      connection_utils.seed_new_connection(other_profile.key, self.org.key)

    for _ in range(_NUMBER_OF_CONNECTIONS_FOR_SECOND_ORG):
      other_profile = profile_utils.seedNDBProfile(self.program.key())
      connection_utils.seed_new_connection(other_profile.key, second_org.key)

    # seed another organization which is not administrated by the user
    third_org = org_utils.seedSOCOrganization(self.program.key())

    # seed a few connections for the other organization
    for _ in range(_NUMBER_OF_CONNECTIONS_FOR_THIRD_ORG):
      other_profile = profile_utils.seedNDBProfile(self.program.key())
      connection_utils.seed_new_connection(other_profile.key, third_org.key)

    list_data = self.getListData(
        _getListConnectionsForOrgAdminUrl(profile), 0)

    # check that all connections are listed: the ones created above for the main
    # org and the second plus two for the organization admin itself
    self.assertEqual(
        len(list_data),
        _NUMBER_OF_CONNECTIONS_FOR_MAIN_ORG +
        _NUMBER_OF_CONNECTIONS_FOR_SECOND_ORG + 2)


class MarkConnectionAsSeenByOrgTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for MarkConnectionAsSeenByOrg class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

    # seed another profile for a connected user
    other_profile = profile_utils.seedNDBProfile(self.program.key())
    self.connection = connection_utils.seed_new_connection(
        other_profile.key, self.org.key, seen_by_org=False)

  @unittest.skip(
      'This request should fail instead of raising NotImplementedError')
  def testGetMethodForbidden(self):
    """Tests that GET method is not permitted."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[self.org.key])

    response = self.get(_getMarkAsSeenByOrgUrl(self.connection))
    self.assertResponseForbidden(response)

  def testConnectionMarkedAsSeen(self):
    """Tests that connection is successfully marked as seen by organization."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[self.org.key])

    response = self.post(_getMarkAsSeenByOrgUrl(self.connection))
    self.assertResponseOK(response)

    # check that connection is marked as seen by organization
    connection = self.connection.key.get()
    self.assertTrue(connection.seen_by_org)
