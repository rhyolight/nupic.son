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

"""GSoC logic for proposals."""

from google.appengine.ext import db

from soc.modules.gsoc.models import proposal as proposal_model


def getProposalsToBeAcceptedForOrg(org_entity, step_size=25):
  """Returns all proposals which will be accepted into the program
  for the given organization.

  Args:
    org_entity: the Organization for which the proposals should be checked
    step_size: optional parameter to specify the amount of Student Proposals
        that should be retrieved per roundtrip to the datastore

  Returns:
    List with all GSoCProposal which will be accepted into the program
  """

  # check if there are already slots taken by this org
  query = proposal_model.GSoCProposal.all()
  query.filter('org', org_entity)
  query.filter('status', 'accepted')

  slots_left_to_assign = max(0, org_entity.slots - query.count())
  if slots_left_to_assign == 0:
    # no slots left so return nothing
    return []

  query = proposal_model.GSoCProposal.all()
  query.filter('org', org_entity)
  query.filter('status', 'pending')
  query.filter('accept_as_project', True)
  query.filter('has_mentor', True)
  query.order('-score')

  # We are not putting this into the filter because order and != do not mix
  # in GAE.
  proposals = query.fetch(slots_left_to_assign)

  offset = slots_left_to_assign
  # retrieve as many additional proposals as needed in case the top
  # N do not have a mentor assigned
  while len(proposals) < slots_left_to_assign:
    new_proposals = query.fetch(step_size, offset=offset)

    if not new_proposals:
      # we ran out of proposals`
      break

    proposals += new_proposals
    offset += step_size

  # cut off any superfluous proposals
  return proposals[:slots_left_to_assign]


def getProposalsQuery(keys_only=False, ancestor=None, **properties):
  """Returns the Appengine proposal_model.GSoCProposal query object
  for the given set of properties.

  Args:
    ancestor: The student for whom the proposals must be fetched.
    properties: keyword arguments containing the properties for which the
        query must be constructed.
  """
  query = db.Query(proposal_model.GSoCProposal, keys_only=keys_only)

  if ancestor:
    query.ancestor(ancestor)

  for k, v in properties.items():
    query.filter(k, v)

  return query
