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


"""Tests for organization score related views.
"""


from soc.modules.gci.models.organization import GCIOrganization

from tests.test_utils import GCIDjangoTestCase


class ChooseOrganizationForOrgScorePageTest(GCIDjangoTestCase):
  """Unit tests for ChooseOrganizationForOrgScorePage.
  """

  def setUp(self):
    self.init()
    self.url = '/gci/org_choose_for_score/' + self.gci.key().name()

  def assertPageTemplatesUsed(self, response):
    """Asserts that all the required templates to render the page were used.
    """
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gci/org_list/base.html')
    self.assertTemplateUsed(
        response, 'modules/gci/accepted_orgs/_project_list.html')
    self.assertTemplateUsed(response, 'soc/list/lists.html')
    self.assertTemplateUsed(response, 'soc/list/list.html')


  def testAccessAsNonHostFails(self):
    response = self.get(self.url)
    self.assertErrorTemplatesUsed(response)

  def testMentorCannotAccess(self):
    self.data.createMentor(self.org)
    response = self.get(self.url)
    self.assertErrorTemplatesUsed(response)

  def testOrgAdminCannotAccess(self):
    self.data.createOrgAdmin(self.org)
    response = self.get(self.url)
    self.assertErrorTemplatesUsed(response)

  def testStudentCannotAccess(self):
    self.data.createStudent()
    response = self.get(self.url)
    self.assertErrorTemplatesUsed(response)    

  def testHostCanAccess(self):
    self.data.createHost()
    response = self.get(self.url)
    self.assertPageTemplatesUsed(response)

  def testActiveOrgsAreDisplayed(self):
    self.data.createHost()

    org_properties = {
        'scope': self.gci, 'status': 'active', 'program': self.gci,
        'home': None, 'backup_winner': None,
    }
    self.seed(GCIOrganization, org_properties)
    self.seed(GCIOrganization, org_properties)

    response = self.get(self.url)
    self.assertPageTemplatesUsed(response)
    list_data = self.getListData(self.url, 0)

    #Third organization is self.gci
    self.assertEqual(3, len(list_data))

  def testNonActiveOrgsAreNotDisplayed(self):
    self.data.createHost()

    org_properties = {
        'scope': self.gci, 'status': 'invalid', 'program': self.gci,
        'home': None, 'backup_winner': None
    }
    self.seed(GCIOrganization, org_properties)
    self.seed(GCIOrganization, org_properties)

    response = self.get(self.url)
    self.assertPageTemplatesUsed(response)
    list_data = self.getListData(self.url, 0)

    #The only organization is self.gci
    self.assertEqual(1, len(list_data))
