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

"""Tests functions in soc.logic.cached_list module."""

import unittest

from melange.models import cached_list as cached_list_model
from melange.logic import cached_list as cached_list_logic

from soc.modules.seeder.logic.seeder import logic as seeder_logic


class TestCacheItems(unittest.TestCase):
  """Test cacheItems function."""

  def testAddingNewCachedList(self):
    cached_list_logic.cacheItems('foo_list', [{'foo': 'bar'}, {'baz': 'qux'}])
    cached_list = cached_list_model.CachedList.query().get()
    self.assertIsNotNone(cached_list)

  def testAddingNewItems(self):
    new_item1 = {'name': 'foo'}
    new_item2 = {'name': 'bar'}
    new_item3 = {'name': 'baz'}
    cached_list_logic.cacheItems('foo_list', [new_item1, new_item2, new_item3])
    cached_list = cached_list_model.CachedList.query().get()
    self.assertIn(new_item1, cached_list.list_data)
    self.assertIn(new_item2, cached_list.list_data)


class TestGetCachedItems(unittest.TestCase):
  """Tests getCachedItems function."""

  def setUp(self):
    self.item1 = {'name': 'foo'}
    self.item2 = {'name': 'bar'}
    self.item3 = {'name': 'baz'}
    self.item4 = {'name': 'qux'}
    self.item5 = {'name': 'quux'}
    cached_list_properties = {
        'id': 'test_list',
        'list_data':
            [self.item1, self.item2, self.item3, self.item4, self.item5]
        }
    seeder_logic.seed(cached_list_model.CachedList, cached_list_properties)

  def testRetrievingCachedItems(self):
    cached_items = cached_list_logic.getCachedItems('test_list', 0, 5)
    self.assertSequenceEqual(
        [self.item1, self.item2, self.item3, self.item4, self.item5],
        cached_items)

  def testRetrievingPartOfCachedItems(self):
    cached_items = cached_list_logic.getCachedItems('test_list', 1, 3)
    self.assertSequenceEqual([self.item2, self.item3, self.item4], cached_items)

  def testRetrievingWithOverSpecifiedLimit(self):
    cached_items = cached_list_logic.getCachedItems('test_list', 2, 100)
    self.assertSequenceEqual([self.item3, self.item4, self.item5], cached_items)

  def testRetrievingWithOverSpecifiedStart(self):
    cached_items = cached_list_logic.getCachedItems('test_list', 100, 3)
    self.assertEqual(0, len(cached_items))

  def testRetrievingWithoutSpecifyingStart(self):
    """Test whether 0 is taken as the starting index."""
    cached_items = cached_list_logic.getCachedItems('test_list', limit=3)
    self.assertListEqual([self.item1, self.item2, self.item3], cached_items)

  def testRetrievingWithoutSpecifyingLimit(self):
    """Test whether all the items from the starting index is returned."""
    cached_items = cached_list_logic.getCachedItems('test_list', start=2)
    self.assertListEqual([self.item3, self.item4, self.item5], cached_items)

  def testErrorForNonExsistentList(self):
    with self.assertRaises(ValueError):
      cached_list_logic.getCachedItems('none_existent', 0, 1)


class TestIsCachedListExists(unittest.TestCase):
  """Unit tests for isCachedListExists function."""

  def setUp(self):
    seeder_logic.seed(cached_list_model.CachedList, {'id': 'cached_list'})

  def testForExistence(self):
    """Test whether True is returned only when the list exists."""
    self.assertTrue(cached_list_logic.isCachedListExists('cached_list'))
    self.assertFalse(cached_list_logic.isCachedListExists('none_existent'))
