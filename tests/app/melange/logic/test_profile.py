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

"""Tests for profile logic."""

import datetime
import unittest

from google.appengine.ext import ndb

from melange.logic import profile as profile_logic
from melange.models import address as address_model
from melange.models import education as education_model
from melange.models import profile as ndb_profile_model
from melange.models import user as user_model

from soc.models import organization as org_model
from soc.models import profile as profile_model
from soc.models import program as program_model
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests import org_utils
from tests import profile_utils
from tests import program_utils


class CanResignAsOrgAdminForOrgTest(unittest.TestCase):
  """Unit tests for canResignAsOrgAdminForOrg function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    # seed a new program
    self.program = seeder_logic.seed(program_model.Program)

    # seed a couple of organizations
    self.organization_one = seeder_logic.seed(org_model.Organization,
        {'program': self.program})
    self.organization_two = seeder_logic.seed(org_model.Organization,
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
        profile_model.Profile, org_admin_properties)

  def testOnlyOrgAdmin(self):
    """Tests that the only org admin cannot resign."""
    can_resign = profile_logic.canResignAsOrgAdminForOrg(
        self.org_admin, self.organization_one.key())
    self.assertFalse(can_resign)
    self.assertEqual(can_resign.extra, profile_logic.ONLY_ORG_ADMIN)

  def testMoreOrgAdmins(self):
    """Tests that org admin can resign if there is another one."""
    org_admin_properties = {
        'is_mentor': True,
        'mentor_for': [self.organization_one.key()],
        'is_org_admin': True,
        'org_admin_for': [self.organization_one.key()],
        'status': 'active',
    }
    self.org_admin = seeder_logic.seed(
        profile_model.Profile, org_admin_properties)

    # now the org admin can resign, as there is another admin
    can_resign = profile_logic.canResignAsOrgAdminForOrg(
        self.org_admin, self.organization_one.key())
    self.assertTrue(can_resign)

  def testNotOrgAdminForOrg(self):
    """Tests that error is raised if the profile is not an org admin."""
    with self.assertRaises(ValueError):
      profile_logic.canResignAsOrgAdminForOrg(
          self.org_admin, self.organization_two.key())


class GetOrgAdminsTest(unittest.TestCase):
  """Unit tests for getOrgAdmins function."""

  def setUp(self):
    # seed a new program
    self.program = seeder_logic.seed(program_model.Program)

    # seed a couple of organizations
    self.organization_one = seeder_logic.seed(org_model.Organization,
        {'program': self.program})
    self.organization_two = seeder_logic.seed(org_model.Organization,
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
    org_admin = seeder_logic.seed(profile_model.Profile, org_admin_properties)

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
        profile_model.Profile, org_admin_properties).key())

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
    seeder_logic.seed(
        profile_model.Profile, org_admin_properties)

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
        profile_model.Profile, org_admin_properties)

    # seed female org admin for organization one
    org_admin_properties['gender'] = 'female'
    seeder_logic.seed(
        profile_model.Profile, org_admin_properties)

    # retrieve only org admins with extra attrs
    extra_attrs = {profile_model.Profile.gender: ['male']}
    org_admins = profile_logic.getOrgAdmins(self.organization_one.key(),
        extra_attrs=extra_attrs)

    # only the male org admin should be returned
    self.assertEqual(1, len(org_admins))
    self.assertEqual(org_admins[0].key(), org_admin.key())


class AssignNoRoleForOrgTest(unittest.TestCase):
  """Unit tests for assignNoRoleForOrg function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    # seed an organization
    self.org = seeder_logic.seed(org_model.Organization)

    # seed a profile
    self.profile = seeder_logic.seed(profile_model.Profile)

  def testForRoleForOneOrg(self):
    """Tests that the user does not have roles for organization anymore."""
    self.profile.is_mentor = True
    self.profile.mentor_for = [self.org.key()]
    self.profile.is_org_admin = True
    self.profile.org_admin_for = [self.org.key()]
    self.profile.put()

    profile_logic.assignNoRoleForOrg(self.profile, self.org.key())

    self.assertFalse(self.profile.is_mentor)
    self.assertListEqual(self.profile.mentor_for, [])
    self.assertFalse(self.profile.is_org_admin)
    self.assertListEqual(self.profile.org_admin_for, [])

  def testForRoleForManyOrgs(self):
    """Tests that the user still have roles for other organizations."""
    # seed another organization
    other_org = seeder_logic.seed(org_model.Organization)

    self.profile.is_mentor = True
    self.profile.mentor_for = [self.org.key(), other_org.key()]
    self.profile.is_org_admin = True
    self.profile.org_admin_for = [self.org.key()]
    self.profile.put()

    profile_logic.assignNoRoleForOrg(self.profile, self.org.key())

    self.assertTrue(self.profile.is_mentor)
    self.assertListEqual(self.profile.mentor_for, [other_org.key()])
    self.assertFalse(self.profile.is_org_admin)
    self.assertListEqual(self.profile.org_admin_for, [])


class AssignMentorRoleForOrgTest(unittest.TestCase):
  """Unit tests for assignMentorRoleForOrg function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    # seed a program
    self.program = program_utils.seedProgram()

    # seed an organization
    self.org = org_utils.seedOrganization(self.program.key())

    # seed a profile
    self.profile = profile_utils.seedNDBProfile(self.program.key())

  def testForUserWithNoRole(self):
    """Tests that a user with no role is promoted to a mentor role."""
    profile_logic.assignMentorRoleForOrg(self.profile, self.org.key)

    self.assertTrue(self.profile.is_mentor)
    self.assertListEqual(self.profile.mentor_for, [self.org.key])
    self.assertFalse(self.profile.is_admin)
    self.assertListEqual(self.profile.admin_for, [])

  def testForUserWithOrgAdminRole(self):
    """Tests that a user with org admin role is lowered to a mentor role."""
    self.profile.mentor_for = [self.org.key]
    self.profile.admin_for = [self.org.key]
    self.profile.put()

    profile_logic.assignMentorRoleForOrg(self.profile, self.org.key)

    self.assertTrue(self.profile.is_mentor)
    self.assertListEqual(self.profile.mentor_for, [self.org.key])
    self.assertFalse(self.profile.is_admin)
    self.assertListEqual(self.profile.admin_for, [])

  def testForOrgAdminForAnotherOrg(self):
    """Tests that a user is still org admin for another organization."""
    # seed another organization
    other_org = org_utils.seedOrganization(self.program.key())

    self.profile.mentor_for = [other_org.key]
    self.profile.admin_for = [other_org.key]
    self.profile.put()

    profile_logic.assignMentorRoleForOrg(self.profile, self.org.key)

    self.assertTrue(self.profile.is_mentor)
    self.assertIn(self.org.key, self.profile.mentor_for)
    self.assertIn(other_org.key, self.profile.mentor_for)
    self.assertTrue(self.profile.is_admin)
    self.assertListEqual(self.profile.admin_for, [other_org.key])


class AssignOrgAdminRoleForOrgTest(unittest.TestCase):
  """Unit tests for assignOrgAdminRoleForOrg function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    # seed a program
    self.program = program_utils.seedProgram()

    # seed an organization
    self.org = org_utils.seedOrganization(self.program.key())

    # seed a profile
    self.profile = profile_utils.seedNDBProfile(self.program.key())

  def testForUserWithNoRole(self):
    """Tests that a user with no role is promoted to an org admin role."""
    profile_logic.assignOrgAdminRoleForOrg(self.profile, self.org.key)

    self.assertTrue(self.profile.is_mentor)
    self.assertListEqual(self.profile.mentor_for, [self.org.key])
    self.assertTrue(self.profile.is_admin)
    self.assertListEqual(self.profile.admin_for, [self.org.key])

  def testForUserWithMentorRole(self):
    """Tests that a user with mentor role is promoted to an org admin role."""
    self.profile.mentor_for = [self.org.key]
    self.profile.put()

    profile_logic.assignOrgAdminRoleForOrg(self.profile, self.org.key)

    self.assertTrue(self.profile.is_mentor)
    self.assertListEqual(self.profile.mentor_for, [self.org.key])
    self.assertTrue(self.profile.is_admin)
    self.assertListEqual(self.profile.admin_for, [self.org.key])

  def testForMentorForAnotherOrg(self):
    """Tests that a user is still only a mentor for another organization."""
    # seed another organization
    other_org = org_utils.seedOrganization(self.program.key())

    self.profile.mentor_for = [other_org.key]
    self.profile.put()

    profile_logic.assignOrgAdminRoleForOrg(self.profile, self.org.key)

    self.assertTrue(self.profile.is_mentor)
    self.assertIn(self.org.key, self.profile.mentor_for)
    self.assertIn(other_org.key, self.profile.mentor_for)
    self.assertTrue(self.profile.is_admin)
    self.assertListEqual(self.profile.admin_for, [self.org.key])


class GetProfileForUsernameTest(unittest.TestCase):
  """Unit tests for getProfileForUsername function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    # seed a program
    self.program_key = seeder_logic.seed(program_model.Program).key()

    # seed a user
    self.user = profile_utils.seedNDBUser(user_id='test')

    # seed a profile
    self.profile = profile_utils.seedNDBProfile(
        self.program_key, user=self.user)

  def testForNoProfile(self):
    """Tests that no entity is returned when a user does not have a profile."""
    profile = profile_logic.getProfileForUsername('other', self.program_key)
    self.assertIsNone(profile)

  def testForOtherProgram(self):
    """Tests that no entity is returned for a different program."""
    other_program = seeder_logic.seed(program_model.Program)
    profile = profile_logic.getProfileForUsername('other', other_program.key())
    self.assertIsNone(profile)

  def testForExistingProfile(self):
    """Tests that profile is returned if exists."""
    profile = profile_logic.getProfileForUsername('test', self.program_key)
    self.assertEqual(profile.key, self.profile.key)


TEST_SPONSOR_ID = 'sponsor_id'
TEST_PROGRAM_ID = 'program_id'
TEST_PROFILE_ID = 'profile_id'

class GetProfileKeyTest(unittest.TestCase):
  """Unit tests for getProfileKey function."""

  def testProfileKey(self):
    """Tests that constructed profile key is correct."""
    key = profile_logic.getProfileKey(
        TEST_SPONSOR_ID, TEST_PROGRAM_ID, TEST_PROFILE_ID)
    self.assertEqual(
        key.id(),
        '%s/%s/%s' % (TEST_SPONSOR_ID, TEST_PROGRAM_ID, TEST_PROFILE_ID))
    self.assertEqual(key.kind(), ndb_profile_model.Profile._get_kind())
    self.assertEqual(key.parent().id(), TEST_PROFILE_ID)
    self.assertEqual(key.parent().kind(), user_model.User._get_kind())


TEST_FIRST_NAME = 'First'
TEST_LAST_NAME = 'Last'
TEST_PUBLIC_NAME = 'Public Name'
TEST_PHOTO_URL = 'http://www.test.photo.url.com'
TEST_BIRTH_DATE = datetime.date(1990, 1, 1)
TEST_STREET = 'Test street'
TEST_CITY = 'Test city'
TEST_COUNTRY = 'United States'
TEST_PROVINCE = 'California'
TEST_POSTAL_CODE = '90000'

TEST_RESIDENTIAL_ADDRESS = address_model.Address(
    street=TEST_STREET, city=TEST_CITY, country=TEST_COUNTRY,
    province=TEST_PROVINCE, postal_code=TEST_POSTAL_CODE)

TEST_PROFILE_PROPERTIES = {
    'first_name': TEST_FIRST_NAME,
    'last_name': TEST_LAST_NAME,
    'public_name': TEST_PUBLIC_NAME,
    'photo_url': TEST_PHOTO_URL,
    'birth_date': TEST_BIRTH_DATE,
    'residential_address': TEST_RESIDENTIAL_ADDRESS,
    }

class CreateProfileTest(unittest.TestCase):
  """Unit tests for createProfile function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.user = profile_utils.seedNDBUser()
    self.program = program_utils.seedProgram()

  def testProfileCreated(self):
    """Tests that profile entity is created."""
    result = profile_logic.createProfile(
        self.user.key, self.program.key(), TEST_PROFILE_PROPERTIES)

    # check that profile is returned
    self.assertTrue(result)

    # check that profile is persisted
    profile = result.extra.key.get()
    self.assertIsNotNone(profile)

    # check properties
    self.assertEqual(
        profile.key.id(),
        '%s/%s' % (self.program.key().name(), self.user.key.id()))
    self.assertEqual(profile.program.to_old_key(), self.program.key())
    self.assertEqual(profile.first_name, TEST_FIRST_NAME)
    self.assertEqual(profile.last_name, TEST_LAST_NAME)
    self.assertEqual(profile.photo_url, TEST_PHOTO_URL)
    self.assertEqual(profile.birth_date, TEST_BIRTH_DATE)
    self.assertEqual(profile.residential_address.street, TEST_STREET)
    self.assertEqual(profile.residential_address.city, TEST_CITY)
    self.assertEqual(profile.residential_address.country, TEST_COUNTRY)
    self.assertEqual(profile.residential_address.province, TEST_PROVINCE)
    self.assertEqual(profile.residential_address.postal_code, TEST_POSTAL_CODE)

  def testProfileExists(self):
    """Tests that second profile is not created for same user and program."""
    # seed a profile
    profile_utils.seedNDBProfile(self.program.key(), user=self.user)

    result = profile_logic.createProfile(
        self.user.key, self.program.key(), TEST_PROFILE_PROPERTIES)
    self.assertFalse(result)
    self.assertEqual(result.extra, profile_logic.PROFILE_EXISTS)


OTHER_TEST_FIRST_NAME = 'Other First'
OTHER_TEST_LAST_NAME = 'Other Last'
OTHER_TEST_PUBLIC_NAME = 'Other Public Name'
OTHER_TEST_PHOTO_URL = 'http://www.other.test.photo.url.com'
OTHER_TEST_BIRTH_DATE = datetime.date(1991, 1, 1)
OTHER_TEST_STREET = 'Test other street'
OTHER_TEST_CITY = 'Test city'
OTHER_TEST_COUNTRY = 'United States'
OTHER_TEST_PROVINCE = 'Alaska'
OTHER_TEST_POSTAL_CODE = '99503'

OTHER_TEST_RESIDENTIAL_ADDRESS = address_model.Address(
    street=OTHER_TEST_STREET, city=OTHER_TEST_CITY, country=OTHER_TEST_COUNTRY,
    province=OTHER_TEST_PROVINCE, postal_code=OTHER_TEST_POSTAL_CODE)

OTHER_TEST_PROFILE_PROPERTIES = {
    'first_name': OTHER_TEST_FIRST_NAME,
    'last_name': OTHER_TEST_LAST_NAME,
    'public_name': OTHER_TEST_PUBLIC_NAME,
    'photo_url': OTHER_TEST_PHOTO_URL,
    'birth_date': OTHER_TEST_BIRTH_DATE,
    'residential_address': OTHER_TEST_RESIDENTIAL_ADDRESS,
    }

class EditProfileTest(unittest.TestCase):
  """Unit tests for editProfile function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.user = profile_utils.seedNDBUser()
    self.program = program_utils.seedProgram()

    self.profile_key = ndb.Key(
      user_model.User._get_kind(), self.user.key.id(),
      ndb_profile_model.Profile._get_kind(),
      '%s/%s' % (self.program.key().name(), self.user.key.id()))

  def testProfileDoesNotExist(self):
    """Tests that error is raised when a profile does not exist."""
    result = profile_logic.editProfile(
        self.profile_key, TEST_PROFILE_PROPERTIES)
    self.assertFalse(result)
    self.assertEqual(
        result.extra,
        profile_logic.PROFILE_DOES_NOT_EXIST % self.profile_key.id())

  def testProfileUpdated(self):
    """Tests that profile properties are updated properly."""
    # seed a profile
    profile = profile_utils.seedNDBProfile(self.program.key(), user=self.user)
    result = profile_logic.editProfile(
        profile.key, OTHER_TEST_PROFILE_PROPERTIES)
    self.assertTrue(result)

    # check that updated profile is persisted
    profile = result.extra.key.get()
    self.assertIsNotNone(profile)

    # check properties
    self.assertEqual(
        profile.key.id(),
        '%s/%s' % (self.program.key().name(), self.user.key.id()))
    self.assertEqual(profile.program.to_old_key(), self.program.key())
    self.assertEqual(profile.first_name, OTHER_TEST_FIRST_NAME)
    self.assertEqual(profile.last_name, OTHER_TEST_LAST_NAME)
    self.assertEqual(profile.photo_url, OTHER_TEST_PHOTO_URL)
    self.assertEqual(profile.birth_date, OTHER_TEST_BIRTH_DATE)
    self.assertEqual(profile.residential_address.street, OTHER_TEST_STREET)
    self.assertEqual(profile.residential_address.city, OTHER_TEST_CITY)
    self.assertEqual(profile.residential_address.country, OTHER_TEST_COUNTRY)
    self.assertEqual(profile.residential_address.province, OTHER_TEST_PROVINCE)
    self.assertEqual(
        profile.residential_address.postal_code, OTHER_TEST_POSTAL_CODE)


TEST_SCHOOL_COUNTRY = 'United States'
TEST_SCHOOL_ID = 'Melange University'
TEST_EXPECTED_GRADUATION = datetime.date.today().year
TEST_EDUCATION_PROPERTIES = {
    'school_country': TEST_SCHOOL_COUNTRY,
    'school_id': TEST_SCHOOL_ID,
    'expected_graduation': TEST_EXPECTED_GRADUATION
    }
TEST_EDUCATION = education_model.Education(**TEST_EDUCATION_PROPERTIES)
TEST_STUDENT_DATA_PROPERTIES = {
    'education': TEST_EDUCATION
    }

class CreateStudentDataTest(unittest.TestCase):
  """Unit tests for createStudentData function."""

  def testStudentDataCreated(self):
    """Tests that student data is created properly if all data is valid."""
    student_data = profile_logic.createStudentData(TEST_STUDENT_DATA_PROPERTIES)

    # check properties
    self.assertDictEqual(
        student_data.education.to_dict(), TEST_EDUCATION_PROPERTIES)
