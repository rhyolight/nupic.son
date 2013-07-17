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

"""Module containing Tabs template."""

from soc.views import template


class Tab(object):
  """Single tab that can be included in the list of tabs."""

  def __init__(self, tab_id, name, url):
    """Initializes a new instance of this class.

    Args:
      tab_id: identifier of the tab.
      name: name of the tab that to be displayed on the page.
      url: URL address to which the tab redirects upon clicking.
      is_selected: whether the tab should be rendered as currently selected.
    """
    self.tab_id = tab_id
    self.name = name
    self.url = url


class Tabs(template.Template):
  """Template for a list of tabs.

  It can be used to form additional dynamic menu that consists of tabs.
  Each tab represents a single element of that list and has its own
  displayable name as well as URL address to which it links. 
  """

  def __init__(self, data, template_path, tabs, selected_tab_id):
    """Initializes a new instance of this class.

    Please note that it is not recommended that more than one of the specified
    tabs are declared as selected.

    Args:
      data: request_data.RequestData object for the current request.
      template_path: path to the HTML template to use for rendering
      tabs: list of Tab objects to be included.
      selected_tab_id: identifier of the tab that should be initially selected.
    """
    super(Tabs, self).__init__(data)
    self._template_path = template_path
    self.tabs = tabs
    self.selected_tab_id = selected_tab_id

  def templatePath(self):
    """See template.Template.templatePath for specification."""
    return self._template_path

  def context(self):
    """See template.Template.context for specification."""
    return {'tabs': self}
