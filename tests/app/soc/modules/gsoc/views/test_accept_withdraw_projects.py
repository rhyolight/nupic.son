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

"""Unit tests for manage projects related views."""

from tests import test_utils


class AcceptProposalsTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for AcceptProposals view."""

  def setUp(self):
    self.init()
    self.url = '/gsoc/admin/proposals/accept/%s' % self.gsoc.key().name()

  def _assertTemplatesUsed(self, response):
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response,
        'v2/modules/gsoc/accept_withdraw_projects/_project_list.html')
    self.assertTemplateUsed(response,
        'v2/modules/gsoc/accept_withdraw_projects/base.html')
    self.assertTemplateUsed(response, 'soc/_program_select.html') 
    self.assertTemplateUsed(response, 'soc/list/lists.html') 
    self.assertTemplateUsed(response, 'soc/list/list.html')

  def testLoneUserAccessForbidded(self):
    """Tests that a lone user cannot access the page."""
    self.data.createUser()
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testStudentAccessForbidded(self):
    """Tests that a student cannot access the page."""
    self.data.createStudent()
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testMentorAccessForbidded(self):
    """Tests that a mentor cannot access the page."""
    self.data.createMentor(self.org)
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testOrgAdminAccessForbidded(self):
    """Tests that an organization admin cannot access the page."""
    self.data.createOrgAdmin(self.org)
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testHostAccessGranted(self):
    """Tests that a program admin can access the page."""
    self.data.createHost()
    response = self.get(self.url)
    self.assertResponseOK(response)
    self._assertTemplatesUsed(response)
