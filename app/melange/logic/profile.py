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

from melange import types


# TODO(daniel): it would be nice if this function returned something more
# verbose than "False", i.e. explanation why
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
    True, if the mentor is allowed to resign; False otherwise
  """
  if org_key not in profile.org_admin_for:
    raise ValueError(
        'The specified profile is not an organization administrator for %s' %
        org_key.name())

  # retrieve keys of other org admins
  org_admin_keys = getOrgAdmins(org_key, keys_only=True, models=models)
  org_admin_keys.remove(profile.key())

  if org_admin_keys:
    # try to retrieve the first org admin from the list
    # therefore, it can be safely used within a XG transaction
    if models.profile_model.get(org_admin_keys[0]):
      return True
    else:
      return False
  else:
    return False


def getOrgAdmins(org_key, keys_only=False, extra_attrs=None,
    models=types.MELANGE_MODELS):
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
    models: instance of types.Models that represent appropriate models.

  Returns:
    list of profiles entities or keys of organization administrators
  """
  query = models.profile_model.all(keys_only=keys_only)
  query.filter('org_admin_for', org_key)
  query.filter('status', 'active')

  _handleExtraAttrs(query, extra_attrs)

  return query.fetch(limit=1000)


def _handleExtraAttrs(query, extra_attrs):
  """Extends the specified query by handling extra attributes.

  The attributes are specified in the passed dictionary. Each element of
  the dictionary maps a property with a requested value. The value may
  be a single object or a list/tuple.

  Args:
    query: query to extend
    extra_attrs: a dictionary containing additional constraints on the query
  """
  if extra_attrs:
    for attribute, value in extra_attrs.iteritems():
      # list and tuples are supported by IN queries
      if isinstance(value, list) or isinstance(value, tuple):
        query.filter('%s IN' % attribute.name, value)
      else:
        query.filter(attribute.name, value)
