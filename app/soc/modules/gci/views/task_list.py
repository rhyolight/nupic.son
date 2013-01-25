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

"""Module containing the views for GCI historic task page."""

from soc.logic.exceptions import AccessViolation
from soc.views.helper import url_patterns
from soc.views.helper import lists
from soc.views.template import Template

from soc.modules.gci.logic import task as task_logic
from soc.modules.gci.models.task import GCITask
from soc.modules.gci.templates.org_list import BasicOrgList
from soc.modules.gci.templates.task_list import TaskList
from soc.modules.gci.views.base import GCIRequestHandler
#from soc.modules.gci.views.base_templates import ProgramSelect
from soc.modules.gci.views.helper import url_names
from soc.modules.gci.views.helper.url_patterns import url


class TaskList2(Template):
  """Template for list of tasks.
  """

  def __init__(self, request, data):
    self.request = request
    self.data = data
    r = data.redirect

    list_config = lists.ListConfiguration()
    list_config.addSimpleColumn('title', 'Title')
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
      q.filter('status', 'Closed')

      response_builder = lists.RawQueryContentResponseBuilder(
          self.request, self._list_config, q, lists.keyStarter)

      return response_builder.build()
    else:
      return None

  def templatePath(self):
    return 'v2/modules/gci/task/_task_list.html'


class TaskListPage(GCIRequestHandler):
  """View for the list task page.
  """

  def templatePath(self):
    return 'v2/modules/gci/task/task_list.html'

  def djangoURLPatterns(self):
    return [
        url(r'finished_tasks/%s$' % url_patterns.PROGRAM, self,
            name='list_gci_finished_tasks'),
    ]

  def checkAccess(self):
    pass

  def jsonContext(self):
    # TODO(nathaniel): Drop the first parameter of TaskList2.
    list_content = TaskList2(self.data.request, self.data).getListData()

    if not list_content:
      raise AccessViolation('You do not have access to this data')

    return list_content.content()

  def context(self):
    return {
        'page_name': "Tasks for %s" % self.data.program.name,
        'task_list': TaskList2(self.data.request, self.data),
#        'program_select': ProgramSelect(self.data, 'list_gci_finished_tasks'),
    }


class StudentTasksForOrganizationList(TaskList):
  """List of tasks that the specified student closed for the given
  organization.
  """

  _COLUMNS = ['title', 'mentors']

  def _getColumns(self):
    return self._COLUMNS

  def _getDescription(self):
    return "List of tasks closed by %s for %s." % (
        self.data.url_profile.name(), self.data.organization.name)

  def _getQuery(self):
    return task_logic.queryForStudentAndOrganizationAndStatus(
        self.data.url_profile, self.data.organization, 'Closed')


class StudentTasksForOrganizationPage(GCIRequestHandler):
  """View for the list of student tasks for organization.
  """

  def templatePath(self):
    return 'v2/modules/gci/task/task_list.html'

  def djangoURLPatterns(self):
    return [
        url(r'student_tasks_for_org/%s$' % url_patterns.USER_ORG, self,
            name=url_names.GCI_STUDENT_TASKS_FOR_ORG),
    ]

  def checkAccess(self):
    # TODO(daniel): who should be able to access it?
    self.mutator.profileFromKwargs()

  def jsonContext(self):
    # TODO(nathaniel): Drop the first parameter of StudentTasksForOrganizationList.
    list_content = StudentTasksForOrganizationList(
        self.data.request, self.data).getListData()

    if not list_content:
      raise AccessViolation('You do not have access to this data')

    return list_content.content()

  def context(self):
    return {
        'page_name': "Tasks closed by %s for %s" % (
            self.data.url_profile.name(), self.data.organization.name),
        'task_list': StudentTasksForOrganizationList(self.data.request, self.data),
    }


class ChooseOrganizationList(BasicOrgList):
  """List of all organizations whose row action redirects to a list of all
  tasks created by the specified organization.
  """

  def _getRedirect(self):
    def redirect(e, *args):
      # TODO(nathaniel): make this .organization call unnecessary.
      self.data.redirect.organization(organization=e)

      return self.data.redirect.urlOf(url_names.GCI_ORG_TASKS_ALL)
    return redirect

  def _getDescription(self):
    return 'Choose an organization for which to display tasks.'


class ChooseOrganizationPage(GCIRequestHandler):
  """View with a list of organizations. When a user clicks on one of them,
  he or she is moved to the organization tasks for this organization.
  """

  def templatePath(self):
    return 'v2/modules/gci/org_list/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'org_choose_for_all_tasks/%s$' % url_patterns.PROGRAM, self,
            name=url_names.GCI_ORG_CHOOSE_FOR_ALL_TASKS),
    ]

  def checkAccess(self):
    self.check.isHost()

  def jsonContext(self):
    # TODO(nathaniel): Drop the first parameter of ChooseOrganizationList.
    list_content = ChooseOrganizationList(
        self.data.request, self.data).getListData()

    if not list_content:
      raise AccessViolation(
          'You do not have access to this data')
    return list_content.content()

  def context(self):
    return {
        'page_name': "Choose an organization for which to display tasks.",
        'org_list': ChooseOrganizationList(self.data.request, self.data),
    }


class AllOrganizationTasksList(TaskList):
  """List of all tasks that have been created by the specified organization.
  """

  _COLUMNS = ['title', 'mentors', 'status']

  def _getColumns(self):
    return self._COLUMNS

  def _getDescription(self):
    return "List of tasks created by %s." % self.data.organization.name

  def _getQuery(self):
    return task_logic.queryForOrganization(self.data.organization)


class AllOrganizationTasksPage(GCIRequestHandler):
  """View for program admins to see all tasks created by an organization
  which is specified in the URL.
  """

  def templatePath(self):
    return 'v2/modules/gci/task/task_list.html'

  def djangoURLPatterns(self):
    return [
        url(r'org/tasks/all/%s$' % url_patterns.ORG, self,
            name=url_names.GCI_ORG_TASKS_ALL),
    ]

  def checkAccess(self):
    self.check.isHost()

  def jsonContext(self):
    # TODO(nathaniel): Drop the first parameter of AllOrganizationTasksList.
    list_content = AllOrganizationTasksList(
        self.data.request, self.data).getListData()

    if not list_content:
      raise AccessViolation('You do not have access to this data')

    return list_content.content()

  def context(self):
    return {
        'page_name': 'Tasks created by %s' % self.data.organization.name,
        'task_list': AllOrganizationTasksList(self.data.request, self.data),
    }
