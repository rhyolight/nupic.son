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

__authors__ = [
  '"Madhusudan C.S." <madhusudancs@gmail.com>',
  ]


from soc.logic.exceptions import AccessViolation
from soc.views.helper import url_patterns
from soc.views.helper import lists
from soc.views.template import Template

from soc.modules.gci.models.task import CLAIMABLE
from soc.modules.gci.models.task import GCITask
from soc.modules.gci.models.task import TaskDifficultyTag
from soc.modules.gci.models.task import TaskTypeTag
from soc.modules.gci.views.base import RequestHandler
from soc.modules.gci.views.helper.url_patterns import url


class TaskList(Template):
  """Template for list of tasks.
  """

  def __init__(self, request, data):
    self.request = request
    self.data = data
    r = data.redirect

    list_config = lists.ListConfiguration()
    list_config.addSimpleColumn('title', 'Title')
    list_config.addColumn(
        'org', 'Organization', lambda entity, *args: entity.org.name)
    list_config.addColumn(
        'mentors', 'Mentors',
        lambda entity, mentors, *args: ', '.join(
            mentors[i].name() for i in entity.mentors))
    #list_config.addColumn(
    #    'difficulty', 'Difficulty',
    #    lambda entity, _, all_d, *args: entity.taskDifficultyName(all_d))
    #list_config.addColumn(
    #    'task_type', 'Type',
    #    lambda entity, _, all_d, all_t, *args: entity.taskType(all_t))
    #list_config.addColumn('time_to_complete', 'Time to complete',
    #                      lambda entity, *args: entity.taskTimeToComplete())

    list_config.addSimpleColumn('status', 'Status')

    list_config.setRowAction(
        lambda e, *args: r.id(e.key().id()).urlOf('gci_view_task'))

    self._list_config = list_config

  def context(self):
    description = 'List of tasks for %s' % (
            self.data.program.name)

    list = lists.ListConfigurationResponse(
        self.data, self._list_config, 0, description)

    return {
        'lists': [list],
    }

  def getListData(self):
    idx = lists.getListIndex(self.request)
    if idx == 0:
      q = GCITask.all()
      q.filter('program', self.data.program)
      q.filter('status IN', CLAIMABLE)

      starter = lists.keyStarter
      prefetcher = lists.listModelPrefetcher(
          GCITask, ['org'], ['mentors'])

      #all_d = TaskDifficultyTag.all().fetch(100)
      #all_t = TaskTypeTag.all().fetch(100)

      #def prefetcher(entities):
      #  args, kwargs = basic_prefetcher(entities)
      #  args += [all_d, all_t]
      #  return (args, kwargs)

      response_builder = lists.RawQueryContentResponseBuilder(
          self.request, self._list_config, q,
          starter=starter, prefetcher=prefetcher)

      return response_builder.build()
    else:
      return None

  def templatePath(self):
    return 'v2/modules/gci/task/_task_list.html'


class TaskListPage(RequestHandler):
  """View for the list task page.
  """

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
    list_content = TaskList(self.request, self.data).getListData()

    if not list_content:
      raise AccessViolation('You do not have access to this data')

    return list_content.content()

  def context(self):
    return {
        'page_name': "Tasks for %s" % self.data.program.name,
        'task_list': TaskList(self.request, self.data),
    }
