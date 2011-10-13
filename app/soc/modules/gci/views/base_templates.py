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

__authors__ = [
  '"Daniel Hans" <daniel.m.hans@gmail.com>',
  '"Sverre Rabbelier" <sverre@rabbelier.nl>',
  '"Lennard de Rijk" <ljvderijk@gmail.com>',
]


from google.appengine.api import users

from soc.views.template import Template
from soc.views.base_templates import LoggedInMsg


def siteMenuContext(data):
  """Generates URL links for the hard-coded GSoC site menu items.
  """
  redirect = data.redirect
  program = data.program

  from soc.modules.gci.models.program import GCIProgram
  about_page = GCIProgram.about_page.get_value_for_datastore(program)
  connect = GCIProgram.connect_with_us_page.get_value_for_datastore(program)
  help_page = GCIProgram.help_page.get_value_for_datastore(program)
  terms = GCIProgram.terms_and_conditions.get_value_for_datastore(program)

  context = {
      'about_link': redirect.document(about_page).url(),
      'terms_link': redirect.document(terms).url(),
      'events_link': redirect.events().url(),
      'connect_link': redirect.document(connect).url(),
      'help_link': redirect.document(help_page).url(),
  }

  if users.get_current_user():
    context['logout_link'] = redirect.logout().url()
  else:
    context['login_link'] = redirect.login().url()

  if data.profile:
    context['dashboard_link'] = redirect.dashboard().url()

  if data.timeline.tasksPubliclyVisible():
    context['tasks_link'] = ''

  return context


class Header(Template):
  """MainMenu template.
  """

  def __init__(self, data):
    self.data = data

  def templatePath(self):
    return "v2/modules/gci/_header.html"

  def context(self):
    return {
        'home_link': self.data.redirect.homepage().url()
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
    })

    if self.data.profile:
      self.data.redirect.program()
      if self.data.profile.status == 'active':
        context['profile_link'] = self.data.redirect.urlOf('edit_gci_profile')

        # Add org admin dashboard link if the user has active
        # org admin profile and is an org admin of some organization
        if self.data.is_org_admin:
          context['org_dashboard_link'] = self.data.redirect.urlOf(
              'gci_org_dashboard')
      else:
        context['profile_link'] = self.data.redirect.urlOf('show_gci_profile')

    if self.data.is_host:
      self.data.redirect.program()
      # TODO(Madhu): Replace with the proper redirect once the
      # gci_admin_dashboard is implemented
      context['admin_link'] = ''

    return context

  def templatePath(self):
    return "v2/modules/gci/_mainmenu.html"


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
        })

    return context

  def templatePath(self):
    return "v2/modules/gci/_footer.html"


class Status(Template):
  """Template to render the status block.
  """

  def __init__(self, data):
    self.data = data

  def context(self):
    return {
      'user_email': self.data.user.account.email(),
      'logout_link': self.data.redirect.logout().url(),
    }


  def templatePath(self):
    return "v2/modules/gci/_status_block.html"
