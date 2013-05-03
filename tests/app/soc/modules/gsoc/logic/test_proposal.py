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

"""Tests for soc.modules.gsoc.logic.duplicates."""

import unittest

from soc.modules.gsoc.logic import proposal as proposal_logic
from soc.modules.gsoc.models.organization import GSoCOrganization
from soc.modules.gsoc.models import profile as profile_model
from soc.modules.gsoc.models.program import GSoCProgram
from soc.modules.gsoc.models import proposal as proposal_model

from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests import profile_utils


class ProposalTest(unittest.TestCase):
  """Tests the gsoc logic for proposals.
  """

  def setUp(self):
    self.program = seeder_logic.seed(GSoCProgram)
    #An organization which has all its slots allocated.
    org_properties = {'scope':self.program, 'slots': 2}
    self.foo_organization = seeder_logic.seed(GSoCOrganization, org_properties)

    proposal_properties = {'program': self.program, 'org': self.foo_organization,
                           'mentor': None, 'status': 'accepted'}
    self.foo_proposals = seeder_logic.seedn(
        proposal_model.GSoCProposal, 2, proposal_properties)

    #Create organization which has slots to be allocated. We create both 
    #rejected and accepted proposals for this organization entity.
    org_properties = {'scope':self.program, 'slots': 5}
    self.bar_organization = seeder_logic.seed(GSoCOrganization, org_properties)
    #Create some already accepted proposals for bar_organization.
    proposal_properties = {'program': self.program, 'org': self.bar_organization,
                           'mentor': None, 'status': 'accepted'}
    self.bar_accepted_proposals = seeder_logic.seedn(
        proposal_model.GSoCProposal, 2, proposal_properties)
    #proposals which are yet to be accepted.
    proposal_properties = {'status': 'pending', 'accept_as_project': True,
                           'has_mentor': True, 'program': self.program,
                           'org': self.bar_organization}
    self.bar_to_be_accepted_proposals = seeder_logic.seedn(
        proposal_model.GSoCProposal, 3, proposal_properties)
    #proposals which were rejected.
    proposal_properties = {'status': 'pending', 'accept_as_project': False,
                           'has_mentor': False, 'program': self.program,
                           'org': self.bar_organization}
    self.bar_rejected_proposals = seeder_logic.seedn(
        proposal_model.GSoCProposal, 2, proposal_properties)

    #Create an organization for which the accepted proposals are more than
    #the available slots.
    org_properties = {'scope': self.program, 'slots': 1}
    self.happy_organization = seeder_logic.seed(GSoCOrganization, org_properties)
    proposal_properties = {'status': 'pending', 'accept_as_project': True,
                           'has_mentor': True, 'program': self.program,
                           'org': self.happy_organization}

    self.happy_accepted_proposals = []
    proposal_properties['score'] = 2
    self.happy_accepted_proposals.append(seeder_logic.seed(
        proposal_model.GSoCProposal, proposal_properties))
    proposal_properties['score'] = 5
    self.happy_accepted_proposals.append(seeder_logic.seed(
        proposal_model.GSoCProposal, proposal_properties))

  def testGetProposalsToBeAcceptedForOrg(self):
    """Tests if all GSoCProposals to be accepted into a program for a given
    organization are returned.
    """
    #Test that for organization which has been allotted all its slots, an empty
    #list is returned.
    org = self.foo_organization
    expected = []
    actual = proposal_logic.getProposalsToBeAcceptedForOrg(org)
    self.assertEqual(expected, actual)

    #Test that for an organization which has empty slots, only accepted
    #proposals are returned. We have both accepted and rejected proposals for
    #bar_organization.
    org = self.bar_organization
    expected_proposals_entities = self.bar_to_be_accepted_proposals
    expected = set([prop.key() for prop in expected_proposals_entities])
    actual_proposals_entities = proposal_logic.getProposalsToBeAcceptedForOrg(org)
    actual = set([prop.key() for prop in actual_proposals_entities])
    self.assertEqual(expected, actual)

    #Since self.happy_organization has more accepted projects than the available
    #slots, a proposal with a higher score should be returned.
    actual_proposals_entities = proposal_logic.getProposalsToBeAcceptedForOrg(
        self.happy_organization)
    actual = [prop.key() for prop in actual_proposals_entities]
    expected = [self.happy_accepted_proposals[1].key()]
    self.assertEqual(actual, expected)

    #Create an organization which has empty slots but no accepted projects.
    properties = {'scope': self.program, 'slots': 5}
    organization = seeder_logic.seed(GSoCOrganization, properties)
    expected = []
    actual = proposal_logic.getProposalsToBeAcceptedForOrg(organization)
    self.assertEqual(actual, expected)

  def testHasMentorProposalAssigned(self):
    """Unit test for proposal_logic.hasMentorProposalAssigned function."""

    # seed a new mentor
    mentor_properties = {
        'is_mentor': True,
        'mentor_for': [self.foo_organization.key()],
        'is_org_admin': False,
        'org_admin_for': [],
        'status': 'active',
    }
    mentor = seeder_logic.seed(
        profile_model.GSoCProfile, mentor_properties)

    # mentor has no proposals
    has_proposal = proposal_logic.hasMentorProposalAssigned(mentor)
    self.assertFalse(has_proposal)

    # seed a new proposal and assign the mentor
    proposal_properties = {
        'status': 'pending',
        'accept_as_project': False,
        'has_mentor': True,
        'mentor': mentor,
        'program': self.program,
        'org': self.foo_organization
        }
    proposal = seeder_logic.seed(
        proposal_model.GSoCProposal, proposal_properties)

    # mentor has a proposal now
    has_proposal = proposal_logic.hasMentorProposalAssigned(mentor)
    self.assertTrue(has_proposal)

    # mentor has also proposal for foo organization
    has_proposal = proposal_logic.hasMentorProposalAssigned(
        mentor, org_key=self.foo_organization.key())
    self.assertTrue(has_proposal)

    # mentor does not have proposal for bar organization
    has_proposal = proposal_logic.hasMentorProposalAssigned(
        mentor, org_key=self.bar_organization.key())
    self.assertFalse(has_proposal)


class CanProposalBeWithdrawn(unittest.TestCase):
  """Unit tests for canProposalBeWithdrawn function."""

  def testCanWithdrawPendingProposal(self):
    proposal_properties = {'status': proposal_model.STATUS_PENDING}
    proposal = seeder_logic.seed(
        proposal_model.GSoCProposal, proposal_properties)

    can_withdraw = proposal_logic.canProposalBeWithdrawn(proposal)

    # it should be possible to withdraw a pending proposal
    self.assertTrue(can_withdraw)

  def testCannotWithdrawWithdrawnProposals(self):
    proposal_properties = {'status': proposal_model.STATUS_WITHDRAWN}
    proposal = seeder_logic.seed(
        proposal_model.GSoCProposal, proposal_properties)

    can_withdraw = proposal_logic.canProposalBeWithdrawn(proposal)

    # it is not possible to withdraw already withdrawn proposal
    self.assertFalse(can_withdraw)

  def testCannotWithdrawIgnoredProposal(self):
    proposal_properties = {'status': proposal_model.STATUS_IGNORED}
    proposal = seeder_logic.seed(
        proposal_model.GSoCProposal, proposal_properties)

    can_withdraw = proposal_logic.canProposalBeWithdrawn(proposal)

    # it is not possible to withdraw ignored proposals
    self.assertFalse(can_withdraw)

  def testCannotWithdrawAcceptedOrRejectedProposal(self):
    proposal_properties = {'status': proposal_model.STATUS_ACCEPTED}
    proposal = seeder_logic.seed(
        proposal_model.GSoCProposal, proposal_properties)

    can_withdraw = proposal_logic.canProposalBeWithdrawn(proposal)

    # it is not possible to withdraw already accepted proposals
    self.assertFalse(can_withdraw)

    proposal.status = proposal_model.STATUS_REJECTED
    proposal.put()

    can_withdraw = proposal_logic.canProposalBeWithdrawn(proposal)

    # it is not possible to withdraw already rejected proposals
    self.assertFalse(can_withdraw)


class WithdrawProposalTest(unittest.TestCase):
  """Unit tests for withdrawProposal function."""

  def setUp(self):
    # seed a new program
    program = seeder_logic.seed(GSoCProgram)

    # seed a new organization
    org_properties = {'program': program}
    organization = seeder_logic.seed(GSoCOrganization, org_properties)

    # create a new profile and make it a student
    self.profile = seeder_logic.seed(profile_model.GSoCProfile, {})

    student_info_properties = {
        'parent': self.profile,
        'number_of_proposals': 1,
        }
    self.student_info = seeder_logic.seed(
        profile_model.GSoCStudentInfo, student_info_properties)

    # seed a new proposal and assign the mentor
    proposal_properties = {'parent': self.profile}
    self.proposal = seeder_logic.seed(
        proposal_model.GSoCProposal, proposal_properties)

  def testWithdrawProposal(self):
    # set the proposal status to pending
    self.proposal.status = proposal_model.STATUS_PENDING
    self.proposal.put()

    # try to withdraw the proposal
    result = proposal_logic.withdrawProposal(self.proposal, self.student_info)

    # the proposal should be withdrawn
    self.assertTrue(result)
    self.assertEqual(proposal_model.STATUS_WITHDRAWN, self.proposal.status)
    self.assertEqual(0, self.student_info.number_of_proposals)

  def testWithdrawProposalTwice(self):
    # set the proposal status to pending
    self.proposal.status = proposal_model.STATUS_PENDING
    self.proposal.put()

    # try to withdraw the proposal twice
    proposal_logic.withdrawProposal(self.proposal, self.student_info)
    result = proposal_logic.withdrawProposal(self.proposal, self.student_info)

    # the result should also be true but number of proposals should not
    # be decreased twice
    self.assertTrue(result)
    self.assertEqual(proposal_model.STATUS_WITHDRAWN, self.proposal.status)
    self.assertEqual(0, self.student_info.number_of_proposals)

  def testWithdrawProposalForStudentWithFewProposals(self):
    # set the proposal status to pending
    self.proposal.status = proposal_model.STATUS_PENDING
    self.proposal.put()

    # create a few other proposals
    proposals = []
    proposal_properties = {
        'parent': self.profile,
        'status': proposal_model.STATUS_PENDING
        }
    for _ in range(3):
      proposals.append(seeder_logic.seed(
          proposal_model.GSoCProposal, proposal_properties))
    self.student_info.number_of_proposals += len(proposals)
    self.student_info.put()

    # withdraw the main proposal
    result = proposal_logic.withdrawProposal(self.proposal, self.student_info)

    # the proposal should be withdrawn
    self.assertTrue(result)
    self.assertEqual(proposal_model.STATUS_WITHDRAWN, self.proposal.status)
    self.assertEqual(len(proposals), self.student_info.number_of_proposals)

  def testForIneligibleProposal(self):
    # set the proposal status to accepted
    self.proposal.status = proposal_model.STATUS_ACCEPTED
    self.proposal.put()

    # try to withdraw the proposal
    result = proposal_logic.withdrawProposal(self.proposal, self.student_info)

    # the proposal should not be withdrawn
    self.assertFalse(result)
    self.assertEqual(proposal_model.STATUS_ACCEPTED, self.proposal.status)
    self.assertEqual(1, self.student_info.number_of_proposals)
