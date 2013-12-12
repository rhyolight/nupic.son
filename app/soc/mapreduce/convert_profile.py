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
"""Mapreduce converting profile model."""

from google.appengine.ext import db

from mapreduce import operation

# This MapReduce requires this model to have been imported.
# pylint: disable=unused-import
from soc.modules.gci.models.profile import GCIProfile
from soc.modules.gsoc.models.profile import GSoCProfile
# pylint: enable=unused-import


@db.transactional
def convertGSoCProfileRolesTxn(profile_key):
  """Converts lists of organizations for which the specified profile has
  role in a transaction.

  Args:
    profile_key: Profile key.
  """
  profile = db.get(profile_key)
  new_mentor_for = []
  for org_key in profile.mentor_for:
    new_mentor_for.append(
        db.Key.from_path('SOCOrganization', org_key.name()))
  profile.mentor_for = new_mentor_for

  new_org_admin_for = []
  for org_key in profile.org_admin_for:
    new_org_admin_for.append(
        db.Key.from_path('SOCOrganization', org_key.name()))
  profile.org_admin_for = new_org_admin_for

  profile.put()


def convertGSoCProfileRoles(profile_key):
  """Converts lists of organizations for which the specified profile has
  role in a transaction.

  Args:
    profile_key: Profile key.
  """
  convertGSoCProfileRolesTxn(profile_key)
  operation.counters.Increment('Profiles converted')
