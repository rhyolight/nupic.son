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
import unittest

from google.appengine.ext import ndb

from melange.logic import school as school_logic
from melange.models import school as school_model

from soc.models import program as program_model
from soc.modules.seeder.logic.seeder import logic as seeder_logic


TEST_INPUT_DATA = (
    ('uid1', 'name1', 'country1'),
    ('uid2', 'name2', 'country2'),
    ('uid3', 'name3', 'country3'))

class UploadSchoolsTest(unittest.TestCase):
  """Unit tests for uploadSchools function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    program_properties = {'predefined_schools_counter': 0}
    self.program = seeder_logic.seed(program_model.Program, program_properties)

  def testSchoolsAreUploaded(self):
    """Tests that schools are uploaded to entity."""
    school_logic.uploadSchools(TEST_INPUT_DATA, self.program)

    school_clusters = ndb.Query(
        kind=school_model.SchoolCluster._get_kind(),
        ancestor=ndb.Key.from_old_key(self.program.key())).fetch(1000)

    # check that SchoolCluster is returned
    self.assertEqual(len(school_clusters), 1)

    # check that correct number of schools is stored
    school_cluster = school_clusters[0]
    self.assertEqual(
        len(school_cluster.schools), len(TEST_INPUT_DATA))

    # check that all data is correct
    for i in range(len(TEST_INPUT_DATA)):
      self.assertEqual(school_cluster.schools[i].uid, TEST_INPUT_DATA[i][0])
      self.assertEqual(school_cluster.schools[i].name, TEST_INPUT_DATA[i][1])
      self.assertEqual(
          school_cluster.schools[i].country, TEST_INPUT_DATA[i][2])

  @mock.patch('melange.logic.school.MAX_SCHOOLS_PER_CLUSTER', new=2)
  def testMoreThanMaxItems(self):
    """Tests that error is raised when more items than allowed is passed."""
    with self.assertRaises(ValueError):
      school_logic.uploadSchools(TEST_INPUT_DATA, self.program)
    
  def testCounterIsUpdated(self):
    """Tests that counter in program model is updated correctly."""
    # update a few schools
    school_logic.uploadSchools(TEST_INPUT_DATA, self.program)

    # check that counter is updated
    program = program_model.Program.get(self.program.key())
    self.assertEqual(program.predefined_schools_counter, len(TEST_INPUT_DATA))

    # update a few more schools
    next_data = [('uid%s' % i, 'name', 'country') for i in range(5)]
    school_logic.uploadSchools(next_data, self.program)

    # check that counter is updated
    program = program_model.Program.get(self.program.key())
    self.assertEqual(
        program.predefined_schools_counter, len(TEST_INPUT_DATA) + 5)


class GetSchoolsForProgramTest(unittest.TestCase):
  """Unit tests for getSchoolsForProgram function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.program = seeder_logic.seed(program_model.Program)

    # seed new schools
    schools = []
    for input_data in TEST_INPUT_DATA:
      schools.append(school_model.School(
          uid=input_data[0], name=input_data[1], country=input_data[2]))
    school_model.SchoolCluster(
        parent=ndb.Key.from_old_key(self.program.key()), schools=schools).put()

  def testForProgram(self):
    """Tests that all schools are returned for the program."""
    schools = school_logic.getSchoolsForProgram(self.program.key())

    # check that all schools are returned
    self.assertEqual(len(schools), len(TEST_INPUT_DATA))

    for i in range(len(TEST_INPUT_DATA)):
      self.assertEqual(schools[i].uid, TEST_INPUT_DATA[i][0])
      self.assertEqual(schools[i].name, TEST_INPUT_DATA[i][1])
      self.assertEqual(schools[i].country, TEST_INPUT_DATA[i][2])

  def testForOtherProgram(self):
    """Tests that no schools are returned for another program."""
    other_program = seeder_logic.seed(program_model.Program)
    schools = school_logic.getSchoolsForProgram(other_program.key())

    # check that no schools are returned
    self.assertListEqual(schools, [])
