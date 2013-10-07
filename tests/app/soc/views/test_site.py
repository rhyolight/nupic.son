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
    # TODO(daniel): eliminate it when page is publicly accessible
    user = profile_utils.seedUser(is_developer=True)
    profile_utils.login(user)

    site_properties = {'key_name': 'site'}
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

    response = self.get('/landing_page')
    self.assertResponseOK(response)    
    self._assertPageTemplatesUsed(response)

  def testOneLatestProgram(self):
    """Tests that redirect response is returned for one defined program."""
    self.site.latest_gsoc = self.gsoc_program.key().name()
    self.site.latest_gci = None
    self.site.put()

    response = self.get('/landing_page')
    self.assertResponseRedirect(response)

    self.site.latest_gsoc = None
    self.site.latest_gci = self.gci_program.key().name()
    self.site.put()

    response = self.get('/landing_page')
    self.assertResponseRedirect(response)

  def testTwoLatestPrograms(self):
    """Tests that redirect response is returned for one defined program."""
    self.site.latest_gsoc = self.gsoc_program.key().name()
    self.site.latest_gci = self.gci_program.key().name()
    self.site.put()

    response = self.get('/landing_page')
    self.assertResponseOK(response)