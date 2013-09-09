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

import mock
import StringIO
import unittest

from google.appengine.ext import blobstore

from melange.logic import school as school_logic

from soc.models import program as program_model
from soc.modules.seeder.logic.seeder import logic as seeder_logic


TEST_INPUT_SIZE = 10
TEST_INPUT_READER_DATA = ''.join(
    'uid%s\tname%s\tcountry%s\n' % (i, i, i) for i in range(TEST_INPUT_SIZE))

TEST_LIST_OF_SCHOOLS = [
    school_logic.School('uid1', 'name1', 'country1'),
    school_logic.School('uid2', 'name2', 'country2'),
    school_logic.School('uid3', 'name3', 'country1'),
    school_logic.School('uid4', 'name4', 'country1'),
    school_logic.School('uid5', 'name5', 'country3'),
    school_logic.School('uid6', 'name6', 'country2')]
EXPECTED_SCHOOL_MAP = {
    'country1': ['name1', 'name3', 'name4'],
    'country2': ['name2', 'name6'],
    'country3': ['name5']
    }

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


class GetMappedByCountriesTest(unittest.TestCase):
  """Unit tests for getMappedByCountries function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.program = seeder_logic.seed(program_model.Program)

  def testForProgramWithNoDefinedSchools(self):
    """Tests for program that has no predefined schools."""
    school_map = school_logic.getMappedByCountries(self.program)
    self.assertDictEqual(school_map, {})

  @mock.patch.object(school_logic, 'getSchoolsFromReader',
      return_value=TEST_LIST_OF_SCHOOLS)
  def testForProgramWithDefinedSchools(self, mock_func):
    """Tests for program that has predefined schools."""
    self.program.schools = 'mock key'
    school_map = school_logic.getMappedByCountries(self.program)
    self.assertDictEqual(school_map, EXPECTED_SCHOOL_MAP)
