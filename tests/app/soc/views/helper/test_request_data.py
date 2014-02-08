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

"""Tests for request_data module."""

import httplib
import unittest

from google.appengine.ext import ndb

from melange.models import settings as settings_model
from melange.request import exception

from soc.models import org_app_survey as org_app_survey_model
from soc.models import organization as org_model
from soc.models import profile as profile_model
from soc.models import program as program_model
from soc.views.helper import request_data
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests import org_utils
from tests import profile_utils
from tests import program_utils
from tests import timeline_utils
from tests.utils import connection_utils

# NOTE(nathaniel): Throughout this module attribute access is used
# as an operation under test. This confuses lint which assumes that
# attribute access is always a safe and side-effect-free action. In
# all fairness, lint is probably right and our code is weird.
# pylint: disable=pointless-statement


class TimelineHelperTest(unittest.TestCase):
  """Unit tests for TimelineHelper class."""

  def setUp(self):
    """See unitest.TestCase.setUp for specification."""
    org_app = seeder_logic.seed(org_app_survey_model.OrgAppSurvey)
    self.timeline_helper = request_data.TimelineHelper(None, org_app)

  def testBeforeOrgSignupStart(self):
    """Tests for beforeOrgSignupStart function."""
    # organization application has yet to start
    self.timeline_helper.org_app.survey_start = timeline_utils.future(delta=1)
    self.timeline_helper.org_app.survey_end = timeline_utils.future(delta=2)
    self.assertTrue(self.timeline_helper.beforeOrgSignupStart())

    # organization application has started
    self.timeline_helper.org_app.survey_start = timeline_utils.past(delta=1)
    self.timeline_helper.org_app.survey_end = timeline_utils.future(delta=2)
    self.assertFalse(self.timeline_helper.beforeOrgSignupStart())

    # organization application has ended
    self.timeline_helper.org_app.survey_start = timeline_utils.past(delta=2)
    self.timeline_helper.org_app.survey_end = timeline_utils.past(delta=1)
    self.assertFalse(self.timeline_helper.beforeOrgSignupStart())

    # no organization application is defined
    self.timeline_helper.org_app = None
    self.assertTrue(self.timeline_helper.beforeOrgSignupStart())


class UrlUserPropertyTest(unittest.TestCase):
  """Unit tests for url_user property of RequestData class."""

  def testNoUserData(self):
    """Tests that error is raised if there is no user data in kwargs."""
    data = request_data.RequestData(None, None, {})
    with self.assertRaises(exception.UserError) as context:
      data.url_ndb_user
    self.assertEqual(context.exception.status, httplib.BAD_REQUEST)

  def testUserDoesNotExist(self):
    """Tests that error is raised if requested user does not exist."""
    data = request_data.RequestData(None, None, {'user': 'non_existing'})
    with self.assertRaises(exception.UserError) as context:
      data.url_ndb_user
    self.assertEqual(context.exception.status, httplib.NOT_FOUND)

  def testUserExists(self):
    """Tests that user is returned correctly if exists."""
    user = profile_utils.seedNDBUser()
    data = request_data.RequestData(None, None, {'user': user.user_id})
    url_user = data.url_ndb_user
    self.assertEqual(user.key, url_user.key)


class UrlProfilePropertyTest(unittest.TestCase):
  """Unit tests for url_profile property of RequestData class."""

  def testNoProfileData(self):
    """Tests that error is raised if there is no profile data in kwargs."""
    # no data at all
    data = request_data.RequestData(None, None, {})
    with self.assertRaises(exception.UserError) as context:
      data.url_profile
    self.assertEqual(context.exception.status, httplib.BAD_REQUEST)

    # program data but no user identifier
    kwargs = {
        'sponsor': 'sponsor_id',
        'program': 'program_id'
        }
    data = request_data.RequestData(None, None, kwargs)
    with self.assertRaises(exception.UserError) as context:
      data.url_profile
    self.assertEqual(context.exception.status, httplib.BAD_REQUEST)

    # user identifier present but no program data
    data = request_data.RequestData(None, None, {'user': 'user_id'})
    with self.assertRaises(exception.UserError) as context:
      data.url_profile
    self.assertEqual(context.exception.status, httplib.BAD_REQUEST)

  def testProfileDoesNotExist(self):
    """Tests that error is raised if requested profile does not exist."""
    kwargs = {
        'sponsor': 'sponsor_id',
        'program': 'program_id',
        'user': 'user_id'
        }
    data = request_data.RequestData(None, None, kwargs)
    with self.assertRaises(exception.UserError) as context:
      data.url_profile
    self.assertEqual(context.exception.status, httplib.NOT_FOUND)

  def testProfileExists(self):
    """Tests that profile is returned correctly if exists."""
    sponsor = program_utils.seedSponsor()
    program = program_utils.seedProgram(sponsor_key=sponsor.key())
    profile = profile_utils.seedNDBProfile(self.program.key())

    kwargs = {
        'sponsor': sponsor.link_id,
        'program': program.program_id,
        'user': profile.profile_id,
        }
    data = request_data.RequestData(None, None, kwargs)
    url_profile = data.url_profile
    self.assertEqual(profile.key(), url_profile.key())


class UrlOrgPropertyTest(unittest.TestCase):
  """Unit tests for url_org property of RequestData class."""

  def testNoOrgData(self):
    """Tests that error is raised if there is no org data in kwargs."""
    # no data at all
    data = request_data.RequestData(None, None, {})
    with self.assertRaises(exception.UserError) as context:
      data.url_org
    self.assertEqual(context.exception.status, httplib.BAD_REQUEST)

    # program data but no user identifier
    kwargs = {
        'sponsor': 'sponsor_id',
        'program': 'program_id'
        }
    data = request_data.RequestData(None, None, kwargs)
    with self.assertRaises(exception.UserError) as context:
      data.url_org
    self.assertEqual(context.exception.status, httplib.BAD_REQUEST)

    # user identifier present but no program data
    data = request_data.RequestData(None, None, {'organization': 'org_id'})
    with self.assertRaises(exception.UserError) as context:
      data.url_org
    self.assertEqual(context.exception.status, httplib.BAD_REQUEST)

  def testOrgDoesNotExist(self):
    """Tests that error is raised if requested organization does not exist."""
    kwargs = {
        'sponsor': 'sponsor_id',
        'program': 'program_id',
        'organization': 'org_id'
        }
    data = request_data.RequestData(None, None, kwargs)
    with self.assertRaises(exception.UserError) as context:
      data.url_org
    self.assertEqual(context.exception.status, httplib.NOT_FOUND)

  def testOrgExists(self):
    """Tests that organization is returned correctly if exists."""
    sponsor = program_utils.seedSponsor()
    program = seeder_logic.seed(program_model.Program)
    org_properties = {
        'key_name': '%s/%s/test_org' % (sponsor.link_id, program.program_id),
        'link_id': 'test_org',
        }
    org = seeder_logic.seed(org_model.Organization, org_properties)

    kwargs = {
        'sponsor': sponsor.link_id,
        'program': program.program_id,
        'organization': org.link_id
        }
    data = request_data.RequestData(None, None, kwargs)
    url_org = data.url_org
    self.assertEqual(org.key(), url_org.key())


class UrlConnectionPropertyTest(unittest.TestCase):
  """Unit tests for url_connection property of RequestData class."""

  def testNoConnectionData(self):
    """Tests that error is raised if there is no enough data in the URL."""
    # no data at all
    data = request_data.RequestData(None, None, {})
    with self.assertRaises(exception.UserError) as context:
      data.url_connection
    self.assertEqual(context.exception.status, httplib.BAD_REQUEST)

    # program and connection data but no user identifier
    kwargs = {
        'sponsor': 'sponsor_id',
        'program': 'program_id',
        'id': '1',
        }
    data = request_data.RequestData(None, None, kwargs)
    with self.assertRaises(exception.UserError) as context:
      data.url_connection
    self.assertEqual(context.exception.status, httplib.BAD_REQUEST)

    # profile data but no connection identifier
    kwargs = {
        'sponsor': 'sponsor_id',
        'program': 'program_id',
        'user': 'user_id',
        }
    data = request_data.RequestData(None, None, kwargs)
    with self.assertRaises(exception.UserError) as context:
      data.url_connection
    self.assertEqual(context.exception.status, httplib.BAD_REQUEST)

    # only connection id
    kwargs = {'id': '1'}
    data = request_data.RequestData(None, None, kwargs)
    with self.assertRaises(exception.UserError) as context:
      data.url_connection
    self.assertEqual(context.exception.status, httplib.BAD_REQUEST)

  def testConnectionDoesNotExist(self):
    """Tests that error is raised if requested connection does not exist."""
    kwargs = {
        'sponsor': 'sponsor_id',
        'program': 'program_id',
        'user': 'user_id',
        'id': '1'
        }
    data = request_data.RequestData(None, None, kwargs)
    with self.assertRaises(exception.UserError) as context:
      data.url_connection
    self.assertEqual(context.exception.status, httplib.NOT_FOUND)

  def testConnectionExists(self):
    """Tests that connection is returned correctly if exists."""
    sponsor = program_utils.seedSponsor()
    program = program_utils.seedProgram(sponsor_key=sponsor.key())
    org = org_utils.seedOrganization(program.key())

    profile = profile_utils.seedNDBProfile(program.key())
    connection = connection_utils.seed_new_connection(profile.key, org.key)

    kwargs = {
        'sponsor': sponsor.link_id,
        'program': program.program_id,
        'user': profile.profile_id,
        'id': str(connection.key.id())
        }
    data = request_data.RequestData(None, None, kwargs)
    url_connection = data.url_connection
    self.assertEqual(connection.key, url_connection.key)


class IsHostPropertyTest(unittest.TestCase):
  """Unit tests for is_host property of RequestData class."""

  def testForHostUser(self):
    """Tests that True is returned for a user who is a host."""
    sponsor = program_utils.seedSponsor()
    program = program_utils.seedProgram(sponsor_key=sponsor.key())
    user = profile_utils.seedNDBUser(host_for=[program])
    profile_utils.loginNDB(user)

    kwargs = {
        'sponsor': sponsor.link_id,
        'program': program.program_id,
        }
    data = request_data.RequestData(None, None, kwargs)
    is_host = data.is_host
    self.assertTrue(is_host)

  def testForNonHostUser(self):
    """Tests that False is returned for a user who is not a host."""
    sponsor = program_utils.seedSponsor()
    program = program_utils.seedProgram(sponsor_key=sponsor.key())
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)

    kwargs = {
        'sponsor': sponsor.link_id,
        'program': program.program_id,
        }
    data = request_data.RequestData(None, None, kwargs)
    is_host = data.is_host
    self.assertFalse(is_host)


class UserPropertyTest(unittest.TestCase):
  """Unit tests for user property of RequestData class."""

  def testNoUser(self):
    """Tests that None is returned for no user entity."""
    data = request_data.RequestData(None, None, None)
    self.assertIsNone(data.ndb_user)

  def testUserExists(self):
    """Tests that user entity is returned when it exists."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)

    data = request_data.RequestData(None, None, None)
    self.assertEqual(data.ndb_user.key, user.key)

  def testForDeveloperWithViewAsUser(self):
    """Tests for developer who has 'view_as' property set."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user, is_admin=True)

    # set the settings so that 'view_as' is set to an existing user
    other_user = profile_utils.seedNDBUser()
    settings = settings_model.UserSettings(
        parent=user.key, view_as=other_user.key)
    settings.put()

    # check that the other user is returned
    data = request_data.RequestData(None, None, None)
    self.assertEqual(data.ndb_user.key, other_user.key)

    # set the settings so that 'view_as' is set to a non-existing user
    settings.view_as = ndb.Key('User', 'non_existing')
    settings.put()

    # check that an error is raised
    data = request_data.RequestData(None, None, None)
    with self.assertRaises(exception.UserError) as context:
      user = data.ndb_user
    self.assertEqual(context.exception.status, httplib.BAD_REQUEST)
