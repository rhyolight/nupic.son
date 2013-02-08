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

from soc.modules.gci.logic import profile as profile_logic
from soc.modules.gci.views import base
from soc.modules.gci.views.helper import url_patterns as gci_url_patterns


class ModerateDeleteAccountPage(base.GCIRequestHandler):
  """View for the GCI delete account page."""

  def templatePath(self):
    return 'v2/modules/gci/moderate_delete_account/base.html'

  def djangoURLPatterns(self):
    return [
        gci_url_patterns.url(
            r'admin/delete_account/%s$' % url_patterns.PROFILE, self,
            name='gci_moderate_delete_account'),
    ]

  def checkAccess(self):
    self.check.isHost()

    self.mutator.profileFromKwargs()

  def context(self, data, check, mutator):
    profile = data.url_profile

    return {
        'page_name': 'Moderate delete account requests',
        'profile': profile,
        'has_tasks': profile_logic.hasTasks(profile),
        'has_created_or_modified_tasks': profile_logic.hasCreatedOrModifiedTask(
            profile),
        'has_task_comments': profile_logic.hasTaskComments(profile),
        'has_other_gci_profiles': profile_logic.hasOtherGCIProfiles(profile),
        'has_other_gsoc_profiles': profile_logic.hasOtherGSoCProfiles(profile),
        }

  def post(self, data, check, mutator):
    link_id = data.url_profile.link_id
    delete_account.confirm_delete(data.url_profile)
    # TODO(nathaniel): Self-redirection.
    return data.redirect.profile(link_id).to(
        'gci_moderate_delete_account', validated=True)
