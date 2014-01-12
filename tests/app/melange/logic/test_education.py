# Copyright 2014 the Melange authors.
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

"""Tests for address logic."""

import datetime
import unittest

from melange.logic import education as education_logic
from melange.models import education as education_model

TEST_SCHOOL_ID = 'school_id'
TEST_SCHOOL_COUNTRY = 'United States'
TEST_EXPECTED_GRADUATION = datetime.date.today().year + 1
TEST_MAJOR = 'Test Major'
TEST_DEGREE = education_model.Degree.MASTERS


class CreatePostSecondaryEducationTest(unittest.TestCase):
  """Unit tests for createPostSecondaryEducation function."""

  def testValidData(self):
    """Tests that education entity is created properly if all data is valid."""
    result = education_logic.createPostSecondaryEducation(
        TEST_SCHOOL_ID, TEST_SCHOOL_COUNTRY, TEST_EXPECTED_GRADUATION,
        TEST_MAJOR, TEST_DEGREE)
    self.assertTrue(result)

    education = result.extra
    self.assertEqual(education.school_id, TEST_SCHOOL_ID)
    self.assertEqual(education.school_country, TEST_SCHOOL_COUNTRY)
    self.assertEqual(education.expected_graduation, TEST_EXPECTED_GRADUATION)
    self.assertEqual(education.major, TEST_MAJOR)
    self.assertEqual(education.degree, TEST_DEGREE)

  def testInvalidData(self):
    """Tests that education entity is not created if data is not valid."""
    # non-existing country
    result = education_logic.createPostSecondaryEducation(
        TEST_SCHOOL_ID, 'Neverland', TEST_EXPECTED_GRADUATION,
        TEST_MAJOR, TEST_DEGREE)
    self.assertFalse(result)

    # graduation year is not a number
    result = education_logic.createPostSecondaryEducation(
        TEST_SCHOOL_ID, TEST_SCHOOL_COUNTRY, str(TEST_EXPECTED_GRADUATION),
        TEST_MAJOR, TEST_DEGREE)
    self.assertFalse(result)
