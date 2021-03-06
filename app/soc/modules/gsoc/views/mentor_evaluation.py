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

"""Module for the GSoC project evaluations."""

from google.appengine.ext import db
from google.appengine.ext import ndb

from django import http
from django.utils.translation import ugettext

import django

from melange.request import access

from soc.views import forms
from soc.views import survey
from soc.views.helper import lists
from soc.views.helper.access_checker import isSet
from soc.views.readonly_template import SurveyRecordReadOnlyTemplate

from soc.modules.gsoc.models import project as project_model
from soc.modules.gsoc.models.grading_project_survey import GradingProjectSurvey
from soc.modules.gsoc.models.grading_project_survey_record import \
    GSoCGradingProjectSurveyRecord
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views import forms as gsoc_forms
from soc.modules.gsoc.views.helper import url_patterns

from summerofcode.request import links


EVALUATION_CHOICES = (
    (True, 'Pass'),
    (False, 'Fail')
    )


class GSoCMentorEvaluationEditForm(gsoc_forms.SurveyEditForm):
  """Form to create/edit GSoC evaluation for the organization."""

  class Meta:
    model = GradingProjectSurvey
    css_prefix = 'gsoc-mentor-eval-edit'
    exclude = ['program', 'scope', 'author', 'created_by', 'modified_by',
               'survey_content', 'link_id', 'prefix', 'is_featured',
               'read_access', 'write_access', 'taking_access']

class GSoCMentorEvaluationTakeForm(gsoc_forms.SurveyTakeForm):
  """Form for the organization to evaluate a student project."""

  def __init__(self, survey=survey, **kwargs):
    """Initialize the form field by adding a new grading field.
    """
    super(GSoCMentorEvaluationTakeForm, self).__init__(survey, **kwargs)

    # hack to re-order grade to push to the end of the survey form
    self.fields.keyOrder.remove('grade')
    self.fields.keyOrder.append('grade')

    self.fields['grade'] = django.forms.ChoiceField(
        label=ugettext('Student evaluation'), required=True,
        help_text=ugettext(
            'The response to this question determines whether the '
            'student receives the next round of payments.'),
        choices=EVALUATION_CHOICES,
        widget=django.forms.RadioSelect(renderer=forms.RadioFieldRenderer))

  class Meta:
    model = GSoCGradingProjectSurveyRecord
    css_prefix = 'gsoc-mentor-eval-record'
    exclude = ['project', 'org', 'user', 'survey', 'created', 'modified']

  def clean_grade(self):
    """Convert the value of grade from string as returned by form to boolean
    """
    grade = self.cleaned_data.get('grade')
    return True if grade == 'True' else False


class GSoCMentorEvaluationEditPage(base.GSoCRequestHandler):
  """View for creating/editing organization evaluation form.
  """

  def djangoURLPatterns(self):
    return [
         url_patterns.url(r'eval/mentor/edit/%s$' % url_patterns.SURVEY,
             self, name='gsoc_edit_mentor_evaluation'),
    ]

  def checkAccess(self, data, check, mutator):
    check.isHost()
    mutator.mentorEvaluationFromKwargs(raise_not_found=False)

  def templatePath(self):
    return 'modules/gsoc/_evaluation.html'

  def context(self, data, check, mutator):
    if data.mentor_evaluation:
      form = GSoCMentorEvaluationEditForm(
          data=data.POST or None, instance=data.mentor_evaluation)
    else:
      form = GSoCMentorEvaluationEditForm(data=data.POST or None)

    page_name = ugettext('Edit - %s' % (data.mentor_evaluation.title)) \
        if data.mentor_evaluation else 'Create new mentor evaluation'

    survey_key = db.Key.from_path(
        GradingProjectSurvey.kind(), '%s/%s' % (
            data.program.key().name(), data.kwargs['survey']))
    context = {
        'page_name': page_name,
        'post_url': links.SOC_LINKER.survey(
            survey_key, 'gsoc_edit_mentor_evaluation'),
        'forms': [form],
        'error': bool(form.errors),
        }

    return context

  def evaluationFromForm(self, data):
    """Create/edit the mentor evaluation entity from form.

    Args:
      data: A RequestData describing the current request.

    Returns:
      a newly created or updated mentor evaluation entity or None.
    """
    if data.mentor_evaluation:
      form = GSoCMentorEvaluationEditForm(
          data=data.POST, instance=data.mentor_evaluation)
    else:
      form = GSoCMentorEvaluationEditForm(data=data.POST)

    if not form.is_valid():
      return None

    form.cleaned_data['modified_by'] = data.user

    if not data.mentor_evaluation:
      form.cleaned_data['link_id'] = data.kwargs.get('survey')
      form.cleaned_data['prefix'] = 'gsoc_program'
      form.cleaned_data['author'] = data.user
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
      survey_key = db.Key.from_path(
          GradingProjectSurvey.kind(), '%s/%s' % (
              data.program.key().name(), data.kwargs['survey']))
      url = links.SOC_LINKER.survey(survey_key, 'gsoc_edit_mentor_evaluation')

      # TODO(daniel): append 'validated=True' to the URL in a more elegant way.
      return http.HttpResponseRedirect(url + '?validated')
    else:
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)


class GSoCMentorEvaluationTakePage(base.GSoCRequestHandler):
  """View for the organization to submit student evaluation."""

  def djangoURLPatterns(self):
    return [
         url_patterns.url(r'eval/mentor/%s$' % url_patterns.SURVEY_RECORD,
             self, name='gsoc_take_mentor_evaluation'),
    ]

  def checkAccess(self, data, check, mutator):
    mutator.mentorEvaluationFromKwargs()
    mutator.mentorEvaluationRecordFromKwargs()

    assert isSet(data.mentor_evaluation)

    show_url = data.redirect.survey_record(
        data.mentor_evaluation.link_id).urlOf(
        'gsoc_show_mentor_evaluation')
    check.isSurveyActive(data.mentor_evaluation, show_url)
    check.canUserTakeSurvey(data.mentor_evaluation, 'org')
    check.isMentorForSurvey()

  def templatePath(self):
    return 'modules/gsoc/_evaluation_take.html'

  def context(self, data, check, mutator):
    if data.mentor_evaluation_record:
      form = GSoCMentorEvaluationTakeForm(
          survey=data.mentor_evaluation,
          data=data.POST or None, instance=data.mentor_evaluation_record)
    else:
      form = GSoCMentorEvaluationTakeForm(
          survey=data.mentor_evaluation, data=data.POST or None)

    student = ndb.Key.from_old_key(data.url_project.parent_key()).get()
    context = {
        'page_name': '%s' % (data.mentor_evaluation.title),
        'description': data.mentor_evaluation.content,
        'project': data.url_project.title,
        'student': student.public_name,
        'forms': [form],
        'error': bool(form.errors),
        }

    return context

  def recordEvaluationFromForm(self, data):
    """Create/edit a new mentor evaluation record based on the form input.

    Args:
      data: A RequestData describing the current request.

    Returns:
      a newly created or updated evaluation record entity or None
    """
    if data.mentor_evaluation_record:
      form = GSoCMentorEvaluationTakeForm(
          survey=data.mentor_evaluation, data=data.POST,
          instance=data.mentor_evaluation_record)
    else:
      form = GSoCMentorEvaluationTakeForm(
          survey=data.mentor_evaluation, data=data.POST)

    if not form.is_valid():
      return None

    if not data.mentor_evaluation_record:
      org_key = project_model.GSoCProject.org.get_value_for_datastore(
          data.org_project)
      form.cleaned_data['project'] = data.url_project
      form.cleaned_data['org'] = org_key
      form.cleaned_data['user'] = data.user
      form.cleaned_data['survey'] = data.mentor_evaluation
      entity = form.create(commit=True)
    else:
      entity = form.save(commit=True)

    return entity

  def post(self, data, check, mutator):
    mentor_evaluation_record = self.recordEvaluationFromForm(data)
    if mentor_evaluation_record:
      data.redirect.survey_record(data.mentor_evaluation.link_id)
      return data.redirect.to('gsoc_take_mentor_evaluation', validated=True)
    else:
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)


class GSoCMentorEvaluationPreviewPage(base.GSoCRequestHandler):
  """View for the host preview mentor evaluation."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
         url_patterns.url(r'eval/mentor/preview/%s$' % url_patterns.SURVEY,
             self, name='gsoc_preview_mentor_evaluation'),
    ]

  def checkAccess(self, data, check, mutator):
    check.isHost()


  def templatePath(self):
    return 'modules/gsoc/_evaluation_take.html'

  def context(self, data, check, mutator):
    mutator.mentorEvaluationFromKwargs()

    form = GSoCMentorEvaluationTakeForm(survey=data.mentor_evaluation)

    context = {
        'page_name': '%s' % (data.mentor_evaluation.title),
        'description': data.mentor_evaluation.content,
        'project': 'The Project Title',
        'student': "The Student's Name",
        'forms': [form],
        'error': bool(form.errors),
        }

    return context


class GSoCMentorEvaluationRecordsList(base.GSoCRequestHandler):
  """View for listing all records of a GSoCGradingProjectSurveyRecord."""

  def djangoURLPatterns(self):
    return [
         url_patterns.url(
             r'eval/mentor/records/%s$' % url_patterns.SURVEY,
             self, name='gsoc_list_mentor_eval_records')
         ]

  def checkAccess(self, data, check, mutator):
    """Defines access checks for this list, all hosts should be able to see it.
    """
    check.isHost()
    mutator.mentorEvaluationFromKwargs()

  def context(self, data, check, mutator):
    """Returns the context of the page to render."""
    record_list = self._createSurveyRecordList(data)

    page_name = ugettext('Records - %s' % (data.mentor_evaluation.title))
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
          data.request, prefetch=['project', 'org']).content()
    else:
      # TODO(nathaniel): missing return statement?
      super(GSoCMentorEvaluationRecordsList, self).jsonContext(
          data, check, mutator)

  def _createSurveyRecordList(self, data):
    """Creates a SurveyRecordList for the requested survey."""
    record_list = survey.SurveyRecordList(
        data, data.mentor_evaluation, GSoCGradingProjectSurveyRecord, idx=0)

    def getOrganization(entity, *args):
      """Helper function to get value of organization column."""
      org_key = GSoCGradingProjectSurveyRecord.org.get_value_for_datastore(
          entity)
      return ndb.Key.from_old_key(org_key).get().name

    record_list.list_config.addSimpleColumn('grade', 'Passed?')
    record_list.list_config.addPlainTextColumn(
        'project', 'Project', lambda ent, *args: ent.project.title)
    record_list.list_config.addPlainTextColumn(
        'org', 'Organization', getOrganization)

    return record_list

  def templatePath(self):
    return 'modules/gsoc/mentor_eval/record_list.html'


class GSoCMentorEvaluationReadOnlyTemplate(SurveyRecordReadOnlyTemplate):
  """Template to construct readonly mentor evaluation record."""

  class Meta:
    model = GSoCGradingProjectSurveyRecord
    css_prefix = 'gsoc-mentor-eval-show'
    survey_name = 'Mentor Evaluation'


class GSoCMentorEvaluationShowPage(base.GSoCRequestHandler):
  """View to display the readonly page for mentor evaluation."""

  def djangoURLPatterns(self):
    return [
        url_patterns.url(r'eval/mentor/show/%s$' % url_patterns.SURVEY_RECORD,
            self, name='gsoc_show_mentor_evaluation'),
    ]

  def checkAccess(self, data, check, mutator):
    mutator.mentorEvaluationFromKwargs()
    mutator.mentorEvaluationRecordFromKwargs()

    assert isSet(data.mentor_evaluation)

    check.isProfileActive()
    check.isMentorForSurvey()

  def templatePath(self):
    return 'modules/gsoc/_survey/show.html'

  def context(self, data, check, mutator):
    assert isSet(data.mentor_evaluation_record)

    record = data.mentor_evaluation_record
    student = data.url_profile

    context = {
        'page_name': 'Student evaluation - %s' % (student.name()),
        'student': student.name(),
        'organization': data.url_project.org.name,
        'project': data.url_project.title,
        'css_prefix': GSoCMentorEvaluationReadOnlyTemplate.Meta.css_prefix,
        }

    if record:
      context['record'] = GSoCMentorEvaluationReadOnlyTemplate(record)

    if data.timeline.surveyPeriod(data.mentor_evaluation):
      context['update_link'] = data.redirect.survey_record(
          data.mentor_evaluation.link_id).urlOf('gsoc_take_mentor_evaluation')

    return context
