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

from google.appengine.ext import db

from melange import types
from melange.utils import rich_bool
from melange.appengine import db as melange_db

ONLY_ORG_ADMIN = 'only_org_admin'


def canResignAsOrgAdminForOrg(profile, org_key, models=types.MELANGE_MODELS):
  """Tells whether the specified profile can resign from their organization
  administrator role for the specified organization.

  An organization administrator may be removed from the list of administrators
  of an organization, if there is at least one other user with this role.

  Args:
    profile: the specified profile entity.
    org_key: the specified organization entity.
    models: instance of types.Models that represent appropriate models.

  Returns:
    RichBool whose value is set to True, if the organization administrator
    is allowed to resign. Otherwise, RichBool whose value is set to False
    and extra part is a string that represents the reason why the user
    is not allowed to resign.
  """
  if org_key not in profile.org_admin_for:
    raise ValueError(
        'The specified profile is not an organization administrator for %s' %
        org_key.name())

  # retrieve keys of other org admins
  org_admin_keys = getOrgAdmins(org_key, keys_only=True, models=models)
  org_admin_keys.remove(profile.key())

  # try to retrieve the first org admin from the list
  # therefore, it can be safely used within a XG transaction
  if org_admin_keys and models.profile_model.get(org_admin_keys[0]):
    return rich_bool.TRUE
  else:
    return rich_bool.RichBool(False, extra=ONLY_ORG_ADMIN)


def getOrgAdmins(org_key, keys_only=False, extra_attrs=None,
    models=types.MELANGE_MODELS):
  """Returns organization administrators for the specified organization.

  Additional constraints on administrators may be specified by passing a custom
  extra_attrs dictionary. Each element of the dictionary maps a property
  with a requested value. The value must be a sequence.

  Please note that this function executes a non-ancestor query, so it cannot
  be safely used within transactions.

  Args:
    org_key: organization key
    keys_only: If true, return only keys instead of complete entities
    extra_args: a dictionary containing additional constraints on
        organization administrators to retrieve
    models: instance of types.Models that represent appropriate models.

  Returns:
    list of profiles entities or keys of organization administrators
  """
  query = models.profile_model.all(keys_only=keys_only)
  query.filter('org_admin_for', org_key)
  query.filter('status', 'active')

  _handleExtraAttrs(query, extra_attrs)

  return query.fetch(limit=1000)


def assignNoRoleForOrg(profile, org_key):
  """Removes any elevated role for the specified profile profile for the
  specified organization.

  Args:
    profile: profile entity.
    org_key: organization key.
  """
  if org_key in profile.mentor_for:
    profile.mentor_for.remove(org_key)
    profile.is_mentor = True if len(profile.mentor_for) else False

  if org_key in profile.org_admin_for:
    profile.org_admin_for.remove(org_key)
    profile.is_org_admin = True if len(profile.org_admin_for) else False

  profile.put()


def assignMentorRoleForOrg(profile, org_key):
  """Assigns the specified profile to a mentor role for the specified
  organization. If a user is currently an organization administrator,
  they will be lowered to a mentor role.

  Args:
    profile: profile entity.
    organization: organization key.
  """
  if org_key in profile.org_admin_for:
    profile.org_admin_for.remove(org_key)
    profile.is_org_admin = bool(profile.org_admin_for)

  profile.is_mentor = True
  profile.mentor_for = list(set(profile.mentor_for + [org_key]))
  profile.put()


def assignOrgAdminRoleForOrg(profile, org_key):
  """Assigns the specified profile to an organization administrator role
  for the specified organization.

  Args:
    profile: profile entity.
    org_key: organization key.
  """
  if org_key not in profile.org_admin_for:
    if org_key not in profile.mentor_for:
      profile.is_mentor = True
      profile.mentor_for.append(org_key)

    profile.is_org_admin = True
    profile.org_admin_for.append(org_key)
    profile.put()


def getProfileForUsername(username, program_key, models=types.MELANGE_MODELS):
  """Returns profile entity for a user with the specified username and
  for the specified program.

  Args:
    username: a string containing username of the user.
    program_key: program key.
    models: instance of types.Models that represent appropriate models.

  Returns:
    profile entity for the specified user and program or None if the user
    does not have a profile for this program.
  """
  profile_key = db.Key.from_path(
      models.profile_model.kind(), '%s/%s' % (program_key.name(), username),
      parent=db.Key.from_path('User', username))
  return db.get(profile_key)


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
      melange_db.addFilterToQuery(query, prop, value)
