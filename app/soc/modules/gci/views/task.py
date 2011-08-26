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
  ]


from google.appengine.ext import db

from django.utils.translation import ugettext
from django import forms as django_forms

from soc.logic import cleaning
from soc.logic.helper import notifications
from soc.tasks import mailer
from soc.views import forms
from soc.views.helper.access_checker import isSet

from soc.modules.gci.models.comment import GCIComment
from soc.modules.gci.models.task import GCITask
from soc.modules.gci.models.work_submission import GCIWorkSubmission
from soc.modules.gci.views.base import RequestHandler
from soc.modules.gci.views.helper import url_patterns

DEF_TASK_CLOSED_MSG = ugettext('This task is closed.')
DEF_TASK_OPEN_MSG = ugettext(
    'This task is open. If you are a GCI student, you can claim it!')

DEF_TASK_REOPENED_MSG = ugettext(
    'This task has been reopened. If you are a GCI student, '
    'you can claim it!')

class CommentForm(forms.Modelform):
  """Djanfgo form for the comment.
  """

  template_path = 'v2/modules/gci/proposal/_comment_form.html'
  class Meta:
    model = GCIomment
    css_prefix = 'gci_comment'
    fields = ['content']

  def clean_content(self):
    field_name = 'content'
    wrapped_clean_html_content = cleaning.clean_html_content(field_name)
    content = wrapped_clean_html_content(self)
    if content:
      return content
    else:
      raise django_forms.ValidationError(
          ugettext('Comment content cannot be empty.'), code='invalid')


class TaskViewPage(RequestHandler):
  """View for the GCI Task view page where all the actions happen.
  """

  def djangoURLPatterns(self):
    return [
          url(r'task/show/%s$' %url_patterns.TASK,
          self, name='gci_show_task'),
    ]

  def checkAccess(self):
    self.mutator.taskFromKwargs()
    self.check.isTaskInURLValid()

  def getWorkSubmissions(self):
    """Gets the Work Submissions for this task.
    """
    query = GCIWorkSubmission.all().filter('user', self.data.task.user)
    work_submissions = query.fetch(1000)
    return work_submissions

  def getComments(self, limit=1000):
    """Gets all comments for the Task.
    """
    assert isSet(self.data.task)

    comments = []
    #The parent for GCIComment entity is GCITask as they run in transactions.
    query = db.Query(GCIComment).parent(self.data.task)
    query.order('created_on')
    all_comments = query.fetch(limit)

    for comment in all_comments:
      comments.append(comment)

    return comments

 def getHeaderMsg(self):
    """Gets the header message for non-logged in general public
       and for logged-in public.
    """
    if self.data.task.status == 'Closed':
      header_msg = self.DEF_TASK_CLOSED_MSG
    elif self.data.task.status == 'Open':
      header_msg = self.DEF_TASK_OPEN_MSG
    elif self.data.task.status == 'Reopened':
      header_msg = self.DEF_TASK_REOPEN_MSG

    return header_msg

  def context(self):
    assert isSet(self.data.url_profile)
    assert isSet(self.data.url_user)
    assert isSet(self.data.task)

    mentors = db.get(self.data.task.mentors)
    mentors_names = ', '.join([m.name() for m in mentors])

    comment_action = reverse('gci_task_comment', kwargs=self.data.kwargs)
    form = CommentForm(self.data.POST or None)
    comment_box = {
              'action': comment_action,
              'form': form,
    }

    header_msg = getHeaderMsg()
    comments = self.getComments()
    work_submissions = self.getWorkSubmissions()

    context = {
      'task': self.data.task
      'header_msg': header_msg
      'mentors': mentors_names
      'comments': comments
      'work_submissions': work_submissions
      'student_name': self.data.url_profile.name()
      'comment_box': comment_box
    }

    return context

    def templatePath(self):
      return 'v2/modules/gci/task/public.html'


class PostComment(RequestHandler):
  """View which handles publishing comments.
  """

  def djangoURLPatterns(self):
    return [
         url(r'task/comment/%s$' % url_patterns.TASK,
         self, name='gci_task_comment'),
    ]

  def checkAccess(self):
    self.check.isProgramActive()
    self.check.isProfileActive()
    self.mutator.TaskFromKwargs()

  def createCommentFromForm(self):
    """Creates a new comment based on the data inserted in the form.

    Returns:
      a newly created comment entity or None
    """
    assert isSet(self.data.task)

    comment_form = CommentForm(self.data.request.POST)
    if not comment_form.is_valid():

    comment_form.cleaned_data['created_by'] = self.data.profile

    to_emails = []
    mentors_keys = self.data.task.mentors
    for mentor_key in mentors_keys:
      if mentor_key != self.data.profile.key():
        mentor = db.get(mentor_key)
        to_emails.append(mentor.email)

    def create_comment_txn():
      comment = comment_form.create(commit=True, parent=self.data.task)
      context = notifications.newCommentContext(self.data, comment, to_emails)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=comment)
      sub_txn()
      return comment

    return db.run_in_transaction(create_comment_txn)

  def post(self):
    assert isSet(self.data.task)
    self.createCommentFromForm()

  def get(self):
    """Special Handler for HTTP GET request since this view only handles POST.
    """
    self.error(405)
