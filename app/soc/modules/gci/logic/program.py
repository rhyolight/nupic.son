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

from soc.modules.gci.models import profile as profile_model


def getMostRecentProgram(data):
  """Returns the most recent program.

  Returns:
    The program link_id for the most recent gsoc program.
  """
  return data.site.latest_gci


def getWinnersForProgram(program):
  """Returns the Grand Prize Winners for the specified program.

  Args:
    program: GCIProgram instance for which to retrieve the winners

  Returns:
    a list of GCIProfile instances containing winners of the program
  """
  student_keys = profile_model.GCIStudentInfo.all(keys_only=True).filter(
      'is_winner', True).filter('program', program).fetch(1000)

  return profile_model.GCIProfile.get(
      [key.parent() for key in student_keys])
