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

from soc.modules.gsoc.models import organization as org_model
from soc.modules.gsoc.models import profile as profile_model
from soc.modules.gsoc.models import program as program_model
from soc.modules.gsoc.models import project as project_model

from soc.modules.seeder.logic.seeder import logic as seeder_logic


class HasMentorProjectAssignedTest(unittest.TestCase):
  """Unit tests for hasMentorProjectAssigned function."""

  def setUp(self):
    # seed a new program
    self.program = seeder_logic.seed(program_model.GSoCProgram)

    # seed a couple of organizations
    self.organization_one = seeder_logic.seed(org_model.GSoCOrganization,
        {'scope': self.program})
    self.organization_two = seeder_logic.seed(org_model.GSoCOrganization,
        {'scope': self.program})

    # seed a couple of projects for the organizations
    self.project_one = seeder_logic.seed(project_model.GSoCProject,
        {'scope': self.program, 'org': self.organization_one})

    # seed a new mentor for organization one, but without projects
    mentor_properties = {
        'is_mentor': True,
        'mentor_for': [self.organization_one.key()],
        'is_org_admin': False,
        'org_admin_for': [],
        'status': 'active',
    }
    self.mentor = seeder_logic.seed(
        profile_model.GSoCProfile, mentor_properties)

  def testMentorWithoutProjects(self):
    has_projects = project_logic.hasMentorProjectAssigned(self.mentor)
    self.assertFalse(has_projects)

    has_projects = project_logic.hasMentorProjectAssigned(
        self.mentor, org_key=self.organization_one.key())
    self.assertFalse(has_projects)

  def testMentorWithProject(self):
    # assign one project to the mentor
    self.project_one.mentors = [self.mentor.key()]
    self.project_one.put()

    # the mentor has a project
    has_projects = project_logic.hasMentorProjectAssigned(self.mentor)
    self.assertTrue(has_projects)

    # the mentor has a project for organization one
    has_projects = project_logic.hasMentorProjectAssigned(
        self.mentor, org_key=self.organization_one.key())
    self.assertTrue(has_projects)

    # the mentor still does not have projects for organization two
    has_projects = project_logic.hasMentorProjectAssigned(
        self.mentor, org_key=self.organization_two.key())
    self.assertFalse(has_projects)

  def testProjectWithMoreMentors(self):
    # seed a few extra mentors for the same project
    mentor_properties = {
        'is_mentor': True,
        'mentor_for': [self.organization_one.key()],
        'is_org_admin': False,
        'org_admin_for': [],
        'status': 'active',
    }
    for _ in range(5):
      other_mentor = seeder_logic.seed(
          profile_model.GSoCProfile, mentor_properties)
      self.project_one.mentors.append(other_mentor.key())
    self.project_one.put()

    # assign our mentor to the project too
    self.project_one.mentors = [self.mentor.key()]
    self.project_one.put()

    # the mentor has a project
    has_projects = project_logic.hasMentorProjectAssigned(self.mentor)
    self.assertTrue(has_projects)

    # the mentor has a project for organization one
    has_projects = project_logic.hasMentorProjectAssigned(
        self.mentor, org_key=self.organization_one)
    self.assertTrue(has_projects)

    # the mentor still does not have projects for organization two
    has_projects = project_logic.hasMentorProjectAssigned(
        self.mentor, org_key=self.organization_two.key())
    self.assertFalse(has_projects)

  def testMentorWithMoreProjects(self):
    # seed a few extra projects and assign our mentor
    project_properties = {
        'scope': self.program,
        'org': self.organization_one,
        'mentors': [self.mentor.key()]
        }
    for _ in range(5):
      seeder_logic.seed(project_model.GSoCProject, project_properties)

    # the mentor has projects for organization one
    has_projects = project_logic.hasMentorProjectAssigned(
        self.mentor, org_key=self.organization_one.key())
    self.assertTrue(has_projects)

  def testMentorWithProjectForOtherOrg(self):
    # set our profile a mentor for organization two
    self.mentor.mentor_for.append(self.organization_two.key())
    self.mentor.put()

    # seed a project for organization two
    project_properties = {
        'scope': self.program,
        'org': self.organization_two,
        'mentors': [self.mentor.key()]
        }
    seeder_logic.seed(project_model.GSoCProject, project_properties)

    # the mentor has a project
    has_projects = project_logic.hasMentorProjectAssigned(self.mentor)
    self.assertTrue(has_projects)

    # the mentor has only a project for organization two
    has_projects = project_logic.hasMentorProjectAssigned(
        self.mentor, org_key=self.organization_one.key())
    self.assertFalse(has_projects)
