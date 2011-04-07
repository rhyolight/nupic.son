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

"""Tests for proposal view.
"""

__authors__ = [
  '"Sverre Rabbelier" <sverre@rabbelier.nl>',
  ]


import httplib

from tests.profile_utils import GSoCProfileHelper
from tests.test_utils import DjangoTestCase
from tests.test_utils import MailTestCase
from tests.timeline_utils import TimelineHelper

# TODO: perhaps we should move this out?
from soc.modules.gsoc.models.proposal import GSoCProposal
from soc.modules.seeder.logic.seeder import logic as seeder_logic


class ProposalTest(MailTestCase, DjangoTestCase):
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

  def assertReviewTemplateUsed(self, response):
    """Asserts that all the proposal review were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/modules/gsoc/proposal/review.html')
    self.assertTemplateUsed(response, 'v2/modules/gsoc/proposal/_comment_form.html')

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
    response = self.client.get(url)
    self.assertProposalTemplatesUsed(response)

    # test proposal POST
    override = {'program': self.gsoc, 'score': 0, 'mentor': None,
                'org': self.org, 'status': 'pending', 'accept_as_project': False}
    response, properties = self.modelPost(url, GSoCProposal, override)
    self.assertResponseRedirect(response)

    self.assertEmailSent(to=mentor.profile.email, n=1)
    self.assertEmailNotSent(to=other_mentor.profile.email)

    proposal = GSoCProposal.all().get()
    self.assertPropertiesEqual(properties, proposal)

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

    self.assertEmailSent(to=mentor.profile.email, n=2)
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

  def testSubmitProposalWhenInactive(self):
    """Test the submission of student proposals during the student signup
    period is not active.
    """
    self.data.createStudent()
    self.timeline.orgSignup()
    url = '/gsoc/proposal/submit/' + self.org.key().name()
    response = self.client.get(url)
    self.assertResponseForbidden(response)

    self.timeline.offSeason()
    url = '/gsoc/proposal/submit/' + self.org.key().name()
    response = self.client.get(url)
    self.assertResponseForbidden(response)

    self.timeline.kickoff()
    url = '/gsoc/proposal/submit/' + self.org.key().name()
    response = self.client.get(url)
    self.assertResponseForbidden(response)

    self.timeline.orgsAnnounced()
    url = '/gsoc/proposal/submit/' + self.org.key().name()
    response = self.client.get(url)
    self.assertResponseForbidden(response)

    self.timeline.studentsAnnounced()
    url = '/gsoc/proposal/submit/' + self.org.key().name()
    response = self.client.get(url)
    self.assertResponseForbidden(response)

  def testUpdateProposal(self):
    """Test update proposals.
    """
    mentor = GSoCProfileHelper(self.gsoc, self.dev_test)
    mentor.createOtherUser('mentor@example.com')
    mentor.createMentor(self.org)
    mentor.notificationSettings(proposal_updates=True)

    self.data.createStudentWithProposal(self.org, mentor.profile)
    self.data.notificationSettings()
    self.timeline.studentSignup()

    proposal = GSoCProposal.all().get()

    url = '/gsoc/proposal/update/%s/%s' % (
        self.gsoc.key().name(), proposal.key().id())
    response = self.client.get(url)
    self.assertProposalTemplatesUsed(response)

    override = {'program': self.gsoc, 'score': 0, 'mentor': mentor.profile,
                'org': self.org, 'status': 'pending', 'action': 'Update',
                'is_publicly_visible': False, 'accept_as_project': False,}
    response, properties = self.modelPost(url, GSoCProposal, override)
    self.assertResponseRedirect(response)

    properties.pop('action')

    proposal = GSoCProposal.all().get()
    self.assertPropertiesEqual(properties, proposal)

    # after update last_modified_on should be updated which is not equal
    # to created_on
    self.assertNotEqual(proposal.created_on, proposal.last_modified_on)

    self.assertEmailSent(to=mentor.profile.email, n=1)
