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
"""Module containing the view for GCI leaderboard page.
"""

from soc.logic.exceptions import AccessViolation

from soc.views.helper import lists
from soc.views.helper import url_patterns
from soc.views.template import Template

from soc.modules.gci.models.student_ranking import GCIStudentRanking

from soc.modules.gci.views.base import RequestHandler
from soc.modules.gci.views.helper import url_names
from soc.modules.gci.views.helper.url_patterns import url


class LeaderboardList(Template):
  """Template for list of tasks.
  """

  LEADERBOARD_LIST_IDX = 0

  def __init__(self, request, data):
    self.request = request
    self.data = data
    r = data.redirect

    list_config = lists.ListConfiguration()
    list_config.addColumn('student', 'Student',
        lambda e, *args: e.student.name())
    list_config.addSimpleColumn('points', 'Points')
    list_config.addColumn('tasks', 'Tasks', lambda e, *args: len(e.tasks))

    self._list_config = list_config

  def context(self):
    description = 'Leaderboard for %s' % (
            self.data.program.name)

    leaderboard_list = lists.ListConfigurationResponse(
        self.data, self._list_config, self.LEADERBOARD_LIST_IDX, description)

    return {
        'lists': [leaderboard_list],
    }

  def getListData(self):
    idx = lists.getListIndex(self.request)
    if idx == self.LEADERBOARD_LIST_IDX:
      q = GCIStudentRanking.all()
      q.filter('program', self.data.program)

      response_builder = lists.RawQueryContentResponseBuilder(
          self.request, self._list_config, q, lists.keyStarter)

      return response_builder.build()
    else:
      return None

  def templatePath(self):
    return 'v2/modules/gci/leaderboard/_leaderboard_list.html'


class LeaderboardPage(RequestHandler):
  """View for the leaderboard page.
  """

  def templatePath(self):
    return 'v2/modules/gci/leaderboard/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'leaderbaord/%s$' % url_patterns.PROGRAM, self,
            name=url_names.GCI_LEADERBOARD),
    ]

  def checkAccess(self):
    pass

  def jsonContext(self):
    list_content = LeaderboardList(self.request, self.data).getListData()

    if not list_content:
      raise AccessViolation('You do not have access to this data')

    return list_content.content()

  def context(self):
    return {
        'page_name': "Leaderboard for %s" % self.data.program.name,
        'leaderboard_list': LeaderboardList(self.request, self.data),
#        'program_select': ProgramSelect(self.data, 'list_gci_finished_tasks'),
    }
