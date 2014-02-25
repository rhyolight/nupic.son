# Copyright 2014 the Melange authors.
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

"""MapReduce job that removes rejected organizations from the list
of organizations which are managed by the user.

More specifically, organization key is removed from admin_for property
and is added to rejected_for property. Therefore, the information that the
user administers the organization is not lost. At the same time, it is
possible to distinguish actual organization administrators.
"""

from google.appengine.ext import ndb

from mapreduce import operation

from melange.models import organization as org_model

# MapReduce requires import of processed models.
# pylint: disable=unused-import
from melange.models.profile import Profile
# pylint: enable=unused-import


@ndb.transactional
def _updateProfileForOrgs(profile_key, orgs):
  """Updates the specified profile by removing the specified organizations
  from admin_for property and appending them to rejected_for property.

  Args:
    profile_key: Profile key.
    orgs: List of organization entities. Status of each organization to remove
      must be set to org_model.Status.REJECTED.

  Raises:
    ValueError: If status of at least one organization is not
      org_model.Status.REJECTED.
  """
  profile = profile_key.get()
  do_put = False

  for org in orgs:
    if org.key in profile.admin_for:
      if org.status != org_model.Status.REJECTED:
        raise ValueError(
            'Only rejected organizations are supported. Status of %s is %s.' % (
                org.name, org.status))
      do_put = True
      profile.admin_for.remove(org.key)
      profile.rejected_for = list(set(profile.rejected_for + [org.key]))

  if do_put:
    profile.put()


def processProfile(profile_key):
  """Processes a single profile.

  Args:
    profile_key: Profile key.
  """
  profile = profile_key.get()
  orgs = ndb.get_multi(profile.admin_for)

  to_reject = []
  for org_key in orgs:
    org = org_key.get()
    if org.status == org_model.Status.REJECTED:
      to_reject.append(org)

  if to_reject:
    _updateProfileForOrgs(profile_key, to_reject)
    yield operation.counters.Increment('updated_profile')
