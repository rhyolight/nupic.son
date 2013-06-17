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

"""Logic for programs."""

from soc.models import program as program_model


def getSponsorKey(program):
  """Returns key which represents Sponsor of the specified program.

  Args:
    program: program entity

  Returns:
    db.Key instance of the sponsor for the specified program
  """
  return program_model.Program.sponsor.get_value_for_datastore(program)
