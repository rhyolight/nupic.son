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

"""Module containing the views for GSoC home page."""

from django.conf.urls.defaults import url as django_url

from melange.appengine import system
from soc.logic import links
from soc.views.helper import url_patterns
from soc.views.template import Template

from soc.modules.gsoc.logic import organization as org_logic
from soc.modules.gsoc.logic import project as project_logic
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views.helper.url_patterns import url


class Timeline(Template):
  """Timeline template.
  """

  def __init__(self, data, current_timeline, next_deadline):
    self.data = data
    self.current_timeline = current_timeline
    self.next_deadline_msg, self.next_deadline_datetime = next_deadline

  def context(self):
    if self.current_timeline == 'kickoff_period':
      img_url = ("/soc/content/%s/images/gsoc/image-map-kickoff.png"
                 % system.getMelangeVersion())
    elif self.current_timeline in ['org_signup_period', 'orgs_announced_period']:
      img_url = ("/soc/content/%s/images/gsoc/image-map-org-apps.png"
                 % system.getMelangeVersion())
    elif self.current_timeline == 'student_signup_period':
      img_url = ("/soc/content/%s/images/gsoc/image-map-student-apps.png"
                 % system.getMelangeVersion())
    elif self.current_timeline == 'coding_period':
      img_url = ("/soc/content/%s/images/gsoc/image-map-on-season.png"
                 % system.getMelangeVersion())
    else:
      img_url = ("/soc/content/%s/images/gsoc/image-map-off-season.png"
                 % system.getMelangeVersion())

    context = {
        'img_url': img_url,
        'events_link': self.data.redirect.events().url(),
        }

    if self.next_deadline_msg and self.next_deadline_datetime:
      context['next_deadline_msg'] = self.next_deadline_msg
      context['next_deadline_datetime'] = self.next_deadline_datetime

    return context

  def templatePath(self):
    return "modules/gsoc/homepage/_timeline.html"


class Apply(Template):
  """Apply template."""

  def __init__(self, data):
    self.data = data

  def context(self):
    context = {}
    accepted_orgs = None
    redirector = self.data.redirect
    redirector.program()

    if self.data.timeline.orgsAnnounced():
      # accepted orgs block
      accepted_orgs = redirector.urlOf('gsoc_accepted_orgs')
      nr_orgs = self.data.program.nr_accepted_orgs
      context['nr_accepted_orgs'] = nr_orgs if nr_orgs else ""
      context['accepted_orgs_link'] = accepted_orgs
      participating_orgs = []
      current_orgs = org_logic.participating(self.data.program)
      for org in current_orgs:
        participating_orgs.append({
            'link': redirector.orgHomepage(org.link_id).url(),
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
      # TODO(nathaniel): One-off linker object.
      context['login_link'] = links.Linker().login(self.data.request)
    if signup and not self.data.profile:
      if self.data.timeline.orgSignup():
        redirector.createProfile('org_admin')
      elif self.data.timeline.studentSignup():
        redirector.createProfile('mentor')
        context['mentor_profile_link'] = redirector.urlOf(
            'create_gsoc_profile', secure=True)
        redirector.createProfile('student')
      elif self.data.timeline.mentorSignup():
        redirector.createProfile('mentor')

      context['profile_link'] = redirector.urlOf(
          'create_gsoc_profile', secure=True)

    if self.data.timeline.orgSignup() and self.data.profile:
      context['org_apply_link'] = redirector.orgAppTake().urlOf(
          'gsoc_take_org_app')
      context['dashboard_link'] = redirector.dashboard().url()

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
    return "modules/gsoc/homepage/_apply.html"


class FeaturedProject(Template):
  """Featured project template
  """

  def __init__(self, data, featured_project):
    self.data = data
    self.featured_project = featured_project

  def context(self):
    project_id = self.featured_project.key().id_or_name()
    student_link_id = self.featured_project.parent().link_id

    redirect = self.data.redirect

    featured_project_url = redirect.project(
        id=project_id,
        student=student_link_id).urlOf('gsoc_project_details')

    return {
      'featured_project': self.featured_project,
      'featured_project_url': featured_project_url,
    }

  def templatePath(self):
    return "modules/gsoc/homepage/_featured_project.html"


class ConnectWithUs(Template):
  """Connect with us template.
  """

  def __init__(self, data):
    self.data = data

  def context(self):
    return {
        'blogger_link': self.data.program.blogger,
        'email': self.data.program.email,
        'irc_channel_link': self.data.program.irc,
        'google_plus_link': self.data.program.gplus,
    }

  def templatePath(self):
    return "modules/gsoc/_connect_with_us.html"


class Homepage(base.GSoCRequestHandler):
  """Encapsulate all the methods required to generate GSoC Home page.
  """

  def templatePath(self):
    return 'modules/gsoc/homepage/base.html'

  def djangoURLPatterns(self):
    """Returns the list of tuples for containing URL to view method mapping.
    """

    return [
        url(r'homepage/%s$' % url_patterns.PROGRAM, self,
            name='gsoc_homepage'),
        url(r'program/home/%s$' % url_patterns.PROGRAM, self),
        django_url(r'^program/home/%s$' % url_patterns.PROGRAM, self),
    ]

  def checkAccess(self, data, check, mutator):
    """Access checks for GSoC Home page."""
    check.isProgramVisible()

  def context(self, data, check, mutator):
    """Handler to for GSoC Home page HTTP get request."""

    current_timeline = data.timeline.currentPeriod()
    next_deadline = data.timeline.nextDeadline()

    context = {
        'timeline': Timeline(data, current_timeline, next_deadline),
        'apply': Apply(data),
        'connect_with_us': ConnectWithUs(data),
        'page_name': '%s - Home page' % (data.program.name),
        'program': data.program,
    }

    featured_project = project_logic.getFeaturedProject(
        current_timeline, data.program)

    if featured_project:
      context['featured_project'] = FeaturedProject(data, featured_project)

    return context
