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

"""Module for the org applications.
"""

__authors__ = [
  '"Madhusudan.C.S" <madhusudancs@gmail.com>',
  ]


from django.utils.translation import ugettext

from soc.views import forms
from soc.views import survey
from soc.views.helper import lists

from soc.models.org_app_record import OrgAppRecord
from soc.models.org_app_survey import OrgAppSurvey
from soc.views.helper.access_checker import isSet
from soc.views.readonly_template import SurveyRecordReadOnlyTemplate

from soc.views.base import SiteRequestHandler
from soc.modules.gsoc.views.base_templates import LoggedInMsg


class OrgAppEditForm(forms.SurveyEditForm):
  """Form to create/edit organization application survey.
  """

  class Meta:
    model = OrgAppSurvey
    css_prefix = 'org-app-edit'
    exclude = ['program', 'created_by', 'modified_by']


class OrgAppTakeForm(forms.SurveyTakeForm):
  """Form for would-be organization admins to apply for the program.
  """

  class Meta:
    model = OrgAppRecord
    css_prefix = 'org-app-record'
    exclude = ['status', 'user', 'survey', 'created', 'modified']


class OrgAppEditPage(SiteRequestHandler):
  """View for creating/editing organization application.
  """

  pass


class OrgAppTakePage(SiteRequestHandler):
  """View for organizations to submit their application.
  """

  def checkAccess(self):
    self.mutator.orgAppFromKwargs()
    self.mutator.orgAppRecordFromKwargs()
    assert isSet(self.data.org_app)

  def templatePath(self):
    return 'v2/modules/gsoc/_evaluation_take.html'

  def context(self):
    if self.data.org_app_record:
      form = OrgAppTakeForm(self.data.org_app, self.data.POST or None,
                            instance=self.data.org_app_record)
    else:
      form = OrgAppTakeForm(self.data.org_app, self.data.POST or None)

    context = {
        'page_name': '%s' % (self.data.org_app.title),
        'form_top_msg': LoggedInMsg(self.data, apply_link=False),
        'forms': [form],
        'error': bool(form.errors),
        }

    return context

  def recordOrgAppFromForm(self):
    """Create/edit a new student evaluation record based on the form input.

    Returns:
      a newly created or updated evaluation record entity or None
    """
    if self.data.student_evaluation_record:
      form = OrgAppTakeForm(
          self.data.org_app,
          self.data.POST, instance=self.data.org_app_record)
    else:
      form = OrgAppTakeForm(
          self.data.org_app, self.data.POST)

    if not form.is_valid():
      return None

    if not self.data.org_app_record:
      form.cleaned_data['user'] = self.data.user
      form.cleaned_data['main_admin'] = self.data.user
      form.cleaned_data['survey'] = self.data.org_app
      entity = form.create(commit=True)
    else:
      entity = form.save(commit=True)

    return entity


class OrgAppRecordsList(SiteRequestHandler):
  """View for listing all records of a Organization Applications.
  """

  def checkAccess(self):
    """Defines access checks for this list, all hosts should be able to see it.
    """
    self.check.isHost()
    self.mutator.orgAppFromKwargs()

  def context(self):
    """Returns the context of the page to render.
    """
    record_list = self._createOrgAppsList()

    page_name = ugettext('Records - %s' % (self.data.org_app.title))
    context = {
        'page_name': page_name,
        'record_list': record_list,
        }
    return context

  def jsonContext(self):
    """Handler for JSON requests.
    """
    idx = lists.getListIndex(self.request)
    if idx == 0:
      record_list = self._createOrgAppsList()
      return record_list.listContentResponse(
          self.request, prefetch=['org', 'project']).content()
    else:
      super(OrgAppRecordsList, self).jsonContext()

  def _createOrgAppsList(self):
    """Creates a SurveyRecordList for the requested survey.
    """
    record_list = survey.SurveyRecordList(
        self.data, self.data.org_app, OrgAppRecord, idx=0)

    return record_list

  def templatePath(self):
    return 'v2/modules/gsoc/student_eval/record_list.html'


class GCIOrgAppReadOnlyTemplate(SurveyRecordReadOnlyTemplate):
  """Template to construct readonly organization application record.
  """

  class Meta:
    model = OrgAppRecord
    css_prefix = 'org-app-show'


class OrgAppShowPage(SiteRequestHandler):
  """View to display the readonly page for organization applications.
  """

  def checkAccess(self):
    self.mutator.orgAppFromKwargs()
    self.mutator.orgAppRecordFromKwargs()
    assert isSet(self.data.org_app)

  def templatePath(self):
    return 'v2/modules/gsoc/_survey/show.html'

  def context(self):
    assert isSet(self.data.program)
    assert isSet(self.data.timeline)
    assert isSet(self.data.org_app_record)

    record = self.data.org_app_record

    context = {
        'page_name': 'Organization application - %s' % (record.name()),
        'organization': record.name,
        'top_msg': LoggedInMsg(self.data, apply_link=False),
        'css_prefix': GCIOrgAppReadOnlyTemplate.Meta.css_prefix,
        }

    if record:
      context['record'] = GCIOrgAppReadOnlyTemplate(record)

    return context
