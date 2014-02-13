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

import unittest

from soc.modules.gsoc.views.helper import request_data

from melange.logic import connection as connection_logic
from melange.models import connection as connection_model
from melange.request import exception
from melange.views import connection as connection_view

from summerofcode.views.helper import urls

from tests import org_utils
from tests import profile_utils
from tests import program_utils
from tests import test_utils
from tests.utils import connection_utils


def _getStartAsOrgUrl(org):
  """Returns URL to 'Start Connection As Organization' page for
  the specified organization.

  Args:
    org: Organization entity.

  Returns:
    The URL to 'Start Connection As Organization' page.
  """
  return '/gsoc/connection/start/org/%s' % org.key.id()


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


def _getListConnectionsForOrgAdminUrl(profile):
  """Returns URL to 'List Connections For Org Admin' page for the specified
  profile entity.

  Args:
    profile: profile entity.

  Returns:
    The URL to 'List Connection For Org Admin' for the specified profile.
  """
  return '/gsoc/connection/list/org/%s' % profile.key.id()


def _getMarkAsSeenByOrgUrl(connection):
  """Returns URL to 'Mark Connection As Seen By Org' handler for the specified
  connection entity.

  Args:
    connection: connection entity.

  Returns:
    The URL to 'Mark Connection As Seen By Org' for the specified connection.
  """
  return '/gci/connection/mark_as_seen/org/%s/%s' % (
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

  def _assertPageTemplatesUsed(self, response):
    """Asserts that all templates for the tested page are used."""
    self.assertGSoCTemplatesUsed(response)
    #self.assertTemplateUsed(
    #    response, 'codein/connection/start_connection_as_org.html')

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
    self.assertResponseRedirect(response, _getStartAsOrgUrl(self.org))

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
