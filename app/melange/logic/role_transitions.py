# Copyright 2012 the Melange authors.
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

"""Logic for handling role transitions for Profiles."""

from google.appengine.ext import db

def assignUserMentorRoleForOrg(profile, organization):
  """Assign a user to a mentor role for a given organization. If a user is
  currently an Org Admin, they will be lowered to a mentor role.
  
  Args:
    profile: The Profile to assign as a mentor.
    organization: The Organization for which the profile will be a mentor.
  """
  org_key = organization.key()
  
  if org_key in profile.org_admin_for:
    profile.org_admin_for.remove(org_key)
    profile.is_org_admin = True if len(profile.org_admin_for) > 0 else False
  
  profile.is_mentor = True
  profile.mentor_for.append(org_key)
  profile.mentor_for = list(set(profile.mentor_for))
  profile.put()

def assignUserOrgAdminRoleForOrg(profile, organization):
  """Elevate a user profile to an org admin role for the given organization.
  
  Args:
    profile: The Profile to assign as an org admin.
    organization: The Organization for which the profile will be a mentor.
  """
  org_key = organization.key()
  
  if org_key not in profile.org_admin_for:
    assignUserMentorRoleForOrg(profile, organization)
    
    profile.is_org_admin = True
    profile.org_admin_for.append(org_key)
    profile.put()
