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

import httplib
import unittest

from melange.request import exception
from melange.views import connection as connection_view

from soc.views.helper import request_data

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
