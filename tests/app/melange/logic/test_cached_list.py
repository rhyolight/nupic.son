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

import datetime
import unittest

from melange import key_column_id_const
from melange.logic import cached_list as cached_list_logic
from melange.models import cached_list as cached_list_model

from soc.modules.seeder.logic.seeder import logic as seeder_logic

KEY = key_column_id_const.KEY_COLUMN_ID


class TestCacheItems(unittest.TestCase):
  """Test cacheItems function."""

  def testAddingNewCachedList(self):
    cached_list_logic.setCacheItems(
        'foo_list', [{KEY: 'one', 'foo': 'bar'}, {KEY: 'two', 'baz': 'qux'}])
    cached_list = cached_list_model.CachedList.query().get()
    self.assertIsNotNone(cached_list)

  def testAddingNewItems(self):
    new_item1 = {KEY: 'one', 'name': 'foo'}
    new_item2 = {KEY: 'two', 'name': 'bar'}
    new_item3 = {KEY: 'three', 'name': 'baz'}
    cached_list_logic.setCacheItems(
        'foo_list', [new_item1, new_item2, new_item3])
    cached_list = cached_list_model.CachedList.query().get()
    self.assertIn(new_item1, cached_list.list_data)
    self.assertIn(new_item2, cached_list.list_data)

  def testUpdatingAfterCaching(self):
    """Tests whether cached list state is updated."""
    valid_period = datetime.timedelta(2, 4, 6)
    cached_list_logic.setCacheItems(
        'test_list', [{KEY: 'foo'}, {KEY: 'bar'}], valid_period)
    cached_list = cached_list_model.CachedList.get_by_id('test_list')

    self.assertAlmostEqual(cached_list.valid_through,
                           datetime.datetime.now() + valid_period,
                           delta=datetime.timedelta(seconds=5))

    self.assertFalse(cached_list.is_processing)

  def testRemovingDuplicates(self):
    """Tests whether the duplicate list items are removed upon saving."""

    item1 = {KEY: 'one', 'name': 'foo'}
    item2 = {KEY: 'two', 'name': 'bar'}
    item3 = {KEY: 'three', 'name': 'baz'}
    dup_item1 = {KEY: 'one', 'name': 'foo'}
    dup_item2 = {KEY: 'two', 'name': 'qux'}

    list_with_duplicates = [item1, item2, item3, dup_item1, dup_item2]
    # duplicate items should not be present in the cached list
    expected_list = [item1, item2, item3]

    cached_list_logic.setCacheItems('test_list', list_with_duplicates)
    cached_list = cached_list_model.CachedList.get_by_id('test_list')
    self.assertListEqual(cached_list.list_data, expected_list)


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


class TestCachedListStates(unittest.TestCase):
  """Unit tests for functions which check and set state of a CachedList."""

  def setUp(self):
    self.valid_list_id = 'valid_cached_list'
    self.invalid_list_id = 'invalid_cached_list'
    self.processing_list_id = 'processing_cached_list'
    self.not_processing_list_id = 'not_processing_cached_list'

    valid_cached_list_properties = {
        'id': self.valid_list_id,
        'valid_through': datetime.datetime.max
    }
    self.valid_list = seeder_logic.seed(
        cached_list_model.CachedList, valid_cached_list_properties)

    invalid_cached_list_properties = {
        'id': self.invalid_list_id,
        'valid_through': datetime.datetime.min
    }
    self.invalid_list = seeder_logic.seed(
        cached_list_model.CachedList, invalid_cached_list_properties)

    processing_cached_list_properties = {
        'id': self.processing_list_id,
        'is_processing': True
    }
    self.processing_list = seeder_logic.seed(
        cached_list_model.CachedList, processing_cached_list_properties)

    not_processing_cached_list_properties = {
        'id': self.not_processing_list_id,
        'is_processing': False
    }
    self.processing_list = seeder_logic.seed(
        cached_list_model.CachedList, not_processing_cached_list_properties)

  def testIsValid(self):
    """Tests isValid function."""
    self.assertTrue(cached_list_logic.isValid(self.valid_list_id))
    self.assertFalse(cached_list_logic.isValid(self.invalid_list_id))

  def testIsProcessing(self):
    """Tests isProcessing function."""
    self.assertTrue(cached_list_logic.isProcessing(self.processing_list_id))
    self.assertFalse(
        cached_list_logic.isProcessing(self.not_processing_list_id))

  def testSetProcessing(self):
    """Tests setProcessing function."""
    cached_list_logic.setProcessing(self.not_processing_list_id)
    updated_list = cached_list_model.CachedList.get_by_id(
        self.not_processing_list_id)
    self.assertTrue(updated_list.is_processing)


class TestCreateEmptyProcessingList(unittest.TestCase):
  """Unit tests for createEmptyProcessingList function."""

  def testCreateEmptyProcessingList(self):
    """Tests createEmptyProcessingList"""
    cached_list_logic.createEmptyProcessingList('empty_processing_list')
    test_list = cached_list_model.CachedList.get_by_id('empty_processing_list')
    self.assertListEqual([], test_list.list_data)
    self.assertTrue(test_list.is_processing)
