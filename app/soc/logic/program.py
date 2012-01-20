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

"""Logic for program model.
"""


def getMostRecentProgram(program_model, timeline_model):
  """Returns the most recent program.

  Args:
    program_model: The model class that represents the program entity
    timeline_model: The model class that represents the program timeline entity
  returns:
    The program entity for the most recent program
  """

  # get the first program ordered by the reverse program end date
  timeline_query = timeline_model.all(keys_only=True)
  timeline_query = timeline_query.order('-program_end')
  timeline_key = timeline_query.get()

  # get the program entity from the timeline key
  program_query = program_model.all()
  program_query = program_query.filter('timeline', timeline_key)
  program = program_query.get()

  return program
