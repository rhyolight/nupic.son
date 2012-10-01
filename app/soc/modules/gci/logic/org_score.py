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


def queryForAncestorAndOrg(ancestor, org, keys_only=False):
  """Returns the query to fetch OrgScore entities for the specified
  ancestor and organization.
  """
  return GCIOrgScore.all().ancestor(ancestor).filter('org', org)
