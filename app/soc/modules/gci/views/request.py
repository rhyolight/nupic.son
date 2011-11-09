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

"""Module containing the view for GCI request page.
"""

__authors__ = [
  '"Daniel Hans" <daniel.m.hans@gmail.com>',
  ]


from soc.views.helper import url_patterns

from soc.modules.gci.models.request import GCIRequest

from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.base import RequestHandler
from soc.modules.gci.views.helper.url_patterns import url


class RequestForm(gci_forms.GCIModelForm):
  """Django form for the invite page.
  """

  class Meta:
    model = GCIRequest
    css_prefix = 'gci_intivation'
    fields = ['message']

class SendRequestPage(RequestHandler):
  """Encapsulate all the methods required to generate Send Request page.
  """

  def templatePath(self):
    return 'v2/modules/gci/request/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'request/send/%s$' % url_patterns.REQUEST,
            self, name='gci_send_request')
    ]

  def checkAccess(self):
    """Access checks for GCI Send Request page.
    """
    #TODO(dhans): check if the program is visible
    # check if the user has a profile
    # check if the user is not a student
    # check if the user does not have role for the organization


  def context(self):
    """Handler to for GCI Send Request page HTTP get request.
    """

    request_form = RequestForm(self.data.POST or None)

    return {
        'logout_link': self.data.redirect.logout(),
        'forms': [request_form],
        'page_name': self._constructPageName()
        }

  def _constructPageName(self):
    role = 'Mentor' if self.data.kwargs['role'] == 'mentor' else 'Org Admin'

    return "Request to become %s" % role


class ManageRequest(RequestHandler):
  """View to manage the invitation by the sender.
  """

  def templatePath(self):
    return 'v2/modules/gci/request/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'request/manage/%s$' % url_patterns.ID, self,
            name='manage_gci_request')
    ]

  def checkAccess(self):
    self.check.isProfileActive()
    
    request_id = int(self.data.kwargs['id'])
    self.data.request = GCIRequest.get_by_id(request_id)
    self.check.isInvitePresent(request_id)
