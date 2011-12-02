#!/usr/bin/env python2.5
#
# Copyright 2009 the Melange authors.
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

"""This module contains the GCI Task Model.
"""


from google.appengine.ext import db

from django.utils.translation import ugettext

from taggable.taggable import Tag
from taggable.taggable import Taggable
from taggable.taggable import tag_property

import soc.models.base
import soc.models.role

import soc.modules.gci.models.program

from soc.modules.gci.models.comment import GCIComment
from soc.modules.gci.models.work_submission import GCIWorkSubmission


# states in which a task does not show up publicly
UNPUBLISHED = ['Unpublished', 'Unapproved']
# states in which a student can claim a task
CLAIMABLE = ['Open', 'Reopened']
# States in which we consider the task to count towards the task quota of
# the student.
ACTIVE_CLAIMED_TASK = ['ClaimRequested', 'Claimed', 'ActionNeeded',
                       'AwaitingRegistration', 'NeedsWork', 'NeedsReview']
# States in which we consider that the student can work on a task as long
# as the deadline has not passed.
TASK_IN_PROGRESS = ['Claimed', 'ActionNeeded', 'NeedsWork', 'NeedsReview']
# states in which the student is allowed to transition the task to NeedsReview
SEND_FOR_REVIEW_ALLOWED = ['Claimed', 'ActionNeeded', 'NeedsWork']


class DifficultyLevel(object):
  """Enumerates all difficulty levels for GCI Tasks.
  """

  EASY = 'Easy'
  MEDOIM = 'Medium'
  HARD = 'Hard'

DIFFICULTIES = [
    DifficultyLevel.EASY, DifficultyLevel.MEDIUM, DifficultyLevel.HARD]


class GCITask(Taggable, soc.models.base.ModelWithFieldAttributes):
  """Model for a task used in GCI workflow.
  """

  #: Required field indicating the "title" of the task
  title = db.StringProperty(required=True,
                            verbose_name=ugettext('Task Title'))
  title.help_text = ugettext('Title of the task')

  #: Required field containing the description of the task
  description = db.TextProperty(required=True,
                                verbose_name=ugettext('Description'))
  description.help_text = ugettext('Complete description of the task')

  #: Field indicating the difficulty level of the Task.
  difficulty_level = db.StringProperty(required=True, 
      verbose_name=('Difficulty'), choices=DIFFICULTIES)

  #: To be removed, when conversion is done.
  difficulty = tag_property('difficulty')

  #: Required field which contains the type of the task. These types are
  #: configured by a Program Admin.
  task_type = tag_property('task_type')

  #: Field which contains the arbitrary tags for the task. These tags can
  #: be assigned by Org Admins and mentors.
  arbit_tag = tag_property('arbit_tag')

  #: A field which contains time allowed for completing the task (in hours)
  #: from the moment that this task has been assigned to a Student
  time_to_complete = db.IntegerProperty(required=True,
                                        verbose_name=('Time to Complete'))
  time_to_complete.help_text = ugettext(
      'Time allowed to complete the task, in hours, once it is claimed')

  #: List of Mentors assigned to this task. A Mentor who creates this
  #: task is assigned as the Mentor by default. An Org Admin will have
  #: to assign a Mentor upon task creation.
  mentors = db.ListProperty(item_type=db.Key, default=[])

  #: Student profile to whom this task is currently assigned to.
  student = db.ReferenceProperty(reference_class=soc.models.role.Role,
                                 required=False,
                                 collection_name='assigned_tasks')

  #: Program in which this Task has been created
  program = db.ReferenceProperty(
      reference_class=soc.modules.gci.models.program.GCIProgram,
      required=True, collection_name='tasks')

  #: Program in which this Task has been created
  org = db.ReferenceProperty(
      reference_class=soc.modules.gci.models.organization.GCIOrganization,
      required=True, collection_name='org_tasks')

  #: Required property which holds the state, the Task is currently in.
  #: This is a hidden field not shown on forms. Handled by logic internally.
  #: The state can be one of the following:
  #: Unapproved: If Task is created by a Mentor, this is the automatically
  #:   assigned state.
  #: Unpublished: This Task is not published yet.
  #: Open: This Task is open and ready to be claimed.
  #: Reopened: This Task has been claimed but never finished and has been
  #:   reopened.
  #: ClaimRequested: A Student has requested to claim this task.
  #: Claimed: This Task has been claimed and someone is working on it.
  #: ActionNeeded: Work on this Task must be submitted for review within
  #:   24 hours.
  #: Closed: Work on this Task has been completed to the org's content.
  #: AwaitingRegistration: Student has completed work on this task, but
  #:   needs to complete Student registration before this task is closed.
  #:   This status is now deprecated since we register before any interaction.
  #: NeedsWork: This work on this Tasks needs a bit more brushing up. This
  #:   state is followed by a Mentor review.
  #: NeedsReview: Student has submitted work for this task and it should
  #:   be reviewed by a Mentor.
  #: Invalid: The Task is deleted either by an Org Admin/Mentor
  status = db.StringProperty(
      required=True, verbose_name=ugettext('Status'),
      choices=['Unapproved', 'Unpublished', 'Open', 'Reopened',
               'ClaimRequested', 'Claimed', 'ActionNeeded',
               'Closed', 'AwaitingRegistration', 'NeedsWork',
               'NeedsReview', 'Invalid'],
      default='Unapproved')

  #: Indicates when the Task was closed. Its value is None before it is
  #: completed.
  closed_on = db.DateTimeProperty(required=False,
                                  verbose_name=ugettext('Closed on'))

  #: This field is set to the next deadline that will have consequences for
  #: this Task. For instance this will store a DateTime property which will
  #: tell when this Task should be completed.
  deadline = db.DateTimeProperty(required=False,
                                 verbose_name=ugettext('Deadline'))

  # Property holding the list of GCIProfiles who are subscribed to the task.
  subscribers = db.ListProperty(item_type=db.Key, default=[])

  #: Required field containing the Mentor/Org Admin who created this task.
  #: If site developer has created the task, it is empty.
  created_by = db.ReferenceProperty(reference_class=soc.models.role.Role,
                                    required=False,
                                    collection_name='created_tasks',
                                    verbose_name=ugettext('Created by'))

  #: Date when the proposal was created
  created_on = db.DateTimeProperty(required=True, auto_now_add=True,
                                   verbose_name=ugettext('Created on'))

  #: Required field containing the Mentor/Org Admin who last edited this
  #: task. It changes only when Mentor/Org Admin changes title, description,
  #: difficulty, task_type, time_to_complete. If site developer has modified
  #: the task, it is empty.
  modified_by = db.ReferenceProperty(reference_class=soc.models.role.Role,
                                     required=False,
                                     collection_name='edited_tasks',
                                     verbose_name=ugettext('Modified by'))

  #: Date when the proposal was last modified, should be set manually on edit
  modified_on = db.DateTimeProperty(required=True, auto_now_add=True,
                                    verbose_name=ugettext('Modified on'))

  #: The task can be marked to be featured on program home page.
  is_featured = db.BooleanProperty(default=False, required=True,
                                   verbose_name=ugettext('Featured'))
  is_featured.help_text = ugettext(
      'Should this task be featured on the program homepage.')

  def __init__(self, parent=None, key_name=None,
               app=None, **entity_values):
    """Constructor for GCITask Model.

    Args:
        See Google App Engine APIs.
    """

    # explicitly call the AppEngine datastore Model constructor
    # pylint: disable=W0233
    db.Model.__init__(self, parent, key_name, app, **entity_values)

    # call the Taggable constructor to initialize the tags specified as
    # keyword arguments
    Taggable.__init__(self, task_type=TaskTypeTag,
                      difficulty=TaskDifficultyTag,
                      arbit_tag=TaskArbitraryTag)

  def taskDifficulty(self, all_difficulties=None):
    if all_difficulties:
      key = self.key()
      difficulties = [i for i in all_difficulties if key in i.tagged]
    else:
      difficulties = self.difficulty

    if len(difficulties) == 1:
      return difficulties[0]

    self.difficulty = {'tags': ['Unknown'], 'scope': self.program}
    return self.difficulty[0]

  def taskType(self, all_types=None, ret_list=False):
    if all_types:
      key = self.key()
      types = [i for i in all_types if key in i.tagged]
    else:
      types = self.task_type

    return self.tags_string(types, ret_list=ret_list)

  def taskArbitTag(self, ret_list=False):
    return self.tags_string(self.arbit_tag, ret_list=ret_list)

  def taskDifficultyName(self, all_difficulties=None):
    difficulty = self.taskDifficulty(all_difficulties)
    return difficulty.tag

  def taskDifficultyValue(self, all_difficulties=None):
    difficulty = self.taskDifficulty(all_difficulties)
    return "%s (%s)" % (difficulty.value, difficulty.tag)

  def taskTimeToComplete(self):
    days = self.time_to_complete / 24
    hours = self.time_to_complete % 24
    result = []

    if days == 1:
      result.append("1 day")
    if days > 1:
      result.append("%d days" % days)

    if days and hours:
      result.append(" and ")

    if hours == 1:
      result.append("1 hour")
    if hours > 1:
      result.append("%d hours" % hours)

    return "".join(result)

  def isPublished(self):
    """Returns True if the task is published.
    """
    return self.status not in UNPUBLISHED

  def workSubmissions(self):
    """Returns the GCIWorksubmissions that have the given task as parent.
    """
    q = GCIWorkSubmission.all()
    q.ancestor(self)
    return q.fetch(1000)

  def comments(self):
    """Returns the GCIComments that have the given task as parent.

    The results are sorted by the date on which they have been created.
    """
    q = GCIComment.all()
    q.ancestor(self)
    q.order('created_on')
    return q.fetch(1000)


class TaskTag(Tag):
  """Model for storing all Task tags.
  """

  order = db.IntegerProperty(required=True, default=0)

  @classmethod
  def get_by_scope(cls, scope):
    """Get the list of tag objects that has the given scope and sorts the
       result by order values.
    """

    tags = db.Query(cls).filter('scope =', scope).order('order').fetch(1000)
    return tags

  @classmethod
  def get_highest_order(cls, scope):
    """Get a tag with highest order.
    """

    tag = db.Query(cls).filter('scope =', scope).order('-order').get()
    if tag:
      return tag.order
    else:
      return -1

  @classmethod
  def update_order(cls, scope, tag_name, order):
    """Updates the order of the tag.
    """

    tag = cls.get_by_scope_and_name(scope, tag_name)
    if tag:
      tag.order = order
      tag.put()
    return tag

  @classmethod
  def get_or_create(cls, scope, tag_name, order=0):
    """Get the Tag object that has the tag value given by tag_value.
    """

    tag_key_name = cls._key_name(scope.key().name(), tag_name)
    existing_tag = cls.get_by_key_name(tag_key_name)
    if existing_tag is None:
      # the tag does not yet exist, so create it.
      if not order:
        order = cls.get_highest_order(scope=scope) + 1
      def create_tag_txn():
        new_tag = cls(key_name=tag_key_name, tag=tag_name,
                      scope=scope, order=order)
        new_tag.put()
        return new_tag
      existing_tag = db.run_in_transaction(create_tag_txn)
    return existing_tag


class TaskTypeTag(TaskTag):
  """Model for storing of task type tags.
  """
  pass


class TaskDifficultyTag(TaskTag):
  """Model for storing of task difficulty level tags.
  """
  value = db.IntegerProperty(default=0, verbose_name=ugettext('value'))


class TaskArbitraryTag(TaskTag):
  """Model for storing of arbitrary tags.
  """

  def __init__(self, *args, **kwds):
    """Initialization function.
    """

    TaskTag.__init__(self, *args, **kwds)
    self.auto_delete = True
