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

"""Module for the GCI Organization application.
"""

__authors__ = [
  '"Madhusudan.C.S" <madhusudancs@gmail.com>',
  ]


from django.utils.translation import ugettext

from soc.views import org_app
from soc.views.helper import access_checker
from soc.views.helper import url_patterns

from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.base import RequestHandler
from soc.modules.gci.views.helper.url_patterns import url


class GCIOrgAppEditPage(RequestHandler):
  """View for creating/editing organization application.
  """

  def djangoURLPatterns(self):
    return [
         url(r'org/application/edit/%s$' % url_patterns.PROGRAM,
             self, name='gci_edit_org_app'),
    ]

  def checkAccess(self):
    self.check.isHost()
    self.mutator.orgAppFromKwargs(raise_not_found=False)

  def templatePath(self):
    return 'v2/modules/gsoc/_evaluation.html'

  def context(self):
    if self.data.org_app:
      form = gci_forms.OrgAppEditForm(
          self.data.POST or None, instance=self.data.org_app)
    else:
      form = gci_forms.OrgAppEditForm(self.data.POST or None)

    if self.data.org_app:
      page_name = ugettext('Edit - %s' % (self.data.org_app.title))
    else:
      page_name = 'Create new organization application'

    context = {
        'page_name': page_name,
        'post_url': self.redirect.program().urlOf('gci_edit_org_app'),
        'forms': [form],
        'error': bool(form.errors),
        }

    return context

  def orgAppFromForm(self):
    """Create/edit the organization application entity from form.

    Returns:
      a newly created or updated organization application entity or None.
    """
    if self.data.org_app:
      form = gci_forms.OrgAppEditForm(
          self.data.POST, instance=self.data.org_app)
    else:
      form = gci_forms.OrgAppEditForm(self.data.POST)

    if not form.is_valid():
      return None

    form.cleaned_data['modified_by'] = self.data.user

    if not self.data.org_app:
      form.cleaned_data['created_by'] = self.data.user
      form.cleaned_data['program'] = self.data.program
      entity = form.create(commit=True)
    else:
      entity = form.save(commit=True)

    return entity

  def post(self):
    org_app = self.orgAppFromForm()
    if org_app:
      r = self.redirect.program()
      r.to('gci_edit_org_app', validated=True)
    else:
      self.get()


class GCIOrgAppPreviewPage(RequestHandler):
  """View for organizations to submit their application.
  """

  def djangoURLPatterns(self):
    return [
         url(r'org/application/preview/%s$' % url_patterns.PROGRAM,
             self, name='gci_take_org_app'),
    ]

  def checkAccess(self):
    self.check.isHost()
    self.mutator.orgAppFromKwargs(raise_not_found=False)

  def templatePath(self):
    return 'v2/modules/gsoc/_evaluation_take.html'

  def context(self):
    form = gci_forms.OrgAppTakeForm(self.data.org_app)

    context = {
        'page_name': '%s' % (self.data.org_app.title),
        'forms': [form],
        'error': bool(form.errors),
        }

    return context


class GCIOrgAppTakePage(RequestHandler):
  """View for organizations to submit their application.
  """

  def djangoURLPatterns(self):
    return [
         url(r'org/application/%s$' % url_patterns.PROGRAM,
             self, name='gci_take_org_app'),
         url(r'org/application/%s$' % url_patterns.ID,
             self, name='gci_take_org_app'),
    ]

  def checkAccess(self):
    self.mutator.orgAppFromKwargs()
    self.mutator.orgAppRecordIfIdInKwargs()
    assert access_checker.isSet(self.data.org_app)

    show_url = None
    if 'organization' in self.kwargs:
      show_url = self.data.redirect.organization().urlOf('gci_show_org_app')

    self.check.isSurveyActive(self.data.org_app, show_url)
    self.check.canAccessOrgApp()

  def templatePath(self):
    return 'v2/modules/gsoc/_evaluation_take.html'

  def context(self):
    if self.data.org_app_record:
      form = gci_forms.OrgAppTakeForm(self.data.org_app,
          self.data.POST or None, instance=self.data.org_app_record)
    else:
      form = gci_forms.OrgAppTakeForm(self.data.org_app,
          self.data.POST or None)

    context = {
        'page_name': '%s' % (self.data.org_app.title),
        'forms': [form],
        'error': bool(form.errors),
        }

    return context

  def recordOrgAppFromForm(self):
    """Create/edit a new student evaluation record based on the form input.

    Returns:
      a newly created or updated evaluation record entity or None
    """
    if self.data.org_app_record:
      form = gci_forms.OrgAppTakeForm(
          self.data.org_app,
          self.data.POST, instance=self.data.org_app_record)
    else:
      form = gci_forms.OrgAppTakeForm(
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

  def post(self):
    org_app_record = self.recordOrgAppFromForm()
    if org_app_record:
      r = self.redirect.id(org_app_record.key().id())
      r.to('gci_take_org_app', validated=True)
    else:
      self.get()


class GCIOrgAppRecordsList(org_app.OrgAppRecordsList):
  """View for listing all records of a GCI Organization application.
  """

  def djangoURLPatterns(self):
    return [
         url(
             r'org/application/records/%s$' % url_patterns.PROGRAM,
             self, name='gci_list_org_app_records')
         ]


class GCIOrgAppShowPage(RequestHandler):
  """View to display the readonly page for organization application.
  """

  def djangoURLPatterns(self):
    return [
        url(r'org/application/show/%s$' % url_patterns.ID,
            self, name='gci_show_org_app'),
    ]

  def checkAccess(self):
    self.mutator.orgAppFromKwargs()
    self.mutator.orgAppRecordIfIdInKwargs()
    assert access_checker.isSet(self.data.org_app)

    self.check.canAccessOrgApp()

  def templatePath(self):
    return 'v2/modules/gsoc/_survey/show.html'

  def context(self):
    assert access_checker.isSet(self.data.program)
    assert access_checker.isSet(self.data.timeline)
    assert access_checker.isSet(self.data.org_app_record)

    record = self.data.org_app_record

    context = {
        'page_name': 'Organization application - %s' % (record.name),
        'organization': record.name,
        'css_prefix': org_app.OrgAppReadOnlyTemplate.Meta.css_prefix,
        }

    if record:
      context['record'] = org_app.OrgAppReadOnlyTemplate(record)

    return context
