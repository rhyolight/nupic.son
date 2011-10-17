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

"""Views for the GCI Task view page.
"""

__authors__ = [
  '"Madhusudan.C.S" <madhusudancs@gmail.com>',
  '"Selwyn Jacob" <selwynjacob90@gmail.com>',
  '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]


import datetime

from google.appengine.ext import db

from django.utils.translation import ugettext
from django import forms as django_forms

from soc.logic import cleaning
from soc.views.template import Template

from soc.modules.gci.logic import comment as comment_logic
from soc.modules.gci.logic import task as task_logic
from soc.modules.gci.models.comment import GCIComment
from soc.modules.gci.models.task import ACTIVE_CLAIMED_TASK
from soc.modules.gci.models.task import UPLOAD_ALLOWED
from soc.modules.gci.models.task import SEND_FOR_REVIEW_ALLOWED
from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.base import RequestHandler
from soc.modules.gci.views.helper import url_patterns
from soc.modules.gci.views.helper.url_patterns import url


class CommentForm(gci_forms.GCIModelForm):
  """Django form for the comment.
  """

  class Meta:
    model = GCIComment
    css_prefix = 'gci_comment'
    fields = ['title', 'content']

  def __init__(self, *args, **kwargs):
    super(CommentForm, self).__init__(*args, **kwargs)

    # For UI purposes we need to set this required, validation does not pick
    # it up.
    self.fields['title'].required = True
    self.fields['content'].required = True

  def clean_content(self):
    content = cleaning.clean_html_content('content')(self)
    if content:
      return content
    else:
      raise django_forms.ValidationError(
          ugettext('Comment content cannot be empty.'), code='invalid')

  def clean_title(self):
    title = self.cleaned_data.get('title')

    if not title:
      raise django_forms.ValidationError(
          ugettext('Comment title cannot be empty.'), code='invalid')

    return title


class TaskViewPage(RequestHandler):
  """View for the GCI Task view page where all the actions happen.
  """

  def djangoURLPatterns(self):
    """URL pattern for this view.
    """
    return [
        url(r'task/view/%s$' % url_patterns.TASK, self, name='gci_view_task'),
    ]

  def checkAccess(self):
    """Checks whether this task is visible to the public and any other checks
    if it is a POST request.
    """
    self.mutator.taskFromKwargs(comments=True, work_submissions=True)
    self.check.isTaskVisible()

    if self.request.method == 'POST':
      # Access checks for the different forms on this page. Note that there
      # are no elif clauses because one could add multiple GET params :).

      if 'post_comment' in self.data.GET:
        # checks for posting comments
        # TODO(ljvderijk): isProgramRunning might not be strict enough
        self.check.isProgramRunning()
        self.check.isProfileActive()

      if 'submit_work' in self.data.GET:
        # TODO(ljvderijk): Checks for submitting work
        pass

  def context(self):
    """Returns the context for this view.
    """
    task = self.data.task

    context = {
      'page_name': '%s - %s' %(task.title, task.org.name),
      'task': task,
      'is_mentor': self.data.mentorFor(task.org),
      'task_info': TaskInformation(self.data),
      'work_submissions': WorkSubmissions(self.data),
      'comments': CommentsTemplate(self.data),
    }

    if not context['is_mentor']:
      # Programmatically change css for non-mentors, to for instance show
      # the open cog when a task can be claimed.
      if task.status == 'Closed':
        block_type = 'completed'
      elif task_logic.isOwnerOfTask(task, self.data.profile):
        block_type = 'owned'
      elif task.status in ACTIVE_CLAIMED_TASK:
        block_type = 'claimed'
      else:
        block_type = 'open'
      context['block_task_type'] = block_type

    return context

  def post(self):
    """Handles all POST calls for the TaskViewPage.
    """
    if 'post_comment' in self.data.GET:
      return self._postComment()
    else:
      self.error(405)

  def _postComment(self):
    """Handles the POST call for the form that creates comments.
    """
    comment_form = CommentForm(self.data.POST)

    if not comment_form.is_valid():
      return self.get()

    comment_form.cleaned_data['created_by'] = self.data.user
    comment_form.cleaned_data['modified_by'] = self.data.user

    comment = comment_form.create(commit=False, parent=self.data.task)
    comment_logic.storeAndNotify(comment)

    # TODO(ljvderijk): Indicate that a comment was successfully created to the
    # user.
    self.redirect.id().to('gci_view_task')

  def templatePath(self):
    return 'v2/modules/gci/task/public.html'


class TaskInformation(Template):
  """Template that contains the details of a task.
  """

  def context(self):
    """Returns the context for the current template.
    """
    task = self.data.task
    mentors = [m.public_name for m in db.get(task.mentors)]

    # We count everyone from the org as a mentor, the mentors property
    # is just who best to contact about this task
    context = {
        'task': task,
        'mentors': mentors,
        'is_mentor': self.data.mentorFor(task.org),
        'is_owner': task_logic.isOwnerOfTask(task, self.data.profile),
        'is_claimed': task.status in ACTIVE_CLAIMED_TASK,
        'profile': self.data.profile,
    }

    if task.deadline:
      # TODO(ljvderijk): investigate django.utils.timesince.timeuntil
      # special formatting of the TimeDelta object for task view
      now = datetime.datetime.utcnow()
      time_remaining = task.deadline - now
      context['now'] = now
      context['remaining_days'] = time_remaining.days
      context['remaining_hours'] = time_remaining.seconds/3600
      context['remaining_minutes'] = (time_remaining.seconds/60)%60

    self.setButtonControls(context)

    return context

  def setButtonControls(self, context):
    """Enables buttons on the TaskInformation block based on status and the
    user.

    Args:
      context: Context dictionary which to write to.
    """
    profile = self.data.profile
    if not profile:
      # no buttons for someone without a profile
      return

    if self.data.timeline.allWorkStopped():
      # no buttons after all worked has stopped
      return

    task = self.data.task

    is_org_admin = self.data.orgAdminFor(task.org)
    is_mentor = self.data.mentorFor(task.org)
    is_student = self.data.is_student
    is_owner = task_logic.isOwnerOfTask(task, profile)

    if is_org_admin:
      if task.status == 'Open' and not self.data.comments:
        # tasks may be removed as long as there is no comment or claim
        context['button_unpublish'] = True
        context['button_delete'] = True

    if is_mentor:
      context['button_edit'] = task.status == 'Open' and not self.data.comments
      context['button_assign'] = task.status == 'ClaimRequested'
      context['button_unassign'] = task.status in ACTIVE_CLAIMED_TASK
      context['button_close_task'] = task.status == 'NeedsReview'
      context['button_extend_deadline'] = task.status == 'NeedsReview'

    if is_student:
      if self.data.timeline.tasksClaimEnded():
        context['button_claim'] = task_logic.canClaimRequestTask(task,
                                                                 profile.user)

    if is_owner:
      context['button_unclaim'] = task.status in ACTIVE_CLAIMED_TASK

    if task.status != 'Closed':
      context['button_subscribe'] = not profile.key() in task.subscribers
      context['button_unsubscribe'] = profile.key() in task.subscribers

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return 'v2/modules/gci/task/_task_information.html'


class WorkSubmissions(Template):
  """Template to render all the GCIWorkSubmissions.

  Contains the form to upload work and contains the "Mark task as complete"
  button for students.
  """

  def context(self):
    """Returns the context for the current template.
    """
    context = {'submissions': self.data.work_submissions}

    task = self.data.task
    is_owner = task_logic.isOwnerOfTask(task, self.data.profile)

    if is_owner:
      context['send_for_review'] = self.data.work_submissions and \
          task.status in SEND_FOR_REVIEW_ALLOWED

      if task.status in UPLOAD_ALLOWED:
        # Add the form for allowing uploads
        context['upload_form'] = True

    return context

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return 'v2/modules/gci/task/_work_submissions.html'


class CommentsTemplate(Template):
  """Template for rendering and adding comments.
  """

  def context(self):
    """Returns the context for the current template.
    """
    context = {
        'profile': self.data.profile,
        'comments': self.data.comments,
        'login': self.data.redirect.login().url(),
        'student_reg_link': self.data.redirect.createProfile('student')
            .urlOf('create_gci_profile'),
    }

    if self.data.task.status != 'Closed':
      if self.data.POST and 'post_comment' in self.data.GET:
        context['comment_form'] = CommentForm(self.data.POST)
      else:
        context['comment_form'] = CommentForm()

    return context

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return 'v2/modules/gci/task/_comments.html'


class PostUploadWork(RequestHandler):
  """View which handles posting WorkSubmissions.
  """

  def djangoURLPatterns(self):
    return [
        url_patterns.url(r'task/submit_work/%s$' % url_patterns.TASK,
            self, name='gci_task_submit_work'),
    ]

  def get(self):
    """Special Handler for HTTP GET request since this view only handles POST.
    """
    self.error(405)
