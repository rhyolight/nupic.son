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

from google.appengine.ext import blobstore

from melange.models import profile as profile_model

from soc.modules.gsoc.logic import profile as profile_logic

from tests import org_utils
from tests import profile_utils
from tests import program_utils
from tests.utils import project_utils
from tests.utils import proposal_utils


class ProfileTest(unittest.TestCase):
  """Tests the GSoC logic for profiles.
  """

  def setUp(self):
    self.program = program_utils.seedGSoCProgram()
    self.foo_organization = org_utils.seedSOCOrganization(self.program.key())

    # create mentors for foo_organization.
    self.foo_mentors = []
    for _ in range(5):
      mentor = profile_utils.seedNDBProfile(
          self.program.key(), mentor_for=[self.foo_organization.key])
      self.foo_mentors.append(mentor)

    # create organization admins for foo_organization.
    self.foo_org_admins = []
    for _ in range(5):
      org_admin = profile_utils.seedNDBProfile(
          self.program.key(), admin_for=[self.foo_organization.key])
      self.foo_org_admins.append(org_admin)

    # create another organization bar_organization for our program.
    self.bar_organization = org_utils.seedSOCOrganization(self.program.key())

    # assign mentors for bar_organization.
    self.bar_mentors = []
    for _ in range(5):
      mentor = profile_utils.seedNDBProfile(
          self.program.key(), mentor_for=[self.bar_organization.key])
      self.bar_mentors.append(mentor)

    # assign an organization admin for bar_organization
    self.bar_org_admin = profile_utils.seedNDBProfile(
        self.program.key(), admin_for=[self.bar_organization.key])


  def testQueryAllMentorsKeysForOrg(self):
    """Tests that a list of keys for all the mentors in an organization are
    returned.
    """
    def runTest(org, mentors, org_admins):
      """Runs the test.
      """
      mentor_keys = [entity.key for entity in mentors]
      org_admin_keys = [entity.key for entity in org_admins]
      expected_keys = set(mentor_keys + org_admin_keys)
      actual_keys = set(profile_logic.queryAllMentorsKeysForOrg(org.key))
      self.assertSetEqual(expected_keys, actual_keys)

    # Test for foo_organization
    mentors = self.foo_mentors
    org_admins = self.foo_org_admins
    org = self.foo_organization
    runTest(org, mentors, org_admins)

    # Test the same for bar_organization
    mentors = self.bar_mentors
    org_admins = [self.bar_org_admin]
    org = self.bar_organization
    runTest(org, mentors, org_admins)

    # Create an organization which has no mentors and org_admins and test that
    # an empty list is returned.
    org = org_utils.seedSOCOrganization(self.program.key())
    mentors = []
    org_admins = []
    runTest(org, mentors, org_admins)


class CanResignAsMentorForOrgTest(unittest.TestCase):
  """Unit tests for canResignAsMentorForOrg function."""

  def setUp(self):
    # seed a new program
    self.program = program_utils.seedGSoCProgram()

    # seed a couple of organizations
    self.organization_one = org_utils.seedSOCOrganization(self.program.key())
    self.organization_two = org_utils.seedSOCOrganization(self.program.key())

    # seed a new mentor for organization one
    self.mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.organization_one.key])

  def testMentorCanResign(self):
    # mentor is not involved in organization one
    can_resign = profile_logic.canResignAsMentorForOrg(
        self.mentor, self.organization_one.key)
    self.assertTrue(can_resign)

  def testMentorWithProject(self):
    # seed a student
    student = profile_utils.seedSOCStudent(self.program)

    # seed a project for organization one
    project_utils.seedProject(
        student, self.program.key(),
        org_key=self.organization_one.key, mentor_key=self.mentor.key)

    # mentor is involved in organization one because of a project
    can_resign = profile_logic.canResignAsMentorForOrg(
        self.mentor, self.organization_one.key)
    self.assertFalse(can_resign)

    # add mentor role for organization two
    self.mentor.mentor_for.append(self.organization_two.key)

    # mentor is not involved in organization two
    can_resign = profile_logic.canResignAsMentorForOrg(
        self.mentor, self.organization_two.key)
    self.assertTrue(can_resign)

  def testMentorWithProposal(self):
    # seed a new proposal and assign our mentor
    student = profile_utils.seedSOCStudent(self.program)
    proposal_utils.seedProposal(
        student.key, self.program.key(),
        org_key=self.organization_one.key, mentor_key=self.mentor.key)

    # mentor is involved in organization one because of a proposal
    can_resign = profile_logic.canResignAsMentorForOrg(
        self.mentor, self.organization_one.key)
    self.assertFalse(can_resign)

    # add mentor role for organization two
    self.mentor.mentor_for.append(self.organization_two.key)

    # mentor is not involved in organization two
    can_resign = profile_logic.canResignAsMentorForOrg(
        self.mentor, self.organization_two.key)
    self.assertTrue(can_resign)

  def testNotMentorForOrg(self):
    # profile is not a mentor for organization two
    with self.assertRaises(ValueError):
      profile_logic.canResignAsMentorForOrg(
          self.mentor, self.organization_two.key)


class ResignAsOrgAdminForOrgTest(unittest.TestCase):
  """Unit tests for resignAsOrgAdminForOrg function."""

  def setUp(self):
    # seed a new program
    self.program = program_utils.seedGSoCProgram()

    # seed a couple of organizations
    self.organization = org_utils.seedSOCOrganization(self.program.key())
    org_utils.seedSOCOrganization(self.program.key())

    # seed a new org admin for organization
    self.org_admin = profile_utils.seedNDBProfile(
        self.program.key(), admin_for=[self.organization.key])

  def testForOnlyOrgAdmin(self):
    profile_logic.resignAsOrgAdminForOrg(
        self.org_admin, self.organization.key)

    # the profile should still be an org admin
    self.assertTrue(self.org_admin.is_admin)
    self.assertIn(self.organization.key, self.org_admin.admin_for)

  def testForTwoOrgAdmins(self):
    # seed another org admin for organization
    profile_utils.seedNDBProfile(
        self.program.key(), admin_for=[self.organization.key])

    profile_logic.resignAsOrgAdminForOrg(self.org_admin, self.organization.key)

    # the profile should not be an org admin anymore
    self.assertFalse(self.org_admin.is_admin)
    self.assertNotIn(self.organization.key, self.org_admin.admin_for)

  def testForOrgAdminForTwoOrgs(self):
    # seed another org admin for organization
    profile_utils.seedNDBProfile(
        self.program.key(), admin_for=[self.organization.key])

    # seed another organization
    organization_two = org_utils.seedSOCOrganization(self.program.key())

    # make the profile an org admin for organization two
    self.org_admin.mentor_for.append(organization_two.key)
    self.org_admin.admin_for.append(organization_two.key)

    profile_logic.resignAsOrgAdminForOrg(self.org_admin, self.organization.key)

    # the profile is not an org admin for organization anymore
    self.assertNotIn(self.organization.key, self.org_admin.admin_for)

    # the profile should still be an org admin for organization two
    self.assertTrue(self.org_admin.is_admin)
    self.assertIn(organization_two.key, self.org_admin.admin_for)


class CountOrgAdminsTest(unittest.TestCase):
  """Unit tests for countOrgAdmins function."""

  def setUp(self):
    # seed a new program
    self.program = program_utils.seedGSoCProgram()

    # seed a couple of organizations
    self.organization_one = org_utils.seedSOCOrganization(self.program.key())
    self.organization_two = org_utils.seedSOCOrganization(self.program.key())

  def testNoOrgAdmin(self):
    number = profile_logic.countOrgAdmins(self.organization_one.key)
    self.assertEqual(number, 0)

  def testManyOrgAdmins(self):
    # seed  org admins for organization one
    for _ in range(5):
      profile_utils.seedNDBProfile(
          self.program.key(), admin_for=[self.organization_one.key])

    # seed  org admins for organization two
    for _ in range(3):
      profile_utils.seedNDBProfile(
          self.program.key(), admin_for=[self.organization_two.key])

    # all org admins for organization one should be returned
    number = profile_logic.countOrgAdmins(self.organization_one.key)
    self.assertEqual(number, 5)

    # all org admins for organization two should be returned
    number = profile_logic.countOrgAdmins(self.organization_two.key)
    self.assertEqual(number, 3)

  def testNotActiveOrgAdmin(self):
    # seed invalid org admin for organization one
    profile_utils.seedNDBProfile(
        self.program.key(), admin_for=[self.organization_one.key],
        status=profile_model.Status.BANNED)

    # seed the other org admin who is active
    profile_utils.seedNDBProfile(
        self.program.key(), admin_for=[self.organization_one.key])

    # only active org admin counted
    org_admins = profile_logic.countOrgAdmins(self.organization_one.key)
    self.assertEqual(org_admins, 1)


class GetMentorsTest(unittest.TestCase):
  """Unit tests for getMentors function."""

  def setUp(self):
    # seed a new program
    self.program = program_utils.seedGSoCProgram()

    # seed a couple of organizations
    self.organization_one = org_utils.seedSOCOrganization(self.program.key())
    self.organization_two = org_utils.seedSOCOrganization(self.program.key())

  def testNoMentors(self):
    mentors = profile_logic.getOrgAdmins(self.organization_one.key)
    self.assertEqual(mentors, [])

  def testOneMentor(self):
    # seed a new mentor for organization one
    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.organization_one.key])

    # the mentor should be returned
    mentors = profile_logic.getMentors(self.organization_one.key)
    self.assertEqual(len(mentors), 1)
    self.assertEqual(mentors[0].key, mentor.key)

    # keys_only set to True should return only the key
    mentor_keys = profile_logic.getMentors(
        self.organization_one.key, keys_only=True)
    self.assertEqual(len(mentor_keys), 1)
    self.assertEqual(mentor_keys[0], mentor.key)

    # there is still no mentor for organization two
    mentors = profile_logic.getMentors(self.organization_two.key)
    self.assertEqual(mentors, [])

  def testManyMentors(self):
    seeded_mentors = set()
    for _ in range(5):
      seeded_mentors.add(
          profile_utils.seedNDBProfile(
              self.program.key(), mentor_for=[self.organization_one.key]).key)

    # all mentors should be returned
    mentors = profile_logic.getMentors(self.organization_one.key)
    self.assertEqual(len(mentors), 5)
    self.assertEqual(seeded_mentors, set([mentor.key for mentor in mentors]))

    # all mentors keys should be returned if keys_only set
    mentor_keys = profile_logic.getMentors(
        self.organization_one.key, keys_only=True)
    self.assertEqual(len(mentor_keys), 5)
    self.assertEqual(seeded_mentors, set(mentor_keys))

  def testNotActiveMentor(self):
    # seed invalid mentor for organization one
    profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.organization_one.key],
        status=profile_model.Status.BANNED)

    # not active mentor not returned
    mentors = profile_logic.getMentors(self.organization_one.key)
    self.assertEqual(mentors, [])

    # keys_only set to True does not return any keys
    mentors_keys = profile_logic.getMentors(
        self.organization_one.key, keys_only=True)
    self.assertEqual(mentors_keys, [])

  def testExtraAttrs(self):
    # seed female mentor for organization one
    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.organization_one.key],
        gender=profile_model.Gender.FEMALE)

    # seed male mentor for organization one
    profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.organization_one.key],
        gender=profile_model.Gender.MALE)

    # retrieve only mentors with extra attrs
    extra_attrs = {profile_model.Profile.gender: [profile_model.Gender.FEMALE]}
    mentors = profile_logic.getMentors(
        self.organization_one.key, extra_attrs=extra_attrs)

    # only the female mentor should be returned
    self.assertEqual(1, len(mentors))
    self.assertEqual(mentors[0].key, mentor.key)

  def testForOrgAdmin(self):
    # seed a new org admin for organization one
    org_admin = profile_utils.seedNDBProfile(
        self.program.key(), admin_for=[self.organization_one.key])

    # the org admin should be returned as it is also a mentor
    mentors = profile_logic.getMentors(self.organization_one.key)
    self.assertEqual(len(mentors), 1)
    self.assertEqual(mentors[0].key, org_admin.key)

    # keys_only set to True should return only the key
    mentor_keys = profile_logic.getMentors(
        self.organization_one.key, keys_only=True)
    self.assertEqual(len(mentor_keys), 1)
    self.assertEqual(mentor_keys[0], org_admin.key)


class ResignAsMentorForOrgTest(unittest.TestCase):
  """Unit tests for resignAsMentorForOrg function."""

  def setUp(self):
    # seed a new program
    self.program = program_utils.seedGSoCProgram()

    # seed a couple of organizations
    self.organization = org_utils.seedSOCOrganization(self.program.key())

    # seed a new mentor for organization one
    self.mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.organization.key],
        gender=profile_model.Gender.FEMALE)

  def testForOrgAdmin(self):
    # make the profile an org admin for organization
    self.mentor.admin_for = [self.organization.key]
    self.mentor.put()

    profile_logic.resignAsMentorForOrg(self.mentor, self.organization.key)

    # the profile should still be a mentor because of being org admin
    self.assertTrue(self.mentor.is_mentor)
    self.assertIn(self.organization.key, self.mentor.mentor_for)

  def testForMentorWithoutProject(self):
    profile_logic.resignAsMentorForOrg(self.mentor, self.organization.key)

    # the profile is not a mentor anymore
    self.assertFalse(self.mentor.is_mentor)
    self.assertNotIn(self.organization.key, self.mentor.mentor_for)

  def testForMentorWithProject(self):
    # seed a project for organization one and set a mentor
    student = profile_utils.seedSOCStudent(self.program)
    project_utils.seedProject(
        student, self.program.key(),
        org_key=self.organization.key, mentor_key=self.mentor.key)

    profile_logic.resignAsMentorForOrg(self.mentor, self.organization.key)

    # the profile should still be a mentor because of the project
    self.assertTrue(self.mentor.is_mentor)
    self.assertIn(self.organization.key, self.mentor.mentor_for)

  def testForMentorForTwoOrgs(self):
    # seed another organization
    organization_two = org_utils.seedSOCOrganization(self.program.key())

    # make the profile a mentor for organization two
    self.mentor.mentor_for.append(organization_two.key)
    self.mentor.put()

    profile_logic.resignAsMentorForOrg(self.mentor, self.organization.key)

    # the profile is not a mentor for organization anymore
    self.assertNotIn(self.organization.key, self.mentor.mentor_for)

    # the profile should still be a mentor for organization_two
    self.assertTrue(self.mentor.is_mentor)
    self.assertIn(organization_two.key, self.mentor.mentor_for)


class CanBecomeMentorTest(unittest.TestCase):
  """Unit tests for canBecomeMentor function."""

  def setUp(self):
    # seed a new program
    self.program = program_utils.seedGSoCProgram()

    # seed an organization
    self.organization = org_utils.seedSOCOrganization(self.program.key())

    # seed a new profile
    self.profile = profile_utils.seedNDBProfile(self.program.key())

  def testForInvalidProfile(self):
    # make the profile invalid
    self.profile.status = profile_model.Status.BANNED
    self.profile.put()

    # invalid profiles cannot become mentors
    can_become = profile_logic.canBecomeMentor(self.profile)
    self.assertFalse(can_become)

  def testForStudentProfile(self):
    # make the profile invalid
    profile = profile_utils.seedSOCStudent(self.program)

    # student profiles cannot become mentors
    can_become = profile_logic.canBecomeMentor(profile)
    self.assertFalse(can_become)

  def testForLoneProfile(self):
    # profile with no roles can become mentors
    can_become = profile_logic.canBecomeMentor(self.profile)
    self.assertTrue(can_become)

  def testForMentor(self):
    # make the profile a mentor for organization
    self.profile.mentor_for = [self.organization.key]
    self.profile.put()

    # profile with a mentor role can still become a mentor
    can_become = profile_logic.canBecomeMentor(self.profile)
    self.assertTrue(can_become)

  def testForOrgAdmin(self):
    # make the profile an org admin for organization
    profile = profile_utils.seedNDBProfile(
        self.program.key(), admin_for=[self.organization.key])

    # profile with an org admin role can still become a mentor
    can_become = profile_logic.canBecomeMentor(profile)
    self.assertTrue(can_become)


class CanBecomeOrgAdminTest(unittest.TestCase):
  """Unit tests for canBecomeOrgAdmin function."""

  def setUp(self):
    # seed a new program
    self.program = program_utils.seedGSoCProgram()

    # seed an organization
    self.organization = org_utils.seedSOCOrganization(self.program.key())

  def testForInvalidProfile(self):
    profile = profile_utils.seedNDBProfile(
        self.program.key(), status=profile_model.Status.BANNED)

    # invalid profiles cannot become org admins
    can_become = profile_logic.canBecomeOrgAdmin(profile)
    self.assertFalse(can_become)

  def testForStudentProfile(self):
    profile = profile_utils.seedSOCStudent(self.program)

    # student profiles cannot become org admins
    can_become = profile_logic.canBecomeOrgAdmin(profile)
    self.assertFalse(can_become)

  def testForLoneProfile(self):
    profile = profile_utils.seedNDBProfile(self.program.key())

    # profile with no roles can become org admins
    can_become = profile_logic.canBecomeOrgAdmin(profile)
    self.assertTrue(can_become)

  def testForMentor(self):
    profile = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.organization.key])

    # profile with a mentor role can become an org admin
    can_become = profile_logic.canBecomeOrgAdmin(profile)
    self.assertTrue(can_become)

  def testForOrgAdmin(self):
    profile = profile_utils.seedNDBProfile(
        self.program.key(), admin_for=[self.organization.key])

    # profile with an org admin role can still become an org admin
    can_become = profile_logic.canBecomeOrgAdmin(profile)
    self.assertTrue(can_become)

  def testForOrgAdminForAnotherOrg(self):
    # seed another organization
    organization_two = org_utils.seedSOCOrganization(self.program.key())

    profile = profile_utils.seedNDBProfile(
        self.program.key(), admin_for=[organization_two.key])

    # profile with an org admin role can still become an org admin
    can_become = profile_logic.canBecomeOrgAdmin(profile)
    self.assertTrue(can_become)


class BecomeMentorForOrgTest(unittest.TestCase):
  """Unit tests for becomeMentorForOrg function."""

  def setUp(self):
    # seed a new program
    self.program = program_utils.seedGSoCProgram()

    # seed a couple of organizations
    self.organization_one = org_utils.seedSOCOrganization(self.program.key())
    self.organization_two = org_utils.seedSOCOrganization(self.program.key())

  def testMentorAdded(self):
    profile = profile_utils.seedNDBProfile(self.program.key())

    profile_logic.becomeMentorForOrg(profile, self.organization_one.key)

    # the profile should be a mentor for organization one
    self.assertTrue(profile.is_mentor)
    self.assertIn(self.organization_one.key, profile.mentor_for)

    # the profile is not a mentor for organization two
    self.assertNotIn(self.organization_two.key, profile.mentor_for)

  def testMentorForAnotherOrgAdded(self):
    profile = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.organization_two.key])

    profile_logic.becomeMentorForOrg(profile, self.organization_one.key)

    # the profile should be a mentor for organization one
    self.assertTrue(profile.is_mentor)
    self.assertIn(self.organization_one.key, profile.mentor_for)

  def testForExistingMentor(self):
    profile = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.organization_one.key])

    profile_logic.becomeMentorForOrg(profile, self.organization_one.key)

    # the profile should still be a mentor for organization one
    self.assertTrue(profile.is_mentor)
    self.assertIn(self.organization_one.key, profile.mentor_for)

  def testForOrgAdminForAnotherOrgAdded(self):
    profile = profile_utils.seedNDBProfile(
        self.program.key(), admin_for=[self.organization_two.key])

    profile_logic.becomeMentorForOrg(profile, self.organization_one.key)

    # the profile should now be mentor for organization one
    self.assertTrue(profile.is_mentor)
    self.assertIn(self.organization_one.key, profile.mentor_for)

  def testProfileNotAllowedToBecomeMentor(self):
    profile = profile_utils.seedSOCStudent(self.program)

    profile_logic.becomeMentorForOrg(profile, self.organization_one.key)

    # the profile should not become a mentor
    self.assertFalse(profile.is_mentor)
    self.assertNotIn(self.organization_one.key, profile.mentor_for)

    # the profile should still be a student
    self.assertTrue(profile.is_student)


class BecomeOrgAdminForOrgTest(unittest.TestCase):
  """Unit tests for becomeOrgAdminForOrg function."""

  def _assertOrgAdmin(self, profile, org):
    self.assertTrue(profile.is_admin)
    self.assertIn(org.key, profile.admin_for)
    self.assertTrue(profile.is_mentor)
    self.assertIn(org.key, profile.mentor_for)

  def _assertNoRole(self, profile, org):
    self.assertNotIn(org.key, profile.admin_for)
    if profile.is_admin:
      self.assertNotEqual(len(profile.admin_for), 0)
    else:
      self.assertEqual(profile.admin_for, [])

    self.assertNotIn(org.key, profile.mentor_for)
    if profile.is_mentor:
      self.assertNotEqual(len(profile.mentor_for), 0)
    else:
      self.assertEqual(profile.mentor_for, [])

  def setUp(self):
    # seed a new program
    self.program = program_utils.seedGSoCProgram()

    # seed a couple of organizations
    self.organization_one = org_utils.seedSOCOrganization(self.program.key())
    self.organization_two = org_utils.seedSOCOrganization(self.program.key())

  def testOrgAdminAdded(self):
    profile = profile_utils.seedNDBProfile(self.program.key())
    profile_logic.becomeOrgAdminForOrg(profile, self.organization_one.key)

    # profile should become org admin for organization one
    self._assertOrgAdmin(profile, self.organization_one)

    # profile should not have any role for organization two
    self._assertNoRole(profile, self.organization_two)

  def testMentorForAnotherOrgAdded(self):
    profile = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.organization_two.key])

    profile_logic.becomeOrgAdminForOrg(profile, self.organization_one.key)

    # profile should become org admin for organization one
    self._assertOrgAdmin(profile, self.organization_one)

    # profile should still be only mentor for organization two
    self.assertNotIn(
        self.organization_two.key, profile.admin_for)
    self.assertTrue(profile.is_mentor)
    self.assertIn(self.organization_two.key, profile.mentor_for)

  def testOrgAdminForAnotherOrgAdded(self):
    profile = profile_utils.seedNDBProfile(
        self.program.key(), admin_for=[self.organization_two.key])

    profile_logic.becomeOrgAdminForOrg(profile, self.organization_one.key)

    # profile should become org admin for organization one
    self._assertOrgAdmin(profile, self.organization_one)

    # profile should still be an org admin for organization two
    self._assertOrgAdmin(profile, self.organization_two)

  def testForExistingOrgAdmin(self):
    profile = profile_utils.seedNDBProfile(
        self.program.key(), admin_for=[self.organization_one.key])

    profile_logic.becomeOrgAdminForOrg(profile, self.organization_one.key)

    # profile should still be an org admin for organization one
    self._assertOrgAdmin(profile, self.organization_one)

  def testProfileNotAllowedToBecomeOrgAdmin(self):
    profile = profile_utils.seedSOCStudent(self.program)

    profile_logic.becomeOrgAdminForOrg(profile, self.organization_one.key)

    # the profile should not become org admin for ogranization one
    self._assertNoRole(profile, self.organization_one)

    # the profile should still be a student
    self.assertTrue(profile.is_student)


class AllFormsSubmittedTest(unittest.TestCase):
  """Unit tests for areFormsSubmitted function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    program = program_utils.seedProgram()
    self.profile = profile_utils.seedSOCStudent(program)

  def testNoAllFormsSubmitted(self):
    """Tests when no all required forms has been submitted."""
    # no forms are submitted
    forms_submitted = profile_logic.allFormsSubmitted(self.profile.student_data)
    self.assertFalse(forms_submitted)

    # only tax form is submitted
    self.profile.student_data.tax_form = blobstore.BlobKey('fake key')
    self.profile.put()
    forms_submitted = profile_logic.allFormsSubmitted(self.profile.student_data)
    self.assertFalse(forms_submitted)

    # only enrollment form is submitted
    self.profile.student_data.tax_form = None
    self.profile.student_data.enrollment_form = blobstore.BlobKey('fake key')
    forms_submitted = profile_logic.allFormsSubmitted(self.profile.student_data)
    self.assertFalse(forms_submitted)

  def testAllFormsSubmitted(self):
    """Tests when all required forms has been submitted."""
    # both forms are submitted
    self.profile.student_data.tax_form = blobstore.BlobKey('fake key')
    self.profile.student_data.enrollment_form = blobstore.BlobKey('fake key')
    forms_submitted = profile_logic.allFormsSubmitted(self.profile.student_data)
    self.assertTrue(forms_submitted)
