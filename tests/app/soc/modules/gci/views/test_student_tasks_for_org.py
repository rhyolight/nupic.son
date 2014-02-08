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

"""Tests for StudentTasksForOrganizationPage view."""

from google.appengine.ext import ndb

from soc.modules.gci.models import task as task_model

from tests import profile_utils
from tests import task_utils
from tests import test_utils


_NUMBER_OF_TASKS = 2

class TestStudentTasksForOrganizationPage(test_utils.GCIDjangoTestCase):
  """Tests GCITask public view.
  """

  def setUp(self):
    """Creates a published task for self.org.
    """
    super(TestStudentTasksForOrganizationPage, self).setUp()
    self.init()
    self.timeline_helper.tasksPubliclyVisible()

    # Create a task, status published
    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[ndb.Key.from_old_key(self.org.key())])
    self.task = task_utils.seedTask(
        self.program, self.org, mentors=[mentor.key.to_old_key()])

    self.student = profile_utils.seedSOCStudent(self.program)

  def testPageLoads(self):
    """Tests that the page loads properly."""
    response = self.get(self._taskPageUrl())

    self.assertResponseOK(response)
    self.assertGCITemplatesUsed(response)

  def testListLoads(self):
    """Tests that the list data loads properly."""
    # seed a couple of tasks that have been closed by the student
    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[ndb.Key.from_old_key(self.org.key())])
    for _ in range(_NUMBER_OF_TASKS):
      task_utils.seedTask(self.program, self.org, [mentor.key.to_old_key()],
          student=self.student.key.to_old_key(), status=task_model.CLOSED)

    # seed a task that is currently claimed by the student
    # it should not be included in the list of closed tasks
    task_utils.seedTask(self.program, self.org, [mentor.key.to_old_key()],
        student=self.student.key.to_old_key(), status=task_model.CLAIMED)

    response = self.getListResponse(self._taskPageUrl(), 0)
    self.assertIsJsonResponse(response)
    data = response.context['data']['']
    self.assertEqual(len(data), _NUMBER_OF_TASKS)


  def _taskPageUrl(self):
    """Returns the url of the page."""
    return '/gci/student_tasks_for_org/%s/%s/%s' % (
        self.program.key().name(),
        self.student.profile_id,
        self.org.link_id)
