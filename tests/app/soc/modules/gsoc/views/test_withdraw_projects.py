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

"""Tests for withdraw projects view."""

import json

from google.appengine.ext import db

from soc.modules.gsoc.models import project as project_model
from soc.modules.gsoc.models import proposal as proposal_model

from tests import profile_utils
from tests.test_utils import GSoCDjangoTestCase
from tests.utils import project_utils


class WithdrawProjectsTest(GSoCDjangoTestCase):
  """Test withdraw projects page
  """

  def setUp(self):
    self.init()

  def assertWithdrawProjects(self, response):
    """Asserts that all templates from the withdraw projects page were used
    and all contexts were passed
    """
    self.assertIn('base_layout', response.context)
    self.assertGSoCTemplatesUsed(response)
    self.assertEqual(response.context['base_layout'],
        'modules/gsoc/base.html')

    self.assertTemplateUsed(response,
        'modules/gsoc/accept_withdraw_projects/base.html')
    self.assertTemplateUsed(response,
        'modules/gsoc/accept_withdraw_projects/base.html')

  def testWithdrawProjects(self):
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    self.timeline_helper.studentsAnnounced()

    url = '/gsoc/withdraw_projects/' + self.program.key().name()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertWithdrawProjects(response)

    # list response without any projects
    response = self.getListResponse(url, 0)
    self.assertIsJsonResponse(response)
    data = response.context['data']['']
    self.assertEqual(0, len(data))

    # list response with projects
    student = profile_utils.seedNDBStudent(self.program)
    project_utils.seedProject(student, self.program.key(), org_key=self.org.key)

    response = self.getListResponse(url, 0)
    self.assertIsJsonResponse(response)
    data = response.context['data']['']
    self.assertEqual(1, len(data))

  def testWithdrawProject(self):
    """Test if withdrawing a project updates all the datastore properties."""
    self.timeline_helper.studentsAnnounced()

    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    student = profile_utils.seedNDBStudent(self.program)
    project = project_utils.seedProject(
        student, self.program.key(), org_key=self.org.key)

    old_number_of_projects = student.key.get().student_data.number_of_projects
    old_project_for_orgs = student.key.get().student_data.project_for_orgs[:]

    data_payload = [{
        'full_project_key': str(project.key()),
        }
    ]

    json_data = json.dumps(data_payload)

    postdata = {
        'data': json_data,
        'button_id': 'withdraw'
        }

    list_idx = 0
    url = '/gsoc/withdraw_projects/%s?fmt=json&marker=1&&idx=%s' % (
        self.program.key().name(), str(list_idx))

    response = self.post(url, postdata)
    self.assertResponseOK(response)

    student = student.key.get()
    project = db.get(project.key())

    proposal = project.proposal

    self.assertEqual(project.status, 'withdrawn')
    self.assertEqual(proposal.status, 'withdrawn')

    self.assertEqual(
        student.student_data.number_of_projects,
        old_number_of_projects - 1)

    old_project_for_orgs.remove(self.org.key)
    self.assertEqual(
        list(student.student_data.project_for_orgs), old_project_for_orgs)
