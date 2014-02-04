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

"""Unit tests for project related logic."""

import unittest

from soc.modules.gsoc.logic import project as project_logic

from tests import org_utils
from tests import profile_utils
from tests import program_utils
from tests.utils import project_utils


class HasMentorProjectAssignedTest(unittest.TestCase):
  """Unit tests for hasMentorProjectAssigned function."""

  def setUp(self):
    # seed a new program
    self.program = program_utils.seedGSoCProgram()

    # seed a couple of organizations
    self.organization_one = org_utils.seedSOCOrganization(self.program.key())
    self.organization_two = org_utils.seedSOCOrganization(self.program.key())

    # seed a project for the organization one
    student = profile_utils.seedNDBStudent(self.program)
    self.project_one = project_utils.seedProject(
        student, self.program.key(), org_key=self.organization_one.key)
    self.project_one.mentors = []
    self.project_one.put()

    # seed a new mentor for organization one, but without projects
    self.mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.organization_one.key])

  def testMentorWithoutProjects(self):
    """Tests for a mentor with no projects."""
    has_projects = project_logic.hasMentorProjectAssigned(self.mentor)
    self.assertFalse(has_projects)

    has_projects = project_logic.hasMentorProjectAssigned(
        self.mentor, org_key=self.organization_one.key)
    self.assertFalse(has_projects)

  def testMentorWithProject(self):
    """Tests for a mentor with one project for one organization."""
    # assign one project to the mentor
    self.project_one.mentors = [self.mentor.key.to_old_key()]
    self.project_one.put()

    # the mentor has a project
    has_projects = project_logic.hasMentorProjectAssigned(self.mentor)
    self.assertTrue(has_projects)

    # the mentor has a project for organization one
    has_projects = project_logic.hasMentorProjectAssigned(
        self.mentor, org_key=self.organization_one.key)
    self.assertTrue(has_projects)

    # the mentor still does not have projects for organization two
    has_projects = project_logic.hasMentorProjectAssigned(
        self.mentor, org_key=self.organization_two.key)
    self.assertFalse(has_projects)

  def testProjectWithMoreMentors(self):
    """Tests for a mentor for project that have more mentors."""
    # seed a few extra mentors for the same project
    for _ in range(5):
      other_mentor = profile_utils.seedNDBProfile(
          self.program.key(), mentor_for=[self.organization_one.key])
      self.project_one.mentors.append(other_mentor.key.to_old_key())
    self.project_one.put()

    # assign our mentor to the project too
    self.project_one.mentors.append(self.mentor.key.to_old_key())
    self.project_one.put()

    # the mentor has a project
    has_projects = project_logic.hasMentorProjectAssigned(self.mentor)
    self.assertTrue(has_projects)

    # the mentor has a project for organization one
    has_projects = project_logic.hasMentorProjectAssigned(
        self.mentor, org_key=self.organization_one.key)
    self.assertTrue(has_projects)

    # the mentor still does not have projects for organization two
    has_projects = project_logic.hasMentorProjectAssigned(
        self.mentor, org_key=self.organization_two.key)
    self.assertFalse(has_projects)

  def testMentorWithMoreProjects(self):
    """Tests for a mentor with more projects."""
    # seed a few extra projects and assign our mentor
    for _ in range(5):
      student = profile_utils.seedNDBStudent(self.program)
      self.project_one = project_utils.seedProject(
          student, self.program.key(), org_key=self.organization_one.key,
          mentor_key=self.mentor.key)

    # the mentor has projects for organization one
    has_projects = project_logic.hasMentorProjectAssigned(
        self.mentor, org_key=self.organization_one.key)
    self.assertTrue(has_projects)

  def testMentorWithProjectForOtherOrg(self):
    """Tests for a mentor who has a project for another organization."""
    # set our profile a mentor for organization two
    self.mentor.mentor_for.append(self.organization_two.key)
    self.mentor.put()

    # seed a project for organization two
    student = profile_utils.seedNDBStudent(self.program)
    project_utils.seedProject(
        student, self.program.key(), org_key=self.organization_two.key,
        mentor_key=self.mentor.key)

    # the mentor has a project
    has_projects = project_logic.hasMentorProjectAssigned(self.mentor)
    self.assertTrue(has_projects)

    # the mentor has only a project for organization two
    has_projects = project_logic.hasMentorProjectAssigned(
        self.mentor, org_key=self.organization_one.key)
    self.assertFalse(has_projects)
