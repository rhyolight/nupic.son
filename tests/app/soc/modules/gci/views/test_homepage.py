#!/usr/bin/env python2.5
#
# Copyright 2010 the Melange authors.
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


"""Tests for program homepage related views.
"""

__authors__ = [
  '"Sverre Rabbelier" <sverre@rabbelier.nl>',
  ]


from tests.test_utils import GCIDjangoTestCase

# TODO: perhaps we should move this out?
from soc.modules.seeder.logic.seeder import logic as seeder_logic


class HomepageViewTest(GCIDjangoTestCase):
  """Tests program homepage views.
  """

  def setUp(self):
    self.init()

  def assertHomepageTemplatesUsed(self, response):
    """Asserts that all the templates from the homepage view were used.
    """
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/modules/gci/homepage/base.html')
    # not always
    # self.assertTemplateUsed(response, 'v2/modules/gci/homepage/_featured_task.html')
    self.assertTemplateUsed(response, 'v2/modules/gci/homepage/_participating_orgs.html')
    self.assertTemplateUsed(response, 'v2/modules/gci/homepage/_connect_with_us.html')
    self.assertTemplateUsed(response, 'v2/modules/gci/homepage/_how_it_works.html')
    # not always
    # self.assertTemplateUsed(response, 'v2/modules/gci/homepage/_timeline.html')

  def testHomepageAnonymous(self):
    """Tests the homepage as an anonymous user throughout the program.
    """
    url = '/gci/homepage/' + self.gci.key().name()

    self.timeline.offSeason()
    response = self.client.get(url)
    self.assertHomepageTemplatesUsed(response)

    self.timeline.kickoff()
    response = self.client.get(url)
    self.assertHomepageTemplatesUsed(response)

    self.timeline.orgSignup()
    response = self.client.get(url)
    self.assertHomepageTemplatesUsed(response)

    self.timeline.orgsAnnounced()
    response = self.client.get(url)
    self.assertHomepageTemplatesUsed(response)

    self.timeline.studentSignup()
    response = self.client.get(url)
    self.assertHomepageTemplatesUsed(response)

    self.timeline.tasksPubliclyVisible()
    response = self.client.get(url)
    self.assertHomepageTemplatesUsed(response)

    self.timeline.taskClaimEnded()
    response = self.client.get(url)
    self.assertHomepageTemplatesUsed(response)

    self.timeline.pencilDown()
    response = self.client.get(url)
    self.assertHomepageTemplatesUsed(response)

  def testHomepageDuringSignup(self):
    """Tests the student homepage during the signup period.
    """
    self.timeline.studentSignup()
    url = '/gci/homepage/' + self.gci.key().name()
    response = self.client.get(url)
    self.assertHomepageTemplatesUsed(response)
    # TOOD
    #timeline_tmpl = response.context['timeline']
    #apply_context = response.context['apply'].context()
    #self.assertEqual(timeline_tmpl.current_timeline, 'student_signup_period')
    #self.assertTrue('profile_link' in apply_context)

  def testHomepageDuringSignupExistingUser(self):
    """Tests the student hompepage during the signup period with an existing user.
    """
    self.data.createProfile()
    self.timeline.studentSignup()
    url = '/gci/homepage/' + self.gci.key().name()
    response = self.client.get(url)
    self.assertHomepageTemplatesUsed(response)
    # TOOD
    #apply_tmpl = response.context['apply']
    #self.assertTrue(apply_tmpl.data.profile)
    #self.assertFalse('profile_link' in apply_tmpl.context())