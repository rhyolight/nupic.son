# Copyright 2011 the Melange authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module containing the Org Homepage view."""

from django.utils.translation import ugettext

from melange.request import access
from melange.request import exception
from melange.request import links

from soc.logic import accounts
from soc.views.helper import lists
from soc.views.helper import url_patterns
from soc.views.org_home import BanOrgPost
from soc.views.template import Template
from soc.views import toggle_button

from soc.modules.gci.models.organization import GCIOrganization
from soc.modules.gci.models.task import CLAIMABLE
from soc.modules.gci.models.task import GCITask
from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views.helper.url_patterns import url
from soc.modules.gci.views.helper import url_names


_BAN_ORGANIZATION_HELP_TEST = ugettext(
    'When an organization is banned, students cannot work on their tasks')

class AboutUs(Template):
  """About us template."""

  def __init__(self, data):
    self.data = data

  def context(self):
    org = self.data.organization
    return {
        'description': org.description,
        'logo_url': org.logo_url,
        'homepage': org.home_page,
        'short_name': org.short_name,
    }

  def templatePath(self):
    return 'modules/gci/org_home/_about_us.html'


class ContactUs(Template):
  """Organization Contact template."""

  def __init__(self, data):
    self.data = data

  def context(self):
    return {
        'organization': self.data.organization,
    }

  def templatePath(self):
    return "modules/gci/org_home/_contact_us.html"


class OpenTasksList(Template):
  """List to display all the open tasks for the current organization."""

  def __init__(self, data):
    self.data = data
    list_config = lists.ListConfiguration()

    list_config.addSimpleColumn('title', 'Title')
    #list_config.addPlainTextColumn(
    #    'task_type', 'Type',
    #    lambda entity, all_d, all_t, *args: entity.taskType(all_t))
    #list_config.addPlainTextColumn('arbit_tag', 'Tags', lambda entity,
    #                      *args: entity.taskArbitTag())
    list_config.addPlainTextColumn('time_to_complete', 'Time to complete',
                          lambda entity, *args: entity.taskTimeToComplete())
    list_config.addPlainTextColumn('types', 'Type',
                          lambda entity, *args: ", ".join(entity.types))

    list_config.setRowAction(
        lambda e, *args: data.redirect.id(e.key().id()).urlOf(url_names.GCI_VIEW_TASK))

    self.list_config = list_config

  def context(self):
    description = 'List of all Open tasks.'
    return {
        'lists': [lists.ListConfigurationResponse(
            self.data, self.list_config, 0, description)],
    }

  def getListData(self):
    if lists.getListIndex(self.data.request) != 0:
      return None
    q = GCITask.all()
    q.filter('org', self.data.organization)
    q.filter('status IN', CLAIMABLE)
    starter = lists.keyStarter

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self.list_config, q, starter)
    return response_builder.build()

  def templatePath(self):
    return 'modules/gci/org_home/_open_tasks.html'

class CompletedTasksList(Template):
  """List to display all the closed/completed tasks for the current organization."""

  def __init__(self, data):
    self.data = data

    list_config = lists.ListConfiguration()

    list_config.addSimpleColumn('title', 'Title')
    list_config.addPlainTextColumn('student', 'Student',
        lambda entity, *args: entity.student.name())
    list_config.addPlainTextColumn('types', 'Type',
        lambda entity, *args: ", ".join(entity.types))

    list_config.setRowAction(
        lambda e, *args: data.redirect.id(e.key().id()).urlOf(
            url_names.GCI_VIEW_TASK))

    self.list_config = list_config

  def context(self):
    description = 'List of all Completed tasks.'
    return {
        'lists': [lists.ListConfigurationResponse(
            self.data, self.list_config, 1, description)],
    }

  def getListData(self):
    if lists.getListIndex(self.data.request) != 1:
      return None
    q = GCITask.all()
    q.filter('org', self.data.organization)
    q.filter('status', 'Closed')
    starter = lists.keyStarter

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self.list_config, q, starter)
    return response_builder.build()

  def templatePath(self):
    return 'modules/gci/org_home/_closed_tasks.html'


class GCIBanOrgPost(BanOrgPost, GCIRequestHandler):
  """Handles banning/unbanning of GCI organizations."""

  def _getModulePrefix(self):
    return 'gci'

  def _getURLPattern(self):
    return url_patterns.ORG

  def _getURLName(self):
    return url_names.GCI_ORG_BAN

  def _getOrgModel(self):
    return GCIOrganization


class HostActions(Template):
  """Template to render the left side host actions.
  """

  def __init__(self, data):
    super(HostActions, self).__init__(data)
    self.toggle_buttons = []

  def context(self):
    is_banned = self.data.organization.status == 'invalid'

    org_banned = toggle_button.ToggleButtonTemplate(
        self.data, 'on_off', 'Banned', 'organization-banned',
        links.LINKER.organization(
            self.data.organization.key(), url_names.GCI_ORG_BAN),
        checked=is_banned,
        help_text=_BAN_ORGANIZATION_HELP_TEST,
        labels={
            'checked': 'Yes',
            'unchecked': 'No'})
    self.toggle_buttons.append(org_banned)

    context = {
        'title': 'Host Actions',
        'toggle_buttons': self.toggle_buttons,
        }

    return context

  def templatePath(self):
    """See template.Template.templatePath for specification."""
    return 'modules/gci/_user_action.html'


class OrgHomepage(GCIRequestHandler):
  """Encapsulates all the methods required to render the org homepage."""

  access_checker = access.ALL_ALLOWED_ACCESS_CHECKER

  def templatePath(self):
    return 'modules/gci/org_home/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'org/%s$' % url_patterns.ORG, self,
            name=url_names.GCI_ORG_HOME),
        url(r'org/home/%s' % url_patterns.ORG, self),
    ]

  def jsonContext(self, data, check, mutator):
    idx = lists.getListIndex(data.request)
    list_content = None
    if idx == 0:
      list_content = OpenTasksList(data).getListData()
    elif idx == 1:
      list_content = CompletedTasksList(data).getListData()

    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def context(self, data, check, mutator):
    context = {
        'page_name': '%s - Home page' % data.organization.name,
        'about_us': AboutUs(data),
        'contact_us': ContactUs(data),
        'feed_url': data.organization.feed_url,
    }

    if data.timeline.tasksPubliclyVisible():
      context['open_tasks_list'] = OpenTasksList(data)
      context['completed_tasks_list'] = CompletedTasksList(data)

    if data.is_host or accounts.isDeveloper():
      context['host_actions'] = HostActions(data)

    return context
