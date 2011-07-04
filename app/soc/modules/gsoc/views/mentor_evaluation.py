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

"""Module for the GSoC project evaluations.
"""

__authors__ = [
  '"Madhusudan.C.S" <madhusudancs@gmail.com>',
  ]


from django import forms as django_forms
from django.conf.urls.defaults import url
from django.utils.translation import ugettext

from soc.views import forms
from soc.views.helper.access_checker import isSet

from soc.modules.gsoc.models.grading_project_survey import GradingProjectSurvey
from soc.modules.gsoc.models.grading_project_survey_record import \
    GSoCGradingProjectSurveyRecord
from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.base_templates import LoggedInMsg
from soc.modules.gsoc.views.helper import url_patterns


EVALUATION_CHOICES = (
    (True, 'Pass'),
    (False, 'Fail')
    )


class GSoCMentorEvaluationEditForm(forms.SurveyEditForm):
  """Form to create/edit GSoC evaluation for the organization.
  """

  class Meta:
    model = GradingProjectSurvey
    css_prefix = 'gsoc_evaluation_edit'
    exclude = ['scope', 'author', 'modified_by', 'survey_content',
               'scope_path', 'link_id', 'prefix', 'survey_order']


class GSoCMentorEvaluationTakeForm(forms.SurveyTakeForm):
  """Form for the organization to evaluate a student project.
  """

  def __init__(self, survey, *args, **kwargs):
    """Initialize the form field by adding a new grading field.
    """
    super(GSoCMentorEvaluationTakeForm, self).__init__(
        survey, *args, **kwargs)

    # hack to re-order grade to push to the end of the survey form
    self.fields.keyOrder.remove('grade')
    self.fields.keyOrder.append('grade')

    self.fields['grade'] = django_forms.ChoiceField(
        label=ugettext('Student evaluation'), required=True,
        help_text=ugettext(
            'The response to this question determines whether the '
            'student receives the next round of payments.'),
        choices=EVALUATION_CHOICES, widget=forms.RadioSelect)

  class Meta:
    model = GSoCGradingProjectSurveyRecord
    css_prefix = 'gsoc_evaluation_record'
    exclude = ['project', 'org', 'user', 'survey', 'created', 'modified']

  def clean_grade(self):
    """Convert the value of grade from string as returned by form to boolean
    """
    grade = self.cleaned_data.get('grade')
    return True if grade == 'True' else False


class GSoCMentorEvaluationEditPage(RequestHandler):
  """View for creating/editing organization evaluation form.
  """

  def djangoURLPatterns(self):
    return [
         url(r'^gsoc/eval/mentor/edit/%s$' % url_patterns.SURVEY,
             self, name='gsoc_edit_mentor_evaluation'),
    ]

  def checkAccess(self):
    self.check.isHost()
    self.mutator.projectEvaluationFromKwargs(raise_not_found=False)

  def templatePath(self):
    return 'v2/modules/gsoc/_survey.html'

  def context(self):
    if self.data.project_evaluation:
      form = GSoCMentorEvaluationEditForm(
          self.data.POST or None, instance=self.data.project_evaluation)
    else:
      form = GSoCMentorEvaluationEditForm(self.data.POST or None)

    page_name = ugettext('Edit - %s' % (self.data.project_evaluation.title)) \
        if self.data.project_evaluation else 'Create new survey'
    context = {
        'page_name': page_name,
        'post_url': self.redirect.survey().urlOf(
            'gsoc_edit_mentor_evaluation'),
        'forms': [form],
        'error': bool(form.errors),
        }

    return context

  def surveyContentFromForm(self):
    """Create/edit the project evaluation survey form.

    Returns:
      a newly created or updated survey entity or None.
    """
    if self.data.project_evaluation:
      form = GSoCMentorEvaluationEditForm(
          self.data.POST, instance=self.data.project_evaluation)
    else:
      form = GSoCMentorEvaluationEditForm(self.data.POST)

    if not form.is_valid():
      return None

    form.cleaned_data['modified_by'] = self.data.user

    if not self.data.project_evaluation:
      form.cleaned_data['link_id'] = self.data.kwargs.get('survey')
      form.cleaned_data['prefix'] = 'gsoc_program'
      form.cleaned_data['author'] = self.data.user
      form.cleaned_data['scope'] = self.data.program
      # kwargs which defines an evaluation
      fields = ['sponsor', 'program', 'survey']

      key_name = '/'.join(['gsoc_program'] +
                          [self.data.kwargs[field] for field in fields])

      entity = form.create(commit=True, key_name=key_name)
    else:
      entity = form.save(commit=True)

    return entity

  def post(self):
    survey_content = self.surveyContentFromForm()
    if survey_content:
      r = self.redirect.survey()
      r.to('gsoc_edit_mentor_evaluation', validated=True)
    else:
      self.get()


class GSoCMentorEvaluationTakePage(RequestHandler):
  """View for the organization to submit student evaluation.
  """

  def djangoURLPatterns(self):
    return [
         url(r'^gsoc/eval/mentor/%s$' % url_patterns.SURVEY_RECORD,
         self, name='gsoc_take_mentor_evaluation'),
    ]

  def checkAccess(self):
    self.mutator.projectFromKwargs()
    self.mutator.projectEvaluationFromKwargs()
    self.mutator.projectEvaluationRecordFromKwargs()

    assert isSet(self.data.project_evaluation)
    self.check.isSurveyActive(self.data.project_evaluation)
    self.check.canUserTakeSurvey(self.data.project_evaluation)
    self.check.isMentorForSurvey()

  def templatePath(self):
    return 'v2/modules/gsoc/_survey_take.html'

  def context(self):
    if self.data.project_evaluation_record:
      form = GSoCMentorEvaluationTakeForm(
          self.data.project_evaluation,
          self.data.POST or None, instance=self.data.project_evaluation_record)
    else:
      form = GSoCMentorEvaluationTakeForm(
          self.data.project_evaluation, self.data.POST or None)

    context = {
        'page_name': '%s page' % (self.data.project_evaluation.title),
        'form_top_msg': LoggedInMsg(self.data, apply_link=False),
        'forms': [form],
        'error': bool(form.errors),
        }

    return context

  def recordSurveyFromForm(self):
    """Create/edit a new survey record based on the data inserted in the form.

    Returns:
      a newly created or updated survey record entity or None
    """
    if self.data.project_evaluation_record:
      form = GSoCMentorEvaluationTakeForm(
          self.data.project_evaluation,
          self.data.POST, instance=self.data.project_evaluation_record)
    else:
      form = GSoCMentorEvaluationTakeForm(
          self.data.project_evaluation, self.data.POST)

    if not form.is_valid():
      return None

    if not self.data.project_evaluation_record:
      form.cleaned_data['project'] = self.data.project
      form.cleaned_data['org'] = self.data.project.org
      form.cleaned_data['user'] = self.data.user
      form.cleaned_data['survey'] = self.data.project_evaluation
      entity = form.create(commit=True)
    else:
      entity = form.save(commit=True)

    return entity

  def post(self):
    project_evaluation_record = self.recordSurveyFromForm()
    if project_evaluation_record:
      r = self.redirect.survey_record(
          self.data.project_evaluation.link_id)
      r.to('gsoc_take_mentor_evaluation', validated=True)
    else:
      self.get()
