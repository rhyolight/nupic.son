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

from soc.modules.gsoc.models.project_survey import ProjectSurvey
from soc.models.survey import SurveyContent
from soc.views.helper.access_checker import isSet

from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.base_templates import LoggedInMsg
from soc.modules.gsoc.views.helper import url_patterns


class SurveyEditForm(forms.ModelForm):
  """Django form for creating and/or editing survey.
  """

  class Meta:
    model = ProjectSurvey
    css_prefix = 'gsoc_survey_edit'
    exclude = ['schema', 'scope', 'author', 'modified_by',
               'survey_content', 'scope_path', 'link_id',
               'prefix', 'survey_order']


class SurveyTakeForm(forms.ModelForm):
  """Django form for taking a survey.
  """

  def __init__(self, survey_content, *args, **kwargs):
    super(SurveyTakeForm, self).__init__(*args, **kwargs)
    self.survey_content = survey_content
    self.constructForm()

  def constructForm(self):
    """Constructs the form based on the schema stored in the survey content
    """
    # insert dynamic survey fields
    if self.survey_content:
      # TODO(madhu): Convert this to JSON
      schema = eval(self.survey_content.schema)
      for position, field_name in self.survey_content.getSurveyOrder().items():
        field_info = schema.get(field_name)
        self.constructField(field_name, field_info)

  def constructField(self, field_name, field_info):
    """Constructs the field for the given field metadata

    Args:
      field_name: Name of the field that must be populated
      field_info: Meta data containing how the field must be constructed
    """
    type = field_info.get('type', '')
    render = field_info.get('render', '')
    label = field_info.get('question', '')
    required = field_info.get('required', True)
    comment = field_info.get('has_comment', False)
    help_text = field_info.get('tip', '')

    choices = [(choice, choice) for choice in getattr(
        self.survey_content, field_name)]

    widget = None

    if type == 'selection':
      field = django_forms.ChoiceField
    elif type == 'pick_multi':
      field = django_forms.MultipleChoiceField
      widget = forms.CheckboxSelectMultiple()
    elif type == 'choice':
      field = django_forms.ChoiceField
      widget = forms.RadioSelect()
    elif type == 'pick_quant':
      field = django_forms.ChoiceField
      widget = forms.RadioSelect()
    elif type == 'long_answer':
      field = django_forms.CharField
    elif type == 'short_answer':
      field = django_forms.CharField
      widget = django_forms.Textarea()

    self.fields[field_name] = field(label=label, required=required,
                                    help_text=help_text)
    if widget:
      self.fields[field_name].widget = widget
    if choices:
      self.fields[field_name].choices = choices

  class Meta:
    model = SurveyContent
    css_prefix = 'gsoc_survey_content'
    exclude = ['schema', 'survey_order']


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

    form = SurveyEditForm(self.data.POST or None,
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

  def templatePath(self):
    return 'v2/modules/gsoc/_survey_take.html'

  def context(self):
    form = SurveyTakeForm(self.data.project_survey.survey_content,
                          self.data.POST or None)

    context = {
        'page_name': "Midterm survey page",
        'form_top_msg': LoggedInMsg(self.data, apply_link=False),
        'forms': [form],
        'error': bool(form.errors),
        }

    return context
