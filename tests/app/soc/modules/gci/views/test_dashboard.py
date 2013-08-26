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

"""Tests the view for GCI Dashboard."""

import json

from soc.modules.gci.models import task as task_model
from soc.modules.gci.views import dashboard as dashboard_view

from tests import gci_task_utils
from tests import test_utils


class DashboardTest(test_utils.GCIDjangoTestCase):
  """Tests the GCI Dashboard components."""

  def setUp(self):
    self.init()
    self.url = '/gci/dashboard/' + self.gci.key().name()

  def assertDashboardTemplatesUsed(self, response):
    """Asserts that all the templates from the dashboard were used."""
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gci/dashboard/base.html')

  def assertDashboardComponentTemplatesUsed(self, response):
    """Asserts that all the templates to render a component were used."""
    self.assertDashboardTemplatesUsed(response)
    self.assertTemplateUsed(response,
        'modules/gci/dashboard/list_component.html')
    self.assertTemplateUsed(response,
        'modules/gci/dashboard/component.html')
    self.assertTemplateUsed(response, 'soc/list/lists.html')
    self.assertTemplateUsed(response, 'soc/list/list.html')

  def testDashboardAsLoneUser(self):
    self.profile_helper.createUser()
    response = self.get(self._getDashboardUrl())
    self.assertResponseForbidden(response)

  def testDashboardAsHost(self):
    self.profile_helper.createHost()
    response = self.get(self._getDashboardUrl())
    self.assertResponseForbidden(response)

  def testDashboardAsMentorWithTask(self):
    self.profile_helper.createMentorWithTask('Open', self.org)
    response = self.get(self._getDashboardUrl())
    self.assertDashboardComponentTemplatesUsed(response)
    response = self.getListResponse(self._getDashboardUrl(), 1)
    self.assertIsJsonResponse(response)
    data = json.loads(response.content)
    self.assertEqual(1, len(data['data']['']))

  def testDashboardAsStudent(self):
    self.profile_helper.createStudent()
    response = self.get(self._getDashboardUrl())
    self.assertResponseOK(response)

  def testPostPublish(self):
    self.profile_helper.createOrgAdmin(self.org)

    # check if Unpublished task may be published
    self._testPostPublish('Unpublished', 'Open', 'publish')

    # check if Unapproved task may be published
    self._testPostPublish(task_model.UNAPPROVED, 'Open', 'publish')

    # check if Open task may be unpublished
    self._testPostPublish('Open', 'Unpublished', 'unpublish')

    # check if Reopened task may not be changed
    self._testPostPublish('Reopened', 'Reopened', 'publish')
    self._testPostPublish('Reopened', 'Reopened', 'unpublish')

    # check if Claimed task may not be changed
    self._testPostPublish('Claimed', 'Claimed', 'publish')
    self._testPostPublish('Claimed', 'Claimed', 'unpublish')

    # check if ActionNeeded task may not be changed
    self._testPostPublish('ActionNeeded', 'ActionNeeded', 'publish')
    self._testPostPublish('ActionNeeded', 'ActionNeeded', 'unpublish')

    # check if Closed task may not be changed
    self._testPostPublish('Closed', 'Closed', 'publish')
    self._testPostPublish('Closed', 'Closed', 'unpublish')

  def _testPostPublish(self, initial_status, final_status, action):
    """Creates a new task with the specified initial status, performs
    a POST action and checks if the task has final status after that.

    Args:
      initial_status: initial status of a task to create
      fianl_status: final status which the task should have after POST action
      action: 'publish' if the task should be published or 'unpublish'
    """
    task_helper = gci_task_utils.GCITaskHelper(self.gci)

    task = task_helper.createTask(
        initial_status, self.org, self.profile_helper.profile)

    data = json.dumps([{'key': str(task.key().id())}])

    if action == 'publish':
      button_id = dashboard_view.MyOrgsTaskList.PUBLISH_BUTTON_ID
    else:
      button_id = dashboard_view.MyOrgsTaskList.UNPUBLISH_BUTTON_ID

    post_data = {
        'idx': dashboard_view.MyOrgsTaskList.IDX,
        'data': data,
        'button_id': button_id
        }

    response = self.post(self._getDashboardUrl(), post_data)
    self.assertResponseOK(response)

    task = task_model.GCITask.get(task.key())
    self.assertEqual(task.status, final_status)

  def testMyOrgsTaskList(self):
    self.profile_helper.createMentor(self.org)

    task_helper = gci_task_utils.GCITaskHelper(self.gci)

    # create a couple of tasks
    task_helper.createTask('Open', self.org, self.profile_helper.profile)
    task_helper.createTask('Reopened', self.org, self.profile_helper.profile)

    response = self.get(self._getDashboardUrl())
    self.assertResponseOK(response)

    list_data = self.getListData(self._getDashboardUrl(),
        dashboard_view.MyOrgsTaskList.IDX)
    self.assertEqual(len(list_data), 2)

  def _getDashboardUrl(self):
    return '/gci/dashboard/' + self.gci.key().name()
