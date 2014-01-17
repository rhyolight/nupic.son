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

from django.conf.urls import url as django_url

from melange.appengine import system
from melange.logic import organization as org_logic
from melange.request import links

from soc.views import base_templates
from soc.views.helper import url_patterns
from soc.views.template import Template

from soc.modules.gsoc.logic import project as project_logic
from soc.modules.gsoc.models import program as program_model
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper.url_patterns import url

from summerofcode.views.helper import urls


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

    context = {'img_url': img_url}

    events_page_key = (
        program_model.GSoCProgram.events_page.get_value_for_datastore(
            self.data.program))
    if events_page_key:
      context['events_link'] = links.LINKER.program(
          self.data.program, 'gsoc_events')

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
      accepted_orgs_link = links.LINKER.program(
          self.data.program, urls.UrlNames.ORG_PUBLIC_LIST)

      nr_orgs = self.data.program.nr_accepted_orgs
      context['nr_accepted_orgs'] = nr_orgs if nr_orgs else ""
      context['accepted_orgs_link'] = accepted_orgs_link
      participating_orgs = []
      current_orgs = org_logic.getAcceptedOrganizations(
          self.data.program.key(), models=self.data.models)

      for org in current_orgs:
        link = links.LINKER.organization(org.key, url_names.GSOC_ORG_HOME)
        participating_orgs.append({
            'link': link,
            'logo': org.logo_url,
            'name': org.name,
            })
      context['participating_orgs'] = participating_orgs

    context['org_signup'] = self.data.timeline.orgSignup()
    context['student_signup'] = self.data.timeline.studentSignup()
    context['mentor_signup'] = self.data.timeline.mentorSignup()

    signup_active = (
        self.data.timeline.orgSignup() or
        self.data.timeline.studentSignup() or
        (self.data.timeline.mentorSignup() and not self.data.student_info)
    )

    # signup block
    if signup_active and not self.data.gae_user:
      # Show a login link
      context['login_link'] = links.LINKER.login(self.data.request)

    # TODO(daniel): links to new profile registration pages must be provided!!
    if signup_active and not self.data.ndb_profile:
      # Show a registration link for a relevant profile type.
      redirector.createProfile('mentor')
      context['mentor_profile_link'] = redirector.urlOf(
          'create_gsoc_profile', secure=True)
      redirector.createProfile('org_admin')
      context['org_admin_profile_link'] = redirector.urlOf(
          'create_gsoc_profile', secure=True)
      redirector.createProfile('student')
      context['student_profile_link'] = redirector.urlOf(
          'create_gsoc_profile', secure=True)

      context['show_profile_link'] = False
      if self.data.timeline.orgSignup():
        context['show_org_admin_link'] = True
        context['show_profile_link'] = True
      elif self.data.timeline.studentSignup():
        context['show_student_link'] = True
        context['show_profile_link'] = True
      elif self.data.timeline.mentorSignup():
        context['show_mentor_link'] = True
        context['show_student_link'] = True
        context['show_profile_link'] = True

    if self.data.timeline.orgSignup() and self.data.ndb_profile:
      context['org_apply_link'] = redirector.program().urlOf(
          'gsoc_take_org_app')
      context['dashboard_link'] = links.LINKER.program(
          self.data.program, 'gsoc_dashboard')

    if ((self.data.timeline.studentSignup() or
        self.data.timeline.mentorSignup()) and self.data.ndb_profile):
      context['apply_link'] = accepted_orgs

    if self.data.ndb_profile:
      if self.data.student_info:
        context['profile_role'] = 'student'
      else:
        context['profile_role'] = 'mentor'

    context['signup_active'] = signup_active

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
    """See template.Template.context for specification."""
    featured_project_url = links.LINKER.userId(
        self.featured_project.parent_key(), self.featured_project.key().id(),
        url_names.GSOC_PROJECT_DETAILS)
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
        'program_select': base_templates.ProgramSelect(
            'modules/gsoc/homepage/_program_select.html', data,
            'gsoc_homepage'),
    }

    featured_project = project_logic.getFeaturedProject(
        current_timeline, data.program)

    if featured_project:
      context['featured_project'] = FeaturedProject(data, featured_project)

    return context
