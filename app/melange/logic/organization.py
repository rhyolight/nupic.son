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

import collections
import datetime

from google.appengine.api import datastore_errors
from google.appengine.api import memcache
from google.appengine.ext import ndb

from melange import types
from melange.models import organization as org_model
from melange.models import survey as survey_model
from melange.utils import rich_bool

from soc.logic.helper import notifications
from soc.tasks import mailer


ORG_ID_IN_USE = 'Organization ID %s is already in use for this program.'

def createOrganization(
    org_id, program_key, org_properties, models=types.MELANGE_MODELS):
  """Creates a new organization profile based on the specified properties.

  Args:
    org_id: Identifier of the new organization. Must be unique on
      'per program' basis.
    program_key: Program key.
    org_properties: A dict mapping organization properties to their values.
    models: instance of types.Models that represent appropriate models.

  Returns:
    RichBool whose value is set to True if organization has been successfully
    created. In that case, extra part points to the newly created organization
    entity. Otherwise, RichBool whose value is set to False and extra part is
    a string that represents the reason why the action could not be completed.
  """
  # TODO(daniel): move it to a utility function
  entity_id = '%s/%s' % (program_key.name(), org_id)

  # check if no organization exists for the given key ID
  if models.ndb_org_model.get_by_id(entity_id) is not None:
    return rich_bool.RichBool(False, extra=ORG_ID_IN_USE % org_id)

  program_key = ndb.Key.from_old_key(program_key)

  try:
    organization = models.ndb_org_model(
        id=entity_id, org_id=org_id, program=program_key, **org_properties)
    organization.put()
  except ValueError as e:
    return rich_bool.RichBool(False, extra=str(e))
  except datastore_errors.BadValueError as e:
    return rich_bool.RichBool(False, extra=str(e))

  return rich_bool.RichBool(True, extra=organization)


def updateOrganization(org, org_properties):
  """Updates the specified organization based on the specified properties.

  Args:
    org: Organization entity.
    org_properties: A dict containing properties to be updated.
  """
  if 'org_id' in org_properties and org_properties['org_id'] != org.org_id:
    raise ValueError('org_id property is immutable.')

  if 'program' in org_properties and org_properties['program'] != org.program:
    raise ValueError('program property is immutable.')

  org.populate(**org_properties)
  org.put()


def getApplicationResponse(org_key):
  """Returns application response for the specified organization.

  Args:
    org_key: Organization key.

  Returns:
    Application response entity for the specified organization.
  """
  return survey_model.SurveyResponse.query(ancestor=org_key).get()


def setApplicationResponse(org_key, survey_key, properties):
  """Sets the specified properties for application of
  the specified organization.

  If no application exists for the organization, a new entity is created and
  persisted in datastore. In both cases, the existing or newly created entity
  is populated with the specified properties.

  Args:
    org_key: Organization key.
    properties: A dict mapping organization application questions to
      corresponding responses.

  Returns:
    survey_model.SurveyResponse entity associated the application.
  """
  app_response = getApplicationResponse(org_key)
  if not app_response:
    app_response = survey_model.SurveyResponse(
        parent=org_key, survey=ndb.Key.from_old_key(survey_key), **properties)
  else:
    # It just just for completeness, but first remove all dynamic properties.
    for prop, value in app_response._properties.items():
      if isinstance(value, ndb.GenericProperty):
        delattr(app_response, prop)
    app_response.populate(**properties)

  app_response.put()
  return app_response


def setStatus(organization, program, site, new_status, recipients=None):
  """Sets status of the specified organization.

  Args:
    organization: Organization entity.
    program: Program entity to which organization is assigned.
    site: Site entity.
    new_status: New status of the organization. Must be one of
      org_model.Status constants.
    recipients: List of one or more recipients for the notification email.

  Returns:
    The updated organization entity.
  """
  if organization.status != new_status:
    organization.status = new_status
    organization.put()

    if (recipients and
        new_status in [org_model.Status.ACCEPTED, org_model.Status.REJECTED]):
      if new_status == org_model.Status.ACCEPTED:
        notification_context = (
            notifications.OrganizationAcceptedContextProvider()
                .getContext(recipients, organization, program, site))
      elif new_status == org_model.Status.REJECTED:
        notification_context = (
            notifications.OrganizationRejectedContextProvider()
                .getContext(recipients, organization, program, site))

      sub_txn = mailer.getSpawnMailTaskTxn(
          notification_context, parent=organization)
      sub_txn()

  return organization


# Default number of accepted organizations to be returned by
# getAcceptedOrganizations function.
_DEFAULT_ORG_NUMBER = 5

# Defines how long a cached list of organizations is valid.
_ORG_CACHE_DURATION = datetime.timedelta(seconds=1800)

# Cache key pattern for organizations participating in the given program.
_ORG_CACHE_KEY_PATTERN = '%s_accepted_orgs_for_%s'

CachedData = collections.namedtuple('CachedData', ['orgs', 'time', 'cursor'])

def getAcceptedOrganizations(
    program_key, limit=None, models=types.MELANGE_MODELS):
  """Gets a list of organizations participating in the specified program.

  There is no guarantee that two different invocation of this function for
  the same arguments will return the same entities. The callers should
  acknowledge that it will receive a list of 'any' accepted organizations for
  the program and not make any further assumptions.

  In order to speed up the function, organizations may be returned
  from memcache, so subsequent calls to this function may be more efficient.

  Args:
    program_key: Program key.
    limit: Maximum number of results to return.
    models: instance of types.Models that represent appropriate models.

  Returns:
    A list of organization entities participating in the specified program.
  """
  limit = limit or _DEFAULT_ORG_NUMBER

  cache_key = _ORG_CACHE_KEY_PATTERN % (limit, program_key.name())
  cached_data = memcache.get(cache_key)
  if cached_data:
    if datetime.datetime.now() < cached_data.time + _ORG_CACHE_DURATION:
      return cached_data.orgs
    else:
      start_cursor = cached_data.cursor
  else:
    start_cursor = None

  # organizations are not returned from the cache so datastore is be queried
  query = models.ndb_org_model.query(
      models.ndb_org_model.program == ndb.Key.from_old_key(program_key),
      models.ndb_org_model.status == org_model.Status.ACCEPTED)
  orgs, next_cursor, _ = query.fetch_page(limit, start_cursor=start_cursor)

  if len(orgs) < limit:
    extra_orgs, next_cursor, _ = query.fetch_page(limit - len(orgs))

    org_keys = [org.key for org in orgs]
    for extra_org in extra_orgs:
      if extra_org.key not in org_keys:
        orgs.append(extra_org)

  # if the requested number of organizations have been found, they are cached
  if len(orgs) == limit:
    memcache.set(
        cache_key, CachedData(orgs, datetime.datetime.now(), next_cursor))

  return orgs
