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

import unittest

from tests import profile_utils
from tests.profile_utils import GSoCProfileHelper
from tests.test_utils import GSoCDjangoTestCase


class HomepageViewTest(GSoCDjangoTestCase):
  """Tests program homepage views.
  """

  def setUp(self):
    self.init()

  def assertHomepageTemplatesUsed(self, response):
    """Asserts that all the templates from the homepage view were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/_connect_with_us.html')
    self.assertTemplateUsed(response, 'modules/gsoc/homepage/base.html')
    self.assertTemplateUsed(response, 'modules/gsoc/homepage/_apply.html')
    self.assertTemplateUsed(response, 'modules/gsoc/homepage/_timeline.html')

  def testHomepageAnonymous(self):
    """Tests the homepage as an anonymous user throughout the program.
    """
    url = '/gsoc/homepage/' + self.gsoc.key().name()

    self.timeline_helper.offSeason()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertHomepageTemplatesUsed(response)

    self.timeline_helper.kickoff()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertHomepageTemplatesUsed(response)

    self.timeline_helper.orgSignup()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertHomepageTemplatesUsed(response)

    self.timeline_helper.orgsAnnounced()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertHomepageTemplatesUsed(response)

    self.timeline_helper.studentSignup()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertHomepageTemplatesUsed(response)

    self.timeline_helper.studentsAnnounced()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertHomepageTemplatesUsed(response)

  @unittest.skip('timeline widget is currently disabled')
  def testHomepageDuringSignup(self):
    """Tests the student homepage during the signup period.
    """
    self.timeline_helper.studentsAnnounced()
    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertHomepageTemplatesUsed(response)
    timeline_tmpl = response.context['timeline']
    apply_context = response.context['apply'].context()
    self.assertEqual(timeline_tmpl.current_timeline, 'coding_period')
    self.assertIn('profile_link', apply_context)

    # Show featured_project
    student = profile_utils.seedGSoCStudent(self.program)

    mentor = GSoCProfileHelper(self.gsoc, self.dev_test)
    mentor.createOtherUser('mentor@example.com')
    mentor.createMentorWithProject(self.org, student)

    from soc.modules.gsoc.models.project import GSoCProject
    project = GSoCProject.all().ancestor(student).get()
    project.is_featured = True
    project.put()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertHomepageTemplatesUsed(response)
    self.assertTemplateUsed(
        response, 'modules/gsoc/homepage/_featured_project.html')

    featured_project_tmpl = response.context['featured_project']
    self.assertEqual(featured_project_tmpl.featured_project.key(),
                     project.key())

  @unittest.skip('timeline widget is currently disabled')
  def testHomepageAfterStudentsAnnounced(self):
    """Tests the student homepage after the student's have been announced.
    """
    self.timeline_helper.studentsAnnounced()
    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertHomepageTemplatesUsed(response)
    timeline_tmpl = response.context['timeline']
    apply_context = response.context['apply'].context()
    self.assertEqual(timeline_tmpl.current_timeline, 'coding_period')
    self.assertIn('profile_link', apply_context)

  def testHomepageDuringSignupExistingUser(self):
    """Tests the student hompepage during the signup period with an existing user.
    """
    self.profile_helper.createProfile()
    self.timeline_helper.studentSignup()
    url = '/gsoc/homepage/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertHomepageTemplatesUsed(response)
    apply_tmpl = response.context['apply']
    self.assertTrue(apply_tmpl.data.profile)
    self.assertNotIn('profile_link', apply_tmpl.context())
