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

"""Module for displaying the GSoC profile read only page.
"""

__authors__ = [
  '"Madhusudan.C.S" <madhusudancs@gmail.com>',
  ]


from django.conf.urls.defaults import url

from soc.views import readonly_template
from soc.views.helper.access_checker import isSet

from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.base_templates import LoggedInMsg
from soc.modules.gsoc.views.helper import url_patterns


class ProfileReadOnlyTemplate(readonly_template.ModelReadOnlyTemplate):
  """Template to construct readonly Profile data.
  """

  class Meta:
    model = GSoCProfile
    css_prefix = 'gsoc_profile_show'
    exclude = ['link_id', 'user', 'scope', 'mentor_for', 'org_admin_for',
               'student_info', 'agreed_to_tos_on', 'scope_path', 'status',
               'name_on_documents', 'agreed_to_tos', 'notify_new_requests',
               'notify_new_proposals', 'notify_proposal_updates',
               'notify_public_comments', 'notify_private_comments',
               'is_mentor', 'is_org_admin']


class ProfileShowPage(RequestHandler):
  """View to display the readonly profile page.
  """

  def djangoURLPatterns(self):
    return [
        url(r'^gsoc/profile/show/%s$' % url_patterns.PROGRAM,
         self, name='show_gsoc_profile'),
        # TODO: Add legacy URLs if any
    ]

  def checkAccess(self):
    self.check.isLoggedIn()
    self.check.isProfileActive()

  def templatePath(self):
    return 'v2/modules/gsoc/profile_show/base.html'

  def context(self):
    assert isSet(self.data.program)
    assert isSet(self.data.profile)
    assert isSet(self.data.user)

    profile = self.data.profile
    program = self.data.program
    user = self.data.user

    return {
        'page_name': '%(program_name)s Profile - %(profile_name)s' % {
            'program_name': program.short_name,
            'profile_name': profile.name()},
        'program_name': program.name,
        'form_top_msg': LoggedInMsg(self.data, apply_link=False),
        'user': user,
        'profile': ProfileReadOnlyTemplate(profile),
        }
