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

"""Module for the GCI participant dashboard.
"""

__authors__ = [
  '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]

from soc.views.helper import url_patterns

from soc.modules.gci.views.base import RequestHandler
from soc.modules.gci.views.helper.url_patterns import url


class Dashboard(RequestHandler):
  """View for the participant dashboard.
  """

  def djangoURLPatterns(self):
    """The URL pattern for the dashboard.
    """
    return [
        url(r'dashboard/%s$' % url_patterns.PROGRAM, self,
            name='gci_dashbaord')]

  def checkAccess(self):
    """Denies access if you are not logged in.
    """
    self.check.isLoggedIn()

  def templatePath(self):
    """Returns the path to the template.
    """
    return 'v2/modules/gci/dashboard/base.html'

  def context(self):
    """Handler for default HTTP GET request.
    """
    components = self.components()

    return {
        'page_name': self.data.program.name,
        'user_name': self.data.profile.name() if self.data.profile else None,
    # TODO(ljvderijk): Implement code for setting dashboard messages.
    #   'alert_msg': 'Default <strong>alert</strong> goes here',
        'components': components
    }

  def components(self):
    """
    """
    return []

