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

"""Module containing list utilities."""

# These imports are needed for the toListItemDict function, to avoid 
# 'KindError' by func(entity) if func access a db.ReferenceProperty of the 
# entity.
from soc.modules.gsoc.models.program import GSoCProgram
from soc.modules.gsoc.models.timeline import GSoCTimeline


def toListItemDict(entity, column_def):
  """Create a list item from a datastore entity.

  Args:
    entity: The datastore entity regarding a list item.
    column_def: a dictionary that has column names of the list as keys, and
      lambda functions that create the value for that column for a list item as
      values. These functions should take one parameter, the entity relevant to
      one list item.

  Returns:
    A dictionary describing a list item.
  """
  output = {}
  for col, func in column_def.items():
    output[col] = func(entity)
  return output
