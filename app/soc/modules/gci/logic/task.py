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
"""GCITask logic methods.
"""

__authors__ = [
    '"Madhusudan.C.S" <madhusudancs@gmail.com>',
    '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]

import datetime
import logging

from google.appengine.api import memcache
from google.appengine.ext import db

from django.utils.translation import ugettext

from soc.logic import tags

from soc.modules.gci.logic import comment as comment_logic
from soc.modules.gci.models.comment import GCIComment
from soc.modules.gci.models.task import ACTIVE_CLAIMED_TASK
from soc.modules.gci.models.task import CLAIMABLE
from soc.modules.gci.models.task import TASK_IN_PROGRESS
from soc.modules.gci.models.task import GCITask
from soc.modules.gci.models.work_submission import GCIWorkSubmission


TAG_NAMES = ['arbit_tag', 'difficulty', 'task_type']
TAGS_SERVICE = tags.TagsService(TAG_NAMES)


DEF_ACTION_NEEDED_TITLE = ugettext('Initial Deadline passed')
DEF_ACTION_NEEDED_MSG = ugettext(
    'Melange has detected that the initial deadline has passed and it has '
    'set the task status to ActionNeeded. You have 24 hours to submit work '
    'before it is reopened.')


DEF_ASSIGNED_TITLE = ugettext('Task Assigned')
DEF_ASSIGNED_MSG_FMT = ugettext(
    'This task has been assigned to %s. '
    'You have %i hours to complete this task, good luck!')


DEF_CLAIM_REQUEST_TITLE = ugettext('Task Claimed')
DEF_CLAIM_REQUEST_MSG = ugettext('I would like to work on this task.')


DEF_CLOSED_TITLE = ugettext('Task Closed')
DEF_CLOSED_MSG = ugettext(
    'Congratulations, this task has been completed successfully.')


DEF_EXTEND_DEADLINE_TITLE = ugettext('Deadline extended')
DEF_EXTEND_DEADLINE_FMT = ugettext(
    'The deadline of the task has been extended with %i days and %i hours.')


DEF_NO_MORE_WORK_TITLE = ugettext('No more Work can be submitted')
DEF_NO_MORE_WORK_MSG = ugettext(
    'Melange has detected that the deadline has passed and no more work can '
    'be submitted. The submitted work should be reviewed.')


DEF_REOPENED_TITLE = ugettext('Task Reopened')
DEF_REOPENED_MSG = ugettext(
    'Melange has detected that the final deadline has passed and it has '
    'reopened the task.')


DEF_UNASSIGNED_TITLE = ugettext('Task Reopened')
DEF_UNASSIGNED_MSG = ugettext('This task has been Reopened.')


DEF_UNCLAIMED_TITLE = ugettext('Claim Removed')
DEF_UNCLAIMED_MSG = ugettext(
    'The claim on this task has been removed, someone else can claim it now.')

# TODO(ljvderijk): Add basic subscribers when task is created

def isOwnerOfTask(task, profile):
  """Returns true if the given profile is owner/student of the task.

  Args:
    task: The GCITask entity
    profile: The GCIProfile which might be the owner of the task
  """
  return profile and task.student and task.student.key() == profile.key()


def canClaimRequestTask(task, profile):
  """Returns true if the given profile is allowed to claim the task.

  Args:
    task: The GCITask entity
    profile: The GCIProfile which we check whether it can claim the task.
  """
  # check if the task can be claimed at all
  if task.status not in CLAIMABLE:
    return False

  # check if the user is allowed to claim this task
  q = GCITask.all()
  q.filter('student', profile)
  q.filter('program', task.program)
  q.filter('status IN', ACTIVE_CLAIMED_TASK)

  max_tasks = task.program.nr_simultaneous_tasks
  count = q.count(max_tasks)

  return count < max_tasks


def canSubmitWork(task, profile):
  """Returns true if the given profile can submit work to this task.

  Args:
    task: The GCITask entity
    profile: The GCIProfile to check

  """
  if not task.deadline or datetime.datetime.utcnow() > task.deadline:
    # deadline has passed
    return False

  return isOwnerOfTask(task, profile) and task.status in TASK_IN_PROGRESS

def assignTask(task, student, assigner):
  """Assigns the task to the student.

  This will put the task in the Claimed state and set the student and deadline
  property. A comment will also be generated to record this event.

  Args:
    task: GCITask entity.
    student: GCIProfile entity of a student.
    assigner: GCIProfile of the user that assigns the student.
  """
  from soc.modules.gci.tasks import task_update

  task.student = student
  task.status = 'Claimed'
  task.deadline = datetime.datetime.now() + \
      datetime.timedelta(hours=task.time_to_complete)

  comment_props = {
      'parent': task,
      'title': DEF_ASSIGNED_TITLE,
      'content': DEF_ASSIGNED_MSG_FMT %(
          student.public_name, task.time_to_complete),
      'created_by': assigner.user,
  }
  comment = GCIComment(**comment_props)

  comment_txn = comment_logic.storeAndNotifyTxn(comment)

  def assignTaskTxn():
    task.put()
    comment_txn()
    task_update.spawnUpdateTask(task, transactional=True)

  return db.run_in_transaction(assignTaskTxn)


def unassignTask(task, user):
  """Unassigns a task.

  This will put the task in the Reopened state and reset the student and
  deadline property. A comment will also be generated to record this event.

  Args:
    task: GCITask entity.
    user: GCIProfile of the user that unassigns the task.
  """
  task.student = None
  task.status = 'Reopened'
  task.deadline = None

  comment_props = {
      'parent': task,
      'title': DEF_UNASSIGNED_TITLE,
      'content': DEF_UNASSIGNED_MSG,
      'created_by': user.user
  }
  comment = GCIComment(**comment_props)

  comment_txn = comment_logic.storeAndNotifyTxn(comment)

  def unassignTaskTxn():
    task.put()
    comment_txn()

  return db.run_in_transaction(unassignTaskTxn)


def closeTask(task, user):
  """Closes the task.

  Args:
    task: GCITask entity.
    user: GCIProfile of the user that closes the task.
  """
  task.status = 'Closed'
  task.deadline = None

  comment_props = {
      'parent': task,
      'title': DEF_CLOSED_TITLE,
      'content': DEF_CLOSED_MSG,
      'created_by': user.user
  }
  comment = GCIComment(**comment_props)

  comment_txn = comment_logic.storeAndNotifyTxn(comment)

  # TODO(ljvderijk): If this is the student's first task send email about
  # the forms they need to fill in. See Issue 1308.
  def closeTaskTxn():
    task.put()
    comment_txn()

  return db.run_in_transaction(closeTaskTxn)


def extendDeadline(task, delta, user):
  """Extends the deadline of a task.

  Args:
    task: The task to extend the deadline for.
    delta: The timedelta object to be added to the current deadline.
    user: GCIProfile of the user that extends the deadline.
  """
  if task.deadline:
    deadline = task.deadline + delta
  else:
    deadline = datetime.datetime.utcnow() + delta

  task.deadline = deadline

  comment_props = {
      'parent': task,
      'title': DEF_EXTEND_DEADLINE_TITLE,
      'content': DEF_EXTEND_DEADLINE_FMT %(delta.days, delta.seconds/3600),
      'created_by': user.user
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
    student: GCIProfile of the student that wants to claim the task.
  """
  task.status = 'ClaimRequested'
  task.student = student

  comment_props = {
      'parent': task,
      'title': DEF_CLAIM_REQUEST_TITLE,
      'content': DEF_CLAIM_REQUEST_MSG,
      'created_by': student.user
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
  student = task.student

  task.student = None
  task.status = 'Reopened'
  task.deadline = None

  comment_props = {
      'parent': task,
      'title': DEF_UNCLAIMED_TITLE,
      'content': DEF_UNCLAIMED_MSG,
      'created_by': student.user
  }
  comment = GCIComment(**comment_props)

  comment_txn = comment_logic.storeAndNotifyTxn(comment)

  def unclaimTaskTxn():
    task.put()
    comment_txn()

  return db.run_in_transaction(unclaimTaskTxn)


def updateTaskStatus(task):
  """Method used to transit a task from a state to another state
  depending on the context. Whenever the deadline has passed.

  To be called by the automated system running on Appengine tasks or
  whenever the public page for the task is loaded in case the Appengine task
  framework is running late.

  Args:
    task: The GCITask entity

  Returns:
    Boolean indicating whether the task has been updated.
  """
  from soc.modules.gci.tasks import task_update

  if not task.deadline or datetime.datetime.now() < task.deadline:
    # do nothing if there is no deadline or it hasn't passed yet
    return False

  # the transition depends on the current state of the task
  transit_func = STATE_TRANSITIONS[task.status]

  if not transit_func:
    logging.warning('Invalid state to transfer from %s' %task.status)
    return False

  # update the task and create a comment
  task, comment = transit_func(task)

  _storeTaskAndComment(task, comment)

  if task.deadline:
    # only if there is a deadline set we should schedule another task
    task_update.spawnUpdateTask(task)

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
    task: The GCITask entity
  """
  # deadline is extended by 24 hours.
  task.status = 'ActionNeeded'
  task.deadline = task.deadline + datetime.timedelta(hours=24)

  comment_props = {
      'parent': task,
      'title': DEF_ACTION_NEEDED_TITLE,
      'content': DEF_ACTION_NEEDED_MSG,
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
    task: The GCITask entity
  """
  # Clear the deadline since mentors are not forced to review work within a
  # certain period.
  task.deadline = None

  comment_props = {
      'parent': task,
      'title': DEF_NO_MORE_WORK_TITLE,
      'content': DEF_NO_MORE_WORK_MSG,
  }
  comment = GCIComment(**comment_props)

  return task, comment


def transitFromActionNeeded(task):
  """Makes a state transition of a GCI Task from ActionNeeded state
  to Reopened state.

  Args:
    task: The GCITask entity
  """
  # reopen the task
  task.student = None
  task.status = 'Reopened'
  task.deadline = None

  comment_props = {
      'parent': task,
      'title': DEF_REOPENED_TITLE,
      'content': DEF_REOPENED_MSG,
  }
  comment = GCIComment(**comment_props)

  return task, comment


def transitFromNeedsWork(task):
  """Makes a state transition of a GCI Task from NeedsWork state
  to Reopened state.

  A task that has been marked as Needs(more)Work will NOT get a deadline 
  extension and will be reopened immediately.

  Args:
    task: The GCITask entity
  """
  task.student = None
  task.status = 'Reopened'
  task.deadline = None

  comment_props = {
      'parent': task,
      'title': DEF_REOPENED_TITLE,
      'content': DEF_REOPENED_MSG,
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

  TAGS_SERVICE.removeAllTagsForEntity(task)
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
    query = GCITask.all()
    query.filter('is_featured', True)
    query.filter('program', program)

    return query

  q = queryForTask()

  # the cache stores a 3-tuple in the order gci task entity,
  # cursor and the last time the cache was updated
  fgt_cache = memcache.get('featured_gci_task')

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
    if task.status in CLAIMABLE + ACTIVE_CLAIMED_TASK:
      new_task = task
      break
  else:
    return None

  new_cursor = q.cursor()
  memcache.set(
    key='featured_gci_task',
    value=(new_task, new_cursor, datetime.datetime.now()))

  return new_task


# define the state transition functions
STATE_TRANSITIONS = {
    'Claimed': transitFromClaimed,
    'NeedsReview': transitFromNeedsReview,
    'ActionNeeded': transitFromActionNeeded,
    'NeedsWork': transitFromNeedsWork,
    }
