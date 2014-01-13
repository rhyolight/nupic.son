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

"""This module contains the view for the site menus."""

from django.core.urlresolvers import reverse

from melange.logic import user as user_logic
from melange.request import links

from soc.views import template

from soc.modules.gci.logic.program import getMostRecentProgram
from soc.modules.gsoc.models import program as program_model
from soc.modules.gsoc.views.helper import url_names


def siteMenuContext(data):
  """Generates URL links for the hard-coded GSoC site menu items."""
  redirect = data.redirect
  program = data.program

  GSoCProgram = program_model.GSoCProgram
  about_page = GSoCProgram.about_page.get_value_for_datastore(program)
  connect = GSoCProgram.connect_with_us_page.get_value_for_datastore(program)
  help_page = GSoCProgram.help_page.get_value_for_datastore(program)

  context = {
      'about_link': redirect.document(about_page).url(),
      'connect_link': redirect.document(connect).url(),
      'help_link': redirect.document(help_page).url(),
  }

  events_page_key = (
      program_model.GSoCProgram.events_page.get_value_for_datastore(
          data.program))

  if events_page_key:
    context['events_link'] = links.LINKER.program(data.program, 'gsoc_events')

  if data.gae_user:
    context['logout_link'] = links.LINKER.logout(data.request)
  else:
    context['login_link'] = links.LINKER.login(data.request)

  if data.profile:
    context['dashboard_link'] = links.LINKER.program(
        data.program, 'gsoc_dashboard')

  if data.timeline.studentsAnnounced():
    context['projects_link'] = links.LINKER.program(
        data.program, 'gsoc_accepted_projects')

  return context


class Header(template.Template):
  """Header template."""

  def __init__(self, data):
    self.data = data

  def templatePath(self):
    return "modules/gsoc/header.html"

  def context(self):
    # Need this import to make sponsor visible for sponsor link_id
    from soc.models.sponsor import Sponsor

    gci_link = ''
    key_name = getMostRecentProgram(self.data)

    if key_name:
      sponsor, program = key_name.split('/')
      gci_kwargs = {
          'sponsor': sponsor,
          'program': program,
      }
      # We have to use reverse method instead of the redirect helper
      # because we have to get the URL for a program of the other module
      # that is not part of the request data. So we cannot directly use
      # the redirect helper, since a module's redirect helper doesn't
      # resolve to the correct module URL prefix.
      gci_link = reverse('gci_homepage', kwargs=gci_kwargs)

    context = {
        'home_link': links.LINKER.program(self.data.program, 'gsoc_homepage'),
        'program_link_id': self.data.program.link_id,
        'gci_link': gci_link,
        }

    if self.data.gae_user:
      context['logout_link'] = links.LINKER.logout(self.data.request)
      context['user_email'] = self.data.gae_user.email()

      if self.data.user:
        context['username'] = self.data.user.link_id

    return context

class MainMenu(template.Template):
  """MainMenu template.
  """

  def __init__(self, data):
    self.data = data

  def context(self):
    context = siteMenuContext(self.data)

    context.update({
        'home_link': links.LINKER.program(self.data.program, 'gsoc_homepage'),
        'search_link': links.LINKER.program(self.data.program, 'search_gsoc'),
    })

    if self.data.profile and self.data.profile.status == 'active':
      self.data.redirect.program()
      context['profile_link'] = self.data.redirect.urlOf(
          url_names.GSOC_PROFILE_SHOW, secure=True)

    if user_logic.isHostForProgram(self.data.ndb_user, self.data.program.key()):
      self.data.redirect.program()
      context['admin_link'] = self.data.redirect.urlOf('gsoc_admin_dashboard')

    return context

  def templatePath(self):
    return "modules/gsoc/mainmenu.html"


class Footer(template.Template):
  """Footer template."""

  def __init__(self, data):
    self.data = data

  def context(self):
    context = siteMenuContext(self.data)
    program = self.data.program

    context.update({
        'privacy_policy_link': program.privacy_policy_url,
        'blogger_link': program.blogger,
        'email_id': program.email,
        'irc_link': program.irc,
        'google_plus_link': program.gplus,
        })

    return context

  def templatePath(self):
    return "modules/gsoc/footer.html"
