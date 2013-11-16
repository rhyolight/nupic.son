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
    self.profile_helper.createStudent()
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testMentorAccessForbidden(self):
    self.profile_helper.createMentor(self.org)
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testOrgAdminAccessForbidden(self):
    self.profile_helper.createOrgAdmin(self.org)
    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testHostAccessGranted(self):
    self.profile_helper.createHost()
    response = self.get(self.url)
    self.assertResponseOK(response)

  def testListData(self):
    self.profile_helper.createHost()

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
        'scope': self.gsoc,
        'program': self.gsoc,
        }
    other_org = seeder_logic.seed(org_model.GSoCOrganization, org_properties)

    # seed slot transfer entity for other_org
    properties['parent'] = other_org
    seeder_logic.seed(slot_transfer_model.GSoCSlotTransfer, properties)

    response = self.get(self.url)
    self.assertResponseOK(response)

    list_data = self.getListData(self.url, 0)
    self.assertEqual(len(list_data), 2)

  def testSlotsReturnedToOrg(self):
    """Tests that if an org admin rejects a slot transfer application that
    they had previously accepted, the slots are transferred back to the org.
    """
    test_slot_count = 3
    self.profile_helper.createHost()
    properties = {
        'program': self.gsoc,
        'nr_slots': test_slot_count,
        'remarks': 'Sample Remark',
        'status': 'pending',
        'parent' : self.org
    }
    slot_transfer = seeder_logic.seed(
        slot_transfer_model.GSoCSlotTransfer, properties)
    slot_transfer_key = slot_transfer.key()

    self.org.slots = test_slot_count
    org_key = self.org.put()

    slot_transfer_id = slot_transfer_key.id()
    slot_json = '[{ "key": "%s", "full_transfer_key" : "%s" }]' % (
        str(slot_transfer_id) + org_key.name(), slot_transfer_key)
    post_data = {
        'idx' : 0,
        'button_id' : [u'accept'],
        'data' : slot_json
        }
    url = '/gsoc/admin/slots/transfer/%s' % self.gsoc.key().name()
    response = self.post(url, post_data)
    self.assertResponseOK(response)

    # Org's slots are removed if the transfer is accepted.
    slot_transfer = slot_transfer_model.GSoCSlotTransfer.get(
        slot_transfer_key)
    self.assertEqual(slot_transfer.status, 'accepted')
    self.assertEqual(0, org_model.GSoCOrganization.get(org_key).slots)

    post_data['button_id'] = [u'reject']
    response = self.post(url, post_data)
    self.assertResponseOK(response)

    # Org's slots are replaced if the transfer is then rejected.
    slot_transfer = slot_transfer_model.GSoCSlotTransfer.get(
        slot_transfer_key)
    self.assertEqual(slot_transfer.status, 'rejected')
    self.assertEqual(
        test_slot_count, org_model.GSoCOrganization.get(org_key).slots)

