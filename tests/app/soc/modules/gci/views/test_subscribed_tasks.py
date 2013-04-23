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

from tests import test_utils
from tests import profile_utils

from soc.modules.gci.models import task as task_model
from soc.modules.seeder.logic import seeder

class SubscribedTasksPageTest(test_utils.GCIDjangoTestCase):

  def setUp(self):
    self.init()
    self.profile_helper = profile_utils.GCIProfileHelper(
        self.gci, self.dev_test)
    user = self.profile_helper.createUser()
    self.url = "/gci/subscribed_tasks/%s/%s" % (
        self.gci.key().name(), user.link_id )

  def testSubscribedListAsLoneUser(self):
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def assertSubscribedTasksTemplateUsed(self):
    self.profile_helper.createProfile()
    self.assertResponseOK(response)
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response,
        'v2/modules/gci/leaderboard/student_tasks.html')

  def testSubscribedListAsStudent(self):
    student = self.profile_helper.createStudent()
    response = self.get(self.url)
    self.assertResponseOK(response)

    task_properties_student_subscribed = {
        'subscribers': [student.key()]
    }

    task_properties_student_not_subscribed = {
        'subscribers': []
    }

    seeder.logic.seed(task_model.GCITask, task_properties_student_subscribed)
    seeder.logic.seed(task_model.GCITask, task_properties_student_subscribed)
    seeder.logic.seed(task_model.GCITask, task_properties_student_subscribed)
    seeder.logic.seed(task_model.GCITask,
        task_properties_student_not_subscribed)
    seeder.logic.seed(task_model.GCITask,
        task_properties_student_not_subscribed)

    list_data = self.getListData(self.url, 0)
    self.assertEqual(3, len(list_data))
