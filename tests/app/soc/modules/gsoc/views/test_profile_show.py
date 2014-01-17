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

"""Tests for GSoC read only profile page related views."""

from tests import profile_utils
from tests.profile_utils import GSoCProfileHelper
from tests.test_utils import GSoCDjangoTestCase


class ProfileAdminPageTest(GSoCDjangoTestCase):
  """Tests the view related to readonly profile page."""

  def setUp(self):
    self.init()

  def assertProfileShowPageTemplatesUsed(self, response):
    """Asserts that correct templates were used to render the view.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/profile_show/base.html')
    self.assertTemplateUsed(response, 'modules/gsoc/_readonly_template.html')

  def testAUserNotLoggedInIsRedirectedToLoginPage(self):
    """Tests that a user who is not logged in and trying to access its profile
    is redirected to a login page.
    """
    profile = profile_utils.seedGSoCProfile(self.program)
    import os
    current_logged_in_account = os.environ.get('USER_EMAIL', None)
    try:
      os.environ['USER_EMAIL'] = ''
      url = '/gsoc/profile/admin/' + profile.key().name()
      response = self.get(url)
      self.assertResponseRedirect(response)
      expected_redirect_url = 'https://www.google.com/accounts/Login?' + \
          'continue=http%3A//some.testing.host.tld' + url
      actual_redirect_url = response.get('location', None)
      self.assertEqual(expected_redirect_url, actual_redirect_url)
    finally:
      if current_logged_in_account is None:
        del os.environ['USER_EMAIL']
      else:
        os.environ['USER_EMAIL'] = current_logged_in_account

  def testANormalUserCanNotAccessItsAdminProfileUrl(self):
    """Tests that a normal user can not access the its admin profile url.
    """
    self.profile_helper.createStudent()
    url = '/gsoc/profile/admin/'+self.profile_helper.profile.key().name()
    response = self.get(url)
    self.assertResponseForbidden(response)

    self.profile_helper.deleteProfile().createMentor(self.org)
    response = self.get(url)
    self.assertResponseForbidden(response)

    self.profile_helper.createOrgAdmin(self.org)
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testOnlyAHostCanAccessTheAdminProfilePage(self):
    """Tests that only the host is allowed to access profile pages."""
    mentor = profile_utils.seedGSoCProfile(
        self.program, mentor_for=[self.org.key.to_old_key()])
    student = GSoCProfileHelper(self.gsoc, self.dev_test)
    student.createOtherUser('student@example.com')
    student.createStudentWithProject(self.org, mentor)

    url = '/gsoc/profile/admin/' + student.profile.key().name()

    self.profile_helper.createStudent()
    response = self.get(url)
    self.assertResponseForbidden(response)

    self.profile_helper.deleteProfile().createMentor(self.org)
    response = self.get(url)
    self.assertResponseForbidden(response)

    self.profile_helper.createOrgAdmin(self.org)
    response = self.get(url)
    self.assertResponseForbidden(response)

    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    response = self.get(url)
    self.assertResponseOK(response)
    self.assertProfileShowPageTemplatesUsed(response)

    context = response.context
    self.assertIn('page_name', context)
    self.assertIn('program_name', context)
    self.assertIn('profile', context)
    self.assertIn('user', context)
    self.assertIn('links', context)
    self.assertIn('css_prefix', context)
    self.assertIn('submit_tax_link', context)
    self.assertIn('submit_enrollment_link', context)

    self.assertEqual(1, len(context['links']))

    expected_page_name = '%s Profile - %s' % (
        self.profile_helper.program.short_name, student.profile.name())
    actual_page_name = context['page_name']
    self.assertEqual(expected_page_name, actual_page_name)

    expected_program_name = self.profile_helper.program.name
    actual_program_name = context['program_name']
    self.assertEqual(expected_program_name, actual_program_name)
