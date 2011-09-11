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

"""Module containing the views for GCI home page.
"""

__authors__ = [
  '"Madhusudan.C.S" <madhusudancs@gmail.com>',
  ]


from soc.views.helper import url_patterns

from soc.modules.gci.views.base import RequestHandler
from soc.modules.gci.views.helper.url_patterns import url


class Homepage(RequestHandler):
  """Encapsulate all the methods required to generate GSoC Home page.
  """

  def templatePath(self):
    return 'v2/modules/gci/homepage/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'homepage/%s$' % url_patterns.PROGRAM, self,
            name='gci_homepage'),
        url(r'program/home/%s$' % url_patterns.PROGRAM, self),
    ]

  def checkAccess(self):
    pass

  def context(self):
    current_timeline = self.data.timeline.currentPeriod()
    next_deadline = self.data.timeline.nextDeadline()

    context = {
        'page_name': '%s - Home page' % (self.data.program.name),
        'program': self.data.program,
    }

    return context
