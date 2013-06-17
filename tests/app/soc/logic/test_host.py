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


class HostTest(unittest.TestCase):
  """Tests for logic of Host Model."""

  def setUp(self):
    """Set up required for the host logic tests."""
    properties = {'home': None}
    self.sponsor = seeder_logic.seed(sponsor_model.Sponsor, properties)

  def testGetHostsForProgram(self):
    """Tests if a host entity for a program is returned."""
    program_properties = {'sponsor': self.sponsor}
    program = seeder_logic.seed(program_model.Program, program_properties)

    # hosts of the program
    user_entities = []
    for _ in range(5):
      user_properties = {'host_for': [self.sponsor.key()]}
      user_entity = seeder_logic.seed(user_model.User, user_properties)
      user_entities.append(user_entity)

    expected_host_keys = set(user.key() for user in user_entities)
    hosts_set = host_logic.getHostsForProgram(program)
    actual_host_keys = set(host.key() for host in hosts_set)
    self.assertSetEqual(actual_host_keys, expected_host_keys)

    # program with a different sponsor
    program = seeder_logic.seed(program_model.Program)
    hosts_set = host_logic.getHostsForProgram(program)
    self.assertSetEqual(hosts_set, set())
