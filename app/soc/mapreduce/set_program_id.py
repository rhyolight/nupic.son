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

"""MapReduce job that sets program_id property for program entities.

The script works for GSoCProgram and GCIProgram models.
"""

import logging

from google.appengine.ext import db

from mapreduce import operation

from soc.modules.gci.models.program import GCIProgram
from soc.modules.gsoc.models.program import GSoCProgram


def process(entity_key):
  """Copies link_id field and writes it to program_id field for the entity with
  the specified key.

  Args:
    entity_key: key of the processed entity.
  """
  def convert_entity_txn():
    entity = db.get(entity_key)
    if not entity:
      logging.error('Missing entity for key %s.' % entity_key)
      return False

    # assign program property by its key
    entity.program_id = entity.link_id
    db.put(entity)
    return True

  result = db.run_in_transaction(convert_entity_txn)

  if result:
    yield operation.counters.Increment('updated_entity')
  else:
    yield operation.counters.Increment('missing_entity')
