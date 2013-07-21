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
as program. It will copy the scope property and save it under program property.

Currently, it can be run for GCIOrganization, GCIProfile, GSoCOrganization,
GSoCProfile.
"""

import logging

from google.appengine.ext import db
from mapreduce import operation

from soc.models.org_app_survey import OrgAppSurvey
from soc.models.survey import Survey
from soc.modules.gci.models.organization import GCIOrganization
from soc.modules.gci.models.profile import GCIProfile
from soc.modules.gci.models.program import GCIProgram
from soc.modules.gsoc.models.grading_project_survey import GradingProjectSurvey
from soc.modules.gsoc.models.organization import GSoCOrganization
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.models.program import GSoCProgram
from soc.modules.gsoc.models.project_survey import ProjectSurvey


def get_model_class(kind):
  return globals()[kind]

def process(entity_key):
  def convert_entity_txn():
    entity = db.get(entity_key)
    if not entity:
      logging.error('Missing entity for key %s.' % entity_key)
      return False

    # assign program property by its key
    model_class = get_model_class(entity.kind())
    entity.program = model_class.scope.get_value_for_datastore(entity)

    db.put(entity)
    return True

  result = db.run_in_transaction(convert_entity_txn)

  if result:
    yield operation.counters.Increment('updated_profile')
  else:
    yield operation.counters.Increment('missing_profile')
