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

"""GCI logic for program."""

from google.appengine.ext import ndb

from melange.models import profile as profile_model


def getMostRecentProgram(data):
  """Returns the most recent program.

  Returns:
    The program link_id for the most recent gsoc program.
  """
  return data.site.latest_gci


def getWinnersForProgram(program_key):
  """Returns the Grand Prize Winners for the specified program.

  Args:
    program_key: Program key.

  Returns:
    A list of Profile instances containing winners of the program
  """
  query = profile_model.Profile.query(
      profile_model.Profile.student_data.is_winner == True,
      profile_model.Profile.program == ndb.Key.from_old_key(program_key))
  return query.fetch(1000)

