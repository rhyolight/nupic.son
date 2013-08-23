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

from melange.appengine import db as melange_db


def getOrgAdmins(org_key, keys_only=False, extra_attrs=None,
    models=melange_db.MELANGE_MODELS):
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
  query = models.profileModel.all(keys_only=keys_only)
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
