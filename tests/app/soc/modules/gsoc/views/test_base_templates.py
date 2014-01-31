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

"""Tests for base templates. All the templates are tested on homepage."""

from google.appengine.ext import ndb

from tests import profile_utils
from tests.test_utils import GSoCDjangoTestCase

# A dict from names of links in the main menu to boolean values of whether
# or not they are "safe" to follow in a test (the logout link will log out
# the user and thus alter the test environment).
MAIN_MENU_COMMON_LINK_NAMES = {
    'home_link': True,
    'search_link': True,
    'about_link': True,
    'events_link': True,
    'connect_link': True,
    'help_link': True,
    'logout_link': False,
}


class BaseTemplatesOnHomePageViewTest(GSoCDjangoTestCase):
  """Tests base templates on home page."""

  def setUp(self):
    self.init()

  def assertMainMenuCommonLinks(self, mainmenu_context):
    """Confirms that each link in the main menu functions."""
    for link_name, follow in MAIN_MENU_COMMON_LINK_NAMES.iteritems():
      url = mainmenu_context.get(link_name, None)
      self.assertIsNotNone(url)
      if follow:
        response = self.get(url)
        self.assertResponseOK(response)

  def testMainMenuDuringKickoff(self):
    """Tests the main menu before the org signup period."""
    self.timeline_helper.kickoff()
    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    mainmenu_context = response.context['mainmenu'].context()

    self.assertMainMenuCommonLinks(mainmenu_context)

    self.assertNotIn('projects_link', mainmenu_context)

    # No profile.
    self.assertNotIn('dashboard_link', mainmenu_context)

    # Create profile.
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(self.program.key(), user=user)

    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    mainmenu_context = response.context['mainmenu'].context()

    self.assertMainMenuCommonLinks(mainmenu_context)
    self.assertIn('dashboard_link', mainmenu_context)

    # Make the current user the host.
    user.host_for = [ndb.Key.from_old_key(self.program.key())]
    profile_utils.loginNDB(user)

    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    mainmenu_context = response.context['mainmenu'].context()

    self.assertMainMenuCommonLinks(mainmenu_context)
    self.assertIn('dashboard_link', mainmenu_context)
    self.assertIn('admin_link', mainmenu_context)

  def testMainMenuDuringOrgSignup(self):
    """Tests the main menu during the org signup period."""
    self.timeline_helper.orgSignup()
    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    mainmenu_context = response.context['mainmenu'].context()

    self.assertMainMenuCommonLinks(mainmenu_context)

    self.assertNotIn('projects_link', mainmenu_context)

  def testMainMenuDuringOrgsAnnounced(self):
    """Tests the main menu after organizations have been announced."""
    self.timeline_helper.orgsAnnounced()
    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    mainmenu_context = response.context['mainmenu'].context()

    self.assertMainMenuCommonLinks(mainmenu_context)

    self.assertNotIn('projects_link', mainmenu_context)

  def testMainMenuDuringStudentSignup(self):
    """Tests the main menu during student signup period."""
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
    """Tests the main menu after accepted students have been announced."""
    self.timeline_helper.studentsAnnounced()
    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    mainmenu_context = response.context['mainmenu'].context()

    self.assertMainMenuCommonLinks(mainmenu_context)
    self.assertIn('projects_link', mainmenu_context)
