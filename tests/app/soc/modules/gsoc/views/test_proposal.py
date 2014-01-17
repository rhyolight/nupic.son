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
from tests.test_utils import GSoCDjangoTestCase

from soc.modules.gsoc.models import profile as profile_model
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
    profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])
    # TODO(daniel): take care of notifications
    #    notify_new_proposals=True, notify_public_comments=True,
    #    notify_private_comments=True)

    profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])

    self.profile_helper.createStudent()
    self.profile_helper.notificationSettings()
    self.timeline_helper.studentSignup()
    url = '/gsoc/proposal/submit/' + self.org.key.id()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertProposalTemplatesUsed(response)

    # test proposal POST
    override = {
        'program': self.gsoc, 'score': 0, 'nr_scores': 0, 'mentor': None,
        'org': self.org.key.to_old_key(),
        'status': 'pending', 'accept_as_project': False,
        'is_editable_post_deadline': False, 'extra': None, 'has_mentor': False,
    }
    response, properties = self.modelPost(
        url, proposal_model.GSoCProposal, override)
    self.assertResponseRedirect(response)

    self.assertEmailSent(to=mentor.email)
    # TODO(daniel): add assertEmailNotSent to DjangoTestCase
    #self.assertEmailNotSent(to=other_mentor.profile.email)

    proposal = proposal_model.GSoCProposal.all().get()

    # check org manually, as proposal.org will fail
    # TODO(daniel): it will not be needed when proposal model is updated
    org_key = proposal_model.GSoCProposal.org.get_value_for_datastore(proposal)
    self.assertEqual(org_key, self.org.key.to_old_key())
    proposal.org = None
    del properties['org']

    self.assertPropertiesEqual(properties, proposal)

  def testProposalsSubmissionLimit(self):
    self.gsoc.apps_tasks_limit = 5
    self.gsoc.put()

    profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])
    # TODO(daniel): take care of notifications
    #    notify_new_proposals=True, notify_public_comments=True,
    #    notify_private_comments=True)

    profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])

    self.profile_helper.createStudent()
    self.profile_helper.notificationSettings()
    self.timeline_helper.studentSignup()

    override = {
        'program': self.gsoc, 'score': 0, 'nr_scores': 0, 'mentor': None,
        'org': self.org, 'status': 'pending', 'accept_as_project': False,
        'is_editable_post_deadline': False, 'extra': None, 'has_mentor': False,
    }

    url = '/gsoc/proposal/submit/' + self.org.key.id()

    # Try to submit proposals four times.
    for i in range(5):
      response, properties = self.modelPost(
          url, proposal_model.GSoCProposal, override)
      self.assertResponseRedirect(response)

    response, properties = self.modelPost(
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
    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])
    # TODO(daniel): take care of notifications: notify_proposal_updates=True

    self.profile_helper.createStudentWithProposal(self.org, mentor)
    self.profile_helper.notificationSettings()
    self.timeline_helper.studentSignup()

    proposal = proposal_model.GSoCProposal.all().get()

    url = '/gsoc/proposal/update/%s/%s/%s' % (
        self.gsoc.key().name(), self.profile_helper.profile.link_id,
        proposal.key().id())
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
    proposal.org = None
    del properties['org']

    self.assertPropertiesEqual(properties, proposal)

    self.assertPropertiesEqual(properties, proposal)

    # after update last_modified_on should be updated which is not equal
    # to created_on
    self.assertNotEqual(proposal.created_on, proposal.last_modified_on)

    self.assertEmailSent(to=mentor.email)

  def testUpdateProposalAfterDeadline(self):
    """Tests attempting to update a proposal after the deadline has passed."""
    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])

    self.profile_helper.createStudentWithProposal(self.org, mentor)
    self.timeline_helper.studentsAnnounced()

    proposal = proposal_model.GSoCProposal.all().get()

    url = '/gsoc/proposal/update/%s/%s/%s' % (
        self.gsoc.key().name(), self.profile_helper.profile.link_id,
        proposal.key().id())
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testUpdateNonExistingProposal(self):
    self.profile_helper.createStudent()
    mock_id = 1
    url = '/gsoc/proposal/update/%s/%s/%s' % (
        self.gsoc.key().name(), self.profile_helper.profile.link_id, mock_id)
    response = self.get(url)
    self.assertResponseNotFound(response)

  def testWithdrawProposal(self):
    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])
    # TODO(daniel): take care of notifications: notify_proposal_updates=True

    self.profile_helper.createStudentWithProposal(self.org, mentor)
    self.profile_helper.notificationSettings()
    self.timeline_helper.studentSignup()

    proposal = proposal_model.GSoCProposal.all().get()

    url = '/gsoc/proposal/update/%s/%s/%s' % (
        self.gsoc.key().name(), self.profile_helper.profile.link_id,
        proposal.key().id())

    # withdraw proposal
    postdata = {
        'action': 'Withdraw',
        }
    response = self.post(url, postdata)

    # check if the proposal is withdrawn
    proposal = proposal_model.GSoCProposal.get(proposal.key())
    self.assertEqual(proposal_model.STATUS_WITHDRAWN, proposal.status)

    # check if number of proposals is decreased
    student_info = profile_model.GSoCStudentInfo.get(
        self.profile_helper.profile.student_info.key())
    self.assertEqual(0, student_info.number_of_proposals)

  def testResubmitProposal(self):
    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])
    # TODO(daniel): take care of notifications: notify_proposal_updates=True

    self.profile_helper.createStudentWithProposal(self.org, mentor)
    self.profile_helper.notificationSettings()
    self.timeline_helper.studentSignup()

    proposal = proposal_model.GSoCProposal.all().get()

    # make the proposal withdrawn so that it can be resubmitted
    proposal.status = proposal_model.STATUS_WITHDRAWN
    proposal.put()
    self.profile_helper.profile.student_info.number_of_proposals -= 1
    self.profile_helper.profile.student_info.put()

    url = '/gsoc/proposal/update/%s/%s/%s' % (
        self.gsoc.key().name(), self.profile_helper.profile.link_id,
        proposal.key().id())

    # resubmit proposal
    postdata = {
        'action': 'Resubmit',
        }
    response = self.post(url, postdata)

    # check if the proposal is resubmitted
    proposal = proposal_model.GSoCProposal.get(proposal.key())
    self.assertEqual(proposal_model.STATUS_PENDING, proposal.status)

    # check if number of proposals is increased
    student_info = profile_model.GSoCStudentInfo.get(
        self.profile_helper.profile.student_info.key())
    self.assertEqual(
        self.profile_helper.profile.student_info.number_of_proposals + 1,
        student_info.number_of_proposals)
