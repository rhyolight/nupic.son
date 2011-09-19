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

"""Module containing the AccessChecker class that contains helper functions
for checking access.
"""

__authors__ = [
    '"Selwyn Jacob" <selwynjacob90@gmail.com>',
    '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]


from soc.logic.exceptions import AccessViolation
from soc.logic.exceptions import NotFound
from soc.views.helper import access_checker

from soc.modules.gci.models.task import GCITask


class Mutator(access_checker.Mutator):
  """Helper class for access checking.

  Mutates the data object as requested.
  """

  def unsetAll(self):
    self.data.task = access_checker.unset
    self.data.comments = access_checker.unset
    self.data.work_submissions = access_checker.unset
    super(Mutator, self).unsetAll()

  def taskFromKwargs(self, comments=False, work_submissions=True):
    """Sets the GCITask entity in RequestData object.

    The entity that is set will always be in a valid state and for the program
    that is set in the RequestData.

    Args:
      comments: If true the comments on this task are added to RequestData
      work_submissions: If true the work submissions on this task are added to
                        RequestData
    """
    id = long(self.data.kwargs['id'])
    task = GCITask.get_by_id(id)

    if not task or (task.program.key() != self.data.program.key()) or \
        task.status == 'invalid':
      error_msg = access_checker.DEF_ID_BASED_ENTITY_NOT_EXISTS_MSG_FMT % {
          'model': 'GCITask',
          'id': id,
          }
      raise NotFound(error_msg)

    self.data.task = task

    if comments:
      self.data.comments = task.comments()

    if work_submissions:
      self.data.work_submissions = task.workSubmissions()

  def taskFromKwargsIfId(self):
    """Sets the GCITask entity in RequestData object if ID exists or None.
    """
    if not 'id' in self.data.kwargs:
      self.data.task = None
      return

    self.taskFromKwargs()


class DeveloperMutator(access_checker.DeveloperMutator,
                       Mutator):
  pass


class AccessChecker(access_checker.AccessChecker):
  """Access checker for GCI specific methods.
  """

  def isTaskVisible(self):
    """Checks if the task is visible to the public.
    """
    assert access_checker.isSet(self.data.task)

    if not self.data.timeline.tasksPubliclyVisible():
      period = self.data.timeline.tasksPubliclyVisibleOn()
      raise AccessViolation(
          access_checker.DEF_PAGE_INACTIVE_BEFORE_MSG_FMT % period)

    if not self.data.task.isPublished():
      error_msg = access_checker.DEF_PAGE_INACTIVE_MSG
      raise AccessViolation(error_msg)


class DeveloperAccessChecker(access_checker.DeveloperAccessChecker):
  """Developer access checker for GCI specific methods.
  """
  pass
