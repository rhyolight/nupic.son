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
from google.appengine.ext import ndb

from soc.modules.gci.logic import profile as profile_logic
from soc.modules.gci.models.score import GCIOrgScore
from soc.modules.gci.models.task import GCITask


# TODO(daniel): this should be a parameter of the program
# determines the maximal position from which the student may be
# proposed to be a winner by organization admins
POSSIBLE_WINNER_MAX_POSITION = 5


def updateOrgScoreTxn(task, student):
  """Returns a transactional function that updates GCIOrgScore for
  the specified task.
  """
  org_key = GCITask.org.get_value_for_datastore(task)

  def txn():
    org_score_query = queryForAncestorAndOrg(student.key.to_old_key(), org_key)

    org_score = org_score_query.get()
    if not org_score:
      org_score = GCIOrgScore(parent=student.key.to_old_key(), org=org_key)

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

    # check if the task is actually closed
    if task.status != 'Closed':
      raise ValueError("The task %d is not closed" % task.key().id())

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

    student_info = profile_logic.queryStudentInfoForParent(student_key).get()
    student_info.number_of_completed_tasks += len(tasks)
    to_put.append(student_info)

    db.put(to_put)

  return txn

# TODO(daniel): add unit tests
def clearOrgScoresTxn(profile_key):
  """Clears all OrgScore entities for the student with the specified
  profile key.
  """
  def txn():
    org_scores = queryForAncestor(profile_key).fetch(1000)
    db.delete(org_scores)

    student_info = profile_logic.queryStudentInfoForParent(profile_key).get()
    student_info.number_of_completed_tasks = 0
    student_info.put()

  return txn


def getPossibleWinners(org):
  """Returns the possible winners for the specified organization which can
  be chosen by the organization admins.
  """
  # TODO(daniel): this should not retrieve all the students and sort them.
  # Currently it is necessary, as it is not possible to order the entities
  # by the length of the list. Instead, number of completed tasks should
  # be explicitly added to OrgScore model.
  org_scores = queryForOrg(org).fetch(1000)
  org_scores = sorted(org_scores, key=lambda e: len(e.tasks), reverse=True)

  profiles = [org_score.parent() for org_score in org_scores]

  return profiles[:POSSIBLE_WINNER_MAX_POSITION]


def queryForOrg(org, keys_only=False):
  """Return the query to fetch OrgScore entities for the specified
  organization.
  """
  return GCIOrgScore.all(keys_only=keys_only).filter('org', org)


def queryForAncestorAndOrg(ancestor, org, keys_only=False):
  """Returns the query to fetch OrgScore entities for the specified
  ancestor and organization.
  """
  return GCIOrgScore.all(keys_only=keys_only).ancestor(
      ancestor).filter('org', org)

def queryForAncestor(ancestor, keys_only=False):
  """Returns the query to fetch OrgScore entities for the specified
  ancestor.
  """
  return GCIOrgScore.all(keys_only=keys_only).ancestor(ancestor)
