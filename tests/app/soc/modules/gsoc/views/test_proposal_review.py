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

from google.appengine.ext import ndb

from django import http

from melange.request import exception

from soc.modules.gsoc.logic import proposal as proposal_logic
from soc.modules.gsoc.models import proposal as proposal_model
from soc.modules.gsoc.models.proposal import GSoCProposal
from soc.modules.gsoc.views import proposal_review as proposal_review_view
from soc.modules.gsoc.views.helper import request_data

from tests import profile_utils
from tests.profile_utils import GSoCProfileHelper
from tests.test_utils import GSoCDjangoTestCase
from tests.utils import proposal_utils


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
    # TODO(daniel): take care of notification settings
    user = profile_utils.seedUser(email=email)
    return profile_utils.seedNDBProfile(
        self.program.key(), user=user, mentor_for=[self.org.key])

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
    self.timeline_helper.studentSignup()
    # TODO(daniel): Re-seed settings when they are added.
    #  {'notify_new_proposals' :True, 'notify_public_comments': True,
    #   'notify_private_comments' :True}
    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedSOCStudent(self.program, user=user)
    proposal = proposal_utils.seedProposal(
        student.key, self.program.key(), org_key=self.org.key)

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        student.key.parent().id(),
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
    override = {'author': student.key.to_old_key(), 'is_private': False}
    response, properties = self.modelPost(url, GSoCComment, override)
    self.assertResponseRedirect(response)

    comment = GSoCComment.all().ancestor(proposal).get()
    author_key = ndb.Key.from_old_key(
        GSoCComment.author.get_value_for_datastore(comment))
    self.assertEqual(author_key, student.key)

    # TODO(daniel): notifications
    # self.assertEmailSent(to=mentor.email)

    # TODO(daniel): add assertEmailNotSent to DjangoTestCase
    # self.assertEmailNotSent(to=self.profile_helper.profile.email)

    # login as a mentor
    profile_utils.loginNDB(mentor.key.parent().get())

    # test score POST
    from soc.modules.gsoc.models.score import GSoCScore
    url = '/gsoc/proposal/score/' + suffix
    override = {
        'author': mentor.key.to_old_key(), 'parent': proposal, 'value': 1}
    response, properties = self.modelPost(url, GSoCScore, override)
    self.assertResponseOK(response)

    score = GSoCScore.all().ancestor(proposal).get()
    author_key = ndb.Key.from_old_key(
        GSoCScore.author.get_value_for_datastore(score))
    self.assertEqual(author_key, mentor.key)
    self.assertEqual(1, score.value)

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
    student = profile_utils.seedSOCStudent(self.program)
    proposal = proposal_utils.seedProposal(
        student.key, self.program.key(), is_publicly_visible=True)

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        student.key.parent().id(),
        proposal.key().id())

    # test review GET
    url = '/gsoc/proposal/review/' + suffix
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/proposal/review.html')

  def testIgnoreProposalButton(self):
    student = profile_utils.seedSOCStudent(self.program)
    proposal = proposal_utils.seedProposal(
        student.key, self.program.key(), org_key=self.org.key)

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        student.profile_id,
        proposal.key().id())

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, mentor_for=[self.org.key])

    url = '/gsoc/proposal/ignore/' + suffix
    postdata = {'value': 'unchecked'}
    response = self.post(url, postdata)

    self.assertResponseForbidden(response)

    proposal = GSoCProposal.all().get()
    self.assertNotEqual(proposal.status, 'ignored')

  def testAcceptProposalButton(self):
    student = profile_utils.seedSOCStudent(self.program)
    proposal = proposal_utils.seedProposal(
        student.key, self.program.key(), org_key=self.org.key)

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        student.key.parent().id(),
        proposal.key().id())

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, mentor_for=[self.org.key])

    url = '/gsoc/proposal/accept/' + suffix
    postdata = {'value': 'unchecked'}
    response = self.post(url, postdata)

    # fail if mentor tries to accept the proposal
    self.assertResponseForbidden(response)

    proposal = GSoCProposal.get(proposal.key())
    self.assertFalse(proposal.accept_as_project)

    # accept the proposal as project when the org admin tries to accept
    # the proposal
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[self.org.key])

    response = self.post(url, postdata)
    self.assertResponseOK(response)

    proposal = GSoCProposal.get(proposal.key())
    self.assertTrue(proposal.accept_as_project)

  def testProposalModificationButton(self):
    student = profile_utils.seedSOCStudent(self.program)
    proposal = proposal_utils.seedProposal(
        student.key, self.program.key(), org_key=self.org.key)

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        student.key.parent().id(),
        proposal.key().id())

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, mentor_for=[self.org.key])

    url = '/gsoc/proposal/modification/' + suffix
    postdata = {'value': 'unchecked'}
    response = self.post(url, postdata)

    self.assertResponseOK(response)

    proposal = GSoCProposal.get(proposal.key())
    self.assertTrue(proposal.is_editable_post_deadline)

  def testWishToMentorButton(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    mentor = profile_utils.seedNDBProfile(
        self.program.key(), user=user, mentor_for=[self.org.key])

    student = profile_utils.seedSOCStudent(self.program)
    proposal = proposal_utils.seedProposal(
        student.key, self.program.key(), org_key=self.org.key)

    other_mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        student.key.parent().id(),
        proposal.key().id())

    url = '/gsoc/proposal/wish_to_mentor/' + suffix
    postdata = {'value': 'unchecked'}
    self.post(url, postdata)

    proposal = GSoCProposal.get(proposal.key())
    self.assertIn(mentor.key.to_old_key(), proposal.possible_mentors)

    postdata = {'value': 'checked'}
    self.post(url, postdata)

    proposal = GSoCProposal.get(proposal.key())
    self.assertNotIn(mentor.key.to_old_key(), proposal.possible_mentors)

    # TODO(daniel): this section (mentor retires) should go to another test
    other_mentor.mentor_for = []
    other_mentor.put()

    proposal.possible_mentors.append(other_mentor.key.to_old_key())
    proposal.put()

    url = '/gsoc/proposal/review/' + suffix
    self.get(url)

    proposal = GSoCProposal.get(proposal.key())
    self.assertNotIn(other_mentor.key.to_old_key(), proposal.possible_mentors)

  def testPubliclyVisibleButton(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)

    student = profile_utils.seedSOCStudent(self.program, user=user)
    proposal = proposal_utils.seedProposal(
        student.key, self.program.key(), org_key=self.org.key)

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        user.key.id(),
        proposal.key().id())

    url = '/gsoc/proposal/publicly_visible/' + suffix
    postdata = {'value': 'unchecked'}
    response = self.post(url, postdata)

    self.assertResponseOK(response)

    proposal = GSoCProposal.get(proposal.key())
    self.assertTrue(proposal.is_publicly_visible)

  def testWithdrawProposalButton(self):
    self.timeline_helper.studentSignup()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedSOCStudent(self.program, user=user)
    proposal = proposal_utils.seedProposal(
        student.key, self.program.key(), org_key=self.org.key)

    number_of_proposals = student.student_data.number_of_proposals

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        student.key.parent().id(),
        proposal.key().id())

    # withdraw the proposal
    url = '/gsoc/proposal/status/' + suffix
    postdata = {'value': proposal_review_view.TOGGLE_BUTTON_IS_WITHDRAWN}
    response = self.post(url, postdata)

    self.assertResponseOK(response)

    # check that the student proposal is withdrawn
    proposal = GSoCProposal.get(proposal.key())
    self.assertEqual(proposal.status, proposal_model.STATUS_WITHDRAWN)

    # check that number of proposals is updated
    student = student.key.get()
    self.assertEqual(
        number_of_proposals - 1, student.student_data.number_of_proposals)

    # try withdrawing the proposal once more time
    url = '/gsoc/proposal/status/' + suffix
    postdata = {'value': proposal_review_view.TOGGLE_BUTTON_IS_WITHDRAWN}
    response = self.post(url, postdata)

    self.assertResponseOK(response)

    # check that the student proposal is still withdrawn
    proposal = GSoCProposal.get(proposal.key())
    self.assertEqual(proposal.status, proposal_model.STATUS_WITHDRAWN)

    # check that number of proposals is still the same
    student = student.key.get()
    self.assertEqual(
        number_of_proposals - 1, student.student_data.number_of_proposals)

    # resubmit the proposal
    url = '/gsoc/proposal/status/' + suffix
    postdata = {'value': proposal_review_view.TOGGLE_BUTTON_NOT_WITHDRAWN}
    response = self.post(url, postdata)

    self.assertResponseOK(response)

    # check that the student proposal is pending
    proposal = GSoCProposal.get(proposal.key())
    self.assertEqual(proposal.status, proposal_model.STATUS_PENDING)

    # check that number of proposals is increased again
    student = student.key.get()
    self.assertEqual(
        number_of_proposals, student.student_data.number_of_proposals)

  def testAssignMentor(self):
    student = profile_utils.seedSOCStudent(self.program)
    proposal = proposal_utils.seedProposal(
        student.key, self.program.key(), org_key=self.org.key, mentor=None)

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        student.profile_id,
        proposal.key().id())

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    mentor = profile_utils.seedNDBProfile(
        self.program.key(), user=user, mentor_for=[self.org.key])

    url = '/gsoc/proposal/assign_mentor/' + suffix
    postdata = {'assign_mentor': mentor.key}
    response = self.post(url, postdata)

    self.assertResponseForbidden(response)

    proposal = GSoCProposal.all().get()

    mentor_key = GSoCProposal.mentor.get_value_for_datastore(proposal)
    self.assertIsNone(mentor_key)


class WithdrawProposalHandlerTest(GSoCDjangoTestCase):
  """Unit tests for WithdrawProposalHandler class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()
    user = profile_utils.seedNDBUser()
    self.profile = profile_utils.seedSOCStudent(self.program, user=user)
    profile_utils.loginNDB(user)

    self.proposal = proposal_utils.seedProposal(
        self.profile.key, self.program.key(), org_key=self.org.key)

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
        'user': self.profile.profile_id,
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
    old_number_of_proposals = self.profile.student_data.number_of_proposals
    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': self.profile.profile_id,
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
    profile = self.profile.key.get()
    self.assertEqual(
        old_number_of_proposals, profile.student_data.number_of_proposals + 1)


class ResubmitProposalHandlerTest(GSoCDjangoTestCase):
  """Unit tests for ResubmitProposalHandler class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()
    user = profile_utils.seedNDBUser()
    self.profile = profile_utils.seedSOCStudent(self.program, user=user)
    profile_utils.loginNDB(user)

    self.proposal = proposal_utils.seedProposal(
        self.profile.key, self.program.key(), org_key=self.org.key)

  def testCannotResubmitProposal(self):
    """Tests that an error occurs when proposal cannot be withdrawn."""
    # proposal cannot be resubmitted, because it is rejected
    self.proposal.status = proposal_model.STATUS_REJECTED
    self.proposal.put()

    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': self.profile.profile_id,
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
    old_number_of_proposals = self.profile.student_data.number_of_proposals
    self.kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': self.profile.profile_id,
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
    profile = self.profile.key.get()
    self.assertEqual(
        old_number_of_proposals, profile.student_data.number_of_proposals - 1)
