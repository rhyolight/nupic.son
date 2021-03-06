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

from django.utils import translation

from google.appengine.api import datastore_errors
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import ndb

from melange import types
from melange.logic import profile as profile_logic
from melange.models import organization as org_model
from melange.models import profile as profile_model
from melange.models import survey as survey_model
from melange.utils import rich_bool

from soc.logic.helper import notifications
from soc.tasks import mailer


DEF_LINKER_URL_NAMES_REQUIRED = translation.ugettext(
    'Linker and UrlNames instances are required for accepting organizations.')

ORG_ID_IN_USE = translation.ugettext(
    'Organization ID %s is already in use for this program.')

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


def getApplicationResponsesQuery(survey_key):
  """Returns a query to fetch all application responses for the specified
  survey.

  Args:
    survey_key: Survey key.

  Returns:
    ndb.Query instance to fetch all responses for the specified survey.
  """
  if isinstance(survey_key, db.Key):
    survey_key = ndb.Key.from_old_key(survey_key)

  return survey_model.SurveyResponse.query(
      survey_model.SurveyResponse.survey == survey_key)


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


@ndb.transactional
def setStatus(organization, program, site, program_messages,
              new_status, linker=None, url_names=None, org_admins=None):
  """Sets status of the specified organization.

  This function may be called to accept the organization into the program
  or rejected it from the program, if new status is set to ACCEPTED or REJECTED,
  respectively. If the optional list of organization administrators
  is specified along with the program specific messages, they will be sent
  acceptance or rejection message.

  Additionally, if the organization status is set to ACCEPTED and the optional
  list of organization administrators is specified along with the program
  specific messages, the administrators will be sent the organization member
  welcome message.

  Args:
    organization: Organization entity.
    program: Program entity to which organization is assigned.
    site: Site entity.
    program_messages: ProgramMessages entity that holds the message
          templates provided by the program admins.
    new_status: New status of the organization. Must be one of
      org_model.Status constants.
    linker: Instance of links.Linker class (Optional: required only for
      sending notifications).
    url_names: Instance of url_names.UrlNames (Optional: required only for
      sending notifications).
    org_admins: Optional list of organization administrators for the specified
      organization.

  Returns:
    The updated organization entity.
  """
  if organization.status != new_status:
    organization.status = new_status
    organization.put()

    if (org_admins and
        new_status in [org_model.Status.ACCEPTED, org_model.Status.REJECTED]):

      # recipients of organization acceptance or rejection email
      recipients = [org_admin.contact.email for org_admin in org_admins]

      if new_status == org_model.Status.ACCEPTED:
        if not (linker and url_names):
          raise ValueError(DEF_LINKER_URL_NAMES_REQUIRED)

        notification_context = (
            notifications.OrganizationAcceptedContextProvider(linker,
                                                              url_names)
                .getContext(
                    recipients, organization, program, site,
                    program_messages))

        # organization administrators are also sent the welcome email
        for org_admin in org_admins:
          if (profile_model.MessageType.ORG_MEMBER_WELCOME_MSG
              not in org_admin.sent_messages):
            profile_logic.dispatchOrgMemberWelcomeEmail(
                org_admin, program, program_messages, site, parent=organization)
      elif new_status == org_model.Status.REJECTED:
        notification_context = (
            notifications.OrganizationRejectedContextProvider()
                .getContext(
                    recipients, organization, program, site,
                    program_messages))

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


# TODO(nathaniel): This is computationally inefficient and just plain weird.
# The right way to fix this problem is to just store org logos in org profiles
# (issue 1796).
def getAcceptedOrganizationsWithLogoURLs(
    program_key, limit=None, models=types.MELANGE_MODELS):
  """Finds accepted organizations that have set a logo URL.

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
    A list of organization entities participating in the specified program
      that have non-empty logo URL attributes.
  """
  limit = limit or _DEFAULT_ORG_NUMBER

  cache_key = '%s_accepted_orgs_with_logo_URLs_%s' % (limit, program_key.name())
  cached_data = memcache.get(cache_key)
  if cached_data:
    if datetime.datetime.now() < cached_data.time + _ORG_CACHE_DURATION:
      return cached_data.orgs
    else:
      cursor = cached_data.cursor
  else:
    cursor = None

  # Iterate through all the orgs looking for limit orgs with logos or a
  # determination that all available orgs have been exhausted.
  orgs = []
  all_found_org_keys = set()
  while len(orgs) < limit:
    query = models.ndb_org_model.query(
        models.ndb_org_model.program == ndb.Key.from_old_key(program_key),
        models.ndb_org_model.status == org_model.Status.ACCEPTED)
    requested = limit - len(orgs)
    found_orgs, next_cursor, _ = query.fetch_page(
        requested, start_cursor=cursor)

    found_org_found_again = False
    for found_org in found_orgs:
      if found_org.key in all_found_org_keys:
        # We've wrapped all the way around the list of orgs and come back
        # to the start. Return what we have.
        found_org_found_again = True
        break  # A labeled break here would save us the local field. :-(
      all_found_org_keys.add(found_org.key)
      if found_org.logo_url:
        orgs.append(found_org)
    if found_org_found_again:
      break

    if len(found_orgs) < requested:
      if cursor:
        # Wrap around to the beginning.
        cursor = None
      else:
        # Even from the beginning there just aren't enough orgs? Give up.
        break
    else:
      cursor = next_cursor

  # If the requested number of organizations have been found, cache them.
  if len(orgs) == limit:
    memcache.set(
        cache_key, CachedData(orgs, datetime.datetime.now(), cursor))

  return orgs
