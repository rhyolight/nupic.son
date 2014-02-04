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

from summerofcode import types

from soc.modules.gsoc.logic import proposal as proposal_logic
from soc.modules.gsoc.models import project as project_model
from soc.modules.gsoc.models import proposal as proposal_model

from tests import org_utils
from tests import profile_utils
from tests import program_utils
from tests import timeline_utils
from tests.utils import proposal_utils


TEST_ORG_ID = 'test_org_id'
TEST_PROGRAM_ID = 'test_program_id'

class ProposalTest(unittest.TestCase):
  """Tests the gsoc logic for proposals.
  """

  def setUp(self):
    self.program = program_utils.seedGSoCProgram()
    # An organization which has all its slots allocated.
    self.foo_organization = org_utils.seedSOCOrganization(
        self.program.key(), slot_allocation=2)

    self.foo_proposals = []
    for _ in range(2):
      student = profile_utils.seedNDBStudent(self.program)
      self.foo_proposals.append(
          proposal_utils.seedProposal(student.key, self.program.key(),
              org_key=self.foo_organization.key,
              status=proposal_model.STATUS_ACCEPTED))

    # Create an organization which has slots to be allocated. We create both
    # rejected and accepted proposals for this organization entity.
    self.bar_organization = org_utils.seedSOCOrganization(
        self.program.key(), slot_allocation=5)
    # Create some already accepted proposals for bar_organization.
    self.bar_accepted_proposals = []
    for _ in range(2):
      student = profile_utils.seedNDBStudent(self.program)
      self.bar_accepted_proposals.append(
          proposal_utils.seedProposal(student.key, self.program.key(),
              org_key=self.bar_organization.key,
              status=proposal_model.STATUS_ACCEPTED))
    # proposals which are yet to be accepted.
    self.bar_to_be_accepted_proposals = []
    for _ in range(3):
      student = profile_utils.seedNDBStudent(self.program)
      self.bar_to_be_accepted_proposals.append(
          proposal_utils.seedProposal(student.key, self.program.key(),
              org_key=self.bar_organization.key, accept_as_project=True,
              status=proposal_model.STATUS_PENDING))

    # proposals which were rejected.
    self.bar_rejected_proposals = []
    for _ in range(3):
      student = profile_utils.seedNDBStudent(self.program)
      self.bar_rejected_proposals.append(
          proposal_utils.seedProposal(student.key, self.program.key(),
              org_key=self.bar_organization.key, accept_as_project=False,
              status=proposal_model.STATUS_PENDING))

    # Create an organization for which the accepted proposals are more than
    # the available slots.
    self.happy_organization = org_utils.seedSOCOrganization(
        self.program.key(), slot_allocation=1)

    self.happy_accepted_proposals = []
    self.happy_accepted_proposals.append(
        proposal_utils.seedProposal(student.key, self.program.key(),
            org_key=self.happy_organization.key, score=2,
            status=proposal_model.STATUS_PENDING, accept_as_project=True))
    self.happy_accepted_proposals.append(
        proposal_utils.seedProposal(student.key, self.program.key(),
            org_key=self.happy_organization.key, score=5,
            status=proposal_model.STATUS_PENDING, accept_as_project=True))

  def testGetProposalsToBeAcceptedForOrg(self):
    """Tests if all GSoCProposals to be accepted into a program for a given
    organization are returned.
    """
    #Test that for organization which has been allotted all its slots, an empty
    #list is returned.
    expected = []
    actual = proposal_logic.getProposalsToBeAcceptedForOrg(
        self.foo_organization)
    self.assertEqual(expected, actual)

    #Test that for an organization which has empty slots, only accepted
    #proposals are returned. We have both accepted and rejected proposals for
    #bar_organization.
    expected_proposals_entities = self.bar_to_be_accepted_proposals
    expected = set([prop.key() for prop in expected_proposals_entities])
    actual_proposals_entities = (
        proposal_logic.getProposalsToBeAcceptedForOrg(self.bar_organization))
    actual = set([prop.key() for prop in actual_proposals_entities])
    self.assertEqual(expected, actual)

    #Since self.happy_organization has more accepted projects than the available
    #slots, a proposal with a higher score should be returned.
    actual_proposals_entities = proposal_logic.getProposalsToBeAcceptedForOrg(
        self.happy_organization)
    actual = [prop.key() for prop in actual_proposals_entities]
    expected = [self.happy_accepted_proposals[1].key()]
    self.assertEqual(actual, expected)

    # Create an organization which has empty slots but no accepted projects.
    organization = org_utils.seedSOCOrganization(
        self.program.key(), slot_allocation=5)
    expected = []
    actual = proposal_logic.getProposalsToBeAcceptedForOrg(organization)
    self.assertEqual(actual, expected)

  def testHasMentorProposalAssigned(self):
    """Unit test for proposal_logic.hasMentorProposalAssigned function."""
    # seed a new mentor
    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.foo_organization.key])

    # mentor has no proposals
    has_proposal = proposal_logic.hasMentorProposalAssigned(mentor)
    self.assertFalse(has_proposal)

    # seed a new proposal and assign the mentor
    student = profile_utils.seedNDBStudent(self.program)
    proposal_utils.seedProposal(
        student.key, self.program.key(), org_key=self.foo_organization.key,
        mentor_key=mentor.key)

    # mentor has a proposal now
    has_proposal = proposal_logic.hasMentorProposalAssigned(mentor)
    self.assertTrue(has_proposal)

    # mentor has also proposal for foo organization
    has_proposal = proposal_logic.hasMentorProposalAssigned(
        mentor, org_key=self.foo_organization.key)
    self.assertTrue(has_proposal)

    # mentor does not have proposal for bar organization
    has_proposal = proposal_logic.hasMentorProposalAssigned(
        mentor, org_key=self.bar_organization.key)
    self.assertFalse(has_proposal)


class CanProposalBeWithdrawn(unittest.TestCase):
  """Unit tests for canProposalBeWithdrawn function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.program = program_utils.seedGSoCProgram()
    self.student = profile_utils.seedNDBStudent(self.program)

  def testCanWithdrawPendingProposal(self):
    proposal = proposal_utils.seedProposal(self.student.key, self.program.key())
    can_withdraw = proposal_logic.canProposalBeWithdrawn(proposal)

    # it should be possible to withdraw a pending proposal
    self.assertTrue(can_withdraw)

  def testCannotWithdrawWithdrawnProposals(self):
    proposal = proposal_utils.seedProposal(
        self.student.key, self.program.key(),
        status=proposal_model.STATUS_WITHDRAWN)
    can_withdraw = proposal_logic.canProposalBeWithdrawn(proposal)

    # it is not possible to withdraw already withdrawn proposal
    self.assertFalse(can_withdraw)

  def testCannotWithdrawIgnoredProposal(self):
    proposal = proposal_utils.seedProposal(
        self.student.key, self.program.key(),
        status=proposal_model.STATUS_IGNORED)
    can_withdraw = proposal_logic.canProposalBeWithdrawn(proposal)

    # it is not possible to withdraw ignored proposals
    self.assertFalse(can_withdraw)

  def testCannotWithdrawAcceptedOrRejectedProposal(self):
    proposal = proposal_utils.seedProposal(
        self.student.key, self.program.key(),
        status=proposal_model.STATUS_ACCEPTED)
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
    self.program = program_utils.seedGSoCProgram()

    # seed a new organization
    self.org = org_utils.seedSOCOrganization(self.program.key())

    # create a new profile and make it a student
    self.student = profile_utils.seedNDBStudent(self.program)

    # seed a new proposal and assign
    self.proposal = proposal_utils.seedProposal(
        self.student.key, self.program.key(), org_key=self.org.key)

  def testWithdrawProposal(self):
    # try to withdraw the proposal
    result = proposal_logic.withdrawProposal(self.proposal, self.student)

    # the proposal should be withdrawn
    self.assertTrue(result)
    self.assertEqual(proposal_model.STATUS_WITHDRAWN, self.proposal.status)
    self.assertEqual(self.student.student_data.number_of_proposals, 0)

  def testWithdrawProposalTwice(self):
    # try to withdraw the proposal twice
    proposal_logic.withdrawProposal(self.proposal, self.student)
    result = proposal_logic.withdrawProposal(self.proposal, self.student)

    # the result should also be true but number of proposals should not
    # be decreased twice
    self.assertTrue(result)
    self.assertEqual(proposal_model.STATUS_WITHDRAWN, self.proposal.status)
    self.assertEqual(self.student.student_data.number_of_proposals, 0)

  def testWithdrawProposalForStudentWithFewProposals(self):
    # create a few other proposals
    for _ in range(3):
      proposal_utils.seedProposal(self.student.key, self.program.key())

    # withdraw the main proposal
    result = proposal_logic.withdrawProposal(self.proposal, self.student)

    # the proposal should be withdrawn
    self.assertTrue(result)
    self.assertEqual(proposal_model.STATUS_WITHDRAWN, self.proposal.status)
    self.assertEqual(3, self.student.student_data.number_of_proposals)

  def testForIneligibleProposal(self):
    # set the proposal status to accepted
    self.proposal.status = proposal_model.STATUS_ACCEPTED
    self.proposal.put()

    # try to withdraw the proposal
    result = proposal_logic.withdrawProposal(self.proposal, self.student)

    # the proposal should not be withdrawn
    self.assertFalse(result)
    self.assertEqual(proposal_model.STATUS_ACCEPTED, self.proposal.status)
    self.assertEqual(1, self.student.student_data.number_of_proposals)


class CanSubmitProposalTest(unittest.TestCase):
  """Unit tests for canSubmitProposal function."""

  def setUp(self):
    sponsor = program_utils.seedSponsor()

    # seed a timeline and set student app period for now
    self.timeline = program_utils.seedTimeline(
        models=types.SOC_MODELS, timeline_id=TEST_PROGRAM_ID,
        sponsor_key=sponsor.key(), student_signup_start=timeline_utils.past(),
        student_signup_end=timeline_utils.future())

    self.program = program_utils.seedGSoCProgram(
        program_id=TEST_PROGRAM_ID, sponsor_key=sponsor.key(),
        timeline_key=self.timeline.key(), app_tasks_limit=3)

    self.student = profile_utils.seedNDBStudent(self.program)

  def testForStudentWithNoProposals(self):
    # it is possible to submit proposal during the student app period
    # and the student has not proposals
    can_submit = proposal_logic.canSubmitProposal(
        self.student, self.program, self.timeline)
    self.assertTrue(can_submit)

  def testForStudentWithMaxMinusOneProposals(self):
    # change the student so that already max - 1 proposals are submitted
    self.student.student_data.number_of_proposals = (
        self.program.apps_tasks_limit - 1)
    self.student.put()

    # it is still possible for the student to submit a proposal
    can_submit = proposal_logic.canSubmitProposal(
        self.student, self.program, self.timeline)
    self.assertTrue(can_submit)

  def testForStudentWithMaxProposals(self):
    # change the student so that max proposals are already submitted
    self.student.student_data.number_of_proposals = (
        self.program.apps_tasks_limit)
    self.student.put()

    # it is not possible to submit a next proposal
    can_submit = proposal_logic.canSubmitProposal(
        self.student, self.program, self.timeline)
    self.assertFalse(can_submit)

  def testBeforeStudentAppPeriod(self):
    # move the student app period to the future
    self.timeline.student_signup_start = timeline_utils.future()
    self.timeline.put()

    # it is not possible to submit a proposal now
    can_submit = proposal_logic.canSubmitProposal(
        self.student, self.program, self.timeline)
    self.assertFalse(can_submit)

  def testAfterStudentAppPeriod(self):
    # move the student app period to the future
    self.timeline.student_signup_end = timeline_utils.past()
    self.timeline.put()

    # it is not possible to submit a proposal now
    can_submit = proposal_logic.canSubmitProposal(
        self.student, self.program, self.timeline)
    self.assertFalse(can_submit)


class CanProposalBeResubmittedTest(unittest.TestCase):
  """Unit tests for canProposalBeResubmitted function."""

  def setUp(self):
    sponsor = program_utils.seedSponsor()

    # seed a timeline and set student app period for now
    self.timeline = program_utils.seedTimeline(
        models=types.SOC_MODELS, timeline_id=TEST_PROGRAM_ID,
        sponsor_key=sponsor.key(), student_signup_start=timeline_utils.past(),
        student_signup_end=timeline_utils.future(delta=50),
        accepted_students_announced_deadline=timeline_utils.future(delta=75))

    self.program = program_utils.seedGSoCProgram(
        program_id=TEST_PROGRAM_ID, sponsor_key=sponsor.key(),
        timeline_key=self.timeline.key(), app_tasks_limit=3)

    # seed a new student
    self.student = profile_utils.seedNDBStudent(self.program)

    # seed a new proposal
    self.proposal = proposal_utils.seedProposal(
        self.student.key, self.program.key(),
        status=proposal_model.STATUS_WITHDRAWN)

  def testResubmitWithdrawnProposal(self):
    # it should be possible to resubmit this proposal
    can_resubmit = proposal_logic.canProposalBeResubmitted(
        self.proposal, self.student, self.program, self.timeline)
    self.assertTrue(can_resubmit)

  def testResubmitForOtherStatuses(self):
    # set status of the proposal to accepted
    self.proposal.status = proposal_model.STATUS_ACCEPTED
    self.proposal.put()

    # it should not be possible to resubmit this proposal
    can_resubmit = proposal_logic.canProposalBeResubmitted(
        self.proposal, self.student, self.program, self.timeline)
    self.assertFalse(can_resubmit)

    # set status of the proposal to ignored
    self.proposal.status = proposal_model.STATUS_IGNORED
    self.proposal.put()

    # it should not be possible to resubmit this proposal
    can_resubmit = proposal_logic.canProposalBeResubmitted(
        self.proposal, self.student, self.program, self.timeline)
    self.assertFalse(can_resubmit)

    # set status of the proposal to invalid
    self.proposal.status = proposal_model.STATUS_INVALID
    self.proposal.put()

    # it should not be possible to resubmit this proposal
    can_resubmit = proposal_logic.canProposalBeResubmitted(
        self.proposal, self.student, self.program, self.timeline)
    self.assertFalse(can_resubmit)

    # set status of the proposal to pending
    self.proposal.status = proposal_model.STATUS_PENDING
    self.proposal.put()

    # it should not be possible to resubmit this proposal
    can_resubmit = proposal_logic.canProposalBeResubmitted(
        self.proposal, self.student, self.program, self.timeline)
    self.assertFalse(can_resubmit)

    # set status of the proposal to rejected
    self.proposal.status = proposal_model.STATUS_REJECTED
    self.proposal.put()

    # it should not be possible to resubmit this proposal
    can_resubmit = proposal_logic.canProposalBeResubmitted(
        self.proposal, self.student, self.program, self.timeline)
    self.assertFalse(can_resubmit)

  def testAfterStudentAppPeriod(self):
    # move the student app period to the future
    self.timeline.student_signup_end = timeline_utils.past()
    self.timeline.put()

    # it should still be possible to resubmit this proposal
    can_resubmit = proposal_logic.canProposalBeResubmitted(
        self.proposal, self.student, self.program, self.timeline)
    self.assertTrue(can_resubmit)

  def testAfterAcceptedStudentsAnnounced(self):
    """Tests that proposal cannot be resubmitted after announcing students."""
    # move the student app period to the future
    self.timeline.student_signup_end = timeline_utils.past()
    self.timeline.accepted_students_announced_deadline = timeline_utils.past()
    self.timeline.put()

    # it should not be possible to resubmit this proposal
    can_resubmit = proposal_logic.canProposalBeResubmitted(
        self.proposal, self.student, self.program, self.timeline)
    self.assertFalse(can_resubmit)

  def testForStudentWithMaxMinusOneProposals(self):
    # change the student so that already max - 1 proposals are submitted
    self.student.student_data.number_of_proposals = (
        self.program.apps_tasks_limit - 1)
    self.student.put()

    # it should not be possible to resubmit this proposal
    can_resubmit = proposal_logic.canProposalBeResubmitted(
        self.proposal, self.student, self.program, self.timeline)
    self.assertTrue(can_resubmit)

  def testForStudentWithMaxProposals(self):
    # change the student so that max proposals are already submitted
    self.student.student_data.number_of_proposals = (
        self.program.apps_tasks_limit)
    self.student.put()

    # it should not be possible to resubmit this proposal
    can_resubmit = proposal_logic.canProposalBeResubmitted(
        self.proposal, self.student, self.program, self.timeline)
    self.assertFalse(can_resubmit)


class ResubmitProposalTest(unittest.TestCase):
  """Unit tests for resubmitProposal function."""

  def setUp(self):
    sponsor = program_utils.seedSponsor()

    # seed a timeline and set student app period for now
    self.timeline = program_utils.seedTimeline(
        models=types.SOC_MODELS, timeline_id=TEST_PROGRAM_ID,
        sponsor_key=sponsor.key(), student_signup_start=timeline_utils.past(),
        student_signup_end=timeline_utils.future(delta=50),
        accepted_students_announced_deadline=timeline_utils.future(delta=75))

    self.program = program_utils.seedGSoCProgram(
        program_id=TEST_PROGRAM_ID, sponsor_key=sponsor.key(),
        timeline_key=self.timeline.key(), app_tasks_limit=3)

    # seed a new student info
    self.student = profile_utils.seedNDBStudent(self.program)

    # seed a new proposal
    self.proposal = proposal_utils.seedProposal(
        self.student.key, self.program.key(),
        status=proposal_model.STATUS_WITHDRAWN)

  def testResubmitProposal(self):
    result = proposal_logic.resubmitProposal(
        self.proposal, self.student, self.program, self.timeline)

    # it should have been possible to resubmit proposal
    self.assertTrue(result)
    self.assertEqual(self.proposal.status, proposal_model.STATUS_PENDING)
    self.assertEqual(self.student.student_data.number_of_proposals, 1)

  def testResubmitProposalTwice(self):
    # resubmit proposal twice
    proposal_logic.resubmitProposal(
        self.proposal, self.student, self.program, self.timeline)
    result = proposal_logic.resubmitProposal(
        self.proposal, self.student, self.program, self.timeline)

    # proposal should be resubmitted but no side effects are present
    self.assertEqual(result, True)
    self.assertEqual(self.proposal.status, proposal_model.STATUS_PENDING)
    self.assertEqual(self.student.student_data.number_of_proposals, 1)

  def testCannotResubmitProposal(self):
    # make it forbidden to resubmit proposal
    self.proposal.status = proposal_model.STATUS_ACCEPTED
    self.proposal.put()
    self.student.student_data.number_of_proposals = 1
    self.student.put()

    result = proposal_logic.resubmitProposal(
        self.proposal, self.student, self.program, self.timeline)

    # proposal should not be resubmitted
    self.assertFalse(result)
    self.assertEqual(self.proposal.status, proposal_model.STATUS_ACCEPTED)
    self.assertEqual(self.student.student_data.number_of_proposals, 1)


class AcceptProposalTest(unittest.TestCase):
  """Unit tests for acceptProposal function."""

  def setUp(self):
    # seed a new program
    self.program = program_utils.seedGSoCProgram()

    # seed a new organizations
    self.organization = org_utils.seedSOCOrganization(self.program.key())

    # seed a new profile and make it a student
    self.student = profile_utils.seedNDBStudent(self.program)

    # seed another profile and make it a mentor
    self.mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.organization.key])

    # seed a new proposal and assign the mentor
    self.proposal = proposal_utils.seedProposal(
        self.student.key, self.program.key(), org_key=self.organization.key,
        mentor_key=self.mentor.key, accept_as_project=True,
        abstract='test abstract')

  def testAcceptProposal(self):
    # accept proposal as project
    project = proposal_logic.acceptProposal(self.proposal)

    # proposal should be accepted
    self.assertEqual(self.proposal.status, proposal_model.STATUS_ACCEPTED)

    # number of projects should be increased
    student = self.student.key.get()
    self.assertEqual(student.student_data.number_of_projects, 1)

    # project should be created correctly
    self.assertIsNotNone(project)
    self.assertEqual(self.proposal.abstract, project.abstract)
    self.assertEqual(
        self.organization.key.to_old_key(),
        project_model.GSoCProject.org.get_value_for_datastore(project))
    self.assertEqual(self.program.key(), project.program.key())
    self.assertEqual(self.student.key.to_old_key(), project.parent_key())
    self.assertListEqual([self.mentor.key.to_old_key()], project.mentors)

  @unittest.skip('This test will work again when proposal and project are NDB')
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
    proposal_two = proposal_utils.seedProposal(
        self.student.key, self.program.key(), org_key=self.organization.key,
        mentor_key=self.mentor.key, accept_as_project=True,
        abstract='test abstract')

    # accept both proposals
    proposal_logic.acceptProposal(self.proposal)
    proposal_logic.acceptProposal(proposal_two)

    # student info should reflect that
    student = self.student.key.get()
    self.assertEqual(student.student_data.number_of_projects, 2)
    self.assertListEqual(
        student.student_data.project_for_orgs, [self.organization.key])


class RejectProposalTest(unittest.TestCase):
  """Unit tests for rejectProposal function."""

  def setUp(self):
    # seed a new program
    self.program = program_utils.seedGSoCProgram()

    # seed a new profile and make it a student
    self.student = profile_utils.seedNDBStudent(self.program)

    self.proposal = proposal_utils.seedProposal(
        self.student.key, self.program.key())

  def testRejectProposal(self):
    # reject the proposal
    proposal_logic.rejectProposal(self.proposal)

    # make sure the proposal is rejected and there is no project for it
    self.assertEqual(self.proposal.status, proposal_model.STATUS_REJECTED)
    self.assertEqual(self.student.student_data.number_of_projects, 0)
    self.assertListEqual(self.student.student_data.project_for_orgs, [])
