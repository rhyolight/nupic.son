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

import urllib

from google.appengine.ext import ndb

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext

from melange.request import exception
from melange.utils import time

from soc.logic import dicts
from soc.models.org_app_record import OrgAppRecord
from soc.views.helper import access_checker

from soc.modules.gci.models.profile import GCIProfile
from soc.modules.gci.models.task import GCITask
from soc.modules.gci.models.task import UNPUBLISHED
from soc.modules.gci.models import conversation as gciconversation_model
from soc.modules.gci.logic import conversation as gciconversation_logic


DEF_ALREADY_PARTICIPATING_AS_NON_STUDENT = ugettext(
    'You cannot register as a student since you are already a '
    'mentor or organization administrator in %s.')

DEF_ALL_WORK_STOPPED = ugettext(
    'All work on tasks has stopped. You can no longer place comments, '
    'submit work or make any changes to existing tasks.')

DEF_COMMENTING_NOT_ALLOWED = ugettext(
    "No more comments can be placed at this time.")

DEF_NO_TASK_CREATE_PRIV = ugettext(
    'You do not have sufficient privileges to create a new task for %s.' )

DEF_NO_TASK_EDIT_PRIV = ugettext(
    'You do not have sufficient privileges to edit a new task for %s.' )

DEF_NO_PREV_ORG_MEMBER = ugettext(
    'To apply as an organization for GCI you must have been a member of an '
    'organization in Google Summer of Code or Google Code In.')

DEF_NOT_ORG_ADMIN_FOR_ORG_APP = ugettext(
    "You should be listed as one of the administrators on %(org_name)s's "
    "organization application to create a new organization profile for "
    "%(org_name)s.")

DEF_TASK_UNEDITABLE_STATUS = ugettext(
    'This task is already published and published tasks cannot be edited.')

DEF_TASK_MUST_BE_IN_STATES = ugettext(
    'The task must be in one of the followings states %s')

DEF_TASK_MAY_NOT_BE_IN_STATES = ugettext(
    'The task may not be in one of the followings states %s')

DEF_ORG_APP_REJECTED = ugettext(
    'This org application has been rejected')

DEF_NOT_IN_CONVERSATION = ugettext(
    'You do not have sufficient privileges to view this conversation.')


class Mutator(access_checker.Mutator):
  """Helper class for access checking.

  Mutates the data object as requested.
  """

  def unsetAll(self):
    self.data.task = access_checker.unset
    self.data.comments = access_checker.unset
    self.data.work_submissions = access_checker.unset
    self.data.is_visible = access_checker.unset
    self.data.full_edit = access_checker.unset
    self.data.conversation = access_checker.unset
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
      error_msg = access_checker.DEF_ID_BASED_ENTITY_NOT_EXISTS % {
          'model': 'GCITask',
          'id': id,
          }
      raise exception.NotFound(message=error_msg)

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

  def conversationFromKwargs(self):
    """Sets the GCIConversation entity in the RequestData object.

    Args:
      messages: If true, the messages for this conversation are added to
                RequestData
    """
    id = long(self.data.kwargs['id'])
    conversation = gciconversation_model.GCIConversation.get_by_id(id)

    if (not conversation or
        ndb.Key.to_old_key(conversation.program) != self.data.program.key()):
      error_msg = access_checker.DEF_ID_BASED_ENTITY_NOT_EXISTS % {
          'model': 'GCIConversation',
          'id': id
          }
      raise exception.NotFound(message=error_msg)

    self.data.conversation = conversation

  def orgAppFromOrgId(self):
    org_id = self.data.GET.get('org_id')

    if not org_id:
      raise exception.BadRequest(message='Missing org_id')

    q = OrgAppRecord.all()
    q.filter('survey', self.data.org_app)
    q.filter('org_id', org_id)

    self.data.org_app_record = q.get()

    if not self.data.org_app_record:
      raise exception.NotFound(
          message="There is no org_app for the org_id %s" % org_id)

  def fullEdit(self, full_edit=False):
    """Sets full_edit to True/False depending on the status of the task.
    """
    self.data.full_edit = full_edit


class DeveloperMutator(access_checker.DeveloperMutator,
                       Mutator):
  pass


class AccessChecker(access_checker.AccessChecker):
  """Access checker for GCI specific methods.
  """

  def isTaskVisible(self):
    """Checks if the task is visible to the public.

    Returns: True if the task is visible, if the task is not visible
        but the user can edit the task, False.
    """
    assert access_checker.isSet(self.data.task)

    # TODO(nathaniel): Yep, this is weird.
    can_edit = False
    try:
      self.checkCanUserEditTask()
      self.checkHasTaskEditableStatus()
      self.checkTimelineAllowsTaskEditing()
      can_edit = True
    except exception.UserError:
      pass

    if not self.data.timeline.tasksPubliclyVisible():
      if can_edit:
        return False
      period = self.data.timeline.tasksPubliclyVisibleOn()
      raise exception.Forbidden(
          message=access_checker.DEF_PAGE_INACTIVE_BEFORE % period)

    if not self.data.task.isPublished():
      if can_edit:
        return False
      raise exception.Forbidden(message=access_checker.DEF_PAGE_INACTIVE)

    return True

  def isTaskInState(self, states):
    """Checks if the task is in any of the given states.

    Args:
      states: List of states in which a task may be for this check to pass.
    """
    assert access_checker.isSet(self.data.task)

    if self.data.task.status not in states:
      raise exception.Forbidden(message=DEF_TASK_MUST_BE_IN_STATES % states)

  def isTaskNotInStates(self, states):
    """Checks if the task is not in any of the given states.

    Args:
      states: List of states in which a task may not be for this check to pass.
    """
    assert access_checker.isSet(self.data.task)

    if self.data.task.status in states:
      raise exception.Forbidden(message=DEF_TASK_MAY_NOT_BE_IN_STATES % states)

  def canApplyStudent(self, edit_url):
    """Checks if a user may apply as a student to the program.
    """
    if self.data.profile:
      if self.data.profile.student_info:
        raise exception.Redirect(edit_url)
      else:
        raise exception.Forbidden(
            message=DEF_ALREADY_PARTICIPATING_AS_NON_STUDENT % (
            self.data.program.name))

    self.studentSignupActive()

    # custom pre-registration age check for GCI students
    age_check = self.data.request.COOKIES.get('age_check', None)
    if not age_check or age_check == '0':
      # no age check done or it failed
      kwargs = dicts.filter(self.data.kwargs, ['sponsor', 'program'])
      age_check_url = reverse('gci_age_check', kwargs=kwargs)
      raise exception.Redirect(age_check_url)
    else:
      self.isLoggedIn()

  def hasNonStudentProfileInAProgram(self):
    """Check if the user has participated in the previous programs.

    This checks if the user has at least one non-student profile in previous
    programs.
    """
    from soc.modules.gsoc.models.profile import GSoCProfile

    if not self.data.user:
      raise exception.Forbidden(message=DEF_NO_PREV_ORG_MEMBER)

    q = GSoCProfile.all(keys_only=True)
    q.filter('is_mentor', True)
    q.filter('status', 'active')
    q.filter('user', self.data.user)
    gsoc_profile = q.get()

    q = GCIProfile.all(keys_only=True)
    q.filter('is_mentor', True)
    q.filter('status', 'active')
    q.filter('user', self.data.user)
    gci_profile = q.get()

    if not (gsoc_profile or gci_profile):
      raise exception.Forbidden(message=DEF_NO_PREV_ORG_MEMBER)

  def canTakeOrgApp(self):
    """Check if the user can take the org app.

    A user can take the GCI org app if he/she participated in GSoC or GCI as
    a non-student and has a non-student profile for the current program.
    """
    # TODO(daniel): make this a program setting - sometimes it may be possible
    # to accept organizations which have not participated before
    self.hasNonStudentProfileInAProgram()

    self.hasProfileOrRedirectToCreate('org_admin')

  def isOrgAppAccepted(self):
    """Checks if the org app stored in request data is accepted.
    """
    assert self.data.org_app_record

    if self.data.org_app_record.status != 'accepted':
      raise exception.Forbidden(message=DEF_ORG_APP_REJECTED)

  def isUserAdminForOrgApp(self):
    """Checks if the user is listed as an admin for the org app in RequestData.
    """
    assert self.data.org_app
    assert self.data.org_app_record

    if not self.data.user or self.data.user.key() not in [
        self.data.org_app_record.main_admin.key(),
        self.data.org_app_record.backup_admin.key()]:
      raise exception.Forbidden(message=DEF_NOT_ORG_ADMIN_FOR_ORG_APP % {
          'org_name': self.data.org_app_record.name})

  def hasProfileOrRedirectToCreate(self, role, get_params=None):
    """Checks if user has a profile and redirects to "Create Profile" page
    if a profile is not present.

    Args:
      role: type of profile that should potentially be created. May be one
        of: org_admin, mentor, student.
      get_params: optional dictionary with GET parameters that should be
        appended to the redirect URL
    """
    if not self.data.profile:
      get_params = get_params or {}
      profile_url = self.data.redirect.createProfile('org_admin').urlOf(
          'create_gci_profile', secure=True)

      if get_params:
        profile_url += '?' + urllib.urlencode(get_params)

      raise exception.Redirect(profile_url)

  def isBeforeAllWorkStopped(self):
    """Raises exception.UserError if all work on tasks has stopped."""
    if not self.data.timeline.allWorkStopped():
      return

    raise exception.Forbidden(message=DEF_ALL_WORK_STOPPED)

  def isCommentingAllowed(self):
    """Raises exception.UserError if commenting is not allowed."""
    if not self.data.timeline.allWorkStopped() or (
        not self.data.timeline.allReviewsStopped() and
        self.data.mentorFor(self.data.task.org)):
      return

    raise exception.Forbidden(message=DEF_COMMENTING_NOT_ALLOWED)

  def canCreateTask(self):
    """Checks whether the currently logged in user can edit the task.
    """
    return self.canCreateTaskWithRequiredRole('mentor')

  def canBulkCreateTask(self):
    """Checks whether the currently logged in user can bulk create tasks.
    """
    return self.canCreateTaskWithRequiredRole('org_admin')

  def canCreateTaskWithRequiredRole(self, required_role):
    """Checks whether the currently logged in user can create or edit
    a task, when the specified role is required.
    """
    assert access_checker.isSet(self.data.organization)
    assert access_checker.isSet(self.data.org_admin_for)
    assert access_checker.isSet(self.data.mentor_for)

    if required_role == 'mentor':
      valid_org_keys = [o.key() for o in self.data.mentor_for]
    elif required_role == 'org_admin':
      valid_org_keys = [o.key() for o in self.data.org_admin_for]
    else:
      raise ValueError('Invalid required_role argument ' + str(required_role))

    if self.data.organization.key() not in valid_org_keys:
      raise exception.Forbidden(message=DEF_NO_TASK_CREATE_PRIV % (
          self.data.organization.name))

    if (time.isBefore(self.data.timeline.orgsAnnouncedOn()) \
        or self.data.timeline.tasksClaimEnded()):
      raise exception.Forbidden(message=access_checker.DEF_PAGE_INACTIVE)

  def canUserEditTask(self):
    """Returns True/False depending on whether the currently logged in user
    can edit the task.
    """
    assert access_checker.isSet(self.data.task)
    assert access_checker.isSet(self.data.mentor_for)

    task = self.data.task

    valid_org_keys = [o.key() for o in self.data.mentor_for]
    if task.org.key() not in valid_org_keys:
      return False

    return True

  def checkCanUserEditTask(self):
    """Checks whether the currently logged in user can edit the task.
    """
    assert access_checker.isSet(self.data.task)

    if not self.canUserEditTask():
      raise exception.Forbidden(
          message=DEF_NO_TASK_EDIT_PRIV % (self.data.task.org.name))

  def hasTaskEditableStatus(self):
    """Returns True/False depending on whether the task is in one of the
    editable states.
    """
    assert access_checker.isSet(self.data.task)

    task = self.data.task

    if task.status not in (UNPUBLISHED + ['Open']):
      return False

    return True

  def checkHasTaskEditableStatus(self):
    """Checks whether the task is in one of the editable states.

    We specifically do not allow editing of tasks which are already claimed.
    """
    if not self.hasTaskEditableStatus():
      raise exception.Forbidden(message=DEF_TASK_UNEDITABLE_STATUS)

  def timelineAllowsTaskEditing(self):
    """Returns True/False depending on whether orgs can edit task depending
    on where in the program timeline we are currently in.
    """
    if (time.isBefore(self.data.timeline.orgsAnnouncedOn()) \
        or self.data.timeline.tasksClaimEnded()):
      return False

    return True

  def checkTimelineAllowsTaskEditing(self):
    """Checks if organizations can edit tasks at the current time in
    the program.
    """
    if not self.timelineAllowsTaskEditing():
      raise exception.Forbidden(message=access_checker.DEF_PAGE_INACTIVE)

  def isUserInConversation(self):
    """Checks if the user is part of a conversation.
    """
    assert access_checker.isSet(self.data.conversation)
    assert access_checker.isSet(self.data.user)

    query = gciconversation_logic.queryConversationUserForConversationAndUser(
        self.data.conversation.key, ndb.Key.from_old_key(self.data.user.key()))

    if query.count() == 0:
      raise exception.Forbidden(message=DEF_NOT_IN_CONVERSATION)


class DeveloperAccessChecker(access_checker.DeveloperAccessChecker):
  """Developer access checker for GCI specific methods.
  """
  def isTaskVisible(self):
    return True
