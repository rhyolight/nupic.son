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

"""Tests for user logic."""

import unittest

from google.appengine.ext import ndb

from melange.logic import user as user_logic

from tests import profile_utils
from tests import program_utils


TEST_ACCOUNT_ID = 'test_account_id'
TEST_EMAIL = 'test@example.com'
TEST_USERNAME = 'test_username'

class CreateUserTest(unittest.TestCase):
  """Unit tests for createUser function."""

  def testUserCreated(self):
    """Tests that user entity is created."""
    program = program_utils.seedProgram()
    # sign in a user with an account but with no user entity
    profile_utils.signInToGoogleAccount(TEST_EMAIL, TEST_ACCOUNT_ID)

    result = ndb.transaction(
        lambda: user_logic.createUser(
            TEST_USERNAME,
            host_for=[ndb.Key.from_old_key(program.key())]))

    self.assertTrue(result)
    self.assertEqual(result.extra.key.id(), TEST_USERNAME)
    self.assertEqual(result.extra.account_id, TEST_ACCOUNT_ID)
    self.assertIn(
        ndb.Key.from_old_key(program.key()), result.extra.host_for)

  def testUserExists(self):
    """Tests that user entity is not existed for a taken username."""
    # seed a user with a specific username
    profile_utils.seedNDBUser(user_id=TEST_USERNAME)

    # sign in a user with an account but with no user entity
    profile_utils.signInToGoogleAccount(TEST_EMAIL, TEST_ACCOUNT_ID)

    result = ndb.transaction(lambda: user_logic.createUser(TEST_USERNAME))
    self.assertFalse(result)

  def testForNonLoggedInAccount(self):
    """Tests that user is not created when no account is logged in."""
    # make sure that nobody is logged in
    profile_utils.logout()

    result = ndb.transaction(lambda: user_logic.createUser(TEST_USERNAME))
    self.assertFalse(result)


class GetByCurrentAccountTest(unittest.TestCase):
  """Unit tests for getByCurrentAccount function."""

  def testForLoggedInAccountWithNoUserEntity(self):
    """Tests that None is returned for a logged-in user with no entity."""
    # sign in a user with an account but with no user entity
    profile_utils.signInToGoogleAccount(TEST_EMAIL, TEST_ACCOUNT_ID)

    result = user_logic.getByCurrentAccount()
    self.assertIsNone(result)

  def testForLoggedInAccountWithUserEntity(self):
    """Tests that user entity is returned for a logged-in user with entity."""
    # seed a user entity and log them in
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)

    result = user_logic.getByCurrentAccount()
    self.assertIsNotNone(result)
    self.assertEqual(user.key, result.key)
    self.assertEqual(user.account_id, result.account_id)

  def testForNonLoggedInAccount(self):
    """Tests that None is returned for a not logged-in user."""
    # seed a user but make sure that nobody is logged in
    profile_utils.seedNDBUser()
    profile_utils.logout()

    result = user_logic.getByCurrentAccount()
    self.assertIsNone(result)


class IsHostForProgramTest(unittest.TestCase):
  """Unit tests for isHostForProgram function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.user = profile_utils.seedNDBUser()

  def testIsHostForProgram(self):
    """Tests that True is returned for a program host."""
    # seed a couple of programs
    program_one = program_utils.seedProgram()
    program_two = program_utils.seedProgram()

    # make the user a host for the first program but not for the other
    self.user.host_for = [ndb.Key.from_old_key(program_one.key())]
    self.user.put()

    # check that the user is a host only for the first program
    self.assertTrue(user_logic.isHostForProgram(self.user, program_one.key()))
    self.assertFalse(user_logic.isHostForProgram(self.user, program_two.key()))


class GetHostsForProgramTest(unittest.TestCase):
  """Unit tests for getHostsForProgram function."""

  def testGetHostsForProgram(self):
    """Tests if a correct user entities are returned."""
    program_one = program_utils.seedProgram()
    program_two = program_utils.seedProgram()

    # seed hosts for the program one
    hosts = set()
    for _ in range(3):
      user_entity = profile_utils.seedNDBUser(host_for=[program_one])
      hosts.add(user_entity.key)

    # seed hosts for the program two
    for _ in range(2):
      user_entity = profile_utils.seedNDBUser(host_for=[program_two])

    # check that correct hosts for program one are returned
    actual_hosts = user_logic.getHostsForProgram(program_one.key())
    self.assertSetEqual(hosts, set(host.key for host in actual_hosts))
