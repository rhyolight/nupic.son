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

"""Module containing the view for GCI leaderboard page."""

from melange.request import access
from melange.request import exception
from soc.views.helper import lists
from soc.views.helper import url_patterns
from soc.views.template import Template

from soc.modules.gci.logic import task as task_logic

from soc.modules.gci.models.score import GCIScore

from soc.modules.gci.templates.task_list import TaskList
from soc.modules.gci.views import common_templates
from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views.helper import url_names
from soc.modules.gci.views.helper.url_patterns import url


class LeaderboardList(Template):
  """Template for the leaderboard list."""

  LEADERBOARD_LIST_IDX = 0

  def __init__(self, data):
    self.data = data

    list_config = lists.ListConfiguration(add_key_column=False)
    list_config.addPlainTextColumn('key', 'Key', (lambda ent, *args: "%s" % (
        ent.parent().key().id_or_name())), hidden=True)
    list_config.addPlainTextColumn('student', 'Student',
        lambda e, *args: e.parent().name())
    list_config.addSimpleColumn('points', 'Points')
    list_config.addNumericalColumn('tasks', 'Tasks',
        lambda e, *args: len(e.tasks))
    list_config.setDefaultSort('points', 'desc')

    list_config.setRowAction(
        lambda e, *args: data.redirect.profile(e.parent().link_id).urlOf(
            url_names.GCI_STUDENT_TASKS))

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
    idx = lists.getListIndex(self.data.request)
    if idx == self.LEADERBOARD_LIST_IDX:
      q = GCIScore.all()
      q.filter('program', self.data.program)

      skipper = lambda entity, start: entity.points <= 0
      prefetcher = lists.ModelPrefetcher(GCIScore, [], True)

      response_builder = lists.RawQueryContentResponseBuilder(
          self.data.request, self._list_config, q, lists.keyStarter,
          skipper=skipper, prefetcher=prefetcher)

      return response_builder.build()
    else:
      return None

  def templatePath(self):
    return 'modules/gci/leaderboard/_leaderboard_list.html'


class AllStudentTasksList(TaskList):
  """Template for list of all tasks which have been completed by
  the specified student.
  """

  _LIST_COLUMNS = ['title', 'organization']

  def __init__(self, data):
    super(AllStudentTasksList, self).__init__(data)

  def _getColumns(self):
    return self._LIST_COLUMNS

  def _getDescription(self):
    return 'List of tasks closed by %s' % (
        self.data.url_profile.name())

  def _getQuery(self):
    return task_logic.queryAllTasksClosedByStudent(self.data.url_profile)


class LeaderboardPage(GCIRequestHandler):
  """View for the leaderboard page."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def templatePath(self):
    return 'modules/gci/leaderboard/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'leaderboard/%s$' % url_patterns.PROGRAM, self,
            name=url_names.GCI_LEADERBOARD),
    ]

  def jsonContext(self, data, check, mutator):
    list_content = LeaderboardList(data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def context(self, data, check, mutator):
    context = {
        'page_name': "Leaderboard for %s" % data.program.name,
        'leaderboard_list': LeaderboardList(data),
        'timeline': common_templates.Timeline(data),
        'complete_percentage': data.timeline.completePercentage(),
        'your_score': common_templates.YourScore(data),
        'program_select': common_templates.ProgramSelect(
            data, url_names.GCI_LEADERBOARD),
        }
    if data.is_host or data.timeline.winnersAnnounced():
      context['winners'] = common_templates.GlobalRankingWinners(data)

    return context


class StudentTasksPage(GCIRequestHandler):
  """View for the list of all the tasks closed by the specified student.
  """

  def templatePath(self):
    return 'modules/gci/leaderboard/student_tasks.html'

  def djangoURLPatterns(self):
    return [
        url(r'student_tasks/%s$' % url_patterns.PROFILE, self,
            name=url_names.GCI_STUDENT_TASKS),
    ]

  def checkAccess(self, data, check, mutator):
    mutator.studentFromKwargs()
    try:
      check.isHost()
    except exception.UserError:
      check.hasProfile()
      # check if the profile in URL kwargs is the current profile
      if data.profile.key() != data.url_profile.key():
        raise exception.Forbidden(
            message='You do not have access to this data')

  def jsonContext(self, data, check, mutator):
    list_content = AllStudentTasksList(data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def context(self, data, check, mutator):
    return {
        'page_name': "Tasks closed by %s" % data.url_profile.name(),
        'tasks_list': AllStudentTasksList(data),
    }
