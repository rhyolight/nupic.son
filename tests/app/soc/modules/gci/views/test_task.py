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

"""Tests for GCITask public view."""

import datetime

from django.utils import html

from soc.modules.gci.logic import org_score as org_score_logic
from soc.modules.gci.logic import profile as profile_logic
from soc.modules.gci.logic.helper.notifications import (
    DEF_NEW_TASK_COMMENT_SUBJECT)
from soc.modules.gci.models import task as task_model
from soc.modules.gci.models.profile import GCIProfile

from tests import profile_utils
from tests import task_utils
from tests.test_utils import GCIDjangoTestCase
from tests.test_utils import TaskQueueTestCase


class TaskViewTest(GCIDjangoTestCase, TaskQueueTestCase):
  """Tests GCITask public view.
  """

  def setUp(self):
    """Creates a published task for self.org.
    """
    super(TaskViewTest, self).setUp()
    self.init()
    self.timeline_helper.tasksPubliclyVisible()

    # Create a task, status open
    mentor = profile_utils.seedGCIProfile(
        self.program, mentor_for=[self.org.key()])
    self.task = task_utils.seedTask(
        self.program, self.org, mentors=[mentor.key()])
    self.createSubscribersForTask()

  #TODO(orc.avs): move notification tests to logic
  def createSubscribersForTask(self):
    """Creates subscribers for the task.
    """
    for i in range(4):
      user = profile_utils.seedUser(email='subscriber%s@example.com' % str(i))
      subscriber = profile_utils.seedGCIProfile(self.program, user=user)
      self.task.subscribers.append(subscriber.key())
    self.task.put()

  def assertMailSentToSubscribers(self, comment):
    """Check if a notification email sent to the subscribers of the task.
    """
    subscribers = GCIProfile.get(self.task.subscribers)
    subject = DEF_NEW_TASK_COMMENT_SUBJECT % {
        'commented_by': comment.created_by.name,
        'program_name': self.task.program.name,
        'task_title': self.task.title
    }
    for subscriber in subscribers:
      self.assertEmailSent(bcc=subscriber.email, subject=subject)

  def testBasicTaskView(self):
    """Tests the rendering of the task view.
    """
    # Use a non-logged-in request to the page for that task
    self.profile_helper.clear()

    url = self._taskPageUrl(self.task)
    response = self.get(url)

    # Expect a proper response (200)
    self.assertResponseOK(response)
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gci/task/public.html')

  def testPostComment(self):
    """Tests leaving a comment on a task.
    """
    self.profile_helper.createMentor(self.org)

    no_comments = self.task.comments()
    self.assertEqual(len(no_comments), 0)

    comment_title = 'Test Comment Title'
    comment_content = 'Test Comment Content'

    comment_data = {
        'title': comment_title,
        'content': comment_content,
    }

    url = '%s?reply' %self._taskPageUrl(self.task)
    response = self.post(url, comment_data)

    self.assertResponseRedirect(response)

    one_comment = self.task.comments()
    self.assertEqual(len(one_comment), 1)

    comment = one_comment[0]
    self.assertEqual(comment_title, comment.title)
    self.assertEqual(comment_content, comment.content)
    self.assertEqual(self.profile_helper.user.key(), comment.created_by.key())
    self.assertEqual(self.profile_helper.user.key(), comment.modified_by.key())
    self.assertEqual(self.task.key(), comment.parent_key())
    self.assertIsNone(comment.reply)
    self.assertMailSentToSubscribers(comment)

  def testPostCommentWithEmptyTitle(self):
    """Tests leaving a comment with an empty title."""
    self.profile_helper.createMentor(self.org)

    self.assertEqual(len(self.task.comments()), 0)

    comment_content = 'Test Comment Content'

    comment_data_with_empty_title = {
        'title': '',
        'content': comment_content,
    }

    url = '%s?reply' %self._taskPageUrl(self.task)
    response = self.post(url, comment_data_with_empty_title)

    self.assertResponseRedirect(response)

    comments = self.task.comments()
    self.assertEqual(len(comments), 1)

    comment = comments[0]
    self.assertIsNone(comment.title)
    self.assertEqual(comment_content, comment.content)
    self.assertEqual(self.profile_helper.user.key(), comment.created_by.key())
    self.assertEqual(self.profile_helper.user.key(), comment.modified_by.key())
    self.assertEqual(self.task.key(), comment.parent_key())
    self.assertIsNone(comment.reply)
    self.assertMailSentToSubscribers(comment)

  def testPostButtonUnpublish(self):
    """Tests the unpublish button.
    """
    self.profile_helper.createOrgAdmin(self.org)

    url = self._taskPageUrl(self.task)
    response = self.buttonPost(url, 'button_unpublish')

    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, 'Unpublished')

    # check if a comment has been created
    comments = self.task.comments()
    self.assertEqual(len(comments), 1)
    self.assertMailSentToSubscribers(comments[0])

  def testPostButtonUnpublishReopenedTaskForbidden(self):
    """Tests the unpublish button on.
    """
    self.profile_helper.createOrgAdmin(self.org)

    url = self._taskPageUrl(self.task)

    # try to unpublish a reopened task
    task = task_model.GCITask.get(self.task.key())
    task.status = task_model.REOPENED
    task.put()

    response = self.buttonPost(url, 'button_unpublish')

    task = task_model.GCITask.get(self.task.key())

    self.assertResponseForbidden(response)
    self.assertEqual(task.status, task_model.REOPENED)

  def testPostButtonUnpublishByUserWithNoRole(self):
    """Tests the unpublish button by a user with no role.
    """
    url = self._taskPageUrl(self.task)
    response = self.buttonPost(url, 'button_unpublish')

    self.assertResponseForbidden(response)

  def testPostButtonUnpublishByMentor(self):
    """Tests the unpublish button by a mentor.
    """
    self.profile_helper.createMentor(self.org)

    url = self._taskPageUrl(self.task)
    response = self.buttonPost(url, 'button_unpublish')

    self.assertResponseForbidden(response)

  def testPostButtonUnpublishByStudent(self):
    """Tests the unpublish button by a mentor.
    """
    self.profile_helper.createStudent()

    url = self._taskPageUrl(self.task)
    response = self.buttonPost(url, 'button_unpublish')

    self.assertResponseForbidden(response)

  def testPostButtonPublishUnpublishedTask(self):
    """Tests the publish button.
    """
    self.profile_helper.createOrgAdmin(self.org)

    self.task.status = 'Unpublished'
    self.task.put()

    url = self._taskPageUrl(self.task)
    response = self.buttonPost(url, 'button_publish')

    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, task_model.OPEN)

    # check if a comment has been created
    comments = self.task.comments()
    self.assertEqual(len(comments), 1)
    self.assertMailSentToSubscribers(comments[0])

  def testPostButtonPublishUnapprovedTask(self):
    """Tests the publish button.
    """
    self.profile_helper.createOrgAdmin(self.org)

    self.task.status = task_model.UNAPPROVED
    self.task.put()

    url = self._taskPageUrl(self.task)
    response = self.buttonPost(url, 'button_publish')

    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, task_model.OPEN)

  def testPostButtonPublishByUserWithNoRole(self):
    """Tests the publish button pressed by a user with no role.
    """
    self.task.status = 'Unpublished'
    self.task.put()

    url = self._taskPageUrl(self.task)
    response = self.buttonPost(url, 'button_publish')

    self.assertResponseForbidden(response)

  def testPostButtonPublishByMentor(self):
    """Tests the publish button pressed by a mentor.
    """
    self.profile_helper.createMentor(self.org)

    self.task.status = 'Unpublished'
    self.task.put()

    url = self._taskPageUrl(self.task)
    response = self.buttonPost(url, 'button_publish')

    self.assertResponseForbidden(response)

  def testPostButtonPublishByStudent(self):
    """Tests the publish button pressed by a student.
    """
    self.profile_helper.createStudent()

    self.task.status = 'Unpublished'
    self.task.put()

    url = self._taskPageUrl(self.task)
    response = self.buttonPost(url, 'button_publish')

    self.assertResponseForbidden(response)

  def testPostButtonDelete(self):
    """Tests the delete button.
    """
    self.profile_helper.createOrgAdmin(self.org)

    url = self._taskPageUrl(self.task)
    response = self.buttonPost(url, 'button_delete')

    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertIsNone(task)

  def testPostButtonAssign(self):
    """Tests the assign button.
    """
    self.profile_helper.createMentor(self.org)

    student = profile_utils.seedGCIStudent(self.program)

    self.task.status = 'ClaimRequested'
    self.task.student = student
    self.task.put()

    url = self._taskPageUrl(self.task)
    response = self.buttonPost(url, 'button_assign')

    # check if the task is properly assigned and a deadline has been set
    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, 'Claimed')
    self.assertEqual(task.student.key(), student.key())
    self.assertTrue(task.deadline)

    # check if a comment has been created
    comments = self.task.comments()
    self.assertEqual(len(comments), 1)
    self.assertMailSentToSubscribers(comments[0])

    # check if the update task has been enqueued
    self.assertTasksInQueue(n=1, url=self._taskUpdateUrl(task))

  def testPostButtonUnassign(self):
    """Tests the unassign button.
    """
    self.profile_helper.createMentor(self.org)

    student = profile_utils.seedGCIStudent(self.program)

    self.task.status = 'Claimed'
    self.task.student = student
    self.task.put()

    url = self._taskPageUrl(self.task)
    response = self.buttonPost(url, 'button_unassign')

    # check if the task is properly unassigned
    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, task_model.REOPENED)
    self.assertIsNone(task.student)
    self.assertIsNone(task.deadline)

    # check if a comment has been created
    comments = self.task.comments()
    self.assertEqual(len(comments), 1)
    self.assertMailSentToSubscribers(comments[0])

  def testPostButtonClose(self):
    """Tests the close task button.
    """
    self.profile_helper.createMentor(self.org)

    student = profile_utils.seedGCIStudent(self.program)

    self.task.status = 'NeedsReview'
    self.task.student = student
    self.task.put()

    url = self._taskPageUrl(self.task)
    response = self.buttonPost(url, 'button_close')

    # check if the task is properly closed
    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, 'Closed')
    self.assertEqual(task.student.key(), student.key())
    self.assertIsNone(task.deadline)

    # check if a comment has been created
    comments = self.task.comments()
    self.assertEqual(len(comments), 1)
    self.assertMailSentToSubscribers(comments[0])

    # check if OrgScore has been updated
    org_score = org_score_logic.queryForAncestorAndOrg(
        task.student, task.org).get()
    self.assertIsNotNone(org_score)
    self.assertEqual(org_score.numberOfTasks(), 1)
    self.assertEqual(org_score.tasks[0], task.key())

    # check if number_of_completed_tasks has been updated
    student_info = profile_logic.queryStudentInfoForParent(task.student).get()
    self.assertEqual(student_info.number_of_completed_tasks, 1)

    self.assertTasksInQueue(n=1, url='/tasks/gci/ranking/update')

  def testPostButtonNeedsWork(self):
    """Tests the needs more work for task button.
    """
    self.profile_helper.createMentor(self.org)

    student = profile_utils.seedGCIStudent(self.program)

    self.task.status = 'NeedsReview'
    self.task.student = student
    self.task.put()

    url = self._taskPageUrl(self.task)
    response = self.buttonPost(url, 'button_needs_work')

    # check if the task is properly closed
    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, 'NeedsWork')
    self.assertEqual(task.student.key(), student.key())
    self.assertIsNone(task.deadline)

    # check if a comment has been created
    comments = self.task.comments()
    self.assertEqual(len(comments), 1)
    self.assertMailSentToSubscribers(comments[0])

  def testPostButtonExtendDeadline(self):
    """Tests the extend deadline button.
    """
    self.profile_helper.createMentor(self.org)

    student = profile_utils.seedGCIStudent(self.program)

    # set it in the future so that the auto state transfer doesn't trigger
    deadline = datetime.datetime.utcnow() + datetime.timedelta(hours=24)

    self.task.status = 'Claimed'
    self.task.student = student
    self.task.deadline = deadline
    self.task.put()

    url = self._taskPageUrl(self.task)
    response = self.buttonPost(
        url, 'button_extend_deadline', {'hours': 1})

    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)

    delta = task.deadline - deadline
    self.assertTrue(delta.seconds == 3600)

    # check if a comment has been created
    comments = self.task.comments()
    self.assertEqual(len(comments), 1)
    self.assertMailSentToSubscribers(comments[0])

  def testPostButtonClaim(self):
    """Tests the claim task button.
    """
    self.profile_helper.createStudentWithConsentForms(
        consent_form=True, student_id_form=True)

    url = self._taskPageUrl(self.task)
    response = self.buttonPost(url, 'button_claim')

    # check if the task is properly claimed
    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, 'ClaimRequested')
    self.assertEqual(task.student.key(), self.profile_helper.profile.key())

    # check if a comment has been created
    comments = self.task.comments()
    self.assertEqual(len(comments), 1)
    self.assertMailSentToSubscribers(comments[0])

  def testPostButtonUnclaim(self):
    """Tests the unclaim task button.
    """
    self.profile_helper.createStudent()

    self.task.status = 'ClaimRequested'
    self.task.student = self.profile_helper.profile
    self.task.put()

    url = self._taskPageUrl(self.task)
    response = self.buttonPost(url, 'button_unclaim')

    # check if the task is properly opened
    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, task_model.REOPENED)
    self.assertIsNone(task.student)
    self.assertIsNone(task.deadline)

    # check if a comment has been created
    comments = self.task.comments()
    self.assertEqual(len(comments), 1)
    self.assertMailSentToSubscribers(comments[0])

  def testPostButtonSubscribe(self):
    """Tests the subscribe button.
    """
    self.profile_helper.createMentor(self.org)

    profile = self.profile_helper.profile
    self.assertNotIn(profile.key(), self.task.subscribers)

    url = self._taskPageUrl(self.task)
    response = self.buttonPost(url, 'button_subscribe')

    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertIn(profile.key(), task.subscribers)

  def testPostButtonUnsubscribe(self):
    """Tests the unsubscribe button.
    """
    self.profile_helper.createMentor(self.org)

    # subscribe to the task manually
    profile = self.profile_helper.profile
    self.task.subscribers.append(profile.key())
    self.task.put()

    url = self._taskPageUrl(self.task)
    response = self.buttonPost(url, 'button_unsubscribe')

    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertNotIn(profile.key(), task.subscribers)

  def testPostSubmitWork(self):
    """Tests for submitting work.
    """
    self.profile_helper.createStudent()

    self.task.status = 'Claimed'
    self.task.student = self.profile_helper.profile
    # set deadline to far future
    self.task.deadline = datetime.datetime.utcnow() + datetime.timedelta(days=1)
    self.task.put()

    no_work = self.task.workSubmissions()
    self.assertEqual(len(no_work), 0)

    work_url = 'http://www.example.com/'
    work_data = {
        'url_to_work': work_url
    }

    url = '%s?submit_work' %self._taskPageUrl(self.task)
    response = self.post(url, work_data)

    self.assertResponseRedirect(response)

    one_work = self.task.workSubmissions()
    self.assertEqual(len(one_work), 1)

    work = one_work[0]
    self.assertEqual(work_url, work.url_to_work)

  def testPostSendForReview(self):
    """Tests for submitting work.
    """
    self.profile_helper.createStudent()

    self.task.status = 'Claimed'
    self.task.student = self.profile_helper.profile
    # set deadline to far future
    self.task.deadline = datetime.datetime.utcnow() + \
        datetime.timedelta(days=1)
    self.task.put()

    task_utils.seedWorkSubmission(self.task)

    url = '%s?send_for_review' % self._taskPageUrl(self.task)
    response = self.post(url)

    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, 'NeedsReview')

  def testPostSendForReviewClosedTaskForbidden(self):
    """Tests for submitting work for a task whose status is Closed.
    """
    self.profile_helper.createStudent()

    self.task.status = 'Closed'
    self.task.student = self.profile_helper.profile
    # set deadline to far future
    self.task.deadline = datetime.datetime.utcnow() + \
        datetime.timedelta(days=1)
    self.task.put()

    task_utils.seedWorkSubmission(self.task)

    url = '%s?send_for_review' % self._taskPageUrl(self.task)
    response = self.post(url)

    self.assertResponseForbidden(response)

    task = task_model.GCITask.get(self.task.key())
    self.assertEqual(task.status, 'Closed')

  def testPostDeleteSubmission(self):
    """Tests for deleting work.
    """
    self.profile_helper.createStudent()

    self.task.status = 'Claimed'
    self.task.student = self.profile_helper.profile
    self.task.put()

    work = task_utils.seedWorkSubmission(self.task)

    self.assertEqual(len(self.task.workSubmissions()), 1)

    url = '%s?delete_submission' %self._taskPageUrl(self.task)
    response = self.post(url, {work.key().id(): ''})

    self.assertResponseRedirect(response)
    self.assertEqual(len(self.task.workSubmissions()), 0)

  def _taskPageUrl(self, task):
    """Returns the url of the task page.
    """
    return '/gci/task/view/%s/%s' %(task.program.key().name(), task.key().id())

  def _taskUpdateUrl(self, task):
    """Returns the url to the task update GAE Task.
    """
    return '/tasks/gci/task/update/%s' %task.key().id()


class WorkSubmissionDownloadTest(GCIDjangoTestCase):
  """Tests the WorkSubmissionDownload class."""

  def setUp(self):
    """Creates a published task for self.org."""
    super(WorkSubmissionDownloadTest, self).setUp()
    self.init()
    self.timeline_helper.tasksPubliclyVisible()

    # Create an open task.
    mentor = profile_utils.seedGCIProfile(
        self.program, mentor_for=[self.org.key()])
    self.task = task_utils.seedTask(
        self.program, self.org, mentors=[mentor.key()])

  def testXSS(self):
    xss_payload = '><img src=http://www.google.com/images/srpr/logo4w.png>'
    url = '/gci/work/download/%s/%s?id=%s' % (
        self.task.program.key().name(), self.task.key().id(), xss_payload)
    response = self.get(url)
    self.assertResponseBadRequest(response)
    self.assertNotIn(xss_payload, response.content)
    self.assertIn(html.escape(xss_payload), response.content)
