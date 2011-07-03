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
  '"Madhusudan.C.S" <madhusudancs@gmail.com>',
  '"Sverre Rabbelier" <sverre@rabbelier.nl>',
  '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]

import logging

from google.appengine.ext import db

from django.utils import simplejson
from django.utils.dateformat import format
from django.utils.translation import ugettext

from soc.logic import cleaning
from soc.logic.exceptions import AccessViolation
from soc.logic.exceptions import BadRequest
from soc.logic.models.request import logic as request_logic
from soc.models.universities import UNIVERSITIES
from soc.views.helper import lists
from soc.views.template import Template

from soc.modules.gsoc.logic import grading_project_survey as gps_logic
from soc.modules.gsoc.logic import grading_project_survey_record as gpsr_logic
from soc.modules.gsoc.logic import project as project_logic
from soc.modules.gsoc.logic import project_survey as ps_logic
from soc.modules.gsoc.logic import project_survey_record as psr_logic
from soc.modules.gsoc.logic.models.org_app_survey import logic as \
    org_app_logic
from soc.modules.gsoc.logic.proposal import getProposalsToBeAcceptedForOrg
from soc.modules.gsoc.logic.project import GSoCProject
from soc.modules.gsoc.models.proposal import GSoCProposal
from soc.modules.gsoc.models.proposal_duplicates import GSoCProposalDuplicate
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.models.profile import GSoCStudentInfo
from soc.modules.gsoc.models.organization import GSoCOrganization
from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.base_templates import LoggedInMsg
from soc.modules.gsoc.views.base_templates import ProgramSelect
from soc.modules.gsoc.views.helper import url_patterns
from soc.modules.gsoc.views.helper.url_patterns import url


DATETIME_FORMAT = 'Y-m-d H:i:s'
BIRTHDATE_FORMAT = 'd-m-Y'


def colorize(choice, yes, no):
  """Differentiate between yes and no status with green and red colors.
  """
  if choice:
    return """<font color="green">%s</font>""" % yes
  else:
    return """<strong><font color="red">%s</font></strong>""" % no


class Dashboard(RequestHandler):
  """View for the participant dashboard.
  """

  def djangoURLPatterns(self):
    """The URL pattern for the dashboard.
    """
    return [
        url(r'dashboard/%s$' % url_patterns.PROGRAM, self,
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

  def post(self):
    """Handler for POST requests.
    """
    components = self._getActiveComponents()

    for component in components:
      if component.post():
        break
    else:
      raise AccessViolation(
          'You cannot change this data')

  def context(self):
    """Handler for default HTTP GET request.
    """
    components = self._getActiveComponents()

    return {
        'page_name': self.data.program.name,
        'user_name': self.data.profile.name() if self.data.profile else None,
        'logged_in_msg': LoggedInMsg(self.data),
        'program_select': ProgramSelect(self.data, 'gsoc_dashboard'),
    # TODO(ljvderijk): Implement code for setting dashboard messages.
    #   'alert_msg': 'Default <strong>alert</strong> goes here',
        'components': components,
    }

  def _getActiveComponents(self):
    """Returns the components that are active on the page.
    """
    components = []

    if self.data.student_info:
      components.append(TodoComponent(self.request, self.data))
      components += self._getStudentComponents()
    elif self.data.is_mentor:
      components.append(TodoComponent(self.request, self.data))
      components += self._getOrgMemberComponents()
      components.append(RequestComponent(self.request, self.data, False))
    else:
      components += self._getLoneUserComponents()
      components.append(RequestComponent(self.request, self.data, False))

    if self.data.is_host:
      components += self._getHostComponents()

    return components

  def _getHostComponents(self):
    """Get the dashboard components for a host.
    """
    components = []

    components.append(StudentsComponent(self.request, self.data))

    return components

  def _getStudentComponents(self):
    """Get the dashboard components for a student.
    """
    components = []

    project_query = project_logic.getAcceptedProjectsQuery(
      keys_only=True, ancestor=self.data.profile)

    if project_query.count() > 0:
      # Add a component to show the evaluations
      ms_eval = ps_logic.getProjectSurveyForProgram(
          self.data.program, 'midterm')
      if (ms_eval and self.data.timeline.afterSurveyStart(
          ms_eval)):
        components.append(MyEvaluationsComponent(self.request, self.data))

      # Add a component to show all the projects
      components.append(MyProjectsComponent(self.request, self.data))

    # Add all the proposals of this current user
    components.append(MyProposalsComponent(self.request, self.data))

    return components

  def _getOrgMemberComponents(self):
    """Get the dashboard components for Organization members.
    """
    components = []

    if self.data.is_mentor:
      if self.data.timeline.studentsAnnounced():
        # add a component to show all projects a user is mentoring
        components.append(
            ProjectsIMentorComponent(self.request, self.data))

    orgs = OrganizationsIParticipateInComponent(self.request, self.data)

    # move to the top during student signup
    if self.data.timeline.studentSignup():
      components.append(orgs)

    if self.data.timeline.afterStudentSignupStart():
      # Add the submitted proposals component
      components.append(
          SubmittedProposalsComponent(self.request, self.data))

    if self.data.is_org_admin:
      # add a component for all organization that this user administers
      components.append(RequestComponent(self.request, self.data, True))
      components.append(ParticipantsComponent(self.request, self.data))

    # move to the bottom after student signup
    if not self.data.timeline.studentSignup():
      components.append(orgs)

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

  def post(self):
    """Handles a post request.

    If posting to the list as requested is not supported by this component
    False is returned.
    """
    # by default post is not supported
    return False


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
        self.data, self._list_config, idx=0)

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
    if lists.getListIndex(self.request) != 0:
      return None

    fields = {'survey': self.org_app_survey,
              'main_admin': self.data.user}
    response_builder = lists.QueryContentResponseBuilder(
        self.request, self._list_config, org_app_logic.getRecordLogic(),
        fields)
    return response_builder.build()


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
    if lists.getListIndex(self.request) != 1:
      return None

    q = GSoCProposal.all()
    q.filter('program', self.data.program)
    q.ancestor(self.data.profile)

    starter = lists.keyStarter
    prefetcher = lists.modelPrefetcher(GSoCProposal, ['org'], parent=True)

    response_builder = lists.RawQueryContentResponseBuilder(
        self.request, self._list_config, q, starter, prefetcher=prefetcher)
    return response_builder.build()


class MyProjectsComponent(Component):
  """Component for listing all the projects of the current Student.
  """

  def __init__(self, request, data):
    """Initializes this component.
    """
    r = data.redirect

    list_config = lists.ListConfiguration(add_key_column=False)
    list_config.addColumn('key', 'Key', (lambda ent, *args: "%s/%s" % (
        ent.parent().key().name(), ent.key().id())), hidden=True)
    list_config.addSimpleColumn('title', 'Title')
    list_config.addColumn('org', 'Organization Name',
                          lambda ent, *args: ent.org.name)
    list_config.setRowAction(lambda e, *args, **kwargs:
        r.project(id=e.key().id_or_name(), student=e.parent().link_id).
        urlOf('gsoc_project_details'))
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
    if lists.getListIndex(self.request) != 2:
      return None

    list_query = project_logic.getAcceptedProjectsQuery(
        ancestor=self.data.profile, program=self.data.program)

    starter = lists.keyStarter
    prefetcher = lists.modelPrefetcher(GSoCProject, ['org'], parent=True)

    response_builder = lists.RawQueryContentResponseBuilder(
        self.request, self._list_config, list_query,
        starter, prefetcher=prefetcher)
    return response_builder.build()

  def context(self):
    """Returns the context of this component.
    """
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=2)
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
    list_config = lists.ListConfiguration(add_key_column=False)
    list_config.addColumn(
        'key', 'Key', (lambda d, *args: d['key']), hidden=True)
    list_config.addDictColumn('evaluation', 'Evaluation')
    list_config.addDictColumn('project_title', 'Project')
    list_config.addDictColumn('status', 'Status')
    def rowAction(d, *args):
      key = d['key']
      if key == 'ms_eval':
        return data.redirect.survey_record(
            'midterm', d.get('project'), d.get('student')).urlOf(
            'gsoc_take_student_evaluation')
      if key == 'fs_eval':
        return data.redirect.survey_record(
            'final', d.get('project'), d.get('student')).urlOf(
            'gsoc_take_student_evaluation')
      return None

    list_config.setRowAction(rowAction)
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
    if lists.getListIndex(self.request) != 3:
      return None

    response = lists.ListContentResponse(self.request, self._list_config)

    projects = project_logic.getAcceptedProjectsForStudent(self.data.profile)

    ms_eval = ps_logic.getProjectSurveyForProgram(self.data.program, 'midterm')
    if (ms_eval and self.data.timeline.afterSurveyStart(ms_eval)):
      for project in projects:
        status = colorize(psr_logic.evalRecordExistsForStudent(
            ms_eval, project), "Submitted", "Not submitted")
        response.addRow({
            'key': 'ms_eval',
            'project': project.key().id(),
            'student': project.parent().link_id,
            'evaluation': 'Midterm',
            'project_title': project.title,
            'status': status
        })

    fs_eval = ps_logic.getProjectSurveyForProgram(self.data.program, 'final')
    if (fs_eval and self.data.timeline.afterSurveyStart(fs_eval)):
      for project in projects:
        status = colorize(psr_logic.evalRecordExistsForStudent(
            fs_eval, project), "Submitted", "Not submitted")
        response.addRow({
            'key': 'fs_eval',
            'project': project.key().id(),
            'student': project.parent().link_id,
            'evaluation': 'Final',
            'project_title': project.title,
            'status': status
        })

    response.next = 'done'

    return response

  def context(self):
    """Returns the context of this component.
    """
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=3)

    return {
        'name': 'evaluations',
        'title': 'EVALUATIONS',
        'lists': [list],
    }



  def context(self):
    """Returns the context of this component.
    """
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=3)

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
      'Click on a proposal to leave comments and give a score.')

  CUSTOM_COLUMNS = ugettext(
      '<p>To show/edit a custom column, select an organization from '
      'the organization dropdown, the custom columns for that organization '
      'will then be shown. Edit a column by clicking on it.<br/>'
      'Hit enter to save your changes to the current column, '
      'press esc or click outside the column to cancel. '
      '<br/> Note: Due to a bug you cannot edit a row after '
      'having just edited it, click a different row first.</p>')

  def __init__(self, request, data):
    """Initializes this component.
    """
    r = data.redirect
    list_config = lists.ListConfiguration(add_key_column=False)
    list_config.addColumn('key', 'Key', (lambda ent, *args: "%s/%s" % (
        ent.parent().key().name(), ent.key().id())), hidden=True)
    list_config.addSimpleColumn('title', 'Title')
    list_config.addColumn(
        'email', 'Student Email',
        (lambda ent, *args: ent.parent().email), hidden=True)
    list_config.addSimpleColumn('score', 'Score')
    list_config.addSimpleColumn('nr_scores', '#scores', hidden=True)
    def getAverage(ent):
      if not ent.nr_scores:
        return float(0)

      average = float(ent.score)/float(ent.nr_scores)
      return float("%.2f" % average)

    list_config.addColumn(
        'average', 'Average', lambda ent, *a: getAverage(ent))

    def getStatusOnDashboard(proposal, accepted, duplicates):
      """Method for determining which status to show on the dashboard.
      """
      if proposal.status == 'pending' and self.data.program.duplicates_visible:
          if proposal.accept_as_project and (
              not GSoCProposal.mentor.get_value_for_datastore(proposal)):
            return """<strong><font color="red">No mentor assigned</font></strong>"""
          elif proposal.key() in duplicates:
            return """<strong><font color="red">Duplicate</font></strong>"""
          elif proposal.key() in accepted:
            return """<strong><font color="green">Pending acceptance</font><strong>"""
      # not showing duplicates or proposal doesn't have an interesting state
      return proposal.status
    options = [
        ('(pending|accepted|rejected|duplicate|mentor)', 'Valid'),
        ('(duplicate|mentor)', 'Needs attention'),
        ('(duplicate)', 'Duplicate'),
        ('(accepted)', 'Accepted'),
        ('(rejected)', 'Rejected'),
        ('(mentor)', 'No mentor assigned'),
        ('', 'All'),
        ('(invalid|withdrawn|ignored)', 'Invalid'),
    ]
    list_config.addColumn('status', 'Status', getStatusOnDashboard, options=options)

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
    list_config.addSimpleColumn('accept_as_project', 'Should accept')

    # assigned mentor column
    def split_key(key):
      split_name = key.name().split('/')
      return split_name[-1]

    def mentor_key(ent, *args):
      key = GSoCProposal.mentor.get_value_for_datastore(ent)
      if not key:
        return ""
      return split_key(key)

    def mentor_keys(ent, *args):
      return ', '.join(split_key(i) for i in ent.possible_mentors)

    list_config.addColumn('mentor', 'Assigned mentor link_id',
                          mentor_key, hidden=True)
    list_config.addColumn('possible_mentors', 'Possible mentor link_ids',
                          mentor_keys, hidden=True)

    # organization column
    if not data.is_host:
      orgs = data.mentor_for
      options = [("^%s$" % i.short_name, i.short_name) for i in orgs]
    else:
      options = None

    if options and len(options) > 1:
      options = [('', 'All')] + options

    hidden = len(data.mentor_for) < 2
    list_config.addColumn(
        'org', 'Organization', (lambda ent, *args: ent.org.short_name),
        options=options, hidden=hidden)

    # hidden keys
    list_config.addColumn(
        'full_proposal_key', 'Full proposal key',
        (lambda ent, *args: str(ent.key())), hidden=True)
    list_config.addColumn(
        'org_key', 'Organization key',
        (lambda ent, *args: ent.org.key().name()), hidden=True)

    # row action
    list_config.setRowAction(lambda e, *args, **kwargs: 
        r.review(e.key().id_or_name(), e.parent().link_id).
        urlOf('review_gsoc_proposal'))
    list_config.setDefaultSort('last_modified_on', 'desc')

    # additional columns
    def get_col_prop(column):
      def getter(ent, *args):
        if not ent.extra:
          return ""
        extra = simplejson.loads(ent.extra)
        return extra.get(column, "")
      return getter

    extra_columns = []
    for org in data.mentor_for:
      for column in org.proposal_extra:
        extra_columns.append(column)
        col_name = "%s" % (column)
        list_config.addColumn(
            column, col_name, get_col_prop(column))
        list_config.setColumnEditable(column, True, 'text', {})
        list_config.setColumnExtra(column, org="^%s$" % org.short_name)

    self.has_extra_columns = bool(extra_columns)

    if self.has_extra_columns:
      fields = ['full_proposal_key', 'org_key']
      list_config.addPostEditButton('save', "Save", "", fields, refresh="none")

    if data.is_org_admin:
      # accept/reject proposals
      bounds = [1,'all']
      keys = ['full_proposal_key']
      list_config.addPostButton('accept', "Accept", "", bounds, keys)
      list_config.addPostButton('unaccept', "Unaccept", "", bounds, keys)

    self._list_config = list_config

    super(SubmittedProposalsComponent, self).__init__(request, data)

  def templatePath(self):
    return'v2/modules/gsoc/dashboard/list_component.html'

  def context(self):
    description = self.DESCRIPTION

    if self.has_extra_columns:
      description += self.CUSTOM_COLUMNS

    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=4, description=description)
    return {
        'name': 'proposals_submitted',
        'title': 'PROPOSALS SUBMITTED TO MY ORGS',
        'lists': [list],
        }

  def post(self):
    idx = lists.getListIndex(self.request)
    if idx != 4:
      return None

    data = self.data.POST.get('data')

    if not data:
      raise BadRequest("Missing data")

    parsed = simplejson.loads(data)

    button_id = self.data.POST.get('button_id')

    if not button_id:
      raise BadRequest("Missing button_id")

    if button_id == 'save':
      return self.postSave(parsed)

    if button_id == 'accept':
      return self.postAccept(parsed, True)

    if button_id == 'unaccept':
      return self.postAccept(parsed, False)

    raise BadRequest("Unknown button_id")

  def postSave(self, parsed):
    extra_columns = {}

    for org in self.data.mentor_for:
      for column in org.proposal_extra:
        extra_columns.setdefault(org.key().name(), []).append(column)

    for _, properties in parsed.iteritems():
      if 'org_key' not in properties or 'full_proposal_key' not in properties:
        logging.warning("Missing key in '%s'" % properties)
        continue

      org_key_name = properties.pop('org_key')
      proposal_key = properties.pop('full_proposal_key')

      valid_columns = set(extra_columns.get(org_key_name, []))
      remove_properties = []

      for key, value in properties.iteritems():
        if key not in valid_columns:
          logging.warning("Invalid property '%s'" % key)
          remove_properties.append(key)
        try:
          cleaning.sanitize_html_string(value)
        except Exception:
          remove_properties.append(key)

      for prop in remove_properties:
        properties.pop(prop)

      def update_proposal_txn():
        proposal = db.get(db.Key(proposal_key))

        if not proposal:
          logging.warning("Invalid proposal_key '%s'" % proposal_key)
          return

        data = {}

        if proposal.extra:
          # we have to loads in the txn, should be fast enough
          data = simplejson.loads(proposal.extra)

        data.update(properties)

        proposal.extra = simplejson.dumps(data)
        proposal.put()

      db.run_in_transaction(update_proposal_txn)

    return True

  def postAccept(self, data, accept):
    for properties in data:
      if 'full_proposal_key' not in properties:
        logging.warning("Missing key in '%s'" % properties)
        continue
      proposal_key = properties['full_proposal_key']
      def accept_proposal_txn():
        proposal = db.get(db.Key(proposal_key))

        if not proposal:
          logging.warning("Invalid proposal_key '%s'" % proposal_key)
          return

        org_key = GSoCProposal.org.get_value_for_datastore(proposal)
        if not self.data.orgAdminFor(org_key):
          logging.warning("Not an org admin")
          return

        proposal.accept_as_project = accept
        proposal.put()

      db.run_in_transaction(accept_proposal_txn)

    return True

  def getListData(self):
    idx = lists.getListIndex(self.request)
    if idx != 4:
      return None

    # Hold all the accepted projects for orgs where this user is a member of
    accepted = []
    # Hold all duplicates for either the entire program or the orgs of the user.
    duplicates = []
    dupQ = GSoCProposalDuplicate.all()
    dupQ.filter('is_duplicate', True)

    q = GSoCProposal.all()
    if not self.data.is_host:
      q.filter('org IN', self.data.mentor_for)
      dupQ.filter('orgs IN', self.data.mentor_for)

      # Only fetch the data if we will display it
      if self.data.program.duplicates_visible:
        for org in self.data.mentor_for:
          accepted.extend([p.key() for p in getProposalsToBeAcceptedForOrg(org)])
    else:
      q.filter('program', self.data.program)
      dupQ.filter('program', self.data.program)

    # Only fetch the data if it is going to be displayed
    if self.data.program.duplicates_visible:
      duplicate_entities = dupQ.fetch(1000)
      for dup in duplicate_entities:
        duplicates.extend(dup.duplicates)

    starter = lists.keyStarter
    prefetcher = lists.modelPrefetcher(GSoCProposal, ['org'], parent=True)

    response_builder = lists.RawQueryContentResponseBuilder(
        self.request, self._list_config, q, starter, prefetcher=prefetcher)
    return response_builder.build(accepted, duplicates)


class ProjectsIMentorComponent(Component):
  """Component for listing all the Projects mentored by the current user.
  """

  def __init__(self, request, data):
    """Initializes this component.
    """
    r = data.redirect
    list_config = lists.ListConfiguration(add_key_column=False)
    list_config.addColumn('key', 'Key', (lambda ent, *args: "%s/%s" % (
        ent.parent().key().name(), ent.key().id())), hidden=True)
    list_config.addSimpleColumn('title', 'Title')
    list_config.addColumn('student', 'Student',
                          lambda ent, *args: ent.parent().name())
    list_config.addColumn('org', 'Organization',
                          lambda ent, *args: ent.org.name)
    list_config.setDefaultSort('title')
    list_config.setRowAction(lambda e, *args, **kwargs:
        r.project(id=e.key().id_or_name(), student=e.parent().link_id).
        urlOf('gsoc_project_details'))
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
    if lists.getListIndex(self.request) != 5:
      return None

    list_query = project_logic.getAcceptedProjectsQuery(
        program=self.data.program)

    if self.data.is_org_admin:
      list_query.filter('org IN', self.data.profile.org_admin_for)
    else:
      list_query.filter('mentor', self.data.profile)

    starter = lists.keyStarter
    prefetcher = lists.modelPrefetcher(GSoCProject, ['org'], parent=True)

    response_builder = lists.RawQueryContentResponseBuilder(
        self.request, self._list_config, list_query,
        starter, prefetcher=prefetcher)
    return response_builder.build()

  def context(self):
    """Returns the context of this component.
    """
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=5)

    if self.data.is_org_admin:
      title = 'PROJECTS FOR MY ORGS'
    else:
      title = 'PROJECTS I AM A MENTOR FOR'

    return {
        'name': 'mentoring_projects',
        'title': title,
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
    list_config.setRowAction(
        lambda e, *args, **kwargs: r.organization(e).urlOf('gsoc_org_home'))

    if not data.program.allocations_visible:
      list_config.addSimpleColumn('name', 'name')
    else:
      def c(ent, s, text):
        if ent.slots - s == 0:
          return text
        return """<strong><font color="red">%s</font></strong>""" % text

      list_config.addSimpleColumn('link_id', 'Link ID', hidden=True)
      list_config.addColumn('name', 'name', lambda ent, s, *args: c(ent, s, ent.name))
      list_config.addSimpleColumn('slots', 'Slots allowed')
      list_config.addColumn(
          'slots_used', 'Slots used', lambda ent, s, *args: s)
      list_config.addColumn(
          'delta', 'Slots difference',
          lambda ent, s, *args: c(ent, s, (ent.slots - s)))
      list_config.addColumn(
          'delta_sortable', 'Slots difference (sortable)',
          (lambda ent, s, *args: abs(ent.slots - s)), hidden=True)

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
    if lists.getListIndex(self.request) != 6:
      return None

    response = lists.ListContentResponse(self.request, self._list_config)

    if response.start == 'done' or (
        response.start and not response.start.isdigit()):
      return response

    pos = int(response.start) if response.start else 0

    if self.data.is_host:
      q = GSoCOrganization.all().filter('scope', self.data.program)
      orgs = q.fetch(1000)
    else:
      orgs = self.data.mentor_for

    if pos < len(orgs):
      org = orgs[pos]
      q = db.Query(GSoCProposal, keys_only=False).filter('org', org)
      q.filter('has_mentor', True).filter('accept_as_project', True)
      slots_used = q.count()
      response.addRow(org, slots_used)

    if (pos + 1) < len(orgs):
      response.next = str(pos + 1)
    else:
      response.next = 'done'

    return response

  def context(self):
    """Returns the context of this component.
    """
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=6)

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
    if lists.getListIndex(self.request) != self.idx:
      return None

    if self.for_admin:
      fields = {'group': self.data.org_admin_for}
    else:
      fields = {'user': self.data.user}
    response_builder = lists.QueryContentResponseBuilder(
        self.request, self._list_config, request_logic, fields, prefetch=['user', 'group'])
    return response_builder.build()

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


class StudentsComponent(Component):
  """Component for listing all the students.
  """

  def __init__(self, request, data):
    """Initializes this component.
    """
    r = data.redirect
    self.data = data
    list_config = lists.ListConfiguration()
    list_config.addColumn(
        'name', 'Name', lambda ent, *args: ent.name())
    list_config.addSimpleColumn('link_id', "Link ID")
    list_config.addSimpleColumn('email', "Email")
    list_config.addSimpleColumn('given_name', "Given name", hidden=True)
    list_config.addSimpleColumn('surname', "Surname", hidden=True)
    list_config.addSimpleColumn('name_on_documents', "Legal name", hidden=True)
    list_config.addColumn(
        'birth_date', "Birthdate",
        (lambda ent, *args: format(ent.birth_date, BIRTHDATE_FORMAT)),
        hidden=True)
    list_config.setRowAction(lambda e, *args, **kwargs:
        r.profile(e.link_id).urlOf('gsoc_profile_admin'))

    def formsSubmitted(ent, si):
      info = si[ent.key()]
      tax = GSoCStudentInfo.tax_form.get_value_for_datastore(info)
      enroll = GSoCStudentInfo.enrollment_form.get_value_for_datastore(info)
      return [tax, enroll]

    list_config.addColumn(
        'tax_submitted', "Tax form submitted",
        (lambda ent, si, *args: bool(formsSubmitted(ent, si)[0])),
        hidden=True)

    list_config.addColumn(
        'enroll_submitted', "Enrollment form submitted",
        (lambda ent, si, *args: bool(formsSubmitted(ent, si)[1])),
        hidden=True)

    list_config.addColumn(
        'forms_submitted', "Forms submitted",
        lambda ent, si, *args: all(formsSubmitted(ent, si)))

    # address fields
    list_config.addSimpleColumn('res_street', "res_street", hidden=True)
    list_config.addSimpleColumn('res_street_extra', "res_street_extra", hidden=True)
    list_config.addSimpleColumn('res_city', "res_city", hidden=True)
    list_config.addSimpleColumn('res_state', "res_state", hidden=True)
    list_config.addSimpleColumn('res_country', "res_country", hidden=True)
    list_config.addSimpleColumn('res_postalcode', "res_postalcode", hidden=True)
    list_config.addSimpleColumn('phone', "phone", hidden=True)
    list_config.addSimpleColumn('ship_name', "ship_name", hidden=True)
    list_config.addSimpleColumn('ship_street', "ship_street", hidden=True)
    list_config.addSimpleColumn('ship_street_extra', "ship_street_extra", hidden=True)
    list_config.addSimpleColumn('ship_city', "ship_city", hidden=True)
    list_config.addSimpleColumn('ship_state', "ship_state", hidden=True)
    list_config.addSimpleColumn('ship_country', "ship_country", hidden=True)
    list_config.addSimpleColumn('ship_postalcode', "ship_postalcode", hidden=True)

    list_config.addColumn(
        'number_of_proposals', "#proposals",
        lambda ent, si, *args: si[ent.key()].number_of_proposals)
    list_config.addColumn(
        'number_of_projects', "#projects",
        lambda ent, si, *args: si[ent.key()].number_of_projects)

    self._list_config = list_config

    super(StudentsComponent, self).__init__(request, data)

  def templatePath(self):
    return'v2/modules/gsoc/dashboard/list_component.html'

  def getListData(self):
    idx = lists.getListIndex(self.request)

    if idx != 10:
      return None

    q = GSoCProfile.all()

    q.filter('scope', self.data.program)
    q.filter('is_student', True)

    starter = lists.keyStarter

    def prefetcher(profiles):
      keys = []

      for profile in profiles:
        key = GSoCProfile.student_info.get_value_for_datastore(profile)
        if key:
          keys.append(key)

      entities = db.get(keys)
      si = dict((i.parent_key(), i) for i in entities if i)

      return ([si], {})

    response_builder = lists.RawQueryContentResponseBuilder(
        self.request, self._list_config, q, starter, prefetcher=prefetcher)

    return response_builder.build()

  def context(self):
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=10)

    return {
        'name': 'students',
        'title': 'PARTICIPATING STUDENTS',
        'lists': [list],
    }


class TodoComponent(Component):
  """Component listing all the Todos for the current user.
  """

  def __init__(self, request, data):
    r = data.redirect
    list_config = lists.ListConfiguration(add_key_column=False)
    list_config.addColumn(
        'key', 'Key', (lambda d, *args: d['key']), hidden=True)
    list_config.addDictColumn('name', 'Name')
    list_config.addDictColumn('status', 'Status')
    def rowAction(d, *args):
      key = d['key']
      if key == 'tax_form':
        return data.redirect.program().urlOf('gsoc_tax_form', secure=True)
      if key == 'enrollment_form':
        return data.redirect.program().urlOf('gsoc_enrollment_form', secure=True)
      if key == 'school_name':
        url = data.redirect.program().urlOf('edit_gsoc_profile')
        return url + '#form_row_school_name'
      if key.isdigit():
        project_id = int(key)
        r.project(id=project_id, student=data.profile.link_id)
        return data.redirect.urlOf('gsoc_update_project')
      return None

    list_config.setRowAction(rowAction)
    self._list_config = list_config

    super(TodoComponent, self).__init__(request, data)

  def templatePath(self):
    return'v2/modules/gsoc/dashboard/list_component.html'

  def getListData(self):
    if lists.getListIndex(self.request) != 11:
      return None

    response = lists.ListContentResponse(self.request, self._list_config)

    if response.start == 'done':
      return response

    info = self.data.student_info

    if self.data.is_student and info.number_of_projects:
      status = colorize(info.tax_form, "Submitted", "Not submitted")
      response.addRow({
          'key': 'tax_form',
          'name': 'Tax form',
          'status': status,
      })

      status = colorize(info.enrollment_form, "Submitted", "Not submitted")
      response.addRow({
          'key': 'enrollment_form',
          'name': 'Enrollment form',
          'status': status,
      })

      matches = info.school_name in UNIVERSITIES.get(info.school_country, [])
      status = colorize(matches, "Yes", "No")
      response.addRow({
          'key': 'school_name',
          'name': 'School name selected from autocomplete',
          'status': status,
      })
      projects = project_logic.getAcceptedProjectsForStudent(self.data.profile)
      for project in projects:
        status = colorize(project.public_info, "Yes", "No")
        response.addRow({
            'key': str(project.key().id()),
            'name': "Set 'additional info' for '%s'" % project.title,
            'status': status
        })

    response.next = 'done'

    return response

  def context(self):
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=11)

    return {
        'name': 'todo',
        'title': 'MY TODOS',
        'lists': [list],
    }
