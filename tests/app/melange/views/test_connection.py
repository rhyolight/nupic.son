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
import httplib
import unittest

from django import http

from melange.logic import connection as connection_logic
from melange.models import connection as connection_model
from melange.request import exception
from melange.views import connection as connection_view
from melange.utils import rich_bool

from soc.views.helper import request_data

# TODO(daniel): Summer Of code module cannot be imported here
from soc.modules.gsoc.logic import profile as profile_logic

from tests import org_utils
from tests import profile_utils
from tests import program_utils
from tests.utils import connection_utils


class UrlConnectionIsForCurrentUserAccessCheckerTest(unittest.TestCase):
  """Unit tests for UrlConnectionIsForCurrentUserAccessChecker class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    sponsor = program_utils.seedSponsor()
    self.program = program_utils.seedProgram(sponsor_key=sponsor.key())
    self.organization = org_utils.seedOrganization(self.program.key())

    self.user = profile_utils.seedNDBUser()
    profile = profile_utils.seedNDBProfile(
        self.program.key(), user=self.user)

    connection = connection_utils.seed_new_connection(
        profile.key, self.organization.key)

    kwargs = {
        'sponsor': sponsor.key().name(),
        'program': self.program.program_id,
        'organization': self.organization.org_id,
        'user': self.user.user_id,
        'id': str(connection.key.id())
        }
    self.data = request_data.RequestData(None, None, kwargs)

  def testConnectedUserAccessGranted(self):
    """Tests that access is granted for the connected user."""
    profile_utils.loginNDB(self.user)
    access_checker = (
        connection_view.UrlConnectionIsForCurrentUserAccessChecker())
    access_checker.checkAccess(self.data, None)

  def testAnotherUserAccessDenied(self):
    """Tests that another (not connected) user is denied access."""
    # seed another user who is currently logged in
    other_user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(other_user)

    access_checker = (
        connection_view.UrlConnectionIsForCurrentUserAccessChecker())
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.status, httplib.FORBIDDEN)

  def testUserWithNoProfileAccessDenied(self):
    """Tests that access for a user with no profile is denied."""
    # check for not logged-in user with no profile
    profile_utils.logout()

    access_checker = (
        connection_view.UrlConnectionIsForCurrentUserAccessChecker())
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.status, httplib.FORBIDDEN)

    # check for another user who is currently logged in but
    # does not have a profile
    other_user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(other_user)

    access_checker = (
        connection_view.UrlConnectionIsForCurrentUserAccessChecker())
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.status, httplib.FORBIDDEN)

  def testOrgAdminAccessDenied(self):
    """Tests that org admin for connected organization is denied access."""
    # seed another user who is currently logged in
    other_user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(other_user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=other_user, admin_for=[self.organization.key])

    access_checker = (
        connection_view.UrlConnectionIsForCurrentUserAccessChecker())
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.status, httplib.FORBIDDEN)


class IsUserOrgAdminForUrlConnectionTest(unittest.TestCase):
  """Unit tests for IsUserOrgAdminForUrlConnection class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    sponsor = program_utils.seedSponsor()
    self.program = program_utils.seedProgram(sponsor_key=sponsor.key())
    self.organization = org_utils.seedOrganization(self.program.key())

    self.user = profile_utils.seedNDBUser()
    profile = profile_utils.seedNDBProfile(
        self.program.key(), user=self.user)

    connection = connection_utils.seed_new_connection(
        profile.key, self.organization.key)

    kwargs = {
        'sponsor': sponsor.key().name(),
        'program': self.program.program_id,
        'organization': self.organization.org_id,
        'user': self.user.user_id,
        'id': str(connection.key.id())
        }
    self.data = request_data.RequestData(None, None, kwargs)


  def testOrgAdminAccessGranted(self):
    """Tests that access is granted for org admin for the connected org."""
    # seed a user who is currently logged in
    other_user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(other_user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=other_user, admin_for=[self.organization.key])

    access_checker = connection_view.IsUserOrgAdminForUrlConnection()
    access_checker.checkAccess(self.data, None)

  def testConnectedUserAccessDenied(self):
    """Tests that access is denied for connected user."""
    profile_utils.loginNDB(self.user)

    access_checker = connection_view.IsUserOrgAdminForUrlConnection()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.status, httplib.FORBIDDEN)

  def testOtherOrgAdminAccessDenied(self):
    """Tests that access is denied for org admin for another org."""
    # seed another organization
    other_org = org_utils.seedOrganization(self.program.key())

    # seed a user who is currently logged in
    other_user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(other_user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=other_user, admin_for=[other_org.key])

    access_checker = connection_view.IsUserOrgAdminForUrlConnection()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.status, httplib.FORBIDDEN)


class _MockView(object):
  """Simple request handler to be used as a callback for other handlers."""

  def get(self, data, access, mutator):
    """See base.RequestHandler.get for specification."""
    pass


class UserActionsFormHandlerTest(unittest.TestCase):
  """Unit tests for UserActionsFormHandler class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.sponsor = program_utils.seedSponsor()
    self.program = program_utils.seedProgram(sponsor_key=self.sponsor.key())
    self.org = org_utils.seedOrganization(self.program.key())

    # unused object used as a callback for the handler
    self.view = _MockView()

  def testUserNoRoleToNoRoleWhileNoRoleOffered(self):
    """Tests NO ROLE if user has no role and no role is offered."""
    profile = profile_utils.seedNDBProfile(self.program.key())

    # no role is offered to the user; the user does not request any role
    connection = connection_utils.seed_new_connection(profile.key, self.org.key)
    old_seen_by_org = connection.seen_by_org
    old_seen_by_user = connection.seen_by_user

    kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.profile_id,
        'id': str(connection.key.id())
        }

    request = http.HttpRequest()
    # the user still does not request any role
    request.POST = {'role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, kwargs)

    handler = connection_view.UserActionsFormHandler(self.view, url='unsed')
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = connection.key.get()
    profile = profile.key.get()
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)
    self.assertEqual(connection.org_role, connection_model.NO_ROLE)
    self.assertNotIn(self.org.key, profile.admin_for)
    self.assertNotIn(self.org.key, profile.mentor_for)

    # nothing has changed, so seen by properties are not changed
    self.assertEqual(connection.seen_by_user, old_seen_by_user)
    self.assertEqual(connection.seen_by_org, old_seen_by_org)

    # check that no connection message is created
    query = connection_model.ConnectionMessage.query(ancestor=connection.key)
    message = query.get()
    self.assertIsNone(message)

  def testUserNoRoleToNoRoleWhileMentorRoleOffered(self):
    """Tests NO ROLE if user has no role and mentor role is offered."""
    profile = profile_utils.seedNDBProfile(self.program.key())

    # mentor role is offered to the user; the user does not request any role
    connection = connection_utils.seed_new_connection(
        profile.key, self.org.key, org_role=connection_model.MENTOR_ROLE)
    old_seen_by_org = connection.seen_by_org
    old_seen_by_user = connection.seen_by_user

    kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.profile_id,
        'id': str(connection.key.id())
        }

    request = http.HttpRequest()
    # the user still does not request any role
    request.POST = {'role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, kwargs)

    handler = connection_view.UserActionsFormHandler(self.view, url='unsed')
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = connection.key.get()
    profile = profile.key.get()
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)
    self.assertEqual(connection.org_role, connection_model.MENTOR_ROLE)
    self.assertNotIn(self.org.key, profile.admin_for)
    self.assertNotIn(self.org.key, profile.mentor_for)

    # nothing has changed, so seen by properties are not changed
    self.assertEqual(connection.seen_by_user, old_seen_by_user)
    self.assertEqual(connection.seen_by_org, old_seen_by_org)

    # check that no connection message is created
    query = connection_model.ConnectionMessage.query(ancestor=connection.key)
    message = query.get()
    self.assertIsNone(message)

  def testUserNoRoleToNoRoleWhileOrgAdminRoleOffered(self):
    """Tests NO ROLE if user has no role and org admin role is offered."""
    profile = profile_utils.seedNDBProfile(self.program.key())

    # org admin role is offered to the user; the user does not request any role
    connection = connection_utils.seed_new_connection(
        profile.key, self.org.key, org_role=connection_model.ORG_ADMIN_ROLE)
    old_seen_by_org = connection.seen_by_org
    old_seen_by_user = connection.seen_by_user

    kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.profile_id,
        'id': str(connection.key.id())
        }

    request = http.HttpRequest()
    # the user still does not request any role
    request.POST = {'role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, kwargs)

    handler = connection_view.UserActionsFormHandler(self.view, url='unused')
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = connection.key.get()
    profile = profile.key.get()
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)
    self.assertEqual(connection.org_role, connection_model.ORG_ADMIN_ROLE)
    self.assertNotIn(self.org.key, profile.admin_for)
    self.assertNotIn(self.org.key, profile.mentor_for)

    # nothing has changed, so seen by properties are not changed
    self.assertEqual(connection.seen_by_user, old_seen_by_user)
    self.assertEqual(connection.seen_by_org, old_seen_by_org)

    # check that no connection message is created
    query = connection_model.ConnectionMessage.query(ancestor=connection.key)
    message = query.get()
    self.assertIsNone(message)

  def testUserNoRoleToRoleWhileNoRoleOffered(self):
    """Tests ROLE if user has no role and no role is offered."""
    profile = profile_utils.seedNDBProfile(self.program.key())

    # no role is offered to the user; the user does not request any role
    connection = connection_utils.seed_new_connection(profile.key, self.org.key)

    kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.profile_id,
        'id': str(connection.key.id())
        }

    request = http.HttpRequest()
    # the user requests a role now
    request.POST = {'role': connection_model.ROLE}
    data = request_data.RequestData(request, None, kwargs)

    handler = connection_view.UserActionsFormHandler(self.view, url='unsed')
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = connection.key.get()
    profile = profile.key.get()
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.NO_ROLE)
    self.assertNotIn(self.org.key, profile.admin_for)
    self.assertNotIn(self.org.key, profile.mentor_for)

    # connection changed, so seen by properties are changed
    self.assertTrue(connection.seen_by_user)
    self.assertFalse(connection.seen_by_org)

    # check that a connection message is created
    query = connection_model.ConnectionMessage.query(ancestor=connection.key)
    message = query.get()
    self.assertIn(connection_logic._USER_REQUESTS_ROLE, message.content)

  def testUserNoRoleToRoleWhileMentorRoleOffered(self):
    """Tests ROLE if user has no role and mentor role is offered."""
    profile = profile_utils.seedNDBProfile(self.program.key())

    # mentor role is offered to the user; the user does not request any role
    connection = connection_utils.seed_new_connection(
        profile.key, self.org.key, org_role=connection_model.MENTOR_ROLE)

    kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.profile_id,
        'id': str(connection.key.id())
        }

    request = http.HttpRequest()
    # the user requests a role now
    request.POST = {'role': connection_model.ROLE}
    data = request_data.RequestData(request, None, kwargs)

    handler = connection_view.UserActionsFormHandler(self.view, url='unsed')
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = connection.key.get()
    profile = profile.key.get()
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.MENTOR_ROLE)
    self.assertNotIn(self.org.key, profile.admin_for)
    self.assertIn(self.org.key, profile.mentor_for)

    # connection changed, so seen by properties are changed
    self.assertTrue(connection.seen_by_user)
    self.assertFalse(connection.seen_by_org)

    # check that a connection message is created
    query = connection_model.ConnectionMessage.query(ancestor=connection.key)
    message = query.get()
    self.assertIn(connection_logic._USER_REQUESTS_ROLE, message.content)

  def testUserNoRoleToRoleWhileOrgAdminRoleOffered(self):
    """Tests ROLE if user has no role and org admin role is offered."""
    profile = profile_utils.seedNDBProfile(self.program.key())

    # org admin role is offered to the user; the user does not request any role
    connection = connection_utils.seed_new_connection(
        profile.key, self.org.key, org_role=connection_model.ORG_ADMIN_ROLE)

    kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.profile_id,
        'id': str(connection.key.id())
        }

    request = http.HttpRequest()
    # the user requests a role now
    request.POST = {'role': connection_model.ROLE}
    data = request_data.RequestData(request, None, kwargs)

    handler = connection_view.UserActionsFormHandler(self.view, url='unsed')
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = connection.key.get()
    profile = profile.key.get()
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.ORG_ADMIN_ROLE)
    self.assertIn(self.org.key, profile.admin_for)
    self.assertIn(self.org.key, profile.mentor_for)

    # connection changed, so seen by properties are changed
    self.assertTrue(connection.seen_by_user)
    self.assertFalse(connection.seen_by_org)

    # check that a connection message is created
    query = connection_model.ConnectionMessage.query(ancestor=connection.key)
    message = query.get()
    self.assertIn(connection_logic._USER_REQUESTS_ROLE, message.content)

  def testUserRoleToRoleWhileNoRoleOffered(self):
    """Tests ROLE if user has role and no role is offered."""
    profile = profile_utils.seedNDBProfile(self.program.key())

    # no role is offered to the user; the user requests role
    connection = connection_utils.seed_new_connection(
        profile.key, self.org.key, user_role=connection_model.ROLE)
    old_seen_by_org = connection.seen_by_org
    old_seen_by_user = connection.seen_by_user

    kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.profile_id,
        'id': str(connection.key.id())
        }

    request = http.HttpRequest()
    # the user still requests a role
    request.POST = {'role': connection_model.ROLE}
    data = request_data.RequestData(request, None, kwargs)

    handler = connection_view.UserActionsFormHandler(self.view, url='unsed')
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = connection.key.get()
    profile = profile.key.get()
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.NO_ROLE)
    self.assertNotIn(self.org.key, profile.admin_for)
    self.assertNotIn(self.org.key, profile.mentor_for)

    # nothing has changed, so seen by properties are not changed
    self.assertEqual(connection.seen_by_user, old_seen_by_user)
    self.assertEqual(connection.seen_by_org, old_seen_by_org)

    # check that no connection message is created
    query = connection_model.ConnectionMessage.query(ancestor=connection.key)
    message = query.get()
    self.assertIsNone(message)

  def testUserRoleToRoleWhileMentorRoleOffered(self):
    """Tests ROLE if user has role and mentor role is offered."""
    # mentor role is offered to the user; the user requests role
    profile = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])
    connection = connection_model.Connection.query(
        connection_model.Connection.organization == self.org.key,
        ancestor=profile.key).get()
    old_seen_by_org = connection.seen_by_org
    old_seen_by_user = connection.seen_by_user

    kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.profile_id,
        'id': str(connection.key.id())
        }

    request = http.HttpRequest()
    # the user still requests a role
    request.POST = {'role': connection_model.ROLE}
    data = request_data.RequestData(request, None, kwargs)

    handler = connection_view.UserActionsFormHandler(self.view, url='unsed')
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = connection.key.get()
    profile = profile.key.get()
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.MENTOR_ROLE)
    self.assertNotIn(self.org.key, profile.admin_for)
    self.assertIn(self.org.key, profile.mentor_for)

    # nothing has changed, so seen by properties are not changed
    self.assertEqual(connection.seen_by_user, old_seen_by_user)
    self.assertEqual(connection.seen_by_org, old_seen_by_org)

    # check that no connection message is created
    query = connection_model.ConnectionMessage.query(ancestor=connection.key)
    message = query.get()
    self.assertIsNone(message)

  def testUserRoleToRoleWhileOrgAdminRoleOffered(self):
    """Tests ROLE if user has role and org admin role is offered."""
    # org admin role is offered to the user; the user requests role
    profile = profile_utils.seedNDBProfile(
        self.program.key(), admin_for=[self.org.key])
    connection = connection_model.Connection.query(
        connection_model.Connection.organization == self.org.key,
        ancestor=profile.key).get()
    old_seen_by_org = connection.seen_by_org
    old_seen_by_user = connection.seen_by_user

    kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.profile_id,
        'id': str(connection.key.id())
        }

    request = http.HttpRequest()
    # the user still requests a role
    request.POST = {'role': connection_model.ROLE}
    data = request_data.RequestData(request, None, kwargs)

    handler = connection_view.UserActionsFormHandler(self.view, url='unsed')
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = connection.key.get()
    profile = profile.key.get()
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.ORG_ADMIN_ROLE)
    self.assertIn(self.org.key, profile.admin_for)
    self.assertIn(self.org.key, profile.mentor_for)

    # nothing has changed, so seen by properties are not changed
    self.assertEqual(connection.seen_by_user, old_seen_by_user)
    self.assertEqual(connection.seen_by_org, old_seen_by_org)

    # check that no connection message is created
    query = connection_model.ConnectionMessage.query(ancestor=connection.key)
    message = query.get()
    self.assertIsNone(message)

  def testUserRoleToNoRoleWhileNoRoleOffered(self):
    """Tests NO ROLE if user has role and no role is offered."""
    profile = profile_utils.seedNDBProfile(self.program.key())

    # no role is offered to the user; the user requests role
    connection = connection_utils.seed_new_connection(
        profile.key, self.org.key, user_role=connection_model.ROLE)

    kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.profile_id,
        'id': str(connection.key.id())
        }

    request = http.HttpRequest()
    # the user does not request role anymore
    request.POST = {'role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, kwargs)

    handler = connection_view.UserActionsFormHandler(self.view, url='unsed')
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = connection.key.get()
    profile = profile.key.get()
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)
    self.assertEqual(connection.org_role, connection_model.NO_ROLE)
    self.assertNotIn(self.org.key, profile.admin_for)
    self.assertNotIn(self.org.key, profile.mentor_for)

    # connection changed, so seen by properties are changed
    self.assertTrue(connection.seen_by_user)
    self.assertFalse(connection.seen_by_org)

    # check that a connection message is created
    query = connection_model.ConnectionMessage.query(ancestor=connection.key)
    message = query.get()
    self.assertIn(
        connection_logic._USER_DOES_NOT_REQUEST_ROLE, message.content)

  def testUserRoleToNoRoleWhileMentorRoleOffered(self):
    """Tests NO ROLE if user has role and mentor role is offered."""
    # mentor role is offered to the user; the user requests role
    profile = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])
    connection = connection_model.Connection.query(
        connection_model.Connection.organization == self.org.key,
        ancestor=profile.key).get()

    old_seen_by_user = connection.seen_by_user
    old_seen_by_org = connection.seen_by_org

    kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.profile_id,
        'id': str(connection.key.id()),
        }

    request = http.HttpRequest()
    # the user does not request role anymore
    request.POST = {'role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, kwargs)

    # assume that mentor is not eligible to quit
    handler = connection_view.UserActionsFormHandler(self.view, url='unsed')
    with mock.patch.object(
        profile_logic, 'isNoRoleEligibleForOrg', return_value=rich_bool.FALSE):
      with self.assertRaises(exception.UserError) as context: 
        handler.handle(data, None, None)
      self.assertEqual(context.exception.status, httplib.BAD_REQUEST)

    # check if all data is updated properly
    connection = connection.key.get()
    profile = profile.key.get()
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.MENTOR_ROLE)
    self.assertNotIn(self.org.key, profile.admin_for)
    self.assertIn(self.org.key, profile.mentor_for)

    # nothing has changed, so seen by properties are not changed
    self.assertEqual(connection.seen_by_user, old_seen_by_user)
    self.assertEqual(connection.seen_by_org, old_seen_by_org)

    # check that no connection message is created
    query = connection_model.ConnectionMessage.query(ancestor=connection.key)
    message = query.get()
    self.assertIsNone(message)

    # try again but now, the user is eligible to quit
    request = http.HttpRequest()
    # the user does not request role anymore
    request.POST = {'role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, kwargs)

    handler = connection_view.UserActionsFormHandler(self.view, url='unsed')

    # assume that mentor is eligible to quit
    with mock.patch.object(
        profile_logic, 'isNoRoleEligibleForOrg', return_value=rich_bool.TRUE):
      handler.handle(data, None, None)

    # check if all data is updated properly
    connection = connection.key.get()
    profile = profile.key.get()
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)
    self.assertEqual(connection.org_role, connection_model.MENTOR_ROLE)
    self.assertNotIn(self.org.key, profile.admin_for)
    self.assertNotIn(self.org.key, profile.mentor_for)

    # connection changed, so seen by properties are changed
    self.assertTrue(connection.seen_by_user)
    self.assertFalse(connection.seen_by_org)

    # check that a connection message is created
    query = connection_model.ConnectionMessage.query(ancestor=connection.key)
    message = query.get()
    self.assertIn(
        connection_logic._USER_DOES_NOT_REQUEST_ROLE, message.content)

  def testUserRoleToNoRoleWhileOrgAdminRoleOffered(self):
    """Tests NO ROLE if user has role and org admin role is offered."""
    # org admin role is offered to the user; the user requests role
    profile = profile_utils.seedNDBProfile(
        self.program.key(), admin_for=[self.org.key])
    connection = connection_model.Connection.query(
        connection_model.Connection.organization == self.org.key,
        ancestor=profile.key).get()

    old_seen_by_user = connection.seen_by_user
    old_seen_by_org = connection.seen_by_org

    kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.profile_id,
        'id': str(connection.key.id())
        }

    request = http.HttpRequest()
    # the user does not request role anymore
    request.POST = {'role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, kwargs)

    # assume that mentor is not eligible to quit
    handler = connection_view.UserActionsFormHandler(self.view, url='unsed')
    with mock.patch.object(
        profile_logic, 'isNoRoleEligibleForOrg', return_value=rich_bool.FALSE):
      with self.assertRaises(exception.UserError) as context:
        handler.handle(data, None, None)
      self.assertEqual(context.exception.status, httplib.BAD_REQUEST)

    # check if all data is updated properly
    connection = connection.key.get()
    profile = profile.key.get()
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertEqual(connection.org_role, connection_model.ORG_ADMIN_ROLE)
    self.assertIn(self.org.key, profile.admin_for)
    self.assertIn(self.org.key, profile.mentor_for)

    # nothing has changed, so seen by properties are not changed
    self.assertEqual(connection.seen_by_user, old_seen_by_user)
    self.assertEqual(connection.seen_by_org, old_seen_by_org)

    # check that no connection message is created
    query = connection_model.ConnectionMessage.query(ancestor=connection.key)
    message = query.get()
    self.assertIsNone(message)

    # try again but now, the user is eligible to quit
    request = http.HttpRequest()
    # the user does not request role anymore
    request.POST = {'role': connection_model.NO_ROLE}
    data = request_data.RequestData(request, None, kwargs)

    handler = connection_view.UserActionsFormHandler(self.view, url='unsed')

    # assume that mentor is eligible to quit
    with mock.patch.object(
        profile_logic, 'isNoRoleEligibleForOrg', return_value=rich_bool.TRUE):
      handler.handle(data, None, None)

    # check if all data is updated properly
    connection = connection.key.get()
    profile = profile.key.get()
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)
    self.assertEqual(connection.org_role, connection_model.ORG_ADMIN_ROLE)
    self.assertNotIn(self.org.key, profile.admin_for)
    self.assertNotIn(self.org.key, profile.mentor_for)

    # connection changed, so seen by properties are changed
    self.assertTrue(connection.seen_by_user)
    self.assertFalse(connection.seen_by_org)

    # check that a connection message is created
    query = connection_model.ConnectionMessage.query(ancestor=connection.key)
    message = query.get()
    self.assertIn(connection_logic._USER_DOES_NOT_REQUEST_ROLE, message.content)
