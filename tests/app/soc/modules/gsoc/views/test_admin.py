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

"""Tests for admin dashboard view."""

from tests import profile_utils
from tests.profile_utils import GSoCProfileHelper
from tests.test_utils import GSoCDjangoTestCase


class AdminDashboardTest(GSoCDjangoTestCase):
  """Tests admin dashboard page.
  """

  def setUp(self):
    self.init()

  def adminDashboardContext(self):
    url = '/gsoc/admin/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertResponseOK(response)
    return response.context

  def assertAdminBaseTemplatesUsed(self, response):
    """Asserts that all the templates from the admin page were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/admin/base.html')

  def assertDashboardTemplatesUsed(self, response):
    """Asserts that all the templates to render a dashboard were used.
    """
    self.assertAdminBaseTemplatesUsed(response)
    self.assertTemplateUsed(response, 'soc/dashboard/base.html')

  def assertUserActionsTemplatesUsed(self, response):
    """Asserts that all the templates to render user actions were used.
    """
    self.assertAdminBaseTemplatesUsed(response)

  def testAdminDashboard(self):
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    url = '/gsoc/admin/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertDashboardTemplatesUsed(response)
    self.assertUserActionsTemplatesUsed(response)

    context = self.adminDashboardContext()
    self.assertIn('dashboards', context)

    # dashboards template context
    for dashboard in context['dashboards']:
      dashboard_context = dashboard.context()
      self.assertIn('title', dashboard_context)
      self.assertIn('name', dashboard_context)
      self.assertIn('subpages', dashboard_context)
      subpages = dashboard_context['subpages']
      self.assertTrue(2 == len(subpages))

    self.assertIn('page_name', context)


class LookupProfileTest(GSoCDjangoTestCase):
  """Test lookup profile page
  """

  def setUp(self):
    self.init()

  def assertLookupProfile(self, response):
    """Asserts that all templates from the lookup profile page were used
    and all contexts were passed
    """
    self.assertIn('base_layout', response.context)
    self.assertResponseOK(response)
    self.assertGSoCTemplatesUsed(response)
    self.assertEqual(response.context['base_layout'],
        'modules/gsoc/base.html')

    self.assertTemplateUsed(response, 'modules/gsoc/admin/lookup.html')

  def testLookupProfile(self):
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    # rendered with default base layout
    url = '/gsoc/admin/lookup/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertLookupProfile(response)

    post_url = '/gsoc/admin/lookup/' + self.gsoc.key().name()
    postdata = {}

    # invalid post data submitted to lookup form
    response = self.post(post_url, postdata)
    self.assertResponseOK(response)
    self.assertTrue(response.context['error'])

    # valid post data submitted to lookup form
    profile = profile_utils.seedNDBProfile(self.program.key())
    postdata = {'user_id': profile.profile_id}
    response = self.post(post_url, postdata)

    new_url = '/gsoc/profile/admin/%s/%s' % (
        self.gsoc.key().name(), profile.profile_id)
    self.assertResponseRedirect(response, new_url)

    response = self.post(post_url, {})
    self.assertResponseOK(response)
    self.assertTrue(response.context['error'])
    self.assertLookupProfile(response)

    # submit valid data to lookup form
    response = self.post(post_url, postdata)
    new_url = '/gsoc/profile/admin/%s/%s' % (
        self.gsoc.key().name(), profile.profile_id)
    self.assertResponseRedirect(response, new_url)


class ProposalsPageTest(GSoCDjangoTestCase):
  """Test proposals list page for admin
  """

  def setUp(self):
    self.init()

  def assertProposalsPage(self, response):
    """Asserts that all the templates from the submitted proposals list
    were used and all contexts were passed.
    """
    self.assertIn('base_layout', response.context)
    self.assertGSoCTemplatesUsed(response)
    self.assertEqual(response.context['base_layout'],
        'modules/gsoc/base.html')

    self.assertTemplateUsed(response, 'modules/gsoc/admin/list.html')
    self.assertTemplateUsed(response,
        'modules/gsoc/admin/_proposals_list.html')

  def testListProposals(self):
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    self.timeline_helper.studentSignup()

    url = '/gsoc/admin/proposals/' + self.org.key.id()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertProposalsPage(response)

    response = self.getListResponse(url, 0)
    self.assertIsJsonResponse(response)
    data = response.context['data']['']
    self.assertEqual(0, len(data))

    # test list with student's proposal
    self.mentor = GSoCProfileHelper(self.gsoc, self.dev_test)
    self.mentor.createMentor(self.org)
    self.profile_helper.createStudentWithProposals(
        self.org, self.mentor.profile, 1)
    response = self.getListResponse(url, 0)
    self.assertIsJsonResponse(response)
    data = response.context['data']['']
    self.assertEqual(1, len(data))
