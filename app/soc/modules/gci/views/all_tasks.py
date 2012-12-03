#!/usr/bin/env python2.5
#
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

"""Module containing the view for GCI tasks list page.
"""


from soc.logic.exceptions import AccessViolation
from soc.views.helper import url_patterns

from soc.modules.gci.logic import task as task_logic
from soc.modules.gci.templates.task_list import TaskList
from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views.helper.url_patterns import url


class AllTasksList(TaskList):
  """Template for list of all tasks which are claimable for the program.
  """

  _LIST_COLUMNS = ['title', 'organization', 'tags', 'types',
                   'mentors', 'status']

  def __init__(self, request, data):
    super(AllTasksList, self).__init__(request, data)

  def _getColumns(self):
    return self._LIST_COLUMNS

  def _getDescription(self):
    return 'List of tasks for %s' % self.data.program.name

  def _getQuery(self):
    return task_logic.queryClaimableTasksForProgram(self.data.program)


class TaskListPage(GCIRequestHandler):
  """View for the list task page.
  """

  TASK_LIST_COLUMNS = ['title', 'organization', 'mentors', 'status']

  def templatePath(self):
    return 'v2/modules/gci/task/task_list.html'

  def djangoURLPatterns(self):
    return [
        url(r'tasks/%s$' % url_patterns.PROGRAM, self,
            name='gci_list_tasks'),
    ]

  def checkAccess(self):
    pass

  def jsonContext(self):
    list_content = AllTasksList(self.request, self.data).getListData()

    if not list_content:
      raise AccessViolation('You do not have access to this data')

    return list_content.content()

  def context(self):
    return {
        'page_name': "Tasks for %s" % self.data.program.name,
        'task_list': AllTasksList(self.request, self.data),
    }
