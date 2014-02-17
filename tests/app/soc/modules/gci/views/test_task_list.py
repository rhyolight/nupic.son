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

"""Unit tests for lists of GCITask entities."""

from google.appengine.ext import ndb

from tests import profile_utils
from tests import task_utils
from tests.test_utils import GCIDjangoTestCase


_NUMBER_OF_TASKS = 2

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
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        mentor_for=[ndb.Key.from_old_key(self.org.key())])

    response = self.get(self.url)
    self.assertErrorTemplatesUsed(response)
    self.assertResponseForbidden(response)

  def testOrgAdminCannotAccess(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        admin_for=[ndb.Key.from_old_key(self.org.key())])

    response = self.get(self.url)
    self.assertErrorTemplatesUsed(response)
    self.assertResponseForbidden(response)

  def testStudentCannotAccess(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBStudent(self.program, user=user)

    response = self.get(self.url)
    self.assertErrorTemplatesUsed(response)
    self.assertResponseForbidden(response)

  def testHostCanAccess(self):
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    response = self.get(self.url)
    self.assertPageTemplatesUsed(response)
    self.assertResponseOK(response)

  def testPageLoads(self):
    """Tests that the page loads properly."""
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    # seed a couple of tasks
    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[ndb.Key.from_old_key(self.org.key())])
    for _ in range(_NUMBER_OF_TASKS):
      task_utils.seedTask(self.program, self.org, [mentor.key.to_old_key()])

    response = self.get(self.url)
    self.assertPageTemplatesUsed(response)
    self.assertResponseOK(response)

    response = self.getListResponse(self.url, 0)
    self.assertIsJsonResponse(response)
    data = response.context['data']['']
    self.assertEqual(len(data), _NUMBER_OF_TASKS)
