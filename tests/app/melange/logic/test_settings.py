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

"""Tests for settings logic."""

import unittest

from google.appengine.ext import ndb

from melange.logic import settings as settings_logic
from melange.models import settings as settings_model

from tests import profile_utils


class SetUserSettingsTest(unittest.TestCase):
  """Unit tests for setUserSettings function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.user_key = profile_utils.seedNDBUser().key

  def testForNonExistingSettings(self):
    """Tests that new entity is created if there is not one."""
    test_key = ndb.Key('User', 'test_user')
    user_settings = settings_logic.setUserSettings(
        self.user_key, view_as=test_key)

    # check that settings are returned
    self.assertIsNotNone(user_settings)

    # check that property is set correctly
    self.assertEqual(user_settings.view_as, test_key)

  def testForExistingSettings(self):
    """Tests that existing entity is updated."""
    # seed user settings
    properties = {'view_as': ndb.Key('User', 'test_user')}
    user_settings = settings_model.UserSettings(
        parent=self.user_key, **properties).put()

    other_key = ndb.Key('User', 'other_user')
    updated_settings = settings_logic.setUserSettings(
        self.user_key, view_as=other_key)

    # check that no new entity is created
    self.assertEqual(user_settings, updated_settings.key)

    # check that property is updated correctly
    self.assertEqual(updated_settings.view_as, other_key)


class GetUserSettingsTest(unittest.TestCase):
  """Unit tests for getUserSettings function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.user_key = profile_utils.seedNDBUser().key

  def testForNonExistingSettings(self):
    """Tests that new entity is created and returned if there is not one."""
    user_settings = settings_logic.getUserSettings(self.user_key)

    # check that settings are created and returned
    self.assertIsNotNone(user_settings)

  def testForExistingSettings(self):
    """Tests that existing settings are returned if entity exists."""
    # seed user settings
    properties = {'view_as': ndb.Key('User', 'test_user')}
    user_settings = settings_model.UserSettings(
        parent=self.user_key, **properties).put()

    retrived_settings = settings_logic.getUserSettings(self.user_key)

    # check that the same entity is returned
    self.assertEqual(user_settings, retrived_settings.key)

  def testFunctionCalledTwice(self):
    """Tests that the same entity is returned if the function is called once."""
    first_settings = settings_logic.getUserSettings(self.user_key)
    other_settings = settings_logic.getUserSettings(self.user_key)

    # check that the same entity is returned
    self.assertEqual(first_settings.key, other_settings.key)

    # check that only one entity exists
    count = settings_model.UserSettings.query(ancestor=self.user_key).count()
    self.assertEqual(count, 1)
