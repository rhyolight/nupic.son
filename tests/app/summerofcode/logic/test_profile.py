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

"""Tests for profile logic."""

import unittest

from summerofcode.logic import profile as profile_logic

from tests import profile_utils
from tests import program_utils


class HasProjectTest(unittest.TestCase):
  """Unit tests for hasProject function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    program = program_utils.seedProgram()
    self.profile = profile_utils.seedSOCStudent(program)

  def testForStudentWithNoProjects(self):
    """Tests for student with no projects."""
    self.profile.student_data.number_of_projects = 0
    has_project = profile_logic.hasProject(self.profile)
    self.assertFalse(has_project)

  def testForStudentWithOneProjects(self):
    """Tests for student with one project."""
    self.profile.student_data.number_of_projects = 1
    has_project = profile_logic.hasProject(self.profile)
    self.assertTrue(has_project)
