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

"""Utils for manipulating organization data."""

from google.appengine.ext import ndb

from soc.modules.seeder.logic.providers import string as string_provider

from melange.models import organization as org_model
from melange.models import survey as survey_model

from summerofcode.models import organization as soc_org_model


TEST_ORG_NAME = 'Test Org'
TEST_ORG_DESCRIPTION = 'Test Organization Description'

def seedOrganization(
    program_key, model=org_model.Organization, org_id=None, **kwargs):
  """Seeds a new organization.

  Args:
    program_key: Program key.
    model: Model class of which a new organization should be seeded.
    org_id: Identifier of the new organization.

  Returns:
    Newly seeded Organization entity.
  """
  org_id = org_id or string_provider.UniqueIDProvider().getValue()

  entity_id = '%s/%s' % (program_key.name(), org_id)
  program_key = ndb.Key.from_old_key(program_key)

  properties = {
      'description': TEST_ORG_DESCRIPTION,
      'org_id': org_id,
      'name': TEST_ORG_NAME,
      }
  properties.update(kwargs)
  org = model(id=entity_id, program=program_key, **properties)
  org.put()

  return org


def seedSOCOrganization(program_key, **kwargs):
  """Seeds a new organization for SOC.

  Args:
    program_key: Program key.

  Returns:
    Newly seeded SOCOrganization entity.
  """
  return seedOrganization(
      program_key, model=soc_org_model.SOCOrganization, **kwargs)


def seedApplication(org_key, survey_key, **kwargs):
  """Seeds a new organization application for the specified organization.

  Args:
    org_key: Organization key.
    survey_key: Survey key.

  Returns:
    Newly seeded SurveyResponse entity.
  """
  properties = {'survey': ndb.Key.from_old_key(survey_key)}
  properties.update(kwargs)

  survey_response = survey_model.SurveyResponse(parent=org_key, **properties)
  survey_response.put()

  return survey_response
