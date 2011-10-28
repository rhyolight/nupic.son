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


from django.core.urlresolvers import reverse
from django.utils.translation import ugettext

from soc.logic import dicts
from soc.logic.exceptions import AccessViolation
from soc.logic.exceptions import NotFound
from soc.logic.exceptions import RedirectRequest
from soc.views.helper import access_checker
from soc.views.helper import request_data

from soc.modules.gci.models.profile import GCIProfile
from soc.modules.gci.models.task import GCITask


DEF_ALREADY_PARTICIPATING_AS_NON_STUDENT_MSG = ugettext(
    'You cannot register as a student since you are already a '
    'mentor or organization administrator in %s.')

DEF_ALL_WORK_STOPPED_MSG = ugettext(
    'All work on tasks has stopped. You can no longer place comments, '
    'submit work or make any changes to existing tasks.')

DEF_NO_TASK_CREATE_PRIV_MSG_FMT = ugettext(
    'You do not have sufficient privileges to create a new task for '
    'the organization %s.' )

DEF_NO_TASK_EDIT_PRIV_MSG_FMT = ugettext(
    'You do not have sufficient privileges to edit a new task for '
    'the organization %s.' )

DEF_NO_PREV_ORG_MEMBER_MSG = ugettext(
    'To apply as an organization for GCI you must have been a member of an '
    'organization in Google Summer of Code or Google Code In.')

DEF_TASK_UNEDITABLE_STATUS_MSG = ugettext(
    'The task cannot be edited because it is already claimed once.')

DEF_TASK_MUST_BE_IN_STATES_FMT = ugettext(
    'The task must be in one of the followings states %s')

DEF_TASK_MAY_NOT_BE_IN_STATES_FMT = ugettext(
    'The task may not be in one of the followings states %s')

class Mutator(access_checker.Mutator):
  """Helper class for access checking.

  Mutates the data object as requested.
  """

  def unsetAll(self):
    self.data.task = access_checker.unset
    self.data.comments = access_checker.unset
    self.data.work_submissions = access_checker.unset
    super(Mutator, self).unsetAll()

  def profileFromKwargs(self):
    """Retrieves profile from the kwargs for GCI.
    """
    super(Mutator, self).profileFromKwargs(GCIProfile)

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

  def isTaskInState(self, states):
    """Checks if the task is in any of the given states.

    Args:
      states: List of states in which a task may be for this check to pass.
    """
    assert access_checker.isSet(self.data.task)

    if self.data.task.status not in states:
      raise AccessViolation(DEF_TASK_MUST_BE_IN_STATES_FMT %states)

  def isTaskNotInStates(self, states):
    """Checks if the task is not in any of the given states.

    Args:
      states: List of states in which a task may not be for this check to pass.
    """
    assert access_checker.isSet(self.data.task)

    if self.data.task.status in states:
      raise AccessViolation(DEF_TASK_MAY_NOT_BE_IN_STATES_FMT %states)

  def canApplyStudent(self, edit_url):
    """Checks if a user may apply as a student to the program.
    """
    self.isLoggedIn()

    if self.data.profile:
      if self.data.profile.student_info:
        raise RedirectRequest(edit_url)
      else:
        raise AccessViolation(
            DEF_ALREADY_PARTICIPATING_AS_NON_STUDENT_MSG % 
            self.data.program.name)

    self.studentSignupActive()

    # custom pre-registration age check for GCI students
    age_check = self.data.request.COOKIES.get('age_check', None)
    if not age_check or age_check == '0':
      # no age check done or it failed
      kwargs = dicts.filter(self.data.kwargs, ['sponsor', 'program'])
      age_check_url = reverse('gci_age_check', kwargs=kwargs)
      raise RedirectRequest(age_check_url)

  def canTakeOrgApp(self):
    """A user can take the GCI org app if he/she participated in GSoC or GCI
    as a non-student.
    """
    from soc.modules.gsoc.models.profile import GSoCProfile

    self.isUser()

    q = GSoCProfile.all()
    q.filter('is_student', False)
    q.filter('status IN', ['active', 'inactive'])
    q.filter('user', self.data.user)
    gsoc_profile = q.get()

    q = GCIProfile.all()
    q.filter('is_student', False)
    q.filter('status IN', ['active', 'inactive'])
    q.filter('user', self.data.user)
    gci_profile = q.get()

    if not (gsoc_profile or gci_profile):
      raise AccessViolation(DEF_NO_PREV_ORG_MEMBER_MSG)

  def isBeforeAllWorkStopped(self):
    """Raises AccessViolation if all work on tasks has stopped.
    """
    if not self.data.timeline.allWorkStopped():
      return

    raise AccessViolation(DEF_ALL_WORK_STOPPED_MSG)

  def canCreateTask(self):
    """Checks whether the currently logged in user can edit the task.
    """
    assert access_checker.isSet(self.data.organization)
    assert access_checker.isSet(self.data.mentor_for)

    valid_org_keys = [o.key() for o in self.data.mentor_for]
    if self.data.organization.key() not in valid_org_keys:
      raise AccessViolation(DEF_NO_TASK_CREATE_PRIV_MSG_FMT % (
          self.data.organization.name))

    if (request_data.isBefore(self.data.timeline.orgsAnnouncedOn()) \
        or self.data.timeline.tasksClaimEnded()):
      raise AccessViolation(access_checker.DEF_PAGE_INACTIVE_MSG)

  def canEditTask(self):
    """Checks whether the currently logged in user can edit the task.
    """
    assert access_checker.isSet(self.data.task)
    assert access_checker.isSet(self.data.mentor_for)

    task = self.data.task

    valid_org_keys = [o.key() for o in self.data.mentor_for]
    if task.org.key() not in valid_org_keys:
      raise AccessViolation(DEF_NO_TASK_EDIT_PRIV_MSG_FMT % (
          task.org.name))

    if task.status not in ['Unapproved', 'Unpublished', 'Open']:
      raise AccessViolation(DEF_TASK_UNEDITABLE_STATUS_MSG)

    if (request_data.isBefore(self.data.timeline.orgsAnnouncedOn()) \
        or self.data.timeline.tasksClaimEnded()):
      raise AccessViolation(access_checker.DEF_PAGE_INACTIVE_MSG)

class DeveloperAccessChecker(access_checker.DeveloperAccessChecker):
  """Developer access checker for GCI specific methods.
  """
  pass
