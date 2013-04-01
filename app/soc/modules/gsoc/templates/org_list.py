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

"""Module for templates with organizations list."""

from django.utils import html as http_utils

from soc.views import template
from soc.views.helper import lists

from soc.modules.gsoc.models import organization as org_model
from soc.modules.gsoc.models import profile as profile_model


class AcceptedOrgsList(template.Template):
  """Template for list of accepted organizations."""

  def __init__(self, data):
    self.data = data

    self._list_config = self._getListConfig()

  def context(self):
    description = 'List of organizations accepted into %s' % (
        self.data.program.name)

    list = lists.ListConfigurationResponse(
        self.data, self._list_config, 0, description)

    return {
        'lists': [list],
    }

  def getListData(self):
    idx = lists.getListIndex(self.data.request)
    if idx != 0:
      return None

    starter = lists.keyStarter
    query = self._getQuery()
    prefetcher = self._getPrefetcher()

    response_builder = lists.RawQueryContentResponseBuilder(self.data.request,
        self._list_config, query, starter, prefetcher=prefetcher)

    return response_builder.build()

  def templatePath(self):
    return "v2/modules/gsoc/admin/_accepted_orgs_list.html"

  def _getListConfig(self):
    """Returns list configuration for the list.

    It must be overridden by subclasses.

    Returns:
      new ListConfiguration object.
    """
    raise NotImplementedError

  def _getPrefetcher(self):
    """Returns a prefetcher for the list.

    It may be overridden by subclasses. By default no prefetcher is returned.

    Returns:
      a function to prefetch entities for the list or None
    """
    return None

  def _getQuery(self):
    """Returns a query to fetch organizations for the list.

    It must be overridden by subclasses.

    Returns:
      a db.Query to fetch entities for the list
    """
    raise NotImplementedError
