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
  ]

from google.appengine.ext import db

from soc.logic.exceptions import AccessViolation
from soc.logic.exceptions import NotFound
from soc.views.helper import access_checker

from soc.modules.gci.models.task import GCITask


class Mutator(access_checker.Mutator):

  def unsetAll(self):
    self.data.task = access_checker.unset
    super(Mutator, self).unsetAll()

  def taskFromKwargs(self):
    """Sets the task entity in RequestData object.
    """
    self.profileFromKwargs()
    assert access_checker.isSet(self.data.url_profile)

    # kwargs which defines a task
    fields = ['sponsor', 'program', 'organization', 'task_link_id']

    key_name = '/'.join(self.data.kwargs[field] for field in fields)
    self.data.task = GCITask.get_by_key_name(key_name)

    if not self.data.task:
      error_msg = access_checker.DEF_KEYNAME_BASED_ENTITY_NOT_EXISTS_MSG_FMT % {
          'model': 'GCITask',
          'key_name': key_name
          }
      raise NotFound(error_msg)


class DeveloperMutator(access_checker.DeveloperMutator,
                       Mutator):
  pass


class AccessChecker(access_checker.AccessChecker):

  def isTaskInURLValid(self):
    """Checks if the task in URL exists.
    """
    assert access_checker.isSet(self.data.task)

    fields = ['sponsor', 'program', 'organization', 'task_link_id']
    key_name = '/'.join(self.data.kwargs[field] for field in fields)
    if not self.data.task:
      error_msg = access_checker.DEF_KEYNAME_BASED_ENTITY_NOT_EXISTS_MSG_FMT % {
          'model': 'GCITask',
          'key_name': key_name
          }
      raise AccessViolation(error_msg)

    invalid_status = ['Invalid', 'Unpublished', 'Unapproved']
    if self.data.task.status in invalid_status:
      error_msg = access_checker.DEF_KEYNAME_BASED_ENTITY_INVALID_MSG_FMT % {
          'model': 'GCITask',
          'key_name': key_name,
          }
      raise AccessViolation(error_msg)

class DeveloperAccessChecker(access_checker.DeveloperAccessChecker,
                             AccessChecker):
  pass
