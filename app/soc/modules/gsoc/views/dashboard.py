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

"""Module for the GSoC participant dashboard."""

import json
import logging

from google.appengine.ext import db
from google.appengine.ext import ndb

from django import http
from django.utils.translation import ugettext

from melange.logic import connection as connection_logic
from melange.models import connection as connection_model
from melange.models import profile as profile_model
from melange.request import access
from melange.request import exception
from melange.request import links

from soc.logic import cleaning
from soc.logic import document as document_logic
from soc.logic import org_app as org_app_logic
from soc.models.org_app_record import OrgAppRecord
from soc.models.universities import UNIVERSITIES
from soc.views import base_templates
from soc.views.dashboard import Component
from soc.views.dashboard import Dashboard
from soc.views.helper import lists
from soc.views.helper import url_patterns
from soc.views.helper.surveys import dictForSurveyModel

from soc.modules.gsoc.logic import document as gsoc_document_logic
from soc.modules.gsoc.logic.evaluations import evaluationRowAdder
from soc.modules.gsoc.logic import project as project_logic
from soc.modules.gsoc.logic.proposal import getProposalsToBeAcceptedForOrg
from soc.modules.gsoc.logic.survey_record import getEvalRecord
from soc.modules.gsoc.models.grading_project_survey import GradingProjectSurvey
from soc.modules.gsoc.models.grading_project_survey_record import \
    GSoCGradingProjectSurveyRecord
from soc.modules.gsoc.models.project import GSoCProject
from soc.modules.gsoc.models.project_survey import ProjectSurvey
from soc.modules.gsoc.models.project_survey_record import \
    GSoCProjectSurveyRecord
from soc.modules.gsoc.models.proposal import GSoCProposal
from soc.modules.gsoc.models.proposal_duplicates import GSoCProposalDuplicate
from soc.modules.gsoc.models.score import GSoCScore
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper.url_patterns import url

from summerofcode.logic import survey as survey_logic

BACKLINKS_TO_ADMIN = {'to': 'main', 'title': 'Main dashboard'}

CONNECTION_ROLES = (
  ('No Role|Mentor|Org Admin', 'All'),
  ('No Role', 'No Role'),
  ('Mentor', 'Mentor'),
  ('Org Admin', 'Org Admin'))

def colorize(choice, yes, no):
  """Differentiate between yes and no status with green and red colors."""
  if choice:
    return """<font color="green">%s</font>""" % yes
  else:
    return """<strong><font color="red">%s</font></strong>""" % no


class MainDashboard(Dashboard):
  """Main dashboard that shows all component dashboard icons."""

  def __init__(self, data):
    """Initializes the dashboard.

    Args:
      data: The RequestData object
    """
    super(MainDashboard, self).__init__(data)
    self.subpages = []

  def context(self):
    """Returns the context of main dashboard.
    """
    return {
        'title': BACKLINKS_TO_ADMIN['title'],
        'name': 'main',
        'subpages': self._divideSubPages(self.subpages),
        'enabled': True
    }

  def addSubpages(self, subpage):
    self.subpages.append(subpage)


class ComponentsDashboard(Dashboard):
  """Dashboard that holds component list."""

  def __init__(self, data, component_property):
    """Initializes the dashboard.

    Args:
      data: The RequestData object
      component_property: Component property
    """
    super(ComponentsDashboard, self).__init__(data)
    self.name = component_property.get('name')
    self.title = component_property.get('title')
    self.components = [component_property.get('component'),]
    self.backlinks = [component_property.get('backlinks'),]

  def context(self):
    """Returns the context of components dashboard."""
    return {
        'title': self.title,
        'name': self.name,
        'backlinks': self.backlinks,
        'components': self.components,
    }


class DashboardPage(base.GSoCRequestHandler):
  """View for the participant dashboard."""

  access_checker = access.HAS_PROFILE_ACCESS_CHECKER

  def djangoURLPatterns(self):
    """The URL pattern for the dashboard."""
    return [
        url(r'dashboard/%s$' % url_patterns.PROGRAM, self,
            name='gsoc_dashboard')]

  def templatePath(self):
    """Returns the path to the template."""
    return 'modules/gsoc/dashboard/base.html'

  def jsonContext(self, data, check, mutator):
    """Handler for JSON requests."""
    for component in self.components(data):
      list_content = component.getListData()
      if list_content:
        return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def post(self, data, check, mutator):
    """Handler for POST requests."""
    for component in self.components(data):
      if component.post():
        return http.HttpResponse()
    else:
      raise exception.Forbidden(message='You cannot change this data')

  def context(self, data, check, mutator):
    """Handler for default HTTP GET request."""
    # dashboard container, will hold each component list
    dashboards = []

    # main container that contains all component list
    main = MainDashboard(data)

    # retrieve active component(s) for currently logged-in user
    components = self.components(data)

    # add components as children of main dashboard and treat the component
    # as dashboard element
    for component in components:
      c = {
          'name': component.context().get('name'),
          'description': component.context().get('description'),
          'title': component.context().get('title'),
          'component_link': True,
          }
      main.addSubpages(c)

      dashboards.append(ComponentsDashboard(data, {
          'name': component.context().get('name'),
          'title': component.context().get('title'),
          'component': component,
          'backlinks': BACKLINKS_TO_ADMIN,
          }))

    dashboards.append(main)

    return {
        'page_name': data.program.name,
        'user_name': data.ndb_profile.public_name,
        'program_select': base_templates.DefaultProgramSelect(
            data, 'gsoc_dashboard'),
    # TODO(ljvderijk): Implement code for setting dashboard messages.
    #   'alert_msg': 'Default <strong>alert</strong> goes here',
        'dashboards': dashboards,
    }

  def components(self, data):
    """Returns the components that are active on the page."""
    components = []

    if data.ndb_profile.is_student:
      components += self._getStudentComponents(data)
    elif data.ndb_profile.is_mentor:
      components.append(TodoComponent(data))
      components += self._getOrgMemberComponents(data)
    else:
      components += self._getLoneUserComponents(data)

    return components

  def _getStudentComponents(self, data):
    """Get the dashboard components for a student."""
    components = []

    components.append(DocumentComponent(data))

    if (data.ndb_profile.is_student 
        and data.ndb_profile.student_data.number_of_projects):
      components.append(TodoComponent(data))
      # Add a component to show the evaluations
      evals = dictForSurveyModel(
          ProjectSurvey, data.program, ['midterm', 'final'])
      any_survey_active = any(
          survey_logic.isSurveyActive(
              evaluation, data.ndb_profile.key.to_old_key())
              for evaluation in evals.values())
      if any_survey_active:
        components.append(MyEvaluationsComponent(data, evals))

      # Add a component to show all the projects
      components.append(MyProjectsComponent(data))

    # Add all the proposals of this current user
    components.append(MyProposalsComponent(data))

    return components

  def _getOrgMemberComponents(self, data):
    """Get the dashboard components for Organization members."""
    components = []

    components.append(DocumentComponent(data))

    component = self._getMyOrgApplicationsComponent(data)
    if component:
      components.append(component)

    components.append(UserConnectionComponent(data))
    evals = dictForSurveyModel(GradingProjectSurvey, data.program,
                               ['midterm', 'final'])

    if evals and data.timeline.afterFirstSurveyStart(evals.values()):
      components.append(OrgEvaluationsComponent(data, evals))

    if data.ndb_profile.is_mentor:
      if data.timeline.studentsAnnounced():
        # add a component to show all projects a user is mentoring
        components.append(ProjectsIMentorComponent(data))

    orgs = OrganizationsIParticipateInComponent(data)

    # move to the top during student signup
    if data.timeline.studentSignup():
      components.append(orgs)

    if data.timeline.afterStudentSignupStart():
      # Add the submitted proposals component
      components.append(SubmittedProposalsComponent(data))

    if data.ndb_profile.is_admin:
      # add a component for all organization that this user administers
      components.append(OrgConnectionComponent(data, True))
      components.append(ParticipantsComponent(data))

    # move to the bottom after student signup
    if not data.timeline.studentSignup():
      components.append(orgs)

    if data.ndb_profile.is_admin:
      mentor_evals = dictForSurveyModel(
          GradingProjectSurvey, data.program, ['midterm', 'final'])
      student_evals = dictForSurveyModel(
          ProjectSurvey, data.program, ['midterm', 'final'])
      components.append(MentorEvaluationComponent(data, mentor_evals))
      components.append(StudentEvaluationComponent(data, student_evals))

    return components

  def _getLoneUserComponents(self, data):
    """Get the dashboard components for users without any role.
    """
    components = []

    my_org_applications_component = self._getMyOrgApplicationsComponent(data)
    if my_org_applications_component:
      components.append(my_org_applications_component)

    components.append(UserConnectionComponent(data))

    return components

  def _getMyOrgApplicationsComponent(self, data):
    """Returns MyOrgApplicationsComponent iff this user is main_admin or
    backup_admin in an application.
    """
    survey = org_app_logic.getForProgram(data.program)

    # Test if this user is main admin or backup admin
    q = OrgAppRecord.all()
    q.filter('survey', survey)
    q.filter('main_admin', data.user)

    record = q.get()

    q = OrgAppRecord.all()
    q.filter('survey', survey)
    q.filter('backup_admin', data.user)

    if record or q.get():
      # add a component showing the organization application of the user
      return MyOrgApplicationsComponent(data, survey)
    else:
      return None


class MyOrgApplicationsComponent(Component):
  """Component for listing the Organization Applications of the current user.
  """

  IDX = 0

  def __init__(self, data, survey):
    """Initializes the component.

    Args:
      data: The RequestData object
      survey: the OrgApplicationSurvey entity
    """
    self.data = data
    # passed in so we don't have to do double queries
    self.survey = survey

    list_config = lists.ListConfiguration()

    list_config.addSimpleColumn('name', 'Name')
    list_config.addSimpleColumn('org_id', 'Organization ID')
    list_config.addSimpleColumn('created', 'Created On',
                                column_type=lists.DATE)
    list_config.addSimpleColumn('modified', 'Last Modified On',
                                column_type=lists.DATE)

    if self.data.timeline.surveyPeriod(survey):
      url_name = 'gsoc_retake_org_app'
    else:
      url_name = 'gsoc_show_org_app'

    list_config.setRowAction(
        lambda e, *args: data.redirect.id(e.key().id()).
            urlOf(url_name))

    self._list_config = list_config

    super(MyOrgApplicationsComponent, self).__init__(data)

  def templatePath(self):
    """Returns the path to the template that should be used in render()."""
    return 'modules/gsoc/dashboard/list_component.html'

  def context(self):
    """Returns the context of this component."""
    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=self.IDX, preload_list=False)

    return {
        'name': 'org_app',
        'title': 'My organization applications',
        'lists': [list_configuration_response],
        'description': ugettext('My organization applications'),
        }

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    if lists.getListIndex(self.data.request) != self.IDX:
      return None

    q = OrgAppRecord.all()
    q.filter('survey', self.survey)
    q.filter('main_admin', self.data.user)

    records = q.fetch(1000)

    q = OrgAppRecord.all()
    q.filter('survey', self.survey)
    q.filter('backup_admin', self.data.user)

    records.extend(q.fetch(1000))

    response = lists.ListContentResponse(self.data.request, self._list_config)

    for record in records:
      response.addRow(record)
    response.next = 'done'

    return response


class MyProposalsComponent(Component):
  """Component for listing all the proposals of the current Student.
  """

  DESCRIPTION = ugettext(
      'Click on a proposal in this list to see the comments or update your proposal.')

  def __init__(self, data):
    """Initializes this component."""

    def getOrganization(entity, *args):
      """Helper function to get value of organization column."""
      org_key = GSoCProposal.org.get_value_for_datastore(entity)
      return ndb.Key.from_old_key(org_key).get().name

    list_config = lists.ListConfiguration()
    list_config.addSimpleColumn('title', 'Title')
    list_config.addPlainTextColumn('org', 'Organization', getOrganization)
    list_config.setRowAction(lambda e, *args:
        links.LINKER.userId(
            e.parent_key(), e.key().id(), url_names.PROPOSAL_REVIEW))
    self._list_config = list_config

    super(MyProposalsComponent, self).__init__(data)


  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return'modules/gsoc/dashboard/list_component.html'

  def context(self):
    """Returns the context of this component."""
    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=1,
        description=MyProposalsComponent.DESCRIPTION, preload_list=False)
    return {
        'name': 'proposals',
        'title': 'Proposals',
        'lists': [list_configuration_response],
        'description': ugettext('List of my submitted proposals'),
        }

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    if lists.getListIndex(self.data.request) != 1:
      return None

    q = GSoCProposal.all()
    q.filter('program', self.data.program)
    q.ancestor(self.data.ndb_profile.key.to_old_key())

    starter = lists.keyStarter

    # TODO(daniel): enable prefetching from ndb models
    #prefetcher = lists.ModelPrefetcher(GSoCProposal, ['org'], parent=True)
    #prefetcher = lists.ModelPrefetcher(GSoCProposal, [], parent=True)

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, q, starter,
        prefetcher=None)
    return response_builder.build()


class MyProjectsComponent(Component):
  """Component for listing all the projects of the current Student."""

  def __init__(self, data):
    """Initializes this component."""

    def getOrganization(entity, *args):
      """Helper function to get value of organization column."""
      org_key = GSoCProject.org.get_value_for_datastore(entity)
      return ndb.Key.from_old_key(org_key).get().name

    list_config = lists.ListConfiguration()
    list_config.addSimpleColumn('title', 'Title')
    list_config.addPlainTextColumn('org', 'Organization Name', getOrganization)
    list_config.setRowAction(
        lambda e, *args: links.LINKER.userId(
            e.parent_key(), e.key().id(), url_names.GSOC_PROJECT_DETAILS))
    self._list_config = list_config

    super(MyProjectsComponent, self).__init__(data)

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return'modules/gsoc/dashboard/list_component.html'

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    if lists.getListIndex(self.data.request) != 2:
      return None

    list_query = project_logic.getAcceptedProjectsQuery(
        ancestor=self.data.ndb_profile.key.to_old_key(),
        program=self.data.program)

    starter = lists.keyStarter
    # TODO(daniel): enable prefetching from ndb models
    #prefetcher = lists.ModelPrefetcher(GSoCProject, [], parent=True)

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, list_query,
        starter, prefetcher=None)
    return response_builder.build()

  def context(self):
    """Returns the context of this component."""
    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=2, preload_list=False)
    return {
        'name': 'projects',
        'title': 'Projects',
        'lists': [list_configuration_response],
        'description': ugettext('Projects'),
    }


class MyEvaluationsComponent(Component):
  """Component for listing all the Evaluations of the current Student.
  """

  def __init__(self, data, evals):
    """Initializes this component.

    Args:
      data: The RequestData object containing the entities from the request
      evals: Dictionary containing evaluations for which the list must be built
    """
    self.evals = evals
    self.record = None

    list_config = lists.ListConfiguration(add_key_column=False)

    # key column must be added manually, as it must use evaluation_id
    # which is not part of the project entity
    list_config.addPlainTextColumn(
        'key', 'Key', (lambda entity, evaluation_id, *args: '%s/%s/%s' % (
            evaluation_id, entity.parent_key().name(),
            entity.key().id())), hidden=True)

    list_config.addPlainTextColumn(
        'evaluation', 'Evaluation',
        lambda ent, eval, *args: eval.capitalize() if eval else '')
    list_config.addSimpleColumn('title', 'Project')
    list_config.addHtmlColumn('status', 'Status', self._getStatus)
    list_config.addDateColumn(
        'created', 'Submitted on',
        lambda ent, eval, *args: self.record.created if self.record else None)
    list_config.addDateColumn(
        'modified', 'Last modified on',
        lambda ent, eval, *args: self.record.modified if self.record else None)
    def rowAction(ent, eval, *args):
      return data.redirect.survey_record(
          eval, ent.key().id_or_name(),
          ent.parent_key().parent().name()).urlOf(
              'gsoc_take_student_evaluation')

    list_config.setRowAction(rowAction)
    self._list_config = list_config

    super(MyEvaluationsComponent, self).__init__(data)

  def _getStatus(self, entity, eval, *args):
    eval_ent = self.evals.get(eval)
    self.record = getEvalRecord(GSoCProjectSurveyRecord, eval_ent, entity)
    return colorize(bool(self.record), "Submitted", "Not submitted")

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return'modules/gsoc/dashboard/list_component.html'

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    if lists.getListIndex(self.data.request) != 3:
      return None

    list_query = project_logic.getProjectsQueryForEval(
        ancestor=self.data.ndb_profile.key.to_old_key())

    starter = lists.keyStarter
    # TODO(daniel): enable prefetching from ndb models ('org', 'parent')
    prefetcher = lists.ListModelPrefetcher(
        GSoCProject, [],
        ['failed_evaluations'])
    row_adder = evaluationRowAdder(self.evals)

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, list_query,
        starter, prefetcher=prefetcher, row_adder=row_adder)
    return response_builder.build()

  def context(self):
    """Returns the context of this component."""
    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=3, preload_list=False)

    return {
        'name': 'evaluations',
        'title': 'Evaluations',
        'lists': [list_configuration_response],
        'description': ugettext('Evaluations'),
    }


class OrgEvaluationsComponent(MyEvaluationsComponent):
  """Component for listing all the Evaluations for the mentor.
  """

  def __init__(self, data, evals):
    """Initializes this component.

    Args:
      data: The RequestData object containing the entities from the request
      evals: Dictionary containing evaluations for which the list must be built
    """
    super(OrgEvaluationsComponent, self).__init__(data, evals)

    def getStudent(entity, evaluation, *args):
      """Helper function to get value of student column."""
      return ndb.Key.from_old_key(entity.parent_key()).get().public_name

    self._list_config.addPlainTextColumn('student', 'Student', getStudent)

    def rowAction(ent, eval, *args):
      eval_ent = eval
      return data.redirect.survey_record(
          eval_ent, ent.key().id_or_name(),
          ent.parent_key().parent().name()).urlOf(
              'gsoc_take_mentor_evaluation')

    self._list_config.setRowAction(rowAction)

  def _getStatus(self, entity, eval, *args):
    eval_ent = self.evals.get(eval)
    self.record = getEvalRecord(GSoCGradingProjectSurveyRecord,
                                eval_ent, entity)
    return colorize(bool(self.record), "Submitted", "Not submitted")

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    if lists.getListIndex(self.data.request) != 3:
      return None

    list_query = project_logic.getProjectsQueryForEval(
        mentors=self.data.ndb_profile.key.to_old_key())

    starter = lists.keyStarter
    # TODO(daniel): enable prefetching from ndb models ('orgs')
    prefetcher = lists.ListModelPrefetcher(
        GSoCProject, [],
        ['mentors', 'failed_evaluations'],
        parent=True)
    row_adder = evaluationRowAdder(self.evals)

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, list_query,
        starter, prefetcher=prefetcher, row_adder=row_adder)
    return response_builder.build()

  def context(self):
    """Returns the context of this component."""
    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=3, preload_list=False)

    return {
        'name': 'evaluations',
        'title': 'My Evaluations',
        'lists': [list_configuration_response],
        'description': ugettext('Evaluations that I must complete'),
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

  # TODO(nathaniel): Wait, is this seriously a 100+-line *constructor*?
  def __init__(self, data):
    """Initializes this component."""

    def getStudentEmail(entity, *args):
      """Helper function to get value of Student Email column."""
      return ndb.Key.from_old_key(entity.parent_key()).get().contact.email

    list_config = lists.ListConfiguration()
    list_config.addSimpleColumn('title', 'Title')
    list_config.addPlainTextColumn(
        'email', 'Student Email', getStudentEmail, hidden=True)
    list_config.addNumericalColumn('score', 'Score',
        lambda e, *args: e.score)
    list_config.addNumericalColumn('nr_scores', '#scores',
        lambda e, *args: e.nr_scores, hidden=True)

    def getAverage(ent):
      if not ent.nr_scores:
        return ''

      average = float(ent.score)/float(ent.nr_scores)
      return float("%.2f" % average)

    list_config.addNumericalColumn(
        'average', 'Average', lambda ent, *a: getAverage(ent))

    query = db.Query(GSoCScore)
    query.filter('author', data.ndb_profile.key.to_old_key())
    myScores = dict((q.parent_key(), q.value) for q in query.fetch(1000))
    def getMyScore(ent, *args):
      return myScores.get(ent.key(), '')

    list_config.addNumericalColumn(
        'my_score', 'My score', getMyScore)

    def getStatusOnDashboard(proposal, accepted, duplicates):
      """Method for determining which status to show on the dashboard."""
      # TODO(nathaniel): HTML in Python.
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
        # TODO(nathaniel): This structured data deserves first-class representation
        # in Python rather than this stringly typed... stuff.
        ('(pending|accepted|rejected|duplicate|mentor)', 'Valid'),
        ('(duplicate|mentor)', 'Needs attention'),
        ('(duplicate)', 'Duplicate'),
        ('(accepted)', 'Accepted'),
        ('(rejected)', 'Rejected'),
        ('(mentor)', 'No mentor assigned'),
        ('', 'All'),
        ('(invalid|withdrawn|ignored)', 'Invalid'),
    ]
    list_config.addHtmlColumn('status', 'Status', getStatusOnDashboard,
        options=options)

    list_config.addSimpleColumn('last_modified_on', 'Last modified',
                                column_type=lists.DATE)
    list_config.addSimpleColumn('created_on', 'Created on',
                                hidden=True, column_type=lists.DATE)

    def getStudent(entity, *args):
      """Helper function to get value of student column."""
      return ndb.Key.from_old_key(entity.parent_key()).get().public_name

    list_config.addPlainTextColumn('student', 'Student', getStudent)
    list_config.addSimpleColumn('accept_as_project', 'Should accept')

    def getOrganization(entity, *args):
      """Helper function to get value of organization column."""
      org_key = GSoCProposal.org.get_value_for_datastore(entity)
      return ndb.Key.from_old_key(org_key).get().name

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

    def getOrganizationKey(entity, *args):
      """Helper function to get value of organization key column."""
      org_key = GSoCProposal.org.get_value_for_datastore(entity)
      return ndb.Key.from_old_key(org_key).id()

    list_config.addPlainTextColumn(
        'mentor', 'Assigned mentor usernames', mentor_key, hidden=True)
    list_config.addPlainTextColumn(
        'possible_mentors', 'Possible mentor usernames',
        mentor_keys, hidden=True)

    orgs = data.mentor_for
    options = [("^%s$" % i.name, i.name) for i in orgs]


    if options and len(options) > 1:
      options = [('', 'All')] + options

    hidden = len(data.mentor_for) < 2
    list_config.addPlainTextColumn(
        'org', 'Organization', getOrganization, options=options, hidden=hidden)

    # hidden keys
    list_config.addPlainTextColumn(
        'full_proposal_key', 'Full proposal key',
        (lambda ent, *args: str(ent.key())), hidden=True)
    list_config.addPlainTextColumn(
        'org_key', 'Organization key', getOrganizationKey, hidden=True)

    # row action
    list_config.setRowAction(lambda e, *args:
        links.LINKER.userId(
            e.parent_key(), e.key().id(), url_names.PROPOSAL_REVIEW))
    list_config.setDefaultSort('last_modified_on', 'desc')

    # additional columns
    def get_col_prop(column):
      def getter(ent, *args):
        if not ent.extra:
          return ""
        extra = json.loads(ent.extra)
        return extra.get(column, "")
      return getter

    extra_columns = []
    for org in data.mentor_for:
      # TODO(daniel): add proposal_extra to Organization model??
      if not hasattr(org, 'proposal_extra'):
        continue

      for column in org.proposal_extra:
        extra_columns.append(column)
        col_name = "%s" % (column)

        list_config.addPlainTextColumn(
            column, col_name, get_col_prop(column))
        list_config.setColumnEditable(column, True, 'text', {})
        list_config.setColumnExtra(column, org="^%s$" % org.short_name)

    self.has_extra_columns = bool(extra_columns)

    if self.has_extra_columns:
      fields = ['full_proposal_key', 'org_key']
      list_config.addPostEditButton('save', "Save", "", fields, refresh="none")

    if data.ndb_profile.is_admin:
      # accept/reject proposals
      bounds = [1,'all']
      keys = ['full_proposal_key']
      list_config.addPostButton('accept', "Accept", "", bounds, keys)
      list_config.addPostButton('unaccept', "Unaccept", "", bounds, keys)

    self._list_config = list_config

    super(SubmittedProposalsComponent, self).__init__(data)

  def templatePath(self):
    return'modules/gsoc/dashboard/list_component.html'

  def context(self):
    description = self.DESCRIPTION

    if self.has_extra_columns:
      description += self.CUSTOM_COLUMNS

    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=4, description=description,
        preload_list=False)
    return {
        'name': 'proposals_submitted',
        'title': 'Proposals submitted to my organizations',
        'lists': [list_configuration_response],
        'description': ugettext(
            'List of proposals submitted to my organizations'),
        }

  def post(self):
    idx = lists.getListIndex(self.data.request)
    if idx != 4:
      return None

    data = self.data.POST.get('data')

    if not data:
      raise exception.BadRequest(message="Missing data")

    parsed = json.loads(data)

    button_id = self.data.POST.get('button_id')

    if not button_id:
      raise exception.BadRequest(message="Missing button_id")

    if button_id == 'save':
      return self.postSave(parsed)

    if button_id == 'accept':
      return self.postAccept(parsed, True)

    if button_id == 'unaccept':
      return self.postAccept(parsed, False)

    raise exception.BadRequest(message="Unknown button_id")

  def postSave(self, parsed):
    extra_columns = {}

    for org in self.data.mentor_for:
      for column in org.proposal_extra:
        extra_columns.setdefault(org.key.id(), []).append(column)

    for _, properties in parsed.iteritems():
      if 'org_key' not in properties or 'full_proposal_key' not in properties:
        logging.warning("Missing key in '%s'", properties)
        continue

      org_key_name = properties.pop('org_key')
      proposal_key = properties.pop('full_proposal_key')

      valid_columns = set(extra_columns.get(org_key_name, []))
      remove_properties = []

      for key, value in properties.iteritems():
        if key not in valid_columns:
          logging.warning("Invalid property '%s'", key)
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
          logging.warning("Invalid proposal_key '%s'", proposal_key)
          return

        data = {}

        if proposal.extra:
          # we have to loads in the txn, should be fast enough
          data = json.loads(proposal.extra)

        data.update(properties)

        proposal.extra = json.dumps(data)
        proposal.put()

      db.run_in_transaction(update_proposal_txn)

    return True

  def postAccept(self, data, accept):
    for properties in data:
      if 'full_proposal_key' not in properties:
        logging.warning("Missing key in '%s'", properties)
        continue
      proposal_key = properties['full_proposal_key']
      def accept_proposal_txn():
        proposal = db.get(db.Key(proposal_key))

        if not proposal:
          logging.warning("Invalid proposal_key '%s'", proposal_key)
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
    idx = lists.getListIndex(self.data.request)
    if idx != 4:
      return None

    # Hold all the accepted projects for orgs where this user is a member of
    accepted = []
    # Hold all duplicates for either the entire program or the orgs of the user.
    duplicates = []
    dupQ = GSoCProposalDuplicate.all()
    dupQ.filter('is_duplicate', True)

    query = GSoCProposal.all()
    query.filter(
        'org IN',
        map(lambda key: key.to_old_key(), self.data.ndb_profile.mentor_for))
    dupQ.filter(
        'orgs IN',
        map(lambda key: key.to_old_key(), self.data.ndb_profile.mentor_for))

    # Only fetch the data if we will display it
    if self.data.program.duplicates_visible:
      for org in self.data.mentor_for:
        accepted.extend([p.key() for p in getProposalsToBeAcceptedForOrg(org)])


    # Only fetch the data if it is going to be displayed
    if self.data.program.duplicates_visible:
      duplicate_entities = dupQ.fetch(1000)
      for dup in duplicate_entities:
        duplicates.extend(dup.duplicates)

    starter = lists.keyStarter
    # TODO(daniel): enable prefetching from ndb models ('org', 'parent')
    #prefetcher = lists.ModelPrefetcher(GSoCProposal, [], parent=True)

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, query, starter,
        prefetcher=None)
    return response_builder.build(accepted, duplicates)


class ProjectsIMentorComponent(Component):
  """Component for listing all the Projects mentored by the current user."""

  def __init__(self, data):
    """Initializes this component."""

    def getOrganization(entity, *args):
      """Helper function to get value of organization column."""
      org_key = GSoCProject.org.get_value_for_datastore(entity)
      return ndb.Key.from_old_key(org_key).get().name

    list_config = lists.ListConfiguration()
    list_config.addSimpleColumn('title', 'Title')

    def getStudent(entity, *args):
      """Helper function to get value of student column."""
      return ndb.Key.from_old_key(entity.parent_key()).get().public_name

    list_config.addPlainTextColumn('student', 'Student', getStudent)
    list_config.addPlainTextColumn('org', 'Organization', getOrganization)
    list_config.setDefaultSort('title')
    list_config.setRowAction(
        lambda e, *args: links.LINKER.userId(
            e.parent_key(), e.key().id(), url_names.GSOC_PROJECT_DETAILS))
    self._list_config = list_config

    super(ProjectsIMentorComponent, self).__init__(data)

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return'modules/gsoc/dashboard/list_component.html'

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    if lists.getListIndex(self.data.request) != 5:
      return None

    list_query = project_logic.getAcceptedProjectsQuery(
        program=self.data.program)

    if self.data.ndb_profile.is_admin:
      list_query.filter(
          'org IN',
          map(lambda key: key.to_old_key(), self.data.ndb_profile.admin_for))
    else:
      list_query.filter('mentors', self.data.ndb_profile.key.to_old_key())

    starter = lists.keyStarter
    # TODO(daniel): enable prefetching from ndb models ('org')
    prefetcher = lists.ModelPrefetcher(GSoCProject, [], parent=True)

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, list_query,
        starter, prefetcher=prefetcher)
    return response_builder.build()

  def context(self):
    """Returns the context of this component."""
    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=5)

    if self.data.ndb_profile.is_admin:
      title = 'Projects for my orgs'
    else:
      title = 'Projects I am a mentor for'

    return {
        'name': 'mentoring_projects',
        'title': title,
        'lists': [list_configuration_response],
        'description': ugettext(title),
    }


class OrganizationsIParticipateInComponent(Component):
  """Component listing all the Organizations the current user participates in.
  """

  def __init__(self, data):
    """Initializes this component."""
    list_config = lists.ListConfiguration()
    list_config.setRowAction(
        lambda e, *args:
            links.LINKER.organization(e.key, url_names.GSOC_ORG_HOME))

    if not data.program.allocations_visible:
      list_config.addSimpleColumn('name', 'name')
    else:
      def c(ent, s, text):
        if ent.slot_allocation - s == 0:
          return text
        return """<strong><font color="red">%s</font></strong>""" % text

      list_config.addSimpleColumn('link_id', 'Organization ID', hidden=True)
      list_config.addHtmlColumn(
          'name', 'name', lambda ent, s, *args: c(ent, s, ent.name))
      list_config.addSimpleColumn('slots', 'Slots allowed')
      list_config.addNumericalColumn(
          'slots_used', 'Slots used', lambda ent, s, *args: s)
      list_config.addHtmlColumn(
          'delta', 'Slots difference',
          lambda ent, s, *args: c(ent, s, (ent.slot_allocation - s)))
      list_config.addNumericalColumn(
          'delta_sortable', 'Slots difference (sortable)',
          (lambda ent, s, *args: abs(ent.slot_allocation - s)), hidden=True)

    list_config.setDefaultSort('name')
    self._list_config = list_config

    super(OrganizationsIParticipateInComponent, self).__init__(data)

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return'modules/gsoc/dashboard/list_component.html'

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    if lists.getListIndex(self.data.request) != 6:
      return None

    response = lists.ListContentResponse(self.data.request, self._list_config)

    if response.start == 'done' or (
        response.start and not response.start.isdigit()):
      return response

    pos = int(response.start) if response.start else 0

    orgs = self.data.mentor_for

    if pos < len(orgs):
      org = orgs[pos]
      used_slots = self._getUsedSlots(org)
      response.addRow(org, used_slots)

    if (pos + 1) < len(orgs):
      response.next = str(pos + 1)
    else:
      response.next = 'done'

    return response

  def context(self):
    """Returns the context of this component."""
    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=6, preload_list=False)

    return {
        'name': 'adminning_organizations',
        'title': 'My organizations',
        'lists': [list_configuration_response],
        'description': ugettext(
            'List of organizations which I participate in'),
    }

  def _getUsedSlots(self, org):
    """Returns number of slots which were used by the specified organization.

    The meaning of the returned integer differs between various points in
    program's timeline.

    Before student proposals are transformed into projects, the number is
    defined as number of proposals which are going to be accepted. After that,
    the number represents the number of proposals which were accepted for the
    specified organization.

    Args:
      org: organization entity.

    Returns:
      number of slots used by the organization
    """
    if self.data.timeline.studentsAnnounced():
      query = db.Query(GSoCProposal, keys_only=True)
      query.filter('org', org.key.to_old_key())
      query.filter('status', 'accepted')
      return query.count()
    else:
      query = db.Query(GSoCProposal, keys_only=True)
      query.filter('org', org.key.to_old_key())
      query.filter('has_mentor', True).filter('accept_as_project', True)
      return query.count()


class OrgConnectionComponent(Component):
  """Component for listing all the connections for orgs of which the user is an
  admin.
  """

  IDX = 7

  def __init__(self, data, for_admin):
    """Initializes this component.
    """
    self.data = data
    list_config = lists.ListConfiguration()

    def getOrganization(entity, *args):
      """Helper function to get value of organization column."""
      org_key = (connection_model.Connection.organization
          .get_value_for_datastore(entity))
      return ndb.Key.from_old_key(org_key).get().name

    def getStudent(entity, *args):
      """Helper function to get value of student column."""
      return ndb.Key.from_old_key(entity.parent_key()).get().public_name

    list_config.addPlainTextColumn(
        'organization', 'Organization', getOrganization)
    list_config.addPlainTextColumn('name', 'Name', getStudent)
    list_config.addPlainTextColumn('role', 'Role',
        lambda e, *args: connection_model.VERBOSE_ROLE_NAMES[e.getRole()],
            options=CONNECTION_ROLES)

    list_config.setRowAction(
        lambda e, *args: data.redirect.show_org_connection(connection=e).url())
    self._list_config = list_config

    super(OrgConnectionComponent, self).__init__(data)

  def templatePath(self):
    return'modules/gsoc/dashboard/list_component.html'

  def getListData(self):
    """Generates a list of data for the table in this component.

    See getListData() method of soc.views.dashboard.Component for more details.

    Returns:
        The list data as requested by the current request. Returns None if there is
        no data to be shown or the request is not for this component's index (IDX).
    """

    if lists.getListIndex(self.data.request) != self.IDX:
      return None

    query = connection_logic.queryForOrganizations(
        self.data.ndb_profile.admin_for)

    starter = lists.keyStarter

    # TODO(daniel): enable prefetching from ndb models
    #prefetcher = lists.ModelPrefetcher(
    #    connection_model.Connection, ['organization'])

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, query, starter, prefetcher=None)
    return response_builder.build()

  def context(self):
    """Returns the context of this component.
    """
    my_list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=7, preload_list=False)

    title = 'Connections for my organizations'
    description = ugettext(
        'List of connections with mentors and admins for my organization.')

    return {
        'name': 'org_connections',
        'title': title,
        'lists': [my_list],
        'description': description
    }


class UserConnectionComponent(Component):
  """Component for listing all the connections for the current user.
  """

  IDX = 8

  def __init__(self, data):
    """Initializes this component.
    """
    def getOrganization(entity, *args):
      """Helper function to get value of organization column."""
      org_key = (connection_model.Connection.organization
          .get_value_for_datastore(entity))
      return ndb.Key.from_old_key(org_key).get().name

    def getStudent(entity, *args):
      """Helper function to get value of student column."""
      return ndb.Key.from_old_key(entity.parent_key()).get().public_name

    list_config = lists.ListConfiguration(add_key_column=False)
    list_config.addPlainTextColumn('key', 'Key',
        lambda e, *args: '%s' % e.keyName(), hidden=True)
    list_config.addPlainTextColumn(
        'organization', 'Organization', getOrganization)
    list_config.addPlainTextColumn('name', 'Name', getStudent)
    list_config.addPlainTextColumn('role', 'Role',
        lambda e, *args: connection_model.VERBOSE_ROLE_NAMES[e.getRole()],
            options=CONNECTION_ROLES)

    list_config.setRowAction(
        lambda e, *args: data.redirect.show_user_connection(
        connection=e).url())
    self._list_config = list_config

    super(UserConnectionComponent, self).__init__(data)

  def templatePath(self):
    return'modules/gsoc/dashboard/list_component.html'

  def getListData(self):
    """Generates a list of data for the table in this component.

    See getListData() method of soc.views.dashboard.Component for more details.

    Returns:
        The list data as requested by the current request. Returns None if there is
        no data to be shown or the request is not for this component's index (IDX).
    """
    if lists.getListIndex(self.data.request) != self.IDX:
      return None

    q = connection_logic.queryForAncestor(self.data.ndb_profile.key)

    starter = lists.keyStarter

    # TODO(daniel): enable prefetching from ndb models
    #prefetcher = lists.ModelPrefetcher(
    #    connection_model.Connection, ['organization'])

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, q, starter,
        prefetcher=None)
    return response_builder.build()

  def context(self):
    """Returns the context of this component.
    """
    my_list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=self.IDX, preload_list=False)

    title = 'My connections'
    description = ugettext('List of my connections with organizations.')

    return {
        'name': 'connections',
        'title': title,
        'lists': [my_list],
        'description': description
    }


class ParticipantsComponent(Component):
  """Component for listing all the participants for all organizations."""

  class AdministeredOrgsPrefetcher(lists.Prefetcher):
    """A simple lists.Prefetcher implementation which prefetches organizations
    for which the current user is an administrator.

    It is used in case the component is created for organization administrator.
    Only memebers belonging to one of his or her organizations will be listed.
    Therefore, organization entities, which have already been retrieved
    and are stored in base.RequestData object, can be reused.

    One of the regular lists.Prefetcher implementations could be used for the
    same purpose, but since entities are already present, there is no need
    to contact the database, so a few round trips are saved.

    See lists.Prefetcher for specification.
    """

    def __init__(self, data):
      """Initializes instances of this class.

      Args:
        data: A RequestData describing the current request.
      """
      self.org_dict = dict((org.key, org) for org in data.org_admin_for)

    def prefetch(self, entities):
      """Prefetches the organizations that are administered by the current
      user.

      Args:
        entities: list of profile entities (not actually used)

      Returns:
        Prefetched organization entities in a structure whose format is
        described in lists.Prefetcher.prefetch

      See lists.Prefetcher.prefetch for specification.
      """
      return [self.org_dict], {}

  def __init__(self, data):
    """Initializes this component.
    """
    self.data = data
    list_config = lists.ListConfiguration()
    list_config.addPlainTextColumn(
        'name', 'Name', lambda ent, *args: ent.name())
    list_config.addSimpleColumn('email', "Email")

    get = lambda i, orgs: orgs[i].name

    list_config.addPlainTextColumn(
        'mentor_for', 'Mentor for',
        lambda ent, orgs, *args: ', '.join(
            [get(i, orgs) for i in ent.mentor_for if data.orgAdminFor(i)]))
    list_config.addPlainTextColumn(
        'admin_for', 'Organization admin for',
        lambda ent, orgs, *args: ', '.join(
            [get(i, orgs) for i in ent.org_admin_for if data.orgAdminFor(i)]))

    self._list_config = list_config

    super(ParticipantsComponent, self).__init__(data)

  def templatePath(self):
    return'modules/gsoc/dashboard/list_component.html'

  def getListData(self):
    idx = lists.getListIndex(self.data.request)

    # TODO(nathaniel): Magic number. What does this 9 really mean?
    if idx != 9:
      return None

    query = self.data.ndb_profile_model.query(
        profile_model.Profile.mentor_for.IN(self.data.ndb_profile.admin_for))
    prefetcher = ParticipantsComponent.AdministeredOrgsPrefetcher(self.data)

    starter = lists.keyStarter

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, query, starter,
        prefetcher=prefetcher)
    return response_builder.build()

  def context(self):
    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=9, preload_list=False)

    return {
        'name': 'participants',
        'title': 'Members of my organizations',
        'lists': [list_configuration_response],
        'description': ugettext(
            'List of your organizations members'),
    }


class TodoComponent(Component):
  """Component listing all the Todos for the current user.
  """

  def __init__(self, data):
    list_config = lists.ListConfiguration(add_key_column=False)
    list_config.addPlainTextColumn(
        'key', 'Key', (lambda d, *args: d['key']), hidden=True)
    list_config.addDictColumn('name', 'Name')
    list_config.addDictColumn('status', 'Status', column_type=lists.HTML)
    def rowAction(d, *args):
      key = d['key']
      if key == 'tax_form':
        data.redirect.program()
        return data.redirect.urlOf('gsoc_tax_form', secure=True)
      if key == 'enrollment_form':
        data.redirect.program()
        return data.redirect.urlOf('gsoc_enrollment_form', secure=True)
      if key == 'school_name':
        data.redirect.program()
        url = data.redirect.urlOf(url_names.GSOC_PROFILE_EDIT, secure=True)
        return url + '#form_row_school_name'
      if key.isdigit(): # provided key represents a project ID
        return links.LINKER.userId(
            data.ndb_profile.key.to_old_key(), int(key),
            url_names.GSOC_PROJECT_UPDATE)
      return None

    list_config.setRowAction(rowAction)
    self._list_config = list_config

    super(TodoComponent, self).__init__(data)

  def templatePath(self):
    return'modules/gsoc/dashboard/list_component.html'

  def getListData(self):
    # TODO(nathaniel): Magic number.
    if lists.getListIndex(self.data.request) != 11:
      return None

    response = lists.ListContentResponse(self.data.request, self._list_config)

    if response.start == 'done':
      return response

    info = self.data.student_info

    isgood = lambda x: x and x.size and x.filename

    if self.data.is_student and info.number_of_projects:
      if self.data.timeline.afterFormSubmissionStart():
        status = colorize(isgood(info.tax_form), "Submitted", "Not submitted")
        response.addRow({
            'key': 'tax_form',
            'name': 'Tax form',
            'status': status,
        })

        status = colorize(
            isgood(info.enrollment_form), "Submitted", "Not submitted")
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
      projects = project_logic.getAcceptedProjectsForStudent(
          self.data.ndb_profile.key.to_old_key())
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
    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=11, preload_list=False)

    return {
        'name': 'todo',
        'title': 'My todos',
        'lists': [list_configuration_response],
        'description': ugettext('List of my todos'),
    }


class StudentEvaluationComponent(Component):
  """Component for listing student evaluations for organizations.
  """

  IDX = 12

  # TODO(nathaniel): This __init__ doesn't make a super call like
  # all other subclasses of Component do. What's up with that?
  def __init__(self, data, evals):
    """Initializes this component.

    Args:
      data: The RequestData object containing the entities from the request
      evals: Dictionary containing evaluations for which the list must be built
      idx: The id for this list component
    """
    self.data = data
    self.evals = evals

    self.record = None

    def getOrganization(entity, evaluation, *args):
      """Helper function to get value of organization column."""
      org_key = GSoCProject.org.get_value_for_datastore(entity)
      return ndb.Key.from_old_key(org_key).get().name

    def getStudent(entity, evaluation, *args):
      """Helper function to get value of student column."""
      return ndb.Key.from_old_key(entity.parent_key()).get().public_name

    list_config = lists.ListConfiguration(add_key_column=False)

    # key column must be added manually, as it must use evaluation_id
    # which is not part of the project entity
    list_config.addPlainTextColumn(
        'key', 'Key', (lambda entity, evaluation_id, *args: "%s/%s/%s" % (
            evaluation_id, entity.parent_key().name(),
            entity.key().id())), hidden=True)

    list_config.addPlainTextColumn(
        'evaluation', 'Evaluation',
        lambda ent, eval, *args: eval.capitalize() if eval else '')
    list_config.addPlainTextColumn('student', 'Student', getStudent)
    list_config.addSimpleColumn('title', 'Project Title')
    list_config.addPlainTextColumn('org', 'Organization', getOrganization)
    list_config.addPlainTextColumn(
        'mentors', 'Mentors',
        lambda ent, eval, mentors, *args: ', '.join(
            [mentors.get(m).name() for m in ent.mentors]))
    list_config.addHtmlColumn(
        'status', 'Status', self._getStatus)
    list_config.addDateColumn(
        'created', 'Submitted on',
        lambda ent, eval, *args: self.record.created if self.record else None)
    list_config.addDateColumn(
        'modified', 'Last modified on',
        lambda ent, eval, *args: self.record.modified if self.record else None)
    list_config.setDefaultSort('student')

    def getRowAction(entity, eval, *args):
      eval_ent = self.evals.get(eval)

      if not self.data.timeline.afterSurveyEnd(eval_ent):
        return ''

      url = self.data.redirect.survey_record(
          eval, entity.key().id_or_name(),
          entity.parent_key().parent().name()).urlOf(
              'gsoc_show_student_evaluation')
      return url
    list_config.setRowAction(getRowAction)

    self._list_config = list_config

  def _getStatus(self, entity, evaluation, *args):
    eval_ent = self.evals.get(evaluation)
    self.record = getEvalRecord(GSoCProjectSurveyRecord, eval_ent, entity)
    return colorize(bool(self.record), "Submitted", "Not submitted")

  def context(self):
    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=self.IDX, preload_list=False)

    return {
        'name': 'student_evaluations',
        'lists': [list_configuration_response],
        'title': 'Student Evaluations',
        'description': ugettext(
          'List of student evaluations for my organizations'),
        'idx': self.IDX,
        }

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    idx = lists.getListIndex(self.data.request)
    if idx == self.IDX:
      list_query = project_logic.getProjectsQueryForEvalForOrgs(
          orgs=self.data.org_admin_for)

      starter = lists.keyStarter
      # TODO(daniel): enable prefetching from ndb models ('org')
      prefetcher = lists.ListModelPrefetcher(
          GSoCProject, [],
          ['mentors', 'failed_evaluations'],
          parent=True)
      row_adder = evaluationRowAdder(self.evals)

      response_builder = lists.RawQueryContentResponseBuilder(
          self.data.request, self._list_config, list_query,
          starter, prefetcher=prefetcher, row_adder=row_adder)
      return response_builder.build()
    else:
      return None

  def templatePath(self):
    return'modules/gsoc/dashboard/list_component.html'


class MentorEvaluationComponent(StudentEvaluationComponent):
  """Component for listing mentor evaluations for organizations."""

  IDX = 13

  def __init__(self, data, evals):
    """Initializes this component.

    Args:
      data: The RequestData object containing the entities from the request
      evals: Dictionary containing evaluations for which the list must be built
      idx: The id for this list component
    """
    super(MentorEvaluationComponent, self).__init__(data, evals)

    self.record = None

    self._list_config.addHtmlColumn(
        'grade', 'Grade', self._getGrade)
    self._list_config.setRowAction(lambda entity, evaluation, *args:
        data.redirect.survey_record(
            evaluation, entity.key().id_or_name(),
            entity.parent_key().parent().name()).urlOf(
                'gsoc_take_mentor_evaluation'))

  def _getStatus(self, entity, evaluation, *args):
    eval_ent = self.evals.get(evaluation)
    self.record = getEvalRecord(GSoCGradingProjectSurveyRecord,
                                eval_ent, entity)
    return colorize(
        bool(self.record), "Submitted", "Not submitted")

  def _getGrade(self, entity, evaluation, *args):
    if self.record:
      return colorize(
        self.record.grade, "Pass", "Fail")
    else:
      return "N/A"

  def context(self):
    context = super(MentorEvaluationComponent, self).context()
    context['title'] = 'Mentor Evaluations'
    context['description'] = ugettext(
        'List of mentor evaluations for my organizations')
    context['name'] = 'mentor_evaluations'
    return context


class DocumentComponent(Component):
  """Component listing all the documents for the current user.
  """

  IDX = 14

  def __init__(self, data):
    """Initializes this component.
    """
    self.data = data
    list_config = lists.ListConfiguration()
    list_config.addPlainTextColumn(
        'title', 'Title', lambda ent, *args: ent.name())

    list_config.setRowAction(
        lambda e, *args: self.data.redirect.document(e).urlOf(
            'show_gsoc_document'))

    self._list_config = list_config

    super(DocumentComponent, self).__init__(data)

  def templatePath(self):
    return'modules/gsoc/dashboard/list_component.html'

  def getListData(self):
    idx = lists.getListIndex(self.data.request)

    if idx != self.IDX:
      return None

    visibilities = gsoc_document_logic.getVisibilities(self.data)
    q = document_logic.getDocumentQueryForRoles(self.data, visibilities)

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, q, lists.keyStarter)
    return response_builder.build()

  def context(self):
    list_config = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=self.IDX, preload_list=False)

    return {
        'name': 'documents',
        'title': 'Important documents',
        'lists': [list_config],
        'description': ugettext('List of important documents'),
    }
