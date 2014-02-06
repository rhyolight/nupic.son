# Copyright 2011 the Melange authors.
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

"""Module for the GSoC slot transfer admin page."""

import json
import logging

from google.appengine.ext import db
from google.appengine.ext import ndb

from django import http

from melange.request import access
from melange.request import exception
from soc.views import template
from soc.views.helper import lists
from soc.views.helper import url_patterns

from soc.modules.gsoc.models.slot_transfer import GSoCSlotTransfer
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views.helper import url_patterns as gsoc_url_patterns


class SlotsTransferAdminList(template.Template):
  """Template for list of slot transfer requests."""

  def __init__(self, data):
    self.data = data

    def getOrganization(entity, *args):
      """Helper function to get value for organization column."""
      return ndb.Key.from_old_key(entity.parent_key()).get().name

    def getSlotRequestMin(entity, *args):
      """Helper function to get value for slot request min column."""
      return ndb.Key.from_old_key(entity.parent_key()).get().slot_request_min

    def getSlotRequestMax(entity, *args):
      """Helper function to get value for slot request max column."""
      return ndb.Key.from_old_key(entity.parent_key()).get().slot_request_max

    def getSlotAllocation(entity, *args):
      """Helper function to get value for slot allocation column."""
      return ndb.Key.from_old_key(entity.parent_key()).get().slot_allocation

    list_config = lists.ListConfiguration()
    # hidden key
    list_config.addPlainTextColumn(
        'full_transfer_key', 'Full slot transfer key',
        lambda ent, *args: str(ent.key()), hidden=True)
    list_config.addPlainTextColumn(
        'org', 'Organization', getOrganization, width=75)
    options = [('', 'All'), ('pending', 'Pending'),
               ('accepted', 'Accepted'), ('rejected', 'Rejected')]
    list_config.addSimpleColumn('status', 'Status', width=40, options=options)
    list_config.addSimpleColumn('remarks', 'Remarks', width=75)
    list_config.addSimpleColumn('nr_slots', 'Returned slots', width=50)
    list_config.setColumnEditable('nr_slots', True)
    list_config.addSimpleColumn('admin_remarks', 'Admin remarks')
    list_config.setColumnEditable('admin_remarks', True) #, edittype='textarea')
    list_config.addNumericalColumn(
        'slot_request_min', 'Min slots requested', getSlotRequestMin,
        width=25, hidden=True)
    list_config.addNumericalColumn(
        'slot_request_max', 'Max slots requested', getSlotRequestMax,
        width=25, hidden=True)
    list_config.addNumericalColumn(
        'slot_allocation', 'Slot allocation', getSlotAllocation,
        width=50, hidden=True)
    list_config.setDefaultPagination(False)
    list_config.setDefaultSort('org')
    list_config.addPostEditButton('save', "Save", "",
                                  ['full_transfer_key'], refresh="none")

    bounds = [1, 'all']
    keys = ['key', 'full_transfer_key']
    list_config.addPostButton('accept', "Accept", "", bounds, keys)
    list_config.addPostButton('reject', "Reject", "", bounds, keys)

    self._list_config = list_config

  def context(self):
    description = 'List of slot transfer requests for the program %s' % (
        self.data.program.name)

    slot_transfer_request_list = lists.ListConfigurationResponse(
        self.data, self._list_config, 0, description)

    return {
        'lists': [slot_transfer_request_list],
    }

  def post(self):
    idx = lists.getListIndex(self.data.request)
    if idx != 0:
      return False

    data = self.data.POST.get('data')

    button_id = self.data.POST.get('button_id')

    if not data:
      raise exception.BadRequest(message="Missing data")

    parsed = json.loads(data)

    if button_id == 'accept':
      return self.postAccept(parsed, True)

    if button_id == 'reject':
      return self.postAccept(parsed, False)

    if button_id == 'save':
      return self.postSave(parsed)

  def postAccept(self, data, accept):
    for properties in data:
      if 'full_transfer_key' not in properties:
        logging.warning("Missing key in '%s'", properties)
        continue

      slot_transfer_key = properties['full_transfer_key']
      def accept_slot_transfer_txn():
        slot_transfer = db.get(slot_transfer_key)

        if not slot_transfer:
          logging.warning("Invalid slot_transfer_key '%s'", slot_transfer_key)
          return

        org_key = slot_transfer.parent_key()
        org = ndb.Key.from_old_key(org_key).get()

        if not org:
          logging.warning("No organization present for the slot transfer %s",
                          slot_transfer_key)
          return

        if accept:
          if slot_transfer.status == 'accepted':
            return

          slot_transfer.status = 'accepted'

          if slot_transfer.nr_slots < 0:
            logging.warning(
                "Organization %s is trying to trick us to gain more slots by "
                "using a negative number %s", org.name, slot_transfer.nr_slots)
            return

          org.slot_allocation -= slot_transfer.nr_slots
          if org.slot_allocation < 0:
            org.slot_allocation = 0

          org.put()
        else:
          if slot_transfer.status == 'rejected':
            return

          if slot_transfer.status == 'accepted':
            org.slot_allocation += slot_transfer.nr_slots
            org.put()

          slot_transfer.status = 'rejected'
        slot_transfer.put()

      # TODO(daniel): run this function in transaction when GSoCSlotTransfer
      # is updated to NDB
      accept_slot_transfer_txn()

    return True

  def postSave(self, parsed):

    for key_name, properties in parsed.iteritems():
      admin_remarks = properties.get('admin_remarks')
      nr_slots = properties.get('nr_slots')
      full_transfer_key = properties.get('full_transfer_key')

      if not full_transfer_key:
        logging.warning(
            "key for the slot transfer request is not present '%s'",
            properties)
        continue

      if 'admin_remarks' not in properties and 'nr_slots' not in properties:
        logging.warning(
            "Neither admin remarks or number of slots present in '%s'",
            properties)
        continue

      if 'nr_slots' in properties:
        if not nr_slots.isdigit():
          logging.warning("Non-int value for slots: '%s'", nr_slots)
          properties.pop('nr_slots')
        else:
          nr_slots = int(nr_slots)

      def update_org_txn():
        slot_transfer = db.get(full_transfer_key)
        if not slot_transfer:
          logging.warning("Invalid slot_transfer_key '%s'", key_name)
          return
        if 'admin_remarks' in properties:
          slot_transfer.admin_remarks = admin_remarks
        if 'nr_slots' in properties:
          slot_transfer.nr_slots = nr_slots
        slot_transfer.put()

      db.run_in_transaction(update_org_txn)

    return True

  def getListData(self):
    idx = lists.getListIndex(self.data.request)
    if idx != 0:
      return None

    q = GSoCSlotTransfer.all().filter('program', self.data.program)

    starter = lists.keyStarter
    # TODO(daniel): enable prefetching ['parent']
    # prefetcher = lists.ModelPrefetcher(GSoCSlotTransfer, [], parent=True)

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, q, starter,
        prefetcher=None)

    return response_builder.build()

  def templatePath(self):
    return "modules/gsoc/slot_transfer_admin/_list.html"


class SlotsTransferAdminPage(base.GSoCRequestHandler):
  """View for the the list of slot transfer requests."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
        gsoc_url_patterns.url(
            r'admin/slots/transfer/%s$' % url_patterns.PROGRAM, self,
            name='gsoc_admin_slots_transfer'),
    ]

  def templatePath(self):
    return 'modules/gsoc/slot_transfer_admin/base.html'

  def jsonContext(self, data, check, mutator):
    list_content = SlotsTransferAdminList(data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def post(self, data, check, mutator):
    slots_list = SlotsTransferAdminList(data)
    if slots_list.post():
      return http.HttpResponse()
    else:
      raise exception.Forbidden(message='You cannot change this data')

  def context(self, data, check, mutator):
    return {
      'page_name': 'Slots transfer action page',
      'slot_transfer_list': SlotsTransferAdminList(data),
    }
