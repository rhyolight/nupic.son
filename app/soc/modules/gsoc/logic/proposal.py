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

from melange.utils import time as time_utils

from soc.logic import timeline as timeline_logic

from soc.views.helper import request_data

from soc.modules.gsoc.models import profile as profile_model
from soc.modules.gsoc.models import project as project_model
from soc.modules.gsoc.models import proposal as proposal_model


def getProposalsToBeAcceptedForOrg(organization, step_size=25):
  """Returns all proposals which will be accepted into the program
  for the specified organization.

  Args:
    organization: Organization entity.
    step_size: optional parameter to specify the amount of Student Proposals
        that should be retrieved per roundtrip to the datastore

  Returns:
    List with all GSoCProposal which will be accepted into the program
  """
  # check if there are already slots taken by this org
  query = proposal_model.GSoCProposal.all()
  query.filter('org', organization.key.to_old_key())
  query.filter('status', proposal_model.STATUS_ACCEPTED)

  slots_left_to_assign = max(0, organization.slot_allocation - query.count())
  if slots_left_to_assign == 0:
    # no slots left so return nothing
    return []

  query = proposal_model.GSoCProposal.all()
  query.filter('org', organization.key.to_old_key())
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


def hasMentorProposalAssigned(profile, org_key=None):
  """Checks whether the specified profile has a proposal assigned. It also
  accepts an optional argument to pass a specific organization to which
  the proposal should belong.

  Please note that this function executes a non-ancestor query, so it cannot
  be safely used within transactions.

  Args:
    profile: the specified GSoCProfile entity or its db.Key
    org_key: optional organization key

  Returns:
    True, if the profile has at least one proposal assigned; False otherwise.
  """
  query = proposal_model.GSoCProposal.all(keys_only=True)
  query.filter('mentor', profile.key.to_old_key())

  if org_key:
    query.filter('org', org_key.to_old_key())

  return query.count() > 0


def canSubmitProposal(student_info, program, timeline):
  """Tells whether the specified student can submit a proposal for
  the specified program.

  Args:
    student_info: student info entity
    program: program entity
    timeline: timeline entity for the program

  Returns:
    True if a new proposal may be submitted; False otherwise
  """
  # check if given timeline corresponds to the given program
  if not timeline_logic.isTimelineForProgram(timeline.key(), program.key()):
    raise ValueError('The specified timeline (key_name: %s) is '
        'not related to program (key_name: %s).' % (
            timeline.key().name(), program.key().name()))

  # check the student application period is open
  timeline_helper = request_data.TimelineHelper(timeline, None)
  if not timeline_helper.studentSignup():
    return False

  # check if the student has not reached the limit of apps per program
  if student_info.number_of_proposals >= program.apps_tasks_limit:
    return False

  return True


def canProposalBeWithdrawn(proposal):
  """Tells whether the specified proposal can be withdrawn.

  Args:
    proposal: proposal entity

  Returns:
    True, if the proposal can be withdrawn; False otherwise
  """
  # only pending proposals can be withdrawn
  # TODO(daniel): discuss with the team what to do with 'ignored' proposals
  # TODO(daniel): discuss with the team if it should be possible to withdraw
  # proposals after student application period is over. No?
  return proposal.status == proposal_model.STATUS_PENDING


def canProposalBeResubmitted(proposal, student_info, program, timeline):
  """Tells whether the specified proposal can be resubmitted by the specified
  student for the given program.

  Args:
    proposal: proposal entity
    student_info: student info entity
    program: program entity
    timeline: timeline entity for the program

  Returns:
    True, if the proposal can be resubmitted; False otherwise
  """
  # check if given timeline corresponds to the given program
  if not timeline_logic.isTimelineForProgram(timeline.key(), program.key()):
    raise ValueError('The specified timeline (key_name: %s) is '
        'not related to program (key_name: %s).' % (
            timeline.key().name(), program.key().name()))

  if time_utils.isAfter(timeline.accepted_students_announced_deadline):
    # students have been accepted / rejected
    return False
  elif proposal.status != proposal_model.STATUS_WITHDRAWN:
    # only withdrawn proposals can be resubmitted
    return False
  elif student_info.number_of_proposals >= program.apps_tasks_limit:
    # student has not reached the limit of proposals per program
    return False
  else:
    return True


def withdrawProposal(proposal, student_info):
  """Withdraws proposal for the specified student profile.

  Args:
    proposal: proposal entity
    student_info: student info entity

  Returns:
    True, if the proposal is withdrawn upon returning from this function;
    False otherwise
  """
  if not canProposalBeWithdrawn(proposal):
    # check if the proposal is already withdrawn
    return proposal.status == proposal_model.STATUS_WITHDRAWN

  proposal.status = proposal_model.STATUS_WITHDRAWN
  student_info.number_of_proposals -= 1

  # student info and proposal are in the same entity group
  db.put([proposal, student_info])

  return True


def resubmitProposal(proposal, student_info, program, timeline):
  """Resubmits (changes status from 'withdrawn' to 'pending')
  the specified proposal for the specified student and program.

  Args:
    proposal: proposal entity
    student_info: student info entity
    program: program entity
    timeline: timeline entity for the program

  Returns:
    True, if the proposal is effectively resubmitted (i.e. its status
    is pending) after this function; False otherwise
  """
  # check if given timeline corresponds to the given program
  if not timeline_logic.isTimelineForProgram(timeline.key(), program.key()):
    raise ValueError('The specified timeline (key_name: %s) is '
        'not related to program (key_name: %s).' % (
            timeline.key().name(), program.key().name()))

  if not canProposalBeResubmitted(
      proposal, student_info, program, timeline):
    # check if the proposal is not already pending
    return proposal.status == proposal_model.STATUS_PENDING

  proposal.status = proposal_model.STATUS_PENDING
  student_info.number_of_proposals += 1

  db.put([proposal, student_info])

  return True


def acceptProposal(proposal):
  """Accepts the specified proposal as a project and creates a new project
  entity if one has not been created so far.

  Args:
    proposal: proposal entity

  Returns:
    project entity created for the specified proposal
  """
  profile_key = proposal.parent_key()

  # check if a project for the proposal has already been created
  query = project_model.GSoCProject.all()
  query.ancestor(profile_key)
  current_projects = query.fetch(1000)

  for current_project in current_projects:
    proposal_key = project_model.GSoCProject.proposal.get_value_for_datastore(
        current_project)
    # if a project exists, return it rather than create a new one
    if proposal_key == proposal.key():
      return current_project

  org_key = proposal_model.GSoCProposal.org.get_value_for_datastore(proposal)
  program_key = proposal_model.GSoCProposal.program.get_value_for_datastore(
      proposal)
  mentor_key = proposal_model.GSoCProposal.mentor.get_value_for_datastore(
      proposal)
  if not mentor_key:
    raise ValueError('The proposal for profile %s with id %s has no '
        'mentor specified' % (proposal.parent_key().name, proposal.key().id()))

  # create new project entity
  properties = {
      'abstract': proposal.abstract,
      'mentors': [mentor_key],
      'org': org_key,
      'proposal': proposal,
      'program': program_key,
      'title': proposal.title,
      }
  project = project_model.GSoCProject(parent=profile_key, **properties)

  # get student info and update its related properties
  student_info = profile_model.GSoCStudentInfo.all().ancestor(
      profile_key).get()
  student_info.number_of_projects += 1
  student_info.project_for_orgs.append(org_key)
  student_info.project_for_orgs = list(set(student_info.project_for_orgs))

  # update proposal's status
  proposal.status = proposal_model.STATUS_ACCEPTED

  db.put([proposal, project, student_info])

  return project


def rejectProposal(proposal):
  """Rejects the specified proposal.

  Args:
    proposal: proposal entity
  """
  # update proposal's status
  proposal.status = proposal_model.STATUS_REJECTED
  proposal.put()
