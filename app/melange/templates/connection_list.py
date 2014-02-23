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

"""Module for templates with connection lists."""

from django.utils import translation

from melange.logic import connection as connection_logic
from melange.models import connection as connection_model
from melange.request import links

from soc.views import template
from soc.views.helper import lists


_CONNECTION_LIST_TITLE = translation.ugettext('Connections')

ORG_ADMIN_CONNECTION_LIST_DESCRIPTION = translation.ugettext(
    'List of connections with mentors and admins for my organizations.')

USER_CONNECTION_LIST_DESCRIPTION = translation.ugettext(
    'List of my connections with organizations.')

class ConnectionList(template.Template):
  """Template for list of connections."""

  def __init__(self, url_names, template_path, data):
    """Initializes a new instance of the list for the specified parameters.

    Args:
      url_names: Instance of url_names.UrlNames.
      template_path: The path of the template to be used.
      data: request_data.RequestData for the current request.
    """
    super(ConnectionList, self).__init__(data)
    self.url_names = url_names
    self.template_path = template_path
    self._list_config = self._getListConfig()

  def context(self):
    """See template.Template.context for specification."""
    description = self._getDescription()

    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, 0, description)

    return {
        'list_title': _CONNECTION_LIST_TITLE,
        'lists': [list_configuration_response]
        }

  def getListData(self):
    # TODO(daniel): add missing doc string
    idx = lists.getListIndex(self.data.request)
    if idx != 0:
      return None

    query = self._getQuery()
    prefetcher = self._getPrefetcher()

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, query,
        lists.keyStarter, prefetcher=prefetcher)

    return response_builder.buildNDB()

  def _getListConfig(self):
    """Returns list configuration for the list.

    It must be overridden by subclasses.

    Returns:
      new lists.ListConfiguration object.
    """
    raise NotImplementedError

  def _getQuery(self):
    """Returns a query to fetch connections for the list.

    It must be overridden by subclasses.

    Returns:
      a db.Query to fetch entities for the list
    """
    raise NotImplementedError

  def _getPrefetcher(self):
    """Returns a lists.Prefetcher for the list.

    It may be overridden by subclasses. By default no prefetcher is returned.

    Returns:
      a lists.Prefetcher object or None
    """
    return None


class UserConnectionList(ConnectionList):
  """Template for list of all connections for a particular user."""

  def _getDescription(self):
    """See ConnectionList._getDescription for specification."""
    return USER_CONNECTION_LIST_DESCRIPTION

  def _getQuery(self):
    """See ConnectionList._getQuery for specification."""
    return connection_logic.queryForAncestor(self.data.ndb_profile.key)

  def _getListConfig(self):
    """See ConnectionList._getListConfig for specification."""
    list_config = lists.ListConfiguration(add_key_column=False)
    list_config.addPlainTextColumn('key', 'Key',
        lambda e, *args: e.keyName(), hidden=True)
    list_config.addPlainTextColumn('organization', 'Organization',
        lambda e, *args: e.organization.get().name)
    list_config.addPlainTextColumn('role', 'Role',
        lambda e, *args: connection_model.VERBOSE_ROLE_NAMES[e.getRole()])
    list_config.addDateColumn('last_modified', 'Last Modified On',
        lambda e, *args: e.last_modified)

    list_config.setRowAction(
        lambda e, *args: links.LINKER.userId(
            e.key.parent(), e.key.id(),
            self.url_names.CONNECTION_MANAGE_AS_USER))

    return list_config


class OrgAdminConnectionList(ConnectionList):
  """Template for list of all connections for a particular
  organization administrator.
  """

  def _getDescription(self):
    """See ConnectionList._getDescription for specification."""
    return ORG_ADMIN_CONNECTION_LIST_DESCRIPTION

  def _getQuery(self):
    """See ConnectionList._getQuery for specification."""
    if len(self.data.url_ndb_profile.admin_for) > 1:
      # explicit order by __key__ is required for MultiQuery,
      # i.e. a query with IN filter.
      return connection_logic.queryForOrganizations(
          self.data.url_ndb_profile.admin_for).order(
              connection_model.Connection._key)
    else:
      return connection_logic.queryForOrganizations(
          self.data.url_ndb_profile.admin_for)

  def _getListConfig(self):
    """See ConnectionList._getListConfig for specification."""
    list_config = lists.ListConfiguration(add_key_column=False)
    list_config.addPlainTextColumn('key', 'Key',
        lambda e, *args: e.keyName(), hidden=True)

    list_config.addPlainTextColumn('username', 'Username',
        lambda e, *args: e.key.parent().parent().id())

    # organization column is added only when the user is an admin for
    # more than one organization
    if len(self.data.url_ndb_profile.admin_for) > 1:
      list_config.addPlainTextColumn('organization', 'Organization',
          lambda e, *args: e.organization.name)

    list_config.addPlainTextColumn('role', 'Role',
        lambda e, *args: connection_model.VERBOSE_ROLE_NAMES[e.getRole()])
    list_config.addDateColumn('last_modified', 'Last Modified On',
        lambda e, *args: e.last_modified)

    list_config.setRowAction(
        lambda e, *args: links.LINKER.userId(
            e.key.parent(), e.key.id(),
            self.url_names.CONNECTION_MANAGE_AS_ORG))

    return list_config
