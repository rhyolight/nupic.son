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

from melange.models import connection as connection_model
from melange.request import exception

from soc.models import organization as org_model
from soc.models import profile as profile_model
from soc.models import program as program_model
from soc.models import sponsor as sponsor_model
from soc.models import user as user_model
from soc.views.helper import request_data
from soc.modules.seeder.logic.seeder import logic as seeder_logic


class UrlUserPropertyTest(unittest.TestCase):
  """Unit tests for url_user property of RequestData class."""

  def testNoUserData(self):
    """Tests that error is raised if there is no user data in kwargs."""
    data = request_data.RequestData(None, None, {})
    with self.assertRaises(ValueError):
      data.url_user

  def testUserDoesNotExist(self):
    """Tests that error is raised if requested user does not exist."""
    data = request_data.RequestData(None, None, {'user': 'non_existing'})
    with self.assertRaises(exception.UserError) as context:
      data.url_user
    self.assertEqual(context.exception.status, httplib.NOT_FOUND)

  def testUserExists(self):
    """Tests that user is returned correctly if exists."""
    user = seeder_logic.seed(user_model.User)
    data = request_data.RequestData(None, None, {'user': user.link_id})
    url_user = data.url_user
    self.assertEqual(user.key(), url_user.key())


class UrlProfilePropertyTest(unittest.TestCase):
  """Unit tests for url_profile property of RequestData class."""

  def testNoProfileData(self):
    """Tests that error is raised if there is no profile data in kwargs."""
    # no data at all
    data = request_data.RequestData(None, None, {})
    with self.assertRaises(ValueError):
      data.url_profile
    
    # program data but no user identifier
    kwargs = {
        'sponsor': 'sponsor_id',
        'program': 'program_id'
        }
    data = request_data.RequestData(None, None, kwargs)
    with self.assertRaises(ValueError):
      data.url_profile

    # user identifier present but no program data
    data = request_data.RequestData(None, None, {'user': 'user_id'})
    with self.assertRaises(ValueError):
      data.url_profile    

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
    sponsor = seeder_logic.seed(sponsor_model.Sponsor)
    program = seeder_logic.seed(program_model.Program)
    user = seeder_logic.seed(user_model.User)
    profile_properties = {
        'key_name': '%s/%s/%s' % 
            (sponsor.link_id, program.program_id, user.link_id),
        'parent': user,
        'link_id': user.link_id
        }
    profile = seeder_logic.seed(profile_model.Profile, profile_properties)

    kwargs = {
        'sponsor': sponsor.link_id,
        'program': program.program_id,
        'user': profile.link_id
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
    with self.assertRaises(ValueError):
      data.url_org

    # program data but no user identifier
    kwargs = {
        'sponsor': 'sponsor_id',
        'program': 'program_id'
        }
    data = request_data.RequestData(None, None, kwargs)
    with self.assertRaises(ValueError):
      data.url_org

    # user identifier present but no program data
    data = request_data.RequestData(None, None, {'organization': 'org_id'})
    with self.assertRaises(ValueError):
      data.url_org

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
    sponsor = seeder_logic.seed(sponsor_model.Sponsor)
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
    with self.assertRaises(ValueError):
      data.url_connection

    # program and connection data but no user identifier
    kwargs = {
        'sponsor': 'sponsor_id',
        'program': 'program_id',
        'id': '1',
        }
    data = request_data.RequestData(None, None, kwargs)
    with self.assertRaises(ValueError):
      data.url_connection

    # profile data but no connection identifier
    kwargs = {
        'sponsor': 'sponsor_id',
        'program': 'program_id',
        'user': 'user_id',
        }
    data = request_data.RequestData(None, None, kwargs)
    with self.assertRaises(ValueError):
      data.url_connection

    # only connection id
    kwargs = {'id': '1'}
    data = request_data.RequestData(None, None, kwargs)
    with self.assertRaises(ValueError):
      data.url_connection

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
    sponsor = seeder_logic.seed(sponsor_model.Sponsor)
    program = seeder_logic.seed(program_model.Program)
    user = seeder_logic.seed(user_model.User)
    profile_properties = {
        'key_name': '%s/%s/%s' % 
            (sponsor.link_id, program.program_id, user.link_id),
        'parent': user,
        'link_id': user.link_id
        }
    profile = seeder_logic.seed(profile_model.Profile, profile_properties)
    connection_properties = {'parent': profile}
    connection = seeder_logic.seed(connection_model.Connection,
        connection_properties)

    kwargs = {
        'sponsor': sponsor.link_id,
        'program': program.program_id,
        'user': profile.link_id,
        'id': str(connection.key().id())
        }
    data = request_data.RequestData(None, None, kwargs)
    url_connection = data.url_connection
    self.assertEqual(connection.key(), url_connection.key())