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

from google.appengine.ext import db

from django import forms as django_forms
from django.utils import simplejson as json
from django.utils.translation import ugettext

from soc.logic import tags as tags_logic
from soc.models.document import Document
from soc.views import forms
from soc.views import program as program_view
from soc.views.helper import url_patterns

from soc.modules.gci.models.program import GCIProgram
from soc.modules.gci.models.program import GCIProgramMessages
from soc.modules.gci.models.timeline import GCITimeline
from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views.forms import GCIModelForm
from soc.modules.gci.views.helper import url_names
from soc.modules.gci.views.helper.url_patterns import url


class TimelineForm(GCIModelForm):
  """Django form to edit timeline settings."""

  class Meta:
    css_prefix = 'timeline_form'
    model = GCITimeline
    exclude = ['link_id', 'scope', 'scope_path']


class ProgramForm(GCIModelForm):
  """Django form for the program settings."""

  def __init__(self, data, *args, **kwargs):
    self.request_data = data

    super(ProgramForm, self).__init__(*args, **kwargs)

    if self.instance:
      self.task_types_json = json.dumps(
          [[t] for t in self.instance.task_types])

  class Meta:
    css_prefix = 'program_form'
    model = GCIProgram
    exclude = ['link_id', 'scope', 'scope_path', 'timeline', 'home',
               'slots_allocation', 'task_types']

  def clean(self):
    """Cleans the data input by the user as a response to the form.
    """
    super(ProgramForm, self).clean()

    self.cleaned_data['task_types'] = self.request_data.POST.getlist(
        'task_type_name')

    return self.cleaned_data


class GCIProgramMessagesForm(GCIModelForm):
  """Django form for the program messages settings.
  """

  def __init__(self, request_data, *args, **kwargs):
    self.request_data = request_data
    super(GCIProgramMessagesForm, self).__init__(*args, **kwargs)

  class Meta:
    css_prefix = 'program_messages_form'
    model = GCIProgramMessages


class ProgramPage(GCIRequestHandler):
  """View for the program profile."""

  def djangoURLPatterns(self):
    return [
        url(r'program/%s$' % url_patterns.PROGRAM, self,
            name='edit_gci_program'),
        url(r'program/edit/%s$' % url_patterns.PROGRAM, self),
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

  def checkAccess(self):
    self.check.isHost()

  def templatePath(self):
    return 'v2/modules/gci/program/base.html'

  def context(self):
    program_form = ProgramForm(self.data, self.data.POST or None,
                               instance=self.data.program)
    return {
        'page_name': 'Edit program settings',
        'forms': [program_form],
        'error': program_form.errors,
    }

  def validate(self):
    program_form = ProgramForm(
        self.data, self.data.POST, instance=self.data.program)

    if program_form.is_valid():
      program_form.save()
      return True
    else:
      return False

  def post(self, data, check, mutator):
    """Handler for HTTP POST request."""
    if self.validate():
      data.redirect.program()
      return data.redirect.to('edit_gci_program', validated=True)
    else:
      # TODO(nathaniel): problematic self-call.
      return self.get(data, check, mutator)


class TimelinePage(GCIRequestHandler):
  """View for the participant profile."""

  def djangoURLPatterns(self):
    return [
        url(r'timeline/%s$' % url_patterns.PROGRAM, self,
            name='edit_gci_timeline'),
        url(r'timeline/edit/%s$' % url_patterns.PROGRAM, self),
    ]

  def checkAccess(self):
    self.check.isHost()

  def templatePath(self):
    return 'v2/modules/gci/timeline/base.html'

  def context(self):
    timeline_form = TimelineForm(self.data.POST or None,
                                 instance=self.data.program_timeline)
    return {
        'page_name': 'Edit program timeline',
        'forms': [timeline_form],
        'error': timeline_form.errors,
    }

  def validate(self):
    timeline_form = TimelineForm(self.data.POST,
                                instance=self.data.program_timeline)

    if timeline_form.is_valid():
      timeline_form.save()
      return True
    else:
      return False

  def post(self, data, check, mutator):
    """Handler for HTTP POST request."""
    if self.validate():
      data.redirect.program()
      return data.redirect.to('edit_gci_timeline', validated=True)
    else:
      # TODO(nathaniel): problematic self-call.
      return self.get(data, check, mutator)


class GCIProgramMessagesPage(
    program_view.ProgramMessagesPage, GCIRequestHandler):
  """View for the content of GCI program specific messages to be sent."""

  def djangoURLPatterns(self):
    return [
        url(r'program/messages/edit/%s$' % url_patterns.PROGRAM, self,
            name=self._getUrlName()),
    ]

  def templatePath(self):
    return 'v2/modules/gci/program/messages.html'

  def _getForm(self, entity):
    return GCIProgramMessagesForm(
        self.data, self.data.POST or None, instance=entity)

  def _getModel(self):
    return GCIProgramMessages

  def _getUrlName(self):
    return url_names.GCI_EDIT_PROGRAM_MESSAGES
