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

"""Module for the GCI Organization application."""

import json
import logging

from django import http
from django.utils.translation import ugettext

from melange.request import access
from melange.request import exception
from soc.logic import org_app as org_app_logic
from soc.mapreduce.helper import control as mapreduce_control
from soc.models.org_app_record import OrgAppRecord
from soc.views import org_app
from soc.views.helper import access_checker
from soc.views.helper import url_patterns

from soc.modules.gci.models import profile as profile_model
from soc.modules.gci.views import forms
from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views.helper import url_names
from soc.modules.gci.views.helper.url_patterns import url

TEMPLATE_PATH = 'modules/gci/_form.html'


class OrgAppEditForm(org_app.OrgAppEditForm):
  """Form to create/edit GCI organization application survey.
  """

  class Meta(org_app.OrgAppEditForm.Meta):
    pass

  def __init__(self, **kwargs):
    super(OrgAppEditForm, self).__init__(forms.GCIBoundField, **kwargs)

  def templatePath(self):
    return TEMPLATE_PATH


class OrgAppTakeForm(org_app.OrgAppTakeForm):
  """Form for would-be organization admins to apply for a GCI program.
  """

  CHECKBOX_SELECT_MULTIPLE = forms.CheckboxSelectMultiple

  RADIO_FIELD_RENDERER = forms.RadioFieldRenderer

  class Meta(org_app.OrgAppTakeForm.Meta):
    pass

  def __init__(self, request_data=None, **kwargs):
    super(OrgAppTakeForm, self).__init__(
        forms.GCIBoundField, request_data=request_data, **kwargs)

  def clean_backup_admin_id(self):
    """Extends the backup admin cleaner to check if the backup admin has a
    valid profile in the program.
    """
    backup_admin = super(OrgAppTakeForm, self).clean_backup_admin_id()
    self.validateBackupAdminProfile(backup_admin, profile_model.GCIProfile)

  def templatePath(self):
    return TEMPLATE_PATH

  def _getCreateProfileURL(self, redirector):
    """Returns the full secure URL of the GCI create profile page."""
    return redirector.urlOf(url_names.GCI_PROFILE_CREATE, full=True, secure=True)


class GCIOrgAppEditPage(GCIRequestHandler):
  """View for creating/editing organization application."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
         url(r'org/application/edit/%s$' % url_patterns.PROGRAM,
             self, name='gci_edit_org_app'),
    ]

  def templatePath(self):
    return 'modules/gci/org_app/edit.html'

  def context(self, data, check, mutator):
    if data.org_app:
      form = OrgAppEditForm(data=data.POST or None, instance=data.org_app)
    else:
      form = OrgAppEditForm(data=data.POST or None)

    if data.org_app:
      page_name = ugettext('Edit - %s' % data.org_app.title)
    else:
      page_name = 'Create new organization application'

    context = {
        'page_name': page_name,
        'post_url': self.linker.program(data.program, 'gci_edit_org_app'),
        'forms': [form],
        'error': bool(form.errors),
        }

    return context

  def orgAppFromForm(self, data):
    """Create/edit the organization application entity from form.

    Args:
      data: A RequestData describing the current request.

    Returns:
      a newly created or updated organization application entity or None.
    """
    if data.org_app:
      form = OrgAppEditForm(data=data.POST, instance=data.org_app)
    else:
      form = OrgAppEditForm(data=data.POST)

    if not form.is_valid():
      return None

    form.cleaned_data['modified_by'] = data.user

    if not data.org_app:
      form.cleaned_data['created_by'] = data.user
      form.cleaned_data['program'] = data.program
      key_name = 'gci_program/%s/orgapp' % data.program.key().name()
      entity = form.create(key_name=key_name, commit=True)
    else:
      entity = form.save(commit=True)

    return entity

  def post(self, data, check, mutator):
    org_app = self.orgAppFromForm(data)
    if org_app:
      # TODO(nathaniel): make unnecessary this .program() call.
      data.redirect.program()

      return data.redirect.to('gci_edit_org_app', validated=True)
    else:
      # TODO(nathaniel): problematic self-call.
      return self.get(data, check, mutator)


class GCIOrgAppPreviewPage(GCIRequestHandler):
  """Organization Application preview page.

  View for Organization Administrators to preview the organization
  application for the program specified in the URL.
  """

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
         url(r'org/application/preview/%s$' % url_patterns.PROGRAM,
             self, name='gci_preview_org_app'),
    ]

  def templatePath(self):
    return 'modules/gci/org_app/take.html'

  def context(self, data, check, mutator):
    form = OrgAppTakeForm(request_data=data)

    context = {
        'page_name': '%s' % data.org_app.title,
        'description': data.org_app.content,
        'forms': [form],
        'error': bool(form.errors),
        }

    return context


class GCIOrgAppTakePage(GCIRequestHandler):
  """View for organizations to submit their application."""

  def djangoURLPatterns(self):
    return [
         url(r'org/application/%s$' % url_patterns.PROGRAM,
             self, name='gci_take_org_app'),
         url(r'org/application/%s$' % url_patterns.ID,
             self, name='gci_retake_org_app'),
    ]

  def checkAccess(self, data, check, mutator):
    if not data.org_app:
      raise exception.NotFound(
          message=access_checker.DEF_NO_ORG_APP % data.program.name)

    mutator.orgAppRecordIfIdInKwargs()
    assert access_checker.isSet(data.org_app)

    # FIXME: There will never be organization in kwargs
    show_url = None
    if 'organization' in data.kwargs:
      # TODO(nathaniel): make this .organization() call unnecessary. Like,
      # more than it already is (see the note above).
      data.redirect.organization()

      show_url = data.redirect.urlOf('gci_show_org_app')

    check.isSurveyActive(data.org_app, show_url)

    if data.org_app_record:
      check.canRetakeOrgApp()
    else:
      check.canTakeOrgApp()

  def templatePath(self):
    return 'modules/gci/org_app/take.html'

  def context(self, data, check, mutator):
    if data.org_app_record:
      form = OrgAppTakeForm(request_data=data, data=data.POST or None,
                            instance=data.org_app_record)
    else:
      form = OrgAppTakeForm(request_data=data, data=data.POST or None)

    context = {
        'page_name': '%s' % data.org_app.title,
        'description': data.org_app.content,
        'forms': [form],
        'error': bool(form.errors),
        }

    return context

  def recordOrgAppFromForm(self, data):
    """Create/edit a new student evaluation record based on the form input.

    Args:
      data: A RequestData describing the current request.

    Returns:
      a newly created or updated evaluation record entity or None
    """
    if data.org_app_record:
      form = OrgAppTakeForm(request_data=data, data=data.POST,
                            instance=data.org_app_record)
    else:
      form = OrgAppTakeForm(request_data=data, data=data.POST)

    if not form.is_valid():
      return None

    if not data.org_app_record:
      form.cleaned_data['user'] = data.user
      form.cleaned_data['main_admin'] = data.user
      form.cleaned_data['survey'] = data.org_app
      entity = form.create(commit=True)
    else:
      entity = form.save(commit=True)

    return entity

  def post(self, data, check, mutator):
    org_app_record = self.recordOrgAppFromForm(data)
    if org_app_record:
      data.redirect.id(org_app_record.key().id())
      return data.redirect.to('gci_retake_org_app', validated=True)
    else:
      # TODO(nathaniel): problematic self-call.
      return self.get(data, check, mutator)


class GCIOrgAppRecordsList(org_app.OrgAppRecordsList, GCIRequestHandler):
  """View for listing all records of a GCI Organization application.
  """

  def __init__(self, *args, **kwargs):
    GCIRequestHandler.__init__(self, *args, **kwargs)
    org_app.OrgAppRecordsList.__init__(self, 'gci_show_org_app')

  def djangoURLPatterns(self):
    return [
         url(
             r'org/application/records/%s$' % url_patterns.PROGRAM,
             self, name=url_names.GCI_LIST_ORG_APP_RECORDS)
         ]

  def post(self, data, check, mutator):
    """Edits records from commands received by the list code."""
    post_dict = data.request.POST

    data.redirect.program()

    if (post_dict.get('process', '') ==
        org_app.PROCESS_ORG_APPS_FORM_BUTTON_VALUE):
      mapreduce_control.start_map('ProcessOrgApp', {
          'program_type': 'gci',
          'program_key': data.program.key().name()
          })
      return data.redirect.to(
          url_names.GCI_LIST_ORG_APP_RECORDS, validated=True)

    if post_dict.get('button_id', None) != 'save':
      raise exception.BadRequest(message='No valid POST data found')

    post_data = post_dict.get('data')
    if not post_data:
      raise exception.BadRequest(message='Missing data')

    parsed = json.loads(post_data)
    data.redirect.program()
    url = data.redirect.urlOf('create_gci_org_profile', full=True)

    for oaid, properties in parsed.iteritems():
      record = OrgAppRecord.get_by_id(long(oaid))

      if not record:
        logging.warning('%s is an invalid OrgAppRecord ID', oaid)
        continue

      if record.survey.key() != data.org_app.key():
        logging.warning(
            '%s is not a record for the Org App in the URL', record.key())
        continue

      new_status = properties['status']
      org_app_logic.setStatus(data, record, new_status, url)

    return http.HttpResponse()


class OrgAppReadOnlyTemplate(org_app.OrgAppReadOnlyTemplate):
  """Template to construct readonly organization application record."""

  template_path = 'modules/gci/org_app/readonly_template.html'


class GCIOrgAppShowPage(GCIRequestHandler):
  """View to display the readonly page for organization application."""

  def djangoURLPatterns(self):
    return [
        url(r'org/application/show/%s$' % url_patterns.ID,
            self, name='gci_show_org_app'),
    ]

  def checkAccess(self, data, check, mutator):
    if not data.org_app:
      raise exception.NotFound(
          message=access_checker.DEF_NO_ORG_APP % data.program.name)

    mutator.orgAppRecordIfIdInKwargs()
    assert access_checker.isSet(data.org_app_record)

    check.canViewOrgApp()

  def templatePath(self):
    return 'modules/gci/org_app/show.html'

  def context(self, data, check, mutator):
    record = data.org_app_record

    context = {
        'page_name': 'Organization application - %s' % (record.name),
        'organization': record.name,
        'css_prefix': OrgAppReadOnlyTemplate.Meta.css_prefix,
        }

    if record:
      context['record'] = OrgAppReadOnlyTemplate(record)

    return context
