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


ORG_ADMIN_CONNECTION_LIST_DESCRIPTION = translation.ugettext(
    'List of connections with mentors and admins for my organizations.')

USER_CONNECTION_LIST_DESCRIPTION = translation.ugettext(
    'List of my connections with organizations.')

class ConnectionList(template.Template):
  """Template for list of connections."""

  def __init__(self, data):
    """See template.Template.__init__ for specification."""
    super(ConnectionList, self).__init__(data)
    self._list_config = self._getListConfig()

  def context(self):
    """See template.Template.context for specification."""
    description = self._getDescription()

    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, 0, description)

    return {'lists': [list_configuration_response]}

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

    return response_builder.build()

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
    return connection_logic.queryForAncestor(self.data.url_profile)

  def _getListConfig(self):
    """See ConnectionList._getListConfig for specification."""
    list_config = lists.ListConfiguration(add_key_column=False)
    list_config.addPlainTextColumn('key', 'Key',
        lambda e, *args: e.keyName(), hidden=True)
    list_config.addPlainTextColumn('organization', 'Organization',
        lambda e, *args: e.organization.name)
    list_config.addPlainTextColumn('role', 'Role',
        lambda e, *args: connection_model.VERBOSE_ROLE_NAMES[e.getRole()])
    list_config.addDateColumn('last_modified', 'Last Modified On',
        lambda e, *args: e.last_modified)

    list_config.setRowAction(
        lambda e, *args: links.LINKER.userId(
            e.parent_key(), e.key().id(),
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
    return connection_logic.queryForOrganizationAdmin(self.data.url_profile)

  def _getListConfig(self):
    """See ConnectionList._getListConfig for specification."""
    list_config = lists.ListConfiguration(add_key_column=False)
    list_config.addPlainTextColumn('key', 'Key',
        lambda e, *args: e.keyName(), hidden=True)

    list_config.addPlainTextColumn('user', 'User',
        lambda e, *args: e.parent_key().parent().name())

    # organization column is added only when the user is an admin for
    # more than one organization
    if len(self.data.url_profile.org_admin_for) > 1:
      list_config.addPlainTextColumn('organization', 'Organization',
          lambda e, *args: e.organization.name)

    list_config.addPlainTextColumn('role', 'Role',
        lambda e, *args: connection_model.VERBOSE_ROLE_NAMES[e.getRole()])
    list_config.addDateColumn('last_modified', 'Last Modified On',
        lambda e, *args: e.last_modified)

    list_config.setRowAction(
        lambda e, *args: links.LINKER.userId(
            e.parent_key(), e.key().id(),
            self.url_names.CONNECTION_MANAGE_AS_ORG))

    return list_config
