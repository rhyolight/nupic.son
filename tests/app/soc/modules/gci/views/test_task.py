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

from google.appengine.ext import ndb

from django.utils import html

from soc.modules.gci.logic import org_score as org_score_logic
from soc.modules.gci.logic.helper import notifications
from soc.modules.gci.models import comment as comment_model
from soc.modules.gci.models import task as task_model

from tests import forms_to_submit_utils
from tests import profile_utils
from tests import task_utils
from tests import test_utils


def _taskPageURL(task):
  """Returns the URL of the task page."""
  # TODO(nathaniel): Make use of a constant here.
  return '/gci/task/view/%s/%s' % (task.program.key().name(), task.key().id())


def _taskUpdateURL(task):
  """Returns the URL of the task update GAE task."""
  # TODO(nathaniel): I'll bet there should be a constant for this.
  return '/tasks/gci/task/update/%s' % task.key().id()


def _createTestTask(program, org):
  mentor = profile_utils.seedNDBProfile(
      program.key(), mentor_for=[ndb.Key.from_old_key(org.key())])
  return task_utils.seedTask(program, org, mentors=[mentor.key.to_old_key()])


class TaskViewTest(test_utils.GCIDjangoTestCase, test_utils.TaskQueueTestCase):
  """Tests GCITask public view."""

  def setUp(self):
    """Creates a published task for self.org."""
    super(TaskViewTest, self).setUp()
    self.init()
    self.timeline_helper.tasksPubliclyVisible()

    # Create a task, status open
    self.task = _createTestTask(self.program, self.org)
    self.createSubscribersForTask()

  # TODO(orc.avs): move notification tests to logic
  def createSubscribersForTask(self):
    """Creates subscribers for the task."""
    for _ in range(4):
      subscriber = profile_utils.seedNDBProfile(self.program.key())
      self.task.subscribers.append(subscriber.key.to_old_key())
    self.task.put()

  def assertBasicTaskView(self):
    """Checks that the task loads."""
    response = self.get(_taskPageURL(self.task))
    self.assertResponseOK(response)
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gci/task/public.html')

  def assertMailSentToSubscribers(self, comment):
    """Check if a notification email sent to the subscribers of the task."""
    subscribers = ndb.get_multi(
        map(ndb.Key.from_old_key, self.task.subscribers))

    author_key = ndb.Key.from_old_key(
        comment_model.GCIComment.created_by.get_value_for_datastore(comment))
    subject = notifications.DEF_NEW_TASK_COMMENT_SUBJECT % {
        'commented_by': author_key.id(),
        'program_name': self.task.program.name,
        'task_title': self.task.title
    }
    for subscriber in subscribers:
      self.assertEmailSent(bcc=subscriber.contact.email, subject=subject)

  def testBasicTaskView(self):
    """Tests the rendering of the task view."""
    # Use a non-logged-in request to the page for that task
    profile_utils.logout()

    self.assertBasicTaskView()

  def testPostComment(self):
    """Tests leaving a comment on a task."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        mentor_for=[ndb.Key.from_old_key(self.org.key())])

    no_comments = self.task.comments()
    self.assertEqual(len(no_comments), 0)

    comment_title = 'Test Comment Title'
    comment_content = 'Test Comment Content'

    comment_data = {
        'title': comment_title,
        'content': comment_content,
    }

    url = '%s?reply' % _taskPageURL(self.task)
    response = self.post(url, comment_data)

    self.assertResponseRedirect(response)

    one_comment = self.task.comments()
    self.assertEqual(len(one_comment), 1)

    comment = one_comment[0]
    self.assertEqual(comment_title, comment.title)
    self.assertEqual(comment_content, comment.content)
    self.assertEqual(
        user.key.to_old_key(),
        comment_model.GCIComment.created_by.get_value_for_datastore(comment))
    self.assertEqual(
        user.key.to_old_key(),
        comment_model.GCIComment.modified_by.get_value_for_datastore(comment))
    self.assertEqual(self.task.key(), comment.parent_key())
    self.assertIsNone(comment.reply)
    self.assertMailSentToSubscribers(comment)

    self.assertBasicTaskView()

  def testPostCommentWithEmptyTitle(self):
    """Tests leaving a comment with an empty title."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        mentor_for=[ndb.Key.from_old_key(self.org.key())])

    self.assertEqual(len(self.task.comments()), 0)

    comment_content = 'Test Comment Content'

    comment_data_with_empty_title = {
        'title': '',
        'content': comment_content,
    }

    url = '%s?reply' % _taskPageURL(self.task)
    response = self.post(url, comment_data_with_empty_title)

    self.assertResponseRedirect(response)

    comments = self.task.comments()
    self.assertEqual(len(comments), 1)

    comment = comments[0]
    self.assertIsNone(comment.title)
    self.assertEqual(comment_content, comment.content)
    self.assertEqual(
        user.key.to_old_key(),
        comment_model.GCIComment.created_by.get_value_for_datastore(comment))
    self.assertEqual(
        user.key.to_old_key(),
        comment_model.GCIComment.modified_by.get_value_for_datastore(comment))
    self.assertEqual(self.task.key(), comment.parent_key())
    self.assertIsNone(comment.reply)
    self.assertMailSentToSubscribers(comment)

    self.assertBasicTaskView()

  def testPostButtonUnpublish(self):
    """Tests the unpublish button."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        admin_for=[ndb.Key.from_old_key(self.org.key())])

    url = _taskPageURL(self.task)
    response = self.buttonPost(url, 'button_unpublish')

    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, 'Unpublished')

    # check if a comment has been created
    comments = self.task.comments()
    self.assertEqual(len(comments), 1)
    self.assertMailSentToSubscribers(comments[0])

    self.assertBasicTaskView()

  def testPostButtonUnpublishReopenedTaskForbidden(self):
    """Tests the unpublish button on."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        admin_for=[ndb.Key.from_old_key(self.org.key())])

    url = _taskPageURL(self.task)

    # try to unpublish a reopened task
    task = task_model.GCITask.get(self.task.key())
    task.status = task_model.REOPENED
    task.put()

    response = self.buttonPost(url, 'button_unpublish')

    task = task_model.GCITask.get(self.task.key())

    self.assertResponseForbidden(response)
    self.assertEqual(task.status, task_model.REOPENED)

  def testPostButtonUnpublishByUserWithNoRole(self):
    """Tests the unpublish button by a user with no role."""
    url = _taskPageURL(self.task)
    response = self.buttonPost(url, 'button_unpublish')

    self.assertResponseForbidden(response)

  def testPostButtonUnpublishByMentor(self):
    """Tests the unpublish button by a mentor."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        mentor_for=[ndb.Key.from_old_key(self.org.key())])

    url = _taskPageURL(self.task)
    response = self.buttonPost(url, 'button_unpublish')

    self.assertResponseForbidden(response)

  def testPostButtonUnpublishByStudent(self):
    """Tests the unpublish button by a mentor."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBStudent(self.program, user=user)

    url = _taskPageURL(self.task)
    response = self.buttonPost(url, 'button_unpublish')

    self.assertResponseForbidden(response)

  def testPostButtonPublishUnpublishedTask(self):
    """Tests the publish button."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        admin_for=[ndb.Key.from_old_key(self.org.key())])

    self.task.status = 'Unpublished'
    self.task.put()

    url = _taskPageURL(self.task)
    response = self.buttonPost(url, 'button_publish')

    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, task_model.OPEN)

    # check if a comment has been created
    comments = self.task.comments()
    self.assertEqual(len(comments), 1)
    self.assertMailSentToSubscribers(comments[0])

    self.assertBasicTaskView()

  def testPostButtonPublishUnapprovedTask(self):
    """Tests the publish button."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        admin_for=[ndb.Key.from_old_key(self.org.key())])

    self.task.status = task_model.UNAPPROVED
    self.task.put()

    url = _taskPageURL(self.task)
    response = self.buttonPost(url, 'button_publish')

    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, task_model.OPEN)

    self.assertBasicTaskView()

  def testPostButtonPublishByUserWithNoRole(self):
    """Tests the publish button pressed by a user with no role."""
    self.task.status = 'Unpublished'
    self.task.put()

    url = _taskPageURL(self.task)
    response = self.buttonPost(url, 'button_publish')

    self.assertResponseForbidden(response)

  def testPostButtonPublishByMentor(self):
    """Tests the publish button pressed by a mentor."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        mentor_for=[ndb.Key.from_old_key(self.org.key())])

    self.task.status = 'Unpublished'
    self.task.put()

    url = _taskPageURL(self.task)
    response = self.buttonPost(url, 'button_publish')

    self.assertResponseForbidden(response)

  def testPostButtonPublishByStudent(self):
    """Tests the publish button pressed by a student."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBStudent(self.program, user=user)

    self.task.status = 'Unpublished'
    self.task.put()

    url = _taskPageURL(self.task)
    response = self.buttonPost(url, 'button_publish')

    self.assertResponseForbidden(response)

  def testPostButtonDelete(self):
    """Tests the delete button."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        admin_for=[ndb.Key.from_old_key(self.org.key())])

    url = _taskPageURL(self.task)
    response = self.buttonPost(url, 'button_delete')

    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertIsNone(task)

  def testPostButtonAssign(self):
    """Tests the assign button."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        mentor_for=[ndb.Key.from_old_key(self.org.key())])

    student = profile_utils.seedNDBStudent(self.program)

    self.task.status = 'ClaimRequested'
    self.task.student = student.key.to_old_key()
    self.task.put()

    url = _taskPageURL(self.task)
    response = self.buttonPost(url, 'button_assign')

    # check if the task is properly assigned and a deadline has been set
    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, 'Claimed')
    self.assertEqual(
        task_model.GCITask.student.get_value_for_datastore(task),
        student.key.to_old_key())
    self.assertTrue(task.deadline)

    # check if a comment has been created
    comments = self.task.comments()
    self.assertEqual(len(comments), 1)
    self.assertMailSentToSubscribers(comments[0])

    # check if the update task has been enqueued
    self.assertTasksInQueue(n=1, url=_taskUpdateURL(task))

    self.assertBasicTaskView()

  def testPostButtonUnassign(self):
    """Tests the unassign button."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        mentor_for=[ndb.Key.from_old_key(self.org.key())])

    student = profile_utils.seedNDBStudent(self.program)

    self.task.status = 'Claimed'
    self.task.student = student.key.to_old_key()
    self.task.put()

    url = _taskPageURL(self.task)
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

    self.assertBasicTaskView()

  def testPostButtonClose(self):
    """Tests the close task button."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        mentor_for=[ndb.Key.from_old_key(self.org.key())])

    student = profile_utils.seedNDBStudent(self.program)

    self.task.status = 'NeedsReview'
    self.task.student = student.key.to_old_key()
    self.task.put()

    url = _taskPageURL(self.task)
    response = self.buttonPost(url, 'button_close')

    # check if the task is properly closed
    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, 'Closed')
    self.assertEqual(
        task_model.GCITask.student.get_value_for_datastore(task),
        student.key.to_old_key())
    self.assertIsNone(task.deadline)

    # check if a comment has been created
    comments = self.task.comments()
    self.assertEqual(len(comments), 1)
    self.assertMailSentToSubscribers(comments[0])

    # check if OrgScore has been updated
    org_score = org_score_logic.queryForAncestorAndOrg(
        task_model.GCITask.student.get_value_for_datastore(task),
        task.org).get()
    self.assertIsNotNone(org_score)
    self.assertEqual(org_score.numberOfTasks(), 1)
    self.assertEqual(org_score.tasks[0], task.key())

    # check if number_of_completed_tasks has been updated
    student = student.key.get()
    self.assertEqual(student.student_data.number_of_completed_tasks, 1)

    self.assertTasksInQueue(n=1, url='/tasks/gci/ranking/update')

    self.assertTaskBasicView()

  def testPostButtonNeedsWork(self):
    """Tests the needs more work for task button."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        mentor_for=[ndb.Key.from_old_key(self.org.key())])

    student = profile_utils.seedNDBStudent(self.program)

    self.task.status = 'NeedsReview'
    self.task.student = student.key.to_old_key()
    self.task.put()

    url = _taskPageURL(self.task)
    response = self.buttonPost(url, 'button_needs_work')

    # check if the task is properly closed
    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, 'NeedsWork')
    self.assertEqual(
        task_model.GCITask.student.get_value_for_datastore(task),
        student.key.to_old_key())
    self.assertIsNone(task.deadline)

    # check if a comment has been created
    comments = self.task.comments()
    self.assertEqual(len(comments), 1)
    self.assertMailSentToSubscribers(comments[0])

    self.assertBasicTaskView()

  def testPostButtonExtendDeadline(self):
    """Tests the extend deadline button."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        mentor_for=[ndb.Key.from_old_key(self.org.key())])

    student = profile_utils.seedNDBStudent(self.program)

    # set it in the future so that the auto state transfer doesn't trigger
    deadline = datetime.datetime.utcnow() + datetime.timedelta(hours=24)

    self.task.status = 'Claimed'
    self.task.student = student.key.to_old_key()
    self.task.deadline = deadline
    self.task.put()

    url = _taskPageURL(self.task)
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

    self.assertBasicTaskView()

  def testPostButtonClaim(self):
    """Tests the claim task button."""
    form = forms_to_submit_utils.FormsToSubmitHelper().createBlobStoreForm()
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedNDBStudent(
        self.program, user=user,
        student_data_properties={'enrollment_form': form, 'consent_form':form})

    url = _taskPageURL(self.task)
    response = self.buttonPost(url, 'button_claim')

    # check if the task is properly claimed
    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, 'ClaimRequested')
    self.assertEqual(
        task_model.GCITask.student.get_value_for_datastore(task),
        student.key.to_old_key())

    # check if a comment has been created
    comments = self.task.comments()
    self.assertEqual(len(comments), 1)
    self.assertMailSentToSubscribers(comments[0])

    self.assertBasicTaskView()

  def testPostButtonUnclaim(self):
    """Tests the unclaim task button."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedNDBStudent(self.program, user=user)

    self.task.status = 'ClaimRequested'
    self.task.student = student.key.to_old_key()
    self.task.put()

    url = _taskPageURL(self.task)
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

    self.assertBasicTaskView()

  def testPostButtonSubscribe(self):
    """Tests the subscribe button."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile = profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        mentor_for=[ndb.Key.from_old_key(self.org.key())])

    self.assertNotIn(profile.key.to_old_key(), self.task.subscribers)

    url = _taskPageURL(self.task)
    response = self.buttonPost(url, 'button_subscribe')

    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertIn(profile.key.to_old_key(), task.subscribers)

    self.assertBasicTaskView()

  def testPostButtonUnsubscribe(self):
    """Tests the unsubscribe button."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile = profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        mentor_for=[ndb.Key.from_old_key(self.org.key())])

    # subscribe to the task manually
    self.task.subscribers.append(profile.key.to_old_key())
    self.task.put()

    url = _taskPageURL(self.task)
    response = self.buttonPost(url, 'button_unsubscribe')

    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertNotIn(profile.key.to_old_key(), task.subscribers)

    self.assertBasicTaskView()

  def testPostSubmitWork(self):
    """Tests for submitting work."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedNDBStudent(self.program, user=user)

    self.task.status = 'Claimed'
    self.task.student = student.key.to_old_key()
    # set deadline to far future
    self.task.deadline = datetime.datetime.utcnow() + datetime.timedelta(days=1)
    self.task.put()

    no_work = self.task.workSubmissions()
    self.assertEqual(len(no_work), 0)

    work_url = 'http://www.example.com/'
    work_data = {
        'url_to_work': work_url
    }

    url = '%s?submit_work' % _taskPageURL(self.task)
    response = self.post(url, work_data)

    self.assertResponseRedirect(response)

    one_work = self.task.workSubmissions()
    self.assertEqual(len(one_work), 1)

    work = one_work[0]
    self.assertEqual(work_url, work.url_to_work)

    self.assertBasicTaskView()

  def testPostSendForReview(self):
    """Tests for submitting work."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedNDBStudent(self.program, user=user)

    self.task.status = 'Claimed'
    self.task.student = student.key.to_old_key()
    # set deadline to far future
    self.task.deadline = datetime.datetime.utcnow() + \
        datetime.timedelta(days=1)
    self.task.put()

    task_utils.seedWorkSubmission(self.task)

    url = '%s?send_for_review' % _taskPageURL(self.task)
    response = self.post(url)

    task = task_model.GCITask.get(self.task.key())
    self.assertResponseRedirect(response)
    self.assertEqual(task.status, 'NeedsReview')

    self.assertBasicTaskView()

  def testPostSendForReviewClosedTaskForbidden(self):
    """Tests for submitting work for a task whose status is Closed."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedNDBStudent(self.program, user=user)

    self.task.status = 'Closed'
    self.task.student = student.key.to_old_key()
    # set deadline to far future
    self.task.deadline = datetime.datetime.utcnow() + datetime.timedelta(days=1)
    self.task.put()

    task_utils.seedWorkSubmission(self.task)

    url = '%s?send_for_review' % _taskPageURL(self.task)
    response = self.post(url)

    self.assertResponseForbidden(response)

    task = task_model.GCITask.get(self.task.key())
    self.assertEqual(task.status, 'Closed')

    self.assertBasicTaskView()

  def testPostDeleteSubmission(self):
    """Tests for deleting work."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedNDBStudent(self.program, user=user)

    self.task.status = 'Claimed'
    self.task.student = student.key.to_old_key()
    self.task.put()

    work = task_utils.seedWorkSubmission(self.task)

    self.assertEqual(len(self.task.workSubmissions()), 1)

    url = '%s?delete_submission' % _taskPageURL(self.task)
    response = self.post(url, {work.key().id(): ''})

    self.assertResponseRedirect(response)
    self.assertEqual(len(self.task.workSubmissions()), 0)

    self.assertBasicTaskView()


class WorkSubmissionDownloadTest(test_utils.GCIDjangoTestCase):
  """Tests the WorkSubmissionDownload class."""

  def setUp(self):
    """Creates a published task for self.org."""
    super(WorkSubmissionDownloadTest, self).setUp()
    self.init()
    self.timeline_helper.tasksPubliclyVisible()

    # Create an open task.
    self.task = _createTestTask(self.program, self.org)

  def testXSS(self):
    xss_payload = '><img src=http://www.google.com/images/srpr/logo4w.png>'
    url = '/gci/work/download/%s/%s?id=%s' % (
        self.task.program.key().name(), self.task.key().id(), xss_payload)
    response = self.get(url)
    self.assertResponseBadRequest(response)
    self.assertNotIn(xss_payload, response.content)
    self.assertIn(html.escape(xss_payload), response.content)
