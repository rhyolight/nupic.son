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

"""Tests for dashboard view."""

import json

from tests import profile_utils
from tests.survey_utils import SurveyHelper
from tests.test_utils import GSoCDjangoTestCase
from tests.utils import project_utils
from tests.utils import proposal_utils


class DashboardTest(GSoCDjangoTestCase):
  """Tests dashboard page.
  """

  def setUp(self):
    self.init()

  def assertDashboardTemplatesUsed(self, response):
    """Asserts that all the templates from the dashboard were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/dashboard/base.html')

  def assertDashboardComponentTemplatesUsed(self, response):
    """Asserts that all the templates to render a component were used.
    """
    self.assertDashboardTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/dashboard/list_component.html')
    self.assertTemplateUsed(response, 'modules/gsoc/dashboard/component.html')
    self.assertTemplateUsed(response, 'soc/list/lists.html')
    self.assertTemplateUsed(response, 'soc/list/list.html')

  def testDasbhoardNoRole(self):
    url = '/gsoc/dashboard/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)
    self.assertResponseForbidden(response)

  def testDashboardAsLoneUser(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(self.program.key(), user=user)

    url = '/gsoc/dashboard/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertDashboardTemplatesUsed(response)

  def testDashboardAsStudent(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBStudent(self.program, user=user)

    url = '/gsoc/dashboard/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertDashboardComponentTemplatesUsed(response)
    response = self.getListResponse(url, 1)
    self.assertIsJsonResponse(response)

  def testDashboardAsStudentWithProposal(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile = profile_utils.seedNDBStudent(self.program, user=user)

    proposal_utils.seedProposal(profile.key, self.program.key())

    url = '/gsoc/dashboard/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertDashboardComponentTemplatesUsed(response)
    response = self.getListResponse(url, 1)
    self.assertIsJsonResponse(response)

  def testDashboardAsStudentWithProject(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile = profile_utils.seedNDBStudent(self.program, user=user)

    project_utils.seedProject(profile, self.program.key())

    url = '/gsoc/dashboard/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertDashboardComponentTemplatesUsed(response)
    response = self.getListResponse(url, 2)
    self.assertIsJsonResponse(response)

  def testDashboardAsStudentWithEval(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile = profile_utils.seedNDBStudent(self.program, user=user)

    project_utils.seedProject(profile, self.program.key())

    url = '/gsoc/dashboard/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertDashboardComponentTemplatesUsed(response)
    response = self.getListResponse(url, 3)
    self.assertResponseForbidden(response)

    response = self.get(url)
    self.assertResponseOK(response)
    self.assertDashboardComponentTemplatesUsed(response)
    self.evaluation = SurveyHelper(self.gsoc, self.dev_test)
    self.evaluation.createStudentEvaluation(override={'link_id': 'midterm'})
    response = self.getListResponse(url, 3)
    self.assertIsJsonResponse(response)
    data = json.loads(response.content)
    self.assertEqual(len(data['data']['']), 1)

    self.evaluation.createStudentEvaluation(override={'link_id': 'final'})
    response = self.getListResponse(url, 3)
    self.assertIsJsonResponse(response)
    data = json.loads(response.content)
    self.assertEqual(len(data['data']['']), 2)

  def testDashboardAsOrgAdmin(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[self.org.key])

    self.timeline_helper.studentsAnnounced()
    url = '/gsoc/dashboard/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertDashboardComponentTemplatesUsed(response)
    response = self.getListResponse(url, 5)
    self.assertIsJsonResponse(response)

  def testDashboardAsMentor(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, mentor_for=[self.org.key])

    self.timeline_helper.studentsAnnounced()
    url = '/gsoc/dashboard/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertDashboardComponentTemplatesUsed(response)
    response = self.getListResponse(url, 4)
    self.assertIsJsonResponse(response)

  def testDashboardAsMentorWithProject(self):
    self.timeline_helper.studentsAnnounced()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile = profile_utils.seedNDBProfile(
        self.program.key(), user=user, mentor_for=[self.org.key])

    student = profile_utils.seedSOCStudent(self.program)
    project_utils.seedProject(
        student, self.program.key(), org_key=self.org.key,
        mentor_key=profile.key)

    url = '/gsoc/dashboard/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertDashboardComponentTemplatesUsed(response)
    response = self.getListResponse(url, 4)
    self.assertIsJsonResponse(response)
