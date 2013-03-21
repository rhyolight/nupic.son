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

import logging

from google.appengine.ext import db

from django import http
from django.utils import simplejson

from soc.logic import exceptions
from soc.views.helper import lists
from soc.views.helper import url_patterns

from soc.modules.gsoc.models import organization as org_model
from soc.modules.gsoc.models import proposal as proposal_model
from soc.modules.gsoc.templates import org_list
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views.helper import url_patterns as gsoc_url_patterns


class SlotsList(org_list.AcceptedOrgsList):
  """Template for list of accepted organizations to allocate slots."""

  def extraColumn(self, list_config):
    options = [('', 'All'), ('true', 'New'), ('false', 'Veteran')]
    list_config.addPlainTextColumn('new_org', 'New/Veteran',
        lambda e, *args:'New' if e.new_org else 'Veteran', width=60,
        options=options)
    list_config.setColumnEditable('new_org', True, 'select')

    list_config.addSimpleColumn('slots_desired', 'Min',
        width=25, column_type=lists.ColumnType.NUMERICAL)
    list_config.addSimpleColumn('max_slots_desired', 'Max',
        width=25, column_type=lists.ColumnType.NUMERICAL)
    list_config.addSimpleColumn('slots', 'Slots',
        width=50, column_type=lists.ColumnType.NUMERICAL)
    list_config.setColumnEditable('slots', True)
    list_config.setColumnSummary('slots', 'sum', "<b>Total: {0}</b>")
    list_config.addHtmlColumn(
          'slots_unused', 'Unused slots',
          lambda ent, s, *args: ('<strong><font color="red">%s</font></strong>'
                                 % (s[ent.key()])))
    list_config.addSimpleColumn('note', 'Note')
    list_config.setColumnEditable('note', True) #, edittype='textarea')
    list_config.setDefaultPagination(False)
    list_config.setDefaultSort('name')
    list_config.addPostEditButton('save', "Save", "", [], refresh="none")

    return list_config

  def post(self):
    idx = lists.getListIndex(self.data.request)
    if idx != 0:
      return False

    data = self.data.POST.get('data')

    if not data:
      raise exceptions.BadRequest("Missing data")

    parsed = simplejson.loads(data)

    for key_name, properties in parsed.iteritems():
      note = properties.get('note')
      slots = properties.get('slots')
      new_org = properties.get('new_org')

      if ('note' not in properties and 'slots' not in properties and
          'new_org' not in properties):
        logging.warning("Neither note or slots present in '%s'" % properties)
        continue

      if 'slots' in properties:
        if not slots.isdigit():
          logging.warning("Non-int value for slots: '%s'" % slots)
          properties.pop('slots')
        else:
          slots = int(slots)

      if new_org:
        if not new_org in ['New', 'Veteran']:
          logging.warning("Invalid value for new_org: '%s'" % new_org)
          properties.pop('new_org')
        else:
          new_org = True if new_org == 'New' else False

      def update_org_txn():
        org = org_model.GSoCOrganization.get_by_key_name(key_name)
        if not org:
          logging.warning("Invalid org_key '%s'" % key_name)
          return
        if 'note' in properties:
          org.note = note
        if 'slots' in properties:
          org.slots = slots
        if 'new_org' in properties:
          org.new_org = new_org

        org.put()

      db.run_in_transaction(update_org_txn)

    return True

  def getListData(self):
    idx = lists.getListIndex(self.data.request)
    if idx != 0:
      return None

    q = org_model.GSoCOrganization.all().filter('scope', self.data.program)

    starter = lists.keyStarter

    def prefetcher(orgs):
      org_slots_unused = {}

      for org in orgs:
        prop_q = db.Query(proposal_model.GSoCProposal, keys_only=False)
        prop_q.filter('org', org)
        prop_q.filter('has_mentor', True)
        prop_q.filter('accept_as_project', True)
        slots_used = prop_q.count()

        org_slots_unused[org.key()] = org.slots - slots_used if \
            org.slots > slots_used else 0

      return ([org_slots_unused], {})

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, q,
        starter, prefetcher=prefetcher)

    return response_builder.build()


class SlotsPage(base.GSoCRequestHandler):
  """View for the participant profile."""

  def djangoURLPatterns(self):
    return [
        gsoc_url_patterns.url(r'admin/slots/%s$' % url_patterns.PROGRAM, self,
            name='gsoc_slots'),
    ]

  def checkAccess(self, data, check, mutator):
    check.isHost()

  def templatePath(self):
    return 'v2/modules/gsoc/admin/list.html'

  def jsonContext(self, data, check, mutator):
    list_content = SlotsList(data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exceptions.AccessViolation('You do not have access to this data')

  def post(self, data, check, mutator):
    slots_list = SlotsList(data)
    if slots_list.post():
      return http.HttpResponse()
    else:
      raise exceptions.AccessViolation('You cannot change this data')

  def context(self, data, check, mutator):
    return {
      'page_name': 'Slots page',
      # TODO(nathaniel): Drop the first parameter of SlotsList.
      'list': SlotsList(data),
    }
