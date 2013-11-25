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

"""Tests for base templates. All the templates are tested on homepage.
"""


from tests.test_utils import GSoCDjangoTestCase


class BaseTemplatesOnHomePageViewTest(GSoCDjangoTestCase):
  """Tests base templates on home page.
  """

  def setUp(self):
    self.init()

  def assertMainMenuCommonLinks(self, mainmenu_context):
    self.assertIn('home_link', mainmenu_context)
    self.assertIn('search_link', mainmenu_context)
    self.assertIn('about_link', mainmenu_context)
    self.assertIn('events_link', mainmenu_context)
    self.assertIn('connect_link', mainmenu_context)
    self.assertIn('help_link', mainmenu_context)
    self.assertIn('logout_link', mainmenu_context)

  def testMainMenuDuringKickoff(self):
    """Tests the main menu before the org signup period.
    """
    self.timeline_helper.kickoff()
    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    mainmenu_context = response.context['mainmenu'].context()

    self.assertMainMenuCommonLinks(mainmenu_context)

    self.assertNotIn('projects_link', mainmenu_context)

    # No profile.
    self.assertNotIn('dashboard_link', mainmenu_context)

    # Create profile.
    self.profile_helper.createProfile()
    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    mainmenu_context = response.context['mainmenu'].context()

    self.assertMainMenuCommonLinks(mainmenu_context)
    self.assertIn('dashboard_link', mainmenu_context)

    # Make the current user the host.
    self.profile_helper.createHost()
    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    mainmenu_context = response.context['mainmenu'].context()

    self.assertMainMenuCommonLinks(mainmenu_context)
    self.assertIn('dashboard_link', mainmenu_context)
    self.assertIn('admin_link', mainmenu_context)

  def testMainMenuDuringOrgSignup(self):
    """Tests the main menu during the org signup period.
    """
    self.timeline_helper.orgSignup()
    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    mainmenu_context = response.context['mainmenu'].context()

    self.assertMainMenuCommonLinks(mainmenu_context)

    self.assertNotIn('projects_link', mainmenu_context)

  def testMainMenuDuringOrgsAnnounced(self):
    """Tests the main menu after organizations have been announced.
    """
    self.timeline_helper.orgsAnnounced()
    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    mainmenu_context = response.context['mainmenu'].context()

    self.assertMainMenuCommonLinks(mainmenu_context)

    self.assertNotIn('projects_link', mainmenu_context)

  def testMainMenuDuringStudentSignup(self):
    """Tests the main menu during student signup period.
    """
    self.timeline_helper.studentSignup()
    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    mainmenu_context = response.context['mainmenu'].context()

    self.assertMainMenuCommonLinks(mainmenu_context)

    self.assertNotIn('projects_link', mainmenu_context)

  def testMainMenuPostStudentSignup(self):
    """Tests the main menu after student signup period i.e. during proposal
    ranking phase.
    """
    self.timeline_helper.postStudentSignup()
    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    mainmenu_context = response.context['mainmenu'].context()

    self.assertMainMenuCommonLinks(mainmenu_context)

    self.assertNotIn('projects_link', mainmenu_context)

  def testMainMenuPostStudentsAnnounced(self):
    """Tests the main menu after accepted students have been announced.
    """
    self.timeline_helper.studentsAnnounced()
    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    mainmenu_context = response.context['mainmenu'].context()

    self.assertMainMenuCommonLinks(mainmenu_context)
    self.assertIn('projects_link', mainmenu_context)
