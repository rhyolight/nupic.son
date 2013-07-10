# Copyright 2012 the Melange authors.
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

"""Module containing template with a list of GCIOrganization entities."""

from soc.views.helper import lists
from soc.views.template import Template

from soc.modules.gci.logic import organization as org_logic


class OrgList(Template):
  """Template for list of organizations."""

  def __init__(self, data):
    self.data = data

    self._list_config = self._getListConfig()

  def context(self):
    description = self._getDescription()

    return {
        'lists': [lists.ListConfigurationResponse(
            self.data, self._list_config, 0, description)],
    }

  def getListData(self):
    idx = lists.getListIndex(self.data.request)
    if idx == 0:
      query = self._getQuery()

      starter = lists.keyStarter
      prefetcher = self._getPrefetcher()

      response_builder = lists.RawQueryContentResponseBuilder(
          self.data.request, self._list_config, query, starter,
          prefetcher=prefetcher)
      return response_builder.build()
    else:
      return None

  def templatePath(self):
    return "modules/gci/accepted_orgs/_project_list.html"

  def _getDescription(self):
    raise NotImplementedError

  def _getListConfig(self):
    raise NotImplementedError

  def _getPrefetcher(self):
    return None

  def _getQuery(self):
    raise NotImplementedError


class BasicOrgList(OrgList):
  """Basic list of all organizations that displays in each row
  link_id and name with a custom redirect.
  """

  def _getListConfig(self):
    """Returns ListConfiguration object for the list.
    """
    list_config = lists.ListConfiguration()
    list_config.addPlainTextColumn('name', 'Name',
        lambda e, *args: e.name.strip())
    list_config.addSimpleColumn('link_id', 'Organization ID', hidden=True)
    list_config.setRowAction(self._getRedirect())
    return list_config

  def _getQuery(self):
    """Returns Query object to fetch entities for the list.
    """
    return org_logic.queryForProgramAndStatus(
        self.data.program, ['new', 'active'])

  def _getRedirect(self):
    """Returns redirect function for each row of the list.
    """
    raise NotImplementedError
