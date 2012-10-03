#!/usr/bin/env python2.5
#
# Copyright 2012 the Melange authors.
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

"""GCIOrgScore logic methods and queries.
"""


from google.appengine.ext import db

from soc.modules.gci.models.score import GCIOrgScore
from soc.modules.gci.models.task import GCITask


def updateOrgScoreTxn(task):
  """Returns a transactional function that updates GCIOrgScore for
  the specified task.
  """
  org_key = GCITask.org.get_value_for_datastore(task)
  student_key = GCITask.student.get_value_for_datastore(task)

  def txn():
    query = queryForAncestorAndOrg(student_key, org_key, True)
  
    org_score = query.get()
    if not org_score:
      org_score = GCIOrgScore(parent=student_key, org=org_key)
  
    org_score.tasks.append(task.key())
    org_score.put()

  return txn


def updateOrgScoresTxn(tasks):
  """Returns a transaction function that updates GCIOrgScore for the
  specified list of tasks that belong to the same student.
  """
  if not tasks:
    return lambda: None

  student_key = GCITask.student.get_value_for_datastore(tasks[0])

  tasks_by_org = {}
  for task in tasks:
    # check if all the tasks belong to the same student
    if GCITask.student.get_value_for_datastore(task) != student_key:
      raise ValueError("Specified tasks belong to more than one student")

    org_key = GCITask.org.get_value_for_datastore(task)

    if org_key not in tasks_by_org:
      tasks_by_org[org_key] = [task]
    else:
      tasks_by_org[org_key].append(task)

  def txn():
    to_put = []

    for org_key, tasks in tasks_by_org.iteritems():
      query = queryForAncestorAndOrg(student_key, org_key)

      org_score = query.get()
      if not org_score:
        org_score = GCIOrgScore(parent=student_key, org=org_key)

      for task in tasks:
        org_score.tasks.append(task.key())

      to_put.append(org_score)

    db.put(to_put)

  return txn


def queryForOrg(org, keys_only=False):
  """Return the query to fetch OrgScore entities for the specified
  organization.
  """
  return GCIOrgScore.all().filter('org', org)


def queryForAncestorAndOrg(ancestor, org, keys_only=False):
  """Returns the query to fetch OrgScore entities for the specified
  ancestor and organization.
  """
  return GCIOrgScore.all().ancestor(ancestor).filter('org', org)
