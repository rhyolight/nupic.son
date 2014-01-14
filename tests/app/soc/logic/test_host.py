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

"""Tests for soc.logic.host."""

import unittest

from soc.logic import host as host_logic
from soc.models import program as program_model
from soc.models import sponsor as sponsor_model
from soc.models import user as user_model

from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests import profile_utils
from tests import program_utils


class HostTest(unittest.TestCase):
  """Tests for logic of Host Model."""

  def setUp(self):
    """Set up required for the host logic tests."""
    self.program = program_utils.seedProgram()

  def testGetHostsForProgram(self):
    """Tests if a host entity for a program is returned."""
    # hosts of the program
    user_entities = []
    for _ in range(5):
      user_entity = profile_utils.seedNDBUser(host_for=[self.program])
      user_entities.append(user_entity)

    expected_host_keys = set(user.key for user in user_entities)
    hosts_set = host_logic.getHostsForProgram(self.program)
    actual_host_keys = set(host.key() for host in hosts_set)
    self.assertSetEqual(actual_host_keys, expected_host_keys)

    # program with a different sponsor
    other_program = program_utils.seedProgram()
    hosts_set = host_logic.getHostsForProgram(other_program)
    self.assertSetEqual(hosts_set, set())
