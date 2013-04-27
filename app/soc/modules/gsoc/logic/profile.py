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


# TODO(daniel): make this function transaction safe
# TODO(daniel): it would be nice if this function returned something more
# verbose than "False", i.e. explanation why
def canResignAsMentorForOrg(profile, org):
  """Tells whether the specified profile can resign from their mentor role
  for the specified organization.

  A mentor may be removed from the list of mentors of an organization, if
  he or she does not have a proposal or a project assigned to mentor.

  Please note that this function executes a non-ancestor query, so it cannot
  be safely used within transactions.

  Args:
    profile: the specified GSoCProfile entity
    org: the specified GSoCOrganization entity

  Returns:
    True, if the mentor is allowed to resign; False otherwise
  """
  # TODO(daniel): figure out what to do with "possible_mentors"
  # user may be asked either to remove herself from those proposals or
  # its profile has to be removed in a safe way.

  if org.key() not in profile.mentor_for:
    raise ValueError('The specified profile is not a mentor for %s' % org.name)

  if proposal_logic.hasMentorProposalAssigned(profile, org=org):
    return False

  if project_logic.hasMentorProjectAssigned(profile, org=org):
    return False

  return True


# TODO(daniel): make this function transaction safe
# TODO(daniel): it would be nice if this function returned something more
# verbose than "False", i.e. explanation why
def canResignAsOrgAdminForOrg(profile, org):
  """Tells whether the specified profile can resign from their organization
  administrator role for the specified organization.

  An organization administrator may be removed from the list of administrators
  of an organization, if there is at least one other user with this role.

  Please note that this function executes a non-ancestor query, so it cannot
  be safely used within transactions.

  Args:
    profile: the specified GSoCProfile entity
    org: the specified GSoCOrganization entity

  Returns:
    True, if the mentor is allowed to resign; False otherwise
  """
  if org.key() not in profile.org_admin_for:
    raise ValueError(
        'The specified profile is not an organization administrator for %s' % 
        org.name)

  return countOrgAdmins(org) > 1


def getOrgAdmins(organization):
  """Returns organization administrators for the specified organization.

  Please note that this function executes a non-ancestor query, so it cannot
  be safely used within transactions.

  Args:
    organization: organization entity or key

  Returns:
    list of profiles of organization administrators
  """
  query = profile_model.GSoCProfile.all()
  query.filter('org_admin_for', organization)
  query.filter('status', 'active')
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
  return query.count()
