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

from melange.logic import user as user_logic

from tests import profile_utils


TEST_ACCOUNT_ID = 'test_account_id'
TEST_EMAIL = 'test@example.com'
TEST_USERNAME = 'test_username'

class CreateUserTest(unittest.TestCase):
  """Unit tests for createUser function."""

  def testUserCreated(self):
    """Tests that user entity is created."""
    # sign in a user with an account but with no user entity
    profile_utils.signInToGoogleAccount(TEST_EMAIL, TEST_ACCOUNT_ID)

    result = user_logic.createUser(TEST_USERNAME)
    self.assertTrue(result)
    self.assertEqual(result.extra.key.id(), TEST_USERNAME)
    self.assertEqual(result.extra.account_id, TEST_ACCOUNT_ID)

  def testUserExists(self):
    """Tests that user entity is not existed for a taken username."""
    # seed a user with a specific username
    profile_utils.seedNDBUser(user_id=TEST_USERNAME)

    # sign in a user with an account but with no user entity
    profile_utils.signInToGoogleAccount(TEST_EMAIL, TEST_ACCOUNT_ID)

    result = user_logic.createUser(TEST_USERNAME)
    self.assertFalse(result)

  def testForNonLoggedInAccount(self):
    """Tests that user is not craeted when no account is logged in."""
    # make sure that nobody is logged in
    profile_utils.logout()

    result = user_logic.createUser(TEST_USERNAME)
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


class GetByAccountTest(unittest.TestCase):
  """Unit tests for getByAccount function."""

  def testUserEntityExists(self):
    """Tests that user entity is returned if it exists for the account."""
    