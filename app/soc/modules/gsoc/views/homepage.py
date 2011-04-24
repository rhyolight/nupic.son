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

"""Module containing the views for GSoC home page.
"""

__authors__ = [
  '"Madhusudan.C.S" <madhusudancs@gmail.com>',
  '"Sverre Rabbelier" <sverre@rabbelier.nl>',
  ]


from google.appengine.api import users

from django.core.urlresolvers import reverse
from django.conf.urls.defaults import url

from soc.logic import dicts
from soc.logic import system
from soc.views.template import Template

from soc.modules.gsoc.logic.models.organization import logic as org_logic
from soc.modules.gsoc.logic import project as project_logic
from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.base_templates import LoggedInMsg
from soc.modules.gsoc.views.helper import url_patterns


class Timeline(Template):
  """Timeline template.
  """

  def __init__(self, data, current_timeline):
    self.data = data
    self.current_timeline = current_timeline

  def context(self):
    if self.current_timeline == 'kickoff_period':
      img_url = ("/soc/content/%s/images/v2/gsoc/image-map-kickoff.png"
                 % system.getMelangeVersion())
    elif self.current_timeline in ['org_signup_period', 'orgs_announced_period']:
      img_url = ("/soc/content/%s/images/v2/gsoc/image-map-org-apps.png"
                 % system.getMelangeVersion())
    elif self.current_timeline == 'student_signup_period':
      img_url = ("/soc/content/%s/images/v2/gsoc/image-map-student-apps.png"
                 % system.getMelangeVersion())
    elif self.current_timeline == 'coding_period':
      img_url = ("/soc/content/%s/images/v2/gsoc/image-map-on-season.png"
                 % system.getMelangeVersion())
    else:
      img_url = ("/soc/content/%s/images/v2/gsoc/image-map-off-season.png"
                 % system.getMelangeVersion())

    return {
        'img_url': img_url
    }

  def templatePath(self):
    return "v2/modules/gsoc/homepage/_timeline.html"


class Apply(Template):
  """Apply template.
  """

  def __init__(self, data):
    self.data = data

  def context(self):
    context = {}
    accepted_orgs = None
    r = self.data.redirect.program()

    if self.data.timeline.orgsAnnounced():
      # accepted orgs block
      accepted_orgs = r.urlOf('gsoc_accepted_orgs')
      nr_orgs = self.data.program.nr_accepted_orgs
      context['nr_accepted_orgs'] = nr_orgs if nr_orgs else ""
      context['accepted_orgs_link'] = accepted_orgs
      participating_orgs = []
      current_orgs = org_logic.getParticipatingOrgs(self.data.program)
      for org in current_orgs:
        participating_orgs.append({
            'link': r.orgHomepage(org.link_id).url(),
            'logo': org.logo_url,
            'name': org.short_name,
            })
      context['participating_orgs'] = participating_orgs

    context['org_signup'] = self.data.timeline.orgSignup()  
    context['student_signup'] = self.data.timeline.studentSignup()
    context['mentor_signup'] = self.data.timeline.mentorSignup()

    signup = (
        self.data.timeline.orgSignup() or
        self.data.timeline.studentSignup() or
        (self.data.timeline.mentorSignup() and not self.data.student_info)
    )

    # signup block
    if signup and not self.data.gae_user:
      context['login_link'] = r.login().url()
    if signup and not self.data.profile:
      if self.data.timeline.orgSignup():
        r.createProfile('org_admin')
      elif self.data.timeline.studentSignup():
        r.createProfile('mentor')
        context['mentor_profile_link'] = r.urlOf('create_gsoc_profile')
        r.createProfile('student')
      elif self.data.timeline.mentorSignup():
        r.createProfile('mentor')

      context['profile_link'] = r.urlOf('create_gsoc_profile')

    if ((self.data.timeline.studentSignup() or
        self.data.timeline.mentorSignup()) and self.data.profile):
      context['apply_link'] = accepted_orgs

    if self.data.profile:
      if self.data.student_info:
        context['profile_role'] = 'student'
      else:
        context['profile_role'] = 'mentor'

    context['apply_block'] = signup

    return context

  def templatePath(self):
    return "v2/modules/gsoc/homepage/_apply.html"


class FeaturedProject(Template):
  """Featured project template
  """

  def __init__(self, data, featured_project):
    self.data = data
    self.featured_project = featured_project

  def context(self):
    redirect = self.data.redirect

    featured_project_url = redirect.projectDetails(self.featured_project).url()

    return {
      'featured_project': self.featured_project,
      'featured_project_url': featured_project_url,
    }

  def templatePath(self):
    return "v2/modules/gsoc/homepage/_featured_project.html"


class ConnectWithUs(Template):
  """Connect with us template.
  """

  def __init__(self, data):
    self.data = data

  def context(self):
    return {
        'facebook_link': self.data.program.facebook,
        'twitter_link': self.data.program.twitter,
        'blogger_link': self.data.program.blogger,
        'email': self.data.program.email,
        'irc_channel_link': self.data.program.irc,
    }

  def templatePath(self):
    return "v2/modules/gsoc/_connect_with_us.html"


class Homepage(RequestHandler):
  """Encapsulate all the methods required to generate GSoC Home page.
  """

  def templatePath(self):
    return 'v2/modules/gsoc/homepage/base.html'

  def djangoURLPatterns(self):
    """Returns the list of tuples for containing URL to view method mapping.
    """

    return [
        url(r'^gsoc/homepage/%s$' % url_patterns.PROGRAM, self,
            name='gsoc_homepage'),
        url(r'^gsoc/program/home/%s$' % url_patterns.PROGRAM, self),
        url(r'^program/home/%s$' % url_patterns.PROGRAM, self),
    ]

  def checkAccess(self):
    """Access checks for GSoC Home page.
    """
    pass

  def context(self):
    """Handler to for GSoC Home page HTTP get request.
    """

    current_timeline = self.data.timeline.currentPeriod()

    featured_project = project_logic.getFeaturedProject(
        current_timeline, self.data.program)

    context = {
        'logged_in_msg': LoggedInMsg(self.data, apply_link=False,
                                     div_name='user-login'),
        'timeline': Timeline(self.data, current_timeline),
        'apply': Apply(self.data),
        'connect_with_us': ConnectWithUs(self.data),
        'page_name': 'Home page',
        'program': self.data.program,
    }

    if featured_project:
      context['featured_project'] = FeaturedProject(
        self.data, featured_project)

    return context
