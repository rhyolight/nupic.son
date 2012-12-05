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

import datetime

from google.appengine.api import users

from django.core.urlresolvers import reverse

from soc.logic import accounts
from soc.views.template import Template

from soc.modules.gsoc.logic.program import getMostRecentProgram

from soc.modules.gci.models.task import ACTIVE_CLAIMED_TASK
from soc.modules.gci.models.task import GCITask
from soc.modules.gci.views.helper import url_names


def siteMenuContext(data):
  """Generates URL links for the hard-coded GCI site menu items.
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

  if data.user:
    context['dashboard_link'] = redirect.dashboard().url()

  if data.timeline.tasksPubliclyVisible():
    # TODO(nathaniel): make this .program() call unnecessary.
    redirect.program()
    context['tasks_link'] = redirect.urlOf('gci_list_tasks')
    if not data.user:
      context['register_as_student_link'] = redirect.createProfile(
          'student').urlOf('create_gci_profile', secure=True)

  return context


class Header(Template):
  """MainMenu template.
  """

  def __init__(self, data):
    self.data = data

  def templatePath(self):
    return "v2/modules/gci/_header.html"

  def context(self):
    # Need this import to make sponsor visible for sponsor link_id
    from soc.models.sponsor import Sponsor

    gsoc_link = ''
    key_name = getMostRecentProgram(self.data)

    if key_name:
      sponsor, program = key_name.split('/')
      gsoc_kwargs = {
          'sponsor': sponsor,
          'program': program,
      }
      # We have to use reverse method instead of the redirect helper
      # because we have to get the URL for a program of the other module
      # that is not part of the request data. So we cannot directly use
      # the redirect helper, since a module's redirect helper doesn't
      # resolve to the correct module URL prefix.
      gsoc_link = reverse('gsoc_homepage', kwargs=gsoc_kwargs)

    return {
        'home_link': self.data.redirect.homepage().url(),
        'gsoc_link': gsoc_link,
        'program_id': self.data.program.link_id,
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
        if self.data.timeline.programActive():
          context['profile_link'] = self.data.redirect.urlOf(
              'edit_gci_profile', secure=True)
        else:
          context['profile_link'] = self.data.redirect.urlOf(
              url_names.GCI_PROFILE_SHOW, secure=True)

        if self.data.is_org_admin:
          # Add org admin dashboard link if the user has active
          # org admin profile and is an org admin of some organization
          context['org_dashboard_link'] = self.data.redirect.urlOf(
              'gci_dashboard')

    if self.data.is_host:
      self.data.redirect.program()
      context['admin_link'] = self.data.redirect.urlOf('gci_admin_dashboard')

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

  def getTimeLeftForTask(self, task):
    """Time left to complete the task in human readable format.
    """
    if not task.deadline:
      return ""

    time_now = datetime.datetime.utcnow()
    time_left = task.deadline - time_now
    days_left = time_left.days
    hours_left = time_left.seconds/3600
    minutes_left = (time_left.seconds/60)%60
    return "%s days %s hrs %s min" % (days_left, hours_left, minutes_left)

  def context(self):
    context = {
        'user_email': accounts.denormalizeAccount(self.data.user.account).email(),
        'link_id': self.data.user.link_id,
        'logout_link': self.data.redirect.logout().url(),
        'dashboard_link': self.data.redirect.dashboard().url()
    }

    if self.data.profile:
      if self.data.is_student and self.data.profile.status == 'active':
        q = GCITask.all()
        q.filter('student', self.data.profile)
        q.filter('status IN', ACTIVE_CLAIMED_TASK)
        task = q.get()
        if task:
          context['task'] = task
          context['time_left'] = self.getTimeLeftForTask(task)
          task_url = self.data.redirect.id(
              task.key().id()).urlOf('gci_view_task')
          context['task_url'] = task_url
    return context

  def templatePath(self):
    return "v2/modules/gci/_status_block.html"
