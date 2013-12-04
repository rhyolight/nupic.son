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

"""Tests for slot allocation view."""

import json

from melange.models import organization as org_model

from tests import profile_utils
from tests.test_utils import GSoCDjangoTestCase


class SlotsTest(GSoCDjangoTestCase):
  """Tests slots page.
  """

  def setUp(self):
    self.init()
    self.org.status = org_model.Status.ACCEPTED
    self.org.put()

  def assertProjectTemplatesUsed(self, response):
    """Asserts that all the templates from the dashboard were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/admin/list.html')
    self.assertTemplateUsed(response,
        'modules/gsoc/admin/_accepted_orgs_list.html')

  def testAllocateSlots(self):
    user = profile_utils.seedUser(host_for=[self.sponsor.key()])
    profile_utils.login(user)

    url = '/gsoc/admin/slots/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertProjectTemplatesUsed(response)

    data = self.getListData(url, 0)
    self.assertEqual(1, len(data))

    org_data = {
        'slot_allocation': '20',
        # TOOD(daniel): add note to organization model?
        #'note':'Great org',
    }
    org_id = self.org.key.id()

    data = json.dumps({org_id: org_data})

    postdata = {
        'data': data,
        'button_id': 'save',
        'idx': 0,
    }
    response = self.post(url, postdata)
    self.assertResponseOK(response)

    org_data['slot_allocation'] = 20

    self.assertPropertiesEqual(org_data, self.org.key.get())

  def testColumnWithZero(self):
    """Tests that a lambda function returning a value that Python considers
    to be False will not result in an empty column value.
    """
    self.org.slot_allocation = 0
    self.org.put()
    self.profile_helper.createHost()

    url = '/gsoc/admin/slots/' + self.gsoc.key().name()
    response = self.getListData(url, 0)
    self.assertEquals(response[0]['columns']['slot_allocation'], 0)
