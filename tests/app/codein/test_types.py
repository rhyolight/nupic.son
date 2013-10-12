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

"""Tests for Code In types module."""

import unittest

from codein import types

from soc.modules.gci.models import organization as org_model
from soc.modules.gci.models import profile as profile_model
from soc.modules.gci.models import program as program_model


class TestCodeInModels(unittest.TestCase):
  """Unit tests for CI_MODELS object."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.models = types.CI_MODELS

  def testOrgModel(self):
    """Tests org_model attribute."""
    self.assertEqual(self.models.org_model, org_model.GCIOrganization)

  def testProfileModel(self):
    """Tests profile_model attribute."""
    self.assertEqual(self.models.profile_model, profile_model.GCIProfile)

  def testProgramModel(self):
    """Tests program_model attribute."""
    self.assertEqual(self.models.program_model, program_model.GCIProgram)
