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

"""Tests for Melange types module."""

import unittest

from melange import types

from melange.models import user as user_model

from soc.models import organization as org_model
from soc.models import profile as profile_model
from soc.models import program as program_model
from soc.models import timeline as timeline_model


class ModelsTest(unittest.TestCase):
  """Unit tests for Models class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.models = types.MELANGE_MODELS

  def testOrgModel(self):
    """Tests org_model attribute."""
    self.assertEqual(self.models.org_model, org_model.Organization)

  def testProfileModel(self):
    """Tests profile_model attribute."""
    self.assertEqual(self.models.profile_model, profile_model.Profile)

  def testProgramModel(self):
    """Tests program_model attribute."""
    self.assertEqual(self.models.program_model, program_model.Program)

  def testProgramMessagesModel(self):
    """Tests program_messages_model attribute."""
    self.assertEqual(
        self.models.program_messages_model, program_model.ProgramMessages)

  def testTimelineModel(self):
    """Tests timeline_model attribute."""
    self.assertEqual(self.models.timeline_model, timeline_model.Timeline)

  def testUserModel(self):
    """Tests user_model attribute."""
    self.assertEqual(self.models.user_model, user_model.User)
