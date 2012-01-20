#!/usr/bin/env python2.5
#
# Copyright 2012 the Melange authors.
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

"""GCI logic for program.
"""


from soc.logic import program as program_logic

from soc.modules.gci.models.program import GCIProgram
from soc.modules.gci.models.timeline import GCITimeline


def getMostRecentProgram():
  """Returns the most recent program.

  Args:
    program_model: The model class that represents the program entity
    timeline_model: The model class that represents the program timeline entity

  Returns:
    The program entity for the most recent program
  """

  return program_logic.getMostRecentProgram(GCIProgram, GCITimeline)