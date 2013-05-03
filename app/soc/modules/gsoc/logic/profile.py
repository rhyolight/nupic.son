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

from google.appengine.ext import db

from soc.modules.gsoc.logic import project as project_logic
from soc.modules.gsoc.logic import proposal as proposal_logic

from soc.modules.gsoc.models import profile as profile_model


def queryAllMentorsKeysForOrg(org, limit=1000):
  """Returns a list of keys of all the mentors for the organization

  Args:
    org: the organization entity for which we need to get all the mentors
    limit: the maximum number of entities that must be fetched
    
  returns:
    List of all the mentors for the organization
  """

  # get all mentors keys first
  query = profile_model.GSoCProfile.all(keys_only=True)
  query.filter('mentor_for', org)
  mentors_keys = query.fetch(limit=limit)

  # get all org admins keys first
  query = profile_model.GSoCProfile.all(keys_only=True)
  query.filter('org_admin_for', org)
  oa_keys = query.fetch(limit=limit)

  return set(mentors_keys + oa_keys)


def queryProfilesForUser(user):
  """Returns a query that fetches all GSoC profiles created for the specified
  User
  
  Args:
    user: User entity for which the profiles are created
  """

  if not user:
    raise ValueError('User cannot be set to None')

  return profile_model.GSoCProfile.all().ancestor(user)


def canBecomeMentor(profile):
  """Tells whether the specified profile can become a mentor.

  Args:
    profile: profile entity

  Returns:
    True, if the profile is allowed to become a mentor; False otherwise
  """
  # TODO(daniel): take into account and simplify somehow checking if
  # the profile has signed mentor agreement
  return profile.status == 'active' and not profile.is_student


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
    profile.is_mentor = True
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
  return profile.status == 'active' and not profile.is_student


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
  if org_key not in profile.org_admin_for:
    profile.org_admin_for.append(org_key)
    profile.is_org_admin = True
    profile.mentor_for.append(org_key)
    profile.mentor_for = list(set(profile.mentor_for))
    profile.is_mentor = True
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
    True, if the mentor is allowed to resign; False otherwise
  """
  # TODO(daniel): figure out what to do with "possible_mentors"
  # user may be asked either to remove herself from those proposals or
  # its profile has to be removed in a safe way.

  if org_key not in profile.mentor_for:
    raise ValueError(
        'The specified profile is not a mentor for %s' % org_key.name())

  if org_key in profile.org_admin_for:
    return False

  if proposal_logic.hasMentorProposalAssigned(profile, org_key=org_key):
    return False

  if project_logic.hasMentorProjectAssigned(profile, org_key=org_key):
    return False

  return True


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
    if not profile.mentor_for:
      profile.is_mentor = False
    profile.put()


# TODO(daniel): it would be nice if this function returned something more
# verbose than "False", i.e. explanation why
def canResignAsOrgAdminForOrg(profile, org_key):
  """Tells whether the specified profile can resign from their organization
  administrator role for the specified organization.

  An organization administrator may be removed from the list of administrators
  of an organization, if there is at least one other user with this role.

  Args:
    profile: the specified GSoCProfile entity
    org_key: the specified GSoCOrganization entity

  Returns:
    True, if the mentor is allowed to resign; False otherwise
  """
  if org_key not in profile.org_admin_for:
    raise ValueError(
        'The specified profile is not an organization administrator for %s' % 
        org_key.name())

  # retrieve keys of other org admins
  org_admin_keys = getOrgAdmins(org_key, keys_only=True)
  org_admin_keys.remove(profile.key())

  if org_admin_keys:
    # try to retrieve the first org admin from the list
    # therefore, it can be safely used within a XG transaction
    if profile_model.GSoCProfile.get(org_admin_keys[0]):
      return True
    else:
      return False
  else:
    return False


def resignAsOrgAdminForOrg(profile, org_key):
  """Removes organization administrator role for the specified organization
  from the specified profile.

  The change will take effect only if it is legal for the administrator
  to resign from the role.

  Args:
    profile: profile entity
    org_key: organization key
  """
  if org_key not in profile.org_admin_for:
    return

  if canResignAsOrgAdminForOrg(profile, org_key):
    profile.org_admin_for = [
        key for key in profile.org_admin_for if key != org_key]
    if not profile.org_admin_for:
      profile.is_org_admin = False
    profile.put()


def getOrgAdmins(org_key, keys_only=False, extra_attrs=None):
  """Returns organization administrators for the specified organization.

  Additional constraints on administrators may be specified by passing a custom
  extra_attrs dictionary. Each element of the dictionary maps a property
  with a requested value. The value may be a single object or a list/tuple.

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
  query = profile_model.GSoCProfile.all(keys_only=keys_only)
  query.filter('org_admin_for', org_key)
  query.filter('status', 'active')

  if extra_attrs:
    for attribute, value in extra_attrs.iteritems():
      # list and tuples are supported by IN queries
      if isinstance(value, list) or isinstance(value, tuple):
        query.filter('%s IN' % attribute.name, value)
      else:
        query.filter(attribute.name, value)

  return query.fetch(limit=1000)


def countOrgAdmins(organization):
  """Returns the number of organization administrators for the specified
  organization.

  Please note that this function executes a non-ancestor query, so it cannot
  be safely used within transactions.

  Args:
    organization: organization entity or key

  Returns:
    number of organization administrators
  """
  query = profile_model.GSoCProfile.all()
  query.filter('org_admin_for', organization)
  query.filter('status', 'active')
  return query.count()
