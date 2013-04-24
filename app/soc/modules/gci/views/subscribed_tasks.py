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

"""Module containing the view for list of a users' subscribed tasks """

from soc.logic import exceptions
from soc.views.helper import url_patterns

from soc.modules.gci.logic import task as task_logic

from soc.modules.gci.templates import task_list
from soc.modules.gci.views import base
from soc.modules.gci.views.helper import url_names
from soc.modules.gci.views.helper import url_patterns as gci_url_patterns


class SubscribedTasksList(task_list.TaskList):
  """Template for list of tasks the specified profile is subscribed to"""

  _LIST_COLUMNS = ['title', 'organization']

  def __init__(self, data):
    super(SubscribedTasksList, self).__init__(data)

  def _getColumns(self):
    return self._LIST_COLUMNS

  def _getDescription(self):
    return 'List of tasks %s is subscribed to.' % (
        self.data.url_profile.name())

  def _getQuery(self):
    return task_logic.querySubscribedTasksForProfile(self.data.url_profile)


class SubscribedTasksPage(base.GCIRequestHandler):
  """View for the list of the tasks the specified profile is subscribed to."""

  def templatePath(self):
    return 'v2/modules/gci/subscribed_tasks/subscribed_tasks.html'

  def djangoURLPatterns(self):
    return [
        gci_url_patterns.url(r'subscribed_tasks/%s$' % url_patterns.PROFILE,
            self, name=url_names.GCI_SUBSCRIBED_TASKS),
    ]

  def checkAccess(self, data, check, mutator):
    check.isProfileActive()
    mutator.profileFromKwargs()
    if data.profile.key() != data.url_profile.key():
      raise exceptions.AccessViolation('You do not have access to this data')

  def jsonContext(self, data, check, mutator):
    return SubscribedTasksList(data).getListData().content()

  def context(self, data, check, mutator):
    return {
        'page_name': "Tasks %s is subscribed to" % data.url_profile.name(),
        'tasks_list': SubscribedTasksList(data),
    }
