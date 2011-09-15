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


from soc.models.user import User
from soc.views import readonly_template
from soc.views.helper.access_checker import isSet

from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.models.project import GSoCProject
from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.base_templates import LoggedInMsg
from soc.modules.gsoc.views.helper import url_patterns
from soc.modules.gsoc.views.helper.url_patterns import url


class UserReadOnlyTemplate(readonly_template.ModelReadOnlyTemplate):
  """Template to construct readonly Profile data.
  """

  class Meta:
    model = User
    css_prefix = 'gsoc_profile_show'
    fields = ['link_id']

  def __init__(self, *args, **kwargs):
    super(UserReadOnlyTemplate, self).__init__(*args, **kwargs)
    self.fields['link_id'].group = "1. User info"


class ProfileReadOnlyTemplate(readonly_template.ModelReadOnlyTemplate):
  """Template to construct readonly Profile data.
  """

  class Meta:
    model = GSoCProfile
    css_prefix = 'gsoc_profile_show'
    fields = ['public_name', 'given_name', 'surname', 'im_network',
              'im_handle', 'home_page', 'blog', 'photo_url',
              'publish_location', 'email', 'res_street',
              'res_street_extra', 'res_city', 'res_state', 'res_country',
              'res_postalcode', 'phone', 'ship_name', 'ship_street',
              'ship_street_extra', 'ship_city', 'ship_state',
              'ship_country', 'ship_postalcode', 'birth_date',
              'tshirt_style', 'tshirt_size', 'gender', 'program_knowledge']
    hidden_fields = ['latitude', 'longitude']


class ProfileShowPage(RequestHandler):
  """View to display the readonly profile page.
  """

  def djangoURLPatterns(self):
    return [
        url(r'profile/show/%s$' % url_patterns.PROGRAM,
         self, name='show_gsoc_profile'),
    ]

  def checkAccess(self):
    self.check.isLoggedIn()
    self.check.hasProfile()

  def templatePath(self):
    return 'v2/modules/gsoc/profile_show/base.html'

  def context(self):
    assert isSet(self.data.program)
    assert isSet(self.data.profile)
    assert isSet(self.data.user)

    profile = self.data.profile
    program = self.data.program

    return {
        'page_name': '%s Profile - %s' % (program.short_name, profile.name()),
        'program_name': program.name,
        'form_top_msg': LoggedInMsg(self.data, apply_link=False),
        'user': UserReadOnlyTemplate(self.data.user),
        'profile': ProfileReadOnlyTemplate(profile),
        'css_prefix': ProfileReadOnlyTemplate.Meta.css_prefix,
        }


class ProfileAdminPage(RequestHandler):
  """View to display the readonly profile page.
  """

  def djangoURLPatterns(self):
    return [
        url(r'profile/admin/%s$' % url_patterns.PROFILE,
         self, name='gsoc_profile_admin'),
    ]

  def checkAccess(self):
    self.check.isHost()
    self.mutator.profileFromKwargs()

  def templatePath(self):
    return 'v2/modules/gsoc/profile_show/base.html'

  def context(self):
    assert isSet(self.data.program)
    assert isSet(self.data.url_profile)
    assert isSet(self.data.url_user)

    user = self.data.url_user
    profile = self.data.url_profile
    program = self.data.program
    r = self.redirect.profile()

    links = []

    for project in GSoCProject.all().ancestor(profile):
      r.project(project.key().id())
      links.append(r.urlOf('gsoc_project_details'))

    r = self.redirect.profile()

    return {
        'page_name': '%s Profile - %s' % (program.short_name, profile.name()),
        'program_name': program.name,
        'form_top_msg': LoggedInMsg(self.data, apply_link=False),
        'user': UserReadOnlyTemplate(user),
        'profile': ProfileReadOnlyTemplate(profile),
        'links': links,
        'css_prefix': ProfileReadOnlyTemplate.Meta.css_prefix,
        'submit_tax_link': r.urlOf('gsoc_tax_form_admin'),
        'submit_enrollment_link': r.urlOf('gsoc_enrollment_form_admin'),
        }
