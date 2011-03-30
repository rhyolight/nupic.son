#!/usr/bin/env python2.5
#
# Copyright 2009 the Melange authors.
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

"""GSoCOrganization (Model) query functions.
"""

__authors__ = [
    '"Madhusudan.C.S" <madhusudancs@gmail.com',
    '"Daniel Hans" <daniel.m.hans@gmail.com>',
    '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]


import datetime

from google.appengine.api import memcache
from google.appengine.ext import db

from soc.logic import tags
from soc.logic.models import organization

import soc.models.organization

from soc.modules.gsoc.models.organization import GSoCOrganization as org_model
from soc.modules.gsoc.logic.models import program as program_logic

class Logic(organization.Logic):
  """Logic methods for the GSoCOrganization model.
  """

  def __init__(self, model=org_model,
               base_model=soc.models.organization.Organization,
               scope_logic=program_logic):
    """Defines the name, key_name and model for this entity.
    """

    self.tags_service = tags.TagsService('org_tag')

    super(Logic, self).__init__(model, base_model=base_model,
                                scope_logic=scope_logic)


  def updateOrCreateFromFields(self, properties, silent=False):
    """See base.Logic.updateOrCreateFromFields().
    """
    
    entity = super(Logic, self).updateOrCreateFromFields(properties, silent)
    
    return self.tags_service.setTagValuesForEntity(entity, properties)

  def updateOrCreateFromKeyName(self, properties, key_name, silent=False):
    """See base.Logic.updateOrCreateFromKeyName().
    """

    entity = super(Logic, self).updateOrCreateFromKeyName(
        properties, key_name, silent)

    return self.tags_service.setTagValuesForEntity(entity, properties)

  def updateEntityProperties(self, entity, entity_properties, silent=False,
                             store=True):
    """See base.Logic.updateEntityProperties().
    
    Also ensures that all tags for the organization are properly updated.
    """

    entity = super(Logic, self).updateEntityProperties(entity,
        entity_properties, silent, store)
    
    return self.tags_service.setTagValuesForEntity(entity, entity_properties)

  def _onCreate(self, entity):
    """Creates a RankerRoot entity.
    """

    from soc.modules.gsoc.logic.models.ranker_root import logic as ranker_root_logic
    from soc.modules.gsoc.models import student_proposal

    # create a new ranker
    ranker_root_logic.create(student_proposal.DEF_RANKER_NAME, entity,
        student_proposal.DEF_SCORE, 100)

    super(Logic, self)._onCreate(entity)

  def delete(self, entity):
    """Delete existing entity from datastore.
    """

    def org_delete_txn(entity):
      """Performs all necessary operations in a single transaction when
       an organization is deleted.
      """

      self.tags_service.removeAllTagsForEntity(entity)
      db.delete(entity)

    db.run_in_transaction(org_delete_txn, entity)

  def getParticipatingOrgs(self, program):
    """Return a list of organizations to display on program homepage.

    Args:
      program: program entity for which the orgs need to be fetched.
    """
    # expiry time to fetch the new organization entities
    # the current expiry time is 30 minutes.
    expiry_time = datetime.timedelta(seconds=1800)

    batch_size = 5

    properties = {
        'scope': program,
        'status': 'active',
        }

    q = self.getQueryForFields(properties)

    # the cache stores a 3-tuple in the order list of org entities,
    # cursor and the last time the cache was updated
    po_cache = memcache.get('participating_orgs')

    if po_cache:
      if not datetime.datetime.now() > po_cache[2] + expiry_time:
        return po_cache[0]
      else:
        q.with_cursor(po_cache[1])
        if q.count() < batch_size:
          q = self.getQueryForFields(properties)

    orgs = q.fetch(batch_size)
    new_cursor = q.cursor()
    memcache.set(
      key='participating_orgs',
      value=(orgs, new_cursor, datetime.datetime.now()))

    return orgs

logic = Logic()
