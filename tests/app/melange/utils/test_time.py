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

"""Tests for time utility functions."""

import unittest

from melange.utils import time

from tests import timeline_utils


class IsBeforeTest(unittest.TestCase):
  """Unit tests for isBefore function."""

  def testIsBefore(self):
    """Tests that True is returned if it is before the examined date."""
    self.assertTrue(time.isBefore(timeline_utils.future()))

  def testIsNotBefore(self):
    """Tests that False is returned if it is after the examined date."""
    self.assertFalse(time.isBefore(timeline_utils.past()))

  def testForNone(self):
    """Tests that False is returned for None."""
    self.assertFalse(time.isBefore(None))


class IsAfterTest(unittest.TestCase):
  """Unit tests for isAfter function."""

  def testIsAfter(self):
    """Tests that True is returned if it is after the examined date."""
    self.assertTrue(time.isAfter(timeline_utils.past()))

  def testIsNotAfter(self):
    """Tests that False is returned if it is before the examined date."""
    self.assertFalse(time.isAfter(timeline_utils.future()))

  def testForNone(self):
    """Tests that False is returned for None."""
    self.assertFalse(time.isAfter(None))


class IsBetweenTest(unittest.TestCase):
  """Unit tests for isBetween function."""

  def testIsAfter(self):
    """Tests that False is returned if it is after the examined period."""
    self.assertFalse(time.isBetween(
        timeline_utils.past(delta=10), timeline_utils.past(delta=5)))

  def testIsBefore(self):
    """Tests that False is returned if it is before the examined period."""
    self.assertFalse(time.isBetween(
        timeline_utils.future(delta=5), timeline_utils.future(delta=10)))

  def testIsBetween(self):
    """Tests that True is returned if it is within the examined perioed."""
    self.assertTrue(time.isBetween(
        timeline_utils.past(delta=10), timeline_utils.future(delta=10)))
