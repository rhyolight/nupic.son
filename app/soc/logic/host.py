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

"""Logic related to program hosts."""

from soc.logic import program as program_logic
from soc.models import user as user_model


def getHostsForProgram(program):
  """Returns all users who are hosts for the specified program.

  Args:
    program: Program entity for which the hosts must be determined.

  Returns:
    A set containing user entities representing program hosts.
  """
  sponsor_key = program_logic.getSponsorKey(program)
  query = user_model.User.all()
  query.filter('host_for', sponsor_key)
  return set(query.fetch(1000))
