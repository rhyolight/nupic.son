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
    exclude = ['scope', 'author', 'program', 'created_by', 'modified_by']


class OrgAppTakeForm(forms.SurveyTakeForm):
  """Form for would-be organization admins to apply for the program.
  """

  class Meta:
    model = OrgAppRecord
    css_prefix = 'org-app-record'
    exclude = ['status', 'user', 'survey', 'created', 'modified']


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


class OrgAppReadOnlyTemplate(SurveyRecordReadOnlyTemplate):
  """Template to construct readonly organization application record.
  """

  class Meta:
    model = OrgAppRecord
    css_prefix = 'org-app-show'
