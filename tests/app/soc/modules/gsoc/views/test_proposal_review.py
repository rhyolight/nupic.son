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

"""Tests for proposal_review views.
"""

import httplib
import mock

from django import http

from melange.request import exception

from soc.modules.gsoc.logic import proposal as proposal_logic
from soc.modules.gsoc.models import profile as profile_model
from soc.modules.gsoc.models import proposal as proposal_model
from soc.modules.gsoc.models.proposal import GSoCProposal
from soc.modules.gsoc.views import proposal_review as proposal_review_view
from soc.modules.gsoc.views.helper import request_data

from tests import profile_utils
from tests.profile_utils import GSoCProfileHelper
from tests.test_utils import GSoCDjangoTestCase


class ProposalReviewTest(GSoCDjangoTestCase):
  """Tests proposal review page.
  """

  def setUp(self):
    super(ProposalReviewTest, self).setUp()
    self.init()

  def assertReviewTemplateUsed(self, response):
    """Asserts that all the proposal review were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/proposal/review.html')
    self.assertTemplateUsed(response, 'modules/gsoc/proposal/_comment_form.html')

  def createMentorWithSettings(self, email, notification_settings={}):
    user = profile_utils.seedUser(email=email)
    return profile_utils.seedGSoCProfile(
        self.program, user=user, mentor_for=[self.org.key.to_old_key()],
        **notification_settings)

  def createProposal(self, override_properties={}):
    properties = {
        'score': 0,
        'nr_scores': 0,
        'is_publicly_visible': False,
        'accept_as_project': False,
        'is_editable_post_deadline': False,
        'status': 'pending',
        'program': self.gsoc,
        'org': self.org.key.to_old_key(),
        'mentor': None
    }
    properties.update(override_properties)
    return self.seed(GSoCProposal, properties)

  def testReviewProposal(self):
    mentor = self.createMentorWithSettings('mentor@example.com',
        {'notify_new_proposals' :True, 'notify_public_comments': True,
         'notify_private_comments' :True})

    self.profile_helper.createStudent()
    self.profile_helper.notificationSettings()
    self.timeline_helper.studentSignup()

    proposal = self.createProposal({'scope': self.profile_helper.profile,
                                    'parent': self.profile_helper.profile})

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        self.profile_helper.user.key().name(),
        proposal.key().id())

    # test review GET
    url = '/gsoc/proposal/review/' + suffix
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertReviewTemplateUsed(response)

    self.assertNotContains(
        response,
        '<p class="status"><strong>Status:</strong> Pending</p>')

    # test comment POST
    from soc.modules.gsoc.models.comment import GSoCComment
    url = '/gsoc/proposal/comment/' + suffix
    override = {'author': self.profile_helper.profile, 'is_private': False}
    response, properties = self.modelPost(url, GSoCComment, override)
    self.assertResponseRedirect(response)

    comment = GSoCComment.all().ancestor(proposal).get()
    self.assertPropertiesEqual(properties, comment)

    self.assertEmailSent(to=mentor.email)

    # TODO(daniel): add assertEmailNotSent to DjangoTestCase
    # self.assertEmailNotSent(to=self.profile_helper.profile.email)

    self.profile_helper.deleteProfile()
    self.profile_helper.createMentor(self.org)

    # test score POST
    from soc.modules.gsoc.models.score import GSoCScore
    url = '/gsoc/proposal/score/' + suffix
    override = {
        'author': self.profile_helper.profile, 'parent': proposal, 'value': 1}
    response, properties = self.modelPost(url, GSoCScore, override)
    self.assertResponseOK(response)

    score = GSoCScore.all().ancestor(proposal).get()
    self.assertPropertiesEqual(properties, score)

    proposal = GSoCProposal.all().get()
    self.assertEqual(1, proposal.score)
    self.assertEqual(1, proposal.nr_scores)

    # test updating score
    override['value'] = 4
    response, properties = self.modelPost(url, GSoCScore, override)
    self.assertResponseOK(response)

    proposal = GSoCProposal.get(proposal.key())
    self.assertEqual(4, proposal.score)
    self.assertEqual(1, proposal.nr_scores)

    # test removing score
    override['value'] = 0
    response, properties = self.modelPost(url, GSoCScore, override)
    self.assertResponseOK(response)

    proposal = GSoCProposal.get(proposal.key())
    self.assertEqual(0, proposal.score)
    self.assertEqual(0, proposal.nr_scores)

  def testReviewProposalPublicView(self):
    student = profile_utils.seedGSoCStudent(self.program)

    proposal = self.createProposal({
        'is_publicly_visible': True,
        'scope': student,
        'parent': student
        })

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        student.user.key().name(),
        proposal.key().id())

    # test review GET
    url = '/gsoc/proposal/review/' + suffix
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/proposal/review.html')

  def testIgnoreProposalButton(self):
    student = profile_utils.seedGSoCStudent(self.program)

    proposal = self.createProposal({'scope': student, 'parent': student})

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        student.user.key().name(),
        proposal.key().id())

    self.profile_helper.createMentor(self.org)

    url = '/gsoc/proposal/ignore/' + suffix
    postdata = {'value': 'unchecked'}
    response = self.post(url, postdata)

    self.assertResponseForbidden(response)

    proposal = GSoCProposal.all().get()
    self.assertNotEqual(proposal.status, 'ignored')

  def testAcceptProposalButton(self):
    student = profile_utils.seedGSoCStudent(self.program)

    proposal = self.createProposal({'scope': student, 'parent': student})

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        student.user.key().name(),
        proposal.key().id())

    self.profile_helper.createMentor(self.org)

    url = '/gsoc/proposal/accept/' + suffix
    postdata = {'value': 'unchecked'}
    response = self.post(url, postdata)

    # fail if mentor tries to accept the proposal
    self.assertResponseForbidden(response)

    proposal = GSoCProposal.get(proposal.key())
    self.assertFalse(proposal.accept_as_project)

    # accept the proposal as project when the org admin tries to accept
    # the proposal
    self.profile_helper.createOrgAdmin(self.org)
    response = self.post(url, postdata)
    self.assertResponseOK(response)

    proposal = GSoCProposal.get(proposal.key())
    self.assertTrue(proposal.accept_as_project)

  def testProposalModificationButton(self):
    student = profile_utils.seedGSoCStudent(self.program)

    proposal = self.createProposal({'scope': student, 'parent': student})

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        student.user.key().name(),
        proposal.key().id())

    self.profile_helper.createMentor(self.org)

    url = '/gsoc/proposal/modification/' + suffix
    postdata = {'value': 'unchecked'}
    response = self.post(url, postdata)

    self.assertResponseOK(response)

    proposal = GSoCProposal.get(proposal.key())
    self.assertTrue(proposal.is_editable_post_deadline)

  def testWishToMentorButton(self):
    student = profile_utils.seedGSoCStudent(self.program)

    self.profile_helper.createMentor(self.org)

    other_mentor = self.createMentorWithSettings('other_mentor@example.com')

    proposal = self.createProposal({'scope': student, 'parent': student})

    suffix = "%s/%s/%d" % (
    self.gsoc.key().name(),
    student.user.key().name(),
    proposal.key().id())

    url = '/gsoc/proposal/wish_to_mentor/' + suffix
    postdata = {'value': 'unchecked'}
    response = self.post(url, postdata)

    proposal = GSoCProposal.get(proposal.key())
    self.assertIn(self.profile_helper.profile.key(), proposal.possible_mentors)

    postdata = {'value': 'checked'}
    response = self.post(url, postdata)

    proposal = GSoCProposal.get(proposal.key())
    self.assertNotIn(
        self.profile_helper.profile.key(), proposal.possible_mentors)

    other_mentor.mentor_for = []
    other_mentor.put()

    proposal.possible_mentors.append(other_mentor.key())
    proposal.put()

    url = '/gsoc/proposal/review/' + suffix
    response = self.get(url)

    proposal = GSoCProposal.get(proposal.key())
    self.assertNotIn(other_mentor.key(), proposal.possible_mentors)

  def testPubliclyVisibleButton(self):
    self.profile_helper.createStudent()

    proposal = self.createProposal({'scope': self.profile_helper.profile,
                                    'parent': self.profile_helper.profile})

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        self.profile_helper.user.key().name(),
        proposal.key().id())

    url = '/gsoc/proposal/publicly_visible/' + suffix
    postdata = {'value': 'unchecked'}
    response = self.post(url, postdata)

    self.assertResponseOK(response)

    proposal = GSoCProposal.get(proposal.key())
    self.assertTrue(proposal.is_publicly_visible)

  def testWithdrawProposalButton(self):
    self.profile_helper.createStudentWithProposal(self.org, None)
    self.timeline_helper.studentSignup()

    proposal = GSoCProposal.all().ancestor(self.profile_helper.profile).get()
    number_of_proposals = (
        self.profile_helper.profile.student_info.number_of_proposals)

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        self.profile_helper.user.key().name(),
        proposal.key().id())

    # withdraw the proposal
    url = '/gsoc/proposal/status/' + suffix
    postdata = {'value': proposal_review_view.TOGGLE_BUTTON_IS_WITHDRAWN}
    response = self.post(url, postdata)

    self.assertResponseOK(response)

    # check that the student proposal is withdrawn
    proposal = GSoCProposal.get(proposal.key())
    self.assertEqual(proposal.status, 'withdrawn')

    # check that number of proposals is updated
    student_info = profile_model.GSoCStudentInfo.get(
        self.profile_helper.profile.student_info.key())
    self.assertEqual(number_of_proposals - 1, student_info.number_of_proposals)

    # try withdrawing the proposal once more time
    url = '/gsoc/proposal/status/' + suffix
    postdata = {'value': proposal_review_view.TOGGLE_BUTTON_IS_WITHDRAWN}
    response = self.post(url, postdata)

    self.assertResponseOK(response)

    # check that the student proposal is still withdrawn
    proposal = GSoCProposal.get(proposal.key())
    self.assertEqual(proposal.status, 'withdrawn')

    # check that number of proposals is still the same
    student_info = profile_model.GSoCStudentInfo.get(
        self.profile_helper.profile.student_info.key())
    self.assertEqual(number_of_proposals - 1, student_info.number_of_proposals)

    # resubmit the proposal
    url = '/gsoc/proposal/status/' + suffix
    postdata = {'value': proposal_review_view.TOGGLE_BUTTON_NOT_WITHDRAWN}
    response = self.post(url, postdata)

    self.assertResponseOK(response)

    # check that the student proposal is pending
    proposal = GSoCProposal.get(proposal.key())
    self.assertEqual(proposal.status, 'pending')

    # check that number of proposals is increased again
    student_info = profile_model.GSoCStudentInfo.get(
        self.profile_helper.profile.student_info.key())
    self.assertEqual(number_of_proposals, student_info.number_of_proposals)

  def testAssignMentor(self):
    student = profile_utils.seedGSoCStudent(self.program)

    proposal = self.createProposal({'scope': student, 'parent': student})

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        student.user.key().name(),
        proposal.key().id())

    self.profile_helper.createMentor(self.org)

    url = '/gsoc/proposal/assign_mentor/' + suffix
    postdata = {'assign_mentor': self.profile_helper.profile.key()}
    response = self.post(url, postdata)

    self.assertResponseForbidden(response)

    proposal = GSoCProposal.all().get()
    self.assertIsNone(proposal.mentor)


class WithdrawProposalHandlerTest(GSoCDjangoTestCase):
  """Unit tests for WithdrawProposalHandler class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()
    self.profile = self.profile_helper.createStudentWithProposal(
        self.org, None)
    self.proposal = GSoCProposal.all().get()

    # view used as a callback for handler
    self.view = proposal_review_view.ProposalStatusSetter()

  def testCannotWithdrawProposal(self):
    """Tests that an error occurs when proposal cannot be withdrawn."""
    # proposal cannot be withdrawn, because it is rejected
    self.proposal.status = proposal_model.STATUS_REJECTED
    self.proposal.put()

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': self.profile.link_id,
        'id': self.proposal.key().id()
        }

    request = http.HttpRequest()
    data = request_data.RequestData(request, None, self.kwargs)

    handler = proposal_review_view.WithdrawProposalHandler(self.view)
    with mock.patch.object(
        proposal_logic, 'canProposalBeWithdrawn', return_value=False):
      with self.assertRaises(exception.UserError) as context:
        handler.handle(data, None, None)
      self.assertEqual(context.exception.status, httplib.FORBIDDEN)

  def testWithdrawProposal(self):
    """Tests that a proposal is successfully withdrawn if possible."""
    old_number_of_proposals = self.profile.student_info.number_of_proposals
    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': self.profile.link_id,
        'id': self.proposal.key().id()
        }

    request = http.HttpRequest()
    data = request_data.RequestData(request, None, self.kwargs)

    handler = proposal_review_view.WithdrawProposalHandler(None)
    with mock.patch.object(
        proposal_logic, 'canProposalBeWithdrawn', return_value=True):
      response = handler.handle(data, None, None)
    self.assertEqual(response.status_code, httplib.OK)

    # check that the proposal is withdrawn
    proposal = GSoCProposal.all().get()
    self.assertEqual(proposal.status, proposal_model.STATUS_WITHDRAWN)

    # check that number of proposals is updated
    student_info = profile_model.GSoCStudentInfo.all(
        ).ancestor(self.profile).get()
    self.assertEqual(
        old_number_of_proposals, student_info.number_of_proposals + 1)


class ResubmitProposalHandlerTest(GSoCDjangoTestCase):
  """Unit tests for ResubmitProposalHandler class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()
    self.profile = self.profile_helper.createStudentWithProposal(
        self.org, None)
    self.proposal = GSoCProposal.all().get()

  def testCannotResubmitProposal(self):
    """Tests that an error occurs when proposal cannot be withdrawn."""
    # proposal cannot be resubmitted, because it is rejected
    self.proposal.status = proposal_model.STATUS_REJECTED
    self.proposal.put()

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': self.profile.link_id,
        'id': self.proposal.key().id()
        }

    request = http.HttpRequest()
    data = request_data.RequestData(request, None, self.kwargs)

    handler = proposal_review_view.ResubmitProposalHandler(None)
    with mock.patch.object(
        proposal_logic, 'canProposalBeResubmitted', return_value=False):
      with self.assertRaises(exception.UserError) as context:
        handler.handle(data, None, None)
      self.assertEqual(context.exception.status, httplib.FORBIDDEN)

  def testResubmitProposal(self):
    """Tests that a proposal is successfully resubmitted if possible."""
    old_number_of_proposals = self.profile.student_info.number_of_proposals
    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': self.profile.link_id,
        'id': self.proposal.key().id()
        }

    request = http.HttpRequest()
    data = request_data.RequestData(request, None, self.kwargs)

    handler = proposal_review_view.ResubmitProposalHandler(None)
    with mock.patch.object(
        proposal_logic, 'canProposalBeResubmitted', return_value=True):
      response = handler.handle(data, None, None)
    self.assertEqual(response.status_code, httplib.OK)

    # check that the proposal is withdrawn
    proposal = GSoCProposal.all().get()
    self.assertEqual(proposal.status, proposal_model.STATUS_PENDING)

    # check that number of proposals is updated
    student_info = profile_model.GSoCStudentInfo.all(
        ).ancestor(self.profile).get()
    self.assertEqual(
        old_number_of_proposals, student_info.number_of_proposals - 1)
