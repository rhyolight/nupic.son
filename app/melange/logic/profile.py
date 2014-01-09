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

from google.appengine.api import datastore_errors
from google.appengine.ext import db
from google.appengine.ext import ndb

from melange import types
from melange.utils import rich_bool
from melange.appengine import db as melange_db

from soc.models import program as program_model


ONLY_ORG_ADMIN = 'only_org_admin'
PROFILE_EXISTS = unicode(
    'A profile has already been registered for this program and this user.')
PROFILE_DOES_NOT_EXIST = unicode(
    'No profile exists for the specified key: %s')


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
  """Assigns the specified profile an organization administrator role
  for the specified organization.

  Args:
    profile: Profile entity.
    org_key: Organization key.
  """
  if org_key not in profile.admin_for:
    if org_key not in profile.mentor_for:
      profile.mentor_for.append(org_key)

    profile.admin_for.append(org_key)
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
  profile_key = ndb.Key(
      models.user_model._get_kind(), username,
      models.ndb_profile_model._get_kind(),
      '%s/%s' % (program_key.name(), username))
  return profile_key.get()


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


def getProfileKey(sponsor_id, program_id, user_id, models=None):
  """Constructs ndb.Key of a profile for the specified sponsor,
  program and user identifiers.

  Args:
    sponsor_id: Sponsor identifier.
    program_id: Program identifier.
    user_id: User identifier.
    models: instance of types.Models that represent appropriate models.

  Returns:
    ndb.Key instance of a profile entity with the specified properties.
  """
  models = models or types.MELANGE_MODELS
  return ndb.Key(
      models.user_model._get_kind(), user_id,
      models.ndb_profile_model._get_kind(),
      '%s/%s/%s' % (sponsor_id, program_id, user_id))


def createProfile(
    user_key, program_key, profile_properties, models=types.MELANGE_MODELS):
  """Creates a new profile entity based on the supplied properties.

  Args:
    user_key: User key for the profile to register.
    program: Program key.
    profile_properties: A dict mapping profile properties to their values.
    models: instance of types.Models that represent appropriate models.

  Returns:
    RichBool whose value is set to True if profile has been successfully
    created. In that case, extra part points to the newly created profile
    entity. Otherwise, RichBool whose value is set to False and extra part is
    a string that represents the reason why the action could not be completed.
  """
  # check if a profile entity for the user and the program already exists.
  profile_key = getProfileKey(
      program_model.getSponsorId(program_key),
      program_model.getProgramId(program_key),
      user_key.id(), models=models)

  if profile_key.get():
    return rich_bool.RichBool(False, PROFILE_EXISTS)
  else:
    try:
      program_key = ndb.Key.from_old_key(program_key)
      profile = models.ndb_profile_model(
          key=profile_key, program=program_key, **profile_properties)
      profile.put()
      return rich_bool.RichBool(True, profile)
    except datastore_errors.BadValueError as e:
      return rich_bool.RichBool(False, str(e))


def editProfile(profile_key, profile_properties):
  """Edits profile with the specified key based on the supplied properties.

  Args:
    profile_key: Profile key of an existing profile to edit.
    profile_properties: A dict mapping profile properties to their values.

  Returns:
    RichBool whose value is set to True if profile has been successfully
    updated. In that case, extra part points to the updated profile entity.
    Otherwise, RichBool whose value is set to False and extra part is a string
    that represents the reason why the action could not be completed.
  """
  profile = profile_key.get()
  if not profile:
    return rich_bool.RichBool(False, PROFILE_DOES_NOT_EXIST % profile_key.id())
  else:
    try:
      profile.populate(**profile_properties)
      profile.put()
      return rich_bool.RichBool(True, profile)
    except datastore_errors.BadValueError as e:
      return rich_bool.RichBool(False, str(e))


def createStudentData(student_data_properties, models=types.MELANGE_MODELS):
  """Creates a new student data object based on the specified properties.

  Args:
    student_data_properties: A dict mapping profile properties to their values.
    models: Instance of types.Models that represent appropriate models.

  Returns:
    Newly created student data entity.
  """
  return models.student_data_model(**student_data_properties)
