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

"""Module for the GSoC participant dashboard.
"""

__authors__ = [
  '"Sverre Rabbelier" <sverre@rabbelier.nl>',
  '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]


from django.conf.urls.defaults import url
from django.utils.dateformat import format
from django.utils.translation import ugettext

from soc.logic.exceptions import AccessViolation
from soc.logic.helper import timeline as timeline_helper
from soc.logic.models.request import logic as request_logic
from soc.views.template import Template

from soc.modules.gsoc.logic.models.org_app_survey import logic as \
    org_app_logic
from soc.modules.gsoc.logic.models.student_project import logic as \
    project_logic
from soc.modules.gsoc.logic.models.survey import project_logic as \
    ps_logic
from soc.modules.gsoc.models.proposal import GSoCProposal
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.base_templates import LoggedInMsg
from soc.modules.gsoc.views.helper import lists
from soc.modules.gsoc.views.helper import url_patterns


DATETIME_FORMAT = 'Y-m-d H:i:s'

class Dashboard(RequestHandler):
  """View for the participant dashboard.
  """

  def djangoURLPatterns(self):
    """The URL pattern for the dashboard.
    """
    return [
        url(r'^gsoc/dashboard/%s$' %url_patterns.PROGRAM, self,
            name='gsoc_dashboard')]

  def checkAccess(self):
    """Denies access if you don't have a role in the current program.
    """
    self.check.isLoggedIn()

  def templatePath(self):
    """Returns the path to the template.
    """
    return 'v2/modules/gsoc/dashboard/base.html'

  def jsonContext(self):
    """Handler for JSON requests.
    """
    components = self._getActiveComponents()

    list_content = None
    for component in components:
      list_content = component.getListData()
      if list_content:
        break

    if not list_content:
      raise AccessViolation(
          'You do not have access to this data')
    return list_content.content()

  def context(self):
    """Handler for default HTTP GET request.
    """
    components = self._getActiveComponents()

    return {
        'page_name': self.data.program.name,
        'user_name': self.data.profile.name() if self.data.profile else None,
        'logged_in_msg': LoggedInMsg(self.data),
    # TODO(ljvderijk): Implement code for setting dashboard messages.
    #   'alert_msg': 'Default <strong>alert</strong> goes here',
        'components': components,
    }

  def _getActiveComponents(self):
    """Returns the components that are active on the page.
    """
    components = []

    if self.data.student_info:
      components += self._getStudentComponents()
    elif self.data.is_mentor:
      components += self._getOrgMemberComponents()
      components.append(RequestComponent(self.request, self.data, False))
    else:
      components += self._getLoneUserComponents()
      components.append(RequestComponent(self.request, self.data, False))

    return components

  def _getStudentComponents(self):
    """Get the dashboard components for a student.
    """
    # Add all the proposals of this current user
    components = [MyProposalsComponent(self.request, self.data)]

    project = project_logic.getOneForFields({'student': self.data.profile})
    if project:
      # Add a component to show all the projects
      components.append(MyProjectsComponent(self.request, self.data))
      # Add a component to show the evaluations
      # TODO(ljvderijk): Enable after the right information can be displayed
      #components.append(MyEvaluationsComponent(self.request, self.data))

    return components

  def _getOrgMemberComponents(self):
    """Get the dashboard components for Organization members.
    """
    components = []

    if self.data.is_mentor:
      if timeline_helper.isAfterEvent(
          self.data.program_timeline, 'accepted_students_announced_deadline'):
        # add a component to show all projects a user is mentoring
        components.append(
            ProjectsIMentorComponent(self.request, self.data))

    if timeline_helper.isAfterEvent(
      self.data.program_timeline, 'student_signup_start'):
      # Add the submitted proposals component
      components.append(
          SubmittedProposalsComponent(self.request, self.data))

    components.append(OrganizationsIParticipateInComponent(self.request, self.data))

    if self.data.is_org_admin:
      # add a component for all organization that this user administers
      components.append(RequestComponent(self.request, self.data, True))
      components.append(ParticipantsComponent(self.request, self.data))

    return components

  def _getLoneUserComponents(self):
    """Get the dashboard components for users without any role.
    """
    components = []

    org_app_survey = org_app_logic.getForProgram(self.data.program)

    fields = {'survey': org_app_survey}
    org_app_record = org_app_logic.getRecordLogic().getForFields(fields,
                                                                 unique=True)

    if org_app_record:
      # add a component showing the organization application of the user
      components.append(MyOrgApplicationsComponent(self.request, self.data,
                                                   org_app_survey))

    return components


class Component(Template):
  """Base component for the dashboard.
  """

  def __init__(self, request, data):
    """Initializes the component.

    Args:
      request: The HTTPRequest object
      data: The RequestData object
    """
    self.request = request
    self.data = data

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    # by default no list is present
    return None


class MyOrgApplicationsComponent(Component):
  """Component for listing the Organization Applications of the current user.
  """

  def __init__(self, request, data, org_app_survey):
    """Initializes the component.

    Args:
      request: The HTTPRequest object
      data: The RequestData object
      org_app_survey: the OrgApplicationSurvey entity
    """
    # passed in so we don't have to do double queries
    self.org_app_survey = org_app_survey

    list_config = lists.ListConfiguration()
    list_config.addSimpleColumn('name', 'Organization Name')
    list_config.setDefaultSort('name')
    self._list_config = list_config

    super(MyOrgApplicationsComponent, self).__init__(request, data)

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return'v2/modules/gsoc/dashboard/list_component.html'

  def context(self):
    """Returns the context of this component.
    """
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=0,
        description='List of your Organization Applications')

    return {
        'name': 'org_applications',
        'title': 'MY ORGANIZATION APPLICATIONS',
        'lists': [list],
        }

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    idx = lists.getListIndex(self.request)
    if idx == 0:
      fields = {'survey': self.org_app_survey,
                'main_admin': self.data.user}
      response_builder = lists.QueryContentResponseBuilder(
          self.request, self._list_config, org_app_logic.getRecordLogic(),
          fields)
      return response_builder.build()
    else:
      return None


class MyProposalsComponent(Component):
  """Component for listing all the proposals of the current Student.
  """

  DESCRIPTION = ugettext(
      'Click on a proposal in this list to see the comments or update your proposal.')

  def __init__(self, request, data):
    """Initializes this component.
    """
    r = data.redirect
    list_config = lists.ListConfiguration()
    list_config.addSimpleColumn('title', 'Title')
    list_config.addColumn('org', 'Organization',
                          lambda ent, *args: ent.org.name)
    list_config.setRowAction(lambda e, *args, **kwargs: 
        r.review(e.key().id_or_name(), e.parent().link_id).
        urlOf('review_gsoc_proposal'))
    self._list_config = list_config

    super(MyProposalsComponent, self).__init__(request, data)


  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return'v2/modules/gsoc/dashboard/list_component.html'

  def context(self):
    """Returns the context of this component.
    """
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=1,
        description=MyProposalsComponent.DESCRIPTION)
    return {
        'name': 'proposals',
        'title': 'PROPOSALS',
        'lists': [list],
        }

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    idx = lists.getListIndex(self.request)
    if idx == 1:
      q = GSoCProposal.all()
      q.filter('program', self.data.program)
      q.ancestor(self.data.profile)

      starter = lists.keyStarter
      prefetcher = lists.modelPrefetcher(GSoCProposal, ['org'], parent=True)

      response_builder = lists.RawQueryContentResponseBuilder(
          self.request, self._list_config, q, starter, prefetcher=prefetcher)
      return response_builder.build()
    else:
      return None


class MyProjectsComponent(Component):
  """Component for listing all the projects of the current Student.
  """

  def __init__(self, request, data):
    """Initializes this component.
    """
    list_config = lists.ListConfiguration()
    list_config.addSimpleColumn('title', 'Title')
    list_config.addColumn('org_name', 'Organization Name',
                          lambda ent, *args: ent.scope.name)
    self._list_config = list_config

    super(MyProjectsComponent, self).__init__(request, data)

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return'v2/modules/gsoc/dashboard/list_component.html'

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    idx = lists.getListIndex(self.request)
    if idx == 2:
      fields = {'program': self.data.program,
                'student': self.data.profile}
      prefetch = ['scope']
      response_builder = lists.QueryContentResponseBuilder(
          self.request, self._list_config, project_logic, fields,
          prefetch=prefetch)
      return response_builder.build()
    else:
      return None

  def context(self):
    """Returns the context of this component.
    """
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=2,
        description='List of my student projects')
    return {
        'name': 'projects',
        'title': 'PROJECTS',
        'lists': [list],
    }


class MyEvaluationsComponent(Component):
  """Component for listing all the Evaluations of the current Student.
  """

  def __init__(self, request, data):
    """Initializes this component.
    """
    # TODO: This list should allow one to view or edit a record for each project
    # available to the student.
    list_config = lists.ListConfiguration()
    list_config.addSimpleColumn('title', 'Title')
    list_config.addSimpleColumn('survey_start', 'Survey Starts')
    list_config.addSimpleColumn('survey_end', 'Survey Ends')
    self._list_config = list_config

    super(MyEvaluationsComponent, self).__init__(request, data)

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return'v2/modules/gsoc/dashboard/list_component.html'

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    idx = lists.getListIndex(self.request)
    if idx == 3:
      fields = {'program': self.data.program}
      response_builder = lists.QueryContentResponseBuilder(
          self.request, self._list_config, ps_logic, fields)
      return response_builder.build()
    else:
      return None

  def context(self):
    """Returns the context of this component.
    """
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=3,
        description='List of my evaluations')

    return {
        'name': 'evaluations',
        'title': 'EVALUATIONS',
        'lists': [list],
    }


class SubmittedProposalsComponent(Component):
  """Component for listing all the proposals send to orgs this user is a member
  of.
  """

  DESCRIPTION = ugettext(
      'Click on a proposal to leave comments and give a score')

  def __init__(self, request, data):
    """Initializes this component.
    """
    r = data.redirect
    list_config = lists.ListConfiguration(add_key_column=False)
    list_config.addColumn('key', 'Key', (lambda ent, *args: "%s/%s" % (
        ent.parent().key().name(), ent.key().id())), hidden=True)
    list_config.addSimpleColumn('title', 'Title')
    list_config.addSimpleColumn('score', 'Score')
    list_config.addColumn(
        'last_modified_on', 'Last modified',
        lambda ent, *args: format(ent.last_modified_on, DATETIME_FORMAT))
    list_config.addColumn(
        'created_on', 'Created on',
        (lambda ent, *args: format(ent.created_on, DATETIME_FORMAT)),
        hidden=True)
    list_config.addColumn(
        'student', 'Student',
        lambda ent, *args: ent.parent().name())
    options = [
        ('(pending|accepted|rejected)', 'Valid'),
        ('', 'All'),
        ('(invalid|withdrawn)', 'Invalid'),
    ]
    list_config.addSimpleColumn('status', 'Status',
                                hidden=True, options=options)

    def mentor_key(ent, *args):
      key = GSoCProposal.mentor.get_value_for_datastore(ent)
      if not key:
        return ""
      split_name = key.name().split('/')
      return split_name[-1]

    list_config.addColumn('mentor', 'Assigned mentor link_id',
                          mentor_key, hidden=True)
    if not data.is_host:
      options = ([('', 'All')] +
          [("^%s$" % i.short_name, i.short_name) for i in data.mentor_for])
    else:
      options = None
    list_config.addColumn(
        'org', 'Organization', (lambda ent, *args: ent.org.short_name),
        options=options, hidden=True)
    list_config.setRowAction(lambda e, *args, **kwargs: 
        r.review(e.key().id_or_name(), e.parent().link_id).
        urlOf('review_gsoc_proposal'))
    list_config.setDefaultSort('last_modified_on', 'desc')
    self._list_config = list_config

    super(SubmittedProposalsComponent, self).__init__(request, data)

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return'v2/modules/gsoc/dashboard/list_component.html'

  def context(self):
    """Returns the context of this component.
    """
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=4,
        description=SubmittedProposalsComponent.DESCRIPTION)
    return {
        'name': 'proposals_submitted',
        'title': 'PROPOSALS SUBMITTED TO MY ORGS',
        'lists': [list],
        }

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    idx = lists.getListIndex(self.request)
    if idx != 4:
      return None

    q = GSoCProposal.all()
    if not self.data.is_host:
      q.filter('org IN', self.data.mentor_for)
    else:
      q.filter('program', self.data.program)

    starter = lists.keyStarter
    prefetcher = lists.modelPrefetcher(GSoCProposal, ['org'], parent=True)

    response_builder = lists.RawQueryContentResponseBuilder(
        self.request, self._list_config, q, starter, prefetcher=prefetcher)
    return response_builder.build()


class ProjectsIMentorComponent(Component):
  """Component for listing all the Projects mentored by the current user.
  """

  def __init__(self, request, data):
    """Initializes this component.
    """
    list_config = lists.ListConfiguration()
    list_config.addSimpleColumn('title', 'Title')
    list_config.addColumn('org_name', 'Organization',
                          lambda ent, *args: ent.scope.name)
    list_config.setDefaultSort('title')
    self._list_config = list_config

    super(ProjectsIMentorComponent, self).__init__(request, data)

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return'v2/modules/gsoc/dashboard/list_component.html'

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    idx = lists.getListIndex(self.request)
    if idx == 5:
      fields =  {'program': self.data.program,
                 'mentor': self.data.profile}
      response_builder = lists.QueryContentResponseBuilder(
          self.request, self._list_config, project_logic,
          fields, prefetch=['scope'])
      return response_builder.build()
    else:
      return None

  def context(self):
    """Returns the context of this component.
    """
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=5,
        description='List of projects I mentor')

    return {
        'name': 'mentoring_projects',
        'title': 'PROJECTS I AM A MENTOR FOR',
        'lists': [list],
    }


class OrganizationsIParticipateInComponent(Component):
  """Component listing all the Organizations the current user participates in.
  """

  def __init__(self, request, data):
    """Initializes this component.
    """
    r = data.redirect
    list_config = lists.ListConfiguration()
    list_config.addSimpleColumn('name', 'name')
    list_config.setRowAction(
        lambda e, *args, **kwargs: r.organization(e).urlOf('gsoc_org_home'))
    list_config.setDefaultSort('name')
    self._list_config = list_config

    super(OrganizationsIParticipateInComponent, self).__init__(request, data)

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return'v2/modules/gsoc/dashboard/list_component.html'

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    idx = lists.getListIndex(self.request)
    if idx == 6:
      response = lists.ListContentResponse(self.request, self._list_config)

      if response.start != 'done':
        # Add all organizations in one go since we already queried for it.
        for mentor in self.data.mentor_for:
          response.addRow(mentor)
        response.next = 'done'

      return response
    else:
      return None

  def context(self):
    """Returns the context of this component.
    """
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=6,
        description='Organizations you are an admin for')

    return {
        'name': 'adminning_organizations',
        'title': 'MY ORGANIZATIONS',
        'lists': [list],
    }


class RequestComponent(Component):
  """Component for listing all the requests for orgs of which the user is an
  admin.
  """

  def __init__(self, request, data, for_admin):
    """Initializes this component.
    """
    self.for_admin = for_admin
    self.idx = 7 if for_admin else 8
    r = data.redirect
    list_config = lists.ListConfiguration()
    list_config.addSimpleColumn('type', 'Request/Invite')
    if self.for_admin:
      list_config.addColumn(
          'user', 'User', lambda ent, *args: "%s (%s)" % (
          ent.user.name, ent.user.link_id))
    list_config.addColumn('role_name', 'Role',
                          lambda ent, *args: ent.roleName())

    options = [
        ('pending', 'Needs action'),
        ('', 'All'),
        ('(rejected|accepted)', 'Handled'),
        ('(withdrawn|invalid)', 'Removed'),
    ]
    list_config.addSimpleColumn('status', 'Status', options=options)
    list_config.addColumn('org_name', 'Organization',
                          lambda ent, *args: ent.group.name)
    list_config.setRowAction(
        lambda ent, *args: r.request(ent).url())
    self._list_config = list_config

    super(RequestComponent, self).__init__(request, data)

  def templatePath(self):
    return'v2/modules/gsoc/dashboard/list_component.html'

  def getListData(self):
    idx = lists.getListIndex(self.request)
    if idx == self.idx:
      if self.for_admin:
        fields = {'group': self.data.org_admin_for}
      else:
        fields = {'user': self.data.user}
      response_builder = lists.QueryContentResponseBuilder(
          self.request, self._list_config, request_logic, fields, prefetch=['user', 'group'])
      return response_builder.build()
    else:
      return None

  def context(self):
    """Returns the context of this component.
    """
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=self.idx)

    if self.for_admin:
      title = 'REQUESTS FOR MY ORGANIZATIONS'
    else:
      title = 'MY REQUESTS'

    return {
        'name': 'requests',
        'title': title,
        'lists': [list],
    }


class ParticipantsComponent(Component):
  """Component for listing all the participants for all organizations.
  """

  def __init__(self, request, data):
    """Initializes this component.
    """
    self.data = data
    list_config = lists.ListConfiguration()
    list_config.addColumn(
        'name', 'Name', lambda ent, *args: ent.name())
    list_config.addSimpleColumn('email', "Email")

    if self.data.is_host:
      get = lambda i, orgs: orgs[i].link_id
    else:
      get = lambda i, orgs: orgs[i].name

    list_config.addColumn(
        'mentor_for', 'Mentor for',
        lambda ent, orgs, *args: ', '.join(
            [get(i, orgs) for i in ent.mentor_for if data.orgAdminFor(i)]))
    list_config.addColumn(
        'admin_for', 'Organization admin for',
        lambda ent, orgs, *args: ', '.join(
            [get(i, orgs) for i in ent.org_admin_for if data.orgAdminFor(i)]))
    self._list_config = list_config

    super(ParticipantsComponent, self).__init__(request, data)

  def templatePath(self):
    return'v2/modules/gsoc/dashboard/list_component.html'

  def getListData(self):
    idx = lists.getListIndex(self.request)

    if idx != 9:
      return None

    q = GSoCProfile.all()

    if self.data.is_host:
      q.filter('scope', self.data.program)
      q.filter('is_mentor', True)
      prefetcher = lists.listPrefetcher(
          GSoCProfile, ['mentor_for', 'org_admin_for'])
    else:
      org_dict = dict((i.key(), i) for i in self.data.mentor_for)
      q.filter('mentor_for IN', self.data.profile.org_admin_for)
      prefetcher = lambda entities: ([org_dict], {})

    starter = lists.keyStarter

    response_builder = lists.RawQueryContentResponseBuilder(
        self.request, self._list_config, q, starter,
        prefetcher=prefetcher)
    return response_builder.build()

  def context(self):
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=9)

    return {
        'name': 'participants',
        'title': 'MEMBERS OF MY ORGANIZATIONS',
        'lists': [list],
    }
