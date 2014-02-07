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

from soc.modules.gsoc.models import slot_transfer as slot_transfer_model
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from melange.models import organization as org_model

from tests import org_utils
from tests import profile_utils
from tests import test_utils


TEST_SLOT_COUNT = 3

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
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBStudent(self.program, user=user)

    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testMentorAccessForbidden(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, mentor_for=[self.org.key])

    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testOrgAdminAccessForbidden(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[self.org.key])

    response = self.get(self.url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testHostAccessGranted(self):
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    response = self.get(self.url)
    self.assertResponseOK(response)

  def testListData(self):
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    properties = {
        'program': self.gsoc,
        'nr_slots': 3,
        'remarks': 'Sample Remark',
        'status': 'pending',
    }

    # seed slot transfer entity for self.org
    properties['parent'] = self.org.key.to_old_key()
    seeder_logic.seed(slot_transfer_model.GSoCSlotTransfer, properties)

    other_org = org_utils.seedSOCOrganization(
        self.program.key(), status=org_model.Status.ACCEPTED)

    # seed slot transfer entity for other_org
    properties['parent'] = other_org.key.to_old_key()
    seeder_logic.seed(slot_transfer_model.GSoCSlotTransfer, properties)

    response = self.get(self.url)
    self.assertResponseOK(response)

    list_data = self.getListData(self.url, 0)
    self.assertEqual(len(list_data), 2)

  def testSlotsReturnedToOrg(self):
    """Tests that if an org admin rejects a slot transfer application that
    they had previously accepted, the slots are transferred back to the org.
    """
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    properties = {
        'program': self.gsoc,
        'nr_slots': TEST_SLOT_COUNT,
        'remarks': 'Sample Remark',
        'status': 'pending',
        'parent' : self.org.key.to_old_key()
    }
    slot_transfer = seeder_logic.seed(
        slot_transfer_model.GSoCSlotTransfer, properties)
    slot_transfer_key = slot_transfer.key()

    self.org.slot_allocation = TEST_SLOT_COUNT
    org_key = self.org.put()

    slot_transfer_id = slot_transfer_key.id()
    slot_json = '[{ "key": "%s", "full_transfer_key" : "%s" }]' % (
        str(slot_transfer_id) + org_key.id(), slot_transfer_key)
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
    self.assertEqual(0, org_key.get().slot_allocation)

    post_data['button_id'] = [u'reject']
    response = self.post(url, post_data)
    self.assertResponseOK(response)

    # Org's slots are replaced if the transfer is then rejected.
    slot_transfer = slot_transfer_model.GSoCSlotTransfer.get(
        slot_transfer_key)
    self.assertEqual(slot_transfer.status, 'rejected')
    self.assertEqual(TEST_SLOT_COUNT, org_key.get().slot_allocation)
