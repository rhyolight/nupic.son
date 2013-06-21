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

"""Tests for soc.modules.seeder.logic.seeder."""

from soc.modules.seeder.logic.seeder import logic as seeder_logic
from soc.modules.seeder.logic import seeder

import ndb_models
import unittest


class SeederTest(unittest.TestCase):
  """Unit tests for seeder logic."""

  def testSeedingNdbDummyModel(self):
    """Tests that the entity can be seeded properly."""
    entity = seeder_logic.seed(ndb_models.NdbDummyModel)
    self.assertIsNotNone(entity)

  def testSeedingNdbKeyPropertyNotSpecified(self):
    """Tests exception raised when any ndb KeyProperty is not specified."""
    with self.assertRaises(seeder.KeyPropertyNotSpecifiedError):
      seeder_logic.seed(ndb_models.NdbKeyProperty)

  def testSeedingNdbKeyPropertySpecified(self):
    """Tests the entity can be seeded properly if ndb KeyProperty specified."""
    ndb_dummy_entity = seeder_logic.seed(ndb_models.NdbDummyModel)
    entity = seeder_logic.seed(ndb_models.NdbKeyProperty,
        properties={'key': ndb_dummy_entity.key})
    self.assertIsNotNone(entity)
