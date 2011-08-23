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

"""Base module for participant dashboards.
"""

__authors__ = [
  '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]

from soc.views.template import Template


class Component(Template):
  """Base component for the dashboard.
  """

  def __init__(self, request, data):
    """Initializes the component.

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

