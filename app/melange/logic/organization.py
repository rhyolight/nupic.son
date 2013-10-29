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

"""Logic for organizations."""

from google.appengine.ext import ndb

from melange import types
from melange.models import organization as org_model
from melange.utils import rich_bool

from summerofcode.models import organization as soc_org_model


ORG_ID_IN_USE = 'Organization ID %s is already in use for this program.'

def createOrganizationWithApplication(
    org_id, program_key, app_key, org_properties, app_properties,
    models=types.MELANGE_MODELS):
  """Creates a new organization and saves a corresponding survey response
  for the specified data.

  Args:
    org_id: Identifier of the new organization. Must be unique on
      'per program' basis.
    program_key: Program key.
    app_key: Organization application key.
    org_properties: A dict mapping organization properties to their values.
    app_properties: A dict mapping organization application questions to
      corresponding responses.
    models: models: instance of types.Models that represent appropriate models.

  Returns:
    RichBool whose value is set to True if organization and application
    response have been successfully created. Otherwise, RichBool whose value is
    set to False and extra part is a string that represents the reason why
    the action could not be completed.
  """
  # TODO(daniel): move it to a utility function
  entity_id = '%s/%s' % (program_key.name(), org_id)

  # check if no organization exists for the given key ID
  if models.ndb_org_model.get_by_id(entity_id) is not None:
    return rich_bool.RichBool(False, extra=ORG_ID_IN_USE % org_id)

  program_key = ndb.Key.from_old_key(program_key)
  organization = models.ndb_org_model(
      id=entity_id, org_id=org_id, program=program_key, **org_properties)

  app_key = ndb.Key.from_old_key(app_key)
  application_record = org_model.ApplicationResponse(
      parent=organization.key, survey=app_key, **app_properties)

  ndb.put_multi([organization, application_record])

  return rich_bool.TRUE
