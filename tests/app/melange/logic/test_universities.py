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

"""Tests for universities logic."""

import mock
import unittest

from google.appengine.ext import ndb

from melange.logic import universities as universities_logic
from melange.models import universities as universities_model

from soc.models import program as program_model
from soc.modules.seeder.logic.seeder import logic as seeder_logic


TEST_INPUT_DATA = (
    ('uid1', 'name1', 'country1'),
    ('uid2', 'name2', 'country2'),
    ('uid3', 'name3', 'country3'))

class UploadUniversitiesTest(unittest.TestCase):
  """Unit tests for uploadUniversities function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.program = seeder_logic.seed(program_model.Program)

  def testUniversitiesAreUploaded(self):
    """Tests that universities are uploaded to entity."""
    universities_logic.uploadUniversities(TEST_INPUT_DATA, self.program.key())

    university_clusters = ndb.Query(
        kind=universities_model.UniversityCluster._get_kind(),
        ancestor=ndb.Key.from_old_key(self.program.key())).fetch(1000)

    # check that Universities is returned
    self.assertEqual(len(university_clusters), 1)

    # check that correct number of universities is stored
    university_cluster = university_clusters[0]
    self.assertEqual(
        len(university_cluster.universities), len(TEST_INPUT_DATA))

    # check that all data is correct
    for i in range(len(TEST_INPUT_DATA)):
      self.assertEqual(
          university_cluster.universities[i].uid, TEST_INPUT_DATA[i][0])
      self.assertEqual(
          university_cluster.universities[i].name, TEST_INPUT_DATA[i][1])
      self.assertEqual(
          university_cluster.universities[i].country, TEST_INPUT_DATA[i][2])

  @mock.patch('melange.logic.universities._MAX_SAFE_SIZE', new=200)
  def testMoreThanOneEntity(self):
    """Tests that more than one entity may be created."""

    test_data = [('uid%s' % i, 'name', 'country') for i in range(10)]
    universities_logic.uploadUniversities(test_data, self.program.key())

    university_clusters = ndb.Query(
        kind=universities_model.UniversityCluster._get_kind(),
        ancestor=ndb.Key.from_old_key(self.program.key())).fetch(1000)

    # check that more than one entity is created
    self.assertGreater(len(university_clusters), 1)

    # check that overall all universities are stored
    universities = []
    for university_cluster in university_clusters:
      universities.extend(university_cluster.universities)
    self.assertEqual(len(universities), 10)


class GetUniversitiesForProgramTest(unittest.TestCase):
  """Unit tests for getUniversitiesForProgram function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.program = seeder_logic.seed(program_model.Program)

    # seed a new universities
    universities = []
    for input_data in TEST_INPUT_DATA:
      universities.append(universities_model.University(
          uid=input_data[0], name=input_data[1], country=input_data[2]))
    universities_model.UniversityCluster(
        parent=ndb.Key.from_old_key(self.program.key()),
        universities=universities).put()

  def testForProgram(self):
    """Tests that all universities are returned for the program."""
    universities = universities_logic.getUniversitiesForProgram(
        self.program.key())

    # check that all universities are returned
    self.assertEqual(len(universities), len(TEST_INPUT_DATA))

    for i in range(len(TEST_INPUT_DATA)):
      self.assertEqual(universities[i].uid, TEST_INPUT_DATA[i][0])
      self.assertEqual(universities[i].name, TEST_INPUT_DATA[i][1])
      self.assertEqual(universities[i].country, TEST_INPUT_DATA[i][2])

  def testForOtherProgram(self):
    """Tests that no universities are returned for another program."""
    other_program = seeder_logic.seed(program_model.Program)
    universities = universities_logic.getUniversitiesForProgram(
        other_program.key())

    # check that no universities are returned
    self.assertListEqual(universities, [])
