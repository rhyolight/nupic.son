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

"""Tests for readonly module."""

import unittest

from codein.templates import readonly


class ReadOnlyTemplateTest(unittest.TestCase):
  """Unit tests for ReadOnlyTemplate class."""

  def testContext(self):
    """Tests that returned context is correct."""
    template = readonly.ReadOnlyTemplate(None)

    # check for empty items
    context = template.context()
    self.assertDictEqual(context['items'], {})

    # add a few items
    items = [('a', '1'), ('b', '2'), ('c', '3')]
    for item in items:
      template.addItem(item[0], item[1])

    # check both content and order
    context = template.context()
    self.assertListEqual(context['items'].items(), items)

  def testAddItem(self):
    """Tests that items are added correctly."""
    template = readonly.ReadOnlyTemplate(None)

    # add a few items
    items = [('a', '1'), ('b', '2'), ('c', '3')]
    for item in items:
      template.addItem(item[0], item[1])

    # test that items are added
    for item in items:
      self.assertIn(item, template._items.items())

    # test that another item is not added
    self.assertNotIn(('d', '4'), template._items.items())
