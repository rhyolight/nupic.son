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

import unittest

from codein.views import connection as connection_view

from django import http

from google.appengine.ext import db

from melange.logic import connection as connection_logic
from melange.models import connection as connection_model
from melange.request import exception

from soc.models import organization as org_model
from soc.models import profile as profile_model
from soc.models import user as user_model

from soc.modules.gci.views.helper import request_data
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests import test_utils
from tests.utils import connection_utils


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


class UserActionsFormHandlerTest(test_utils.GCIDjangoTestCase):
  """Unit tests for UserActionsFormHandler class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

  def testHandleNoRoleSelection(self):
    """Tests that NO ROLE choice is handled properly."""
    profile = self.profile_helper.createMentor(self.org)
    connection = connection_logic.queryForAncestorAndOrganization(
        profile.key(), self.org.key()).get()

    request = http.HttpRequest()
    request.POST = {'user_role': connection_model.NO_ROLE}

    kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }

    data = request_data.RequestData(request, None, kwargs)

    view = connection_view.ManageConnectionAsUser()

    handler = connection_view.UserActionsFormHandler(view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.NO_ROLE)
    self.assertNotIn(self.org.key(), profile.mentor_for)
    self.assertNotIn(self.org.key(), profile.org_admin_for)

  def testHandleRoleSelection(self):
    """Tests that ROLE choice is handled properly."""
    profile = self.profile_helper.createProfile()
    connection = connection_utils.seed_new_connection(
        profile, self.org, org_role=connection_model.MENTOR_ROLE)

    request = http.HttpRequest()
    request.POST = {'user_role': connection_model.ROLE}

    kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': profile.link_id,
        'id': connection.key().id()
        }

    data = request_data.RequestData(request, None, kwargs)

    view = connection_view.ManageConnectionAsUser()

    handler = connection_view.UserActionsFormHandler(view)
    handler.handle(data, None, None)

    # check if all data is updated properly
    connection = db.get(connection.key())
    profile = db.get(profile.key())
    self.assertEqual(connection.user_role, connection_model.ROLE)
    self.assertIn(self.org.key(), profile.mentor_for)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
