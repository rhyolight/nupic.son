# Copyright 2012 the Melange authors.
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

"""Tests of soc.logic.linker."""

import unittest
import urllib

from melange.request import links
from melange.views.helper import urls

from soc.models import organization as org_model
from soc.models import profile as profile_model
from soc.models import program as program_model
from soc.modules.gci.views.helper import url_names as gci_url_names
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from summerofcode.views.helper import urls as soc_urls

from tests import profile_utils
from tests import program_utils


class _PathOnlyMockHttpRequest(object):
  """A mock HttpRequest supporting only the get_full_path method.

  Why Django doesn't provide an instantiable HttpRequest
  implementation is completely beyond me.
  """

  def __init__(self, path):
    """Creates a _PathOnlyMockHttpRequest.

    Args:
      path: Any string intended to represent the path portion of
        a requested URL.
    """
    self._path = path

  def get_full_path(self):
    """See http.HttpRequest.get_full_path for specification."""
    return self._path


# TODO(daniel): this class is on a non-specific level, but it refers
# to GCI specific names. Make it generic.
class TestLinker(unittest.TestCase):
  """Tests the Linker class."""

  def setUp(self):
    self.linker = links.Linker()

  def testLogin(self):
    """Tests that some reasonable value is created by Linker.login."""
    test_path = '/a/fake/test/path'
    # NOTE(nathaniel): The request parameter and value are just here
    # for coverage; I don't actually have sufficient familiarity with
    # them to assert that their quoting and escaping are completely
    # correct.
    test_arg = 'some_test_arg'
    test_arg_value = 'some_test_value'

    request = _PathOnlyMockHttpRequest(
        '%s?%s=%s' % (test_path, test_arg, test_arg_value))
    login_url = self.linker.login(request)
    self.assertIn(test_path, login_url)
    self.assertIn(
        urllib.quote('%s=%s' % (test_arg, test_arg_value)), login_url)

  def testLogout(self):
    """Tests that some reasonable value is created by Linker.logout."""
    test_path = 'a/fake/test/path/to/visit/after/logout'
    request = _PathOnlyMockHttpRequest(test_path)
    logout_path = self.linker.logout(request)
    self.assertIn(test_path, logout_path)

  def testSite(self):
    self.assertEqual('/site/edit', self.linker.site('edit_site_settings'))

  def testProfile(self):
    # seed a program
    program = program_utils.seedProgram()

    # seed a profile
    profile = profile_utils.seedNDBProfile(program.key())

    self.assertEqual(
        '/gci/profile/show/%s/%s' % (
            profile.program.id(), profile.key.parent().id()),
        self.linker.profile(profile, gci_url_names.GCI_PROFILE_SHOW_ADMIN))

  def testProgram(self):
    """Tests program function."""
    program = program_utils.seedProgram()
    self.assertEqual(
        '/gci/homepage/%s' % program.key().name(),
        self.linker.program(program, 'gci_homepage'))

  def testSponsor(self):
    """Tests sponsor function."""
    sponsor = program_utils.seedSponsor()
    self.assertEqual(
        '/gci/program/create/%s' % sponsor.key().name(),
        self.linker.sponsor(sponsor, 'gci_program_create'))

  def testUser(self):
    """Tests user function."""
    # seed a user
    user = profile_utils.seedNDBUser()

    self.assertEqual(
        '/site/settings/user/%s' % user.key.id(),
        self.linker.user(user, urls.UrlNames.USER_SETTINGS))

  def testUserOrg(self):
    """Tests userOrg function."""
    # seed a program
    program = seeder_logic.seed(program_model.Program)
    program.program_id = program.link_id
    program.sponsor = program.scope

    # seed a user
    user = profile_utils.seedUser()

    # seed a profile
    profile_properties = {
        'program': program,
        'scope': program,
        'parent': user
        }
    profile = seeder_logic.seed(profile_model.Profile, profile_properties)

    # seed an organization
    org = seeder_logic.seed(org_model.Organization)

    self.assertEqual(
        '/gci/student_tasks_for_org/%s/%s/%s' % (profile.program.key().name(),
            profile.parent_key().name(), org.link_id),
        self.linker.userOrg(
            profile, org, gci_url_names.GCI_STUDENT_TASKS_FOR_ORG))

  def testUserId(self):
    """Tests userId function."""
    # seed a program
    program = seeder_logic.seed(program_model.Program)
    program.program_id = program.link_id
    program.sponsor = program.scope

    profile = profile_utils.seedProfile(program)

    self.assertEqual(
        '/gsoc/project/manage/admin/%s/%s/%s' % (
            profile.program.key().name(),
            profile.parent_key().name(), 42),
        self.linker.userId(
            profile.key(), 42, soc_urls.UrlNames.PROJECT_MANAGE_ADMIN))

  def testOrganization(self):
    """Tests organization function."""
    # seed a program
    program = seeder_logic.seed(program_model.Program)
    program.program_id = program.link_id
    program.sponsor = program.scope

    # seed an organization
    org_properties = {
        'scope': program,
        'program': program
        }
    organization = seeder_logic.seed(
        org_model.Organization, properties=org_properties)

    url = self.linker.organization(
        organization.key(), soc_urls.UrlNames.ORG_PROFILE_EDIT)
    self.assertEqual(
        '/gsoc/org/profile/edit/%s' % organization.key().name(), url)
