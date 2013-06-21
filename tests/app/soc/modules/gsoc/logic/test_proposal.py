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

from google.appengine.ext import db

from soc.modules.gsoc.logic import proposal as proposal_logic
from soc.modules.gsoc.models.organization import GSoCOrganization
from soc.modules.gsoc.models import profile as profile_model
from soc.modules.gsoc.models.program import GSoCProgram
from soc.modules.gsoc.models import proposal as proposal_model
from soc.modules.gsoc.models import timeline as timeline_model

from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests import profile_utils
from tests import timeline_utils


class ProposalTest(unittest.TestCase):
  """Tests the gsoc logic for proposals.
  """

  def setUp(self):
    self.program = seeder_logic.seed(GSoCProgram)
    #An organization which has all its slots allocated.
    org_properties = {
        'scope': self.program,
        'slots': 2,
        'program': self.program
        }
    self.foo_organization = seeder_logic.seed(GSoCOrganization, org_properties)

    proposal_properties = {
        'program': self.program,
        'org': self.foo_organization,
        'mentor': None,
        'status': proposal_model.STATUS_ACCEPTED,
    }
    self.foo_proposals = seeder_logic.seedn(
        proposal_model.GSoCProposal, 2, proposal_properties)

    #Create organization which has slots to be allocated. We create both
    #rejected and accepted proposals for this organization entity.
    org_properties = {'scope':self.program, 'slots': 5}
    self.bar_organization = seeder_logic.seed(GSoCOrganization, org_properties)
    #Create some already accepted proposals for bar_organization.
    proposal_properties = {
        'program': self.program,
        'org': self.bar_organization,
        'mentor': None,
        'status': proposal_model.STATUS_ACCEPTED,
        }
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
    properties = {
        'scope': self.program,
        'slots': 5,
        'program': self.program
        }
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

    # seed a new proposal and assign
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


class CanSubmitProposalTest(unittest.TestCase):
  """Unit tests for canSubmitProposal function."""

  def setUp(self):
    # seed a timeline and set student app period for now
    timeline_properties = {
        'key_name': 'test_keyname',
        'student_signup_start': timeline_utils.past(),
        'student_signup_end': timeline_utils.future(),
        }
    self.timeline = seeder_logic.seed(
        timeline_model.GSoCTimeline, timeline_properties)

    # seed a proggram
    program_properties = {
        'key_name': 'test_keyname',
        'timeline': self.timeline,
        'apps_tasks_limit': 3
        }
    self.program = seeder_logic.seed(GSoCProgram, program_properties)

    # seed a new student info
    student_info_properties = {
        'number_of_proposals': 0,
        }
    self.student_info = seeder_logic.seed(
        profile_model.GSoCStudentInfo, student_info_properties)

  def testForStudentWithNoProposals(self):
    # it is possible to submit proposal during the student app period
    # and the student has not proposals
    can_submit = proposal_logic.canSubmitProposal(
        self.student_info, self.program, self.timeline)
    self.assertTrue(can_submit)

  def testForStudentWithMaxMinusOneProposals(self):
    # change the student so that already max - 1 proposals are submitted
    self.student_info.number_of_proposals = self.program.apps_tasks_limit - 1
    self.student_info.put()

    # it is still possible for the student to submit a proposal
    can_submit = proposal_logic.canSubmitProposal(
        self.student_info, self.program, self.timeline)
    self.assertTrue(can_submit)

  def testForStudentWithMaxProposals(self):
    # change the student so that max proposals are already submitted
    self.student_info.number_of_proposals = self.program.apps_tasks_limit
    self.student_info.put()

    # it is not possible to submit a next proposal
    can_submit = proposal_logic.canSubmitProposal(
        self.student_info, self.program, self.timeline)
    self.assertFalse(can_submit)

  def testBeforeStudentAppPeriod(self):
    # move the student app period to the future
    self.timeline.student_signup_start = timeline_utils.future()
    self.timeline.put()

    # it is not possible to submit a proposal now
    can_submit = proposal_logic.canSubmitProposal(
        self.student_info, self.program, self.timeline)
    self.assertFalse(can_submit)

  def testAfterStudentAppPeriod(self):
    # move the student app period to the future
    self.timeline.student_signup_end = timeline_utils.past()
    self.timeline.put()

    # it is not possible to submit a proposal now
    can_submit = proposal_logic.canSubmitProposal(
        self.student_info, self.program, self.timeline)
    self.assertFalse(can_submit)


class CanProposalBeResubmittedTest(unittest.TestCase):
  """Unit tests for canProposalBeResubmitted function."""

  def setUp(self):
    # seed a timeline and set student app period for now
    timeline_properties = {
        'key_name': 'test_keyname',
        'student_signup_start': timeline_utils.past(),
        'student_signup_end': timeline_utils.future(),
        }
    self.timeline = seeder_logic.seed(
        timeline_model.GSoCTimeline, timeline_properties)

    # seed a new program
    program_properties = {
        'key_name': 'test_keyname',
        'timeline': self.timeline,
        'apps_tasks_limit': 3,
        }
    self.program = seeder_logic.seed(GSoCProgram, program_properties)

    # seed a new student info
    student_info_properties = {
        'number_of_proposals': 0,
        }
    self.student_info = seeder_logic.seed(
        profile_model.GSoCStudentInfo, student_info_properties)

    # seed a new proposal
    proposal_properties = {'status': proposal_model.STATUS_WITHDRAWN}
    self.proposal = seeder_logic.seed(
        proposal_model.GSoCProposal, proposal_properties)

  def testResubmitWithdrawnProposal(self):
    # it should be possible to resubmit this proposal
    can_resubmit = proposal_logic.canProposalBeResubmitted(
        self.proposal, self.student_info, self.program, self.timeline)
    self.assertTrue(can_resubmit)

  def testResubmitForOtherStatuses(self):
    # set status of the proposal to accepted
    self.proposal.status = proposal_model.STATUS_ACCEPTED
    self.proposal.put()

    # it should not be possible to resubmit this proposal
    can_resubmit = proposal_logic.canProposalBeResubmitted(
        self.proposal, self.student_info, self.program, self.timeline)
    self.assertFalse(can_resubmit)

    # set status of the proposal to ignored
    self.proposal.status = proposal_model.STATUS_IGNORED
    self.proposal.put()

    # it should not be possible to resubmit this proposal
    can_resubmit = proposal_logic.canProposalBeResubmitted(
        self.proposal, self.student_info, self.program, self.timeline)
    self.assertFalse(can_resubmit)

    # set status of the proposal to invalid
    self.proposal.status = proposal_model.STATUS_INVALID
    self.proposal.put()

    # it should not be possible to resubmit this proposal
    can_resubmit = proposal_logic.canProposalBeResubmitted(
        self.proposal, self.student_info, self.program, self.timeline)
    self.assertFalse(can_resubmit)

    # set status of the proposal to pending
    self.proposal.status = proposal_model.STATUS_PENDING
    self.proposal.put()

    # it should not be possible to resubmit this proposal
    can_resubmit = proposal_logic.canProposalBeResubmitted(
        self.proposal, self.student_info, self.program, self.timeline)
    self.assertFalse(can_resubmit)

    # set status of the proposal to rejected
    self.proposal.status = proposal_model.STATUS_REJECTED
    self.proposal.put()

    # it should not be possible to resubmit this proposal
    can_resubmit = proposal_logic.canProposalBeResubmitted(
        self.proposal, self.student_info, self.program, self.timeline)
    self.assertFalse(can_resubmit)

  def testAfterStudentAppPeriod(self):
    # move the student app period to the future
    self.timeline.student_signup_end = timeline_utils.past()
    self.timeline.put()

    # it should not be possible to resubmit this proposal
    can_resubmit = proposal_logic.canProposalBeResubmitted(
        self.proposal, self.student_info, self.program, self.timeline)
    self.assertFalse(can_resubmit)

  def testForStudentWithMaxMinusOneProposals(self):
    # change the student so that already max - 1 proposals are submitted
    self.student_info.number_of_proposals = self.program.apps_tasks_limit - 1
    self.student_info.put()

    # it should not be possible to resubmit this proposal
    can_resubmit = proposal_logic.canProposalBeResubmitted(
        self.proposal, self.student_info, self.program, self.timeline)
    self.assertTrue(can_resubmit)

  def testForStudentWithMaxProposals(self):
    # change the student so that max proposals are already submitted
    self.student_info.number_of_proposals = self.program.apps_tasks_limit
    self.student_info.put()

    # it should not be possible to resubmit this proposal
    can_resubmit = proposal_logic.canProposalBeResubmitted(
        self.proposal, self.student_info, self.program, self.timeline)
    self.assertFalse(can_resubmit)


class ResubmitProposalTest(unittest.TestCase):
  """Unit tests for resubmitProposal function."""

  def setUp(self):
    # seed a timeline and set student app period for now
    timeline_properties = {
        'key_name': 'test_keyname',
        'student_signup_start': timeline_utils.past(),
        'student_signup_end': timeline_utils.future(),
        }
    self.timeline = seeder_logic.seed(
        timeline_model.GSoCTimeline, timeline_properties)

    # seed a new program
    program_properties = {
        'key_name': 'test_keyname',
        'timeline': self.timeline,
        'apps_tasks_limit': 3,
        }
    self.program = seeder_logic.seed(GSoCProgram, program_properties)

    # seed a new student info
    student_info_properties = {
        'number_of_proposals': 0,
        }
    self.student_info = seeder_logic.seed(
        profile_model.GSoCStudentInfo, student_info_properties)

    # seed a new proposal
    proposal_properties = {'status': proposal_model.STATUS_WITHDRAWN}
    self.proposal = seeder_logic.seed(
        proposal_model.GSoCProposal, proposal_properties)

  def testResubmitProposal(self):
    result = proposal_logic.resubmitProposal(
        self.proposal, self.student_info, self.program, self.timeline)

    # it should have been possible to resubmit proposal
    self.assertEqual(result, True)
    self.assertEqual(self.proposal.status, proposal_model.STATUS_PENDING)
    self.assertEqual(self.student_info.number_of_proposals, 1)

  def testResubmitProposalTwice(self):
    # resubmit proposal twice
    proposal_logic.resubmitProposal(
        self.proposal, self.student_info, self.program, self.timeline)
    result = proposal_logic.resubmitProposal(
        self.proposal, self.student_info, self.program, self.timeline)

    # proposal should be resubmitted but no side effects are present
    self.assertEqual(result, True)
    self.assertEqual(self.proposal.status, proposal_model.STATUS_PENDING)
    self.assertEqual(self.student_info.number_of_proposals, 1)

  def testCannotResubmitProposal(self):
    # make it forbidden to resubmit proposal
    self.proposal.status = proposal_model.STATUS_ACCEPTED
    self.proposal.put()
    self.student_info.number_of_proposals = 1
    self.student_info.put()

    result = proposal_logic.resubmitProposal(
        self.proposal, self.student_info, self.program, self.timeline)

    # proposal should not be resubmitted
    self.assertEqual(result, False)
    self.assertEqual(self.proposal.status, proposal_model.STATUS_ACCEPTED)
    self.assertEqual(self.student_info.number_of_proposals, 1)


class AcceptProposalTest(unittest.TestCase):
  """Unit tests for acceptProposal function."""

  def setUp(self):
    # seed a new program
    self.program = seeder_logic.seed(GSoCProgram)

    # seed a new organization
    org_properties = {'program': self.program}
    self.organization = seeder_logic.seed(GSoCOrganization, org_properties)

    # seed a new profile and make it a student
    self.profile = seeder_logic.seed(profile_model.GSoCProfile, {})

    student_info_properties = {
        'parent': self.profile,
        'number_of_proposals': 1,
        'number_of_projects': 0,
        'project_for_orgs': [],
        }
    self.student_info = seeder_logic.seed(
        profile_model.GSoCStudentInfo, student_info_properties)
    self.profile.student_info = self.student_info
    self.profile.put()

    # seed anther profile and make it a mentor
    mentor_properties = {
        'is_mentor': True,
        'mentor_for': [self.organization.key()]
        }
    self.mentor = seeder_logic.seed(
        profile_model.GSoCProfile, mentor_properties)

    # seed a new proposal and assign the mentor
    self.proposal_properties = {
        'status': 'pending',
        'accept_as_project': True,
        'has_mentor': True,
        'mentor': self.mentor,
        'program': self.program,
        'org': self.organization,
        'parent': self.profile,
        'abstract': 'test abstract',
        }
    self.proposal = seeder_logic.seed(
        proposal_model.GSoCProposal, self.proposal_properties)

  def testAcceptProposal(self):
    # accept proposal as project
    project = proposal_logic.acceptProposal(self.proposal)

    # proposal should be accepted
    self.assertEqual(self.proposal.status, proposal_model.STATUS_ACCEPTED)

    # number of projects should be increased
    student_info = profile_model.GSoCStudentInfo.get(self.student_info.key())
    self.assertEqual(student_info.number_of_projects, 1)

    # project should be created correctly
    self.assertIsNotNone(project)
    self.assertEqual(self.proposal_properties['abstract'], project.abstract)
    self.assertEqual(self.organization.key(), project.org.key())
    self.assertEqual(self.program.key(), project.program.key())
    self.assertEqual(self.profile.key(), project.parent_key())
    self.assertEqual([self.mentor.key()], project.mentors)

  def testAcceptProposalInTxn(self):
    # the function should safely execute within a single entity group txn
    db.run_in_transaction(proposal_logic.acceptProposal, self.proposal)

  def testAcceptProposalWithoutMentor(self):
    self.proposal.mentor = None

    with self.assertRaises(ValueError):
      proposal_logic.acceptProposal(self.proposal)

  def testAcceptProposalTwice(self):
    # accept proposal as project
    project_one = proposal_logic.acceptProposal(self.proposal)

    # and again
    project_two = proposal_logic.acceptProposal(self.proposal)

    # the same entity should actually be returned
    self.assertEqual(project_one.key(), project_two.key())

  def testAcceptTwoProposalsForStudent(self):
    # seed another proposal
    proposal_properties = {
        'status': 'pending',
        'accept_as_project': True,
        'has_mentor': True,
        'mentor': self.mentor,
        'program': self.program,
        'org': self.organization,
        'parent': self.profile,
        'abstract': 'test abstract',
        }
    proposal_two = seeder_logic.seed(
        proposal_model.GSoCProposal, self.proposal_properties)

    # accept both proposals
    proposal_logic.acceptProposal(self.proposal)
    proposal_logic.acceptProposal(proposal_two)

    # student info should reflect that
    student_info = profile_model.GSoCStudentInfo.get(self.student_info.key())
    self.assertEqual(student_info.number_of_projects, 2)
    self.assertEqual(student_info.project_for_orgs, [self.organization.key()])


class RejectProposalTest(unittest.TestCase):
  """Unit tests for rejectProposal function."""

  def setUp(self):
    # seed a new program
    self.program = seeder_logic.seed(GSoCProgram)

    # seed a new profile and make it a student
    self.profile = seeder_logic.seed(profile_model.GSoCProfile, {})

    student_info_properties = {
        'parent': self.profile,
        'number_of_proposals': 1,
        'number_of_projects': 0,
        'project_for_orgs': [],
        }
    self.student_info = seeder_logic.seed(
        profile_model.GSoCStudentInfo, student_info_properties)
    self.profile.student_info = self.student_info
    self.profile.put()

    mentor = seeder_logic.seed(profile_model.GSoCProfile, {})

    # seed a new proposal
    self.proposal_properties = {
        'status': 'pending',
        'accept_as_project': False,
        'has_mentor': True,
        'program': self.program,
        'parent': self.profile,
        'mentor': mentor,
        }
    self.proposal = seeder_logic.seed(
        proposal_model.GSoCProposal, self.proposal_properties)

  def testRejectProposal(self):
    # reject the proposal
    proposal_logic.rejectProposal(self.proposal)

    # make sure the proposal is rejected and there is no project for it
    self.assertEqual(self.proposal.status, proposal_model.STATUS_REJECTED)
    self.assertEqual(self.student_info.number_of_projects, 0)
    self.assertEqual(self.student_info.project_for_orgs, [])
