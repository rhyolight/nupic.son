#!/usr/bin/env python2.5
#
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

"""Module containing the view for GCI winners page.
"""


from soc.views.helper import url_patterns

from soc.modules.gci.logic.ranking import winnersForProgram
from soc.modules.gci.views import common_templates
from soc.modules.gci.views.base import RequestHandler
from soc.modules.gci.views.helper import url_names
from soc.modules.gci.views.helper.url_patterns import url


class WinnersPage(RequestHandler):
  """View for the winners page.
  """

  def templatePath(self):
    return 'v2/modules/gci/winners/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'winners/%s$' % url_patterns.PROGRAM, self,
            name=url_names.GCI_WINNERS),
    ]

  def checkAccess(self):
    self.check.areWinnersVisible()

  def context(self):
    winners = winnersForProgram(self.data)

    #e.parent().name()
    #e.tasks()
    return {
        'page_name': "Winners of %s" % self.data.program.name,
        'winners': winners,
        'your_score': common_templates.YourScore(self.data),
        'program_select': common_templates.ProgramSelect(
            self.data, url_names.GCI_WINNERS),
    }
