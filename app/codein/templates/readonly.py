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

"""Module containing a template to display items in read-only manner."""

import collections

from soc.views import template


class ReadOnlyTemplate(template.Template):
  """Template to display a list of read-only items."""

  def __init__(self, data):
    """Initializes new instance of read-only template.

    Args:
      data: request_data.RequestData for the current request.
    """
    super(ReadOnlyTemplate, self).__init__(data)
    self._items = collections.OrderedDict()

  def addItem(self, label, value):
    """Adds an arbitrary item with the specified label and value.

    Args:
      label: a string containing a label for the item.
      value: a string containing a value of the item.
    """
    self._items[label] = value

  def templatePath(self):
    """See template.Template.templatePath for specification."""
    return 'codein/readonly/_readonly.html'

  def context(self):
    """See template.Template.context for specification."""
    return {'items': self._items}
