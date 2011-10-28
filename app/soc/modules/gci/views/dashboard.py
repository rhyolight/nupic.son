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
    elif self.data.is_mentor:
      components += self._getOrgMemberComponents()
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

  def _getOrgMemberComponents(self):
    """Get the dashboard components for Organization members.
    """
    components = []

    component = self._getMyOrgApplicationsComponent()
    if component:
      components.append(component)

    components.append(MyOrgsTaskList(self.request, self.data))

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

    list_config.addSimpleColumn('title', 'Title')
    list_config.addSimpleColumn('status', 'Status')
    list_config.addSimpleColumn('description', 'Description', hidden=True)

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
        'title': 'All tasks of my organizations',
        'lists': [list],
        'description': ugettext('List of all tasks of my organization'),
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

    response_builder = lists.RawQueryContentResponseBuilder(
        self.request, self._list_config, q, starter)

    return response_builder.build()
