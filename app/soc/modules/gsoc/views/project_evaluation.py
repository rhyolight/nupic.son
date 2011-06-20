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

from soc.views.helper.access_checker import isSet

from soc.modules.gsoc.models.project_survey import ProjectSurvey
from soc.modules.gsoc.models.project_survey_record import \
    GSoCProjectSurveyRecord
from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.base_templates import LoggedInMsg
from soc.modules.gsoc.views.helper import url_patterns


  """

  class Meta:
    model = ProjectSurvey
    css_prefix = 'gsoc_survey_edit'
    exclude = ['schema', 'scope', 'author', 'modified_by',
               'survey_content', 'scope_path', 'link_id',
               'prefix', 'survey_order']


  """

  class Meta:
    exclude = ['project', 'org', 'user', 'survey', 'created', 'modified']


  """

  def djangoURLPatterns(self):
    return [
    ]


  """

  def djangoURLPatterns(self):
    return [
    ]

  def checkAccess(self):


  def templatePath(self):
    return 'v2/modules/gsoc/_survey_take.html'

  def context(self):
    else:

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
    else:

    if not form.is_valid():
      return None

      form.cleaned_data['project'] = self.data.project
      form.cleaned_data['org'] = self.data.project.org
      form.cleaned_data['user'] = self.data.user
      entity = form.create(commit=True)
    else:
      entity = form.save(commit=True)

    return entity

  def post(self):
    else:
      self.get()
