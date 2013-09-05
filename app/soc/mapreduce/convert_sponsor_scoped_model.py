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

"""MapReduce that can be used to update models for which scope is defined
as sponsor. It will copy the scope property and save it under sponsor property.

Currently, it can be run for GCIProgram, GSoCProgram models.
"""

import logging

from google.appengine.ext import db
from mapreduce import operation

# This MapReduce requires these models to have been imported.
# pylint: disable=unused-import
from soc.models.sponsor import Sponsor
from soc.modules.gci.models.program import GCIProgram
from soc.modules.gsoc.models.program import GSoCProgram
# pylint: enable=unused-import


def _get_model_class(kind):
  return globals()[kind]

def process(entity_key):
  """Copies scope field and writes it to sponsor field for the entity with
  the specified key.

  Args:
    entity_key: key of the processed entity.
  """
  def convert_entity_txn():
    entity = db.get(entity_key)
    if not entity:
      logging.error('Missing entity for key %s.', entity_key)
      return False

    # assign program property by its key
    model_class = _get_model_class(entity.kind())
    entity.sponsor = model_class.scope.get_value_for_datastore(entity)

    db.put(entity)
    return True

  result = db.run_in_transaction(convert_entity_txn)

  if result:
    yield operation.counters.Increment('updated_entity')
  else:
    yield operation.counters.Increment('missing_entity')
