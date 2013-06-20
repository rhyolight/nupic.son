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

"""Unit tests for lists of GCITask entities.
"""


from tests.test_utils import GCIDjangoTestCase


class AllOrganizationTasksPageTest(GCIDjangoTestCase):
  """Unit tests for AllOrganizationTasksPage.
  """

  def setUp(self):
    self.init()
    self.url = '/gci/org/tasks/all/' + self.org.key().name()

  def assertPageTemplatesUsed(self, response):
    """Asserts that all the required templates to render the page were used.
    """
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gci/task/task_list.html')
    self.assertTemplateUsed(
        response, 'modules/gci/task/_task_list.html')
    self.assertTemplateUsed(response, 'soc/list/lists.html')
    self.assertTemplateUsed(response, 'soc/list/list.html')

  def testNonLoggedInCannotAccess(self):
    response = self.get(self.url)
    self.assertErrorTemplatesUsed(response)
    self.assertResponseForbidden(response)

  def testMentorCannotAccess(self):
    self.data.createMentor(self.org)
    response = self.get(self.url)
    self.assertErrorTemplatesUsed(response)
    self.assertResponseForbidden(response)

  def testOrgAdminCannotAccess(self):
    self.data.createOrgAdmin(self.org)
    response = self.get(self.url)
    self.assertErrorTemplatesUsed(response)
    self.assertResponseForbidden(response)

  def testStudentCannotAccess(self):
    self.data.createStudent()
    response = self.get(self.url)
    self.assertErrorTemplatesUsed(response) 
    self.assertResponseForbidden(response)   

  def testHostCanAccess(self):
    self.data.createHost()
    response = self.get(self.url)
    self.assertPageTemplatesUsed(response)
    self.assertResponseOK(response);
