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

"""GCITask logic methods."""

import datetime
import logging

from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.ext import db
from google.appengine.ext import ndb

from django.utils.translation import ugettext

from soc.modules.gci.logic import comment as comment_logic
from soc.modules.gci.logic import profile as profile_logic
from soc.modules.gci.logic import org_score as org_score_logic
from soc.modules.gci.models.comment import GCIComment
from soc.modules.gci.models import task as task_model
from soc.modules.gci.models.work_submission import GCIWorkSubmission

DEF_ACTION_NEEDED_TITLE = ugettext('Initial Deadline passed')
DEF_ACTION_NEEDED = ugettext(
    'Melange has detected that the initial deadline has passed and it has '
    'set the task status to ActionNeeded. The student has 24 hours to submit '
    'the work before the task is reopened and sent back to the pool for '
    'other students to claim.')


DEF_ASSIGNED_TITLE = ugettext('Task Assigned')
DEF_ASSIGNED = ugettext(
    'This task has been assigned to %s. '
    'You have %i hours to complete this task, good luck!')


DEF_CLAIM_REQUEST_TITLE = ugettext('Task Claimed')
DEF_CLAIM_REQUEST = ugettext('I would like to work on this task.')


DEF_CLOSED_TITLE = ugettext('Task Closed')
DEF_CLOSED = ugettext(
    'Congratulations, this task has been completed successfully.')


DEF_NEEDS_WORK_TITLE = ugettext('Task Needs More Work')
DEF_NEEDS_WORK = ugettext(
    'One of the mentors has sent this task back for more work. Talk to '
    'the mentor(s) assigned to this task to satisfy the requirements needed '
    'to complete this task, submit your work again and mark the task as '
    'complete once you re-submit your work.')


DEF_EXTEND_DEADLINE_TITLE = ugettext('Deadline extended')
DEF_EXTEND_DEADLINE = ugettext(
    'The deadline of the task has been extended with %i days and %i hours.')


DEF_NO_MORE_WORK_TITLE = ugettext('No more Work can be submitted')
DEF_NO_MORE_WORK = ugettext(
    'Melange has detected that the deadline has passed and no more work can '
    'be submitted. The submitted work should be reviewed.')


DEF_PUBLISHED_TITLE = ugettext('Task Published')
DEF_PUBLISHED = ugettext('This task is open and can be claimed.')


DEF_REOPENED_TITLE = ugettext('Task Reopened')
DEF_REOPENED = ugettext(
    'Melange has detected that the final deadline has passed and it has '
    'reopened the task.')


DEF_SEND_FOR_REVIEW_TITLE = ugettext('Ready for review')
DEF_SEND_FOR_REVIEW = ugettext(
    'The work on this task is ready to be reviewed.')


DEF_UNASSIGNED_TITLE = ugettext('Task Reopened')
DEF_UNASSIGNED = ugettext('This task has been Reopened.')


DEF_UNCLAIMED_TITLE = ugettext('Claim Removed')
DEF_UNCLAIMED = ugettext(
    'The claim on this task has been removed, someone else can claim it now.')


DEF_UNPUBLISHED_TITLE = ugettext('Task Unpublished')
DEF_UNPUBLISHED = ugettext('The task is unpublished.')


DELETE_EXPIRATION = datetime.timedelta(minutes=10)

# TODO(ljvderijk): Add basic subscribers when task is created

def _spawnUpdateTask(entity, transactional=False):
  """Spawns a task to update the state of the task."""
  update_url = '/tasks/gci/task/update/%s' % entity.key().id()
  new_task = taskqueue.Task(eta=entity.deadline, url=update_url)
  new_task.add('gci-update', transactional=transactional)


def hasTaskEditableStatus(task):
  """Reports whether or not a task is in one of the editable states.

  Args:
    task: Any task_model.GCITask.
  """
  editable_statuses = task_model.UNAVAILABLE[:]
  editable_statuses.append(task_model.OPEN)
  return task.status in editable_statuses


def isOwnerOfTask(task, profile):
  """Returns true if the given profile is owner/student of the task.

  Args:
    task: The task_model.GCITask entity
    profile: The GCIProfile which might be the owner of the task
  """
  if not (task_model.GCITask.student.get_value_for_datastore(task) and profile):
    return False
  else:
    student_key = ndb.Key.from_old_key(
        task_model.GCITask.student.get_value_for_datastore(task))
    return student_key == profile.key


def canClaimRequestTask(task, profile):
  """Returns true if the given profile is allowed to claim the task.

  Args:
    task: The task_model.GCITask entity
    profile: The GCIProfile which we check whether it can claim the task.
  """
  # check if the task can be claimed at all
  if task.status not in task_model.CLAIMABLE:
    return False

  # check if the user is allowed to claim this task
  q = task_model.GCITask.all()
  q.filter('student', profile.key.to_old_key())
  q.filter('program', task.program)
  q.filter('status IN', task_model.ACTIVE_CLAIMED_TASK)

  max_tasks = task.program.nr_simultaneous_tasks
  count = q.count(max_tasks)

  has_forms = profile_logic.hasStudentFormsUploaded(profile)

  return count < max_tasks and has_forms


def canSubmitWork(task, profile):
  """Returns true if the given profile can submit work to this task.

  Args:
    task: The task_model.GCITask entity
    profile: The GCIProfile to check

  """
  return (task.deadline and
          datetime.datetime.utcnow() <= task.deadline and
          isOwnerOfTask(task, profile) and
          task.status in task_model.TASK_IN_PROGRESS)


def publishTask(task, publisher):
  """Publishes the task.

  This will put the task in the Open state. A comment will also be generated
  to record this event.

  Args:
    task: GCITask entity.
    publisher: GCIProfile of the user that publishes the task.
  """
  task.status = task_model.OPEN

  comment_props = {
      'parent': task,
      'title': DEF_PUBLISHED_TITLE,
      'content': DEF_PUBLISHED,
      'created_by': publisher.key.parent().to_old_key(),
  }
  comment = GCIComment(**comment_props)

  comment_txn = comment_logic.storeAndNotifyTxn(comment)

  def publishTaskTxn():
    task.put()
    comment_txn()
    _spawnUpdateTask(task, transactional=True)

  return db.run_in_transaction(publishTaskTxn)


def unpublishTask(task, unpublisher):
  """Unpublishes the task.

  This will put the task in the Unpublished state. A comment will also be
  generated to record this event.

  Args:
    task: GCITask entity.
    publisher: GCIProfile of the user that unpublishes the task.
  """
  task.status = task_model.UNPUBLISHED

  comment_props = {
      'parent': task,
      'title': DEF_UNPUBLISHED_TITLE,
      'content': DEF_UNPUBLISHED,
      'created_by': unpublisher.key.parent().to_old_key(),
  }
  comment = GCIComment(**comment_props)

  comment_txn = comment_logic.storeAndNotifyTxn(comment)

  def unpublishTaskTxn():
    task.put()
    comment_txn()
    _spawnUpdateTask(task, transactional=True)

  return db.run_in_transaction(unpublishTaskTxn)


def assignTask(task, student_key, assigner):
  """Assigns the task to the student.

  This will put the task in the Claimed state and set the student and deadline
  property. A comment will also be generated to record this event.

  Args:
    task: task_model.GCITask entity.
    student_key: Key of the student to assign
    assigner: GCIProfile of the user that assigns the student.
  """
  task.student = student_key.to_old_key()
  task.status = 'Claimed'
  task.deadline = datetime.datetime.now() + \
      datetime.timedelta(hours=task.time_to_complete)

  student = student_key.get()
  comment_props = {
      'parent': task,
      'title': DEF_ASSIGNED_TITLE,
      'content': DEF_ASSIGNED %(
          student.public_name, task.time_to_complete),
      'created_by': assigner.key.parent().to_old_key(),
  }
  comment = GCIComment(**comment_props)

  comment_txn = comment_logic.storeAndNotifyTxn(comment)

  def assignTaskTxn():
    task.put()
    comment_txn()
    _spawnUpdateTask(task, transactional=True)

  return db.run_in_transaction(assignTaskTxn)


def unassignTask(task, profile):
  """Unassigns a task.

  This will put the task in the Reopened state and reset the student and
  deadline property. A comment will also be generated to record this event.

  Args:
    task: task_model.GCITask entity.
    profile: GCIProfile of the user that unassigns the task.
  """
  task.student = None
  task.status = task_model.REOPENED
  task.deadline = None

  comment_props = {
      'parent': task,
      'title': DEF_UNASSIGNED_TITLE,
      'content': DEF_UNASSIGNED,
      'created_by': profile.key.parent().to_old_key()
  }
  comment = GCIComment(**comment_props)

  comment_txn = comment_logic.storeAndNotifyTxn(comment)

  def unassignTaskTxn():
    task.put()
    comment_txn()

  return db.run_in_transaction(unassignTaskTxn)


def closeTask(task, profile):
  """Closes the task.

  Args:
    task: task_model.GCITask entity.
    profile: GCIProfile of the user that closes the task.
  """
  from soc.modules.gci.tasks.ranking_update import startUpdatingTask

  task.status = 'Closed'
  task.closed_on = datetime.datetime.now()
  task.deadline = None

  comment_props = {
      'parent': task,
      'title': DEF_CLOSED_TITLE,
      'content': DEF_CLOSED,
      'created_by': profile.key.parent().to_old_key()
  }
  comment = GCIComment(**comment_props)

  comment_txn = comment_logic.storeAndNotifyTxn(comment)

  student_key = ndb.Key.from_old_key(
      task_model.GCITask.student.get_value_for_datastore(task))
  student = student_key.get()

  # student, who worked on the task, should receive a confirmation
  # having submitted his or her first task
  query = queryAllTasksClosedByStudent(student, keys_only=True)
  if query.get() is None: # this is the first task
    confirmation = profile_logic.sendFirstTaskConfirmationTxn(student, task)
  else:
    confirmation = lambda: None

  org_score_txn = org_score_logic.updateOrgScoreTxn(task, student)

  @db.transactional(xg=True)
  def closeTaskTxn():
    task.put()
    comment_txn()
    startUpdatingTask(task, transactional=True)
    confirmation()
    org_score_txn()

  # TODO(daniel): move this to a transaction when other models are NDB
  student = student_key.get()
  student.student_data.number_of_completed_tasks += 1
  student.put()

  return closeTaskTxn()


def needsWorkTask(task, profile):
  """Closes the task.

  Args:
    task: task_model.GCITask entity.
    profile: GCIProfile of the user that marks this task as needs more work.
  """
  task.status = 'NeedsWork'

  comment_props = {
      'parent': task,
      'title': DEF_NEEDS_WORK_TITLE,
      'content': DEF_NEEDS_WORK,
      'created_by': profile.key.parent().to_old_key()
  }
  comment = GCIComment(**comment_props)

  comment_txn = comment_logic.storeAndNotifyTxn(comment)

  def needsWorkTaskTxn():
    task.put()
    comment_txn()

  return db.run_in_transaction(needsWorkTaskTxn)


def extendDeadline(task, delta, profile):
  """Extends the deadline of a task.

  Args:
    task: The task to extend the deadline for.
    delta: The timedelta object to be added to the current deadline.
    profile: GCIProfile of the user that extends the deadline.
  """
  if task.deadline:
    deadline = task.deadline + delta
  else:
    deadline = datetime.datetime.utcnow() + delta

  task.deadline = deadline

  comment_props = {
      'parent': task,
      'title': DEF_EXTEND_DEADLINE_TITLE,
      'content': DEF_EXTEND_DEADLINE %(delta.days, delta.seconds/3600),
      'created_by': profile.key.parent().to_old_key()
  }
  comment = GCIComment(**comment_props)

  comment_txn = comment_logic.storeAndNotifyTxn(comment)

  def extendDeadlineTxn():
    task.put()
    comment_txn()

  return db.run_in_transaction(extendDeadlineTxn)


def claimRequestTask(task, student):
  """Used when a student requests to claim a task.

  Updates the status of the tasks and places a comment notifying the org
  that someone wants to work on this task.

  Args:
    task: The task to claim.
    student: Profile of the student that wants to claim the task.
  """
  task.status = 'ClaimRequested'
  task.student = student.key.to_old_key()

  if student.key.to_old_key() not in task.subscribers:
    task.subscribers.append(student.key.to_old_key())

  comment_props = {
      'parent': task,
      'title': DEF_CLAIM_REQUEST_TITLE,
      'content': DEF_CLAIM_REQUEST,
      'created_by': student.key.parent().to_old_key()
  }
  comment = GCIComment(**comment_props)

  comment_txn = comment_logic.storeAndNotifyTxn(comment)

  def claimRequestTaskTxn():
    task.put()
    comment_txn()

  return db.run_in_transaction(claimRequestTaskTxn)


def unclaimTask(task):
  """Used when a student requests to unclaim a task.

  Args:
    task: The task to unclaim.
  """
  student_key = task_model.GCITask.student.get_value_for_datastore(task)

  task.student = None
  task.status = task_model.REOPENED
  task.deadline = None

  comment_props = {
      'parent': task,
      'title': DEF_UNCLAIMED_TITLE,
      'content': DEF_UNCLAIMED,
      'created_by': student_key.parent()
  }
  comment = GCIComment(**comment_props)

  comment_txn = comment_logic.storeAndNotifyTxn(comment)

  def unclaimTaskTxn():
    task.put()
    comment_txn()

  return db.run_in_transaction(unclaimTaskTxn)


def sendForReview(task, student):
  """Send in a task for review.

  Args:
    task: The task to send for review.
    student: Profile of the student that is sending in the work.
  """
  task.status = 'NeedsReview'

  comment_props = {
      'parent': task,
      'title': DEF_SEND_FOR_REVIEW_TITLE,
      'content': DEF_SEND_FOR_REVIEW,
      'created_by': student.key.parent().to_old_key(),
  }
  comment = GCIComment(**comment_props)

  comment_txn = comment_logic.storeAndNotifyTxn(comment)

  def sendForReviewTxn():
    task.put()
    comment_txn()

  return db.run_in_transaction(sendForReviewTxn)


def updateTaskStatus(task):
  """Method used to transit a task from a state to another state
  depending on the context. Whenever the deadline has passed.

  To be called by the automated system running on Appengine tasks or
  whenever the public page for the task is loaded in case the Appengine task
  framework is running late.

  Args:
    task: The task_model.GCITask entity

  Returns:
    Boolean indicating whether the task has been updated.
  """
  if not task.deadline or datetime.datetime.now() < task.deadline:
    # do nothing if there is no deadline or it hasn't passed yet
    return False

  if task.program.timeline.stop_all_work_deadline < datetime.datetime.now():
    # do not change the status of the task after the work deadline ends
    return False

  # the transition depends on the current state of the task
  transit_func = STATE_TRANSITIONS.get(task.status, None)

  if not transit_func:
    logging.warning('Invalid state to transfer from %s', task.status)
    return False

  # update the task and create a comment
  task, comment = transit_func(task)

  _storeTaskAndComment(task, comment)

  if task.deadline:
    # only if there is a deadline set we should schedule another task
    _spawnUpdateTask(task)

  return True

def _storeTaskAndComment(task, comment):
  """Stores the task and comment and notifies those that are interested in a
  single transaction.
  """
  comment_txn = comment_logic.storeAndNotifyTxn(comment)
  def updateTaskAndCreateCommentTxn():
    db.put(task)
    comment_txn()

  db.run_in_transaction(updateTaskAndCreateCommentTxn)

def transitFromClaimed(task):
  """Makes a state transition of a GCI Task from Claimed state
  to ActionNeeded.

  Args:
    task: The task_model.GCITask entity
  """
  # deadline is extended by 24 hours.
  task.status = 'ActionNeeded'
  task.deadline = task.deadline + datetime.timedelta(hours=24)

  comment_props = {
      'parent': task,
      'title': DEF_ACTION_NEEDED_TITLE,
      'content': DEF_ACTION_NEEDED,
  }
  comment = GCIComment(**comment_props)

  return task, comment


def transitFromNeedsReview(task):
  """Makes a state transition of a GCI Task that is in NeedsReview state.

  This state transition is special since it actually only clears the deadline
  field and does not change value of the state field. A Task is in this state
  when work has been submitted and it has not been reviewed before the original
  deadline runs out.

  Args:
    task: The task_model.GCITask entity
  """
  # Clear the deadline since mentors are not forced to review work within a
  # certain period.
  task.deadline = None

  comment_props = {
      'parent': task,
      'title': DEF_NO_MORE_WORK_TITLE,
      'content': DEF_NO_MORE_WORK,
  }
  comment = GCIComment(**comment_props)

  return task, comment


def transitFromActionNeeded(task):
  """Makes a state transition of a GCI Task from ActionNeeded state
  to Reopened state.

  Args:
    task: The task_model.GCITask entity
  """
  # reopen the task
  task.student = None
  task.status = task_model.REOPENED
  task.deadline = None

  comment_props = {
      'parent': task,
      'title': DEF_REOPENED_TITLE,
      'content': DEF_REOPENED,
  }
  comment = GCIComment(**comment_props)

  return task, comment


def transitFromNeedsWork(task):
  """Makes a state transition of a GCI Task from NeedsWork state
  to Reopened state.

  A task that has been marked as Needs(more)Work will NOT get a deadline
  extension and will be reopened immediately.

  Args:
    task: The task_model.GCITask entity
  """
  task.student = None
  task.status = task_model.REOPENED
  task.deadline = None

  comment_props = {
      'parent': task,
      'title': DEF_REOPENED_TITLE,
      'content': DEF_REOPENED,
  }
  comment = GCIComment(**comment_props)

  return task, comment


def delete(task):
  """Delete existing task from datastore.
  """
  def task_delete_txn(task):
    """Performs all necessary operations in a single transaction when a task
    is deleted.
    """
    to_delete = []
    to_delete += GCIComment.all(keys_only=True).ancestor(task)
    to_delete += GCIWorkSubmission.all(keys_only=True).ancestor(task)
    to_delete += [task.key()]

    db.delete(to_delete)

  db.run_in_transaction(task_delete_txn, task)


def getFeaturedTask(program):
  """Return a featured task for a given program.

  Args:
    program: entity representing the program from which the featured
        tasks should be fetched
  """
  # expiry time to fetch the new featured gci task entity
  # the current expiry time is 2 hours.
  expiry_time = datetime.timedelta(seconds=7200)

  def queryForTask():
    query = task_model.GCITask.all()
    query.filter('is_featured', True)
    query.filter('program', program)

    return query

  q = queryForTask()

  # the cache stores a 3-tuple in the order gci task entity,
  # cursor and the last time the cache was updated
  fgt_cache = memcache.get('featured_gci_task' + program.key().name())

  if fgt_cache:
    cached_task, cached_cursor, cache_expiry_time = fgt_cache
    if (cached_task and not
        datetime.datetime.now() > cache_expiry_time + expiry_time):
      return cached_task
    else:
      q.with_cursor(cached_cursor)
      if q.count() == 0:
        q = queryForTask()

  for task in q:
    if task.status in task_model.CLAIMABLE + task_model.ACTIVE_CLAIMED_TASK:
      new_task = task
      break
  else:
    return None

  new_cursor = q.cursor()
  memcache.set(
    key='featured_gci_task',
    value=(new_task, new_cursor, datetime.datetime.now()))

  return new_task


def setTaskStatus(task_key, status):
  """Set the status of the specified task in a transaction.
  """

  def setTaskStatusTxn():
    task = task_model.GCITask.get(task_key)
    task.status = status
    task.put()

  db.run_in_transaction(setTaskStatusTxn)


# define the state transition functions
STATE_TRANSITIONS = {
    'Claimed': transitFromClaimed,
    'NeedsReview': transitFromNeedsReview,
    'ActionNeeded': transitFromActionNeeded,
    'NeedsWork': transitFromNeedsWork,
    }

# useful queries for tasks
def queryClaimableTasksForProgram(program):
  q = task_model.GCITask.all()
  q.filter('program', program)
  q.filter('status IN', task_model.CLAIMABLE)
  return q


def queryAllTasksClosedByStudent(profile, keys_only=False):
  """Returns a query for all the tasks that have been closed by the
  specified profile.
  """
  if not profile.is_student:
    raise ValueError('Only students can be queried for closed tasks.')

  return task_model.GCITask.all(keys_only=keys_only).filter(
      'student', profile.key.to_old_key()).filter('status', 'Closed')


def queryCurrentTaskForStudent(profile, keys_only=False):
  """Returns a query for the task that the specified student
  is currently working on.
  """
  if not profile.is_student:
    raise ValueError('Only students can be queried for their current task.')

  return task_model.GCITask.all(keys_only=keys_only).filter(
      'student', profile.key.to_old_key()).filter('status != ', 'Closed')


def querySubscribedTasksForProfile(profile_key, keys_only=False):
  """Returns a query for tasks that the specified profile is subscribed to."""
  return task_model.GCITask.all(keys_only=keys_only).filter(
      'subscribers', profile_key.to_old_key())


def queryForStudentAndOrganizationAndStatus(student_key, org_key, status,
    keys_only=False):
  """Returns a query for all tasks for the specified student,
  organization and status.

  Args:
    student_key: Student key.
    org_key: Organization key.
    status: List of allowed statuses of the tasks to query.

  Returns:
    A query to fetch all tasks with the specified properties.
  """
  query = task_model.GCITask.all()
  query.filter('student', student_key)
  query.filter('org', org_key)

  if isinstance(status, list):
    query.filter('status IN', status)
  else:
    query.filter('status', status)

  return query


def queryForOrganization(org, keys_only=False):
  """Returns a query for all tasks for the specified organization.
  """
  return task_model.GCITask.all().filter('org', org)
