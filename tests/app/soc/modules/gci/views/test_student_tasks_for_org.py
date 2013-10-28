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

from tests import profile_utils
from tests import task_utils
from tests import test_utils


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
    mentor = profile_utils.seedGCIProfile(
        self.program, mentor_for=[self.org.key()])
    self.task = task_utils.seedTask(
        self.program, self.org, mentors=[mentor.key()])

    self.student = profile_utils.seedGCIStudent(self.program)

  def testTemplateUsed(self):
    url = self._taskPageUrl()
    response = self.get(url)

    self.assertResponseOK(response)
    self.assertGCITemplatesUsed(response)

  def _taskPageUrl(self):
    """Returns the url of the page.
    """
    return '/gci/student_tasks_for_org/%s/%s/%s' % (
        self.program.key().name(),
        self.student.link_id,
        self.org.link_id)
