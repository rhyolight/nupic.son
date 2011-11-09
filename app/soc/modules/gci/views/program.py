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

"""Module for the program settings pages.
"""

__authors__ = [
  '"Sverre Rabbelier" <sverre@rabbelier.nl>',
  ]


from google.appengine.ext import db

from django import forms as django_forms
from django.utils import simplejson as json
from django.utils.translation import ugettext

from soc.logic import tags as tags_logic
from soc.models.document import Document
from soc.views import forms
from soc.views.helper import url_patterns

from soc.modules.gci.models.program import GCIProgram
from soc.modules.gci.models.task import TaskDifficultyTag
from soc.modules.gci.models.task import TaskTypeTag
from soc.modules.gci.models.timeline import GCITimeline
from soc.modules.gci.views.base import RequestHandler
from soc.modules.gci.views.forms import GCIModelForm
from soc.modules.gci.views.helper.url_patterns import url


class TimelineForm(GCIModelForm):
  """Django form to edit timeline settings.
  """

  class Meta:
    css_prefix = 'timeline_form'
    model = GCITimeline
    exclude = ['link_id', 'scope', 'scope_path']


class ProgramForm(GCIModelForm):
  """Django form for the program settings.
  """

  def __init__(self, scope_path, *args, **kwargs):
    self.scope_path = scope_path
    super(ProgramForm, self).__init__(*args, **kwargs)

    if self.instance:
      difficulty_tags = tags_logic.getTagsForProgram(
          TaskDifficultyTag, self.instance, order=['order'])
      self.task_difficulties_json = json.dumps(
          [[t.tag, t.value] for t in difficulty_tags])

      type_tags = tags_logic.getTagsForProgram(
          TaskTypeTag, self.instance, order=['order'])
      self.task_types_json = json.dumps([[t.tag] for t in type_tags])


  class Meta:
    css_prefix = 'program_form'
    model = GCIProgram
    exclude = ['link_id', 'scope', 'scope_path', 'timeline', 'home',
               'slots_allocation']

    widgets = forms.hiddenWidgets(
        GCIProgram, ['task_difficulties', 'task_types'])


class ProgramPage(RequestHandler):
  """View for the program profile.
  """

  def djangoURLPatterns(self):
    return [
        url(r'program/%s$' % url_patterns.PROGRAM, self,
            name='edit_gci_program'),
        url(r'program/edit/%s$' % url_patterns.PROGRAM, self),
    ]

  def jsonContext(self):
    q = Document.all()
    q.filter('prefix', 'gci_program')
    q.filter('scope', self.data.program.key())

    data = [{'key': str(i.key()),
            'key_name': i.key().name(),
            'label': i.title}
            for i in q]

    return {'data': data}

  def checkAccess(self):
    self.check.isHost()

  def templatePath(self):
    return 'v2/modules/gci/program/base.html'

  def context(self):
    scope_path = self.data.program.key().id_or_name()
    program_form = ProgramForm(scope_path, self.data.POST or None,
                               instance=self.data.program)
    return {
        'page_name': 'Edit program settings',
        'forms': [program_form],
        'error': program_form.errors,
    }

  def validate(self):
    program = self.data.program
    to_put = []

    scope_path = program.key().id_or_name()
    program_form = ProgramForm(scope_path, self.data.POST, instance=program)

    if not program_form.is_valid():
      return False

    task_difficulties = self.data.POST.getlist('task_difficulty_name')
    task_difficulties_values = self.data.POST.getlist(
        'task_difficulty_value')

    try:
      difficulties_dict = dict(
          (name, {'value': int(value), 'order': i}) for i, (name, value)
               in enumerate(zip(task_difficulties, task_difficulties_values)))
    except ValueError:
        raise django_forms.ValidationError(
          ugettext('The value %s for the tag must be an integer.' % (
              value)))

    difficulty_tags = tags_logic.getTagsForProgram(TaskDifficultyTag, program)

    for tag in difficulty_tags:
      tag_name = tag.tag

      if tag_name not in difficulties_dict:
        continue

      new_value = difficulties_dict.get(tag_name).get('value')
      new_order = difficulties_dict.get(tag_name).get('order')

      difficulties_dict.pop(tag_name)

      if new_value == tag.value and new_order == tag.order:
        continue

      tag.value = new_value
      tag.order = new_order
      to_put.append(tag)

    for name, props in difficulties_dict.items():
      to_put.append(TaskDifficultyTag(
          scope=program, tag=name, value=props.get('value'),
          order=props.get('order')))


    task_types = self.data.POST.getlist('task_type_name')

    types_dict = dict((name, i) for i, name in enumerate(task_types))

    type_tags = tags_logic.getTagsForProgram(TaskTypeTag, program)

    for tag in type_tags:
      tag_name = tag.tag

      if tag_name not in types_dict:
        continue

      new_order = types_dict.pop(tag_name)

      if new_order == tag.order:
        continue

      tag.order = new_order
      to_put.append(tag)

    for name, order in types_dict.items():
      to_put.append(TaskTypeTag(scope=program, tag=name, order=order))

    program_form.save()
    db.put(to_put)

    return True

  def post(self):
    """Handler for HTTP POST request.
    """
    if self.data.GET.get('cbox'):
      cbox = True
    else:
      cbox = False

    if self.validate():
      self.redirect.program()
      self.redirect.to('edit_gci_program', validated=True, cbox=cbox)
    else:
      self.get()


class TimelinePage(RequestHandler):
  """View for the participant profile.
  """

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

    if not timeline_form.is_valid():
      return False

    timeline_form.save()
    return True

  def post(self):
    """Handler for HTTP POST request.
    """
    if self.data.GET.get('cbox'):
      cbox = True
    else:
      cbox = False

    if self.validate():
      self.redirect.program()
      self.redirect.to('edit_gci_timeline', validated=True, cbox=cbox)
    else:
      self.get()
