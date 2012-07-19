#!/usr/bin/env python
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

"""Module containing the views for Organization Homepage.
"""


from google.appengine.ext import db

from soc.views.helper import url_patterns
from soc.views.helper.access_checker import isSet


class BanOrgPost(object):
  """Handles banning/unbanning of organizations.
  """

  def djangoURLPatterns(self):
    return [
         url_patterns.url(
             self._getModulePrefix(),
             r'organization/ban/%s$' % self._getURLPattern(),
             self, name=self._getURLName()),
    ]

  def checkAccess(self):
    self.check.isHost();

  def post(self):
    assert isSet(self.data.organization)
    
    value = self.data.POST.get('value')
    org_key = self.data.organization.key()

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

  def _getModulePrefix(self):
    raise NotImplementedError

  def _getURLPattern(self):
    raise NotImplementedError

  def _getURLName(self):
    raise NotImplementedError

  def _getOrgModel(self):
    raise NotImplementedError
