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


from django.utils.translation import ugettext

import django

from soc.views import forms
from soc.views.helper.access_checker import isSet
from soc.views.readonly_template import SurveyRecordReadOnlyTemplate

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
    css_prefix = 'gsoc-mentor-eval-edit'
    exclude = ['scope', 'author', 'modified_by', 'survey_content',
               'scope_path', 'link_id', 'prefix', 'read_access',
               'write_access', 'taking_access', 'is_featured']

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


class GSoCMentorEvaluationEditPage(RequestHandler):
  """View for creating/editing organization evaluation form.
  """

  def djangoURLPatterns(self):
    return [
         url_patterns.url(r'eval/mentor/edit/%s$' % url_patterns.SURVEY,
             self, name='gsoc_edit_mentor_evaluation'),
    ]

  def checkAccess(self):
    self.check.isHost()
    self.mutator.mentorEvaluationFromKwargs(raise_not_found=False)

  def templatePath(self):
    return 'v2/modules/gsoc/_evaluation.html'

  def context(self):
    if self.data.mentor_evaluation:
      form = GSoCMentorEvaluationEditForm(
          self.data.POST or None, instance=self.data.mentor_evaluation)
    else:
      form = GSoCMentorEvaluationEditForm(self.data.POST or None)

    page_name = ugettext('Edit - %s' % (self.data.mentor_evaluation.title)) \
        if self.data.mentor_evaluation else 'Create new mentor evaluation'
    context = {
        'page_name': page_name,
        'post_url': self.redirect.survey().urlOf(
            'gsoc_edit_mentor_evaluation'),
        'forms': [form],
        'error': bool(form.errors),
        }

    return context

  def evaluationFromForm(self):
    """Create/edit the mentor evaluation entity from form.

    Returns:
      a newly created or updated mentor evaluation entity or None.
    """
    if self.data.mentor_evaluation:
      form = GSoCMentorEvaluationEditForm(
          self.data.POST, instance=self.data.mentor_evaluation)
    else:
      form = GSoCMentorEvaluationEditForm(self.data.POST)

    if not form.is_valid():
      return None

    form.cleaned_data['modified_by'] = self.data.user

    if not self.data.mentor_evaluation:
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
    evaluation = self.evaluationFromForm()
    if evaluation:
      r = self.redirect.survey()
      r.to('gsoc_edit_mentor_evaluation', validated=True)
    else:
      self.get()


class GSoCMentorEvaluationTakePage(RequestHandler):
  """View for the organization to submit student evaluation.
  """

  def djangoURLPatterns(self):
    return [
         url_patterns.url(r'eval/mentor/%s$' % url_patterns.SURVEY_RECORD,
             self, name='gsoc_take_mentor_evaluation'),
    ]

  def checkAccess(self):
    self.mutator.projectFromKwargs()
    self.mutator.mentorEvaluationFromKwargs()
    self.mutator.mentorEvaluationRecordFromKwargs()

    assert isSet(self.data.mentor_evaluation)
    self.check.isSurveyActive(self.data.mentor_evaluation)
    self.check.canUserTakeSurvey(self.data.mentor_evaluation)
    self.check.isMentorForSurvey()

  def templatePath(self):
    return 'v2/modules/gsoc/_evaluation_take.html'

  def context(self):
    if self.data.mentor_evaluation_record:
      form = GSoCMentorEvaluationTakeForm(
          self.data.mentor_evaluation,
          self.data.POST or None, instance=self.data.mentor_evaluation_record)
    else:
      form = GSoCMentorEvaluationTakeForm(
          self.data.mentor_evaluation, self.data.POST or None)

    context = {
        'page_name': '%s page' % (self.data.mentor_evaluation.title),
        'form_top_msg': LoggedInMsg(self.data, apply_link=False),
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

  def post(self):
    mentor_evaluation_record = self.recordEvaluationFromForm()
    if mentor_evaluation_record:
      r = self.redirect.survey_record(
          self.data.mentor_evaluation.link_id)
      r.to('gsoc_take_mentor_evaluation', validated=True)
    else:
      self.get()


class GSoCMentorEvaluationReadOnlyTemplate(SurveyRecordReadOnlyTemplate):
  """Template to construct readonly mentor evaluation record.
  """

  class Meta:
    model = GSoCGradingProjectSurveyRecord
    css_prefix = 'gsoc-mentor-eval-show'


class GSoCMentorEvaluationShowPage(RequestHandler):
  """View to display the readonly page for mentor evaluation.
  """

  def djangoURLPatterns(self):
    return [
        url_patterns.url(r'eval/mentor/show/%s$' % url_patterns.SURVEY_RECORD,
            self, name='gsoc_show_mentor_evaluation'),
    ]

  def checkAccess(self):
    self.mutator.projectFromKwargs()
    self.mutator.mentorEvaluationFromKwargs()
    self.mutator.mentorEvaluationRecordFromKwargs()

    assert isSet(self.data.project)
    assert isSet(self.data.mentor_evaluation)

    self.check.isProfileActive()
    self.check.isMentorForSurvey()

  def templatePath(self):
    return 'v2/modules/gsoc/_survey/show.html'

  def context(self):
    assert isSet(self.data.mentor_evaluation_record)

    record = self.data.mentor_evaluation_record
    student = self.data.url_profile

    context = {
        'page_name': 'Student evaluation - %s' % (student.name()),
        'student': student.name(),
        'organization': self.data.project.org.name,
        'project': self.data.project.title,
        'top_msg': LoggedInMsg(self.data, apply_link=False),
        'css_prefix': GSoCMentorEvaluationReadOnlyTemplate.Meta.css_prefix,
        }

    if record:
      context['record'] = GSoCMentorEvaluationReadOnlyTemplate(record)

    if self.data.timeline.surveyPeriod(self.data.mentor_evaluation):
      context['update_link'] = self.data.redirect.survey_record(
          self.data.mentor_evaluation.link_id).urlOf(
          'gsoc_take_mentor_evaluation')

    return context
