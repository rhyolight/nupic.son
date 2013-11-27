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

"""Views for the GCI Task view page."""

import datetime
import logging

from google.appengine.ext import blobstore
from google.appengine.ext import db

from django import forms as django_forms
from django.forms.util import ErrorDict
from django.utils.translation import ugettext

from melange.request import exception
from soc.logic import cleaning
from soc.views.helper import blobstore as bs_helper
from soc.views.template import Template

from soc.modules.gci.logic import comment as comment_logic
from soc.modules.gci.logic import profile as profile_logic
from soc.modules.gci.logic import task as task_logic
from soc.modules.gci.logic.helper import timeline as timeline_helper
from soc.modules.gci.models.comment import GCIComment
from soc.modules.gci.models.task import ACTIVE_CLAIMED_TASK
from soc.modules.gci.models.task import CLAIMABLE
from soc.modules.gci.models.task import SEND_FOR_REVIEW_ALLOWED
from soc.modules.gci.models.task import TASK_IN_PROGRESS
from soc.modules.gci.models.task import UNPUBLISHED
from soc.modules.gci.models.work_submission import GCIWorkSubmission
from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views.helper import url_patterns
from soc.modules.gci.views.helper.url_patterns import url
from soc.modules.gci.views.helper import url_names

DEF_NOT_ALLOWED_TO_OPERATE_BUTTON = ugettext(
    'You are not allowed to operate the button named %s')

DEF_NOT_ALLOWED_TO_UPLOAD_WORK = ugettext(
    'You are not allowed to upload work')

DEF_NO_UPLOAD = ugettext(
    'An error occurred, please upload a file.')

DEF_NO_URL = ugettext(
    'An error occurred, please submit a valid URL.')

DEF_NO_WORK_FOUND = ugettext('No submission found with id %s')

DEF_NOT_ALLOWED_TO_DELETE = ugettext(
    'You are not allowed to delete this submission')

DEF_CANT_SEND_FOR_REVIEW = ugettext(
    'Only a task that you own and that has submitted work and that has '
    'not been closed can be send in for review.')


class CommentForm(gci_forms.GCIModelForm):
  """Django form for the comment."""

  class Meta:
    model = GCIComment
    css_prefix = 'gci_comment'
    fields = ['title', 'content']

  def idSuffix(self, field):
    if field.name != 'content':
      return ''

    if not self.reply:
      return ''

    return "-%d" % self.reply

  def __init__(self, reply=None, **kwargs):
    super(CommentForm, self).__init__(**kwargs)
    self.reply = reply

    # For UI purposes we need to set this required, validation does not pick
    # it up.
    self.fields['content'].required = True

  def clean_content(self):
    content = cleaning.clean_html_content('content')(self)
    if content:
      return content
    else:
      raise django_forms.ValidationError(
          ugettext('Comment content cannot be empty.'), code='invalid')


class WorkSubmissionFileForm(gci_forms.GCIModelForm):
  """Django form for submitting work as file.
  """

  class Meta:
    model = GCIWorkSubmission
    css_prefix = 'gci_work_submission'
    fields = ['upload_of_work']

  upload_of_work = django_forms.FileField(
      label='Upload work', required=False)

  def addFileRequiredError(self):
    """Appends a form error message indicating that this field is required.
    """
    if not self._errors:
      self._errors = ErrorDict()

    self._errors["upload_of_work"] = self.error_class([DEF_NO_UPLOAD])

  def clean_upload_of_work(self):
    """Ensure that file field has data.
    """
    cleaned_data = self.cleaned_data

    upload = cleaned_data.get('upload_of_work')

    # Although we need the ValidationError exception the message there
    # is dummy because it won't pass through the Appengine's Blobstore
    # API. We use the same error message when adding the form error.
    # See self.addFileRequiredError method.
    if not upload:
      raise gci_forms.ValidationError(DEF_NO_UPLOAD)

    return upload


class WorkSubmissionURLForm(gci_forms.GCIModelForm):
  """Django form for submitting work as URL.
  """

  class Meta:
    model = GCIWorkSubmission
    css_prefix = 'gci_work_submission'
    fields = ['url_to_work']

  def clean_url_to_work(self):
    """Ensure that at least one of the fields has data.
    """
    cleaned_data = self.cleaned_data

    url = cleaned_data.get('url_to_work')

    if not url:
      raise gci_forms.ValidationError(DEF_NO_URL)

    return url


class TaskViewPage(GCIRequestHandler):
  """View for the GCI Task view page where all the actions happen."""

  def djangoURLPatterns(self):
    """URL pattern for this view."""
    return [
        url(r'task/view/%s$' % url_patterns.TASK, self,
            name=url_names.GCI_VIEW_TASK),
    ]

  def checkAccess(self, data, check, mutator):
    """Checks whether this task is visible to the public and any other checks
    if it is a POST request.
    """
    mutator.taskFromKwargs(comments=True, work_submissions=True)
    data.is_visible = check.isTaskVisible()

    if task_logic.updateTaskStatus(data.task):
      # The task logic updated the status of the task since the deadline passed
      # and the GAE task was late to run. Reload the page.
      raise exception.Redirect('')

    if data.request.method == 'POST':
      # Access checks for the different forms on this page. Note that there
      # are no elif clauses because one could add multiple GET params :).
      check.isProfileActive()

      # Tasks for non-active organizations cannot be touched
      check.isOrganizationActive(data.task.org)

      if 'reply' in data.GET:
        # checks for posting comments
        # valid tasks and profile are already checked.
        check.isBeforeAllWorkStopped()
        check.isCommentingAllowed()

      if 'submit_work' in data.GET:
        check.isBeforeAllWorkStopped()
        if not task_logic.canSubmitWork(data.task, data.profile):
          check.fail(DEF_NOT_ALLOWED_TO_UPLOAD_WORK)

      if 'button' in data.GET:
        # check for any of the buttons
        button_name = self._buttonName(data)

        buttons = {}
        TaskInformation(data).setButtonControls(buttons)
        if not buttons.get(button_name):
          check.fail(DEF_NOT_ALLOWED_TO_OPERATE_BUTTON % button_name)

      if 'send_for_review' in data.GET:
        check.isBeforeAllWorkStopped()
        if not task_logic.isOwnerOfTask(data.task, data.profile) or \
            not data.work_submissions or \
            data.task.status not in TASK_IN_PROGRESS:
          check.fail(DEF_CANT_SEND_FOR_REVIEW)

      if 'delete_submission' in data.GET:
        check.isBeforeAllWorkStopped()
        id = self._submissionId(data)
        work = GCIWorkSubmission.get_by_id(id, parent=data.task)

        if not work:
          check.fail(DEF_NO_WORK_FOUND %id)

        time_expired = work.submitted_on - datetime.datetime.now()
        if work.user.key() != data.user.key() or \
            time_expired > task_logic.DELETE_EXPIRATION:
          check.fail(DEF_NOT_ALLOWED_TO_DELETE)

  def jsonContext(self, data, check, mutator):
    url = '%s?submit_work' % (
          data.redirect.id().urlOf(url_names.GCI_VIEW_TASK))
    return {
        'upload_link': blobstore.create_upload_url(url),
        }

  def context(self, data, check, mutator):
    """Returns the context for this view."""
    task = data.task

    context = {
      'page_name': '%s - %s' % (task.title, task.org.name),
      'task': task,
      'is_mentor': data.mentorFor(task.org),
      'task_info': TaskInformation(data),
    }

    if task.deadline:
      # TODO(nathaniel): This is math - move it to a helper function.
      context['complete_percentage'] = timeline_helper.completePercentage(
          end=task.deadline, duration=(task.time_to_complete*3600))

    if data.is_visible:
      context['work_submissions'] = WorkSubmissions(data)
      context['comment_ids'] = [i.key().id() for i in data.comments]
      context['comments'] = CommentsTemplate(data)

    if not context['is_mentor']:
      # Programmatically change css for non-mentors, to for instance show
      # the open cog when a task can be claimed.
      if task.status == 'Closed':
        block_type = 'completed'
      elif task_logic.isOwnerOfTask(task, data.profile):
        block_type = 'owned'
      elif task.status in ACTIVE_CLAIMED_TASK:
        block_type = 'claimed'
      else:
        block_type = 'open'
      context['block_task_type'] = block_type

    return context

  def post(self, data, check, mutator):
    """Handles all POST calls for the TaskViewPage."""
    # TODO(nathaniel): What? Why is data.GET being read in this POST handler?
    if data.is_visible and 'reply' in data.GET:
      return self._postComment(data, check, mutator)
    elif 'button' in data.GET:
      return self._postButton(data)
    elif 'send_for_review' in data.GET:
      return self._postSendForReview(data)
    elif 'delete_submission' in data.GET:
      return self._postDeleteSubmission(data)
    elif 'work_file_submit' in data.POST or 'submit_work' in data.GET:
      return self._postSubmitWork(data, check, mutator)
    else:
      raise exception.BadRequest()

  def _postComment(self, data, check, mutator):
    """Handles the POST call for the form that creates comments."""
    reply = data.GET.get('reply', '')
    reply = int(reply) if reply.isdigit() else None
    comment_form = CommentForm(reply=reply, data=data.POST)

    if not comment_form.is_valid():
      # TODO(nathaniel): problematic self-call.
      return self.get(data, check, mutator)

    comment_form.cleaned_data['reply'] = reply
    comment_form.cleaned_data['created_by'] = data.user
    comment_form.cleaned_data['modified_by'] = data.user

    comment = comment_form.create(commit=False, parent=data.task)
    comment_logic.storeAndNotify(comment)

    # TODO(ljvderijk): Indicate that a comment was successfully created to the
    # user.
    return data.redirect.id().to(url_names.GCI_VIEW_TASK)

  def _postButton(self, data):
    """Handles the POST call for any of the control buttons on the task page.
    """
    button_name = self._buttonName(data)
    task = data.task
    task_key = task.key()

    if button_name == 'button_unpublish':
      task_logic.setTaskStatus(task.key(), 'Unpublished')
    elif button_name == 'button_publish':
      task_logic.setTaskStatus(task.key(), 'Open')
    elif button_name == 'button_edit':
      data.redirect.id(id=task.key().id_or_name())
      return data.redirect.to('gci_edit_task')
    elif button_name == 'button_delete':
      task_logic.delete(task)
      return data.redirect.homepage().to()
    elif button_name == 'button_assign':
      task_logic.assignTask(task, task.student, data.profile)
    elif button_name == 'button_unassign':
      task_logic.unassignTask(task, data.profile)
    elif button_name == 'button_close':
      task_logic.closeTask(task, data.profile)
    elif button_name == 'button_needs_work':
      task_logic.needsWorkTask(task, data.profile)
    elif button_name == 'button_extend_deadline':
      hours = data.POST.get('hours', '')
      hours = int(hours) if hours.isdigit() else 0
      if hours > 0:
        delta = datetime.timedelta(hours=hours)
        task_logic.extendDeadline(task, delta, data.profile)
    elif button_name == 'button_claim':
      task_logic.claimRequestTask(task, data.profile)
    elif button_name == 'button_unclaim':
      task_logic.unclaimTask(task)
    elif button_name == 'button_subscribe':
      profile_key = data.profile.key()
      def txn():
        task = db.get(task_key)
        if profile_key not in task.subscribers:
          task.subscribers.append(profile_key)
          task.put()
      db.run_in_transaction(txn)
    elif button_name == 'button_unsubscribe':
      profile_key = data.profile.key()
      def txn():
        task = db.get(task_key)
        if profile_key in task.subscribers:
          task.subscribers.remove(profile_key)
          task.put()
      db.run_in_transaction(txn)

    return data.redirect.id().to(url_names.GCI_VIEW_TASK)

  def _buttonName(self, data):
    """Returns the name of the button specified in the POST dict."""
    for key in data.POST.keys():
      if key.startswith('button'):
        return key

    return None

  def _postSubmitWork(self, data, check, mutator):
    """POST handler for the work submission form."""
    if 'url_to_work' in data.POST:
      form = WorkSubmissionURLForm(data=data.POST)
      if not form.is_valid():
        # TODO(nathaniel): Problematic self-call.
        return self.get(data, check, mutator)
    elif data.request.file_uploads:
      form = WorkSubmissionFileForm(
          data=data.POST, files=data.request.file_uploads)
      if not form.is_valid():
        # we are not storing this form, remove the uploaded blob from the cloud
        for f in data.request.file_uploads.itervalues():
          f.delete()
        return data.redirect.id().to(
            url_names.GCI_VIEW_TASK, extra=['file=0'])
    else:
      # TODO(nathaniel): Is this user error? If so, we shouldn't be logging
      # it at server-warning level.
      logging.warning('Neither the URL nor the files were provided for work '
                      'submission.')
      return data.redirect.id().to(
          url_names.GCI_VIEW_TASK, extra=['ws_error=1'])

    task = data.task
    # TODO(ljvderijk): Add a non-required profile property?
    form.cleaned_data['user'] = data.user
    form.cleaned_data['org'] =  task.org
    form.cleaned_data['program'] = task.program

    # store the submission, parented by the task
    form.create(parent=task)

    return data.redirect.id().to(url_names.GCI_VIEW_TASK)

  def _postSendForReview(self, data):
    """POST handler for the mark as complete button."""
    task_logic.sendForReview(data.task, data.profile)

    return data.redirect.id().to(url_names.GCI_VIEW_TASK)

  def _postDeleteSubmission(self, data):
    """POST handler to delete a GCIWorkSubmission."""
    submission_id = self._submissionId(data)
    work = GCIWorkSubmission.get_by_id(submission_id, parent=data.task)

    if not work:
      raise exception.BadRequest(message=DEF_NO_WORK_FOUND % submission_id)

    # Deletion of blobs always runs separately from transaction so it has no
    # added value to use it here.
    upload = work.upload_of_work
    work.delete()
    if upload:
      upload.delete()

    # TODO(nathaniel): Redirection to self.
    return data.redirect.id().to(url_names.GCI_VIEW_TASK)

  def _submissionId(self, data):
    """Retrieves the submission id from the POST data."""
    for key in data.POST.keys():
      if key.isdigit():
        return int(key)

    return -1

  def templatePath(self):
    return 'modules/gci/task/public.html'


class TaskInformation(Template):
  """Template that contains the details of a task.
  """

  def context(self):
    """Returns the context for the current template.
    """
    task = self.data.task
    mentors = [m.public_name for m in db.get(task.mentors)]
    profile = self.data.profile

    # We count everyone from the org as a mentor, the mentors property
    # is just who best to contact about this task
    context = {
        'task': task,
        'mentors': mentors,
        'is_mentor': self.data.mentorFor(task.org),
        'is_task_mentor': profile.key() in task.mentors if profile else None,
        'is_owner': task_logic.isOwnerOfTask(task, self.data.profile),
        'is_claimed': task.status in ACTIVE_CLAIMED_TASK,
        'profile': self.data.profile,
    }

    if task.deadline:
      rdays, rhrs, rmins = timeline_helper.remainingTimeSplit(task.deadline)
      context['remaining_days'] = rdays
      context['remaining_hours'] = rhrs
      context['remaining_minutes'] = rmins

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

    if self.data.timeline.allReviewsStopped():
      # no buttons after all reviews has stopped
      return

    task = self.data.task

    is_org_admin = self.data.orgAdminFor(task.org)
    is_mentor = self.data.mentorFor(task.org)
    is_student = self.data.is_student
    is_owner = task_logic.isOwnerOfTask(task, profile)

    if is_org_admin:
      can_unpublish = task.status == 'Open' and not task.student
      context['button_unpublish'] = can_unpublish

      can_publish = task.status in UNPUBLISHED
      context['button_publish'] = can_publish

      context['button_delete'] = not task.student

    if is_mentor:
      context['button_edit'] = task.status in \
          UNPUBLISHED + CLAIMABLE + ACTIVE_CLAIMED_TASK
      context['button_assign'] = task.status == 'ClaimRequested'
      context['button_unassign'] = task.status in ACTIVE_CLAIMED_TASK
      context['button_close'] = task.status == 'NeedsReview'
      context['button_needs_work'] = task.status == 'NeedsReview'
      context['button_extend_deadline'] = task.status in TASK_IN_PROGRESS

    if is_student:
      if not self.data.timeline.tasksClaimEnded():
        if not profile_logic.hasStudentFormsUploaded(profile.student_info):
          # TODO(nathaniel): make this .program() call unnecessary.
          self.data.redirect.program()

          context['student_forms_link'] = self.data.redirect.urlOf(
              url_names.GCI_STUDENT_FORM_UPLOAD)
        # TODO(lennie): Separate the access check out in to different
        # methods and add a context variable to show separate messages.
        context['button_claim'] = task_logic.canClaimRequestTask(
            task, profile)

    if is_owner:
      if not self.data.timeline.tasksClaimEnded():
        context['button_unclaim'] = task.status in ACTIVE_CLAIMED_TASK

    if task.status != 'Closed':
      context['button_subscribe'] = not profile.key() in task.subscribers
      context['button_unsubscribe'] = profile.key() in task.subscribers

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return 'modules/gci/task/_task_information.html'


class WorkSubmissions(Template):
  """Template to render all the GCIWorkSubmissions.

  Contains the form to upload work and contains the "Mark task as complete"
  button for students.
  """

  def _buildWorkSubmissionContext(self):
    """Builds a list containing the info related to each work submission.
    """
    submissions = []
    source = self.data.work_submissions
    for submission in sorted(source, key=lambda e: e.submitted_on):
      submission_info = {
          'entity': submission
          }
      upload_of_work = submission.upload_of_work
      submission_info['upload_of_work'] = upload_of_work
      if upload_of_work:
        uploaded_blob = blobstore.BlobInfo.get(upload_of_work.key())
        submission_info['is_blob_valid'] = True if uploaded_blob else False
      submissions.append(submission_info)

    return submissions

  def context(self):
    """Returns the context for the current template.
    """
    context = {
        'submissions': self._buildWorkSubmissionContext(),
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
        # File form doesn't have any POST parameters so it should not be
        # passed while reconstructing the form. So only URL form is
        # constructed from POST data
        context['work_url_form'] = WorkSubmissionURLForm(data=self.data.POST)
      else:
        context['work_url_form'] = WorkSubmissionURLForm()

      # As mentioned in the comment above since there is no POST data to
      # be passed to the file form, it is constructed in the same way
      # in either cases.
      context['work_file_form'] = WorkSubmissionFileForm()
      if self.data.GET.get('file', None) == '0':
        context['work_file_form'].addFileRequiredError()

      if self.data.GET.get('ws_error', None) == '1':
        context['ws_error'] = True

      url = '%s?submit_work' %(
          self.data.redirect.id().urlOf(url_names.GCI_VIEW_TASK))
      context['direct_post_url'] = url

    return context

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return 'modules/gci/task/_work_submissions.html'


class CommentsTemplate(Template):
  """Template for rendering and adding comments.
  """

  class CommentItem(object):
    def __init__(self, entity, form, author_link):
      self.entity = entity
      self.form = form
      self.author_link = author_link

  def context(self):
    """Returns the context for the current template.
    """
    comments = []
    reply = self.data.GET.get('reply')

    for comment in self.data.comments:
      # generate Reply form, if needed
      form = None
      if self._commentingAllowed():
        comment_id = comment.key().id()
        if self.data.POST and reply == str(comment_id):
          form = CommentForm(reply=comment_id, data=self.data.POST)
        else:
          form = CommentForm(reply=comment_id)

      # generate author link, if comment sent by a student
      author_link = None
      author = comment.created_by
      if author:
        profile = profile_logic.queryProfileForUserAndProgram(
            author, self.data.program).get()
        if profile and profile.is_student:
          author_link = self.data.redirect.profile(profile.link_id).urlOf(
              url_names.GCI_STUDENT_TASKS)

      item = self.CommentItem(comment, form, author_link)
      comments.append(item)

    context = {
        'profile': self.data.profile,
        'comments': comments,
    }

    if self._commentingAllowed():
      if self.data.POST and reply == 'self':
        context['comment_form'] = CommentForm(data=self.data.POST)
      else:
        context['comment_form'] = CommentForm()

    return context

  def _commentingAllowed(self):
    """Returns true iff the comments are allowed to be posted at this time."""
    return not self.data.timeline.allWorkStopped() or (
        not self.data.timeline.allReviewsStopped() and
        self.data.mentorFor(self.data.task.org))

  def templatePath(self):
    """Returns the path to the template that should be used in render()."""
    return 'modules/gci/task/_comments.html'


class WorkSubmissionDownload(GCIRequestHandler):
  """Request handler for downloading blobs from a GCIWorkSubmission."""

  def djangoURLPatterns(self):
    """URL pattern for this view."""
    return [
        url(r'work/download/%s$' % url_patterns.TASK, self,
            name='gci_download_work'),
    ]

  def checkAccess(self, data, check, mutator):
    """Checks whether this task is visible to the public."""
    mutator.taskFromKwargs()
    check.isTaskVisible()

  def get(self, data, check, mutator):
    """Attempts to download the blob in the worksubmission that is specified
    in the GET argument.
    """
    id_string = data.request.GET.get('id', '')
    submission_id = int(id_string) if id_string.isdigit() else -1

    work = GCIWorkSubmission.get_by_id(submission_id, data.task)

    if work and work.upload_of_work:
      return bs_helper.sendBlob(work.upload_of_work)
    else:
      raise exception.BadRequest(message=DEF_NO_WORK_FOUND % id_string)
