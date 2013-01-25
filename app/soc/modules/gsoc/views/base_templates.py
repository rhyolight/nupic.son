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

"""This module contains the view for the site menus."""


from google.appengine.api import users

from django.core.urlresolvers import reverse

from soc.views.base_templates import LoggedInMsg
from soc.views.template import Template

from soc.modules.gci.logic.program import getMostRecentProgram


def siteMenuContext(data):
  """Generates URL links for the hard-coded GSoC site menu items.
  """
  redirect = data.redirect
  program = data.program

  from soc.modules.gsoc.models.program import GSoCProgram
  about_page = GSoCProgram.about_page.get_value_for_datastore(program)
  connect = GSoCProgram.connect_with_us_page.get_value_for_datastore(program)
  help_page = GSoCProgram.help_page.get_value_for_datastore(program)

  context = {
      'about_link': redirect.document(about_page).url(),
      'events_link': redirect.events().url(),
      'connect_link': redirect.document(connect).url(),
      'help_link': redirect.document(help_page).url(),
  }

  if data.gae_user:
    context['logout_link'] = redirect.logout().url()
  else:
    context['login_link'] = redirect.login().url()

  if data.profile:
    context['dashboard_link'] = redirect.dashboard().url()

  if data.timeline.studentsAnnounced():
    context['projects_link'] = redirect.allProjects().url()

  return context


class Header(Template):
  """MainMenu template.
  """

  def __init__(self, data):
    self.data = data

  def templatePath(self):
    return "v2/modules/gsoc/header.html"

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

    return {
        'home_link': self.data.redirect.homepage().url(),
        'program_link_id': self.data.program.link_id,
        'gci_link': gci_link,
    }


class MainMenu(Template):
  """MainMenu template.
  """

  def __init__(self, data):
    self.data = data

  def context(self):
    context = siteMenuContext(self.data)
    context.update({
        'home_link': self.data.redirect.homepage().url(),
        'search_link': self.data.redirect.searchpage().url(),
    })

    if self.data.profile and self.data.profile.status == 'active':
      self.data.redirect.program()
      if self.data.timeline.programActive():
        context['profile_link'] = self.data.redirect.urlOf(
            'edit_gsoc_profile', secure=True)
      else:
        context['profile_link'] = self.data.redirect.urlOf(
            'show_gsoc_profile', secure=True)

    if self.data.is_host:
      self.data.redirect.program()
      context['admin_link'] = self.data.redirect.urlOf('gsoc_admin_dashboard')

    return context

  def templatePath(self):
    return "v2/modules/gsoc/mainmenu.html"


class Footer(Template):
  """Footer template.
  """

  def __init__(self, data):
    self.data = data

  def context(self):
    context = siteMenuContext(self.data)
    redirect = self.data.redirect
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
    return "v2/modules/gsoc/footer.html"


class LoggedInMsg(LoggedInMsg):
  """Template to render user login message at the top of the profile form.
  """

  def templatePath(self):
    return "v2/modules/gsoc/_loggedin_msg.html"
