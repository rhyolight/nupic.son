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

"""Module for displaying the GSoC profile read only page."""

from django.utils.translation import ugettext

from melange.request import access
from melange.request import links

from soc.views import profile_show
from soc.views.helper import url_patterns
from soc.views.helper.access_checker import isSet

from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.models.project import GSoCProject
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views import readonly_template
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper.url_patterns import url

from summerofcode.templates import tabs


class GSoCProfileReadOnlyTemplate(readonly_template.GSoCModelReadOnlyTemplate):
  """Template to construct read-only GSoCProfile data.
  """

  class Meta:
    model = GSoCProfile
    css_prefix = 'gsoc_profile_show'
    fields = ['public_name', 'given_name', 'surname', 'im_network',
              'im_handle', 'home_page', 'blog', 'photo_url', 'email',
              'res_street', 'res_street_extra', 'res_city', 'res_state',
              'res_country', 'res_postalcode', 'phone', 'ship_name',
              'ship_street', 'ship_street_extra', 'ship_city', 'ship_state',
              'ship_country', 'ship_postalcode', 'birth_date',
              'tshirt_style', 'tshirt_size', 'gender', 'program_knowledge']

class GSoCUserReadOnlyTemplate(profile_show.UserReadOnlyTemplate):
  """Template to construct read-only User data to be displayed on Summer
  Of Code view.
  """
  template_path = readonly_template.GSoCModelReadOnlyTemplate.template_path


class GSoCHostActions(profile_show.HostActions):
  """Template to render the left side host actions.
  """

  DEF_BAN_PROFILE_HELP = ugettext(
      'When a profile is banned, the user cannot participate in the program')

  def _getActionURLName(self):
    return url_names.GSOC_PROFILE_BAN

  def _getHelpText(self):
    return self.DEF_BAN_PROFILE_HELP


class GSoCBanProfilePost(profile_show.BanProfilePost, base.GSoCRequestHandler):
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


class GSoCProfileShowPage(profile_show.ProfileShowPage, base.GSoCRequestHandler):
  """View to display the read-only profile page."""

  def djangoURLPatterns(self):
    """See base.GSoCRequestHandler.djangoURLPatterns for specification."""
    return [
        url(r'profile/show/%s$' % url_patterns.PROGRAM,
            self, name=url_names.GSOC_PROFILE_SHOW),
    ]

  def templatePath(self):
    """See base.GSoCRequestHandler.templatePath for specification."""
    return 'modules/gsoc/profile_show/base.html'

  def _getProfileReadOnlyTemplate(self, profile):
    """See profile_show.ProfileShowPage._getProfileReadOnlyTemplate
    for specification.
    """
    return GSoCProfileReadOnlyTemplate(profile)

  def _getUserReadOnlyTemplate(self, user):
    """See profile_show.ProfileShowPage._getUserReadOnlyTemplate
    for specification.
    """
    return GSoCUserReadOnlyTemplate(user)

  def _getTabs(self, data):
    """See profile_show.ProfileShowPage._getTabs for specification."""
    return tabs.profileTabs(
        data, selected_tab_id=tabs.VIEW_PROFILE_TAB_ID)


class GSoCProfileAdminPage(base.GSoCRequestHandler):
  """View to display the readonly profile page."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
        url(r'profile/admin/%s$' % url_patterns.PROFILE,
         self, name=url_names.GSOC_PROFILE_SHOW_ADMIN),
    ]

  def templatePath(self):
    return 'modules/gsoc/profile_show/base.html'

  def context(self, data, check, mutator):
    profile = data.url_profile
    program = data.program

    context = {
        'program_name': program.name,
        'user': GSoCUserReadOnlyTemplate(data.url_ndb_user),
        'css_prefix': GSoCProfileReadOnlyTemplate.Meta.css_prefix,
        }

    if profile:
      urls = []
      for project_key in GSoCProject.all(keys_only=True).ancestor(
            data.url_profile.key.to_old_key()):
        urls.append(
            links.ABSOLUTE_LINKER.userId(
                data.url_ndb_profile.key, project_key.id(),
                url_names.GSOC_PROJECT_DETAILS))

      # TODO(nathaniel): Eliminate this state-setting call.
      data.redirect.profile()

      context.update({
          'profile': GSoCProfileReadOnlyTemplate(profile),
          'links': urls,
          'submit_tax_link': data.redirect.urlOf('gsoc_tax_form_admin'),
          'submit_enrollment_link': data.redirect.urlOf(
              'gsoc_enrollment_form_admin'),
          'page_name': '%s Profile - %s' % (
              program.short_name, profile.name()),
          'host_actions': GSoCHostActions(data)
          })
    else:
      context.update({
          'page_name': '%s Profile - %s' % (
              program.short_name, data.url_ndb_user.user_id),
          })

    return context
