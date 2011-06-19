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


from soc.views import forms

from django.conf.urls.defaults import url
from django import forms as django_forms

from soc.views.helper.access_checker import isSet

from soc.modules.gsoc.models.project_survey import ProjectSurvey
from soc.modules.gsoc.models.project_survey_record import \
    GSoCProjectSurveyRecord
from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.base_templates import LoggedInMsg
from soc.modules.gsoc.views.helper import url_patterns


class GSoCProjectSurveyEditForm(forms.SurveyEditForm):
  """Form to create/edit GSoC project survey for students.
  """

  class Meta:
    model = ProjectSurvey
    css_prefix = 'gsoc_survey_edit'
    exclude = ['schema', 'scope', 'author', 'modified_by',
               'survey_content', 'scope_path', 'link_id',
               'prefix', 'survey_order']


class GSoCProjectSurveyTakeForm(forms.SurveyTakeForm):
  """Form for students to respond to the survey during evaluations.
  """

  class Meta:
    model = GSoCProjectSurveyRecord
    css_prefix = 'gsoc_survey_content'
    exclude = ['project', 'org', 'user', 'survey', 'created', 'modified']


class SurveyEditPage(RequestHandler):
  """View for creating and/or editing surveys.
  """

  def djangoURLPatterns(self):
    return [
         url(r'^gsoc/evaluation/midterm/%s$' % url_patterns.PROGRAM,
         self, name='gsoc_edit_midterm_survey'),
    ]

  def checkAccess(self):
    pass

  def templatePath(self):
    return 'v2/modules/gsoc/_survey.html'

  def context(self):
    # TODO: (test code) remove it
    from google.appengine.ext import db
    org_app_key_name = 'gsoc_program/google/gsoc2009/gsoc2009survey'
    org_app_key = db.Key.from_path('OrgAppSurvey', org_app_key_name)
    org_app = db.get(org_app_key)
    # Test code end

    form = GSoCProjectSurveyEditForm(self.data.POST or None,
                                     instance=org_app.survey_content)

    context = {
        'page_name': "Midterm survey page",
        'form_top_msg': LoggedInMsg(self.data, apply_link=False),
        'forms': [form],
        'error': bool(form.errors),
        }

    return context


class SurveyTakePage(RequestHandler):
  """View for creating and/or editing surveys.
  """

  def djangoURLPatterns(self):
    return [
         url(r'^gsoc/survey/%s$' % url_patterns.SURVEY_RECORD,
         self, name='gsoc_take_midterm_survey'),
    ]

  def checkAccess(self):
    self.mutator.projectSurveyRecordFromKwargs()

    assert isSet(self.data.project_survey)
    self.check.isSurveyActive(self.data.project_survey)
    self.check.canUserTakeSurvey(self.data.project_survey)
    self.check.isStudentForSurvey()

  def templatePath(self):
    return 'v2/modules/gsoc/_survey_take.html'

  def context(self):
    if self.data.project_survey_record:
      form = GSoCProjectSurveyTakeForm(
          self.data.project_survey.survey_content,
          self.data.POST or None, instance=self.data.project_survey_record)
    else:
      form = GSoCProjectSurveyTakeForm(
          self.data.project_survey.survey_content, self.data.POST or None)

    context = {
        'page_name': "Midterm survey page",
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
    if self.data.project_survey_record:
      form = GSoCProjectSurveyTakeForm(
          self.data.project_survey.survey_content,
          self.data.POST, instance=self.data.project_survey_record)
    else:
      form = GSoCProjectSurveyTakeForm(
          self.data.project_survey.survey_content, self.data.POST)

    if not form.is_valid():
      return None

    if not self.data.project_survey_record:
      form.cleaned_data['project'] = self.data.project
      form.cleaned_data['org'] = self.data.project.org
      form.cleaned_data['user'] = self.data.user
      form.cleaned_data['survey'] = self.data.project_survey
      entity = form.create(commit=True)
    else:
      entity = form.save(commit=True)

    return entity

  def post(self):
    project_survey_record = self.recordSurveyFromForm()
    if project_survey_record:
      r = self.redirect.survey_record(self.data.project_survey)
      r.to('gsoc_take_midterm_survey', validated=True)
    else:
      self.get()
