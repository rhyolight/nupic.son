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

"""Module containing template with a list of conversations."""

from soc.views.helper import lists
from soc.views import template


class ConversationList(template.Template):
  """Template for list of conversations."""

  def __init__(self, data):
    self.data = data
    self._list_config = self._getListConfig()

  def context(self):
    """See soc.views.template.Template.context for full specification."""
    description = self._getDescription()

    return {
        'lists': [lists.ListConfigurationResponse(
            self.data, self._list_config, 0, description)],
    }

  def getListData(self):
    """Makes a soc.views.helper.lists.ListContentResponse for the request.

    Returns:
      If the requested list index is 0, the ListContentResponse for the query,
      otherwise None.
    """
    idx = lists.getListIndex(self.data.request)
    if idx == 0:
      query = self._getQuery()

      starter = lists.keyStarter

      response_builder = lists.RawQueryContentResponseBuilder(
          self.data.request, self._list_config, query, starter)
      return response_builder.build()
    else:
      return None

  def templatePath(self):
    """See soc.views.template.Template.templatePath for full specification."""
    return "modules/gci/conversations/_conversations.html"

  def _getDescription(self):
    """Returns the string of a description of the list which is displayed above
    it.

    Concrete subclasses must override this method.
    """
    raise NotImplementedError()

  def _getListConfig(self):
    """Returns the soc.views.helper.lists.ListConfiguration which contains
    the configuration for this list and its rows.

    Concrete subclasses must override this method.
    """
    raise NotImplementedError()

  def _getQuery(self):
    """Returns the datastore query for this lists's data.

    Concrete subclasses must override this method.
    """
    raise NotImplementedError()
