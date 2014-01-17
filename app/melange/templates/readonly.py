# Copyright 2014 the Melange authors.
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

"""Module containing a template to display read-only sets of data."""

from soc.views import template
from django.template import loader


class Group(object):
  """Class that forms different fields together into a group.

  Attributes:
    title: Title of the group.
    fields: Fields that belong to the group.
  """

  def __init__(self, title, fields):
    """Initializes a new group for the specified attributes.

    Args:
      title: Title of the group.
      fields: A dict containing label-value pairs that belong to the group.
    """
    self.title = title
    self.fields = fields


class Readonly(template.Template):
  """Template to list items in read-only manner."""

  def __init__(self, data, template_path, groups):
    """Initializes a new instance of this class.

    Please note that it is not recommended that more than one of the specified
    tabs are declared as selected.

    Args:
      data: request_data.RequestData object for the current request.
      template_path: Path to the HTML template to use for rendering.
      groups: List of groups to include in the template.
    """
    super(Readonly, self).__init__(data)
    self._template_path = template_path
    self._groups = groups

  def render(self):
    """Renders the template as HTML.

    Returns:
      A string containing HTML form of the template.
    """
    context = {'groups': self._groups}
    return loader.render_to_string(self._template_path, dictionary=context)
