#!/usr/bin/env python2.5
#
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

__authors__ = [
  '"Madhusudan.C.S" <madhusudancs@gmail.com>',
  '"Sverre Rabbelier" <sverre@rabbelier.nl>',
  ]


from tests.profile_utils import GSoCProfileHelper
from tests.test_utils import DjangoTestCase
from tests.test_utils import MailTestCase
from tests.timeline_utils import TimelineHelper

from soc.modules.gsoc.models.proposal import GSoCProposal


class ProposalReviewTest(MailTestCase, DjangoTestCase):
  """Tests proposal review page.
  """

  def setUp(self):
    super(ProposalReviewTest, self).setUp()
    self.init()

  def assertReviewTemplateUsed(self, response):
    """Asserts that all the proposal review were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/modules/gsoc/proposal/review.html')
    self.assertTemplateUsed(response, 'v2/modules/gsoc/proposal/_comment_form.html')

  def createMentorWithSettings(self, email, notification_settings={}):
    mentor = GSoCProfileHelper(self.gsoc, self.dev_test)
    mentor.createOtherUser(email)
    mentor.createMentor(self.org)
    mentor.notificationSettings(**notification_settings)
    return mentor

  def createProposal(self, override_properties={}):
    properties = {
        'score': 0, 'nr_scores': 0, 'is_publicly_visible': False,
        'accept_as_project': False, 'is_editable_post_deadline': False,
        'status': 'pending', 'program': self.gsoc, 'org': self.org,
        'mentor': None
    }
    properties.update(override_properties)
    return self.seed(GSoCProposal, properties)

  def testReviewProposal(self):
    mentor = self.createMentorWithSettings('mentor@example.com', 
        {'new_proposals' :True, 'public_comments': True,
         'private_comments' :True})

    self.data.createStudent()
    self.data.notificationSettings()
    self.timeline.studentSignup()

    proposal = self.createProposal({'scope': self.data.profile,
                                    'parent': self.data.profile})

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        self.data.user.key().name(),
        proposal.key().id())

    # test review GET
    url = '/gsoc/proposal/review/' + suffix
    response = self.client.get(url)
    self.assertReviewTemplateUsed(response)

    # test comment POST
    from soc.modules.gsoc.models.comment import GSoCComment
    url = '/gsoc/proposal/comment/' + suffix
    override = {'author': self.data.profile, 'is_private': False}
    response, properties = self.modelPost(url, GSoCComment, override)
    self.assertResponseRedirect(response)

    comment = GSoCComment.all().get()
    self.assertPropertiesEqual(properties, comment)

    self.assertEmailSent(to=mentor.profile.email, n=1)
    self.assertEmailNotSent(to=self.data.profile.email)

    # Hacky
    self.data.createMentor(self.org)
    self.data.profile.student_info = None
    self.data.profile.put()

    # test score POST
    from soc.modules.gsoc.models.score import GSoCScore
    url = '/gsoc/proposal/score/' + suffix
    override = {'author': self.data.profile, 'parent': proposal, 'value': 1}
    response, properties = self.modelPost(url, GSoCScore, override)
    self.assertResponseOK(response)

    score = GSoCScore.all().get()
    self.assertPropertiesEqual(properties, score)

    proposal = GSoCProposal.all().get()
    self.assertEqual(1, proposal.score)
    self.assertEqual(1, proposal.nr_scores)

    # test updating score
    override['value'] = 4
    response, properties = self.modelPost(url, GSoCScore, override)
    self.assertResponseOK(response)

    proposal = GSoCProposal.all().get()
    self.assertEqual(4, proposal.score)
    self.assertEqual(1, proposal.nr_scores)

    # test removing score
    override['value'] = 0
    response, properties = self.modelPost(url, GSoCScore, override)
    self.assertResponseOK(response)

    proposal = GSoCProposal.all().get()
    self.assertEqual(0, proposal.score)
    self.assertEqual(0, proposal.nr_scores)

  def testReviewProposalPublicView(self):
    student = GSoCProfileHelper(self.gsoc, self.dev_test)
    student.createOtherUser('student@example.com')
    student.createStudent()

    proposal = self.createProposal({'is_publicly_visible': True,
                                    'scope': student.profile,
                                    'parent': student.profile})

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        student.user.key().name(),
        proposal.key().id())

    # test review GET
    url = '/gsoc/proposal/review/' + suffix
    response = self.client.get(url)
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/modules/gsoc/proposal/review.html')

  def testIgnoreProposalButton(self):
    student = GSoCProfileHelper(self.gsoc, self.dev_test)
    student.createOtherUser('student@example.com')
    student.createStudent()

    proposal = self.createProposal({'scope': student.profile,
                                    'parent': student.profile})

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        student.user.key().name(),
        proposal.key().id())

    self.data.createMentor(self.org)

    url = '/gsoc/proposal/ignore/' + suffix
    postdata = {'value': 'enable'}
    response = self.post(url, postdata)

    self.assertResponseForbidden(response)

    proposal = GSoCProposal.all().get()
    self.assertNotEqual(proposal.status, 'ignored')

  def testAcceptProposalButton(self):
    student = GSoCProfileHelper(self.gsoc, self.dev_test)
    student.createOtherUser('student@example.com')
    student.createStudent()

    proposal = self.createProposal({'scope': student.profile,
                                    'parent': student.profile})

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        student.user.key().name(),
        proposal.key().id())

    self.data.createMentor(self.org)

    url = '/gsoc/proposal/accept/' + suffix
    postdata = {'value': 'enable'}
    response = self.post(url, postdata)

    self.assertResponseForbidden(response)

    proposal = GSoCProposal.all().get()
    self.assertNotEqual(proposal.status, 'accepted')

  def testProposalModificationButton(self):
    student = GSoCProfileHelper(self.gsoc, self.dev_test)
    student.createOtherUser('student@example.com')
    student.createStudent()

    proposal = self.createProposal({'scope': student.profile,
                                    'parent': student.profile})

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        student.user.key().name(),
        proposal.key().id())

    self.data.createMentor(self.org)

    url = '/gsoc/proposal/modification/' + suffix
    postdata = {'value': 'enable'}
    response = self.post(url, postdata)

    self.assertResponseOK(response)

    proposal = GSoCProposal.all().get()
    self.assertTrue(proposal.is_editable_post_deadline)

  def testWishToMentorButton(self):
    student = GSoCProfileHelper(self.gsoc, self.dev_test)
    student.createOtherUser('student@example.com')
    student.createStudent()

    self.data.createMentor(self.org)

    other_mentor = self.createMentorWithSettings('other_mentor@example.com')

    proposal = self.createProposal({'scope': student.profile,
                                    'parent': student.profile})

    suffix = "%s/%s/%d" % (
    self.gsoc.key().name(),
    student.user.key().name(),
    proposal.key().id())

    url = '/gsoc/proposal/wish_to_mentor/' + suffix
    postdata = {'value': 'enable'}
    response = self.post(url, postdata)

    proposal = GSoCProposal.all().get()
    self.assertTrue(self.data.profile.key() in proposal.possible_mentors)

    postdata = {'value': 'disable'}
    response = self.post(url, postdata)

    proposal = GSoCProposal.all().get()
    self.assertFalse(self.data.profile.key() in proposal.possible_mentors)

    other_mentor.profile.mentor_for = []
    other_mentor.profile.put()

    proposal.possible_mentors.append(other_mentor.profile.key())
    proposal.put()

    url = '/gsoc/proposal/review/' + suffix
    response = self.client.get(url)

    proposal = GSoCProposal.all().get()
    self.assertFalse(other_mentor.profile.key() in proposal.possible_mentors)

  def testPubliclyVisibleButton(self):
    self.data.createStudent()

    proposal = self.createProposal({'scope': self.data.profile,
                                    'parent': self.data.profile})

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        self.data.user.key().name(),
        proposal.key().id())

    url = '/gsoc/proposal/publicly_visible/' + suffix
    postdata = {'value': 'enable'}
    response = self.post(url, postdata)

    self.assertResponseOK(response)

    proposal = GSoCProposal.all().get()
    self.assertTrue(proposal.is_publicly_visible)

  def testWithdrawProposalButton(self):
    self.data.createStudent()

    proposal = self.createProposal({'scope': self.data.profile,
                                    'parent': self.data.profile})

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        self.data.user.key().name(),
        proposal.key().id())

    url = '/gsoc/proposal/withdraw/' + suffix
    postdata = {'value': 'enable'}
    response = self.post(url, postdata)

    self.assertResponseOK(response)

    proposal = GSoCProposal.all().get()
    self.assertEqual(proposal.status, 'withdrawn')

    url = '/gsoc/proposal/withdraw/' + suffix
    postdata = {'value': 'enable'}
    response = self.post(url, postdata)

    self.assertResponseBadRequest(response)

    proposal = GSoCProposal.all().get()
    self.assertEqual(proposal.status, 'withdrawn')

    url = '/gsoc/proposal/withdraw/' + suffix
    postdata = {'value': 'disable'}
    response = self.post(url, postdata)

    self.assertResponseOK(response)

    proposal = GSoCProposal.all().get()
    self.assertEqual(proposal.status, 'pending')

