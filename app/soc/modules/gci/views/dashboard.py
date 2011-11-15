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

"""Module for the GCI participant dashboard.
"""

__authors__ = [
  '"Akeda Bagus" <admin@gedex.web.id>',
  '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]

from django.utils.dateformat import format
from django.utils.translation import ugettext

from soc.logic.exceptions import AccessViolation
from soc.views.dashboard import Component
from soc.views.dashboard import Dashboard
from soc.views.helper import lists
from soc.views.helper import url_patterns
from soc.models.org_app_record import OrgAppRecord

from soc.modules.gci.logic import org_app as org_app_logic
from soc.modules.gci.models import task
from soc.modules.gci.models.organization import GCIOrganization
from soc.modules.gci.models.task import GCITask
from soc.modules.gci.views.base import RequestHandler
from soc.modules.gci.views.helper.url_patterns import url


BACKLINKS_TO_MAIN = {'to': 'main', 'title': 'Main dashboard'}
DATETIME_FORMAT = 'Y-m-d H:i:s'


class MainDashboard(Dashboard):
  """Dashboard for user's main-dashboard
  """

  def __init__(self, request, data):
    """Initializes the dashboard.

    Args:
      request: The HTTPRequest object
      data: The RequestData object
    """
    super(MainDashboard, self).__init__(request, data)
    self.subpages = []

  def context(self):
    """Returns the context of main dashboard.
    """
    return {
        'title': 'Participant dashboard',
        'name': 'main',
        'subpages': self._divideSubPages(self.subpages),
        'enabled': True
    }

  def addSubpages(self, subpage):
    self.subpages.append(subpage)


class ComponentsDashboard(Dashboard):
  """Dashboard that holds component list
  """

  def __init__(self, request, data, component_property):
    """Initializes the dashboard.

    Args:
      request: The HTTPRequest object
      data: The RequestData object
      component_property: Component property
    """
    super(ComponentsDashboard, self).__init__(request, data)
    self.name = component_property.get('name')
    self.title = component_property.get('title')
    self.components = [component_property.get('component'),]
    self.backlinks = [component_property.get('backlinks'),]

  def context(self):
    """Returns the context of components dashboard.
    """
    return {
        'title': self.title,
        'name': self.name,
        'backlinks': self.backlinks,
        'components': self.components,
    }


class DashboardPage(RequestHandler):
  """View for the participant dashboard.
  """

  def djangoURLPatterns(self):
    """The URL pattern for the dashboard.
    """
    return [
        url(r'dashboard/%s$' % url_patterns.PROGRAM, self,
            name='gci_dashboard')]

  def checkAccess(self):
    """Denies access if you are not logged in.
    """
    self.check.isLoggedIn()

  def templatePath(self):
    """Returns the path to the template.
    """
    return 'v2/modules/gci/dashboard/base.html'

  def context(self):
    """Handler for default HTTP GET request.
    """
    # dashboard container, will hold each component list
    dashboards = []

    # main container that contains all component list
    main = MainDashboard(self.request, self.data)

    # retrieve active links and add it to the main dashboard
    links = self.links()
    for link in links:
      main.addSubpages(link)

    # retrieve active component(s) for currently logged-in user
    components = self.components()

    # add components as children of main dashboard and treat the component
    # as dashboard element
    for component in components:
      c = {
          'name': component.context().get('name'),
          'description': component.context().get('description'),
          'title': component.context().get('title'),
          'component_link': True,
          }
      main.addSubpages(c)

      dashboards.append(ComponentsDashboard(self.request, self.data, {
          'name': component.context().get('name'),
          'title': component.context().get('title'),
          'component': component,
          'backlinks': BACKLINKS_TO_MAIN,
          }))

    dashboards.append(main)

    return {
        'page_name': self.data.program.name,
        'user_name': self.data.user.name if self.data.user else None,
        'dashboards': dashboards,
    }

  def jsonContext(self):
    """Handler for JSON requests.
    """
    components = self.components()

    list_content = None
    for component in components:
      list_content = component.getListData()
      if list_content:
        break

    if not list_content:
      raise AccessViolation(
          'You do not have access to this data')
    return list_content.content()

  def components(self):
    """Returns the list components that are active on the page.
    """
    components = []

    if self.data.student_info:
      components += self._getStudentComponents()
    elif self.data.is_org_admin:
      components += self._getOrgAdminComponents()
      components += self._getMentorComponents()
    elif self.data.is_mentor:
      components += self._getMentorComponents()
    else:
      components += self._getLoneUserComponents()

    if self.data.is_host:
      components += self._getHostComponents()

    return components

  def _getHostComponents(self):
    """Get the dashboard components for a host.
    """
    components = []

    return components

  def _getStudentComponents(self):
    """Get the dashboard components for a student.
    """
    components = []

    return components

  def _getMentorComponents(self):
    """Get the dashboard components for Organization members.
    """
    components = []

    component = self._getMyOrgApplicationsComponent()
    if component:
      components.append(component)

    components.append(MyOrgsTaskList(self.request, self.data))

    # add org list just before creating task and invitation, so mentor can
    # choose which organization the task or invitite will be created for
    components.append(MyOrgsListBeforeCreateTask(self.request, self.data))

    return components

  def _getOrgAdminComponents(self):
    """Get the dashboard components for org admins.
    """
    components = []

    # add invite mentors compontent
    components.append(MyOrgsListBeforeInviteMentor(self.request, self.data))

    return components

  def _getLoneUserComponents(self):
    """Get the dashboard components for users without any role.
    """
    components = []

    component = self._getMyOrgApplicationsComponent()
    if component:
      components.append(component)

    return components

  def _getMyOrgApplicationsComponent(self):
    """Returns MyOrgApplicationsComponent iff this user is main_admin or
    backup_admin in an application.
    """
    survey = org_app_logic.getForProgram(self.data.program)

    # Test if this user is main admin or backup admin
    q = OrgAppRecord.all()
    q.filter('survey', survey)
    q.filter('main_admin', self.data.user)

    record = q.get()

    q = OrgAppRecord.all()
    q.filter('survey', survey)
    q.filter('backup_admin', self.data.user)

    if record or q.get():
      # add a component showing the organization application of the user
      return MyOrgApplicationsComponent(self.request, self.data, survey)

    return None

  def links(self):
    """Returns additional links of main dashboard that are active on the page.
    """
    links = []

    if self.data.is_mentor:
      links += self._getOrgMemberLinks()
    else:
      links += self._getLoneUserLinks()

    return links

  def _getOrgMemberLinks(self):
    """Get the main dashboard links for Organization members.
    """
    links = []

    # org app link for
    link = self._getAddNewOrgAppLink()
    if link:
      links.append(link)

    return links

  def _getLoneUserLinks(self):
    """Get the main dashboard links for users without any role.
    """
    links = []

    link = self._getAddNewOrgAppLink()
    if link:
      links.append(link)

    return links

  def _getAddNewOrgAppLink(self):
    """Get the link for org admins to take organization application survey.
    """
    survey = org_app_logic.getForProgram(self.data.program)
    if not survey or not self.data.timeline.surveyPeriod(survey):
      return []

    r = self.data.redirect
    r.program()

    return {
        'name': 'take_org_app',
        'description': ugettext(
            'Take organization application survey.'),
        'title': 'Take organization application',
        'link': r.urlOf('gci_take_org_app')
        }


class MyOrgApplicationsComponent(Component):
  """Component for listing the Organization Applications of the current user.
  """

  def __init__(self, request, data, survey):
    """Initializes the component.

    Args:
      request: The HTTPRequest object
      data: The RequestData object
      survey: the OrgApplicationSurvey entity
    """
    super(MyOrgApplicationsComponent, self).__init__(request, data)

    # passed in so we don't have to do double queries
    self.survey = survey

    list_config = lists.ListConfiguration()

    list_config.addSimpleColumn('name', 'Name')
    list_config.addSimpleColumn('org_id', 'Organization ID')
    list_config.addColumn(
        'created', 'Created On',
        lambda ent, *args: format(ent.created, DATETIME_FORMAT))
    list_config.addColumn(
        'modified', 'Last Modified On',
        lambda ent, *args: format(ent.modified, DATETIME_FORMAT))

    if self.data.timeline.surveyPeriod(survey):
      url_name = 'gci_retake_org_app'
    else:
      url_name = 'gci_show_org_app'

    list_config.setRowAction(
        lambda e, *args: data.redirect.id(e.key().id()).
            urlOf(url_name))

    self._list_config = list_config

    super(MyOrgApplicationsComponent, self).__init__(request, data)

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return'v2/modules/gci/dashboard/list_component.html'

  def context(self):
    """Returns the context of this component.
    """
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=0, preload_list=False)

    return {
        'name': 'org_app',
        'title': 'My organization applications',
        'lists': [list],
        'description': ugettext('My organization applications'),
        }

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    if lists.getListIndex(self.request) != 0:
      return None

    q = OrgAppRecord.all()
    q.filter('survey', self.survey)
    q.filter('main_admin', self.data.user)

    records = q.fetch(1000)

    q = OrgAppRecord.all()
    q.filter('survey', self.survey)
    q.filter('backup_admin', self.data.user)

    records.extend(q.fetch(1000))

    response = lists.ListContentResponse(self.request, self._list_config)

    for record in records:
      response.addRow(record)
    response.next = 'done'

    return response

class MyOrgsTaskList(Component):
  """Component for listing the tasks of the orgs of the current user.
  """

  def __init__(self, request, data):
    """Initializes the component.

    Args:
      request: The HTTPRequest object
      data: The RequestData object
    """
    super(MyOrgsTaskList, self).__init__(request, data)

    list_config = lists.ListConfiguration()

    def mentorsFromPrefetchedList(entity, *args):
      """Returns the comma separated list of mentor names for the entity.

      Args:
        entity: The task entity that is being considered for the row
        args: list of prefetched entities
        args[0]: Dictionary of mentors will be the first item of args.
            In each key-value pair in the dictionary key will be the mentor
            entity key and the value will be the entity itself.
      """

      mentor_names = []
      for key in entity.mentors:
        mentor = args[0].get(key)
        mentor_names.append(mentor.name())

      return ', '.join(mentor_names)


    list_config.addSimpleColumn('title', 'Title')
    list_config.addColumn('org', 'Organization',
                          lambda entity, *args: entity.org.name)
    list_config.addColumn('difficulty', 'Difficulty',
                          lambda entity, *args: entity.taskDifficultyName())
    list_config.addColumn('task_type', 'Type',
                          lambda entity, *args: entity.taskType())
    list_config.addColumn('arbit_tag', 'Tags',
                          lambda entity, *args: entity.taskArbitTag())
    list_config.addColumn('time_to_complete', 'Time to complete',
                          lambda entity, *args: entity.taskTimeToComplete())

    # This complicated comma separated mentor names string construction
    # is separated in an inline function.
    list_config.addColumn('mentors', 'Mentors', mentorsFromPrefetchedList)

    list_config.addColumn(
        'student', 'Student',
        lambda ent, *args: ent.student.name() if ent.student else '',
        hidden=True)
    list_config.addColumn(
        'created_by', 'Created by',
        lambda entity, *args: entity.created_by.name() \
            if entity.created_by else '',
        hidden=True)
    list_config.addColumn(
        'modified_by', 'Modified by',
        lambda entity, *args: entity.modified_by.name() \
            if entity.modified_by else '',
        hidden=True)
    list_config.addColumn(
        'created_on', 'Created on',
        lambda entity, *args: format(entity.created_on, DATETIME_FORMAT) \
            if entity.created_on else '',
        hidden=True)
    list_config.addColumn(
        'modified_on', 'Modified on',
        lambda entity, *args: format(entity.modified_on, DATETIME_FORMAT) \
            if entity.modified_on else '',
        hidden=True)
    list_config.addColumn('closed_on', 'Closed on',
        lambda entity, *args: format(
            entity.closed_on, DATETIME_FORMAT) if entity.closed_on else '',
        hidden=True)
    list_config.addSimpleColumn('status', 'Status')

    # TODO (madhu): Super temporary solution until the pretty lists are up.
    list_config.addColumn('edit', 'Edit',
        lambda entity, *args: (
          '<a href="%s" style="color:#0000ff;text-decoration:underline;">'
          'Edit</a>' % (data.redirect.id(entity.key().id()).urlOf(
              'gci_edit_task'))))

    list_config.setRowAction(
        lambda e, *args: data.redirect.id(e.key().id()).
            urlOf('gci_view_task'))

    self._list_config = list_config

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return'v2/modules/gci/dashboard/list_component.html'

  def context(self):
    """Returns the context of this component.
    """
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=1, preload_list=False)

    return {
        'name': 'all_org_tasks',
        'title': 'All tasks for my organizations',
        'lists': [list],
        'description': ugettext('List of all tasks for my organization'),
        }

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    if lists.getListIndex(self.request) != 1:
      return None

    q = GCITask.all()
    q.filter('program', self.data.program)
    q.filter('org IN', self.data.mentor_for)

    starter = lists.keyStarter
    prefetcher = lists.listModelPrefetcher(
        GCITask, ['org', 'student', 'created_by', 'modified_by'], ['mentors'])

    response_builder = lists.RawQueryContentResponseBuilder(
        self.request, self._list_config, q, starter, prefetcher=prefetcher)

    return response_builder.build()


class MyOrgsList(Component):
  """Component for listing the orgs of the current user.

  Since mentor_for is a list of orgs, we need to give org selection first
  """

  def __init__(self, request, data):
    """Initializes the component.

    Args:
      request: The HTTPRequest object
      data: The RequestData object
    """
    super(MyOrgsList, self).__init__(request, data)

    list_config = lists.ListConfiguration()

    list_config.addSimpleColumn('name', 'Organization Name')

    self._list_config = list_config

    self._setRowAction(request, data)

    self._setIdx()

  def _setIdx(self):
    raise NotImplemented

  def _setRowAction(self, request, data):
    """Since setRowAction can be vary, it must be implemented individually.
    """
    raise NotImplemented
    
  def _getContext(self):
    raise NotImplemented

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return'v2/modules/gci/dashboard/list_component.html'

  def context(self):
    """Returns the context of this component.
    """
    return self._getContext()


  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    if lists.getListIndex(self.request) != self.idx:
      return None

    q = GCIOrganization.all()
    q.filter('scope', self.data.program)
    q.filter('__key__ IN', self.data.mentor_for)

    starter = lists.keyStarter

    response_builder = lists.RawQueryContentResponseBuilder(
        self.request, self._list_config, q, starter)

    return response_builder.build()


class MyOrgsListBeforeCreateTask(MyOrgsList):
  """Component for listing the orgs of the current user, just before creating
  task.
  """

  def _setIdx(self):
    self.idx = 2

  def _getContext(self):
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=self.idx, preload_list=False)

    return {
        'name': 'create_tasks',
        'title': 'Create Task',
        'lists': [list],
        'description': ugettext('Create task for students. Since you may '
            'belong to more than one organizations, you need to choose one '
            'organization you will create the task for.')}

  def _setRowAction(self, request, data):
    self._list_config.setRowAction(
        lambda e, *args: data.redirect.organization(e).
            urlOf('gci_create_task'))


class MyOrgsListBeforeInviteMentor(MyOrgsList):
  """Component for listing the orgs of the current user, just before creating
  invite.
  """

  def _setIdx(self):
    self.idx = 3

  def _getContext(self):
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=self.idx, preload_list=False)

    return {
        'name': 'invite_mentor',
        'title': 'Invite mentor',
        'lists': [list],
        'description': ugettext('Invite mentors to be part of your '
            'organization.')}

  def _setRowAction(self, request, data):
    r = data.redirect

    self._list_config.setRowAction(
        lambda e, *args: r.invite('mentor', e).urlOf('gci_invite'))
