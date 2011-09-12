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


from google.appengine.ext import db

from django.utils.translation import ugettext
from django import forms as django_forms


from soc.logic import cleaning
from soc.views import forms
from soc.views.template import Template
from soc.views.helper.access_checker import isSet

from soc.modules.gci.logic import comment as comment_logic
from soc.modules.gci.logic import task as task_logic
from soc.modules.gci.models.comment import GCIComment
from soc.modules.gci.models.task import UPLOAD_ALLOWED
from soc.modules.gci.models.task import SEND_FOR_REVIEW_ALLOWED
from soc.modules.gci.views.base import RequestHandler
from soc.modules.gci.views.helper import url_patterns
from soc.modules.gci.views.helper.url_patterns import url


class CommentForm(forms.ModelForm):
  """Django form for the comment.
  """

  template_path = 'v2/modules/gci/proposal/_comment_form.html'
  class Meta:
    model = GCIComment
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
    """URL pattern for this view.
    """
    return [
        url(r'task/view/%s$' % url_patterns.TASK, self, name='gci_view_task'),
    ]

  def checkAccess(self):
    """Checks whether this task is visible to the public.
    """
    self.mutator.taskFromKwargs(comments=True, work_submissions=True)
    self.check.isTaskVisible()

  def context(self):
    """Returns the context for this view.
    """
    context = {
      'page_name': '%s - %s' %(self.data.task.title, self.data.task.org.name),
      'task': self.data.task,
      'task_info': TaskInformation(self.data),
      'work_submissions': WorkSubmissions(self.data),
      'comments': CommentsTemplate(self.data),
    }

    return context

  def templatePath(self):
    return 'v2/modules/gci/task/public.html'


class TaskInformation(Template):
  """Template that contains the details of a task.
  """
  def context(self):
    """Returns the context for the current template.
    """
    # TODO: Switches for control buttons that are based on role, status and 
    # the program's timeline.
    task = self.data.task
    mentors = [m.public_name for m in db.get(task.mentors)]

    return {'task': task,
            'mentors': mentors}

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return 'v2/modules/gci/task/_task_information.html'


class WorkSubmissions(Template):
  """Template to render all the GCIWorkSubmissions, contain the form to upload
     work and to contain the Mark task as Complete button for students.
  """
  def context(self):
    """Returns the context for the current template.
    """
    context = {'submissions': self.data.work_submissions}

    task = self.data.task
    is_owner = task_logic.isOwnerOfTask(task, self.data.user)

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
        'comments': self.data.comments
    }

    if self.data.task.status != 'Closed':
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


class PostComment(RequestHandler):
  """View which handles publishing comments.
  """

  def djangoURLPatterns(self):
    return [
        url_patterns.url(r'task/post_comment/%s$' % url_patterns.TASK,
            self, name='gci_task_post_comment'),
    ]

  def checkAccess(self):
    self.mutator.TaskFromKwargs()
    self.check.isTaskVisible()
    self.check.isProgramActive()
    self.check.isUser()

  def post(self):
    assert isSet(self.data.task)

    comment_form = CommentForm(self.data.request.POST)

    if not comment_form.is_valid():
      # TODO(ljvderijk): Form error handling
      return

    self.cleaned_data['created_by'] = self.data.user
    self.cleaned_data['modified_by'] = self.data.user

    comment = comment_form.create(commit=False, parent=self.data.task)
    comment_logic.storeAndNotify(comment)

    self.redirect.to('gci_view_task', validated=True)

  def get(self):
    """Special Handler for HTTP GET request since this view only handles POST.
    """
    self.error(405)
