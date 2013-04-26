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
