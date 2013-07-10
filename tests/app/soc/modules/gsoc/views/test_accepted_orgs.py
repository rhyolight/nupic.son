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

"""Tests the view for GSoC accepted organizations."""

from soc.modules.gsoc.models import organization as org_model
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests import test_utils


class AcceptedOrgsPublicPageTest(test_utils.GSoCDjangoTestCase):
  """Tests the page to display accepted organization."""

  def setUp(self):
    self.init()
    self.url1 = '/gsoc/accepted_orgs/' + self.gsoc.key().name()
    self.url2 = '/gsoc/program/accepted_orgs/' + self.gsoc.key().name()
    self.url3 = '/program/accepted_orgs/' + self.gsoc.key().name()

  def assertAcceptedOrgsPageTemplatesUsed(self, response):
    """Asserts that all the required templates to render the page were used."""
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response,
        'modules/gsoc/accepted_orgs/base.html')
    self.assertTemplateUsed(response,
        'modules/gsoc/admin/_accepted_orgs_list.html')
    self.assertTemplateUsed(response, 'soc/_program_select.html')
    self.assertTemplateUsed(response, 'soc/list/lists.html')
    self.assertTemplateUsed(response, 'soc/list/list.html')

  def testPageForbiddenBeforeOrgsAnnounced(self):
    self.timeline_helper.kickoff()
    response = self.get(self.url3)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

    response = self.get(self.url2)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

    response = self.get(self.url1)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

    self.timeline_helper.orgSignup()
    response = self.get(self.url3)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

    response = self.get(self.url2)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

    response = self.get(self.url1)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testPageAllowedAfterOrgsAnnounced(self):
    # a list functions which change the timeline properties
    period_setters = [
        self.timeline_helper.orgsAnnounced,
        self.timeline_helper.studentSignup,
        self.timeline_helper.postStudentSignup,
        self.timeline_helper.studentsAnnounced,
        self.timeline_helper.formSubmission
        ]

    for period_setter in period_setters:
      # set the environment as defined by the current function
      period_setter()

      response = self.get(self.url3)
      self.assertResponseOK(response)
      self.assertAcceptedOrgsPageTemplatesUsed(response)

      response = self.get(self.url2)
      self.assertResponseOK(response)
      self.assertAcceptedOrgsPageTemplatesUsed(response)

      response = self.get(self.url3)
      self.assertResponseOK(response)
      self.assertAcceptedOrgsPageTemplatesUsed(response)

  def testAcceptedOrgList(self):
    self.timeline_helper.orgsAnnounced()

    org_properties = {
        'scope': self.gsoc,
        'status': 'active'
    }
    seeder_logic.seed(org_model.GSoCOrganization, org_properties)
    seeder_logic.seed(org_model.GSoCOrganization, org_properties)

    list_data = self.getListData(self.url1, 0)
    #Third organization is self.gsoc
    self.assertEqual(len(list_data), 3)


class AcceptedOrgsAdminPageTest(test_utils.GSoCDjangoTestCase):
  """Tests the page to display accepted organizations for admins."""

  def setUp(self):
    self.init()
    self.url = '/gsoc/admin/accepted_orgs/' + self.gsoc.key().name()

  def assertAcceptedOrgsPageTemplatesUsed(self, response):
    """Asserts that all the required templates to render the page were used."""
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response,
        'modules/gsoc/admin/list.html')
    self.assertTemplateUsed(response,
        'modules/gsoc/admin/_accepted_orgs_list.html')
    self.assertTemplateUsed(response, 'soc/list/lists.html')
    self.assertTemplateUsed(response, 'soc/list/list.html')

  def testPageForbiddenForLoneUsers(self):
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testPageForbiddenForStudents(self):
    self.profile_helper.createStudent()
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testPageForbiddenForMentors(self):
    self.profile_helper.createMentor(self.org)
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testPageForbiddenForOrgAdmins(self):
    self.profile_helper.createOrgAdmin(self.org)
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testPageAccessibleForHosts(self):
    self.profile_helper.createHost()
    response = self.get(self.url)
    self.assertResponseOK(response)
    self.assertAcceptedOrgsPageTemplatesUsed(response)
