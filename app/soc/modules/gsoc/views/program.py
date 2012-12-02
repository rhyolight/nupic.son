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

from soc.models import document

from soc.views import program as soc_program_view
from soc.views.helper import url_patterns as soc_url_patterns

from soc.modules.gsoc.models import program
from soc.modules.gsoc.models import timeline
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views import forms
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper import url_patterns


class TimelineForm(forms.GSoCModelForm):
  """Django form to edit timeline settings."""

  class Meta:
    css_prefix = 'timeline_form'
    model = timeline.GSoCTimeline
    exclude = ['link_id', 'scope', 'scope_path']


class ProgramForm(forms.GSoCModelForm):
  """Django form for the program settings."""

  def __init__(self, request_data, *args, **kwargs):
    self.request_data = request_data
    super(ProgramForm, self).__init__(*args, **kwargs)

  class Meta:
    css_prefix = 'program_form'
    model = program.GSoCProgram
    exclude = ['link_id', 'scope', 'scope_path', 'timeline',
               'home', 'slots_allocation', 'student_max_age',
               'min_slots']


class GSoCProgramMessagesForm(forms.GSoCModelForm):
  """Django form for the program settings."""

  def __init__(self, request_data, *args, **kwargs):
    self.request_data = request_data
    super(program.GSoCProgramMessagesForm, self).__init__(*args, **kwargs)

  class Meta:
    css_prefix = 'program_messages_form'
    model = program.GSoCProgramMessages


class ProgramPage(base.GSoCRequestHandler):
  """View for the program profile."""

  def djangoURLPatterns(self):
    return [
        url_patterns.url(r'program/%s$' % soc_url_patterns.PROGRAM, self,
            name='edit_gsoc_program'),
        url_patterns.url(r'program/edit/%s$' % soc_url_patterns.PROGRAM, self),
    ]

  def jsonContext(self):
    q = document.Document.all()
    q.filter('prefix', 'gsoc_program')
    q.filter('scope', self.data.program.key())

    data = [{'key': str(i.key()),
            'key_name': i.key().name(),
            'label': i.title}
            for i in q]

    return {'data': data}

  def checkAccess(self):
    self.check.isHost()

  def templatePath(self):
    return 'v2/modules/gsoc/program/base.html'

  def context(self):
    scope_path = self.data.program.key().id_or_name()
    program_form = ProgramForm(self.data, self.data.POST or None,
                               instance=self.data.program)
    return {
        'page_name': 'Edit program settings',
        'forms': [program_form],
        'error': program_form.errors,
    }

  def validate(self):
    scope_path = self.data.program.key().id_or_name()
    program_form = ProgramForm(self.data, self.data.POST,
                               instance=self.data.program)

    if program_form.is_valid():
      program_form.save()
      return True
    else:
      return False

  def post(self):
    """Handler for HTTP POST request."""
    cbox = bool(self.data.GET.get('cbox'))

    if self.validate():
      self.redirect.program()
      self.redirect.to('edit_gsoc_program', validated=True, cbox=cbox)
    else:
      self.get()


class TimelinePage(base.GSoCRequestHandler):
  """View for the participant profile."""

  def djangoURLPatterns(self):
    return [
        url_patterns.url(r'timeline/%s$' % soc_url_patterns.PROGRAM, self,
            name='edit_gsoc_timeline'),
        url_patterns.url(r'timeline/edit/%s$' % soc_url_patterns.PROGRAM, self),
    ]

  def checkAccess(self):
    self.check.isHost()

  def templatePath(self):
    return 'v2/modules/gsoc/timeline/base.html'

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

  def post(self):
    """Handler for HTTP POST request."""
    cbox = bool(self.data.GET.get('cbox'))

    if self.validate():
      self.redirect.program()
      self.redirect.to('edit_gsoc_timeline', validated=True, cbox=cbox)
    else:
      self.get()


class GSoCProgramMessagesPage(
    soc_program_view.ProgramMessagesPage, base.GSoCRequestHandler):
  """View for the content of GSoC program specific messages to be sent."""

  def djangoURLPatterns(self):
    return [
        url_patterns.url(
            r'program/messages/edit/%s$' % soc_url_patterns.PROGRAM, self,
            name=self._getUrlName()),
    ]

  def templatePath(self):
    return 'v2/modules/gsoc/program/messages.html'

  def _getForm(self, entity):
    return program.GSoCProgramMessagesForm(self.data, self.data.POST or None,
        instance=entity)

  def _getModel(self):
    return program.GSoCProgramMessages

  def _getUrlName(self):
    return url_names.GSOC_EDIT_PROGRAM_MESSAGES
