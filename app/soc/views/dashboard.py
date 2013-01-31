#!/usr/bin/env python2.5
#
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


from django.utils.translation import ugettext

from soc.views.template import Template


class Component(Template):
  """Base component for the list component.
  """

  def __init__(self, request, data):
    """Initializes the list component.

    Args:
      request: The HTTPRequest object
      data: The RequestData object
    """
    self.request = request
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


class Dashboard(Template):
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

  def __init__(self, request, data, subpages=None):
    """Initializes the dashboard.

    Args:
      request: The HTTPRequest object
      data: The RequestData object
      subpages: Subpages of current dashboard
    """
    self.request = request
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
