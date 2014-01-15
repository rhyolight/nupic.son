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

from summerofcode.templates import tabs

from tests import profile_utils
from tests.profile_utils import GSoCProfileHelper
from tests.test_utils import GSoCDjangoTestCase


class ProfileShowPageTest(GSoCDjangoTestCase):
  """Tests the view for read only profile show page."""

  def setUp(self):
    self.init()

  def _viewProfileUrl(self):
    """Returns URL for View Profile page.

    Returns:
      URL for View Profile page.
    """
    return '/gsoc/profile/show/' + self.gsoc.key().name()

  def assertProfileShowTemplateUsed(self, response):
    """Asserts that correct templates were used to render the view.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/profile_show/base.html')
    self.assertTemplateUsed(response, 'modules/gsoc/_readonly_template.html')

  def testUserWithoutAProfileCanNotAccessItsProfile(self):
    """Tests that a user which has no profile can not access its profile.
    """
    self.profile_helper.createUser()
    response = self.get(self._viewProfileUrl())
    self.assertResponseForbidden(response)

  def testAUserNotLoggedInIsRedirectedToLoginPage(self):
    """Tests that a user who is not logged in and trying to access its profile
    is redirected to a login page.
    """
    import os
    current_logged_in_account = os.environ.get('USER_EMAIL', None)
    try:
      os.environ['USER_EMAIL'] = ''
      response = self.get(self._viewProfileUrl())
      expected_redirect_url = 'https://www.google.com/accounts/Login?' + \
          'continue=http%3A//some.testing.host.tld' + self._viewProfileUrl()
      actual_redirect_url = response.get('location', None)
      self.assertResponseRedirect(response)
      self.assertEqual(expected_redirect_url, actual_redirect_url)
    finally:
      if current_logged_in_account is None:
        del os.environ['USER_EMAIL']
      else:
        os.environ['USER_EMAIL'] = current_logged_in_account

  def testAStudentWithAProfileCanAccessItsProfilePage(self):
    """Tests that a logged in student with a profile can access its profile page.
    """
    self.profile_helper.createStudent()
    response = self.get(self._viewProfileUrl())
    self.assertResponseOK(response)
    self.assertProfileShowTemplateUsed(response)

    context = response.context
    self.assertIn('page_name', context)
    self.assertIn('program_name', context)
    self.assertIn('profile', context)
    self.assertIn('css_prefix', context)
    self.assertNotIn('submit_tax_link', context)
    self.assertNotIn('submit_enrollment_link', context)

    expected_page_name = '%s Profile - %s' % (
        self.profile_helper.program.short_name,
        self.profile_helper.profile.name())
    actual_page_name = context['page_name']
    self.assertEqual(expected_page_name, actual_page_name)

    expected_program_name = self.profile_helper.program.name
    actual_program_name = context['program_name']
    self.assertEqual(expected_program_name, actual_program_name)

  def testProfileTabs(self):
    """Tests that correct profile related tabs are present in context."""
    self.timeline_helper.orgsAnnounced()
    self.profile_helper.createProfile()

    response = self.get(self._viewProfileUrl())

    # check that tabs are present in context
    self.assertIn('tabs', response.context)

    # check that tab to "Edit Profile" page is the selected one
    self.assertEqual(response.context['tabs'].selected_tab_id,
        tabs.VIEW_PROFILE_TAB_ID)


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
