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

"""Module for slot allocation."""

import json
import logging

from google.appengine.ext import db
from google.appengine.ext import ndb

from django import http

from melange.models import organization as org_model
from melange.request import access
from melange.request import exception

from soc.views.helper import lists
from soc.views.helper import url_patterns

from soc.modules.gsoc.models import proposal as proposal_model
from soc.modules.gsoc.templates import org_list
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views.helper import url_patterns as gsoc_url_patterns

from summerofcode.models import organization as soc_org_model


class SlotsList(org_list.OrgList):
  """Template for list of accepted organizations to allocate slots."""

  class ListPrefetcher(lists.Prefetcher):
    """Prefetcher used by SlotsList.

    See lists.Prefetcher for specification.
    """

    def prefetch(self, entities):
      """Prefetches the number of unused slots for each item in the
      specified list of organization entities.

      See lists.Prefetcher.prefetch for specification.

      Args:
        entities: List of organization entities.

      Returns:
        Prefetched numbers in a structure whose format is described
        in lists.ListModelPrefetcher.prefetch.
      """
      org_slots_unused = {}

      for entity in entities:
        query = proposal_model.GSoCProposal.all(keys_only=True)
        query.filter('org', entity.key.to_old_key())
        query.filter('has_mentor', True)
        query.filter('accept_as_project', True)
        slots_used = query.count()

        org_slots_unused[entity.key] = max(
            entity.slot_allocation - slots_used, 0)

      return ([org_slots_unused], {})

  def _getDescription(self):
    """See org_list.OrgList._getDescription for specification."""
    return org_list.ACCEPTED_ORG_LIST_DESCRIPTION % self.data.program.name

  def _getListConfig(self):
    """See org_list.OrgList._getListConfig for specification."""
    list_config = lists.ListConfiguration()

    list_config.addPlainTextColumn('name', 'Name',
        lambda e, *args: e.name.strip())

    list_config.addSimpleColumn('org_id', 'Organization ID', hidden=True)

    options = [('', 'All'), ('true', 'New'), ('false', 'Veteran')]
    list_config.addPlainTextColumn('is_veteran', 'New/Veteran',
        lambda e, *args: 'Veteran' if e.is_veteran else 'New', width=60,
        options=options)
    list_config.setColumnEditable('is_veteran', True, 'select')

    list_config.addSimpleColumn('slot_request_min', 'Min',
        width=25, column_type=lists.NUMERICAL)
    list_config.addSimpleColumn('slot_request_max', 'Max',
        width=25, column_type=lists.NUMERICAL)

    list_config.addSimpleColumn('slot_allocation', 'Slots',
        width=50, column_type=lists.NUMERICAL)
    list_config.setColumnEditable('slot_allocation', True)
    list_config.setColumnSummary('slot_allocation', 'sum', '<b>Total: {0}</b>')

    list_config.addHtmlColumn(
        'slots_unused', 'Unused slots',
        lambda ent, s, *args: ('<strong><font color="red">%s</font></strong>'
            % (s[ent.key])))

    # TODO(daniel): add note to organization model?
    #list_config.addSimpleColumn('note', 'Note')
    #list_config.setColumnEditable('note', True)

    list_config.setDefaultPagination(False)
    list_config.setDefaultSort('name')
    list_config.addPostEditButton('save', 'Save', "", [], refresh='none')

    return list_config

  def _getQuery(self):
    """See org_list.OrgList._getQuery for specification."""
    query = soc_org_model.SOCOrganization.query(
        soc_org_model.SOCOrganization.program ==
            ndb.Key.from_old_key(self.data.program.key()),
        soc_org_model.SOCOrganization.status == org_model.Status.ACCEPTED)
    return query

  def post(self):
    """POST handler for the list actions.

    Returns:
      True if the data is successfully modified; False otherwise.
    """
    idx = lists.getListIndex(self.data.request)
    if idx != 0:
      return False

    data = self.data.POST.get('data')

    if not data:
      raise exception.BadRequest(message="Missing data")

    parsed = json.loads(data)

    for key_id, properties in parsed.iteritems():
      note = properties.get('note')
      slot_allocation = properties.get('slot_allocation')
      is_veteran = properties.get('is_veteran')

      if ('note' not in properties and 'slot_allocation' not in properties and
          'is_veteran' not in properties):
        logging.warning(
            'Neither note nor slots nor is_veteran present in "%s"', properties)
        continue

      if 'slot_allocation' in properties:
        if not slot_allocation.isdigit():
          logging.warning('Non-int value for slots: "%s', slot_allocation)
          properties.pop('slot_allocation')
        else:
          slot_allocation = int(slot_allocation)

      if is_veteran:
        if not is_veteran in ['New', 'Veteran']:
          logging.warning('Invalid value for new_org: "%s"', is_veteran)
          properties.pop('is_veteran')
        else:
          is_veteran = True if is_veteran == 'Veteran' else False

      def update_org_txn():
        org = soc_org_model.SOCOrganization.get_by_id(key_id)
        if not org:
          logging.warning('Invalid org_key "%s"', key_id)
        elif 'note' in properties:
          pass
          # TODO(daniel): add note to organization model
          #org.note = note
        elif 'slot_allocation' in properties:
          org.slot_allocation = slot_allocation
        if 'is_veteran' in properties:
          org.is_veteran = is_veteran

        org.put()

      db.run_in_transaction(update_org_txn)

    return True

  def _getPrefetcher(self):
    """See org_list.OrgList._getPrefetcher for specification."""
    return SlotsList.ListPrefetcher()


class SlotsPage(base.GSoCRequestHandler):
  """View for the participant profile."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
        gsoc_url_patterns.url(r'admin/slots/%s$' % url_patterns.PROGRAM, self,
            name='gsoc_slots'),
    ]

  def templatePath(self):
    return 'modules/gsoc/admin/list.html'

  def jsonContext(self, data, check, mutator):
    list_content = SlotsList(data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.BadRequest(
          message='Missing idx parameter for component.')

  def post(self, data, check, mutator):
    slots_list = SlotsList(data)
    if slots_list.post():
      return http.HttpResponse()
    else:
      raise exception.Forbidden(message='You cannot change this data')

  def context(self, data, check, mutator):
    return {
      'page_name': 'Slots page',
      'list': SlotsList(data),
    }
