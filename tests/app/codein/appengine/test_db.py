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

"""Tests for codein.appengine.db."""

import unittest

from codein.appengine import db as codein_db

from soc.modules.gci.models import profile as profile_model


class TestCodeInModels(unittest.TestCase):
  """Unit tests for CI_MODELS object."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.models = codein_db.CI_MODELS

  def testProfileModel(self):
    """Tests that appropriate profile model is returned."""
    self.assertEqual(self.models.profileModel, profile_model.GCIProfile)
