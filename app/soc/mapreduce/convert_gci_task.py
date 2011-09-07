#!/usr/bin/python2.5
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

"""GCI Task updating MapReduce.
"""

__authors__ = [
  '"Madhusudan.C.S" <madhusudancs@gmail.com>',
  ]


from google.appengine.ext import db
from google.appengine.ext.mapreduce import operation

from soc.models.host import Host
from soc.models.role import Role

from soc.modules.gci.models.comment import GCIComment
from soc.modules.gci.models.mentor import GCIMentor
from soc.modules.gci.models.org_admin import GCIOrgAdmin
from soc.modules.gci.models.profile import GCIProfile
from soc.modules.gci.models.student import GCIStudent
from soc.modules.gci.models.task import GCITask
from soc.modules.gci.models.task_subscription import GCITaskSubscription
from soc.modules.gci.models.work_submission import GCIWorkSubmission


TASK_PROPERTIES = GCITask.properties()
# We do not want history property in the new entities in any more because
# we are not using it
TASK_PROPERTIES.pop('scope', 'history')

COMMENT_PROPERTIES = GCIComment.properties()
WORK_SUBMISSION_PROPERTIES = GCIWorkSubmission.properties()


def process_task(task):
  """Conversion to make GCI Tasks ID based and getting rid of unnecessary
  properties.
  """
  # Get the values for all the properties in the GCITask model from the
  # old entity to create the new entity.
  new_task_properties = {}
  for prop in TASK_PROPERTIES:
    new_task_properties[prop] = getattr(task, prop)
    new_task_properties['org'] = task.scope

  # We do not want a separate model for subscriptions because there
  # is only one property that stores the list of all subscribers to
  # the task which can be stored in the task itself. So moving it to
  # the task.
  q = GCITaskSubscription.all()
  q.filter('task', task)
  task_subscription = q.get()

  new_task_properties['subscribers'] = task_subscription.subscribers

  new_task = GCITask(**new_task_properties)
  new_task_key = new_task.put()

  if new_task_key:
    # Update all the comments with the new task as the parent
    comments = GCIComment.all().ancestor(new_task_key).fetch(1000)
    for c in comments:
      new_comm_properties = {}
      for c_prop in COMMENT_PROPERTIES:
        new_comm_properties[c_prop] = getattr(c, c_prop)
      new_comment = GCIComment(parent=new_task_key, **new_comm_properties)
      yield operation.db.Put(new_comment)
      yield operation.counters.Increment("comment_updated")

    # Update all the work submission entities with the new task as the parent
    work_submissions = GCIWorkSubmission.all().ancestor(
        new_task_key).fetch(1000)
    for ws in work_submissions:
      new_ws_properties = {}
      for ws_prop in WORK_SUBMISSION_PROPERTIES:
        new_ws_properties[ws_prop] = getattr(ws, ws_prop)
      new_ws = GCIWorkSubmission(parent=new_task_key, **new_comm_properties)
      yield operation.db.Put(new_ws)
      yield operation.counters.Increment("work_submission_updated")

    yield operation.counters.Increment("task_updated")


def new_task_for_old(task):
  q = GCITask.all(keys_only=True)
  q.filter('org', task.scope)
  q.filter('link_id', task.link_id)
  return q.get()


def process_student_ranking(student_ranking):
  """Replace all the references to the list of old tasks to the new tasks.
  """
  tasks = GCITask.get(student_ranking.tasks)
  new_tasks = []
  for t in tasks:
    new_t = new_task_for_old(t)
    if new_t:
      new_tasks.append(new_t)

  student_ranking.tasks = new_tasks

  yield operation.db.Put(student_ranking)
  yield operation.counters.Increment("student_ranking_updated")


def process_tag(tag):
  """Replace all the references to the list of old tasks to the new tasks.
  """
  tagged = db.get(tag.tagged)
  new_tagged_keys = []
  for t in tagged:
    try:
      task = GCITask.get(t)
      new_tagged = new_task_for_old(task)
    except db.KindError:
      new_tagged = t

    new_tagged_keys.append(new_tagged)

  tag.tagged = new_tagged_keys

  yield operation.db.Put(tag)
  yield operation.counters.Increment("tag_updated")
