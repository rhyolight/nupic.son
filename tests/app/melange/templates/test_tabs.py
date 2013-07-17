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

"""Tests for tabs module."""

import unittest

from melange.templates import tabs


class MockRequestData(object):
  """Mock implementation of RequestData."""
  pass


TEST_TAB_ID_FMT = 'test_tab_id_%i'
TEST_TAB_NAME_FMT = 'Test Name %i'
TEST_TAB_URL_FMT = 'http://www.test%i.com'

SELECTED_TAB_INDEX = 3
NUMBER_OF_TABS = 5

TEMPLATE_PATH = '/some/test/path'


class TabsTest(unittest.TestCase):
  """Unit tests for Tabs class."""

  def setUp(self):
    self.tabs_list = []
    for i in range(NUMBER_OF_TABS):
      tab_id = TEST_TAB_ID_FMT % i
      name = TEST_TAB_NAME_FMT % i
      url = TEST_TAB_URL_FMT % i
      self.tabs_list.append(tabs.Tab(tab_id, name, url))

    self.selected_tab_id = TEST_TAB_ID_FMT % SELECTED_TAB_INDEX

    self.tabs = tabs.Tabs(MockRequestData(), TEMPLATE_PATH, self.tabs_list,
        self.selected_tab_id)

  def testFieldInitialization(self):
    """Tests that correct values of properties are returned."""
    self.assertListEqual(self.tabs.tabs, self.tabs_list)
    self.assertEqual(self.tabs.selected_tab_id, self.selected_tab_id)
    self.assertEqual(self.tabs.templatePath(), TEMPLATE_PATH)

  def testContext(self):
    """Tests that correct context is returned."""
    self.assertDictEqual(self.tabs.context(), {'tabs': self.tabs})
    
