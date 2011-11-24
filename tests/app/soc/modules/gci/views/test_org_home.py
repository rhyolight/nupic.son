#!/usr/bin/env python2.5
#
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


"""Tests the view for GCI org homepage.
"""


from soc.modules.gci.models.organization import GCIOrganization
from soc.modules.gci.models.task import GCITask

from tests.test_utils import GCIDjangoTestCase

from soc.modules.seeder.logic.seeder import logic as seeder_logic

class OrgHomeTest(GCIDjangoTestCase):
  """Tests the GCI org homepage.
  """
  
  def setUp(self):
    self.init()
    self.url = '/gci/org/' + self.org.key().name()
    
  def assertTemplatesUsed(self, response):
    """Asserts if all the templates required to correctly render the page
    were used.
    """
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/modules/gci/org_home/base.html')
    self.assertTemplateUsed(
        response, 'v2/modules/gci/org_home/_open_tasks.html')
    self.assertTemplateUsed(
        response, "v2/modules/gci/org_home/_contact_us.html")
    self.assertTemplateUsed(response, 'v2/modules/gci/org_home/_about_us.html')
    self.assertTemplateUsed(response, 'v2/soc/list/lists.html')
    self.assertTemplateUsed(response, 'v2/soc/list/list.html')
    

  def testOpenTasksList(self):
    """Tests if the list of open tasks is rendered.
    """
    task_prop = {'status': 'Open', 'program': self.gci, 'org': self.org}
    seeder_logic.seed(GCITask, task_prop)
    seeder_logic.seed(GCITask, task_prop)
    response = self.get(self.url)
    self.assertResponseOK(response)
    self.assertTemplatesUsed(response)
    #list = self.getListResponse(self.url, idx=0)
    #print list
    list_data = self.getListData(self.url, 0)
    self.assertEqual(len(list_data), 2)