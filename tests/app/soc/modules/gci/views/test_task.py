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


"""Tests for GCITask public view.
"""

__authors__ = [
  '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]

import datetime

from soc.modules.gci.models.task import GCITask

from tests.gci_task_utils import GCITaskHelper
from tests.profile_utils import GCIProfileHelper
from tests.test_utils import GCIDjangoTestCase
from tests.test_utils import TaskQueueTestCase


class TaskViewTest(GCIDjangoTestCase, TaskQueueTestCase):
  """Tests GCITask public view.
  """

  def setUp(self):
    """Creates a published task for self.org.
    """
    self.init()
    self.timeline.tasksPubliclyVisible()

    # Create a task, status published
    profile = GCIProfileHelper(self.gci, self.dev_test)
    self.task = profile.createOtherUser('mentor@example.com').\
        createMentorWithTask('Open', self.org)

  def testBasicTaskView(self):
    """Tests the rendering of the task view.
    """
    # Use a non-logged-in request to the page for that task
    self.data.clear()

    url = self._taskPageUrl(self.task)
    response = self.get(url)

    # Expect a proper response (200)
    self.assertResponseOK(response)
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/modules/gci/task/public.html')

  def testPostComment(self):
    """Tests leaving a comment on a task.
    """
    self.data.createMentor(self.org)

    no_comments = self.task.comments()
    self.assertLength(no_comments, 0)

    comment_title = 'Test Comment Title'
    comment_content = 'Test Comment Content'

    comment_data = {
        'title': comment_title,
        'content': comment_content,
    }

    url = '%s?post_comment' %self._taskPageUrl(self.task)
    response = self.post(url, comment_data)

    self.assertResponseRedirect(response)

    one_comment = self.task.comments()
    self.assertLength(one_comment, 1)

    comment = one_comment[0]
    self.assertEqual(comment_title, comment.title)
    self.assertEqual(comment_content, comment.content)

  def testPostButtonUnpublish(self):
    """Tests the unpublish button.
    """
    self.data.createOrgAdmin(self.org)

    url = '%s?button' %self._taskPageUrl(self.task)
    response = self.post(url, {'button_unpublish': ''})

    task = GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, 'Unpublished')

  def testPostButtonDelete(self):
    """Tests the delete button.
    """
    self.data.createOrgAdmin(self.org)

    url = '%s?button' %self._taskPageUrl(self.task)
    response = self.post(url, {'button_delete': ''})

    task = GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task, None)

  def testPostButtonAssign(self):
    """Tests the assign button.
    """
    self.data.createMentor(self.org)

    profile_helper = GCIProfileHelper(self.gci, self.dev_test)
    profile_helper.createOtherUser('student@example.com').createStudent()
    student = profile_helper.profile

    self.task.status = 'ClaimRequested'
    self.task.student = student
    self.task.put()

    url = '%s?button' %self._taskPageUrl(self.task)
    response = self.post(url, {'button_assign': ''})

    # check if the task is properly assigned and a deadline has been set
    task = GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, 'Claimed')
    self.assertEqual(task.student.key(), student.key())
    self.assertTrue(task.deadline)

    # check if a comment has been created
    comments = self.task.comments()
    self.assertLength(comments, 1)

    # check if the update task has been enqueued
    self.assertTasksInQueue(n=1, url=self._taskUpdateUrl(task))


  def testPostButtonUnassign(self):
    """Tests the unassign button.
    """
    self.data.createMentor(self.org)

    profile_helper = GCIProfileHelper(self.gci, self.dev_test)
    profile_helper.createOtherUser('student@example.com').createStudent()
    student = profile_helper.profile

    self.task.status = 'Claimed'
    self.task.student = student
    self.task.put()

    url = '%s?button' %self._taskPageUrl(self.task)
    response = self.post(url, {'button_unassign': ''})

    # check if the task is properly unassigned
    task = GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, 'Reopened')
    self.assertEqual(task.student, None)
    self.assertEqual(task.deadline, None)

    # check if a comment has been created
    comments = self.task.comments()
    self.assertLength(comments, 1)

  def testPostButtonClose(self):
    """Tests the close task button.
    """
    self.data.createMentor(self.org)

    profile_helper = GCIProfileHelper(self.gci, self.dev_test)
    profile_helper.createOtherUser('student@example.com').createStudent()
    student = profile_helper.profile

    self.task.status = 'NeedsReview'
    self.task.student = student
    self.task.put()

    url = '%s?button' %self._taskPageUrl(self.task)
    response = self.post(url, {'button_close': ''})

    # check if the task is properly closed
    task = GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, 'Closed')
    self.assertEqual(task.student.key(), student.key())
    self.assertEqual(task.deadline, None)

    # check if a comment has been created
    comments = self.task.comments()
    self.assertLength(comments, 1)

    self.assertTasksInQueue(n=1, url='/tasks/gci/ranking/update')

  def testPostButtonExtendDeadline(self):
    """Tests the extend deadline button.
    """
    self.data.createMentor(self.org)

    profile_helper = GCIProfileHelper(self.gci, self.dev_test)
    profile_helper.createOtherUser('student@example.com').createStudent()
    student = profile_helper.profile

    # set it in the future so that the auto state transfer doesn't trigger
    deadline = datetime.datetime.utcnow() + datetime.timedelta(hours=24)

    self.task.status = 'Claimed'
    self.task.student = student
    self.task.deadline = deadline
    self.task.put()

    url = '%s?button' %self._taskPageUrl(self.task)
    response = self.post(
        url, {'button_extend_deadline': '', 'hours': 1})

    task = GCITask.get(self.task.key())
    self.assertResponseRedirect(response)

    delta = task.deadline - deadline
    self.assertTrue(delta.seconds == 3600)

    # check if a comment has been created
    comments = self.task.comments()
    self.assertLength(comments, 1)

  def testPostButtonClaim(self):
    """Tests the claim task button.
    """
    self.data.createStudent()

    url = '%s?button' %self._taskPageUrl(self.task)
    response = self.post(url, {'button_claim': ''})

    # check if the task is properly claimed
    task = GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, 'ClaimRequested')
    self.assertEqual(task.student.key(), self.data.profile.key())

    # check if a comment has been created
    comments = self.task.comments()
    self.assertLength(comments, 1)

  def testPostButtonUnclaim(self):
    """Tests the unclaim task button.
    """
    self.data.createStudent()

    self.task.status = 'ClaimRequested'
    self.task.student = self.data.profile
    self.task.put()

    url = '%s?button' %self._taskPageUrl(self.task)
    response = self.post(url, {'button_unclaim': ''})

    # check if the task is properly opened
    task = GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, 'Reopened')
    self.assertEqual(task.student, None)
    self.assertEqual(task.deadline, None)

    # check if a comment has been created
    comments = self.task.comments()
    self.assertLength(comments, 1)

  def testPostButtonSubscribe(self):
    """Tests the subscribe button.
    """
    self.data.createMentor(self.org)

    profile = self.data.profile
    self.assertFalse(profile.key() in self.task.subscribers)

    url = '%s?button' %self._taskPageUrl(self.task)
    response = self.post(url, {'button_subscribe': ''})

    task = GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertTrue(profile.key() in task.subscribers)

  def testPostButtonUnsubscribe(self):
    """Tests the unsubscribe button.
    """
    self.data.createMentor(self.org)

    # subscribe to the task manually
    profile = self.data.profile
    self.task.subscribers.append(profile.key())
    self.task.put()

    url = '%s?button' %self._taskPageUrl(self.task)
    response = self.post(url, {'button_unsubscribe': ''})

    task = GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertFalse(profile.key() in task.subscribers)

  def testPostSubmitWork(self):
    """Tests for submitting work.
    """
    self.data.createStudent()

    self.task.status = 'Claimed'
    self.task.student = self.data.profile
    # set deadline to far future
    self.task.deadline = datetime.datetime.utcnow() + datetime.timedelta(days=1)
    self.task.put()

    no_work = self.task.workSubmissions()
    self.assertLength(no_work, 0)

    work_url = 'http://www.example.com/'
    work_data = {
        'url_to_work': work_url
    }

    url = '%s?submit_work' %self._taskPageUrl(self.task)
    response = self.post(url, work_data)

    self.assertResponseRedirect(response)

    one_work = self.task.workSubmissions()
    self.assertLength(one_work, 1)

    work = one_work[0]
    self.assertEqual(work_url, work.url_to_work)

  def testPostSendForReview(self):
    """Tests for submitting work.
    """
    self.data.createStudent()

    self.task.status = 'Claimed'
    self.task.student = self.data.profile
    # set deadline to far future
    self.task.deadline = datetime.datetime.utcnow() + datetime.timedelta(days=1)
    self.task.put()

    GCITaskHelper(self.program).createWorkSubmission(
        self.task, self.data.profile)

    url = '%s?send_for_review' %self._taskPageUrl(self.task)
    response = self.post(url)

    task = GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, 'NeedsReview')

  def _taskPageUrl(self, task):
    """Returns the url of the task page.
    """
    return '/gci/task/view/%s/%s' %(task.program.key().name(), task.key().id())

  def _taskUpdateUrl(self, task):
    """Returns the url to the task update GAE Task.
    """
    return '/tasks/gci/task/update/%s' %task.key().id()
