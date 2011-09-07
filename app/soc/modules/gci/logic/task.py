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
    '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]


from soc.modules.gci.models.task import ACTIVE_CLAIMED_TASK
from soc.modules.gci.models.task import CLAIMABLE
from soc.modules.gci.models.task import GCITask


def isOwnerOfTask(task, user):
  """Returns true if the given profile is owner/student of the task.

  Args:
    task: The GCITask entity
    user: The User which might be the owner of the task
  """
  return task.user.key() == user.key()


def canClaimRequestTask(task, user):
  """Returns true if the given profile is allowed to claim the task.

  Args:
    task: The GCITask entity
    user: The User which we check whether it can claim the task.
  """

  # check if the task can be claimed at all
  if task.status not in CLAIMABLE:
    return False

  # check if the user is allowed to claim this task
  q = GCITask.all()
  q.filter('user', user)
  q.filter('program', task.program)
  q.filter('status IN', ACTIVE_CLAIMED_TASK)

  max = task.program.nr_simultaneous_tasks
  count = q.count(max)

  return count < max


def canAdministrateTask(task, profile):
  """Returns true if the given profile is allowed to administrate the task.

  Args:
    task: The GCITask entity
    profile: The GCIProfile which we check whether it can administrate the task.
  """
  if profile.is_student:
    return False

  org = task.org.key()
  return org in profile.is_mentor_for or org in profile.is_org_admin_for
