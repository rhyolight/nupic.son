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

"""Tests for base templates. All the templates will be tested on homepage.
"""


from tests.test_utils import GSoCDjangoTestCase


class BaseTemplatesOnHomePageViewTest(GSoCDjangoTestCase):
  """Tests base templates on home page.
  """

  def setUp(self):
    self.init()

  def assertMainMenuCommonLinks(self, mainmenu_context):
    self.assertTrue('home_link' in mainmenu_context)
    self.assertTrue('search_link' in mainmenu_context)
    self.assertTrue('about_link' in mainmenu_context)
    self.assertTrue('events_link' in mainmenu_context)
    self.assertTrue('connect_link' in mainmenu_context)
    self.assertTrue('help_link' in mainmenu_context)
    self.assertTrue('logout_link' in mainmenu_context)

  def testMainMenuDuringKickoff(self):
    """Tests the main menu before the org signup period.
    """
    self.timeline.kickoff()
    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    mainmenu_context = response.context['mainmenu'].context()

    self.assertMainMenuCommonLinks(mainmenu_context)

    self.assertTrue('accepted_orgs_link' not in mainmenu_context)
    self.assertTrue('projects_link' not in mainmenu_context)

    # No profile
    self.assertTrue('dashboard_link' not in mainmenu_context)

    # Create profile
    self.data.createProfile()
    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    mainmenu_context = response.context['mainmenu'].context()

    self.assertMainMenuCommonLinks(mainmenu_context)
    self.assertTrue('dashboard_link' in mainmenu_context)

    self.data.createHost()
    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    mainmenu_context = response.context['mainmenu'].context()

    self.assertMainMenuCommonLinks(mainmenu_context)
    self.assertTrue('dashboard_link' in mainmenu_context)
    self.assertTrue('admin_link' in mainmenu_context)

  def testMainMenuDuringOrgSignup(self):
    """Tests the main menu during the org signup period.
    """
    self.timeline.orgSignup()
    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    mainmenu_context = response.context['mainmenu'].context()

    self.assertMainMenuCommonLinks(mainmenu_context)

    self.assertTrue('accepted_orgs_link' not in mainmenu_context)
    self.assertTrue('projects_link' not in mainmenu_context)

  def testMainMenuDuringOrgsAnnounced(self):
    """Tests the main menu after organizations have been announced.
    """
    self.timeline.orgsAnnounced()
    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    mainmenu_context = response.context['mainmenu'].context()

    self.assertMainMenuCommonLinks(mainmenu_context)
    self.assertTrue('accepted_orgs_link' in mainmenu_context)

    self.assertTrue('projects_link' not in mainmenu_context)

  def testMainMenuDuringStudentSignup(self):
    """Tests the main menu during student signup period.
    """
    self.timeline.studentSignup()
    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    mainmenu_context = response.context['mainmenu'].context()

    self.assertMainMenuCommonLinks(mainmenu_context)
    self.assertTrue('accepted_orgs_link' in mainmenu_context)

    self.assertTrue('projects_link' not in mainmenu_context)

  def testMainMenuPostStudentSignup(self):
    """Tests the main menu after student signup period i.e. during proposal
    ranking phase.
    """
    self.timeline.postStudentSignup()
    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    mainmenu_context = response.context['mainmenu'].context()

    self.assertMainMenuCommonLinks(mainmenu_context)
    self.assertTrue('accepted_orgs_link' in mainmenu_context)

    self.assertTrue('projects_link' not in mainmenu_context)

  def testMainMenuPostStudentsAnnounced(self):
    """Tests the main menu after accepted students have been announced.
    """
    self.timeline.studentsAnnounced()
    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    mainmenu_context = response.context['mainmenu'].context()

    self.assertMainMenuCommonLinks(mainmenu_context)
    self.assertTrue('accepted_orgs_link' in mainmenu_context)
    self.assertTrue('projects_link' in mainmenu_context)
