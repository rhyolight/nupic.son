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

"""Tests for site related views."""

import httplib

from soc.models import program as program_model
from soc.models import site as site_model
from soc.modules.gci.models import program as gci_program_model
from soc.modules.gsoc.models import program as gsoc_program_model
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests import profile_utils
from tests import test_utils


class LandingPageTest(test_utils.DjangoTestCase):
  """Unit tests for LandingPage class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.user = profile_utils.seedUser()
    profile_utils.login(self.user)

    site_properties = {
        'key_name': 'site',
        'maintenance_mode': False
        }
    self.site = seeder_logic.seed(site_model.Site, properties=site_properties)

    self.gsoc_program = seeder_logic.seed(gsoc_program_model.GSoCProgram)
    self.gci_program = seeder_logic.seed(gci_program_model.GCIProgram)

  def _assertPageTemplatesUsed(self, response):
    """Asserts that all templates for the tested page are used."""
    self.assertTemplateUsed(
        response, 'melange/landing_page/_program_section.html')
    self.assertTemplateUsed(
        response, 'melange/landing_page/_contact_us_section.html')

  def testPageLoads(self):
    """Tests that page loads correctly."""
    self.site.latest_gsoc = self.gsoc_program.key().name()
    self.site.latest_gci = self.gci_program.key().name()
    self.site.mailing_list = 'dev@test.com'
    self.site.put()

    response = self.get('/')
    self.assertResponseOK(response)    
    self._assertPageTemplatesUsed(response)

  def testOneLatestProgram(self):
    """Tests that redirect response is returned for one defined program."""
    self.site.latest_gsoc = self.gsoc_program.key().name()
    self.site.latest_gci = None
    self.site.put()

    response = self.get('/')
    self.assertResponseRedirect(response)

    self.site.latest_gsoc = None
    self.site.latest_gci = self.gci_program.key().name()
    self.site.put()

    response = self.get('/')
    self.assertResponseRedirect(response)

  def testTwoLatestPrograms(self):
    """Tests that redirect response is returned for one defined program."""
    self.site.latest_gsoc = self.gsoc_program.key().name()
    self.site.latest_gci = self.gci_program.key().name()
    self.site.put()

    response = self.get('/')
    self.assertResponseOK(response)

  def testMaintenanceMode(self):
    """Tests that page is accessible only to developers when in maintenance."""
    self.site.latest_gsoc = self.gsoc_program.key().name()
    self.site.latest_gci = self.gci_program.key().name()
    self.site.put()

    # the page should is in maintenance mode
    self.site.maintenance_mode = True
    self.site.put()

    # check that page is not accessible for non-developers
    response = self.get('/')
    self.assertResponseCode(response, httplib.SERVICE_UNAVAILABLE)

    self.user.is_developer = True
    self.user.put()
    response = self.get('/')
    self.assertResponseOK(response)


TEST_DESCRIPTION = 'Test description of the site.'

class EditSitePageTest(test_utils.DjangoTestCase):
  """Unit tests for EditSitePage class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

    # TODO (daniel): Edit Site Page should work without an active program
    program = seeder_logic.seed(program_model.Program)

    site_properties = {
        'key_name': 'site',
        'active_program': program,
        'tos': None,
        }
    self.site = seeder_logic.seed(site_model.Site, properties=site_properties)

  def testPageLoads(self):
    """Tests that page loads properly."""
    user = profile_utils.seedUser(is_developer=True)
    profile_utils.login(user)

    response = self.get('/site/edit')
    self.assertResponseOK(response)

  def testUpdateSettings(self):
    """Tests that site settings are updated properly."""
    user = profile_utils.seedUser(is_developer=True)
    profile_utils.login(user)

    postdata = {
        'description': TEST_DESCRIPTION,
        'active_program': self.site.active_program.key()
        }
    response = self.post('/site/edit', postdata=postdata)
    self.assertResponseRedirect(response, url='/site/edit')

    site = site_model.Site.get_by_key_name('site')
    self.assertEqual(site.description, TEST_DESCRIPTION)
