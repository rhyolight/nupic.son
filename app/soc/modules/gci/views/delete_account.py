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

"""Module for the GCI delete account page."""

from soc.logic import delete_account

from soc.views.helper import url_patterns

from soc.modules.gci.views import base
from soc.modules.gci.views.helper.url_patterns import url


class DeleteAccountPage(base.GCIRequestHandler):
  """View for the GCI delete account page."""

  def templatePath(self):
    return 'modules/gci/delete_account/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'delete_account/%s$' % url_patterns.PROGRAM,
            self, name='gci_delete_account')
    ]

  def checkAccess(self, data, check, mutator):
    check.isLoggedIn()

  def context(self, data, check, mutator):
    return {
        'page_name': 'Delete your account'
        }

  def post(self, data, check, mutator):
    delete_account.request_account_deletion(data.user)
    # TODO(nathaniel): make this .program() call unnecessary.
    data.redirect.program()

    return data.redirect.to('gci_delete_account', validated=True)
