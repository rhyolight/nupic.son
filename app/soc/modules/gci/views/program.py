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

"""Module for the program settings pages."""

import json

from django import http

from melange.request import access
from soc.models.document import Document
from soc.views import program as soc_program_view
from soc.views.helper import url_patterns as soc_url_patterns

from soc.modules.gci.models import program as program_model
from soc.modules.gci.models import timeline as timeline_model
from soc.modules.gci.views import base
from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.helper import url_names
from soc.modules.gci.views.helper import url_patterns


class TimelineForm(gci_forms.GCIModelForm):
  """Django form to edit timeline settings."""

  class Meta:
    css_prefix = 'timeline_form'
    model = timeline_model.GCITimeline
    exclude = ['link_id', 'scope']


class CreateProgramForm(gci_forms.GCIModelForm):
  """Django form to create the settings for a new program."""

  def __init__(self, request_data=None, **kwargs):
    self.request_data = request_data
    super(CreateProgramForm, self).__init__(**kwargs)

  class Meta:
    css_prefix = 'create_program_form'
    model = program_model.GCIProgram
    exclude = [
        'scope', 'timeline', 'org_admin_agreement', 'events_page',
        'mentor_agreement', 'student_agreement', 'about_page',
        'connect_with_us_page', 'help_page', 'task_types', 'link_id',
        'sponsor', 'terms_and_conditions']

  def clean(self):
    """Cleans the data input by the user as a response to the form."""
    super(CreateProgramForm, self).clean()

    # TODO(daniel): get rid of this check
    # this is an ugly hack which is needed by the test runner
    # request data POST is not represented by QueryDict, but by a regular
    # dict which does not have getlist method
    if isinstance(self.request_data.POST, http.QueryDict):
      self.cleaned_data['task_types'] = self.request_data.POST.getlist(
          'task_type_name')

    return self.cleaned_data


class EditProgramForm(gci_forms.GCIModelForm):
  """Django form for the program settings."""

  def __init__(self, request_data=None, **kwargs):
    self.request_data = request_data

    super(EditProgramForm, self).__init__(**kwargs)

    if self.instance:
      self.task_types_json = json.dumps(
          [[t] for t in self.instance.task_types])

  class Meta:
    css_prefix = 'edit_program_form'
    model = program_model.GCIProgram
    exclude = ['link_id', 'scope', 'timeline', 'task_types', 'program_id',
        'sponsor']

  def clean(self):
    """Cleans the data input by the user as a response to the form.
    """
    super(EditProgramForm, self).clean()

    self.cleaned_data['task_types'] = self.request_data.POST.getlist(
        'task_type_name')

    return self.cleaned_data


class GCIProgramMessagesForm(gci_forms.GCIModelForm):
  """Django form for the program messages settings.
  """

  def __init__(self, request_data=None, **kwargs):
    self.request_data = request_data
    super(GCIProgramMessagesForm, self).__init__(**kwargs)

  class Meta:
    css_prefix = 'program_messages_form'
    model = program_model.GCIProgramMessages


class GCIEditProgramPage(base.GCIRequestHandler):
  """View to edit the program settings."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
        url_patterns.url(
            r'program/edit/%s$' % soc_url_patterns.PROGRAM, self,
            name=url_names.GCI_PROGRAM_EDIT),
    ]

  def jsonContext(self, data, check, mutator):
    q = Document.all()
    q.filter('prefix', 'gci_program')
    q.filter('scope', data.program.key())

    json_data = [{'key': str(i.key()),
                  'key_name': i.key().name(),
                  'label': i.title}
                  for i in q]

    return {'data': json_data}

  def templatePath(self):
    return 'modules/gci/program/base.html'

  def context(self, data, check, mutator):
    program_form = EditProgramForm(
        request_data=data, data=data.POST or None, instance=data.program)
    return {
        'page_name': 'Edit program settings',
        'forms': [program_form],
        'error': program_form.errors,
    }

  def validate(self, data):
    program_form = EditProgramForm(
        request_data=data, data=data.POST, instance=data.program)

    if program_form.is_valid():
      program_form.save()
      return True
    else:
      return False

  def post(self, data, check, mutator):
    """Handler for HTTP POST request."""
    if self.validate(data):
      data.redirect.program()
      return data.redirect.to(url_names.GCI_PROGRAM_EDIT, validated=True)
    else:
      # TODO(nathaniel): problematic self-call.
      return self.get(data, check, mutator)


class GCICreateProgramPage(soc_program_view.CreateProgramPage,
    base.GCIRequestHandler):
  """View to create a new GCI program."""

  def djangoURLPatterns(self):
    """See soc.views.base.RequestHandler.djangoURLPatterns
    for specification.
    """
    return [
        url_patterns.url(
            r'program/create/%s$' % soc_url_patterns.SPONSOR, self,
            name=url_names.GCI_PROGRAM_CREATE),
    ]

  def templatePath(self):
    """See soc.views.base.RequestHandler.templatePath for specification."""
    return 'modules/gci/program/base.html'

  def _getForm(self, data):
    """See soc.views.program.CreateProgram._getForm for specification."""
    return CreateProgramForm(request_data=data, data=data.POST or None)

  def _getTimelineModel(self):
    """See soc.views.program.CreateProgram._getTimelineModel
    for specification.
    """
    return timeline_model.GCITimeline

  def _getUrlNameForRedirect(self):
    """See soc.views.program.CreateProgram._getUrlNameForRedirect
    for specification.
    """
    return url_names.GCI_PROGRAM_EDIT


class TimelinePage(base.GCIRequestHandler):
  """View for the participant profile."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
        url_patterns.url(
            r'timeline/%s$' % soc_url_patterns.PROGRAM, self,
            name='edit_gci_timeline'),
        url_patterns.url(
            r'timeline/edit/%s$' % soc_url_patterns.PROGRAM, self),
    ]

  def templatePath(self):
    return 'modules/gci/timeline/base.html'

  def context(self, data, check, mutator):
    timeline_form = TimelineForm(
        data=data.POST or None, instance=data.program_timeline)
    return {
        'page_name': 'Edit program timeline',
        'forms': [timeline_form],
        'error': timeline_form.errors,
    }

  def validate(self, data):
    timeline_form = TimelineForm(
        data=data.POST, instance=data.program_timeline)

    if timeline_form.is_valid():
      timeline_form.save()
      return True
    else:
      return False

  def post(self, data, check, mutator):
    """Handler for HTTP POST request."""
    if self.validate(data):
      data.redirect.program()
      return data.redirect.to('edit_gci_timeline', validated=True)
    else:
      # TODO(nathaniel): problematic self-call.
      return self.get(data, check, mutator)


class GCIProgramMessagesPage(
    soc_program_view.ProgramMessagesPage, base.GCIRequestHandler):
  """View for the content of GCI program specific messages to be sent."""

  def djangoURLPatterns(self):
    return [
        url_patterns.url(
            r'program/messages/edit/%s$' % soc_url_patterns.PROGRAM,
            self, name=self._getUrlName()),
    ]

  def templatePath(self):
    return 'modules/gci/program/messages.html'

  def _getForm(self, data, entity):
    return GCIProgramMessagesForm(
        request_data=data, data=data.POST or None, instance=entity)

  def _getModel(self):
    return program_model.GCIProgramMessages

  def _getUrlName(self):
    return url_names.GCI_EDIT_PROGRAM_MESSAGES
