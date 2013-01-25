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

"""Module containing the views for GSoC Organization Application."""

import logging

from django import http
from django.utils import simplejson
from django.utils.translation import ugettext

from soc.logic.exceptions import BadRequest
from soc.logic.exceptions import NotFound
from soc.mapreduce.helper import control as mapreduce_control
from soc.models.org_app_record import OrgAppRecord
from soc.views import org_app
from soc.views.helper import access_checker
from soc.views.helper import url_patterns

from soc.logic import org_app as org_app_logic
from soc.modules.gsoc.views import forms as gsoc_forms
from soc.modules.gsoc.views.base import GSoCRequestHandler
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper.url_patterns import url


class GSoCOrgAppEditForm(org_app.OrgAppEditForm):
  """Form to create/edit GSoC organization application survey.
  """

  class Meta(org_app.OrgAppEditForm.Meta):
    pass

  def __init__(self, *args, **kwargs):
    super(GSoCOrgAppEditForm, self).__init__(
        gsoc_forms.GSoCBoundField, *args, **kwargs)

  def templatePath(self):
    return 'v2/modules/gsoc/_form.html'


class GSoCOrgAppTakeForm(org_app.OrgAppTakeForm):
  """Form for would-be organization admins to apply for a GSoC program.
  """

  CHECKBOX_SELECT_MULTIPLE = gsoc_forms.CheckboxSelectMultiple

  RADIO_FIELD_RENDERER = gsoc_forms.RadioFieldRenderer

  class Meta(org_app.OrgAppTakeForm.Meta):
    pass

  def __init__(self, survey, tos_content, *args, **kwargs):
    super(GSoCOrgAppTakeForm, self).__init__(
        survey, tos_content, gsoc_forms.GSoCBoundField, *args, **kwargs)

  def templatePath(self):
    return 'v2/modules/gsoc/_form.html'


class GSoCOrgAppEditPage(GSoCRequestHandler):
  """View for creating/editing organization application.
  """

  def djangoURLPatterns(self):
    return [
         url(r'org/application/edit/%s$' % url_patterns.PROGRAM,
             self, name='gsoc_edit_org_app'),
    ]

  def checkAccess(self):
    self.check.isHost()

  def templatePath(self):
    return 'v2/modules/gsoc/org_app/edit.html'

  def context(self):
    if self.data.org_app:
      form = GSoCOrgAppEditForm(
          self.data.POST or None, instance=self.data.org_app)
    else:
      form = GSoCOrgAppEditForm(self.data.POST or None)

    if self.data.org_app:
      page_name = ugettext('Edit - %s' % (self.data.org_app.title))
    else:
      page_name = 'Create new organization application'

    context = {
        'page_name': page_name,
        'post_url': self.linker.program(
            self.data.program, 'gsoc_edit_org_app'),
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
      form = GSoCOrgAppEditForm(
          self.data.POST, instance=self.data.org_app)
    else:
      form = GSoCOrgAppEditForm(self.data.POST)

    if not form.is_valid():
      return None

    form.cleaned_data['modified_by'] = self.data.user

    if not self.data.org_app:
      form.cleaned_data['created_by'] = self.data.user
      form.cleaned_data['program'] = self.data.program
      key_name = 'gsoc_program/%s/orgapp' % self.data.program.key().name()
      entity = form.create(key_name=key_name, commit=True)
    else:
      entity = form.save(commit=True)

    return entity

  def post(self):
    org_app = self.orgAppFromForm()
    if org_app:
      # TODO(nathaniel): is this .program() necessary?
      self.redirect.program()

      return self.redirect.to('gsoc_edit_org_app', validated=True)
    else:
      # TODO(nathaniel): problematic self-use.
      return self.get()


class GSoCOrgAppPreviewPage(GSoCRequestHandler):
  """Organization Application preview page.

  View for Organization Administrators to preview the organization
  application for the program specified in the URL.
  """

  def djangoURLPatterns(self):
    return [
         url(r'org/application/preview/%s$' % url_patterns.PROGRAM,
             self, name='gsoc_preview_org_app'),
    ]

  def checkAccess(self):
    self.check.isHost()
    if not self.data.org_app:
      raise NotFound(access_checker.DEF_NO_ORG_APP % self.data.program.name)

  def templatePath(self):
    return 'v2/modules/gsoc/org_app/take.html'

  def context(self):
    oa_agreement = self.data.program.org_admin_agreement.content if \
        self.data.program.org_admin_agreement else ''
    form = GSoCOrgAppTakeForm(
        self.data.org_app, oa_agreement)

    context = {
        'page_name': '%s' % (self.data.org_app.title),
        'forms': [form],
        'error': bool(form.errors),
        }

    return context


class GSoCOrgAppTakePage(GSoCRequestHandler):
  """View for organizations to submit their application.
  """

  def djangoURLPatterns(self):
    return [
         url(r'org/application/%s$' % url_patterns.PROGRAM,
             self, name='gsoc_take_org_app'),
         url(r'org/application/%s$' % url_patterns.ID,
             self, name='gsoc_retake_org_app'),
    ]

  def checkAccess(self):
    if not self.data.org_app:
      raise NotFound(access_checker.DEF_NO_ORG_APP % self.data.program.name)
    self.mutator.orgAppRecordIfIdInKwargs()
    assert access_checker.isSet(self.data.org_app)

    show_url = None
    if 'id' in self.kwargs:
      show_url = self.data.redirect.id().urlOf('gsoc_show_org_app')

    self.check.isSurveyActive(self.data.org_app, show_url)

    if self.data.org_app_record:
      self.check.canRetakeOrgApp()
    else:
      self.check.canTakeOrgApp()

  def templatePath(self):
    return 'v2/modules/gsoc/org_app/take.html'

  def _getTOSContent(self):
    return self.data.program.org_admin_agreement.content if \
        self.data.program.org_admin_agreement else ''

  def context(self):
    if self.data.org_app_record:
      form = GSoCOrgAppTakeForm(self.data.org_app, self._getTOSContent(),
          self.data.POST or None, instance=self.data.org_app_record)
    else:
      form = GSoCOrgAppTakeForm(self.data.org_app, self._getTOSContent(),
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
      form = GSoCOrgAppTakeForm(
          self.data.org_app, self._getTOSContent(),
          self.data.POST, instance=self.data.org_app_record)
    else:
      form = GSoCOrgAppTakeForm(
          self.data.org_app, self._getTOSContent(), self.data.POST)

    if not form.is_valid():
      return None

    if not self.data.org_app_record:
      form.cleaned_data['user'] = self.data.user
      form.cleaned_data['main_admin'] = self.data.user
      form.cleaned_data['survey'] = self.data.org_app
      form.cleaned_data['program'] = self.data.program
      entity = form.create(commit=True)
    else:
      entity = form.save(commit=True)

    return entity

  def post(self):
    org_app_record = self.recordOrgAppFromForm()
    if org_app_record:
      r = self.redirect.id(org_app_record.key().id())
      return r.to('gsoc_retake_org_app', validated=True)
    else:
      # TODO(nathaniel): problematic self-use.
      return self.get()


class GSoCOrgAppRecordsList(org_app.OrgAppRecordsList, GSoCRequestHandler):
  """View for listing all records of a GSoC Organization application.
  """

  def __init__(self, *args, **kwargs):
    GSoCRequestHandler.__init__(self, *args, **kwargs)
    org_app.OrgAppRecordsList.__init__(self, 'gsoc_show_org_app')

  def djangoURLPatterns(self):
    return [
         url(
             r'org/application/records/%s$' % url_patterns.PROGRAM,
             self, name='gsoc_list_org_app_records')
         ]

  def post(self):
    """Edits records from commands received by the list code."""
    post_data = self.data.request.POST

    self.data.redirect.program()

    if (post_data.get('process', '') ==
        org_app.PROCESS_ORG_APPS_FORM_BUTTON_VALUE):
      mapreduce_control.start_map('ProcessOrgApp', {
          'program_type': 'gsoc',
          'program_key': self.data.program.key().name()
          })
      return self.redirect.to('gsoc_list_org_app_records', validated=True)

    if not post_data.get('button_id', None) == 'save':
      raise BadRequest('No valid POST data found')

    data = self.data.POST.get('data')

    if not data:
      raise BadRequest('Missing data')

    parsed = simplejson.loads(data)
    url = self.data.redirect.urlOf('create_gsoc_org_profile', full=True)

    for oaid, properties in parsed.iteritems():
      record = OrgAppRecord.get_by_id(long(oaid))

      if not record:
        logging.warning('%s is an invalid OrgAppRecord ID' % oaid)
        continue

      if record.survey.key() != self.data.org_app.key():
        logging.warning(
            '%s is not a record for the Org App in the URL' % record.key())
        continue

      new_status = properties['status']
      org_app_logic.setStatus(self.data, record, new_status, url)

    return http.HttpResponse()


class OrgAppReadOnlyTemplate(org_app.OrgAppReadOnlyTemplate):
  """Template to construct readonly organization application record.
  """

  template_path = 'v2/modules/gsoc/org_app/readonly_template.html'


class GSoCOrgAppShowPage(GSoCRequestHandler):
  """View to display the readonly page for organization application.
  """

  def djangoURLPatterns(self):
    return [
        url(r'org/application/show/%s$' % url_patterns.ID,
            self, name='gsoc_show_org_app'),
    ]

  def checkAccess(self):
    if not self.data.org_app:
      raise NotFound(access_checker.DEF_NO_ORG_APP % self.data.program.name)
    self.mutator.orgAppRecordIfIdInKwargs()
    assert access_checker.isSet(self.data.org_app_record)

    self.check.canViewOrgApp()

  def templatePath(self):
    return 'v2/modules/gsoc/org_app/show.html'

  def context(self):
    record = self.data.org_app_record

    context = {
        'page_name': 'Organization application - %s' % (record.name),
        'organization': record.name,
        'css_prefix': OrgAppReadOnlyTemplate.Meta.css_prefix,
        }

    if record:
      context['record'] = OrgAppReadOnlyTemplate(record)

      # admin info should be available only to the hosts
      if self.data.is_host:
        context['main_admin_url'] = self.data.redirect.profile(
            record.main_admin.link_id).urlOf(url_names.GSOC_PROFILE_SHOW)
        context['backup_admin_url'] = self.data.redirect.profile(
            record.backup_admin.link_id).urlOf(url_names.GSOC_PROFILE_SHOW)

    if self.data.timeline.surveyPeriod(self.data.org_app):
      if record:
        context['update_link'] = self.data.redirect.id().urlOf(
            'gsoc_retake_org_app')
      else:
        context['create_link'] = self.linker.program(
            self.data.program, 'gsoc_take_org_app')

    return context
