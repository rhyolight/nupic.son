# Copyright 2011 the Melange authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import unittest

from soc.logic import validate


class ValidateTest(unittest.TestCase):
  """Tests related to the validation helper functions."""

  def testIsFeedURLValid(self):
    """Tests whether the urls are valid feed urls."""
    #invalid: not a feed url
    self.assertFalse(validate.isFeedURLValid('http://www.google.com'))

    self.assertFalse(validate.isFeedURLValid(''))

    #valid feed url
    self.assertTrue(validate.isFeedURLValid(
        'http://googlesummerofcode.blogspot.com/feeds/posts/default'))

    #invalid: wrong protocol
    self.assertFalse(validate.isFeedURLValid(
        'htp://googlesummerofcode.blogspot.com/feeds/posts/default'))

  def testIsLinkIdFormatValid(self):
    """Tests the validity of Link Ids."""
    #valid: starts with lowercase, no double underscores, does not end
    #with an underscore
    self.assertTrue(validate.isLinkIdFormatValid('sfd32'))

    #invalid: starts with a number
    self.assertFalse(validate.isLinkIdFormatValid('9s8whhu'))

    #invalid: starts with an underscore
    self.assertFalse(validate.isLinkIdFormatValid('_jhja87'))

    #valid: double underscore
    self.assertTrue(validate.isLinkIdFormatValid('kjnask__j87'))

    #valid: trailing underscore
    self.assertTrue(validate.isLinkIdFormatValid('jhsdfj_'))

    #invalid: starting and trailing underscores
    self.assertFalse(validate.isLinkIdFormatValid('_jhsj38_'))

    #invalid: starts with uppercase
    self.assertFalse(validate.isLinkIdFormatValid('Ukkjs'))

    #valid: underscore in the middle and rest in lowercase
    self.assertTrue(validate.isLinkIdFormatValid('a_b'))

    #invalid: a capital letter in the middle
    self.assertFalse(validate.isLinkIdFormatValid('aBc'))

  def testIsAgeSufficientForProgram(self):
    test_program_start = datetime.date(2012, 11, 26)
    test_min_age = 13
    test_max_age = 20

    # TODO(nathaniel): Use a real program.
    class MockProgram(object):
      student_min_age_as_of = test_program_start
      student_min_age = test_min_age
      student_max_age = test_max_age
    mock_program = MockProgram()

    # Someone hasn't yet been born.
    test_birth_date = test_program_start.replace(
        year=test_program_start.year + 1)
    self.assertFalse(validate.isAgeSufficientForProgram(
        test_birth_date, mock_program))

    # Someone's really, really young.
    test_birth_date = test_program_start.replace(
        year=test_program_start.year - 1)
    self.assertFalse(validate.isAgeSufficientForProgram(
        test_birth_date, mock_program))

    # Someone's just one day too young.
    test_birth_date = test_program_start.replace(
        year=test_program_start.year - test_min_age)
    test_birth_date = test_birth_date + datetime.timedelta(1)
    self.assertFalse(validate.isAgeSufficientForProgram(
        test_birth_date, mock_program))

    # Someone's just old enough today.
    test_birth_date = test_program_start.replace(
        year=test_program_start.year - test_min_age)
    self.assertTrue(validate.isAgeSufficientForProgram(
        test_birth_date, mock_program))

    # Someone's old enough by a full day.
    test_birth_date = test_program_start.replace(
        year=test_program_start.year - test_min_age)
    test_birth_date = test_birth_date - datetime.timedelta(1)
    self.assertTrue(validate.isAgeSufficientForProgram(
        test_birth_date, mock_program))

    # Someone's right in the sweet spot.
    test_birth_date = test_program_start.replace(
        year=test_program_start.year - (test_min_age + test_max_age - 1) / 2)
    test_birth_date = test_birth_date + datetime.timedelta(173)
    self.assertTrue(validate.isAgeSufficientForProgram(
        test_birth_date, mock_program))

    # Someone's young enough by six months.
    test_birth_date = test_program_start.replace(
        year=test_program_start.year - test_max_age - 1)
    test_birth_date = test_birth_date + datetime.timedelta(180)
    self.assertTrue(validate.isAgeSufficientForProgram(
        test_birth_date, mock_program))

    # Someone's just young enough.
    test_birth_date = test_program_start.replace(
        year=test_program_start.year - test_max_age - 1)
    test_birth_date = test_birth_date + datetime.timedelta(1)
    self.assertTrue(validate.isAgeSufficientForProgram(
        test_birth_date, mock_program))

    # Someone's having a birthday! Sadly they are too old.
    test_birth_date = test_program_start.replace(
        year=test_program_start.year - test_max_age - 1)
    self.assertFalse(validate.isAgeSufficientForProgram(
        test_birth_date, mock_program))

    # Someone's too old by a full day.
    test_birth_date = test_program_start.replace(
        year=test_program_start.year - test_max_age - 1)
    test_birth_date = test_birth_date - datetime.timedelta(1)
    self.assertFalse(validate.isAgeSufficientForProgram(
        test_birth_date, mock_program))

    # Someone's too old by six months.
    test_birth_date = test_program_start.replace(
        year=test_program_start.year - test_max_age - 1)
    test_birth_date = test_birth_date - datetime.timedelta(180)
    self.assertFalse(validate.isAgeSufficientForProgram(
        test_birth_date, mock_program))

    # Someone's way too old.
    test_birth_date = test_program_start.replace(
        year=test_program_start.year - test_max_age * 12)
    self.assertFalse(validate.isAgeSufficientForProgram(
        test_birth_date, mock_program))
