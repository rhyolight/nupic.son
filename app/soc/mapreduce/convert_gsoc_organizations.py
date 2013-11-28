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
"""Mapreduce converting GSoCOrganization to the new SOCOrganization model."""

from google.appengine.ext import ndb

from mapreduce import operation

from melange.models import contact as contact_model
from melange.models import survey as survey_model


# This MapReduce requires this model to have been imported.
# pylint: disable=unused-import
from soc.models.org_app_record import OrgAppRecord
from soc.models.org_app_survey import OrgAppSurvey
from soc.modules.gci.models.organization import GCIOrganization
from soc.modules.gci.models.program import GCIProgram
from soc.modules.gsoc.models.organization import GSoCOrganization
from soc.modules.gsoc.models.program import GSoCProgram
# pylint: enable=unused-import

from codein.models import organization as ci_org_model

from summerofcode.models import organization as soc_org_model


def _socSpecificProperties(organization):
  """Converts properties which are specific to Summer Of Code organizations.

  Args:
    organization: Organization entity.

  Returns:
    A dict mapping Summer Of Code specific organization properties to their
    values.
  """
  return {
      'ideas_page': organization.ideas,
      'slot_allocation': organization.slots,
      'slot_request_min': organization.slots_desired,
      'slot_request_max': organization.max_slots_desired,
      'max_score': organization.max_score,
      'list_all_mentors': organization.list_all_mentors,
      'is_veteran': not organization.new_org,
      }


def _ciSpecificProperties(organization):
  """Converts properties which are specific to Code In organizations.

  Args:
    organization: Organization entity.

  Returns:
    A dict mapping Code In specific organization properties to their values.
  """
  backup_winner_key = (
      GCIOrganization.backup_winner.get_value_for_datastore(organization))
  return {
      'task_quota_limit': organization.task_quota_limit,
      'email_for_notifications': organization.notification_mailing_list,
      'nominated_winners': [
          ndb.Key.from_old_key(proposed_winner) for proposed_winner in
          organization.proposed_winners],
      'nominated_backup_winner':
          ndb.Key.from_old_key(backup_winner_key) if backup_winner_key else None
      }


def _generalProperties(organization):
  """Converts general properties of organizations.

  Converts the specified organization by creating a new organization entity
  that inherits from NDB model.

  Args:
    organization: Organization entity.

  Returns:
    A dict mapping general organization properties to their values.
  """
  contact_properties = {
      'blog': getattr(organization, 'blog', None),
      'facebook': getattr(organization, 'facebook', None),
      'feed_url': getattr(organization, 'feed_url', None),
      'google_plus': getattr(organization, 'google_plus', None),
      'irc_channel': getattr(organization, 'irc_channel', None),
      'mailing_list': getattr(organization, 'pub_mailing_list', None),
      'twitter': getattr(organization, 'twitter', None),
      'web_page': getattr(organization, 'home_page', None),
      }
  contact = contact_model.Contact(**contact_properties)

  org_properties = {
      'contact': contact,
      'description': organization.description,
      'logo_url': organization.logo_url,
      'name': organization.name,
      'org_id': organization.link_id,
      'program': ndb.Key.from_old_key(organization.program.key()),
      }
  return org_properties


def _convertSurveyResponse(app_record, organization):
  """Converts the specified organization application record to the new,
  NDB based, SurveyResponse entity.

  Args:
    app_record: OrgAppRecord entity.
    organization: New (NDB based) organization entity.

  Returns:
    Newly created SurveyResponse entity.
  """

  if app_record:
    app_properties = {}
    app_properties['created_on'] = getattr(app_record, 'created')
    app_properties['modified_on'] = getattr(app_record, 'modified')

    for prop in app_record.dynamic_properties():
      app_properties[prop] = getattr(app_record, prop)

    survey = ndb.Key.from_old_key(app_record.survey.key())

    return survey_model.SurveyResponse(
        parent=organization.key, survey=survey, **app_properties)


@ndb.transactional
def persistEntitiesTxn(to_put):
  """Creates new entities within a transaction.

  Args:
    to_put: List of entities to persist.
  """
  ndb.put_multi(to_put)


def convertSOCOrganization(org_key):
  """Converts the specified Summer Of Code organization by creating a new
  organization entity that inherits from NDB model.

  Args:
    org_key: Organization key.
  """
  organization = GSoCOrganization.get(org_key)

  entity_id = '%s/%s' % (
      organization.program.key().name(), organization.link_id)

  org_properties = {}
  org_properties.update(_generalProperties(organization))
  org_properties.update(_socSpecificProperties(organization))
  new_organization = soc_org_model.SOCOrganization(
      id=entity_id, **org_properties)
  to_put = [new_organization]

  # find organization application record corresponding to this organization
  app_record = OrgAppRecord.all().filter(
      'org_id', organization.link_id).filter(
          'program', organization.program).get()
  if app_record:
    to_put.append(_convertSurveyResponse(app_record, new_organization))

  persistEntitiesTxn(to_put)
  operation.counters.Increment('Organizations converted')


def convertCIOrganization(org_key):
  """Converts the specified Code In organization by creating a new
  organization entity that inherits from NDB model.

  Args:
    org_key: Organization key.
  """
  organization = GCIOrganization.get(org_key)

  entity_id = '%s/%s' % (
      organization.program.key().name(), organization.link_id)

  org_properties = {}
  org_properties.update(_generalProperties(organization))
  org_properties.update(_ciSpecificProperties(organization))
  new_organization = ci_org_model.CIOrganization(
      id=entity_id, **org_properties)
  to_put = [new_organization]

  # find organization application record corresponding to this organization
  app_record = OrgAppRecord.all().filter(
      'org_id', organization.link_id).filter(
          'program', organization.program).get()
  if app_record:
    to_put.append(_convertSurveyResponse(app_record, new_organization))

  persistEntitiesTxn(to_put)
  operation.counters.Increment('Organizations converted')
