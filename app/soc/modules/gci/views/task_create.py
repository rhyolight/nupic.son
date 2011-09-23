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


import time

from django import forms as django_forms
from django.utils.translation import ugettext

from soc.logic import cleaning
from soc.views import forms
from soc.views.helper import url_patterns

from soc.modules.gci.models import task
from soc.modules.gci.models.profile import GCIProfile
from soc.modules.gci.views.base import RequestHandler
from soc.modules.gci.views.base_templates import LoggedInMsg
from soc.modules.gci.views.helper.url_patterns import url


class TaskCreateForm(forms.ModelForm):
  """Django form for the task creation page.
  """

  tags = django_forms.CharField(label=ugettext('Tags'))

  time_to_complete_days = django_forms.IntegerField(
      label=ugettext('Time to complete'))

  time_to_complete_hours = django_forms.IntegerField(
      label=ugettext('Time to complete'))

  def __init__(self, data, *args, **kwargs):
    super(TaskCreateForm, self).__init__(*args, **kwargs)

    # get a list difficulty levels stored for the program entity
    difficulties = task.TaskDifficultyTag.get_by_scope(data.program)

    task_difficulties = []
    for difficulty in difficulties:
      task_difficulties.append((difficulty.tag, difficulty.tag))

    self.fields['difficulties'] = django_forms.ChoiceField(
        label=ugettext('Difficulty'), choices=task_difficulties)

    # get a list of task type tags stored for the program entity
    type_tags = task.TaskTypeTag.get_by_scope(data.program)

    task_type_tags = []
    for type_tag in type_tags:
      task_type_tags.append((type_tag.tag, type_tag.tag))

    self.fields['task_type'] = django_forms.MultipleChoiceField(
        label=ugettext('Type'), choices=task_type_tags,
        widget=forms.CheckboxSelectMultiple)

    org_choices = []
    for org in set(data.org_admin_for + data.mentor_for):
      org_choices.append((org.link_id, org.name))

    self.fields['organization'] = django_forms.ChoiceField(
        label=ugettext('Organization'), choices=org_choices)

#    self.fields['mentors'] = django_forms.ChoiceField(
#        widget=django_forms.MultipleHiddenInput(), choices=)

  class Meta:
    model = task.GCITask
    css_prefix = 'gci_task'
    fields = ['title', 'description', 'difficulty' , 'task_type', 'arbit_tag']

  clean_description = cleaning.clean_html_content('description')

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


class TaskCreatePage(RequestHandler):
  """View to create a new task.
  """

  def djangoURLPatterns(self):
    return [
        url(r'task/create/%s$' % url_patterns.PROGRAM,
            self, name='gci_create_task'),
    ]

  def checkAccess(self):
    self.mutator.taskFromKwargsIfId()

    self.check.isLoggedIn()

  def templatePath(self):
    return 'v2/modules/gci/task/create.html'

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
      'form_top_msg': LoggedInMsg(self.data, apply_link=False),
      'forms': [form],
      'error': form.errors,
    }


    return context

  def putWithMentors(self, form, entity):
    program_key_name = self.request_data.program.key().name()

    mentor_link_ids = form.cleaned_data['mentors']
    split_link_ids = mentor_link_ids.split(',')

    #The creator of the task automatically becomes a mentor
    mentors_keys = [self.data.url_user.key()]
    for link_id in split_link_ids:
      link_id = link_id.strip()
      mentor_key_name = '%s/%s' % (program_key_name, link_id)
      mentor_entity = GCIProfile.get_by_key_name(mentor_key_name)
      mentors_keys.append(mentor_entity.key())

    entity.mentors = mentors_keys

    entity.put()

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
    task_link_id = 't%i' % (int(time.time()*100))
    if not self.data.task:
      key_name = '%s/%s' % (
          self.data.organization.key.name(),
          task_link_id
          )
      entity = form.create(commit=False, key_name=key_name)
    else:
      entity = form.create(commit=False)

    self.putWithMentors(form, entity)

  def post(self):
    task = self.createTaskFromForm()
    if task:
      self.redirect.to('gci_show_task', validated=True)
    else:
      self.get()
