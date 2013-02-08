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

from django.utils.translation import ugettext

import django

from soc.views import forms
from soc.views import survey
from soc.views.helper import lists
from soc.views.helper.access_checker import isSet
from soc.views.readonly_template import SurveyRecordReadOnlyTemplate

from soc.modules.gsoc.models.grading_project_survey import GradingProjectSurvey
from soc.modules.gsoc.models.grading_project_survey_record import \
    GSoCGradingProjectSurveyRecord
from soc.modules.gsoc.views import forms as gsoc_forms
from soc.modules.gsoc.views.base import GSoCRequestHandler
from soc.modules.gsoc.views.base_templates import LoggedInMsg
from soc.modules.gsoc.views.helper import url_patterns

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
               'survey_content', 'scope_path', 'link_id', 'prefix',
               'read_access', 'write_access', 'taking_access',
               'is_featured']

class GSoCMentorEvaluationTakeForm(gsoc_forms.SurveyTakeForm):
  """Form for the organization to evaluate a student project."""

  def __init__(self, survey, *args, **kwargs):
    """Initialize the form field by adding a new grading field.
    """
    super(GSoCMentorEvaluationTakeForm, self).__init__(
        survey, *args, **kwargs)

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


class GSoCMentorEvaluationEditPage(GSoCRequestHandler):
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
    return 'v2/modules/gsoc/_evaluation.html'

  def context(self, data, check, mutator):
    if data.mentor_evaluation:
      form = GSoCMentorEvaluationEditForm(
          data.POST or None, instance=data.mentor_evaluation)
    else:
      form = GSoCMentorEvaluationEditForm(data.POST or None)

    page_name = ugettext('Edit - %s' % (data.mentor_evaluation.title)) \
        if data.mentor_evaluation else 'Create new mentor evaluation'
    context = {
        'page_name': page_name,
        'post_url': data.redirect.survey().urlOf(
            'gsoc_edit_mentor_evaluation'),
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
          data.POST, instance=data.mentor_evaluation)
    else:
      form = GSoCMentorEvaluationEditForm(data.POST)

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
      data.redirect.survey()
      return data.redirect.to('gsoc_edit_mentor_evaluation', validated=True)
    else:
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)


class GSoCMentorEvaluationTakePage(GSoCRequestHandler):
  """View for the organization to submit student evaluation.
  """

  def djangoURLPatterns(self):
    return [
         url_patterns.url(r'eval/mentor/%s$' % url_patterns.SURVEY_RECORD,
             self, name='gsoc_take_mentor_evaluation'),
    ]

  def checkAccess(self, data, check, mutator):
    mutator.projectFromKwargs()
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
    return 'v2/modules/gsoc/_evaluation_take.html'

  def context(self, data, check, mutator):
    if data.mentor_evaluation_record:
      form = GSoCMentorEvaluationTakeForm(
          data.mentor_evaluation,
          data.POST or None, instance=data.mentor_evaluation_record)
    else:
      form = GSoCMentorEvaluationTakeForm(
          data.mentor_evaluation, data.POST or None)

    context = {
        'page_name': '%s' % (data.mentor_evaluation.title),
        'description': data.mentor_evaluation.content,
        'form_top_msg': LoggedInMsg(data, apply_link=False,
                                    div_name='user-login'),
        'project': data.project.title,
        'student': data.project_owner.name(),
        'forms': [form],
        'error': bool(form.errors),
        }

    return context

  def recordEvaluationFromForm(self):
    """Create/edit a new mentor evaluation record based on the form input.

    Returns:
      a newly created or updated evaluation record entity or None
    """
    if self.data.mentor_evaluation_record:
      form = GSoCMentorEvaluationTakeForm(
          self.data.mentor_evaluation,
          self.data.POST, instance=self.data.mentor_evaluation_record)
    else:
      form = GSoCMentorEvaluationTakeForm(
          self.data.mentor_evaluation, self.data.POST)

    if not form.is_valid():
      return None

    if not self.data.mentor_evaluation_record:
      form.cleaned_data['project'] = self.data.project
      form.cleaned_data['org'] = self.data.project.org
      form.cleaned_data['user'] = self.data.user
      form.cleaned_data['survey'] = self.data.mentor_evaluation
      entity = form.create(commit=True)
    else:
      entity = form.save(commit=True)

    return entity

  def post(self, data, check, mutator):
    mentor_evaluation_record = self.recordEvaluationFromForm()
    if mentor_evaluation_record:
      data.redirect.survey_record(data.mentor_evaluation.link_id)
      return data.redirect.to('gsoc_take_mentor_evaluation', validated=True)
    else:
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)


class GSoCMentorEvaluationPreviewPage(GSoCRequestHandler):
  """View for the host preview mentor evaluation.
  """

  def djangoURLPatterns(self):
    return [
         url_patterns.url(r'eval/mentor/preview/%s$' % url_patterns.SURVEY,
             self, name='gsoc_preview_mentor_evaluation'),
    ]

  def checkAccess(self, data, check, mutator):
    check.isHost()
    mutator.mentorEvaluationFromKwargs(raise_not_found=False)

  def templatePath(self):
    return 'v2/modules/gsoc/_evaluation_take.html'

  def context(self, data, check, mutator):
    form = GSoCMentorEvaluationTakeForm(data.mentor_evaluation)

    context = {
        'page_name': '%s' % (data.mentor_evaluation.title),
        'description': data.mentor_evaluation.content,
        'form_top_msg': LoggedInMsg(data, apply_link=False,
                                    div_name='user-login'),
        'project': 'The Project Title',
        'student': "The Student's Name",
        'forms': [form],
        'error': bool(form.errors),
        }

    return context


class GSoCMentorEvaluationRecordsList(GSoCRequestHandler):
  """View for listing all records of a GSoCGradingProjectSurveyRecord.
  """

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
    record_list = self._createSurveyRecordList()

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
      record_list = self._createSurveyRecordList()
      return record_list.listContentResponse(
          data.request, prefetch=['project', 'org']).content()
    else:
      # TODO(nathaniel): missing return statement?
      super(GSoCMentorEvaluationRecordsList, self).jsonContext(
          data, check, mutator)

  def _createSurveyRecordList(self):
    """Creates a SurveyRecordList for the requested survey.
    """
    record_list = survey.SurveyRecordList(
        self.data, self.data.mentor_evaluation, GSoCGradingProjectSurveyRecord,
        idx=0)

    record_list.list_config.addSimpleColumn('grade', 'Passed?')
    record_list.list_config.addPlainTextColumn(
        'project', 'Project', lambda ent, *args: ent.project.title)
    record_list.list_config.addPlainTextColumn(
        'org', 'Organization', lambda ent, *args: ent.org.name)

    return record_list

  def templatePath(self):
    return 'v2/modules/gsoc/mentor_eval/record_list.html'


class GSoCMentorEvaluationReadOnlyTemplate(SurveyRecordReadOnlyTemplate):
  """Template to construct readonly mentor evaluation record.
  """

  class Meta:
    model = GSoCGradingProjectSurveyRecord
    css_prefix = 'gsoc-mentor-eval-show'
    survey_name = 'Mentor Evaluation'


class GSoCMentorEvaluationShowPage(GSoCRequestHandler):
  """View to display the readonly page for mentor evaluation.
  """

  def djangoURLPatterns(self):
    return [
        url_patterns.url(r'eval/mentor/show/%s$' % url_patterns.SURVEY_RECORD,
            self, name='gsoc_show_mentor_evaluation'),
    ]

  def checkAccess(self, data, check, mutator):
    mutator.projectFromKwargs()
    mutator.mentorEvaluationFromKwargs()
    mutator.mentorEvaluationRecordFromKwargs()

    assert isSet(data.project)
    assert isSet(data.mentor_evaluation)

    check.isProfileActive()
    check.isMentorForSurvey()

  def templatePath(self):
    return 'v2/modules/gsoc/_survey/show.html'

  def context(self, data, check, mutator):
    assert isSet(data.mentor_evaluation_record)

    record = data.mentor_evaluation_record
    student = data.url_profile

    context = {
        'page_name': 'Student evaluation - %s' % (student.name()),
        'student': student.name(),
        'organization': data.project.org.name,
        'project': data.project.title,
        'top_msg': LoggedInMsg(data, apply_link=False),
        'css_prefix': GSoCMentorEvaluationReadOnlyTemplate.Meta.css_prefix,
        }

    if record:
      context['record'] = GSoCMentorEvaluationReadOnlyTemplate(record)

    if self.data.timeline.surveyPeriod(data.mentor_evaluation):
      context['update_link'] = data.redirect.survey_record(
          data.mentor_evaluation.link_id).urlOf('gsoc_take_mentor_evaluation')

    return context
