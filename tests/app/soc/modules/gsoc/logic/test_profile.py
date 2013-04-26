# Copyright 2011 the Melange authors.
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

"""Tests for soc.modules.gsoc.logic.profile.
"""


import unittest

from soc.modules.gsoc.logic import profile as profile_logic

from soc.modules.gsoc.models import profile as profile_model
from soc.modules.gsoc.models import project as project_model
from soc.modules.gsoc.models import proposal as proposal_model

from soc.modules.gsoc.models.organization import GSoCOrganization
from soc.modules.gsoc.models.program import GSoCProgram

from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests.profile_utils import GSoCProfileHelper


class ProfileTest(unittest.TestCase):
  """Tests the GSoC logic for profiles.
  """

  def createMentor(self, email, organization):
    """Creates a mentor for the given organization.
    """
    profile_helper = GSoCProfileHelper(self.program, dev_test=False)
    profile_helper.createOtherUser(email)
    mentor = profile_helper.createMentor(organization)
    return mentor

  def createOrgAdmin(self, email, organization):
    """Creates an organization admin for the given organization.
    """
    profile_helper = GSoCProfileHelper(self.program, dev_test=False)
    profile_helper.createOtherUser(email)
    admin = profile_helper.createOrgAdmin(organization)
    return admin

  def setUp(self):
    self.program = seeder_logic.seed(GSoCProgram)
    organization_properties = {'program': self.program}
    self.foo_organization = seeder_logic.seed(GSoCOrganization,
                                              organization_properties)

    #create mentors for foo_organization.
    self.foo_mentors = []
    for i in range(5):
      email = 'foomentor%s@example.com' % str(i)
      mentor = self.createMentor(email, self.foo_organization)
      self.foo_mentors.append(mentor)

    #create organization admins for foo_organization.
    self.foo_org_admins = []
    for i in range(5):
      email = 'fooorgadmin%s@gmail.com' % str(i)
      admin = self.createOrgAdmin(email, self.foo_organization)
      self.foo_org_admins.append(admin)

    #create another organization bar_organization for our program.
    self.bar_organization = seeder_logic.seed(GSoCOrganization,
                                              organization_properties)
    #assign mentors for bar_organization.
    self.bar_mentors = []
    for i in range(5):
      email = 'barmentor%s@gmail.com' % str(i)
      mentor = self.createMentor(email, self.bar_organization)
      self.bar_mentors.append(mentor)
    #assign an organization admin for bar_organization
    email = 'barorgadmin@gmail.com'
    self.bar_org_admin = self.createOrgAdmin(email, self.bar_organization)


  def testQueryAllMentorsKeysForOrg(self):
    """Tests that a list of keys for all the mentors in an organization are
    returned.
    """
    def runTest(org, mentors, org_admins):
      """Runs the test.
      """
      mentor_keys = [entity.key() for entity in mentors]
      org_admin_keys = [entity.key() for entity in org_admins]
      expected_keys = set(mentor_keys + org_admin_keys)
      actual_keys = set(profile_logic.queryAllMentorsKeysForOrg(org))
      self.assertEqual(expected_keys, actual_keys)

    #Test for foo_organization
    mentors = self.foo_mentors
    org_admins = self.foo_org_admins
    org = self.foo_organization
    runTest(org, mentors, org_admins)

    #Test the same for bar_organization
    mentors = self.bar_mentors
    org_admins = [self.bar_org_admin]
    org = self.bar_organization
    runTest(org, mentors, org_admins)

    #Create an organization which has no mentors and org_admins and test that
    #an empty list is returned.
    organization_properties = {'program': self.program}
    org = seeder_logic.seed(GSoCOrganization, organization_properties)
    mentors = []
    org_admins = []
    runTest(org, mentors, org_admins)


class CanResignAsMentorForOrgTest(unittest.TestCase):
  """Unit tests for canResignAsMentorForOrg function."""

  def setUp(self):
    # seed a new program
    self.program = seeder_logic.seed(GSoCProgram)

     # seed a couple of organizations
    self.organization_one = seeder_logic.seed(GSoCOrganization,
        {'program': self.program})
    self.organization_two = seeder_logic.seed(GSoCOrganization,
        {'program': self.program})

    # seed a new mentor for organization one
    mentor_properties = {
        'is_mentor': True,
        'mentor_for': [self.organization_one.key()],
        'is_org_admin': False,
        'org_admin_for': [],
        'status': 'active',
    }
    self.mentor = seeder_logic.seed(
        profile_model.GSoCProfile, mentor_properties)

  def testMentorCanResign(self):
    # mentor is not involved in organization one
    can_resign = profile_logic.canResignAsMentorForOrg(
        self.mentor, self.organization_one)
    self.assertTrue(can_resign)

  def testMentorWithProject(self):
    # seed a project for organization one
    project_properties = {
        'scope': self.program,
        'org': self.organization_one,
        'mentors': [self.mentor.key()]
        }
    seeder_logic.seed(project_model.GSoCProject, project_properties)

    # mentor is involved in organization one because of a project
    can_resign = profile_logic.canResignAsMentorForOrg(
        self.mentor, self.organization_one)
    self.assertFalse(can_resign)

    # add mentor role for organization two
    self.mentor.mentor_for.append(self.organization_two.key())

    # mentor is not involved in organization two
    can_resign = profile_logic.canResignAsMentorForOrg(
        self.mentor, self.organization_two)
    self.assertTrue(can_resign)

  def testMentorWithProposal(self):
    # seed a new proposal and assign our mentor
    proposal_properties = {
        'status': 'pending',
        'accept_as_project': False,
        'has_mentor': True,
        'mentor': self.mentor,
        'program': self.program,
        'org': self.organization_one,
        }
    proposal = seeder_logic.seed(
        proposal_model.GSoCProposal, proposal_properties)

    # mentor is involved in organization one because of a proposal
    can_resign = profile_logic.canResignAsMentorForOrg(
        self.mentor, self.organization_one)
    self.assertFalse(can_resign)

    # add mentor role for organization two
    self.mentor.mentor_for.append(self.organization_two.key())

    # mentor is not involved in organization two
    can_resign = profile_logic.canResignAsMentorForOrg(
        self.mentor, self.organization_two)
    self.assertTrue(can_resign)

  def testNotMentorForOrg(self):
    # profile is not a mentor for organization two
    with self.assertRaises(ValueError):
      profile_logic.canResignAsMentorForOrg(
          self.mentor, self.organization_two)
