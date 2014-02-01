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

"""Tests for proposal view."""

from tests import profile_utils
from tests.utils import proposal_utils
from tests.test_utils import GSoCDjangoTestCase

from soc.modules.gsoc.models import proposal as proposal_model


class ProposalTest(GSoCDjangoTestCase):
  """Tests proposal page.
  """

  def setUp(self):
    super(ProposalTest, self).setUp()
    self.init()

  def assertProposalTemplatesUsed(self, response):
    """Asserts that all the templates from the proposal were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/proposal/base.html')
    self.assertTemplateUsed(response, 'modules/gsoc/_form.html')

  def testSubmitProposal(self):
    self.timeline_helper.studentSignup()

    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])
    # TODO(daniel): take care of notifications
    #    notify_new_proposals=True, notify_public_comments=True,
    #    notify_private_comments=True)

    profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedSOCStudent(self.program, user)

    # TODO(daniel): take care of notifications
    # self.profile_helper.notificationSettings()

    url = '/gsoc/proposal/submit/' + self.org.key.id()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertProposalTemplatesUsed(response)

    # test proposal POST
    override = {
        'program': self.gsoc, 'score': 0, 'nr_scores': 0, 'mentor': None,
        'org': self.org.key.to_old_key(), 'is_publicly_visible': False,
        'status': 'pending', 'accept_as_project': False,
        'is_editable_post_deadline': False, 'extra': None, 'has_mentor': False,
    }
    response, _ = self.modelPost(
        url, proposal_model.GSoCProposal, override)
    self.assertResponseRedirect(response)

    # TODO(daniel): take care of notifications
    # self.assertEmailSent(to=mentor.contact.email)
    # TODO(daniel): add assertEmailNotSent to DjangoTestCase
    #self.assertEmailNotSent(to=other_mentor.profile.email)

    proposal = proposal_model.GSoCProposal.all().get()

    # check org manually, as proposal.org will fail
    # TODO(daniel): it will not be needed when proposal model is updated
    org_key = proposal_model.GSoCProposal.org.get_value_for_datastore(proposal)
    self.assertEqual(org_key, self.org.key.to_old_key())

    self.assertFalse(proposal.is_publicly_visible)
    self.assertIsNone(proposal.extra)
    self.assertFalse(proposal.accept_as_project)
    self.assertFalse(proposal.is_editable_post_deadline)

  def testProposalsSubmissionLimit(self):
    self.timeline_helper.studentSignup()

    self.gsoc.apps_tasks_limit = 5
    self.gsoc.put()

    profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])
    # TODO(daniel): take care of notifications
    #    notify_new_proposals=True, notify_public_comments=True,
    #    notify_private_comments=True)

    profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedSOCStudent(self.program, user)

    # TODO(daniel): take care of notifications
    # self.profile_helper.notificationSettings()

    override = {
        'program': self.gsoc, 'score': 0, 'nr_scores': 0, 'mentor': None,
        'org': self.org, 'status': 'pending', 'accept_as_project': False,
        'is_editable_post_deadline': False, 'extra': None, 'has_mentor': False,
    }

    url = '/gsoc/proposal/submit/' + self.org.key.id()

    # Try to submit proposals four times.
    for _ in range(5):
      response, _ = self.modelPost(
          url, proposal_model.GSoCProposal, override)
      self.assertResponseRedirect(response)

    response, _ = self.modelPost(
        url, proposal_model.GSoCProposal, override)
    self.assertResponseForbidden(response)


  def testSubmitProposalWhenInactive(self):
    """Test the submission of student proposals during the student signup
    period is not active.
    """
    self.profile_helper.createStudent()
    self.timeline_helper.orgSignup()
    url = '/gsoc/proposal/submit/' + self.org.key.id()
    response = self.get(url)
    self.assertResponseForbidden(response)

    self.timeline_helper.offSeason()
    url = '/gsoc/proposal/submit/' + self.org.key.id()
    response = self.get(url)
    self.assertResponseForbidden(response)

    self.timeline_helper.kickoff()
    url = '/gsoc/proposal/submit/' + self.org.key.id()
    response = self.get(url)
    self.assertResponseForbidden(response)

    self.timeline_helper.orgsAnnounced()
    url = '/gsoc/proposal/submit/' + self.org.key.id()
    response = self.get(url)
    self.assertResponseForbidden(response)

    self.timeline_helper.studentsAnnounced()
    url = '/gsoc/proposal/submit/' + self.org.key.id()
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testUpdateProposal(self):
    """Test update proposals."""
    self.timeline_helper.studentSignup()

    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])
    # TODO(daniel): take care of notifications: notify_proposal_updates=True

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedSOCStudent(self.program, user)
    proposal = proposal_utils.seedProposal(
        student.key, self.program.key(), org_key=self.org.key,
        mentor_key=mentor.key)
    # TODO(daniel): take care of notifications
    # self.profile_helper.notificationSettings()

    url = '/gsoc/proposal/update/%s/%s/%s' % (
        self.gsoc.key().name(), student.profile_id, proposal.key().id())
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertProposalTemplatesUsed(response)

    override = {
        'program': self.gsoc, 'score': 0, 'nr_scores': 0, 'has_mentor': True,
        'mentor': mentor, 'org': self.org, 'status': 'pending',
        'action': 'Update', 'is_publicly_visible': False, 'extra': None,
        'accept_as_project': False, 'is_editable_post_deadline': False
    }
    response, properties = self.modelPost(
        url, proposal_model.GSoCProposal, override)
    self.assertResponseRedirect(response)

    properties.pop('action')

    proposal = proposal_model.GSoCProposal.all().get()

    # check org manually, as proposal.org will fail
    # TODO(daniel): it will not be needed when proposal model is updated
    org_key = proposal_model.GSoCProposal.org.get_value_for_datastore(proposal)
    self.assertEqual(org_key, self.org.key.to_old_key())

    self.assertFalse(proposal.is_publicly_visible)
    self.assertIsNone(proposal.extra)
    self.assertFalse(proposal.accept_as_project)
    self.assertFalse(proposal.is_editable_post_deadline)

    # after update last_modified_on should be updated which is not equal
    # to created_on
    self.assertNotEqual(proposal.created_on, proposal.last_modified_on)

    print mentor.contact.email
    self.assertEmailSent(to=mentor.contact.email)

  def testUpdateProposalAfterDeadline(self):
    """Tests attempting to update a proposal after the deadline has passed."""
    self.timeline_helper.studentsAnnounced()

    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedSOCStudent(self.program, user)
    proposal = proposal_utils.seedProposal(
        student.key, self.program.key(), org_key=self.org.key,
        mentor_key=mentor.key)

    url = '/gsoc/proposal/update/%s/%s/%s' % (
        self.gsoc.key().name(), student.profile_id, proposal.key().id())
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testUpdateNonExistingProposal(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedSOCStudent(self.program, user=user)

    mock_id = 1
    url = '/gsoc/proposal/update/%s/%s/%s' % (
        self.gsoc.key().name(), student.profile_id, mock_id)
    response = self.get(url)
    self.assertResponseNotFound(response)

  def testWithdrawProposal(self):
    self.timeline_helper.studentSignup()

    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])
    # TODO(daniel): take care of notifications: notify_proposal_updates=True

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedSOCStudent(self.program, user)
    proposal = proposal_utils.seedProposal(
        student.key, self.program.key(), org_key=self.org.key,
        mentor_key=mentor.key)

    # TODO(daniel): take care of notifications
    #self.profile_helper.notificationSettings()

    url = '/gsoc/proposal/update/%s/%s/%s' % (
        self.gsoc.key().name(), student.profile_id, proposal.key().id())

    # withdraw proposal
    postdata = {
        'action': 'Withdraw',
        }
    response = self.post(url, postdata)

    # check if the proposal is withdrawn
    proposal = proposal_model.GSoCProposal.get(proposal.key())
    self.assertEqual(proposal_model.STATUS_WITHDRAWN, proposal.status)

    # check if number of proposals is decreased
    student = student.key.get()
    self.assertEqual(0, student.student_data.number_of_proposals)

  def testResubmitProposal(self):
    self.timeline_helper.studentSignup()

    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])
    # TODO(daniel): take care of notifications: notify_proposal_updates=True

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedSOCStudent(self.program, user)
    proposal = proposal_utils.seedProposal(
        student.key, self.program.key(), org_key=self.org.key,
        mentor_key=mentor.key, status=proposal_model.STATUS_WITHDRAWN)

    # TODO(daniel): take care of notifications
    # self.profile_helper.notificationSettings()

    url = '/gsoc/proposal/update/%s/%s/%s' % (
        self.gsoc.key().name(), student.profile_id, proposal.key().id())

    # resubmit proposal
    postdata = {'action': 'Resubmit'}
    self.post(url, postdata)

    # check if the proposal is resubmitted
    proposal = proposal_model.GSoCProposal.get(proposal.key())
    self.assertEqual(proposal_model.STATUS_PENDING, proposal.status)

    student = student.key.get()
    # check if number of proposals is increased
    self.assertEqual(student.student_data.number_of_proposals, 1)
