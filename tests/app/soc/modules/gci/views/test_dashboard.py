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

from google.appengine.ext import ndb

from soc.modules.gci.models import task as task_model
from soc.modules.gci.views import dashboard as dashboard_view

from tests import profile_utils
from tests import task_utils
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
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)

    response = self.get(self._getDashboardUrl())
    self.assertResponseForbidden(response)

  def testDashboardAsHost(self):
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    response = self.get(self._getDashboardUrl())
    self.assertResponseForbidden(response)

  def testDashboardAsMentorWithTask(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile = profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        mentor_for=[ndb.Key.from_old_key(self.org.key())])
    task_utils.seedTask(
        self.program, self.org, [profile.key.to_old_key()])

    response = self.get(self._getDashboardUrl())
    self.assertDashboardComponentTemplatesUsed(response)
    response = self.getListResponse(self._getDashboardUrl(), 1)
    self.assertIsJsonResponse(response)
    data = json.loads(response.content)
    self.assertEqual(1, len(data['data']['']))

  def testDashboardAsStudent(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBStudent(self.program, user=user)

    response = self.get(self._getDashboardUrl())
    self.assertResponseOK(response)

  def testPostPublish(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile = profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        admin_for=[ndb.Key.from_old_key(self.org.key())])

    # check if Unpublished task may be published
    self._testPostPublish(profile, 'Unpublished', 'Open', 'publish')

    # check if Unapproved task may be published
    self._testPostPublish(profile, task_model.UNAPPROVED, 'Open', 'publish')

    # check if Open task may be unpublished
    self._testPostPublish(profile, 'Open', 'Unpublished', 'unpublish')

    # check if Reopened task may not be changed
    self._testPostPublish(
        profile, task_model.REOPENED, task_model.REOPENED, 'publish')
    self._testPostPublish(
        profile, task_model.REOPENED, task_model.REOPENED, 'unpublish')

    # check if Claimed task may not be changed
    self._testPostPublish(profile, 'Claimed', 'Claimed', 'publish')
    self._testPostPublish(profile, 'Claimed', 'Claimed', 'unpublish')

    # check if ActionNeeded task may not be changed
    self._testPostPublish(profile, 'ActionNeeded', 'ActionNeeded', 'publish')
    self._testPostPublish(profile, 'ActionNeeded', 'ActionNeeded', 'unpublish')

    # check if Closed task may not be changed
    self._testPostPublish(profile, 'Closed', 'Closed', 'publish')
    self._testPostPublish(profile, 'Closed', 'Closed', 'unpublish')

  def _testPostPublish(self, profile, initial_status, final_status, action):
    """Creates a new task with the specified initial status, performs
    a POST action and checks if the task has final status after that.

    Args:
      profile: Profile entity of the user who takes the action.
      initial_status: initial status of a task to create
      fianl_status: final status which the task should have after POST action
      action: 'publish' if the task should be published or 'unpublish'
    """
    task = task_utils.seedTask(
        self.program, self.org, [profile.key.to_old_key()],
        status=initial_status)

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
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile = profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        mentor_for=[ndb.Key.from_old_key(self.org.key())])

    # create a couple of tasks
    task_utils.seedTask(
        self.program, self.org, [profile.key.to_old_key()])
    task_utils.seedTask(
        self.program, self.org, [profile.key.to_old_key()],
        status=task_model.REOPENED)

    response = self.get(self._getDashboardUrl())
    self.assertResponseOK(response)

    list_data = self.getListData(self._getDashboardUrl(),
        dashboard_view.MyOrgsTaskList.IDX)
    self.assertEqual(len(list_data), 2)

  def _getDashboardUrl(self):
    return '/gci/dashboard/' + self.gci.key().name()
