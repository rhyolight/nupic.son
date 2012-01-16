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

  def __init__(self, data, *args, **kwargs):
    self.request_data = data

    super(ProgramForm, self).__init__(*args, **kwargs)

    if self.instance:
      difficulty_tags = tags_logic.getTagsForProgram(
          TaskDifficultyTag, self.instance, order=['order'])
      self.task_difficulties_json = json.dumps(
          [[t.tag, t.value] for t in difficulty_tags])

      self.task_types_json = json.dumps(self.instance.task_types)

  class Meta:
    css_prefix = 'program_form'
    model = GCIProgram
    exclude = ['link_id', 'scope', 'scope_path', 'timeline', 'home',
               'slots_allocation', 'task_difficulties', 'task_types']

  def clean_difficulty(self):
    """Retrieve and validate task difficulty tags and its value from the form.
    """
    program = self.request_data.program
    to_put = []

    task_difficulties = self.request_data.POST.getlist('task_difficulty_name')
    task_difficulties_values = self.request_data.POST.getlist(
        'task_difficulty_value')

    try:
      difficulties_dict = dict(
          (name, {'value': int(value), 'order': i}) for i, (name, value)
               in enumerate(zip(task_difficulties, task_difficulties_values)))
    except ValueError:
        raise forms.ValidationError(
          ugettext('The value for the tag must be an integer.'))

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

    scope_path = program.key().id_or_name()

    for name, props in difficulties_dict.items():
      to_put.append(TaskDifficultyTag(
          key_name=TaskDifficultyTag._key_name(scope_path, name),
          scope=program, tag=name, value=props.get('value'),
          order=props.get('order')))

    self.cleaned_data['task_difficulty_entities'] = to_put

  def clean(self):
    """Cleans the data input by the user as a response to the form.

    Here we populate the tags that are dynamically added using Javascript
    in the form and do some validation on the tags. We cannot just assume
    that the clean_* methods are called on difficulty and task_types because
    they are not defined fields in the Django's form. In fact they are
    excluded from the actual model form. So we will have to explicitly call
    their cleaners.
    """
    super(ProgramForm, self).clean()

    self.clean_difficulty()

    self.cleaned_data['task_types'] = self.request_data.POST.getlist(
        'task_type_name')

    return self.cleaned_data

  def save(self):
    """Save the form along with the tags.
    """
    super(ProgramForm, self).save()

    # Note the dictionary keys for tags, i.e. task_difficulty_entities and
    # task_type_entities is not the same as corresponding property names in
    # the GCITask model so these values won't be stored when we call
    # form.save() and hence we extend it here.
    #
    # Also purposefully make the key names different because we do not want
    # the ModelForm code to save these entities since the corresponding
    # properties are not regular Appengine property types. So we are happy
    # handling them separately!
    db.put(
        self.cleaned_data['task_difficulty_entities'])


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
    program_form = ProgramForm(self.data, self.data.POST or None,
                               instance=self.data.program)
    return {
        'page_name': 'Edit program settings',
        'forms': [program_form],
        'error': program_form.errors,
    }

  def validate(self):
    program_form = ProgramForm(self.data, self.data.POST,
                               instance=self.data.program)

    if not program_form.is_valid():
      return False

    program_form.save()

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
