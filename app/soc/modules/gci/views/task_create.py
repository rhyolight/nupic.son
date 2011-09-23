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

"""Module for the GCI Task creation page.
"""

__authors__ = [
  '"Selwyn Jacob" <selwynjacob90@gmail.com>',
  ]


import time

from google.appengine.ext import db

from django import forms as djang_forms
from django.utils.translation import ugettext

from soc.logic import cleaning
from soc.logic.exceptions import AccessViolation
from soc.logic.helper import notifications
from soc.views import forms
from soc.tasks import mailer

from soc.modules.gci.models import task
from soc.modules.gci.views.base import RequestHandler
from soc.modules.gci.views.base_templates import LoggedInMsg
from soc.modules.gci.views.helper import url_patterns

class CreateTaskForm(forms.ModelForm):
  """Django form for the task creation page.
  """

  class Meta:
    model = task.GCITask
    css_prefix = 'gci_task'
    exclude = ['mentors', 'user', 'student', 'program', 'closed_on',
        'deadline', 'created_by', 'created_on', 'modified_by',
        'modified_on', 'history']

    widgets = forms.choiceWidgets(task.GCITask,
        ['difficulty', 'task_type'])

  time_to_complete_days = django_forms.IntegerField()
  clean_description = cleaning.clean_html_content('description')

  def __init__(self, request_data, *args, **kwargs):
    super(CreateTaskForm, self).__init__(*args, **kwargs)
    self_request_data = request_data

  def clean_mentors(self):
    program_key_name = self.request_data.program.key().name()

    mentor_link_ids = form.cleaned_data['mentors']
    split_link_ids = mentor_link_ids.split(',')

    for link_id in split_link_ids:
      link_id = link_id.strip()
      mentor_key_name = '%s/%s' % (program_key_name, link_id)
      mentor_entity = db.get_by_key_name(mentor_key_name)
      if self.request_data.organization.key() not in mentor_entity.mentor_for:
        raise django_forms.ValidationError(
            "link id %s is not a valid mentor" % (link_id))

    return mentor_link_ids

class CreateTaskPage(RequestHandler):
  """View to create a new task.
  """

  def djangoURLPatterns(self):
    return [
        url(r'task/create/%s$' % url_patterns.ORG,
            self, name='gci_create_task'),
    ]

  def checkAccess(self):
    self.check.isLoggedIn()
    self.mutator.organiationFromKwargs()
    self.check.isMentorForOrganization(self.data.organization)

  def templatePath(self):
    return 'v2/modules/gci/task/create.html'

  def context(self):
    if self.data.task:
      form = CreateTaskFrom(self.data.POST or None,
                                       instance=self.data.task)
      page_name = "Edit task"
    else:
      form = CreateTaskForm(self.data.POST or None)
      page_name = "Create task"
    error = form.errors

    org_entity = self.data.organization

    # get a list difficulty levels stored for the program entity
    task_difficulty_tags = task.TaskDifficultyTag.get_by_scope(org_entity.scope)
    form.fields['difficulties'] = [(d.tag, d.tag) for d in task_difficulty_tags]

    # get a list of task type tags stored for the program entity
    task_type_tags = task.TaskTypeTag.get_by_scope(org_entity.scope)
    form.fields['task_type'] = [(t.tag, t.tag) for t in task_type_tags]

    context = {
      'page_name':  page_name,
      'form_top_msg': LoggedInMsg(self.data, apply_link=False),
      'form': [form],
      'error': error,
    }

    return context

    def post(self):
      task = creatTaskFromForm()
      if task:
        self.redirect.to('gci_show_task', validated=True)
      else:
        self.get()

    def putWithMentors(self, form, entity):
      program_key_name = self.request_data.program.key().name()

      mentor_link_ids = form.cleaned_data['mentors']
      split_link_ids = mentor_link_ids.split(',')

      #The creator of the task automatically becomes a mentor
      mentors_keys = [self.data.url_user.key()]
      for link_id in split_link_ids:
        link_id = link_id.strip()
        mentor_key_name = '%s/%s' % (program_key_name, link_id)
        mentor_entity = db.get_by_key_name(mentor_key_name)
        mentors_keys.append(mentor_entity.key())

      entity.mentors = mentors_keys

      entity.put()

    def createTaskFromForm(self):
      """Creates a new task based on the data inserted in the form.

      Returns:
        a newly created task entity or None.
      """
      if self.data.task:
        form = CreatTaskForm(self.data.POST, instance=self.data.task)
      else:
        form = CreateTaskForm(self.data.POST)

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

