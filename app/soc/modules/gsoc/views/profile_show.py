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


from django.utils.translation import ugettext

from soc.logic.exceptions import NotFound

from soc.views import readonly_template
from soc.views import profile_show
from soc.views.helper import url_patterns
from soc.views.helper.access_checker import isSet

from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.models.project import GSoCProject
from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.base_templates import LoggedInMsg
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper.url_patterns import url


class GSoCProfileReadOnlyTemplate(readonly_template.ModelReadOnlyTemplate):
  """Template to construct read-only GSoCProfile data.
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


class GSoCHostActions(profile_show.HostActions):
  """Template to render the left side host actions.
  """
  
  DEF_BAN_PROFILE_HELP = ugettext(
      'When a profile is banned, the user cannot participate in the program')

  def _getActionURLName(self):
    return url_names.GSOC_PROFILE_BAN

  def _getHelpText(self):
    return self.DEF_BAN_PROFILE_HELP


class GSoCBanProfilePost(profile_show.BanProfilePost, RequestHandler):
  """Handles banning/unbanning of GSoC profiles.
  """

  def _getModulePrefix(self):
    return 'gsoc'

  def _getURLPattern(self):
    return url_patterns.PROFILE

  def _getURLName(self):
    return url_names.GSOC_PROFILE_BAN

  def _getProfileModel(self):
    return GSoCProfile


class GSoCProfileShowPage(profile_show.ProfileShowPage, RequestHandler):
  """View to display the read-only profile page.
  """

  def djangoURLPatterns(self):
    return [
        url(r'profile/show/%s$' % url_patterns.PROGRAM,
            self, name='show_gsoc_profile'),
    ]

  def templatePath(self):
    return 'v2/modules/gsoc/profile_show/base.html'

  def _getProfileReadOnlyTemplate(self, profile):
    return GSoCProfileReadOnlyTemplate(profile)


class GSoCProfileAdminPage(RequestHandler):
  """View to display the readonly profile page.
  """

  def djangoURLPatterns(self):
    return [
        url(r'profile/admin/%s$' % url_patterns.PROFILE,
         self, name=url_names.GSOC_PROFILE_SHOW),
    ]

  def checkAccess(self):
    self.check.isHost()
    self.mutator.userFromKwargs()
    try:
      self.mutator.profileFromKwargs()
    except NotFound:
      # it is not a terminal error, when Profile does not exist
      pass

  def templatePath(self):
    return 'v2/modules/gsoc/profile_show/base.html'

  def context(self):
    assert isSet(self.data.program)
    assert isSet(self.data.url_user)

    user = self.data.url_user
    profile = self.data.url_profile
    program = self.data.program

    context = {
        'program_name': program.name,
        'form_top_msg': LoggedInMsg(self.data, apply_link=False),
        'user': profile_show.UserReadOnlyTemplate(user),
        'css_prefix': GSoCProfileReadOnlyTemplate.Meta.css_prefix,
        }

    if profile:
      links = []
      r = self.redirect.profile()
      for project in GSoCProject.all().ancestor(profile):
        r.project(project.key().id())
        links.append(r.urlOf('gsoc_project_details', full=True))
      r = self.redirect.profile()
      
      user_role = None
      if profile.is_student:
          user_role = 'Student'
      elif profile.is_org_admin:
          user_role = 'Org Admin'
      elif profile.is_mentor:
          user_role = 'Mentor'
      
      context.update({
          'profile': GSoCProfileReadOnlyTemplate(profile),
          'links': links,
          'submit_tax_link': r.urlOf('gsoc_tax_form_admin'),
          'submit_enrollment_link': r.urlOf('gsoc_enrollment_form_admin'),
          'page_name': '%s Profile - %s' % (
              program.short_name, profile.name()),
          'user_role': user_role,
          'host_actions': GSoCHostActions(self.data)
          })
    else:
      context.update({
          'page_name': '%s Profile - %s' % (program.short_name, user.account),
          })

    return context
