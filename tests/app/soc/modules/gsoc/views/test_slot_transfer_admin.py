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

"""Unit tests for slot transfer admin view."""

from soc.modules.gsoc.models import organization as org_model
from soc.modules.gsoc.models import slot_transfer as slot_transfer_model
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests import profile_utils
from tests import test_utils


class SlotsTransferAdminPageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for SlotsTransferAdminPage class."""

  def setUp(self):
    self.init()
    self.url = '/gsoc/admin/slots/transfer/%s' % self.gsoc.key().name()

  def testLoneUserAccessForbidden(self):
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testStudentAccessForbidden(self):
    self.data.createStudent()
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testMentorAccessForbidden(self):
    self.data.createMentor(self.org)
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testOrgAdminAccessForbidden(self):
    self.data.createOrgAdmin(self.org)
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testHostAccessGranted(self):
    self.data.createHost()
    response = self.get(self.url)
    self.assertResponseOK(response)

  def testListData(self):
    self.data.createHost()

    properties = {
        'program': self.gsoc,
        'nr_slots': 3,
        'remarks': 'Sample Remark',
        'status': 'pending',
    }

    # seed slot transfer entity for self.org
    properties['parent'] = self.org
    seeder_logic.seed(slot_transfer_model.GSoCSlotTransfer, properties)

    org_properties = {
        'status': 'active',
        'scope': self.gsoc
        }
    other_org = seeder_logic.seed(org_model.GSoCOrganization, org_properties)

    # seed slot transfer entity for other_org
    properties['parent'] = other_org
    seeder_logic.seed(slot_transfer_model.GSoCSlotTransfer, properties)

    response = self.get(self.url)
    self.assertResponseOK(response)

    list_data = self.getListData(self.url, 0)
    self.assertEqual(len(list_data), 2)
