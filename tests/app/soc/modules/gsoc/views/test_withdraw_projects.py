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

    url = '/gsoc/withdraw_projects/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertWithdrawProjects(response)

    # list response without any projects
    response = self.getListResponse(url, 0)
    self.assertIsJsonResponse(response)
    data = response.context['data']['']
    self.assertEqual(0, len(data))

    # list response with projects
    mentor = profile_utils.seedGSoCProfile(
        self.program, mentor_for=[self.org.key.to_old_key()])
    self.profile_helper.createStudentWithProposal(self.org, mentor)
    self.profile_helper.createStudentWithProject(self.org, mentor)

    response = self.getListResponse(url, 0)
    self.assertIsJsonResponse(response)
    data = response.context['data']['']
    self.assertEqual(1, len(data))

  def testWithdrawProject(self):
    """Test if withdrawing a project updates all the datastore properties."""
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    self.timeline_helper.studentsAnnounced()

    # list response with projects
    mentor = profile_utils.seedGSoCProfile(
        self.program, mentor_for=[self.org.key.to_old_key()])
    self.profile_helper.createStudentWithProposal(self.org, mentor)
    student = self.profile_helper.createStudentWithProject(self.org, mentor)
    student_key = student.key()
    orig_number_of_projects = student.student_info.number_of_projects
    orig_project_for_orgs = student.student_info.project_for_orgs

    project_q = project_model.GSoCProject.all().ancestor(student)
    project = project_q.get()

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
        self.gsoc.key().name(), str(list_idx))

    response = self.post(url, postdata)
    self.assertResponseOK(response)

    student = db.get(student_key)
    project_q = project_model.GSoCProject.all().ancestor(student)
    project = project_q.get()

    proposal_q = proposal_model.GSoCProposal.all().ancestor(student)
    proposal = proposal_q.get()

    self.assertEqual(project.status, 'withdrawn')
    self.assertEqual(proposal.status, 'withdrawn')

    self.assertEqual(student.student_info.number_of_projects,
                     orig_number_of_projects - 1)

    orig_project_for_orgs.remove(self.org.key.to_old_key())
    self.assertEqual(list(student.student_info.project_for_orgs),
                     orig_project_for_orgs)
