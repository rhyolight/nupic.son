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

"""Module containing the views for Organization Homepage."""

from google.appengine.ext import db

from django import http

from soc.views.helper import url_patterns
from soc.views.helper.access_checker import isSet
from soc.views.template import Template
from soc.views.toggle_button import ToggleButtonTemplate


class BanOrgPost(object):
  """Handles banning/unbanning of organizations."""

  def djangoURLPatterns(self):
    return [
         url_patterns.url(
             self._getModulePrefix(),
             r'organization/ban/%s$' % self._getURLPattern(),
             self, name=self._getURLName()),
    ]

  def checkAccess(self):
    self.check.isHost();

  def post(self, data, check, mutator):
    """See soc.views.base.RequestHandler.post for specification."""
    assert isSet(data.organization)

    value = data.POST.get('value')
    org_key = data.organization.key()

    def banOrgTxn(value):
      org_model = self._getOrgModel()
      org = org_model.get(org_key)
      if value == 'unchecked' and org.status == 'active':
        org.status = 'invalid'
        org.put()
      elif value == 'checked' and org.status == 'invalid':
        org.status = 'active'
        org.put()

    db.run_in_transaction(banOrgTxn, value)

    return http.HttpResponse()

  def _getModulePrefix(self):
    raise NotImplementedError

  def _getURLPattern(self):
    raise NotImplementedError

  def _getURLName(self):
    raise NotImplementedError

  def _getOrgModel(self):
    raise NotImplementedError


class HostActions(Template):
  """Template to render the left side host actions.
  """

  def __init__(self, data):
    super(HostActions, self).__init__(data)
    self.toggle_buttons = []

  def context(self):
    assert isSet(self.data.organization)

    # TODO(nathaniel): make this .organization() call unnecessary.
    self.data.redirect.organization()

    is_banned = self.data.organization.status == 'invalid'

    org_banned = ToggleButtonTemplate(
        self.data, 'on_off', 'Banned', 'organization-banned',
        self.data.redirect.urlOf(self._getActionURLName()),
        checked=is_banned,
        help_text=self._getHelpText(),
        labels={
            'checked': 'Yes',
            'unchecked': 'No'})
    self.toggle_buttons.append(org_banned)

    context = {
        'title': 'Host Actions',
        'toggle_buttons': self.toggle_buttons,
        }

    return context

  def templatePath(self):
    return "soc/_user_action.html"

  def _getActionURLName(self):
    raise NotImplementedError

  def _getHelpText(self):
    raise NotImplementedError
