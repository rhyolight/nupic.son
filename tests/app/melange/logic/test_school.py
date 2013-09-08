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

"""Tests for schools logic."""

import StringIO
import unittest

from melange.logic import school as school_logic


TEST_INPUT_SIZE = 10
TEST_INPUT_READER_DATA = ''.join(
    'uid%s\tname%s\tcountry%s\n' % (i, i, i) for i in range(TEST_INPUT_SIZE))

class GetSchoolsFromReaderTest(unittest.TestCase):
  """Unit tests for getSchoolsFromReader function."""

  def testGetSchoolsFromEmptyReader(self):
    """Tests that no schools are returned for empty input reader."""
    reader = StringIO.StringIO()
    schools = school_logic.getSchoolsFromReader(reader)
    self.assertListEqual(schools, [])

  def testGetSchoolsFromNonEmptyReader(self):
    """Tests that schools are correctly returned for valid input."""
    reader = StringIO.StringIO(TEST_INPUT_READER_DATA)
    schools = school_logic.getSchoolsFromReader(reader)

    self.assertEqual(len(schools), TEST_INPUT_SIZE)
    for i in range(TEST_INPUT_SIZE):
      self.assertEqual(schools[i].uid, 'uid%s' % i)
      self.assertEqual(schools[i].name, 'name%s' % i)
      self.assertEqual(schools[i].country, 'country%s' % i)

