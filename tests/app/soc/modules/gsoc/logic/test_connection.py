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

"""Tests for soc.modules.gsoc.logic.connection."""

import unittest

from soc.modules.gsoc.logic import connection as connection_logic
from soc.modules.gsoc.models import GSoCConnection

from soc.modules.seeder.logic.seeder import logic as seeder_logic

class ConnectionTest(unittest.TestCase):
  
  def testConnectionExists(self):
    """Tests that existing GSoCConnection objects between Profiles and
    Organizations can be fetched with this helper.
    """
    pass
  
  def testCreateConnection(self):
    """Tests that a GSoCConnection object can be generated successfully.
    """
    pass
  
  def testCreateConnectionMessage(self):
    """Tests that a GSoCConnectionMessage can be added to an existing
    GSoCConnection object.
    """
    pass