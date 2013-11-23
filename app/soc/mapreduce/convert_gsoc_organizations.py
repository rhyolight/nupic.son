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
from soc.models.org_app_survey import OrgAppSurvey
# pylint: enable=unused-import

from soc.models.org_app_record import OrgAppRecord
from soc.modules.gsoc.models.organization import GSoCOrganization

# This MapReduce requires this model to have been imported.
# pylint: disable=unused-import
from soc.modules.gsoc.models.program import GSoCProgram
# pylint: enable=unused-import

from summerofcode.models import organization as org_model


def convertOrg(org_key):
  """Converts the specified organization by creating a new organization entity
  that inherits from NDB model.

  Args:
    org_key: Organization key.
  """
  organization = GSoCOrganization.get(org_key)

  contact_properties = {
      'blog': organization.blog,
      'facebook': organization.facebook,
      'feed_url': organization.feed_url,
      'google_plus': organization.google_plus,
      'irc_channel': organization.irc_channel,
      'mailing_list': organization.pub_mailing_list,
      'twitter': organization.twitter,
      'web_page': organization.home_page,
      }
  contact = contact_model.Contact(**contact_properties)

  entity_id = '%s/%s' % (
      organization.program.key().name(), organization.link_id)
  org_properties = {
      'contact': contact,
      'description': organization.description,
      'ideas_page': organization.ideas,
      'is_veteran': not organization.new_org,
      'logo_url': organization.logo_url,
      'name': organization.name,
      'org_id': organization.link_id,
      'program': ndb.Key.from_old_key(organization.program.key()),
      'slot_allocation': organization.slots,
      'slot_request_min': organization.slots_desired,
      'slot_request_max': organization.max_slots_desired,
      }
  new_organization = org_model.SOCOrganization(id=entity_id, **org_properties)

  # find organization application record corresponding to this organization
  app_record = OrgAppRecord.all().filter(
      'org_id', organization.link_id).filter(
          'program', organization.program).get()
  if app_record:
    app_properties = {}
    app_properties['created_on'] = getattr(app_record, 'created')
    app_properties['modified_on'] = getattr(app_record, 'modified')

    for prop in app_record.dynamic_properties():
      app_properties[prop] = getattr(app_record, prop)

    survey = ndb.Key.from_old_key(app_record.survey.key())

    survey_response = survey_model.SurveyResponse(
        parent=new_organization.key, survey=survey, **app_properties)

  @ndb.transactional
  def convertOrgTxn():
    """Creates new entities within a transaction."""
    new_organization.put()
    survey_response.put()

  convertOrgTxn()
  operation.counters.Increment('Organizations converted')
