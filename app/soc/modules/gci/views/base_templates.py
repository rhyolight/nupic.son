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

  if users.get_current_user():
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
        'search_link': self.data.redirect.searchpage().url(),
    })
    
    if self.data.profile:
      self.data.redirect.program()
      if self.data.profile.status == 'active':
        context['profile_link'] = self.data.redirect.urlOf('edit_gsoc_profile')

        # Add org admin dashboard link if the user has active
        # org admin profile and is an org admin of some organization
        if self.data.is_org_admin:
          context['org_dashboard_link'] = self.data.redirect.urlOf(
              'gsoc_org_dashboard')
      else:
        context['profile_link'] = self.data.redirect.urlOf('show_gsoc_profile')

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

    from soc.modules.gsoc.models.program import GSoCProgram
    policy = GSoCProgram.privacy_policy.get_value_for_datastore(program)

    context.update({
        'privacy_policy_url': redirect.document(policy).url(),
        'facebook_url': program.facebook,
        'twitter_url': program.twitter,
        'blogger_url': program.blogger,
        'email_id': program.email,
        'irc_url': program.irc,
        })

    return context

  def templatePath(self):
    return "v2/modules/gsoc/footer.html"


class LoggedInMsg(Template):
  """Template to render user login message at the top of the profile form.
  """
  def __init__(self, data, apply_role=False, apply_link=True, div_name=None):
    if not div_name:
      div_name = 'loggedin-message'
    self.data = data
    self.apply_link = apply_link
    self.apply_role = apply_role
    self.div_name = div_name

  def context(self):
    context = {
        'logout_link': self.data.redirect.logout().url(),
        'user_email': self.data.gae_user.email(),
        'has_profile': bool(self.data.profile),
        'div_name': self.div_name,
    }

    if self.apply_role and self.data.kwargs.get('role'):
      context['role'] = self.data.kwargs['role']

    if self.data.user:
      context['link_id'] = " [link_id: %s]" % self.data.user.link_id

    if self.apply_link and self.data.timeline.orgsAnnounced() and (
      (self.data.profile and not self.data.student_info) or
      (self.data.timeline.studentSignup() and self.data.student_info)):
      context['apply_link'] = self.data.redirect.acceptedOrgs().url()

    return context

  def templatePath(self):
    return "v2/modules/gsoc/_loggedin_msg.html"


class ProgramSelect(Template):
  """Program select template.
  """

  def __init__(self, data, url_name):
    self.data = data
    self.url_name = url_name

  def context(self):
    def url(program):
      r = self.data.redirect.program(program)
      return r.urlOf(self.url_name)
    def attr(program):
      if program.key() == self.data.program.key():
        return "selected=selected"
      return ""

    programs = [(i.short_name, url(i), attr(i)) for i in self.data.programs]

    return {
        'programs': programs,
        'render': len(programs) > 1,
    }

  def templatePath(self):
    return "v2/modules/gsoc/_program_select.html"