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

"""Tests for lists of SubscribedTasksPage view."""

from tests import profile_utils
from tests import task_utils
from tests import test_utils


_NUMBER_OF_SUBSCRIBED_TASKS = 3
_NUMBER_OF_NON_SUBSCRIBED_TASKS = 2

def _getSubscribedTasksUrl(program, user_id):
  """Returns URL to Subscribed Tasks page.

  Args:
    program: Program entity.
    user_id: User identifier.

  Returns:
    A string containing the URL to Subscribed Tasks page.
  """
  return '/gci/subscribed_tasks/%s/%s' % (program.key().name(), user_id)


class SubscribedTasksPageTest(test_utils.GCIDjangoTestCase):
  """Unit tests for SubscribedTasksPage."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

  def testSubscribedListAsLoneUser(self):
    """Tests that access for a user without a profile is denied."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)

    response = self.get(_getSubscribedTasksUrl(self.program, user.user_id))
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def assertSubscribedTasksTemplateUsed(self):
    """Tests that correct templates are used to render the page."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(self.program.key(), user=user)

    response = self.get(_getSubscribedTasksUrl(self.program, user.user_id))
    self.assertResponseOK(response)
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response,
        'modules/gci/leaderboard/student_tasks.html')

  def testSubscribedListAsStudent(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile = profile_utils.seedNDBStudent(self.program, user=user)

    response = self.get(_getSubscribedTasksUrl(self.program, user.user_id))
    self.assertResponseOK(response)

    for _ in range(_NUMBER_OF_SUBSCRIBED_TASKS):
      task_utils.seedTask(
          self.program, self.org, [], subscribers=[profile.key.to_old_key()])

    for _ in range(_NUMBER_OF_NON_SUBSCRIBED_TASKS):
      task_utils.seedTask(self.program, self.org, [])

    list_data = self.getListData(
        _getSubscribedTasksUrl(self.program, user.user_id), 0)
    self.assertEqual(_NUMBER_OF_SUBSCRIBED_TASKS, len(list_data))
