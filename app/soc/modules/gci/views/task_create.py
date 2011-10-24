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

"""Views for creating/editing GCI Tasks.
"""

__authors__ = [
  '"Madhusudan.C.S" <madhusudancs@gmail.com>',
  '"Selwyn Jacob" <selwynjacob90@gmail.com>',
  ]


import datetime

from django import forms as django_forms
from django.utils.translation import ugettext

from soc.logic import cleaning
from soc.views import forms
from soc.views.helper import url_patterns

from soc.modules.gci.models import task
from soc.modules.gci.models.organization import GCIOrganization
from soc.modules.gci.models.profile import GCIProfile
from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.base import RequestHandler
from soc.modules.gci.views.helper.url_patterns import url


class TaskCreateForm(gci_forms.GCIModelForm):
  """Django form for the task creation page.
  """

  tags = django_forms.CharField(
      label=ugettext('Tags'),
      help_text=ugettext('Describe this task with tags (comma separated). '
                         'Ex: Linux, Apache, C++, GUI'))

  time_to_complete_days = django_forms.IntegerField(
      label=ugettext('Time to complete'), min_value=0,
      error_messages={'min_value': ugettext('Days cannot be negative.')})

  time_to_complete_hours = django_forms.IntegerField(
      label=ugettext('Time to complete'), min_value=0,
      error_messages={'min_value': ugettext('Hours cannot be negative.')})

  def __init__(self, data, *args, **kwargs):
    super(TaskCreateForm, self).__init__(*args, **kwargs)

    self.request_data = data

    # get a list difficulty levels stored for the program entity
    difficulties = task.TaskDifficultyTag.get_by_scope(data.program)

    task_difficulties = []
    for difficulty in difficulties:
      task_difficulties.append((difficulty.tag, difficulty.tag))

    self.fields['difficulty'] = django_forms.ChoiceField(
        label=ugettext('Difficulty'), choices=task_difficulties)

    # get a list of task type tags stored for the program entity
    type_tags = task.TaskTypeTag.get_by_scope(data.program)

    task_type_tags = []
    for type_tag in type_tags:
      task_type_tags.append((type_tag.tag, type_tag.tag))

    self.fields['task_type'] = django_forms.MultipleChoiceField(
        label=ugettext('Type'), choices=task_type_tags,
        widget=forms.CheckboxSelectMultiple)

    if self.instance:
      difficulties = self.instance.difficulty
      if difficulties:
        self.fields['difficulty'].initial = difficulties[0].tag

      task_types = self.instance.task_type
      if task_types:
        self.fields['task_type'].initial = [t.tag for t in task_types]

      self.fields['tags'].initial = self.instance.tags_string(
          self.instance.arbit_tag)

      ttc = datetime.timedelta(hours=self.instance.time_to_complete)
      self.fields['time_to_complete_days'].initial = ttc.days
      self.fields['time_to_complete_hours'].initial = ttc.seconds / 3600

#    self.fields['mentors'] = django_forms.ChoiceField(
#        widget=django_forms.MultipleHiddenInput(), choices=)

    # Bind all the fields here to boundclass since we do not iterate
    # over the fields using iterator for this form.
    self.bound_fields = {}
    for name, field in self.fields.items():
      self.bound_fields[name] = gci_forms.GCIBoundField(self, field, name)

  def _save_extras(self, entity):
    entity.difficulty = {
        'tags': self.cleaned_data['difficulty'],
        'scope': self.request_data.program,
        }
    entity.task_type = {
        'tags': self.cleaned_data['task_type'],
        'scope': self.request_data.program,
        }
    entity.arbit_tag = {
        'tags': self.cleaned_data['tags'],
        'scope': self.request_data.program,
        }

  def create(self, commit=True, key_name=None, parent=None):
    entity = super(TaskCreateForm, self).create(
        commit=False, key_name=key_name, parent=parent)

    if entity:
      self._save_extras(entity)

    if commit:
      entity.put()

    # organization and status are in this create method and not in cleaner
    # because we want to store it in the entity only when it is created an
    # not while editing.
    organization = self.request_data.organization
    entity.org = organization

    if organization.key() in self.request_data.org_admin_for:
      entity.status = 'Unpublished'
    elif organization.key() in self.request_data.mentor_for:
      entity.status = 'Unapproved'

    if entity:
      self._save_extras(entity)

    return entity

  def save(self, commit=True):
    entity = super(TaskCreateForm, self).save(commit=False)

    if commit:
      entity.put()

    return entity

  clean_description = cleaning.clean_html_content('description')

  def clean(self):
    super(TaskCreateForm, self).clean()

    cleaned_data = self.cleaned_data
    ttc_days = cleaned_data.get("time_to_complete_days", 0)
    ttc_hours = cleaned_data.get("time_to_complete_hours", 0)

    if ttc_days or ttc_hours:
      cleaned_data['time_to_complete'] = ttc_days * 24 + ttc_hours
    else:
      raise django_forms.ValidationError(
          ugettext('Time to complete must be specified.'))

    cleaned_data['program'] = self.request_data.program

    return cleaned_data

  def clean_mentors(self):
    program_key_name = self.request_data.program.key().name()

    mentor_link_ids = self.cleaned_data['mentors']
    split_link_ids = mentor_link_ids.split(',')

    for link_id in split_link_ids:
      link_id = link_id.strip()
      mentor_key_name = '%s/%s' % (program_key_name, link_id)
      mentor_entity = GCIProfile.get_by_key_name(mentor_key_name)
      if self.request_data.organization.key() not in mentor_entity.mentor_for:
        raise django_forms.ValidationError(
            "link id %s is not a valid mentor" % (link_id))

    return mentor_link_ids

  class Meta:
    model = task.GCITask
    css_prefix = 'gci-task'
    fields = ['title', 'description', 'difficulty' , 'task_type', 'arbit_tag']


class TaskCreatePage(RequestHandler):
  """View to create a new task.
  """

  def djangoURLPatterns(self):
    return [
        url(r'task/create/%s$' % url_patterns.ORG,
            self, name='gci_create_task'),
        url(r'task/edit/%s$' % url_patterns.ID,
            self, name='gci_edit_task'),
    ]

  def checkAccess(self):
    self.mutator.taskFromKwargsIfId()

    self.check.isLoggedIn()

  def templatePath(self):
    return 'v2/modules/gci/task_create/base.html'

  def context(self):
    if self.data.task:
      form = TaskCreateForm(self.data, self.data.POST or None,
                            instance=self.data.task)
      page_name = "Edit task - %s" % (self.data.task.title)
    else:
      form = TaskCreateForm(self.data, self.data.POST or None)
      page_name = "Create a new task"

    context = {
      'page_name':  page_name,
      'form': form,
      'error': form.errors,
    }

    return context

  def createTaskFromForm(self):
    """Creates a new task based on the data inserted in the form.

    Returns:
      a newly created task entity or None.
    """
    if self.data.task:
      form = TaskCreateForm(self.data, self.data.POST,
                            instance=self.data.task)
    else:
      form = TaskCreateForm(self.data, self.data.POST)

    if not form.is_valid():
      return None

    if not self.data.task:
      entity = form.create(commit=True)
    else:
      entity = form.save(commit=True)

    return entity

  def post(self):
    task = self.createTaskFromForm()
    if task:
      r = self.redirect.id(id=task.key().id_or_name())
      r.to('gci_edit_task', validated=True)
    else:
      self.get()
