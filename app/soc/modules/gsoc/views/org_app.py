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

import json
import logging

from django import http
from django.utils.translation import ugettext

from melange.logic import user as user_logic
from melange.request import access
from melange.request import exception
from soc.logic import org_app as org_app_logic
from soc.mapreduce.helper import control as mapreduce_control
from soc.models.org_app_record import OrgAppRecord
from soc.views import org_app
from soc.views.helper import access_checker
from soc.views.helper import url_patterns


from soc.modules.gsoc.models import profile as profile_model
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views import forms as gsoc_forms
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper.url_patterns import url


class GSoCOrgAppEditForm(org_app.OrgAppEditForm):
  """Form to create/edit GSoC organization application survey.
  """

  class Meta(org_app.OrgAppEditForm.Meta):
    pass

  def __init__(self, **kwargs):
    super(GSoCOrgAppEditForm, self).__init__(
        gsoc_forms.GSoCBoundField, **kwargs)

  def templatePath(self):
    return 'modules/gsoc/_form.html'


class GSoCOrgAppTakeForm(org_app.OrgAppTakeForm):
  """Form for would-be organization admins to apply for a GSoC program.
  """

  CHECKBOX_SELECT_MULTIPLE = gsoc_forms.CheckboxSelectMultiple

  RADIO_FIELD_RENDERER = gsoc_forms.RadioFieldRenderer

  class Meta(org_app.OrgAppTakeForm.Meta):
    pass

  def __init__(self, request_data=None, **kwargs):
    super(GSoCOrgAppTakeForm, self).__init__(
        gsoc_forms.GSoCBoundField, request_data=request_data, **kwargs)

  def clean_backup_admin_id(self):
    """Extends the backup admin cleaner to check if the backup admin has a
    valid profile in the program.
    """
    backup_admin = super(GSoCOrgAppTakeForm, self).clean_backup_admin_id()
    self.validateBackupAdminProfile(backup_admin, profile_model.GSoCProfile)

  def templatePath(self):
    return 'modules/gsoc/_form.html'

  def _getCreateProfileURL(self, redirector):
    """Returns the full secure URL of the GSoC create profile page."""
    return redirector.urlOf(url_names.GSOC_PROFILE_CREATE, full=True, secure=True)


class GSoCOrgAppEditPage(base.GSoCRequestHandler):
  """View for creating/editing organization application."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
         url(r'org/application/edit/%s$' % url_patterns.PROGRAM,
             self, name='gsoc_edit_org_app'),
    ]

  def templatePath(self):
    return 'modules/gsoc/org_app/edit.html'

  def context(self, data, check, mutator):
    if data.org_app:
      form = GSoCOrgAppEditForm(data=data.POST or None, instance=data.org_app)
    else:
      form = GSoCOrgAppEditForm(data=data.POST or None)

    if data.org_app:
      page_name = ugettext('Edit - %s' % (data.org_app.title))
    else:
      page_name = 'Create new organization application'

    context = {
        'page_name': page_name,
        'post_url': self.linker.program(data.program, 'gsoc_edit_org_app'),
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
      form = GSoCOrgAppEditForm(data=data.POST, instance=data.org_app)
    else:
      form = GSoCOrgAppEditForm(data=data.POST)

    if not form.is_valid():
      return None

    form.cleaned_data['modified_by'] = data.ndb_user.key.to_old_key()

    if not data.org_app:
      form.cleaned_data['created_by'] = data.ndb_user.key.to_old_key()
      form.cleaned_data['program'] = data.program
      key_name = 'gsoc_program/%s/orgapp' % data.program.key().name()
      entity = form.create(key_name=key_name, commit=True)
    else:
      entity = form.save(commit=True)

    return entity

  def post(self, data, check, mutator):
    org_app = self.orgAppFromForm(data)
    if org_app:
      # TODO(nathaniel): is this .program() necessary?
      data.redirect.program()

      return data.redirect.to('gsoc_edit_org_app', validated=True)
    else:
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)


class GSoCOrgAppPreviewPage(base.GSoCRequestHandler):
  """Organization Application preview page.

  View for Organization Administrators to preview the organization
  application for the program specified in the URL.
  """

  def djangoURLPatterns(self):
    return [
         url(r'org/application/preview/%s$' % url_patterns.PROGRAM,
             self, name='gsoc_preview_org_app'),
    ]

  def checkAccess(self, data, check, mutator):
    check.isHost()
    if not data.org_app:
      raise exception.NotFound(
          message=access_checker.DEF_NO_ORG_APP % data.program.name)

  def templatePath(self):
    return 'modules/gsoc/org_app/take.html'

  def context(self, data, check, mutator):
    form = GSoCOrgAppTakeForm(request_data=data)

    context = {
        'page_name': '%s' % (data.org_app.title),
        'description': data.org_app.content,
        'forms': [form],
        'error': bool(form.errors),
        }

    return context


class GSoCOrgAppTakePage(base.GSoCRequestHandler):
  """View for organizations to submit their application."""

  def djangoURLPatterns(self):
    return [
         url(r'org/application/%s$' % url_patterns.PROGRAM,
             self, name='gsoc_take_org_app'),
         url(r'org/application/%s$' % url_patterns.ID,
             self, name='gsoc_retake_org_app'),
    ]

  def checkAccess(self, data, check, mutator):
    if not data.org_app:
      raise exception.NotFound(
          message=access_checker.DEF_NO_ORG_APP % data.program.name)
    mutator.orgAppRecordIfIdInKwargs()
    assert access_checker.isSet(data.org_app)

    show_url = None
    if 'id' in data.kwargs:
      show_url = data.redirect.id().urlOf('gsoc_show_org_app')

    check.isSurveyActive(data.org_app, show_url)

    if data.org_app_record:
      check.canRetakeOrgApp()
    else:
      check.canTakeOrgApp()

  def templatePath(self):
    return 'modules/gsoc/org_app/take.html'

  def context(self, data, check, mutator):
    if data.org_app_record:
      form = GSoCOrgAppTakeForm(
          request_data=data, data=data.POST or None,
          instance=data.org_app_record)
    else:
      form = GSoCOrgAppTakeForm(request_data=data, data=data.POST or None)

    context = {
        'page_name': '%s' % (data.org_app.title),
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
      form = GSoCOrgAppTakeForm(
          request_data=data, data=data.POST, instance=data.org_app_record)
    else:
      form = GSoCOrgAppTakeForm(request_data=data, data=data.POST)

    if not form.is_valid():
      return None

    if not data.org_app_record:
      form.cleaned_data['user'] = data.user
      form.cleaned_data['main_admin'] = data.user
      form.cleaned_data['survey'] = data.org_app
      form.cleaned_data['program'] = data.program
      entity = form.create(commit=True)
    else:
      entity = form.save(commit=True)

    return entity

  def post(self, data, check, mutator):
    org_app_record = self.recordOrgAppFromForm(data)
    if org_app_record:
      data.redirect.id(org_app_record.key().id())
      return data.redirect.to('gsoc_retake_org_app', validated=True)
    else:
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)


class GSoCOrgAppRecordsList(org_app.OrgAppRecordsList,
      base.GSoCRequestHandler):
  """View for listing all records of a GSoC Organization application.
  """

  def __init__(self, *args, **kwargs):
    base.GSoCRequestHandler.__init__(self, *args, **kwargs)
    org_app.OrgAppRecordsList.__init__(self, 'gsoc_show_org_app')

  def djangoURLPatterns(self):
    return [
         url(
             r'org/application/records/%s$' % url_patterns.PROGRAM,
             self, name='gsoc_list_org_app_records')
         ]

  def post(self, data, check, mutator):
    """Edits records from commands received by the list code."""
    post_dict = data.request.POST

    data.redirect.program()

    if (post_dict.get('process', '') ==
        org_app.PROCESS_ORG_APPS_FORM_BUTTON_VALUE):
      mapreduce_control.start_map('ProcessOrgApp', {
          'program_type': 'gsoc',
          'program_key': data.program.key().name()
          })
      return data.redirect.to('gsoc_list_org_app_records', validated=True)

    if post_dict.get('button_id', None) != 'save':
      raise exception.BadRequest(message='No valid POST data found')

    post_data = post_dict.get('data')

    if not post_data:
      raise exception.BadRequest(message='Missing data')

    parsed = json.loads(post_data)

    url = 'TODO(daniel): remove this part as it is not used anymore'

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
  """Template to construct readonly organization application record.
  """

  template_path = 'modules/gsoc/org_app/readonly_template.html'


class GSoCOrgAppShowPage(base.GSoCRequestHandler):
  """View to display the readonly page for organization application.
  """

  def djangoURLPatterns(self):
    return [
        url(r'org/application/show/%s$' % url_patterns.ID,
            self, name='gsoc_show_org_app'),
    ]

  def checkAccess(self, data, check, mutator):
    if not data.org_app:
      raise exception.NotFound(
          message=access_checker.DEF_NO_ORG_APP % data.program.name)
    mutator.orgAppRecordIfIdInKwargs()
    assert access_checker.isSet(data.org_app_record)

    check.canViewOrgApp()

  def templatePath(self):
    return 'modules/gsoc/org_app/show.html'

  def context(self, data, check, mutator):
    record = data.org_app_record

    context = {
        'page_name': 'Organization application - %s' % (record.name),
        'organization': record.name,
        'css_prefix': OrgAppReadOnlyTemplate.Meta.css_prefix,
        }

    if record:
      context['record'] = OrgAppReadOnlyTemplate(record)

      # admin info should be available only to the hosts
      if user_logic.isHostForProgram(data.ndb_user, data.program.key()):
        context['main_admin_url'] = data.redirect.profile(
            record.main_admin.link_id).urlOf(url_names.GSOC_PROFILE_SHOW_ADMIN)
        context['backup_admin_url'] = data.redirect.profile(
            record.backup_admin.link_id).urlOf(
                url_names.GSOC_PROFILE_SHOW_ADMIN)

    if data.timeline.surveyPeriod(data.org_app):
      if record:
        context['update_link'] = data.redirect.id().urlOf(
            'gsoc_retake_org_app')
      else:
        context['create_link'] = self.linker.program(
            data.program, 'gsoc_take_org_app')

    return context
