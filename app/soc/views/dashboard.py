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

"""Module for rendering dashboard and component list.

The classes in this module are intended to serve as base classes for
iconic dashboard (Dashboard) and component list (Component).
"""

from django.utils import translation

# TODO(daniel): URLs must be injected depending on the program
from codein.views.helper import urls

from melange.request import links

from soc.views import template


class Component(template.Template):
  """Base component for the list component."""

  def __init__(self, data):
    """Initializes the list component.

    Args:
      data: The RequestData object
    """
    self.data = data

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    # by default no list is present
    return None

  def post(self):
    """Handles a post request.

    If posting to the list as requested is not supported by this component
    False is returned.
    """
    # by default post is not supported
    return False


class Dashboard(template.Template):
  """Base template to render iconic dashboard.

  This class cannot be instantiated directly. Iconic dashboard must be
  implemented by derived classes with at least title, name, and subpages set in
  the context. Dashboard can be nested by supplying subpages_link's context.
  Dashboard also can be rendered as a list component container by
  supplying component's context (with list component as its value).

  See soc.modules.gsoc.views.admin.MainDashboard and
  soc.modules.gsoc.views.dashboard.ComponentsDashboard as an example of iconic
  dashboard implementation.
  """

  def __init__(self, data, subpages=None):
    """Initializes the dashboard.

    Args:
      data: The RequestData object
      subpages: Subpages of current dashboard
    """
    self.data = data
    self.subpages = subpages

  def getSubpagesLink(self):
    """Returns the link to other dashboard that appears
    on top of the dashboard.
    """
    return self.subpages

  def templatePath(self):
    """Returns the path to the template that should be used in render()
    """
    return 'soc/dashboard/base.html'

  def _divideSubPages(self, subpages):
    """Returns the subpages divided into two columns.
    """
    middle_ceil = (len(subpages) + 1) / 2

    return [
        subpages[:middle_ceil],
        subpages[middle_ceil:],
    ]


def _initMainDashboardSubpages(data):
  """Initializes list of subpages for the main dashboard.

  Args:
    request_data.RequestData for the current request.

  Returns:
    initial list of subpages to set for the main dashboard.
  """
  if False:
  # TODO(daniel): re-enable when connection views are back
  #if not data.profile.is_student and data.timeline.orgsAnnounced():
    connection_dashboard = ConnectionsDashboard(data)

    return [{
        'name': 'connections_dashboard',
        'description': translation.ugettext(
            'Connect with organizations, check current status and '
            'participate in the program.'),
        'title': 'Connections',
        'link': '',
        'subpage_links': connection_dashboard.getSubpagesLink(),
        }]
  else:
    return []


class ConnectionsDashboard(Dashboard):
  """Dashboard grouping connection related elements."""

  def __init__(self, data):
    """Initializes new instance of this class.

    Args:
      data: request_data.RequestData for the current request.
    """
    super(ConnectionsDashboard, self).__init__(data)
    self.subpages = _initConnectionDashboardSubpages(data)


  def context(self):
    """See dashboard.Dashboard.context for specification."""
    subpages = self._divideSubPages(self.subpages)

    return {
        'title': 'Connections',
        'name': 'connections_dashboard',
        'backlinks': [
            {
                'to': 'main',
                'title': 'Participant dashboard'
            },
        ],
        'subpages': subpages
    }


def _initConnectionDashboardSubpages(data):
  """Initializes list of subpages for the connection dashboard.

  Args:
    data: request_data.RequestData for the current request.

  Returns:
    initial list of subpages to set for the connection dashboard.
  """
  subpages = [
      {
          'name': 'list_connections_for_user',
          'description': translation.ugettext(
              'Check status of your existing connections with '
              'organizations and communicate with administrators.'),
          'title': translation.ugettext('See your connections'),
          'link': links.LINKER.program(
              data.program, urls.UrlNames.CONNECTION_PICK_ORG)
      },
      {
          'name': 'connect',
          'description': translation.ugettext(
              'Connect with organizations and request a role to '
              'participate in the program.'),
          'title': translation.ugettext('Connect with organizations'),
          'link': links.LINKER.program(
              data.program, urls.UrlNames.CONNECTION_PICK_ORG)
      }]

  # add organization admin specific items
  if data.ndb_profile.is_admin:
    subpages.append({
        'name': 'list_connections_for_org_admin',
        'description': translation.ugettext(
            'Manage connections for the organizations for which you have '
            'administrator role at this moment.'),
        'title': translation.ugettext('See organization\'s connections'),
        'link': links.LINKER.profile(
            data.ndb_profile, urls.UrlNames.CONNECTION_LIST_FOR_ORG_ADMIN)
        })

    for org in data.org_admin_for:
      subpages.append({
          'name': 'connect_for_%s' % org.link_id,
          'description': translation.ugettext(
              'Connect with users and offer them role in your '
              'organization.'),
          'title': translation.ugettext('Connect users with %s' % org.name),
          'link': links.LINKER.organization(
              org.key(), urls.UrlNames.CONNECTION_START_AS_ORG)
          })

  return subpages
