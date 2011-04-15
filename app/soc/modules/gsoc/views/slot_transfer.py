#!/usr/bin/env python2.5
#
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

"""Module for the GSoC slot transfer page.
"""

__authors__ = [
  '"Madhusudan.C.S" <madhusudancs@gmail.com>',
  ]


from google.appengine.ext import db

from django import forms as django_forms
from django.conf.urls.defaults import url

from soc.logic import cleaning
from soc.views import forms

from soc.modules.gsoc.logic import slot_transfer as slot_transfer_logic
from soc.modules.gsoc.models.slot_transfer import GSoCSlotTransfer

from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.helper import url_patterns


class SlotTransferForm(forms.ModelForm):
  """Django form for the slot transfer page.
  """

  template_path = 'v2/modules/gsoc/slot_transfer/_form.html'

  def __init__(self, max_slots, *args, **kwargs):
    super(SlotTransferForm, self).__init__(*args, **kwargs)
    choices = [('None', self.fields['nr_slots'].label)] + [
        (i, i) for i in range(1, max_slots + 1)]
    self.fields['nr_slots'].widget = django_forms.widgets.Select(
        choices=choices)

  class Meta:
    model = GSoCSlotTransfer
    css_prefix = 'gsoc_slot_transfer'
    exclude = ['status', 'created_on', 'last_modified_on']

  clean_remarks = cleaning.clean_html_content('remarks')


class SlotTransferPage(RequestHandler):
  """View for transferring the slots.
  """

  def djangoURLPatterns(self):
    return [
        url(r'^gsoc/slots/transfer/%s$' % url_patterns.NEW_SLOT_TRANSFER,
            self, name='gsoc_new_slot_transfer'),
        url(r'^gsoc/slots/transfer/%s$' % url_patterns.ORG,
         self, name='gsoc_slot_transfer'),
    ]

  def checkAccess(self):
    self.check.isLoggedIn()
    self.check.isProgramActive()
    self.mutator.organizationFromKwargs()
    self.check.isOrganizationInURLActive()
    self.check.isOrgAdminForOrganization(self.data.organization)

  def templatePath(self):
    return 'v2/modules/gsoc/slot_transfer/base.html'

  def context(self):
    slots = self.data.organization.slots

    slot_transfer_entity = slot_transfer_logic.getSlotTransferEntityForOrg(
        self.data.organization)

    if self.data.POST:
      slot_transfer_form = SlotTransferForm(slots, self.data.POST,
                                            instance=slot_transfer_entity)
    else:
      slot_transfer_form = SlotTransferForm(slots,
                                            instance=slot_transfer_entity)

    context = {
        'page_name': 'Transfer slots to pool',
        'form_header_msg': 'Transfer the slots to the pool',
        'forms': [slot_transfer_form],
        }

    if slot_transfer_entity:
      context['status'] = slot_transfer_entity.status

    return context

  def createOrUpdateFromForm(self):
    """Creates a new proposal based on the data inserted in the form.

    Returns:
      a newly created proposal entity or None
    """

    slot_transfer_form = SlotTransferForm(self.data.organization.slots,
                                          self.data.POST)

    if not slot_transfer_form.is_valid():
      return None

    slot_transfer_entity = slot_transfer_logic.getSlotTransferEntityForOrg(
        self.data.organization)

    def create_or_update_slot_transfer_trx():
      if slot_transfer_entity:
        slot_transfer = db.get(slot_transfer_entity.key())
        slot_transfer_form.instance = slot_transfer
        slot_transfer = slot_transfer_form.save(commit=True)
      else:
        slot_transfer = slot_transfer_form.create(
            commit=True, parent=self.data.organization)

      return slot_transfer

    return db.run_in_transaction(create_or_update_slot_transfer_trx)

  def post(self):
    """Handler for HTTP POST request.
    """

    slot_transfer_entity = self.createOrUpdateFromForm()
    if slot_transfer_entity:
      self.redirect.organization(self.data.organization)
      self.redirect.to('gsoc_slot_transfer', validated=True)
    else:
      self.get()
