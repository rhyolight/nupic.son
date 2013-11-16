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

"""Unit tests for participants view."""

from tests import profile_utils
from tests import test_utils


class MentorsListAdminPageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for MentorsListAdminPage view."""

  def setUp(self):
    self.init()
    self.url = '/gsoc/admin/list/mentors/%s' % self.gsoc.key().name()

  def _assertPageTemplatesUsed(self, response):
    """Asserts that all the required templates to render the page were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/participants/base.html')
    self.assertTemplateUsed(
        response, 'modules/gsoc/participants/_mentors_list.html')
    self.assertTemplateUsed(response, 'soc/list/lists.html')
    self.assertTemplateUsed(response, 'soc/list/list.html')

  def testLoneUserAccessForbidden(self):
    response = self.get(self.url)
    self.assertErrorTemplatesUsed(response)

  def testMentorAccessForbidden(self):
    self.profile_helper.createMentor(self.org)
    response = self.get(self.url)
    self.assertErrorTemplatesUsed(response)
    self.assertResponseForbidden(response)

  def testOrgAdminAccessForbidden(self):
    self.profile_helper.createOrgAdmin(self.org)
    response = self.get(self.url)
    self.assertErrorTemplatesUsed(response)
    self.assertResponseForbidden(response)

  def testStudentAccessForbidden(self):
    self.profile_helper.createStudent()
    response = self.get(self.url)
    self.assertErrorTemplatesUsed(response)
    self.assertResponseForbidden(response)

  def testHostAccessGranted(self):
    self.profile_helper.createHost()
    response = self.get(self.url)
    self._assertPageTemplatesUsed(response)

  def testMentorsAreDisplayed(self):
    self.profile_helper.createHost()

    # seed a couple of mentors
    profile_utils.GSoCProfileHelper(self.gsoc, False).createMentor(self.org)
    profile_utils.GSoCProfileHelper(self.gsoc, False).createMentor(self.org)
    profile_utils.GSoCProfileHelper(self.gsoc, False).createMentor(self.org)

    response = self.get(self.url)
    self._assertPageTemplatesUsed(response)
    list_data = self.getListData(self.url, 0)

    #The only organization is self.gsoc
    self.assertEqual(3, len(list_data))
