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

"""Tests the view for GSoC accepted organizations."""

from tests import profile_utils
from tests import test_utils


class AcceptedOrgsAdminPageTest(test_utils.GSoCDjangoTestCase):
  """Tests the page to display accepted organizations for admins."""

  def setUp(self):
    self.init()
    self.url = '/gsoc/admin/accepted_orgs/' + self.gsoc.key().name()

  def assertAcceptedOrgsPageTemplatesUsed(self, response):
    """Asserts that all the required templates to render the page were used."""
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response,
        'modules/gsoc/admin/list.html')
    self.assertTemplateUsed(response,
        'modules/gsoc/admin/_accepted_orgs_list.html')
    self.assertTemplateUsed(response, 'soc/list/lists.html')
    self.assertTemplateUsed(response, 'soc/list/list.html')

  def testPageForbiddenForLoneUsers(self):
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testPageForbiddenForStudents(self):
    self.profile_helper.createStudent()
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testPageForbiddenForMentors(self):
    self.profile_helper.createMentor(self.org)
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testPageForbiddenForOrgAdmins(self):
    self.profile_helper.createOrgAdmin(self.org)
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testPageAccessibleForHosts(self):
    self.profile_helper.createHost()
    response = self.get(self.url)
    self.assertResponseOK(response)
    self.assertAcceptedOrgsPageTemplatesUsed(response)
