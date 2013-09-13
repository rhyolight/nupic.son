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

"""Unit tests for connection related views."""

import mock
import unittest

from codein.logic import profile as profile_logic
from codein.views import connection as connection_view

from django import http

from google.appengine.ext import db

from melange.logic import connection as connection_logic
from melange.models import connection as connection_model
from melange.request import access
from melange.request import exception
from melange.utils import rich_bool

from soc.models import organization as org_model
from soc.models import profile as profile_model
from soc.models import user as user_model

from soc.modules.gci.views.helper import request_data
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests import profile_utils
from tests import test_utils
from tests.utils import connection_utils


def _getManageAsUserUrl(connection):
  """Returns URL to 'Manage Connection As User' page for the specified
  connection entity.

  Args:
    connection: connection entity.

  Returns:
    The URL to 'Manage Connection As User' for the specified connection.
  """
  return '/gci/connection/manage/user/%s/%s' % (
      connection.parent_key().name(), connection.key().id())


def _getManageAsOrgUrl(connection):
  """Returns URL to 'Manage Connection As Org' page for the specified
  connection entity.

  Args:
    connection: connection entity.

  Returns:
    The URL to 'Manage Connection As Org' for the specified connection.
  """
  return '/gci/connection/manage/org/%s/%s' % (
      connection.parent_key().name(), connection.key().id())


class NoConnectionExistsAccessCheckerTest(unittest.TestCase):
  """Unit tests for NoConnectionExistsAccessChecker class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.data = request_data.RequestData(None, None, None)

    user = seeder_logic.seed(user_model.User)
    self.data._url_profile = seeder_logic.seed(profile_model.Profile,
        {'parent': user})
    self.data._url_org = seeder_logic.seed(org_model.Organization)

  def testNoConnectionExists(self):
    """Tests that access is granted if no connection exists."""
    access_checker = connection_view.NoConnectionExistsAccessChecker()
    access_checker.checkAccess(self.data, None, None)

  def testConnectionExists(self):
    """Tests that access is denied if connection already exists."""
    connection_properties = {
        'parent': self.data._url_profile,
        'organization': self.data._url_org
        }
    seeder_logic.seed(connection_model.Connection, connection_properties)
    access_checker = connection_view.NoConnectionExistsAccessChecker()
    with self.assertRaises(exception.Redirect):
      access_checker.checkAccess(self.data, None, None)


class StartConnectionAsOrgTest(test_utils.GCIDjangoTestCase):
  """Unit tests for StartConnectionAsOrg class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

  def _getUrl(self, org):
    """Returns URL to 'start connection as organization' view for
    the specified organization.

    Args:
      org: organization entity.

    Returns:
      URL to 'start connection as organization' view.
    """
    return '/gci/connection/start/org/%s' % org.key().name()

  def _assertPageTemplatesUsed(self, response):
    """Asserts that all templates for the tested page are used."""
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(
        response, 'codein/connection/start_connection_as_org.html')

  def testPageLoads(self):
    """Tests that page loads properly."""
    self.profile_helper.createOrgAdmin(self.org)
    response = self.get(self._getUrl(self.org))
    self.assertResponseOK(response)
    self._assertPageTemplatesUsed(response)

  def testConnectionStarted(self):
    """Tests that connection is created successfully."""
    self.profile_helper.createOrgAdmin(self.org)

    profile_helper = profile_utils.GCIProfileHelper(
       self.program, False)
    profile_helper.createOtherUser('first@example.com')
    first_profile = profile_helper.createProfile()

    profile_helper = profile_utils.GCIProfileHelper(
       self.program, False)
    profile_helper.createOtherUser('second@example.com')
    second_profile = profile_helper.createProfile()

    post_data = {
        'role': connection_model.MENTOR_ROLE,
        'users': '%s, %s' % (first_profile.link_id, second_profile.link_id)
        }
    response = self.post(self._getUrl(self.org), post_data)
    self.assertResponseRedirect(response, self._getUrl(self.org))

    # check that connection with the first profile is created
    connection = connection_model.Connection.all().ancestor(
        first_profile.key()).filter('organization', self.org).get()
    self.assertIsNotNone(connection)
    self.assertEqual(connection.org_role, connection_model.MENTOR_ROLE)
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)

    # check that connection with the second profile is created
    connection = connection_model.Connection.all().ancestor(
        second_profile.key()).filter('organization', self.org).get()
    self.assertIsNotNone(connection)
    self.assertEqual(connection.org_role, connection_model.MENTOR_ROLE)
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)


class StartConnectionAsUserTest(test_utils.GCIDjangoTestCase):
  """Unit tests for ShowConnectionAsUser class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

  def _getUrl(self, profile, org):
    """Returns URL to 'start connection as user' view for the specified
    profile and organization.

    Args:
      profile: profile entity.
      org: organization entity.

    Returns:
      URL to 'start connection as user' view.
    """
    return '/gci/connection/start/user/%s/%s' % (
        profile.key().name(), org.link_id)

  def testStudentAccessDenied(self):
    """Tests that students cannot access the site."""
    profile = self.profile_helper.createStudent()
    url = self._getUrl(profile, self.org)
    response = self.get(url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testNonStudentAccessGranted(self):
    """Tests that a user with non-student profile can access the site."""
    profile = self.profile_helper.createProfile()
    url = self._getUrl(profile, self.org)
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertTemplateUsed(
        response, 'modules/gci/form_base.html')

  def testConnectionExists(self):
    """Tests that exception is raised when connection already exists."""
    profile = self.profile_helper.createProfile()

    # seed a connection between the user and organization
    connection_properties = {
        'parent': profile,
        'organization': self.org
        }
    connection = seeder_logic.seed(
        connection_model.Connection, properties=connection_properties)

    url = self._getUrl(profile, self.org)

    # check that user is redirected when a connection exists
    response = self.get(url)
    self.assertResponseRedirect(response, _getManageAsUserUrl(connection))

    # check that bad request is raised when a connection already exists
    # on POST request after access checker concludes
    with mock.patch.object(
        connection_view.StartConnectionAsUser, 'access_checker',
        new=access.ALL_ALLOWED_ACCESS_CHECKER):
      response = self.post(url)
      self.assertResponseBadRequest(response)


class ManageConnectionAsOrgTest(test_utils.GCIDjangoTestCase):
  """Unit tests for ManageConnectionAsOrg class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

  def testPageLoads(self):
    """Tests that page loads properly."""
    self.profile_helper.createOrgAdmin(self.org)

    profile_helper = profile_utils.GCIProfileHelper(
       self.program, False)
    profile_helper.createOtherUser('other@example.com')
    other_profile = profile_helper.createProfile()

    connection = connection_utils.seed_new_connection(other_profile, self.org)

    response = self.get(_getManageAsOrgUrl(connection))
    self.assertResponseOK(response)


class UserActionsFormHandlerTest(test_utils.GCIDjangoTestCase):
  """Unit tests for UserActionsFormHandler class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

    # view used as a callback for handler
    self.view = connection_view.ManageConnectionAsUser()

  def testUserNoRoleToNoRoleWhileNoRoleOffered(self):
    """Tests NO ROLE if user has no role and no role is offered."""
    profile = self.profile_helper.createProfile()

    # no role is offered to the user; the user does not request any role
    connection = connection_utils.seed_new_connection(profile, self.org)

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }
    
    request = http.HttpRequest()
    # the user still does not request any role
    request.POST = {'user_role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.UserActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)
    self.assertEqual(connection.org_role, connection_model.NO_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertNotIn(self.org.key(), profile.mentor_for)

  def testUserNoRoleToNoRoleWhileMentorRoleOffered(self):
    """Tests NO ROLE if user has no role and mentor role is offered."""
    profile = self.profile_helper.createProfile()

    # mentor role is offered to the user; the user does not request any role
    connection = connection_utils.seed_new_connection(
    profile, self.org, org_role=connection_model.MENTOR_ROLE)

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }
    
    request = http.HttpRequest()
    # the user still does not request any role
    request.POST = {'user_role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.UserActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)
    self.assertEqual(connection.org_role, connection_model.MENTOR_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertNotIn(self.org.key(), profile.mentor_for)

  def testUserNoRoleToNoRoleWhileOrgAdminRoleOffered(self):
    """Tests NO ROLE if user has no role and org admin role is offered."""
    profile = self.profile_helper.createProfile()

    # org admin role is offered to the user; the user does not request any role
    connection = connection_utils.seed_new_connection(
    profile, self.org, org_role=connection_model.ORG_ADMIN_ROLE)

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }
    
    request = http.HttpRequest()
    # the user still does not request any role
    request.POST = {'user_role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.UserActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)
    self.assertEqual(connection.org_role, connection_model.ORG_ADMIN_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertNotIn(self.org.key(), profile.mentor_for)

  def testUserNoRoleToRoleWhileNoRoleOffered(self):
    """Tests ROLE if user has no role and no role is offered."""
    profile = self.profile_helper.createProfile()

    # no role is offered to the user; the user does not request any role
    connection = connection_utils.seed_new_connection(profile, self.org)

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }
    
    request = http.HttpRequest()
    # the user requests a role now
    request.POST = {'user_role': connection_model.ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.UserActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.NO_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertNotIn(self.org.key(), profile.mentor_for)

  def testUserNoRoleToRoleWhileMentorRoleOffered(self):
    """Tests ROLE if user has no role and mentor role is offered."""
    profile = self.profile_helper.createProfile()

    # mentor role is offered to the user; the user does not request any role
    connection = connection_utils.seed_new_connection(
        profile, self.org, org_role=connection_model.MENTOR_ROLE)

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }
    
    request = http.HttpRequest()
    # the user requests a role now
    request.POST = {'user_role': connection_model.ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.UserActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.MENTOR_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertIn(self.org.key(), profile.mentor_for)

  def testUserNoRoleToRoleWhileOrgAdminRoleOffered(self):
    """Tests ROLE if user has no role and org admin role is offered."""
    profile = self.profile_helper.createProfile()

    # org admin role is offered to the user; the user does not request any role
    connection = connection_utils.seed_new_connection(
        profile, self.org, org_role=connection_model.ORG_ADMIN_ROLE)

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }
    
    request = http.HttpRequest()
    # the user requests a role now
    request.POST = {'user_role': connection_model.ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.UserActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.ORG_ADMIN_ROLE)
    self.assertIn(self.org.key(), profile.org_admin_for)
    self.assertIn(self.org.key(), profile.mentor_for)

  def testUserRoleToRoleWhileNoRoleOffered(self):
    """Tests ROLE if user has role and no role is offered."""
    profile = self.profile_helper.createProfile()

    # no role is offered to the user; the user requests role
    connection = connection_utils.seed_new_connection(
        profile, self.org, user_role=connection_model.ROLE)

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }
    
    request = http.HttpRequest()
    # the user still requests a role
    request.POST = {'user_role': connection_model.ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.UserActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.NO_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertNotIn(self.org.key(), profile.mentor_for)

  def testUserRoleToRoleWhileMentorRoleOffered(self):
    """Tests ROLE if user has role and mentor role is offered."""
    # mentor role is offered to the user; the user requests role
    profile = self.profile_helper.createMentor(self.org)
    connection = connection_model.Connection.all().ancestor(
        profile).filter('organization', self.org).get()

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }
    
    request = http.HttpRequest()
    # the user still requests a role
    request.POST = {'user_role': connection_model.ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.UserActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.MENTOR_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertIn(self.org.key(), profile.mentor_for)

  def testUserRoleToRoleWhileOrgAdminRoleOffered(self):
    """Tests ROLE if user has role and org admin role is offered."""
    # org admin role is offered to the user; the user requests role
    profile = self.profile_helper.createOrgAdmin(self.org)
    connection = connection_model.Connection.all().ancestor(
        profile).filter('organization', self.org).get()

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }
    
    request = http.HttpRequest()
    # the user still requests a role
    request.POST = {'user_role': connection_model.ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.UserActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.ORG_ADMIN_ROLE)
    self.assertIn(self.org.key(), profile.org_admin_for)
    self.assertIn(self.org.key(), profile.mentor_for)

  def testUserRoleToNoRoleWhileNoRoleOffered(self):
    """Tests NO ROLE if user has role and no role is offered."""
    profile = self.profile_helper.createProfile()

    # no role is offered to the user; the user requests role
    connection = connection_utils.seed_new_connection(
        profile, self.org, user_role=connection_model.ROLE)

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }
    
    request = http.HttpRequest()
    # the user does not request role anymore
    request.POST = {'user_role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.UserActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)
    self.assertEqual(connection.org_role, connection_model.NO_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertNotIn(self.org.key(), profile.mentor_for)

  def testUserRoleToNoRoleWhileMentorRoleOffered(self):
    """Tests NO ROLE if user has role and mentor role is offered."""
    # mentor role is offered to the user; the user requests role
    profile = self.profile_helper.createMentor(self.org)
    connection = connection_model.Connection.all().ancestor(
        profile).filter('organization', self.org).get()

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }
    
    request = http.HttpRequest()
    # the user does not request role anymore
    request.POST = {'user_role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.UserActionsFormHandler(self.view)

    # assume that mentor is not eligible to quit
    with mock.patch.object(
        profile_logic, 'isNoRoleEligibleForOrg', return_value=rich_bool.FALSE):
      handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.MENTOR_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertIn(self.org.key(), profile.mentor_for)

    # try again but now, the user is eligible to quit
    request = http.HttpRequest()
    # the user does not request role anymore
    request.POST = {'user_role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.UserActionsFormHandler(self.view)

    # assume that mentor is eligible to quit
    with mock.patch.object(
        profile_logic, 'isNoRoleEligibleForOrg', return_value=rich_bool.TRUE):
      handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)
    self.assertEqual(connection.org_role, connection_model.MENTOR_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertNotIn(self.org.key(), profile.mentor_for)

  def testUserRoleToNoRoleWhileOrgAdminRoleOffered(self):
    """Tests NO ROLE if user has role and org admin role is offered."""
    # org admin role is offered to the user; the user requests role
    profile = self.profile_helper.createOrgAdmin(self.org)
    connection = connection_model.Connection.all().ancestor(
        profile).filter('organization', self.org).get()

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }
    
    request = http.HttpRequest()
    # the user does not request role anymore
    request.POST = {'user_role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.UserActionsFormHandler(self.view)

    # assume that mentor is not eligible to quit
    with mock.patch.object(
        profile_logic, 'isNoRoleEligibleForOrg', return_value=rich_bool.FALSE):
      handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.ORG_ADMIN_ROLE)
    self.assertIn(self.org.key(), profile.org_admin_for)
    self.assertIn(self.org.key(), profile.mentor_for)

    # try again but now, the user is eligible to quit
    request = http.HttpRequest()
    # the user does not request role anymore
    request.POST = {'user_role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.UserActionsFormHandler(self.view)

    # assume that mentor is eligible to quit
    with mock.patch.object(
        profile_logic, 'isNoRoleEligibleForOrg', return_value=rich_bool.TRUE):
      handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)
    self.assertEqual(connection.org_role, connection_model.ORG_ADMIN_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertNotIn(self.org.key(), profile.mentor_for)


class OrgActionsFormHandlerTest(test_utils.GCIDjangoTestCase):
  """Unit tests for OrgActionsFormHandler class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

    # view used as a callback for handler
    self.view = connection_view.ManageConnectionAsOrg()

  def testNoRoleToNoRoleWhileNoRoleRequested(self):
    """Tests NO ROLE if no role offered and user requests no role."""
    profile = self.profile_helper.createProfile()

    # user does not request any role from organization
    connection = connection_utils.seed_new_connection(profile, self.org)

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }

    request = http.HttpRequest()
    # no role is still offered 
    request.POST = {'role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.OrgActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)
    self.assertEqual(connection.org_role, connection_model.NO_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertNotIn(self.org.key(), profile.mentor_for)

  def testNoRoleToNoRoleWhileRoleRequested(self):
    """Tests NO ROLE if no role offered and user requests role."""
    profile = self.profile_helper.createProfile()

    # user requests role from organization
    connection = connection_utils.seed_new_connection(
        profile, self.org, user_role=connection_model.ROLE)

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }

    request = http.HttpRequest()
    # no role is still offered 
    request.POST = {'role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.OrgActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.NO_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertNotIn(self.org.key(), profile.mentor_for)

  def testNoRoleToMentorRoleWhileNoRoleRequested(self):
    """Tests MENTOR ROLE if no role offered and user requests no role."""
    profile = self.profile_helper.createProfile()

    # user does not request any role from organization
    connection = connection_utils.seed_new_connection(profile, self.org)

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }

    request = http.HttpRequest()
    # mentor role is offered now 
    request.POST = {'role': connection_model.MENTOR_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.OrgActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)
    self.assertEqual(connection.org_role, connection_model.MENTOR_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertNotIn(self.org.key(), profile.mentor_for)

  def testNoRoleToMentorRoleWhileRoleRequested(self):
    """Tests MENTOR ROLE if no role offered and user requests role."""
    profile = self.profile_helper.createProfile()

    # user requests role from organization
    connection = connection_utils.seed_new_connection(
        profile, self.org, user_role=connection_model.ROLE)

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }

    request = http.HttpRequest()
    # mentor role is offered now 
    request.POST = {'role': connection_model.MENTOR_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.OrgActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.MENTOR_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertIn(self.org.key(), profile.mentor_for)

  def testNoRoleToOrgAdminRoleWhileNoRoleRequested(self):
    """Tests ORG ADMIN ROLE if no role offered and user requests no role."""
    profile = self.profile_helper.createProfile()

    # user does not request any role from organization
    connection = connection_utils.seed_new_connection(profile, self.org)

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }

    request = http.HttpRequest()
    # org admin role is offered now 
    request.POST = {'role': connection_model.ORG_ADMIN_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.OrgActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)
    self.assertEqual(connection.org_role, connection_model.ORG_ADMIN_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertNotIn(self.org.key(), profile.mentor_for)

  def testNoRoleToOrgAdminRoleWhileRoleRequested(self):
    """Tests ORG ADMIN ROLE if no role offered and user requests role."""
    profile = self.profile_helper.createProfile()

    # user requests role from organization
    connection = connection_utils.seed_new_connection(
        profile, self.org, user_role=connection_model.ROLE)

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }

    request = http.HttpRequest()
    # org admin role is offered now 
    request.POST = {'role': connection_model.ORG_ADMIN_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.OrgActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.ORG_ADMIN_ROLE)
    self.assertIn(self.org.key(), profile.org_admin_for)
    self.assertIn(self.org.key(), profile.mentor_for)

  def testMentorRoleToNoRoleWhileNoRoleRequested(self):
    """Tests NO ROLE if mentor role offered and user requests no role."""
    profile = self.profile_helper.createProfile()

    # user does not request any role from organization
    connection = connection_utils.seed_new_connection(
        profile, self.org, org_role=connection_model.MENTOR_ROLE)

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }

    request = http.HttpRequest()
    # no role is offered now 
    request.POST = {'role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.OrgActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)
    self.assertEqual(connection.org_role, connection_model.NO_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertNotIn(self.org.key(), profile.mentor_for)

  def testMentorRoleToNoRoleWhileRoleRequested(self):
    """Tests NO ROLE if mentor role offered and user requests role."""
    # user is a mentor for organization
    profile = self.profile_helper.createMentor(self.org)
    connection = connection_model.Connection.all().ancestor(
        profile).filter('organization', self.org).get()

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }

    request = http.HttpRequest()
    # no role is offered now 
    request.POST = {'role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    # assume that mentor cannot be removed
    with mock.patch.object(
        profile_logic, 'isNoRoleEligibleForOrg', return_value=rich_bool.FALSE):
      handler = connection_view.OrgActionsFormHandler(self.view)
      handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.MENTOR_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertIn(self.org.key(), profile.mentor_for)

    # now the mentor can be removed
    request = http.HttpRequest()
    # no role is offered now 
    request.POST = {'role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    # assume that mentor can be removed
    with mock.patch.object(
        profile_logic, 'isNoRoleEligibleForOrg', return_value=rich_bool.TRUE):
      handler = connection_view.OrgActionsFormHandler(self.view)
      handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.NO_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertNotIn(self.org.key(), profile.mentor_for)

  def testMentorRoleToMentorRoleWhileNoRoleRequested(self):
    """Tests MENTOR ROLE if mentor role offered and user requests no role."""
    profile = self.profile_helper.createProfile()

    # user does not request any role from organization
    connection = connection_utils.seed_new_connection(
        profile, self.org, org_role=connection_model.MENTOR_ROLE)

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }

    request = http.HttpRequest()
    # mentor role is offered now 
    request.POST = {'role': connection_model.MENTOR_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.OrgActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)
    self.assertEqual(connection.org_role, connection_model.MENTOR_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertNotIn(self.org.key(), profile.mentor_for)

  def testMentorRoleToMentorRoleWhileRoleRequested(self):
    """Tests MENTOR ROLE if mentor role offered and user requests role."""
    # user is a mentor for organization
    profile = self.profile_helper.createMentor(self.org)
    connection = connection_model.Connection.all().ancestor(
        profile).filter('organization', self.org).get()

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }

    request = http.HttpRequest()
    # mentor role is offered now 
    request.POST = {'role': connection_model.MENTOR_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.OrgActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.MENTOR_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertIn(self.org.key(), profile.mentor_for)

  def testMentorRoleToOrgAdminRoleWhileNoRoleRequested(self):
    """Tests ORG ADMIN if mentor role offered and user requests no role."""
    profile = self.profile_helper.createProfile()

    # user does not request any role from organization
    connection = connection_utils.seed_new_connection(
        profile, self.org, org_role=connection_model.MENTOR_ROLE)

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }

    request = http.HttpRequest()
    # org admin role is offered now 
    request.POST = {'role': connection_model.ORG_ADMIN_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.OrgActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)
    self.assertEqual(connection.org_role, connection_model.ORG_ADMIN_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertNotIn(self.org.key(), profile.mentor_for)

  def testMentorRoleToOrgAdminRoleWhileRoleRequested(self):
    """Tests ORG ADMIN if mentor role offered and user requests role."""
    # user is a mentor for organization
    profile = self.profile_helper.createMentor(self.org)
    connection = connection_model.Connection.all().ancestor(
        profile).filter('organization', self.org).get()

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }

    request = http.HttpRequest()
    # org admin role is offered now 
    request.POST = {'role': connection_model.ORG_ADMIN_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.OrgActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.ORG_ADMIN_ROLE)
    self.assertIn(self.org.key(), profile.org_admin_for)
    self.assertIn(self.org.key(), profile.mentor_for)

  def testOrgAdminRoleToNoRoleWhileNoRoleRequested(self):
    """Tests NO ROLE if org admin offered and user requests no role."""
    profile = self.profile_helper.createProfile()

    # user does not request any role from organization
    connection = connection_utils.seed_new_connection(
        profile, self.org, org_role=connection_model.ORG_ADMIN_ROLE)

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }

    request = http.HttpRequest()
    # no role is offered now 
    request.POST = {'role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.OrgActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)
    self.assertEqual(connection.org_role, connection_model.NO_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertNotIn(self.org.key(), profile.mentor_for)

  def testOrgAdminRoleToNoRoleWhileRoleRequested(self):
    """Tests NO ROLE if org admin offered and user requests role."""
    # user is an org admin for organization
    profile = self.profile_helper.createOrgAdmin(self.org)
    connection = connection_model.Connection.all().ancestor(
        profile).filter('organization', self.org).get()

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }

    request = http.HttpRequest()
    # no role is offered now 
    request.POST = {'role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    # assume that org admin cannot be removed
    with mock.patch.object(
        profile_logic, 'isNoRoleEligibleForOrg', return_value=rich_bool.FALSE):
      handler = connection_view.OrgActionsFormHandler(self.view)
      handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.ORG_ADMIN_ROLE)
    self.assertIn(self.org.key(), profile.org_admin_for)
    self.assertIn(self.org.key(), profile.mentor_for)

    # now the mentor can be removed
    request = http.HttpRequest()
    # no role is offered now 
    request.POST = {'role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    # assume that org admin can be removed
    with mock.patch.object(
        profile_logic, 'isNoRoleEligibleForOrg', return_value=rich_bool.TRUE):
      handler = connection_view.OrgActionsFormHandler(self.view)
      handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.NO_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertNotIn(self.org.key(), profile.mentor_for)

  def testOrgAdminRoleToMentorRoleWhileNoRoleRequested(self):
    """Tests MENTOR ROLE if org admin offered and user requests no role."""
    profile = self.profile_helper.createProfile()

    # user does not request any role from organization
    connection = connection_utils.seed_new_connection(
        profile, self.org, org_role=connection_model.ORG_ADMIN_ROLE)

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }

    request = http.HttpRequest()
    # mentor role is offered now 
    request.POST = {'role': connection_model.MENTOR_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.OrgActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)
    self.assertEqual(connection.org_role, connection_model.MENTOR_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertNotIn(self.org.key(), profile.mentor_for)

  def testOrgAdminRoleToMentorRoleWhileRoleRequested(self):
    """Tests MENTOR ROLE if org admin offered and user requests role."""
    # user is an org admin for organization
    profile = self.profile_helper.createOrgAdmin(self.org)
    connection = connection_model.Connection.all().ancestor(
        profile).filter('organization', self.org).get()

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }

    request = http.HttpRequest()
    # mentor role is offered now
    request.POST = {'role': connection_model.MENTOR_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    # assume that org admin cannot be removed
    with mock.patch.object(
        profile_logic, 'isMentorRoleEligibleForOrg',
        return_value=rich_bool.FALSE):
      handler = connection_view.OrgActionsFormHandler(self.view)
      handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.ORG_ADMIN_ROLE)
    self.assertIn(self.org.key(), profile.org_admin_for)
    self.assertIn(self.org.key(), profile.mentor_for)

    # now the org admin can be removed
    request = http.HttpRequest()
    # mentor role is offered now 
    request.POST = {'role': connection_model.MENTOR_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    # assume that org admin can be removed
    with mock.patch.object(
        profile_logic, 'isMentorRoleEligibleForOrg',
        return_value=rich_bool.TRUE):
      handler = connection_view.OrgActionsFormHandler(self.view)
      handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.MENTOR_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertIn(self.org.key(), profile.mentor_for)

  def testOrgAdminRoleToOrgAdminRoleWhileNoRoleRequested(self):
    """Tests ORG ADMIN if org admin offered and user requests no role."""
    profile = self.profile_helper.createProfile()

    # user does not request any role from organization
    connection = connection_utils.seed_new_connection(
        profile, self.org, org_role=connection_model.ORG_ADMIN_ROLE)

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }

    request = http.HttpRequest()
    # org admin role is offered now 
    request.POST = {'role': connection_model.ORG_ADMIN_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.OrgActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)
    self.assertEqual(connection.org_role, connection_model.ORG_ADMIN_ROLE)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    self.assertNotIn(self.org.key(), profile.mentor_for)

  def testOrgAdminRoleToOrgAdminRoleWhileRoleRequested(self):
    """Tests ORG ADMIN if org admin offered and user requests role."""
    # user is a org admin for organization
    profile = self.profile_helper.createOrgAdmin(self.org)
    connection = connection_model.Connection.all().ancestor(
        profile).filter('organization', self.org).get()

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }

    request = http.HttpRequest()
    # org admin role is offered now 
    request.POST = {'role': connection_model.ORG_ADMIN_ROLE}
    data = request_data.RequestData(request, None, self.kwargs)

    handler = connection_view.OrgActionsFormHandler(self.view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.ORG_ADMIN_ROLE)
    self.assertIn(self.org.key(), profile.org_admin_for)
    self.assertIn(self.org.key(), profile.mentor_for)
