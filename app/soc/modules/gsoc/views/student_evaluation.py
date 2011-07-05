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

"""Module for the GSoC project student survey.
"""

__authors__ = [
  '"Madhusudan.C.S" <madhusudancs@gmail.com>',
  ]


from soc.views import forms

from django.conf.urls.defaults import url
from django.utils.translation import ugettext

from soc.views.helper.access_checker import isSet

from soc.modules.gsoc.models.project_survey import ProjectSurvey
from soc.modules.gsoc.models.project_survey_record import \
    GSoCProjectSurveyRecord
from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.base_templates import LoggedInMsg
from soc.modules.gsoc.views.helper import url_patterns


class GSoCStudentEvaluationEditForm(forms.SurveyEditForm):
  """Form to create/edit GSoC project survey for students.
  """

  class Meta:
    model = ProjectSurvey
    css_prefix = 'gsoc-student-eval-edit'
    exclude = ['scope', 'author', 'modified_by', 'survey_content',
               'scope_path', 'link_id', 'prefix', 'read_access',
               'write_access', 'taking_access', 'is_featured']


class GSoCStudentEvaluationTakeForm(forms.SurveyTakeForm):
  """Form for students to respond to the survey during evaluations.
  """

  class Meta:
    model = GSoCProjectSurveyRecord
    css_prefix = 'gsoc-student-eval-record'
    exclude = ['project', 'org', 'user', 'survey', 'created', 'modified']


class GSoCStudentEvaluationEditPage(RequestHandler):
  """View for creating/editing student evalution.
  """

  def djangoURLPatterns(self):
    return [
         url(r'^gsoc/eval/student/edit/%s$' % url_patterns.SURVEY,
         self, name='gsoc_edit_student_evaluation'),
    ]

  def checkAccess(self):
    self.check.isHost()
    self.mutator.studentEvaluationFromKwargs(raise_not_found=False)

  def templatePath(self):
    return 'v2/modules/gsoc/_evaluation.html'

  def context(self):
    if self.data.student_evaluation:
      form = GSoCStudentEvaluationEditForm(
          self.data.POST or None, instance=self.data.student_evaluation)
    else:
      form = GSoCStudentEvaluationEditForm(self.data.POST or None)

    page_name = ugettext('Edit - %s' % (self.data.student_evaluation.title)) \
        if self.data.student_evaluation else 'Create new student evaluation'
    context = {
        'page_name': page_name,
        'post_url': self.redirect.survey().urlOf(
            'gsoc_edit_student_evaluation'),
        'forms': [form],
        'error': bool(form.errors),
        }

    return context

  def evaluationFromForm(self):
    """Create/edit the student evaluation entity from form.

    Returns:
      a newly created or updated student evaluation entity or None.
    """
    if self.data.student_evaluation:
      form = GSoCStudentEvaluationEditForm(
          self.data.POST, instance=self.data.student_evaluation)
    else:
      form = GSoCStudentEvaluationEditForm(self.data.POST)

    if not form.is_valid():
      return None

    form.cleaned_data['modified_by'] = self.data.user

    if not self.data.student_evaluation:
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
      r.to('gsoc_edit_student_evaluation', validated=True)
    else:
      self.get()

class GSoCStudentEvaluationTakePage(RequestHandler):
  """View for students to submit their evaluation.
  """

  def djangoURLPatterns(self):
    return [
         url(r'^gsoc/eval/student/%s$' % url_patterns.SURVEY_RECORD,
         self, name='gsoc_take_student_evaluation'),
    ]

  def checkAccess(self):
    self.mutator.projectFromKwargs()
    self.mutator.studentEvaluationFromKwargs()
    self.mutator.studentEvaluationRecordFromKwargs()

    assert isSet(self.data.student_evaluation)
    self.check.isSurveyActive(self.data.student_evaluation)
    self.check.canUserTakeSurvey(self.data.student_evaluation)
    self.check.isStudentForSurvey()

  def templatePath(self):
    return 'v2/modules/gsoc/_evaluation_take.html'

  def context(self):
    if self.data.student_evaluation_record:
      form = GSoCStudentEvaluationTakeForm(
          self.data.student_evaluation,
          self.data.POST or None, instance=self.data.student_evaluation_record)
    else:
      form = GSoCStudentEvaluationTakeForm(
          self.data.student_evaluation, self.data.POST or None)

    context = {
        'page_name': '%s page' % (self.data.student_evaluation.title),
        'form_top_msg': LoggedInMsg(self.data, apply_link=False),
        'forms': [form],
        'error': bool(form.errors),
        }

    return context

  def recordEvaluationFromForm(self):
    """Create/edit a new student evaluation record based on the form input.

    Returns:
      a newly created or updated evaluation record entity or None
    """
    if self.data.student_evaluation_record:
      form = GSoCStudentEvaluationTakeForm(
          self.data.student_evaluation,
          self.data.POST, instance=self.data.student_evaluation_record)
    else:
      form = GSoCStudentEvaluationTakeForm(
          self.data.student_evaluation, self.data.POST)

    if not form.is_valid():
      return None

    if not self.data.student_evaluation_record:
      form.cleaned_data['project'] = self.data.project
      form.cleaned_data['org'] = self.data.project.org
      form.cleaned_data['user'] = self.data.user
      form.cleaned_data['survey'] = self.data.student_evaluation
      entity = form.create(commit=True)
    else:
      entity = form.save(commit=True)

    return entity

  def post(self):
    student_evaluation_record = self.recordEvaluationFromForm()
    if student_evaluation_record:
      r = self.redirect.survey_record(
          self.data.student_evaluation.link_id)
      r.to('gsoc_take_student_evaluation', validated=True)
    else:
      self.get()
