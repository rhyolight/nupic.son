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

"""Module containing the views for GSoC Homepage."""

from django.conf.urls import url as django_url
from django.utils.translation import ugettext

from melange.request import access
from melange.request import exception
from melange.request import links

from soc.logic import accounts
from soc.logic.helper import timeline as timeline_helper
from soc.views.helper import lists
from soc.views.helper import url as url_helper
from soc.views.helper import url_patterns
from soc.views.helper.access_checker import isSet
from soc.views.org_home import BanOrgPost
from soc.views.org_home import HostActions
from soc.views.template import Template

from soc.modules.gsoc.logic import project as project_logic
from soc.modules.gsoc.models.organization import GSoCOrganization
from soc.modules.gsoc.models.project import GSoCProject
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper.url_patterns import url

from summerofcode.views.helper import urls


class Apply(Template):
  """Apply template."""

  def __init__(self, data, current_timeline):
    self.data = data
    self.current_timeline = current_timeline

  def context(self):
    context = {
        'request_data': self.data,
        'current_timeline': self.current_timeline,
        'organization': self.data.url_ndb_org,
    }

    if not self.data.profile:
      suffix = '?org=' + self.data.organization.link_id

      if self.data.timeline.studentsAnnounced():
        return context

      if self.data.timeline.studentSignup():
        context['student_apply_block'] = True
        profile_link = self.data.redirect.createProfile('student').urlOf(
            'create_gsoc_profile', secure=True)
        context['student_profile_link'] = profile_link + suffix
      else:
        context['mentor_apply_block'] = True

      profile_link = self.data.redirect.createProfile('mentor').urlOf(
          'create_gsoc_profile', secure=True)
      context['mentor_profile_link'] = profile_link + suffix
      return context

    if self.data.student_info:
      if self.data.timeline.studentSignup():
        context['student_apply_block'] = True
        # TODO(nathaniel): make this .organization() call unnecessary.
        self.data.redirect.organization()

        submit_proposal_link = self.data.redirect.urlOf('submit_gsoc_proposal')
        context['submit_proposal_link'] = submit_proposal_link

      return context

    context['mentor_apply_block'] = True

    if self.data.orgAdminFor(self.data.url_ndb_org.key):
      context['role'] = 'an administrator'
      return context

    if self.data.mentorFor(self.data.url_ndb_org.key):
      context['role'] = 'a mentor'
      return context

    mentor_connect_link = self.data.redirect.connect_user(
        self.data.user).urlOf(url_names.GSOC_USER_CONNECTION)
    context['mentor_connect_link'] = mentor_connect_link
    return context

  def templatePath(self):
    return "modules/gsoc/org_home/_apply.html"


class Contact(Template):
  """Organization Contact template.
  """

  def __init__(self, data):
    self.data = data

  def context(self):
    return {
        'facebook_link': self.data.organization.facebook,
        'twitter_link': self.data.organization.twitter,
        'blogger_link': self.data.organization.blog,
        'pub_mailing_list_link': self.data.organization.pub_mailing_list,
        'irc_channel_link': self.data.organization.irc_channel,
        'google_plus_link': self.data.organization.google_plus
    }

  def templatePath(self):
    return "modules/gsoc/_connect_with_us.html"


class ProjectList(Template):
  """Template for list of student projects accepted under the organization."""

  def __init__(self, data):
    self.data = data

    list_config = lists.ListConfiguration()
    list_config.addPlainTextColumn('student', 'Student',
        lambda entity, *args: entity.parent().name())
    list_config.addSimpleColumn('title', 'Title')
    list_config.addPlainTextColumn(
        'mentors', 'Mentor',
        lambda entity, m, *args: ", ".join(
            [m[i].name() for i in entity.mentors]))
    list_config.setDefaultSort('student')
    list_config.setRowAction(
        lambda e, *args, **kwargs: links.LINKER.userId(
            e.parent_key(), e.key().id(), url_names.GSOC_PROJECT_DETAILS))
    self._list_config = list_config

  def context(self):
    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=0,
        description='List of projects accepted into %s' % (
            self.data.organization.name))

    return {
        'lists': [list_configuration_response],
        }

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    idx = lists.getListIndex(self.data.request)
    if idx == 0:
      list_query = project_logic.getAcceptedProjectsQuery(
          program=self.data.program, org=self.data.organization)

      starter = lists.keyStarter
      prefetcher = lists.ListModelPrefetcher(
          GSoCProject, [],  ['mentors'], parent=True)

      response_builder = lists.RawQueryContentResponseBuilder(
          self.data.request, self._list_config, list_query,
          starter, prefetcher=prefetcher)
      return response_builder.build()
    else:
      return None

  def templatePath(self):
    return "modules/gsoc/org_home/_project_list.html"


class GSoCBanOrgPost(BanOrgPost, base.GSoCRequestHandler):
  """Handles banning/unbanning of GSoC organizations.
  """

  def _getModulePrefix(self):
    return 'gsoc'

  def _getURLPattern(self):
    return url_patterns.ORG

  def _getURLName(self):
    return url_names.GSOC_ORG_BAN

  def _getOrgModel(self):
    return GSoCOrganization


class GSoCHostActions(HostActions):
  """Template to render the left side host actions.
  """

  DEF_BAN_ORGANIZATION_HELP = ugettext(
      'When an organization is banned, it is not active in the program')

  def _getActionURLName(self):
    return url_names.GSOC_ORG_BAN

  def _getHelpText(self):
    return self.DEF_BAN_ORGANIZATION_HELP


class OrgHome(base.GSoCRequestHandler):
  """View methods for Organization Home page."""

  access_checker = access.ALL_ALLOWED_ACCESS_CHECKER

  def templatePath(self):
    return 'modules/gsoc/org_home/base.html'

  def djangoURLPatterns(self):
    """Returns the list of tuples for containing URL to view method mapping."""

    return [
        url(r'org/%s$' % url_patterns.ORG, self,
            name=url_names.GSOC_ORG_HOME),
        url(r'org/show/%s$' % url_patterns.ORG, self),
        url(r'org/home/%s$' % url_patterns.ORG, self),
        django_url(r'^org/show/%s$' % url_patterns.ORG, self),
        django_url(r'^org/home/%s$' % url_patterns.ORG, self),
    ]

  def jsonContext(self, data, check, mutator):
    """Handler for JSON requests."""
    assert isSet(data.organization)
    list_content = ProjectList(data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def context(self, data, check, mutator):
    """Handler to for GSoC Organization Home page HTTP get request."""
    current_timeline = self.getCurrentTimeline(
        data.program_timeline, data.org_app)

    assert isSet(data.organization)
    organization = data.organization

    context = {
        'page_name': '%s - Homepage' % organization.short_name,
        'organization': organization,
        'contact': Contact(data),
        'apply': Apply(data, current_timeline),
    }

    ideas = organization.ideas

    if organization.ideas:
      context['ideas_link'] = ideas
      context['ideas_link_trimmed'] = url_helper.trim_url_to(ideas, 50)

    if data.orgAdminFor(organization):
      # TODO(nathaniel): make this .organization call unnecessary.
      data.redirect.organization(organization=organization)

      context['edit_link'] = links.LINKER.organization(
          organization.key(), urls.UrlNames.ORG_PROFILE_EDIT)
      context['start_connection_link'] = data.redirect.connect_org().urlOf(
          url_names.GSOC_ORG_CONNECTION)

      if (data.program.allocations_visible and
          data.timeline.beforeStudentsAnnounced()):
        # TODO(nathaniel): make this .organization call unnecessary.
        data.redirect.organization(organization=organization)

        context['slot_transfer_link'] = data.redirect.urlOf(
            'gsoc_slot_transfer')

    if data.timeline.studentsAnnounced():
      context['students_announced'] = True

      context['project_list'] = ProjectList(data)

    if data.is_host or accounts.isDeveloper():
      context['host_actions'] = GSoCHostActions(data)

    return context

  def getCurrentTimeline(self, timeline, org_app):
    """Return where we are currently on the timeline."""
    if timeline_helper.isActivePeriod(org_app, 'survey'):
      return 'org_signup_period'
    elif timeline_helper.isActivePeriod(timeline, 'student_signup'):
      return 'student_signup_period'
    elif timeline_helper.isActivePeriod(timeline, 'program'):
      return 'program_period'
    else:
      return 'offseason'
