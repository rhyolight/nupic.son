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

"""GSoC logic for profiles."""

from melange.appengine import db as melange_db
from melange.logic import profile as profile_logic
from melange.models import profile as profile_model
from melange.utils import rich_bool

from soc.modules.gsoc.logic import project as project_logic
from soc.modules.gsoc.logic import proposal as proposal_logic

from summerofcode import types


# List of reasons why the specified profile cannot resign from mentor role
IS_ORG_ADMIN = 'is_org_admin'
HAS_PROPOSAL_ASSIGNED = 'has_proposal_assigned'
HAS_PROJECT_ASSIGNED = 'has_project_assigned'

def queryAllMentorsKeysForOrg(org_key, limit=1000):
  """Returns a list of keys of all the mentors for the specified organization.

  Args:
    org_key: Organization key.
    limit: the maximum number of entities that must be fetched

  returns:
    List of db.Key of all the mentors for the organization.
  """
  # get all mentors keys first
  query = profile_model.Profile.query(
      profile_model.Profile.mentor_for == org_key)
  return query.fetch(limit=limit, keys_only=True)


def queryProfilesForUser(user):
  """Returns a query that fetches all GSoC profiles created for the specified
  User

  Args:
    user: User entity for which the profiles are created
  """

  if not user:
    raise ValueError('User cannot be set to None')

  return profile_model.Profile.query(ancestor=user.key)


def _handleExtraAttrs(query, extra_attrs):
  """Extends the specified query by handling extra attributes.

  The attributes are specified in the passed dictionary. Each element of
  the dictionary maps a property with a requested value. The value must
  be a sequence (list or tuple).

  Args:
    query: query to extend.
    extra_attrs: a dictionary containing additional constraints on the query.
  """
  if extra_attrs:
    for prop, value in extra_attrs.iteritems():
      query = melange_db.addFilterToNDBQuery(query, prop, value)
  return query


def canBecomeMentor(profile):
  """Tells whether the specified profile can become a mentor.

  Args:
    profile: profile entity

  Returns:
    True, if the profile is allowed to become a mentor; False otherwise
  """
  # TODO(daniel): take into account and simplify somehow checking if
  # the profile has signed mentor agreement
  return (profile.status == profile_model.Status.ACTIVE
      and not profile.is_student)


def becomeMentorForOrg(profile, org_key):
  """Adds the specified profile as a mentor for the specified organization.

  Args:
    profile: profile entity
    org_key: organization key
  """
  if not canBecomeMentor(profile):
    return

  # the operation is idempotent: adding a mentor more than once has no effect
  if org_key not in profile.mentor_for:
    profile.mentor_for.append(org_key)
    profile.put()


def canBecomeOrgAdmin(profile):
  """Tells whether the specified user can become an organization administrator.

  Args:
    profile: profile entity

  Returns:
    True, if the profile is allowed to become an organization administrator;
    False otherwise
  """
  # TODO(daniel): take into account and simplify somehow checking if
  # the profile has signed mentor agreement
  return (profile.status == profile_model.Status.ACTIVE
      and not profile.is_student)


def becomeOrgAdminForOrg(profile, org_key):
  """Adds the specified profile as an organization administrator
  for the specified organization.

  Args:
    profile: profile entity
    org_key: organization key
  """
  if not canBecomeMentor(profile) or not canBecomeOrgAdmin(profile):
    return

  # the operation is idempotent: adding more than once has no effect
  if org_key not in profile.admin_for:
    profile.admin_for.append(org_key)
    profile.mentor_for.append(org_key)
    profile.mentor_for = list(set(profile.mentor_for))
    profile.put()


# TODO(daniel): make this function transaction safe
# TODO(daniel): it would be nice if this function returned something more
# verbose than "False", i.e. explanation why
def canResignAsMentorForOrg(profile, org_key):
  """Tells whether the specified profile can resign from their mentor role
  for the specified organization.

  A mentor may be removed from the list of mentors of an organization, if
  he or she does not have a proposal or a project assigned to mentor. Also,
  organization administrators have cannot resign from mentorship. They have
  to give up that role first.

  Please note that this function executes a non-ancestor query, so it cannot
  be safely used within transactions.

  Args:
    profile: the specified GSoCProfile entity
    org_key: organization key

  Returns:
    RichBool whose value is set to True, if the mentor is allowed to resign.
    Otherwise, RichBool whose value is set to False and extra part is a string
    that represents the reason why the user is not allowed to resign.
  """
  # TODO(daniel): figure out what to do with "possible_mentors"
  # user may be asked either to remove herself from those proposals or
  # its profile has to be removed in a safe way.

  if org_key not in profile.mentor_for:
    raise ValueError(
        'The specified profile is not a mentor for %s' % org_key.id())

  if org_key in profile.admin_for:
    return rich_bool.RichBool(False, IS_ORG_ADMIN)

  if proposal_logic.hasMentorProposalAssigned(profile, org_key=org_key):
    return rich_bool.RichBool(False, HAS_PROPOSAL_ASSIGNED)

  if project_logic.hasMentorProjectAssigned(profile, org_key=org_key):
    return rich_bool.RichBool(False, HAS_PROJECT_ASSIGNED)

  return rich_bool.TRUE


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
  if org_key in profile.admin_for:
    result = profile_logic.canResignAsOrgAdminForOrg(profile, org_key)
    if not result:
      return result

  if org_key in profile.mentor_for:
    result = canResignAsMentorForOrg(profile, org_key)
    if not result:
      return result

  return rich_bool.TRUE


# TODO(daniel): make this function transaction safe
def resignAsMentorForOrg(profile, org_key):
  """Removes mentor role for the specified organization from the specified
  profile.

  The change will take effect only if it is legal for the mentor to resign
  from their mentorship.

  Please note that this function executes a non-ancestor query, so it cannot
  be safely used within transactions.

  Args:
    profile: profile entity
    org_key: organization key
  """
  if org_key not in profile.mentor_for:
    return

  if canResignAsMentorForOrg(profile, org_key):
    profile.mentor_for = [
        key for key in profile.mentor_for if key != org_key]
    profile.put()


def canResignAsOrgAdminForOrg(profile, org_key):
  """Tells whether the specified profile can resign from their organization
  administrator role for the specified organization.

  An organization administrator may be removed from the list of administrators
  of an organization, if there is at least one other user with this role.

  Args:
    profile: the specified profile entity.
    org_key: the specified organization entity.

  Returns:
    RichBool whose value is set to True, if the organization administrator
    is allowed to resign. Otherwise, RichBool whose value is set to False
    and extra part is a string that represents the reason why the user
    is not allowed to resign.
  """
  return profile_logic.canResignAsOrgAdminForOrg(
      profile, org_key, models=types.SOC_MODELS)


def resignAsOrgAdminForOrg(profile, org_key):
  """Removes organization administrator role for the specified organization
  from the specified profile.

  The change will take effect only if it is legal for the administrator
  to resign from the role.

  Args:
    profile: profile entity
    org_key: organization key
  """
  if org_key not in profile.admin_for:
    return

  if canResignAsOrgAdminForOrg(profile, org_key):
    profile.admin_for = [
        key for key in profile.admin_for if key != org_key]
    profile.put()


def getOrgAdmins(org_key, keys_only=False, extra_attrs=None):
  """Returns organization administrators for the specified organization.

  Additional constraints on administrators may be specified by passing a custom
  extra_attrs dictionary. Each element of the dictionary maps a property
  with a requested value. The value must be a sequence (list or tuple).

  Please note that this function executes a non-ancestor query, so it cannot
  be safely used within transactions.

  Args:
    org_key: organization key
    keys_only: If true, return only keys instead of complete entities
    extra_args: a dictionary containing additional constraints on
        organization administrators to retrieve

  Returns:
    list of profiles entities or keys of organization administrators
  """
  return profile_logic.getOrgAdmins(
      org_key, keys_only=keys_only, extra_attrs=extra_attrs,
      models=types.SOC_MODELS)


def countOrgAdmins(org_key):
  """Returns the number of organization administrators for the specified
  organization.

  Please note that this function executes a non-ancestor query, so it cannot
  be safely used within transactions.

  Args:
    org_key: Organization key.

  Returns:
    number of organization administrators
  """
  return profile_model.Profile.query(
      profile_model.Profile.admin_for == org_key,
      profile_model.Profile.status == profile_model.Status.ACTIVE).count()


def getMentors(org_key, keys_only=False, extra_attrs=None):
  """Returns mentors for the specified organization.

  Additional constraints on mentors may be specified by passing a custom
  extra_attrs dictionary. Each element of the dictionary maps a property
  with a requested value. The value must be a sequence (list or tuple).

  Please note that this function executes a non-ancestor query, so it cannot
  be safely used within transactions.

  Args:
    org_key: organization key
    keys_only: If true, return only keys instead of complete entities
    extra_args: a dictionary containing additional constraints on
        mentors to retrieve

  Returns:
    list of profiles entities or keys of mentors
  """
  query = profile_model.Profile.query(
      profile_model.Profile.status == profile_model.Status.ACTIVE,
      profile_model.Profile.mentor_for == org_key)

  query = _handleExtraAttrs(query, extra_attrs)

  return query.fetch(1000, keys_only=keys_only)


def allFormsSubmitted(student_data):
  """Tells whether the specified student has submitted all required forms.

  Args:
    student_data: Student data object.

  Returns:
    True if all forms has been submitted; False otherwise.
  """
  return student_data.tax_form and student_data.enrollment_form
