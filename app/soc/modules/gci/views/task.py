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

from google.appengine.ext import blobstore
from google.appengine.ext import db

from django.utils.translation import ugettext
from django import forms as django_forms

from soc.logic import cleaning
from soc.logic.exceptions import RedirectRequest
from soc.views.helper import blobstore as bs_helper
from soc.views.template import Template

from soc.modules.gci.logic import comment as comment_logic
from soc.modules.gci.logic import task as task_logic
from soc.modules.gci.models.comment import GCIComment
from soc.modules.gci.models.task import ACTIVE_CLAIMED_TASK
from soc.modules.gci.models.task import CLAIMABLE
from soc.modules.gci.models.task import SEND_FOR_REVIEW_ALLOWED
from soc.modules.gci.models.task import TASK_IN_PROGRESS
from soc.modules.gci.models.work_submission import GCIWorkSubmission
from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.base import RequestHandler
from soc.modules.gci.views.helper import url_patterns
from soc.modules.gci.views.helper.url_patterns import url
from soc.modules.gci.views.helper import url_names


DEF_NOT_ALLOWED_TO_OPERATE_BUTTON = ugettext(
    'You are not allowed to operate the button named %s')

DEF_NOT_ALLOWED_TO_UPLOAD_WORK = ugettext(
    'You are not allowed to upload work')

DEF_NO_URL_OR_UPLOAD = ugettext(
    'An error occurred, please use a valid URL or upload a file.')

DEF_NO_WORK_FOUND = ugettext('No submission found with id %i')

DEF_NOT_ALLOWED_TO_DELETE = ugettext(
    'You are not allowed to delete this submission')

DEF_CANT_SEND_FOR_REVIEW = ugettext(
    'Only a task that you own and that has submitted work can be send in '
    'for review.')

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


class WorkSubmissionForm(gci_forms.GCIModelForm):
  """Django form for submitting work.
  """

  class Meta:
    model = GCIWorkSubmission
    css_prefix = 'gci_work_submission'
    fields = ['upload_of_work', 'url_to_work']

  upload_of_work = django_forms.FileField(
      label='Upload work', required=False)

  def clean(self):
    """Ensure that at least one of the fields has data.
    """
    cleaned_data = self.cleaned_data

    upload = cleaned_data.get('upload_of_work')
    url = cleaned_data.get('url_to_work')

    if not (upload or url):
      raise gci_forms.ValidationError(DEF_NO_URL_OR_UPLOAD)

    return cleaned_data


class TaskViewPage(RequestHandler):
  """View for the GCI Task view page where all the actions happen.
  """

  def djangoURLPatterns(self):
    """URL pattern for this view.
    """
    return [
        url(r'task/view/%s$' % url_patterns.TASK, self,
            name=url_names.GCI_VIEW_TASK),
    ]

  def checkAccess(self):
    """Checks whether this task is visible to the public and any other checks
    if it is a POST request.
    """
    self.mutator.taskFromKwargs(comments=True, work_submissions=True)
    self.data.is_visible = self.check.isTaskVisible()

    if task_logic.updateTaskStatus(self.data.task):
      # The task logic updated the status of the task since the deadline passed
      # and the GAE task was late to run. Reload the page.
      raise RedirectRequest('')

    if self.request.method == 'POST':
      # Access checks for the different forms on this page. Note that there
      # are no elif clauses because one could add multiple GET params :).
      self.check.isBeforeAllWorkStopped()
      self.check.isProfileActive()

      if 'post_comment' in self.data.GET:
        # checks for posting comments
        self.check.isTaskNotInStates(['Closed'])

      if 'submit_work' in self.data.GET:
        if not task_logic.canSubmitWork(self.data.task, self.data.profile):
          self.check.fail(DEF_NOT_ALLOWED_TO_UPLOAD_WORK)

      if 'button' in self.data.GET:
        # check for any of the buttons
        button_name = self._buttonName()

        buttons = {}
        TaskInformation(self.data).setButtonControls(buttons)
        if button_name not in buttons:
          self.check.fail(DEF_NOT_ALLOWED_TO_OPERATE_BUTTON %button_name)

      if 'send_for_review' in self.data.GET:
        if not task_logic.isOwnerOfTask(self.data.task, self.data.profile) or \
            not self.data.work_submissions:
          self.check.fail(DEF_CANT_SEND_FOR_REVIEW)

      if 'delete_submission' in self.data.GET:
        id = self._submissionId()
        work = GCIWorkSubmission.get_by_id(id, parent=self.data.task)

        if not work:
          self.check.fail(DEF_NO_WORK_FOUND %id)

        time_expired = work.submitted_on - datetime.datetime.now()
        if work.user.key() != self.data.user.key() or \
            time_expired > task_logic.DELETE_EXPIRATION:
          self.check.fail(DEF_NOT_ALLOWED_TO_DELETE)


  def context(self):
    """Returns the context for this view.
    """
    task = self.data.task

    context = {
      'page_name': '%s - %s' %(task.title, task.org.name),
      'task': task,
      'is_mentor': self.data.mentorFor(task.org),
      'task_info': TaskInformation(self.data),
    }

    if self.data.is_visible:
      context['work_submissions'] = WorkSubmissions(self.data)
      context['comments'] = CommentsTemplate(self.data)

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
    if self.data.is_visible and 'post_comment' in self.data.GET:
      return self._postComment()
    elif 'button' in self.data.GET:
      return self._postButton()
    elif 'submit_work' in self.data.GET:
      return self._postSubmitWork()
    elif 'send_for_review' in self.data.GET:
      return self._postSendForReview()
    elif 'delete_submission' in self.data.GET:
      return self._postDeleteSubmission()
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

  def _postButton(self):
    """Handles the POST call for any of the control buttons on the task page.
    """
    button_name = self._buttonName()
    task = self.data.task
    task_key = task.key()

    if button_name == 'button_unpublish':
      def txn():
        task = db.get(task_key)
        task.status = 'Unpublished'
        task.put()
      db.run_in_transaction(txn)
    elif button_name == 'button_delete':
      task_logic.delete(task)
      self.redirect.homepage().to()
      return
    elif button_name == 'button_assign':
      task_logic.assignTask(task, task.student, self.data.profile)
    elif button_name == 'button_unassign':
      task_logic.unassignTask(task, self.data.profile)
    elif button_name == 'button_close':
      task_logic.closeTask(task, self.data.profile)
    elif button_name == 'button_extend_deadline':
      hours = int(self.data.POST.get('hours', 0))
      if hours > 0:
        delta = datetime.timedelta(hours=hours)
        task_logic.extendDeadline(task, delta, self.data.profile)
    elif button_name == 'button_claim':
      task_logic.claimRequestTask(task, self.data.profile)
    elif button_name == 'button_unclaim':
      task_logic.unclaimTask(task)
    elif button_name == 'button_subscribe':
      profile_key = self.data.profile.key()
      def txn():
        task = db.get(task_key)
        if profile_key not in task.subscribers:
          task.subscribers.append(profile_key)
          task.put()
      db.run_in_transaction(txn)
    elif button_name == 'button_unsubscribe':
      profile_key = self.data.profile.key()
      def txn():
        task = db.get(task_key)
        if profile_key in task.subscribers:
          task.subscribers.remove(profile_key)
          task.put()
      db.run_in_transaction(txn)

    self.redirect.id().to('gci_view_task')

  def _buttonName(self):
    """Returns the name of the button specified in the POST dict.
    """
    for key in self.data.POST.keys():
      if key.startswith('button'):
        return key

    return None

  def _postSubmitWork(self):
    """POST handler for the work submission form.
    """
    form = WorkSubmissionForm(
        data=self.data.POST,
        files=self.data.request.file_uploads)

    if not form.is_valid():
      # we are not storing this form, remove the uploaded blob from the cloud
      for file in self.data.request.file_uploads.itervalues():
        file.delete()

      return self.get()

    task = self.data.task
    # TODO(ljvderijk): Add a non-required profile property?
    form.cleaned_data['user'] = self.data.profile.user
    form.cleaned_data['org'] =  task.org
    form.cleaned_data['program'] = task.program

    # store the submission, parented by the task
    form.create(parent=task)

    return self.redirect.id().to('gci_view_task')

  def _postSendForReview(self):
    """POST handler for the mark as complete button.
    """
    task_logic.sendForReview(self.data.task, self.data.profile)

    self.redirect.id().to('gci_view_task')

  def _postDeleteSubmission(self):
    """POST handler to delete a GCIWorkSubmission.
    """
    id = self._submissionId()
    work = GCIWorkSubmission.get_by_id(id, parent=self.data.task)

    if not work:
      return self.error(400, DEF_NO_WORK_FOUND %id)

    # Deletion of blobs always runs separately from transaction so it has no
    # added value to use it here.
    upload = work.upload_of_work
    work.delete()
    if upload:
      upload.delete()

    self.redirect.id().to('gci_view_task')

  def _submissionId(self):
    """Retrieves the submission id from the POST data.
    """
    for key in self.data.POST.keys():
      if key.isdigit():
        return int(key)

    return -1

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
      can_unpublish = (task.status in CLAIMABLE) and not task.student
      context['button_unpublish'] = can_unpublish
      context['button_delete'] = not task.student

    if is_mentor:
      context['button_assign'] = task.status == 'ClaimRequested'
      context['button_unassign'] = task.status in ACTIVE_CLAIMED_TASK
      context['button_close'] = task.status == 'NeedsReview'
      context['button_extend_deadline'] = task.status in TASK_IN_PROGRESS

    if is_student:
      if not self.data.timeline.tasksClaimEnded():
        context['button_claim'] = task_logic.canClaimRequestTask(
            task, profile.user)

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
    context = {
        'submissions': self.data.work_submissions,
        'download_url': self.data.redirect.id().urlOf('gci_download_work')
        }

    task = self.data.task
    is_owner = task_logic.isOwnerOfTask(task, self.data.profile)

    if is_owner:
      context['send_for_review'] = self.data.work_submissions and \
          task.status in SEND_FOR_REVIEW_ALLOWED

    deleteable = []
    if self.data.user:
      for work in self.data.work_submissions:
        if work.user.key() == self.data.user.key():
          # Ensure that it is the work from the current user in case the task
          # got re-assigned.
          time_expired = work.submitted_on - datetime.datetime.now()
          if time_expired < task_logic.DELETE_EXPIRATION:
            deleteable.append(work)
    context['deleteable'] = deleteable

    if task_logic.canSubmitWork(task, self.data.profile):
      if self.data.POST and 'submit_work' in self.data.GET:
        context['work_form'] = WorkSubmissionForm(self.data.POST)
      else:
        context['work_form'] = WorkSubmissionForm()

      url = '%s?submit_work' %(
          self.data.redirect.id().urlOf('gci_view_task'))
      context['upload_url'] = blobstore.create_upload_url(url)

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

    if self.data.task.status != 'Closed' and \
        not self.data.timeline.allWorkStopped():
      if self.data.POST and 'post_comment' in self.data.GET:
        context['comment_form'] = CommentForm(self.data.POST)
      else:
        context['comment_form'] = CommentForm()

    return context

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return 'v2/modules/gci/task/_comments.html'


class WorkSubmissionDownload(RequestHandler):
  """Request handler for downloading blobs from a GCIWorkSubmission.
  """

  def djangoURLPatterns(self):
    """URL pattern for this view.
    """
    return [
        url(r'work/download/%s$' % url_patterns.TASK, self,
            name='gci_download_work'),
    ]

  def checkAccess(self):
    """Checks whether this task is visible to the public.
    """
    self.mutator.taskFromKwargs()
    self.check.isTaskVisible()

  def get(self):
    """Attempts to download the blob in the worksubmission that is specified
    in the GET argument.
    """
    id_s = self.request.GET.get('id', '')
    id = int(id_s) if id_s.isdigit() else -1

    work = GCIWorkSubmission.get_by_id(id, self.data.task)

    if not work or not work.upload_of_work:
      return self.error(400, DEF_NO_WORK_FOUND %id)

    upload = work.upload_of_work
    self.response = bs_helper.send_blob(upload, save_as=upload.filename)
