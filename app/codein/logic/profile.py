# Copyright 2013 the Melange authors.
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

"""Logic for profiles."""

from codein import types

from melange.logic import profile as profile_logic
from melange.utils import rich_bool

from soc.modules.gci.models import task as task_model


MENTOR_HAS_TASK_ASSIGNED = 'mentor_has_task_assigned'
NOT_MENTOR_FOR_ORG = 'not_mentor_for_org'

def canResignAsMentorForOrg(profile, org_key):
  """Tells whether the specified profile can resign from their mentor role
  for the specified organization.

  A mentor may be removed from the list of mentors of an organization, if
  he or she does not have any tasks, which have not been closed, assigned.

  Please note that this function executes a non-ancestor query, so it cannot
  be safely used within transactions.

  Args:
    profile: profile entity.
    org_key: organization key.

  Returns:
    RichBool whose value is set to True, if the mentor is allowed to resign.
    Otherwise, RichBool whose value is set to False and extra part is a string
    that represents the reason why the user is not allowed to resign.
  """
  if org_key not in profile.mentor_for:
    return rich_bool.RichBool(False, extra=NOT_MENTOR_FOR_ORG)

  # TODO(daniel): if all work is already completed/reviewed, 
  # the mentor can always resign?

  # the mentor cannot have any non-closed tasks assigned
  query = task_model.GCITask.all()
  query.filter('mentors', profile.key())
  query.filter('status !=', 'Closed')
  if query.get():
    return rich_bool.RichBool(False, extra=MENTOR_HAS_TASK_ASSIGNED)
  else:
    return rich_bool.TRUE


def canResignAsOrgAdminForOrg(profile, org_key):
  """Tells whether the specified profile can resign from their organization
  administrator role for the specified organization.

  An organization administrator may be removed from the list of administrators
  of an organization, if there is at least one other user with this role.

  Args:
    profile: profile entity.
    org_key: organization key.

  Returns:
    True, if the mentor is allowed to resign; False otherwise
  """
  return profile_logic.canResignAsOrgAdminForOrg(
      profile, org_key, models=types.CI_MODELS)


def isNoRoleEligibleForOrg(profile, org_key):
  """Tells whether the specified user is eligible to have no role for the
  specified organization.

  A user is eligible for no role if he or she does not have any obligations
  to the organization.

  Please note that this function executes a non-ancestor query, so it cannot
  be safely used within transactions.

  Args:
    profile: profile entity.
    org_key: organization key.

  Returns:
    RichBool whose value is set to True, if the user is eligible for no
    role for the specified organization. Otherwise, RichBool whose value is set
    to False and extra part is a string that represents a reason why the user
    is not eligible to resign from role at this time.
  """
  if org_key in profile.org_admin_for:
    result = canResignAsOrgAdminForOrg(profile, org_key)
    if not result:
      return result

  if org_key in profile.mentor_for:
    result = canResignAsMentorForOrg(profile, org_key)
    if not result:
      return result

  return rich_bool.TRUE


def isMentorRoleEligibleForOrg(profile, org_key):
  """Tells whether the specified user is eligible to have only mentor role
  for the specified organization.

  A user is eligible for mentor role only if he or she can resign from
  organization administrator role, if the person has one.

  Please note that this function executes a non-ancestor query, so it cannot
  be safely used within transactions.

  Args:
    profile: profile entity.
    org_key: organization key.

  Returns:
    RichBool whose value is set to True, if the user is eligible for mentor
    only role for the specified organization. Otherwise, RichBool whose value
    is set to False and extra part is a string that represents a reason why
    the user is not eligible to have mentor role only at this time.
  """
  if org_key in profile.org_admin_for:
    return canResignAsOrgAdminForOrg(profile, org_key)
  else:
    return rich_bool.TRUE
