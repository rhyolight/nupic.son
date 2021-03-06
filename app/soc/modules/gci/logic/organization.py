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

"""GCIOrganization logic methods."""

from soc.logic import organization as org_logic

from soc.modules.gci.models import task as task_model
from soc.modules.gci.models.organization import GCIOrganization


def getRemainingTaskQuota(org):
  """Returns the number of remaining tasks that the organization can publish.

  While calculating the remaining quota we consider all the tasks that
  were published including the closed tasks but not the deleted tasks.

  Args:
    org: The organization entity for which the quota must be calculated

  Returns:
    An integer which is the number of tasks the organization can publish yet
  """
  # TODO(Madhu): Refactor to create Open Tasks and Closed tasks variables
  # count all the tasks the organization has published till now.
  # This excludes tasks in Unapproved, Unpublished and Invalid states.
  valid_status = ['Open', task_model.REOPENED, 'ClaimRequested', 'Claimed',
                  'ActionNeeded', 'Closed', 'NeedsWork', 'NeedsReview']

  q = task_model.GCITask.all()
  q.filter('org', org)
  q.filter('status IN', valid_status)

  return org.task_quota_limit - q.count()


def participating(program, org_count=None):
  """Return a list of GCI organizations to display on GCI program homepage.

  Function that acts as a GCI module wrapper for fetching participating
  organizations.

  Args:
    program: GCIProgram entity for which the orgs need to be fetched.
    org_count: The number of organizations to return (if possible).
  """
  return org_logic.participating(GCIOrganization, program, org_count=org_count)


def queryForProgramAndStatus(program, status, keys_only=False):
  query = GCIOrganization.all()
  query.filter('program', program)

  if isinstance(status, list):
    query.filter('status IN', status)
  else:
    query.filter('status', status)

  return query


def queryForOrgAdminAndStatus(org_admin, status):
  """Returns a query for GCIOrganization entities with the specified org admin
  and status.

  Args:
    org_admin: GCIProfile entity
    status: the specified status or a list of acceptable statuses

  Returns:
    a Query object which may be used to retrieved GCIOrganization entities
  """
  query = GCIOrganization.all()
  query.filter('__key__ IN', org_admin.org_admin_for)

  if isinstance(status, list):
    query.filter('status IN', status)
  else:
    query.filter('status', status)

  return query
