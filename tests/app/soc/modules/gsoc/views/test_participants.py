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


NUMBER_OF_MENTORS = 3

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
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, mentor_for=[self.org.key])

    response = self.get(self.url)
    self.assertErrorTemplatesUsed(response)
    self.assertResponseForbidden(response)

  def testOrgAdminAccessForbidden(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[self.org.key])

    response = self.get(self.url)
    self.assertErrorTemplatesUsed(response)
    self.assertResponseForbidden(response)

  def testStudentAccessForbidden(self):
    self.profile_helper.createStudent()
    response = self.get(self.url)
    self.assertErrorTemplatesUsed(response)
    self.assertResponseForbidden(response)

  def testHostAccessGranted(self):
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    response = self.get(self.url)
    self._assertPageTemplatesUsed(response)

  def testMentorsAreDisplayed(self):
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    # seed a couple of mentors
    for _ in range(NUMBER_OF_MENTORS):
      profile_utils.seedNDBProfile(
          self.program.key(), mentor_for=[self.org.key])

    response = self.get(self.url)
    self._assertPageTemplatesUsed(response)
    list_data = self.getListData(self.url, 0)

    # The only organization is self.gsoc
    self.assertEqual(NUMBER_OF_MENTORS, len(list_data))
