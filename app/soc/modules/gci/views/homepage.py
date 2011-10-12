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

"""Module containing the views for GCI home page.
"""

__authors__ = [
  '"Madhusudan.C.S" <madhusudancs@gmail.com>',
  ]


from soc.views.helper import url_patterns
from soc.views.template import Template

from soc.modules.gci.logic import organization as org_logic
from soc.modules.gci.logic import task as task_logic
from soc.modules.gci.views.base import RequestHandler
from soc.modules.gci.views.helper.url_patterns import url


class HowItWorks(Template):
  """How it works template.
  """

  def __init__(self, data):
    self.data = data

  def context(self):
    r = self.data.redirect
    program = self.data.program

    from soc.modules.gci.models.program import GCIProgram
    about_page = GCIProgram.about_page.get_value_for_datastore(program)

    if not self.data.timeline.programActive():
      start_text = start_link = ''
    elif self.data.timeline.orgSignup():
      start_text = 'Sign up as organization'
      start_link = r.program().urlOf('gci_take_org_app')
    else:
      # TODO
      start_text = start_link = ''

    return {
        'about_link': r.document(about_page).url(),
        'start_text': start_text,
        'start_link': start_link,
    }

  def templatePath(self):
    return "v2/modules/gci/homepage/_how_it_works.html"


class FeaturedTask(Template):
  """Featured task template.
  """

  def __init__(self, data, featured_task):
    self.data = data
    self.featured_task = featured_task

  def context(self):
    task_url = self.data.redirect.id(self.featured_task.key().id()).urlOf(
        'gci_view_task')

    return {
        'featured_task': self.featured_task,
        'featured_task_url': task_url,
        }

  def templatePath(self):
    return "v2/modules/gci/homepage/_featured_task.html"


class ParticipatingOrgs(Template):
  """Participating orgs template.
  """

  def __init__(self, data):
    self.data = data

  def context(self):
    r = self.data.redirect

    participating_orgs = []
    current_orgs = org_logic.participating(self.data.program)
    for org in current_orgs:
      participating_orgs.append({
          # TODO(madhu): Put the URL bank once the org home page appears.
          #'link': r.orgHomepage(org.link_id).url(),
          'logo': org.logo_url,
          'name': org.short_name,
          })

    return {
        'participating_orgs': participating_orgs,
        # TODO(madhu): Generate the URL for list of all
        # participating organizations once the page is ready.
        'org_list_url': '',
    }

  def templatePath(self):
    return "v2/modules/gci/homepage/_participating_orgs.html"


class Timeline(Template):
  """News template.
  """

  def __init__(self, data):
    self.data = data

  def context(self):
    return {
    }

  def templatePath(self):
    return "v2/modules/gci/homepage/_timeline.html"


class ConnectWithUs(Template):
  """Connect with us template.
  """

  def __init__(self, data):
    self.data = data

  def context(self):
    return {
        'program': self.data.program,
    }

  def templatePath(self):
    return "v2/modules/gci/homepage/_connect_with_us.html"


class Homepage(RequestHandler):
  """Encapsulate all the methods required to generate GSoC Home page.
  """

  def templatePath(self):
    return 'v2/modules/gci/homepage/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'homepage/%s$' % url_patterns.PROGRAM, self,
            name='gci_homepage'),
        url(r'program/home/%s$' % url_patterns.PROGRAM, self),
    ]

  def checkAccess(self):
    self.check.isProgramVisible()

  def context(self):
    context = {
        'page_name': '%s - Home page' % (self.data.program.name),
        'how_it_works': HowItWorks(self.data),
        'participating_orgs': ParticipatingOrgs(self.data),
        'connect_with_us': ConnectWithUs(self.data),
        'program': self.data.program,
    }

    current_timeline = self.data.timeline.currentPeriod()

    if current_timeline == 'student_signup_period':
      context['timeline'] = Timeline(self.data)

    featured_task = task_logic.getFeaturedTask(
        current_timeline, self.data.program)

    if featured_task:
      context['featured_task'] = FeaturedTask(
        self.data, featured_task)

    return context
