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

"""Module for the GSoC project student survey."""

from google.appengine.ext import db
from google.appengine.ext import ndb

from django import http
from django.utils.translation import ugettext

from soc.views import survey
from soc.views.helper import lists

from melange.logic import user as user_logic
from melange.request import access
from melange.request import exception

from soc.views.helper.access_checker import isSet
from soc.views.readonly_template import SurveyRecordReadOnlyTemplate

from soc.modules.gsoc.models import project as project_model
from soc.modules.gsoc.models.project_survey import ProjectSurvey
from soc.modules.gsoc.models.project_survey_record import \
    GSoCProjectSurveyRecord
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views import forms as gsoc_forms
from soc.modules.gsoc.views.helper import url_patterns

from summerofcode.request import links


DEF_CANNOT_ACCESS_EVALUATION = ugettext(
    'Organization Administrators can view this evaluation submitted by the '
    'student only after the evaluation deadline. Please visit this page '
    'after the evaluation deadline has passed.')


class GSoCStudentEvaluationEditForm(gsoc_forms.SurveyEditForm):
  """Form to create/edit GSoC project survey for students."""

  class Meta:
    model = ProjectSurvey
    css_prefix = 'gsoc-student-eval-edit'
    exclude = ['program', 'scope', 'author', 'created_by', 'modified_by',
               'survey_content', 'link_id', 'prefix', 'is_featured',
               'read_access', 'write_access', 'taking_access']


class GSoCStudentEvaluationTakeForm(gsoc_forms.SurveyTakeForm):
  """Form for students to respond to the survey during evaluations.
  """

  class Meta:
    model = GSoCProjectSurveyRecord
    css_prefix = 'gsoc-student-eval-record'
    exclude = ['project', 'org', 'user', 'survey', 'created', 'modified']


class GSoCStudentEvaluationEditPage(base.GSoCRequestHandler):
  """View for creating/editing student evalution."""

  def djangoURLPatterns(self):
    return [
         url_patterns.url(r'eval/student/edit/%s$' % url_patterns.SURVEY,
             self, name='gsoc_edit_student_evaluation'),
    ]

  def checkAccess(self, data, check, mutator):
    check.isHost()
    mutator.studentEvaluationFromKwargs(raise_not_found=False)

  def templatePath(self):
    return 'modules/gsoc/_evaluation.html'

  def context(self, data, check, mutator):
    if data.student_evaluation:
      form = GSoCStudentEvaluationEditForm(
          data=data.POST or None, instance=data.student_evaluation)
    else:
      form = GSoCStudentEvaluationEditForm(data=data.POST or None)

    page_name = ugettext('Edit - %s' % (data.student_evaluation.title)) \
        if data.student_evaluation else 'Create new student evaluation'

    survey_key = db.Key.from_path(
        ProjectSurvey.kind(), '%s/%s' % (
            data.program.key().name(), data.kwargs['survey']))
    context = {
        'page_name': page_name,
        'post_url': links.SOC_LINKER.survey(
            survey_key, 'gsoc_edit_student_evaluation'),
        'forms': [form],
        'error': bool(form.errors),
        }

    return context

  def evaluationFromForm(self, data):
    """Create/edit the student evaluation entity from form.

    Args:
      data: A RequestData describing the current request.

    Returns:
      a newly created or updated student evaluation entity or None.
    """
    if data.student_evaluation:
      form = GSoCStudentEvaluationEditForm(
          data=data.POST, instance=data.student_evaluation)
    else:
      form = GSoCStudentEvaluationEditForm(data=data.POST)

    if not form.is_valid():
      return None

    form.cleaned_data['modified_by'] = data.ndb_user.key.to_old_key()

    if not data.student_evaluation:
      form.cleaned_data['link_id'] = data.kwargs.get('survey')
      form.cleaned_data['prefix'] = 'gsoc_program'
      form.cleaned_data['author'] = data.ndb_user.key.to_old_key()
      form.cleaned_data['scope'] = data.program
      # kwargs which defines an evaluation
      fields = ['sponsor', 'program', 'survey']

      key_name = '/'.join(['gsoc_program'] +
                          [data.kwargs[field] for field in fields])

      entity = form.create(commit=True, key_name=key_name)
    else:
      entity = form.save(commit=True)

    return entity

  def post(self, data, check, mutator):
    evaluation = self.evaluationFromForm(data)
    if evaluation:
      # TODO(nathaniel): Redirection to self?
      survey_key = db.Key.from_path(
          ProjectSurvey.kind(), '%s/%s' % (
              data.program.key().name(), data.kwargs['survey']))
      url = links.SOC_LINKER.survey(survey_key, 'gsoc_edit_student_evaluation')

      # TODO(daniel): append 'validated=True' to the URL in a more elegant way.
      return http.HttpResponseRedirect(url + '?validated')
    else:
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)


class GSoCStudentEvaluationTakePage(base.GSoCRequestHandler):
  """View for students to submit their evaluation."""

  def djangoURLPatterns(self):
    return [
         url_patterns.url(r'eval/student/%s$' % url_patterns.SURVEY_RECORD,
             self, name='gsoc_take_student_evaluation'),
    ]

  def checkAccess(self, data, check, mutator):
    mutator.studentEvaluationFromKwargs()
    mutator.studentEvaluationRecordFromKwargs()

    assert isSet(data.student_evaluation)

    if user_logic.isHostForProgram(data.ndb_user, data.program.key()):
      return

    show_url = data.redirect.survey_record(
          data.student_evaluation.link_id).urlOf(
          'gsoc_show_student_evaluation')
    check.isStudentSurveyActive(
        data.student_evaluation, data.url_ndb_profile, show_url=show_url)

    check.isProfileActive()
    # TODO(dcrodman): When GSoCProject is converted to NDB, this Key
    # conversion will need to be removed.
    org_key = project_model.GSoCProject.org.get_value_for_datastore(
        data.url_project)
    org_key = ndb.Key.from_old_key(org_key)

    if data.orgAdminFor(org_key):
      raise exception.Redirect(show_url)

    check.canUserTakeSurvey(data.student_evaluation, 'student')
    check.isStudentForSurvey()

  def templatePath(self):
    return 'modules/gsoc/_evaluation_take.html'

  def context(self, data, check, mutator):
    if data.student_evaluation_record:
      form = GSoCStudentEvaluationTakeForm(
          survey=data.student_evaluation, data=data.POST or None,
          instance=data.student_evaluation_record)
    else:
      form = GSoCStudentEvaluationTakeForm(
          survey=data.student_evaluation, data=data.POST or None)

    context = {
        'page_name': '%s' % data.student_evaluation.title,
        'description': data.student_evaluation.content,
        'project': data.url_project.title,
        'forms': [form],
        'error': bool(form.errors),
        }

    return context

  def recordEvaluationFromForm(self, data):
    """Create/edit a new student evaluation record based on the form input.

    Args:
      data: A RequestData describing the current request.

    Returns:
      a newly created or updated evaluation record entity or None
    """
    if data.student_evaluation_record:
      form = GSoCStudentEvaluationTakeForm(
          survey=data.student_evaluation, data=data.POST,
          instance=data.student_evaluation_record)
    else:
      form = GSoCStudentEvaluationTakeForm(
          survey=data.student_evaluation, data=data.POST)

    if not form.is_valid():
      return None

    if not data.student_evaluation_record:
      org_key = project_model.GSoCProject.org.get_value_for_datastore(
          data.url_project)
      form.cleaned_data['project'] = data.url_project
      form.cleaned_data['org'] = org_key
      form.cleaned_data['user'] = data.ndb_user.key.to_old_key()
      form.cleaned_data['survey'] = data.student_evaluation
      entity = form.create(commit=True)
    else:
      entity = form.save(commit=True)

    return entity

  def post(self, data, check, mutator):
    student_evaluation_record = self.recordEvaluationFromForm(data)
    if student_evaluation_record:
      data.redirect.survey_record(data.student_evaluation.link_id)
      return data.redirect.to('gsoc_take_student_evaluation', validated=True)
    else:
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)


class GSoCStudentEvaluationPreviewPage(base.GSoCRequestHandler):
  """View for the host to preview the evaluation."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
         url_patterns.url(
             r'eval/student/preview/%s$' % url_patterns.SURVEY,
             self, name='gsoc_preview_student_evaluation'),
    ]

  def templatePath(self):
    return 'modules/gsoc/_evaluation_take.html'

  def context(self, data, check, mutator):
    mutator.studentEvaluationFromKwargs()

    form = GSoCStudentEvaluationTakeForm(survey=data.student_evaluation)

    context = {
        'page_name': '%s' % data.student_evaluation.title,
        'description': data.student_evaluation.content,
        'project': "The Project Title",
        'forms': [form],
        'error': bool(form.errors),
        }

    return context


class GSoCStudentEvaluationRecordsList(base.GSoCRequestHandler):
  """View for listing all records of a GSoCGProjectSurveyRecord."""

  def djangoURLPatterns(self):
    return [
         url_patterns.url(
             r'eval/student/records/%s$' % url_patterns.SURVEY,
             self, name='gsoc_list_student_eval_records')
         ]

  def checkAccess(self, data, check, mutator):
    """Defines access checks for this list, all hosts should be able to see it.
    """
    check.isHost()
    mutator.studentEvaluationFromKwargs()

  def context(self, data, check, mutator):
    """Returns the context of the page to render."""
    record_list = self._createSurveyRecordList(data)

    page_name = ugettext('Records - %s' % (data.student_evaluation.title))
    context = {
        'page_name': page_name,
        'record_list': record_list,
        }
    return context

  def jsonContext(self, data, check, mutator):
    """Handler for JSON requests."""
    idx = lists.getListIndex(data.request)
    if idx == 0:
      record_list = self._createSurveyRecordList(data)
      return record_list.listContentResponse(
          data.request, prefetch=['org', 'project']).content()
    else:
      # TODO(nathaniel): This smells like it is missing a return statement.
      super(GSoCStudentEvaluationRecordsList, self).jsonContext(
          data, check, mutator)

  def _createSurveyRecordList(self, data):
    """Creates a SurveyRecordList for the requested survey."""
    record_list = survey.SurveyRecordList(
        data, data.student_evaluation, GSoCProjectSurveyRecord, idx=0)

    def getOrganization(entity, *args):
      """Helper function to get value of organization column."""
      org_key = GSoCProjectSurveyRecord.org.get_value_for_datastore(entity)
      return ndb.Key.from_old_key(org_key).get().name

    record_list.list_config.addPlainTextColumn(
        'project', 'Project', lambda ent, *args: ent.project.title)
    record_list.list_config.addPlainTextColumn(
        'org', 'Organization', getOrganization)

    return record_list

  def templatePath(self):
    return 'modules/gsoc/student_eval/record_list.html'


class GSoCStudentEvaluationReadOnlyTemplate(SurveyRecordReadOnlyTemplate):
  """Template to construct readonly student evaluation record."""

  class Meta:
    model = GSoCProjectSurveyRecord
    css_prefix = 'gsoc-student-eval-show'
    survey_name = 'Student Evaluation'


class GSoCStudentEvaluationShowPage(base.GSoCRequestHandler):
  """View to display the readonly page for student evaluation.
  """

  def djangoURLPatterns(self):
    return [
        url_patterns.url(r'eval/student/show/%s$' % url_patterns.SURVEY_RECORD,
            self, name='gsoc_show_student_evaluation'),
    ]

  def checkAccess(self, data, check, mutator):
    mutator.studentEvaluationFromKwargs()
    mutator.studentEvaluationRecordFromKwargs()

    assert isSet(data.student_evaluation)

    check.isProfileActive()
    old_entity = project_model.GSoCProject.org.get_value_for_datastore(
        data.url_project)
    org_key = ndb.Key.from_old_key(old_entity)
    if data.orgAdminFor(org_key):
      data.role = 'org_admin'
      if data.timeline.afterSurveyEnd(data.student_evaluation):
        return
      else:
        raise exception.Forbidden(message=DEF_CANNOT_ACCESS_EVALUATION)

    check.isStudentForSurvey()
    data.role = 'student'

  def templatePath(self):
    return 'modules/gsoc/_survey/show.html'

  def context(self, data, check, mutator):
    assert isSet(data.program)
    assert isSet(data.timeline)
    assert isSet(data.student_evaluation_record)

    record = data.student_evaluation_record
    student = data.url_ndb_profile

    org_key = project_model.GSoCProject.org.get_value_for_datastore(
        data.url_project)
    org = ndb.Key.from_old_key(org_key).get()

    context = {
        'page_name': 'Student evaluation - %s' % (student.public_name),
        'student': student.public_name,
        'organization': org.name,
        'project': data.url_project.title,
        'css_prefix': GSoCStudentEvaluationReadOnlyTemplate.Meta.css_prefix,
        }

    if record:
      context['record'] = GSoCStudentEvaluationReadOnlyTemplate(record)

    if data.timeline.surveyPeriod(data.student_evaluation):
      if data.role == 'student':
        context['update_link'] = data.redirect.survey_record(
            data.student_evaluation.link_id).urlOf(
            'gsoc_take_student_evaluation')
      else:
        context['submission_msg'] = ugettext(
            'Bug your student to submit the evaluation.')

    return context
