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
from soc.models.user import User


def getHostsForProgram(program_entity, limit=1000):
  """Returns all the host entities for the given program.

  Args:
    program_entity: The Program entity for which the hosts must be determined

  Returns:
    The list of user entities for the specified program entity
  """
  sponsor_key = program_logic.getSponsorKey(program_entity)
  query = User.all()
  query.filter('host_for', sponsor_key)
  # TODO(Madhu): Return the host entities once we run the Mapreduce to convert
  # host entities to refer to their corresponding user entities.
  return query.fetch(1000)
