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

"""Tests for slots view.
"""

__authors__ = [
  '"Sverre Rabbelier" <sverre@rabbelier.nl>',
  ]


import httplib

from tests.profile_utils import GSoCProfileHelper
from tests.test_utils import DjangoTestCase
from tests.timeline_utils import TimelineHelper


class SlotsTest(DjangoTestCase):
  """Tests slots page.
  """

  def setUp(self):
    self.init()

  def assertProjectTemplatesUsed(self, response):
    """Asserts that all the templates from the dashboard were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/modules/gsoc/admin/slots.html')
    self.assertTemplateUsed(response, 'v2/modules/gsoc/admin/_slots_list.html')

  def testListProjects(self):
    self.data.createHost()
    url = '/gsoc/admin/slots/' + self.gsoc.key().name()
    response = self.client.get(url)
    self.assertProjectTemplatesUsed(response)

    data = self.getListData(url, 0)
    self.assertEqual(1, len(data))
