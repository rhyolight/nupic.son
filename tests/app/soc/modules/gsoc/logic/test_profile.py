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

"""Tests for soc.modules.gsoc.logic.profile."""

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
        self.mentor, self.organization_one.key())
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
        self.mentor, self.organization_one.key())
    self.assertFalse(can_resign)

    # add mentor role for organization two
    self.mentor.mentor_for.append(self.organization_two.key())

    # mentor is not involved in organization two
    can_resign = profile_logic.canResignAsMentorForOrg(
        self.mentor, self.organization_two.key())
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
        self.mentor, self.organization_one.key())
    self.assertFalse(can_resign)

    # add mentor role for organization two
    self.mentor.mentor_for.append(self.organization_two.key())

    # mentor is not involved in organization two
    can_resign = profile_logic.canResignAsMentorForOrg(
        self.mentor, self.organization_two.key())
    self.assertTrue(can_resign)

  def testNotMentorForOrg(self):
    # profile is not a mentor for organization two
    with self.assertRaises(ValueError):
      profile_logic.canResignAsMentorForOrg(
          self.mentor, self.organization_two.key())


class CanResignAsOrgAdminTest(unittest.TestCase):
  """Unit tests for canResignAsOrgAdmin function."""

  def setUp(self):
    # seed a new program
    self.program = seeder_logic.seed(GSoCProgram)

     # seed a couple of organizations
    self.organization_one = seeder_logic.seed(GSoCOrganization,
        {'program': self.program})
    self.organization_two = seeder_logic.seed(GSoCOrganization,
        {'program': self.program})

    # seed a new org admin for organization one
    org_admin_properties = {
        'is_mentor': True,
        'mentor_for': [self.organization_one.key()],
        'is_org_admin': True,
        'org_admin_for': [self.organization_one.key()],
        'status': 'active',
    }
    self.org_admin = seeder_logic.seed(
        profile_model.GSoCProfile, org_admin_properties)

  def testOnlyOrgAdmin(self):
    # the only org admin cannot resign
    can_resign = profile_logic.canResignAsOrgAdminForOrg(
        self.org_admin, self.organization_one.key())
    self.assertFalse(can_resign)

  def testMoreOrgAdmins(self):
    # seed another org admin for organization one
    org_admin_properties = {
        'is_mentor': True,
        'mentor_for': [self.organization_one.key()],
        'is_org_admin': True,
        'org_admin_for': [self.organization_one.key()],
        'status': 'active',
    }
    self.org_admin = seeder_logic.seed(
        profile_model.GSoCProfile, org_admin_properties)

    # now the org admin can resign, as there is another admin
    can_resign = profile_logic.canResignAsOrgAdminForOrg(
        self.org_admin, self.organization_one.key())
    self.assertTrue(can_resign)

  def testNotOrgAdminForOrg(self):
    # profile is not an org admin for organization two
    with self.assertRaises(ValueError):
      profile_logic.canResignAsOrgAdminForOrg(
          self.org_admin, self.organization_two.key())


class ResignAsOrgAdminForOrgTest(unittest.TestCase):
  """Unit tests for resignAsOrgAdminForOrg function."""

  def setUp(self):
    # seed a new program
    self.program = seeder_logic.seed(GSoCProgram)

     # seed a couple of organizations
    self.organization = seeder_logic.seed(GSoCOrganization,
        {'program': self.program})
    self.organization = seeder_logic.seed(GSoCOrganization,
        {'program': self.program})

    # seed a new org admin for organization
    org_admin_properties = {
        'is_mentor': True,
        'mentor_for': [self.organization.key()],
        'is_org_admin': True,
        'org_admin_for': [self.organization.key()],
        'status': 'active',
    }
    self.org_admin = seeder_logic.seed(
        profile_model.GSoCProfile, org_admin_properties)

  def testForOnlyOrgAdmin(self):
    profile_logic.resignAsOrgAdminForOrg(
        self.org_admin, self.organization.key())

    # the profile should still be an org admin
    self.assertTrue(self.org_admin.is_org_admin)
    self.assertIn(self.organization.key(), self.org_admin.org_admin_for)

  def testForTwoOrgAdmins(self):
    # seed another org admin for organization
    org_admin_properties = {
        'is_mentor': True,
        'mentor_for': [self.organization.key()],
        'is_org_admin': True,
        'org_admin_for': [self.organization.key()],
        'status': 'active',
    }
    seeder_logic.seed(
        profile_model.GSoCProfile, org_admin_properties)

    profile_logic.resignAsOrgAdminForOrg(
        self.org_admin, self.organization.key())

    # the profile should not be an org admin anymore
    self.assertFalse(self.org_admin.is_org_admin)
    self.assertNotIn(self.organization.key(), self.org_admin.org_admin_for)

  def testForOrgAdminForTwoOrgs(self):
    # seed another org admin for organization
    org_admin_properties = {
        'is_mentor': True,
        'mentor_for': [self.organization.key()],
        'is_org_admin': True,
        'org_admin_for': [self.organization.key()],
        'status': 'active',
    }
    seeder_logic.seed(
        profile_model.GSoCProfile, org_admin_properties)

    # seed another organization
    organization_two = seeder_logic.seed(GSoCOrganization,
        {'program': self.program})

    # make the profile an org admin for organization two
    self.org_admin.mentor_for.append(organization_two.key())
    self.org_admin.org_admin_for.append(organization_two.key())

    profile_logic.resignAsOrgAdminForOrg(
        self.org_admin, self.organization.key())

    # the profile is not an org admin for organization anymore
    self.assertNotIn(self.organization.key(), self.org_admin.org_admin_for)

    # the profile should still be an org admin for organization two
    self.assertTrue(self.org_admin.is_org_admin)
    self.assertIn(organization_two.key(), self.org_admin.org_admin_for)


class GetOrgAdminsTest(unittest.TestCase):
  """Unit tests for getOrgAdmins function."""

  def setUp(self):
    # seed a new program
    self.program = seeder_logic.seed(GSoCProgram)

     # seed a couple of organizations
    self.organization_one = seeder_logic.seed(GSoCOrganization,
        {'program': self.program})
    self.organization_two = seeder_logic.seed(GSoCOrganization,
        {'program': self.program})

  def testNoOrgAdmin(self):
    org_admins = profile_logic.getOrgAdmins(self.organization_one.key())
    self.assertEqual(org_admins, [])

  def testOneOrgAdmin(self):
    # seed a new org admin for organization one
    org_admin_properties = {
        'is_mentor': True,
        'mentor_for': [self.organization_one.key()],
        'is_org_admin': True,
        'org_admin_for': [self.organization_one.key()],
        'status': 'active',
    }
    org_admin = seeder_logic.seed(
        profile_model.GSoCProfile, org_admin_properties)

    # the org admin should be returned
    org_admins = profile_logic.getOrgAdmins(self.organization_one.key())
    self.assertEqual(len(org_admins), 1)
    self.assertEqual(org_admins[0].key(), org_admin.key())

    # keys_only set to True should return only the key
    org_admins_keys = profile_logic.getOrgAdmins(
        self.organization_one.key(), keys_only=True)
    self.assertEqual(len(org_admins_keys), 1)
    self.assertEqual(org_admins_keys[0], org_admin.key())

    # there is still no org admin for organization two
    org_admins = profile_logic.getOrgAdmins(self.organization_two.key())
    self.assertEqual(org_admins, [])

  def testManyOrgAdmins(self):
    # seed  org admins for organization one
    org_admin_properties = {
        'is_mentor': True,
        'mentor_for': [self.organization_one.key()],
        'is_org_admin': True,
        'org_admin_for': [self.organization_one.key()],
        'status': 'active',
    }
    seeded_org_admins = set()
    for _ in range(5):
      seeded_org_admins.add(seeder_logic.seed(
        profile_model.GSoCProfile, org_admin_properties).key())

    # all org admins should be returned
    org_admins = profile_logic.getOrgAdmins(self.organization_one.key())
    self.assertEqual(len(org_admins), 5)
    self.assertEqual(seeded_org_admins,
        set([org_admin.key() for org_admin in org_admins]))

    # all org admins keys should be returned if keys_only set
    org_admins_keys = profile_logic.getOrgAdmins(
        self.organization_one.key(), keys_only=True)
    self.assertEqual(len(org_admins_keys), 5)
    self.assertEqual(seeded_org_admins, set(org_admins_keys))

  def testNotActiveOrgAdmin(self):
    # seed invalid org admins for organization one
    org_admin_properties = {
        'is_mentor': True,
        'mentor_for': [self.organization_one.key()],
        'is_org_admin': True,
        'org_admin_for': [self.organization_one.key()],
        'status': 'invalid',
    }
    org_admin = seeder_logic.seed(
        profile_model.GSoCProfile, org_admin_properties)

    # not active org admin not returned
    org_admins = profile_logic.getOrgAdmins(self.organization_one.key())
    self.assertEqual(org_admins, [])

    # keys_only set to True does not return any keys
    org_admins_keys = profile_logic.getOrgAdmins(
        self.organization_one.key(), keys_only=True)
    self.assertEqual(org_admins_keys, [])

  def testExtraAttrs(self):
    # seed male org admin for organization one
    org_admin_properties = {
        'is_mentor': True,
        'mentor_for': [self.organization_one.key()],
        'is_org_admin': True,
        'org_admin_for': [self.organization_one.key()],
        'status': 'active',
        'gender': 'male',
      }
    org_admin = seeder_logic.seed(
        profile_model.GSoCProfile, org_admin_properties)

    # seed female org admin for organization one
    org_admin_properties['gender'] = 'female'
    seeder_logic.seed(
        profile_model.GSoCProfile, org_admin_properties)

    # retrieve only org admins with extra attrs
    extra_attrs = {
        profile_model.GSoCProfile.gender: 'male',
        }
    org_admins = profile_logic.getOrgAdmins(self.organization_one.key(),
        extra_attrs=extra_attrs)

    # only the male org admin should be returned
    self.assertEqual(1, len(org_admins))
    self.assertEqual(org_admins[0].key(), org_admin.key())


class CountOrgAdminsTest(unittest.TestCase):
  """Unit tests for countOrgAdmins function."""

  def setUp(self):
    # seed a new program
    self.program = seeder_logic.seed(GSoCProgram)

     # seed a couple of organizations
    self.organization_one = seeder_logic.seed(GSoCOrganization,
        {'program': self.program})
    self.organization_two = seeder_logic.seed(GSoCOrganization,
        {'program': self.program})

  def testNoOrgAdmin(self):
    number = profile_logic.countOrgAdmins(self.organization_one.key())
    self.assertEqual(number, 0)

  def testManyOrgAdmins(self):
    # seed  org admins for organization one
    org_admin_properties = {
        'is_mentor': True,
        'mentor_for': [self.organization_one.key()],
        'is_org_admin': True,
        'org_admin_for': [self.organization_one.key()],
        'status': 'active',
    }
    seeded_org_admins = set()
    for _ in range(5):
      seeder_logic.seed(profile_model.GSoCProfile, org_admin_properties)

    # seed  org admins for organization one
    org_admin_properties = {
        'is_mentor': True,
        'mentor_for': [self.organization_two.key()],
        'is_org_admin': True,
        'org_admin_for': [self.organization_two.key()],
        'status': 'active',
    }
    seeded_org_admins = set()
    for _ in range(3):
      seeder_logic.seed(profile_model.GSoCProfile, org_admin_properties)

    # all org admins for organization one should be returned
    number = profile_logic.countOrgAdmins(self.organization_one.key())
    self.assertEqual(number, 5)

    # all org admins for organization two should be returned
    number = profile_logic.countOrgAdmins(self.organization_two.key())
    self.assertEqual(number, 3)

    def testNotActiveOrgAdmin(self):
      # seed invalid org admins for organization one
      org_admin_properties = {
          'is_mentor': True,
          'mentor_for': [self.organization_one.key()],
          'is_org_admin': True,
          'org_admin_for': [self.organization_one.key()],
          'status': 'invalid',
      }
      org_admin = seeder_logic.seed(
          profile_model.GSoCProfile, org_admin_properties)
  
      # seed the other org admin who is active
      org_admin_properties['status'] = 'active'
      org_admin = seeder_logic.seed(
          profile_model.GSoCProfile, org_admin_properties)  
  
      # only active org admin counted
      org_admins = profile_logic.countOrgAdmins(self.organization_one.key())
      self.assertEqual(org_admins, 1)


class ResignAsMentorForOrgTest(unittest.TestCase):
  """Unit tests for resignAsMentorForOrg function."""

  def setUp(self):
    # seed a new program
    self.program = seeder_logic.seed(GSoCProgram)

     # seed a couple of organizations
    self.organization = seeder_logic.seed(GSoCOrganization,
        {'program': self.program})

    # seed a new mentor for organization one
    mentor_properties = {
        'is_mentor': True,
        'mentor_for': [self.organization.key()],
        'is_org_admin': False,
        'org_admin_for': [],
        'status': 'active',
    }
    self.mentor = seeder_logic.seed(
        profile_model.GSoCProfile, mentor_properties)

  def testForOrgAdmin(self):
    # make the profile an org admin for organization
    self.mentor.is_org_admin = True
    self.mentor.org_admin_for = [self.organization.key()]
    self.mentor.put()

    profile_logic.resignAsMentorForOrg(self.mentor, self.organization.key())

    # the profile should still be a mentor because of being org admin
    self.assertTrue(self.mentor.is_mentor)
    self.assertIn(self.organization.key(), self.mentor.mentor_for)

  def testForMentorWithoutProject(self):
    profile_logic.resignAsMentorForOrg(self.mentor, self.organization.key())

    # the profile is not a mentor anymore
    self.assertFalse(self.mentor.is_mentor)
    self.assertNotIn(self.organization.key(), self.mentor.mentor_for)

  def testForMentorWithProject(self):
    # seed a project for organization one and set a mentor
    project_properties = {
        'scope': self.program,
        'org': self.organization,
        'mentors': [self.mentor.key()]
        }
    seeder_logic.seed(project_model.GSoCProject, project_properties)

    profile_logic.resignAsMentorForOrg(self.mentor, self.organization.key())

    # the profile should still be a mentor because of the project
    self.assertTrue(self.mentor.is_mentor)
    self.assertIn(self.organization.key(), self.mentor.mentor_for)

  def testForMentorForTwoOrgs(self):
    # seed another organization
    organization_two = seeder_logic.seed(GSoCOrganization,
        {'program': self.program})

    # make the profile a mentor for organization two
    self.mentor.mentor_for.append(organization_two.key())
    self.mentor.put()

    profile_logic.resignAsMentorForOrg(self.mentor, self.organization.key())

    # the profile is not a mentor for organization anymore
    self.assertNotIn(self.organization.key(), self.mentor.mentor_for)

    # the profile should still be a mentor for organization_two
    self.assertTrue(self.mentor.is_mentor)
    self.assertIn(organization_two.key(), self.mentor.mentor_for)


class CanBecomeMentorTest(unittest.TestCase):
  """Unit tests for canBecomeMentor function."""

  def setUp(self):
    # seed a new program
    self.program = seeder_logic.seed(GSoCProgram)

     # seed an organization
    self.organization = seeder_logic.seed(GSoCOrganization,
        {'program': self.program})

    # seed a new profile
    profile_properties = {
        'is_mentor': False,
        'mentor_for': [],
        'is_org_admin': False,
        'org_admin_for': [],
        'status': 'active',
        'is_student': False
    }
    self.profile = seeder_logic.seed(
        profile_model.GSoCProfile, profile_properties)

  def testForInvalidProfile(self):
    # make the profile invalid
    self.profile.status = 'invalid'
    self.profile.put()

    # invalid profiles cannot become mentors
    can_become = profile_logic.canBecomeMentor(self.profile)
    self.assertFalse(can_become)

  def testForStudentProfile(self):
    # make the profile invalid
    self.profile.is_student = True
    self.profile.put()

    # student profiles cannot become mentors
    can_become = profile_logic.canBecomeMentor(self.profile)
    self.assertFalse(can_become)

  def testForLoneProfile(self):
    # profile with no roles can become mentors
    can_become = profile_logic.canBecomeMentor(self.profile)
    self.assertTrue(can_become)

  def testForMentor(self):
    # make the profile a mentor for organization
    self.profile.is_mentor = True
    self.profile.mentor_for = [self.organization.key()]

    # profile with a mentor role can still become a mentor
    can_become = profile_logic.canBecomeMentor(self.profile)
    self.assertTrue(can_become)

  def testForOrgAdmin(self):
    # make the profile an org admin for organization
    self.profile.is_mentor = True
    self.profile.mentor_for = [self.organization.key()]
    self.profile.is_org_admin = True
    self.profile.org_admin_for = [self.organization.key()]

    # profile with an org admin role can still become a mentor
    can_become = profile_logic.canBecomeMentor(self.profile)
    self.assertTrue(can_become)


class CanBecomeOrgAdminTest(unittest.TestCase):
  """Unit tests for canBecomeOrgAdmin function."""

  def setUp(self):
    # seed a new program
    self.program = seeder_logic.seed(GSoCProgram)

     # seed an organization
    self.organization = seeder_logic.seed(GSoCOrganization,
        {'program': self.program})

    # seed a new profile
    profile_properties = {
        'is_mentor': False,
        'mentor_for': [],
        'is_org_admin': False,
        'org_admin_for': [],
        'status': 'active',
        'is_student': False
    }
    self.profile = seeder_logic.seed(
        profile_model.GSoCProfile, profile_properties)

  def testForInvalidProfile(self):
    # make the profile invalid
    self.profile.status = 'invalid'
    self.profile.put()

    # invalid profiles cannot become org admins
    can_become = profile_logic.canBecomeOrgAdmin(self.profile)
    self.assertFalse(can_become)

  def testForStudentProfile(self):
    # make the profile a student
    self.profile.is_student = True
    self.profile.put()

    # student profiles cannot become org admins
    can_become = profile_logic.canBecomeOrgAdmin(self.profile)
    self.assertFalse(can_become)

  def testForLoneProfile(self):
    # profile with no roles can become org admins
    can_become = profile_logic.canBecomeOrgAdmin(self.profile)
    self.assertTrue(can_become)

  def testForMentor(self):
    # make the profile a mentor for organization
    self.profile.is_mentor = True
    self.profile.mentor_for = [self.organization.key()]

    # profile with a mentor role can become an org admin
    can_become = profile_logic.canBecomeOrgAdmin(self.profile)
    self.assertTrue(can_become)

  def testForOrgAdmin(self):
    # make the profile an org admin for organization
    self.profile.is_mentor = True
    self.profile.mentor_for = [self.organization.key()]
    self.profile.is_org_admin = True
    self.profile.org_admin_for = [self.organization.key()]

    # profile with an org admin role can still become an org admin
    can_become = profile_logic.canBecomeOrgAdmin(self.profile)
    self.assertTrue(can_become)

  def testForOrgAdminForAnotherOrg(self):
    # seed another organization
    organization_two = seeder_logic.seed(GSoCOrganization,
        {'program': self.program})

    # make the profile an org admin for organization two
    self.profile.is_mentor = True
    self.profile.mentor_for = [organization_two.key()]
    self.profile.is_org_admin = True
    self.profile.org_admin_for = [organization_two.key()]

    # profile with an org admin role can still become an org admin
    can_become = profile_logic.canBecomeOrgAdmin(self.profile)
    self.assertTrue(can_become)


class BecomeMentorForOrgTest(unittest.TestCase):
  """Unit tests for becomeMentorForOrg function."""

  def setUp(self):
    # seed a new program
    self.program = seeder_logic.seed(GSoCProgram)

     # seed a couple of organizations
    self.organization_one = seeder_logic.seed(GSoCOrganization,
        {'program': self.program})
    self.organization_two = seeder_logic.seed(GSoCOrganization,
        {'program': self.program})

    # seed a new profile
    profile_properties = {
        'is_mentor': False,
        'mentor_for': [],
        'is_org_admin': False,
        'org_admin_for': [],
        'status': 'active',
        'is_student': False
    }
    self.profile = seeder_logic.seed(
        profile_model.GSoCProfile, profile_properties)

  def testMentorAdded(self):
    profile_logic.becomeMentorForOrg(self.profile, self.organization_one.key())

    # the profile should be a mentor for organization one
    self.assertTrue(self.profile.is_mentor)
    self.assertIn(self.organization_one.key(), self.profile.mentor_for)

    # the profile is not a mentor for organization two
    self.assertNotIn(self.organization_two.key(), self.profile.mentor_for)

  def testMentorForAnotherOrgAdded(self):
    # make the profile a mentor for organization two
    self.profile.is_mentor = True
    self.profile.mentor_for = [self.organization_two.key()]
    self.profile.put()

    profile_logic.becomeMentorForOrg(self.profile, self.organization_one.key())

    # the profile should be a mentor for organization one
    self.assertTrue(self.profile.is_mentor)
    self.assertIn(self.organization_one.key(), self.profile.mentor_for)

  def testForExistingMentor(self):
    # make the profile a mentor for organization one
    self.profile.is_mentor = True
    self.profile.mentor_for = [self.organization_one.key()]
    self.profile.put()

    profile_logic.becomeMentorForOrg(self.profile, self.organization_one.key())

    # the profile should still be a mentor for organization one
    self.assertTrue(self.profile.is_mentor)
    self.assertIn(self.organization_one.key(), self.profile.mentor_for)

  def testForOrgAdminForAnotherOrgAdded(self):
    # make the profile an org admin for organization two
    self.profile.is_mentor = True
    self.profile.mentor_for = [self.organization_two.key()]
    self.profile.is_org_admin = True
    self.profile.org_admin_for = [self.organization_two.key()]
    self.profile.put()

    profile_logic.becomeMentorForOrg(self.profile, self.organization_one.key())

    # the profile should now be mentor for organization one
    self.assertTrue(self.profile.is_mentor)
    self.assertIn(self.organization_one.key(), self.profile.mentor_for)

  def testProfileNotAllowedToBecomeMentor(self):
    # make the profile a student
    self.profile.is_student = True
    self.profile.put()

    profile_logic.becomeMentorForOrg(self.profile, self.organization_one.key())

    # the profile should not become a mentor
    self.assertFalse(self.profile.is_mentor)
    self.assertNotIn(self.organization_one.key(), self.profile.mentor_for)

    # the profile should still be a student
    self.assertTrue(self.profile.is_student)


class BecomeOrgAdminForOrgTest(unittest.TestCase):
  """Unit tests for becomeOrgAdminForOrg function."""

  def _assertOrgAdmin(self, profile, org):
    self.assertTrue(profile.is_org_admin)
    self.assertIn(org.key(), profile.org_admin_for)
    self.assertTrue(profile.is_mentor)
    self.assertIn(org.key(), profile.mentor_for)

  def _assertNoRole(self, profile, org):
    self.assertNotIn(org.key(), profile.org_admin_for)
    if self.profile.is_org_admin:
      self.assertNotEqual(len(profile.org_admin_for), 0)
    else:
      self.assertEqual(profile.org_admin_for, [])

    self.assertNotIn(org.key(), profile.mentor_for)
    if self.profile.is_mentor:
      self.assertNotEqual(len(profile.mentor_for), 0)
    else:
      self.assertEqual(profile.mentor_for, [])

  def setUp(self):
    # seed a new program
    self.program = seeder_logic.seed(GSoCProgram)

     # seed a couple of organizations
    self.organization_one = seeder_logic.seed(GSoCOrganization,
        {'program': self.program})
    self.organization_two = seeder_logic.seed(GSoCOrganization,
        {'program': self.program})

    # seed a new profile
    profile_properties = {
        'is_mentor': False,
        'mentor_for': [],
        'is_org_admin': False,
        'org_admin_for': [],
        'status': 'active',
        'is_student': False
    }
    self.profile = seeder_logic.seed(
        profile_model.GSoCProfile, profile_properties)

  def testOrgAdminAdded(self):
    profile_logic.becomeOrgAdminForOrg(
        self.profile, self.organization_one.key())

    # profile should become org admin for organization one
    self._assertOrgAdmin(self.profile, self.organization_one)

    # profile should not have any role for organization two
    self._assertNoRole(self.profile, self.organization_two)

  def testMentorForAnotherOrgAdded(self):
    # make the profile a mentor for organization two
    self.profile.is_mentor = True
    self.profile.mentor_for = [self.organization_two.key()]
    self.profile.put()

    profile_logic.becomeOrgAdminForOrg(
        self.profile, self.organization_one.key())

    # profile should become org admin for organization one
    self._assertOrgAdmin(self.profile, self.organization_one)

    # profile should still be only mentor for organization two
    self.assertNotIn(self.organization_two.key(), self.profile.org_admin_for)
    self.assertTrue(self.profile.is_mentor)
    self.assertIn(self.organization_two.key(), self.profile.mentor_for)

  def testOrgAdminForAnotherOrgAdded(self):
    # make the profile an org admin for organization two
    self.profile.is_mentor = True
    self.profile.mentor_for = [self.organization_two.key()]
    self.profile.is_org_admin = True
    self.profile.org_admin_for = [self.organization_two.key()]
    self.profile.put()

    profile_logic.becomeOrgAdminForOrg(
        self.profile, self.organization_one.key())

    # profile should become org admin for organization one
    self._assertOrgAdmin(self.profile, self.organization_one)

    # profile should still be an org admin for organization two
    self._assertOrgAdmin(self.profile, self.organization_two)

  def testForExistingOrgAdmin(self):
    # make the profile an org admin for organization one
    self.profile.is_mentor = True
    self.profile.mentor_for = [self.organization_one.key()]
    self.profile.is_org_admin = True
    self.profile.org_admin_for = [self.organization_one.key()]
    self.profile.put()

    profile_logic.becomeOrgAdminForOrg(
        self.profile, self.organization_one.key())

    # profile should still be an org admin for organization one
    self._assertOrgAdmin(self.profile, self.organization_one)

  def testProfileNotAllowedToBecomeOrgAdmin(self):
    # make the profile a student
    self.profile.is_student = True
    self.profile.put()

    profile_logic.becomeOrgAdminForOrg(
        self.profile, self.organization_one.key())

    # the profile should not become org admin for ogranization one
    self._assertNoRole(self.profile, self.organization_one)

    # the profile should still be a student
    self.assertTrue(self.profile.is_student)
