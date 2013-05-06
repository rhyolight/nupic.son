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


from tests.profile_utils import GSoCProfileHelper
from tests.test_utils import GSoCDjangoTestCase
from tests.test_utils import MailTestCase

from soc.modules.gsoc.models import profile as profile_model
from soc.modules.gsoc.models import proposal as proposal_model


class ProposalTest(MailTestCase, GSoCDjangoTestCase):
  """Tests proposal page.
  """

  def setUp(self):
    super(ProposalTest, self).setUp()
    self.init()

  def assertProposalTemplatesUsed(self, response):
    """Asserts that all the templates from the proposal were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/modules/gsoc/proposal/base.html')
    self.assertTemplateUsed(response, 'v2/modules/gsoc/_form.html')

  def testSubmitProposal(self):
    mentor = GSoCProfileHelper(self.gsoc, self.dev_test)
    mentor.createOtherUser('mentor@example.com')
    mentor.createMentor(self.org)
    mentor.notificationSettings(
        new_proposals=True, public_comments=True, private_comments=True)

    other_mentor = GSoCProfileHelper(self.gsoc, self.dev_test)
    other_mentor.createOtherUser('other_mentor@example.com')
    other_mentor.createMentor(self.org)
    other_mentor.notificationSettings()

    self.data.createStudent()
    self.data.notificationSettings()
    self.timeline.studentSignup()
    url = '/gsoc/proposal/submit/' + self.org.key().name()
    response = self.get(url)
    self.assertProposalTemplatesUsed(response)

    # test proposal POST
    override = {
        'program': self.gsoc, 'score': 0, 'nr_scores': 0, 'mentor': None,
        'org': self.org, 'status': 'pending', 'accept_as_project': False,
        'is_editable_post_deadline': False, 'extra': None, 'has_mentor': False,
    }
    response, properties = self.modelPost(
        url, proposal_model.GSoCProposal, override)
    self.assertResponseRedirect(response)

    self.assertEmailSent(to=mentor.profile.email, n=1)
    self.assertEmailNotSent(to=other_mentor.profile.email)

    proposal = proposal_model.GSoCProposal.all().get()
    self.assertPropertiesEqual(properties, proposal)

  def testProposalsSubmissionLimit(self):
    self.gsoc.apps_tasks_limit = 5
    self.gsoc.put()

    mentor = GSoCProfileHelper(self.gsoc, self.dev_test)
    mentor.createOtherUser('mentor@example.com')
    mentor.createMentor(self.org)
    mentor.notificationSettings(
        new_proposals=True, public_comments=True, private_comments=True)

    other_mentor = GSoCProfileHelper(self.gsoc, self.dev_test)
    other_mentor.createOtherUser('other_mentor@example.com')
    other_mentor.createMentor(self.org)
    other_mentor.notificationSettings()

    self.data.createStudent()
    self.data.notificationSettings()
    self.timeline.studentSignup()

    override = {
        'program': self.gsoc, 'score': 0, 'nr_scores': 0, 'mentor': None,
        'org': self.org, 'status': 'pending', 'accept_as_project': False,
        'is_editable_post_deadline': False, 'extra': None, 'has_mentor': False,
    }

    url = '/gsoc/proposal/submit/' + self.org.key().name()

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
    self.data.createStudent()
    self.timeline.orgSignup()
    url = '/gsoc/proposal/submit/' + self.org.key().name()
    response = self.get(url)
    self.assertResponseForbidden(response)

    self.timeline.offSeason()
    url = '/gsoc/proposal/submit/' + self.org.key().name()
    response = self.get(url)
    self.assertResponseForbidden(response)

    self.timeline.kickoff()
    url = '/gsoc/proposal/submit/' + self.org.key().name()
    response = self.get(url)
    self.assertResponseForbidden(response)

    self.timeline.orgsAnnounced()
    url = '/gsoc/proposal/submit/' + self.org.key().name()
    response = self.get(url)
    self.assertResponseForbidden(response)

    self.timeline.studentsAnnounced()
    url = '/gsoc/proposal/submit/' + self.org.key().name()
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testUpdateProposal(self):
    """Test update proposals."""
    mentor = GSoCProfileHelper(self.gsoc, self.dev_test)
    mentor.createOtherUser('mentor@example.com')
    mentor.createMentor(self.org)
    mentor.notificationSettings(proposal_updates=True)

    self.data.createStudentWithProposal(self.org, mentor.profile)
    self.data.notificationSettings()
    self.timeline.studentSignup()

    proposal = proposal_model.GSoCProposal.all().get()

    url = '/gsoc/proposal/update/%s/%s/%s' % (
        self.gsoc.key().name(), self.data.profile.link_id, proposal.key().id())
    response = self.get(url)
    self.assertProposalTemplatesUsed(response)

    override = {
        'program': self.gsoc, 'score': 0, 'nr_scores': 0, 'has_mentor': True,
        'mentor': mentor.profile, 'org': self.org, 'status': 'pending',
        'action': 'Update', 'is_publicly_visible': False, 'extra': None,
        'accept_as_project': False, 'is_editable_post_deadline': False
    }
    response, properties = self.modelPost(
        url, proposal_model.GSoCProposal, override)
    self.assertResponseRedirect(response)

    properties.pop('action')

    proposal = proposal_model.GSoCProposal.all().get()
    self.assertPropertiesEqual(properties, proposal)

    # after update last_modified_on should be updated which is not equal
    # to created_on
    self.assertNotEqual(proposal.created_on, proposal.last_modified_on)

    self.assertEmailSent(to=mentor.profile.email, n=1)

  def testUpdateNonExistingProposal(self):
    self.data.createStudent()
    mock_id = 1
    url = '/gsoc/proposal/update/%s/%s/%s' % (
        self.gsoc.key().name(), self.data.profile.link_id, mock_id)
    response = self.get(url)
    self.assertResponseNotFound(response)

  def testWithdrawProposal(self):
    mentor = GSoCProfileHelper(self.gsoc, self.dev_test)
    mentor.createOtherUser('mentor@example.com')
    mentor.createMentor(self.org)
    mentor.notificationSettings(proposal_updates=True)

    self.data.createStudentWithProposal(self.org, mentor.profile)
    self.data.notificationSettings()
    self.timeline.studentSignup()

    proposal = proposal_model.GSoCProposal.all().get()

    url = '/gsoc/proposal/update/%s/%s/%s' % (
        self.gsoc.key().name(), self.data.profile.link_id, proposal.key().id())

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
        self.data.profile.student_info.key())
    self.assertEqual(0, student_info.number_of_proposals)

  def testResubmitProposal(self):
    mentor = GSoCProfileHelper(self.gsoc, self.dev_test)
    mentor.createOtherUser('mentor@example.com')
    mentor.createMentor(self.org)
    mentor.notificationSettings(proposal_updates=True)

    self.data.createStudentWithProposal(self.org, mentor.profile)
    self.data.notificationSettings()
    self.timeline.studentSignup()

    proposal = proposal_model.GSoCProposal.all().get()

    # make the proposal withdrawn so that it can be resubmitted
    proposal.status = proposal_model.STATUS_WITHDRAWN
    proposal.put()
    self.data.profile.student_info.number_of_proposals -= 1
    self.data.profile.student_info.put()

    url = '/gsoc/proposal/update/%s/%s/%s' % (
        self.gsoc.key().name(), self.data.profile.link_id, proposal.key().id())

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
        self.data.profile.student_info.key())
    self.assertEqual(
        self.data.profile.student_info.number_of_proposals + 1,
        student_info.number_of_proposals)
