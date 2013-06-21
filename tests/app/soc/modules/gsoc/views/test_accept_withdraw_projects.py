# Copyright 2013 the Melange authors.
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

"""Unit tests for manage projects related views."""

import json

from soc.modules.gsoc.models import profile as profile_model
from soc.modules.gsoc.models import project as project_model
from soc.modules.gsoc.models import proposal as proposal_model
from soc.modules.gsoc.views import accept_withdraw_projects

from tests import profile_utils
from tests import test_utils


class AcceptProposalsTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for AcceptProposals view."""

  def setUp(self):
    self.init()
    self.url = '/gsoc/admin/proposals/accept/%s' % self.gsoc.key().name()

  def _assertTemplatesUsed(self, response):
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response,
        'modules/gsoc/accept_withdraw_projects/_project_list.html')
    self.assertTemplateUsed(response,
        'modules/gsoc/accept_withdraw_projects/base.html')
    self.assertTemplateUsed(response, 'soc/_program_select.html')
    self.assertTemplateUsed(response, 'soc/list/lists.html')
    self.assertTemplateUsed(response, 'soc/list/list.html')

  def testLoneUserAccessForbidded(self):
    """Tests that a lone user cannot access the page."""
    self.data.createUser()
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testStudentAccessForbidded(self):
    """Tests that a student cannot access the page."""
    self.data.createStudent()
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testMentorAccessForbidded(self):
    """Tests that a mentor cannot access the page."""
    self.data.createMentor(self.org)
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testOrgAdminAccessForbidded(self):
    """Tests that an organization admin cannot access the page."""
    self.data.createOrgAdmin(self.org)
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testHostAccessGranted(self):
    """Tests that a program admin can access the page."""
    self.data.createHost()
    response = self.get(self.url)
    self.assertResponseOK(response)
    self._assertTemplatesUsed(response)

  def testAcceptProposal(self):
    """Tests that a proposal is correctly accepted."""
    self.data.createHost()

    mentor = profile_utils.GSoCProfileHelper(
        self.gsoc, False).createMentor(self.org)
    student = profile_utils.GSoCProfileHelper(
        self.gsoc, False).createStudentWithProposal(self.org, mentor)
    proposal = proposal_model.GSoCProposal.all().ancestor(student).get()

    list_data = [{
        accept_withdraw_projects._PROPOSAL_KEY: str(proposal.key())
        }]
    post_data = {
        'button_id': 'accept',
        'data': json.dumps(list_data),
        'idx': 0,
        }
    self.post(self.url, post_data)

    # check if proposal is accepted correctly
    proposal = proposal_model.GSoCProposal.get(proposal.key())
    self.assertEqual(proposal.status, proposal_model.STATUS_ACCEPTED)

    # check if a project is created
    project = project_model.GSoCProject.all().ancestor(student).get()
    self.assertEqual(project.status, project_model.STATUS_ACCEPTED)
    self.assertEqual(project.proposal.key(), proposal.key())

    # check if number of projects is updated
    student_info = profile_model.GSoCStudentInfo.all().ancestor(student).get()
    self.assertEqual(student_info.number_of_projects, 1)

  def testAcceptTwoProposals(self):
    """Tests that two proposals can be accepted in the same request."""

    self.data.createHost()

    mentor = profile_utils.GSoCProfileHelper(
        self.gsoc, False).createMentor(self.org)
    student1 = profile_utils.GSoCProfileHelper(
        self.gsoc, False).createStudentWithProposal(self.org, mentor)
    student2 = profile_utils.GSoCProfileHelper(
        self.gsoc, False).createStudentWithProposal(self.org, mentor)

    proposal1 = proposal_model.GSoCProposal.all().ancestor(student1).get()
    proposal2 = proposal_model.GSoCProposal.all().ancestor(student2).get()

    list_data = [
        {accept_withdraw_projects._PROPOSAL_KEY: str(proposal1.key())},
        {accept_withdraw_projects._PROPOSAL_KEY: str(proposal2.key())}
        ]

    post_data = {
        'button_id': 'accept',
        'data': json.dumps(list_data),
        'idx': 0,
        }
    self.post(self.url, post_data)

    # check if both proposals are accepted correctly
    proposal1 = proposal_model.GSoCProposal.get(proposal1.key())
    self.assertEqual(proposal1.status, proposal_model.STATUS_ACCEPTED)

    proposal2 = proposal_model.GSoCProposal.get(proposal2.key())
    self.assertEqual(proposal2.status, proposal_model.STATUS_ACCEPTED)
