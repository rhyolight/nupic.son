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

"""Module for the GSoC slot transfer page."""

from google.appengine.ext import db

from django import forms as django_forms
from django import http

from melange.logic import user as user_logic
from melange.request import exception
from melange.request import links

from soc.logic import cleaning
from soc.tasks import mailer
from soc.views.helper import url_patterns

from soc.modules.gsoc.logic.helper import notifications
from soc.modules.gsoc.models.slot_transfer import GSoCSlotTransfer
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views import forms
from soc.modules.gsoc.views import readonly_template
from soc.modules.gsoc.views.helper.url_patterns import url

from summerofcode.views.helper import urls


class SlotTransferForm(forms.GSoCModelForm):
  """Django form for the slot transfer page.
  """

  def __init__(self, max_slots=None, **kwargs):
    super(SlotTransferForm, self).__init__(**kwargs)
    choices = [('None', self.fields['nr_slots'].label)] + [
        (i, i) for i in range(1, max_slots + 1)]
    self.fields['nr_slots'].widget = django_forms.widgets.Select(
        choices=choices)

  class Meta:
    model = GSoCSlotTransfer
    css_prefix = 'gsoc_slot_transfer'
    exclude = ['status', 'created_on', 'last_modified_on',
               'program', 'admin_remarks']

  clean_remarks = cleaning.clean_html_content('remarks')


class SlotTransferReadOnlyTemplate(readonly_template.GSoCModelReadOnlyTemplate):
  """Template to display readonly information from previous requests.
  """

  template_path = 'modules/gsoc/slot_transfer/_readonly_template.html'

  def __init__(self, counter, *args, **kwargs):
    super(SlotTransferReadOnlyTemplate, self).__init__(*args, **kwargs)
    self.counter = counter

  class Meta:
    model = GSoCSlotTransfer
    css_prefix = 'gsoc_slot_transfer'
    exclude = ['program']


class SlotTransferPage(base.GSoCRequestHandler):
  """View for transferring the slots.
  """

  def djangoURLPatterns(self):
    return [
        url(r'slots/transfer/%s$' % url_patterns.ORG,
            self, name='gsoc_slot_transfer'),
    ]

  def checkAccess(self, data, check, mutator):
    check.isLoggedIn()
    check.isProgramVisible()
    check.isOrganizationInURLActive()
    check.isOrgAdminForOrganization(data.url_ndb_org.key.to_old_key())

    check.isSlotTransferActive()
    mutator.slotTransferEntities()
    if not data.slot_transfer_entities:
      if 'new' not in data.kwargs:
        url = links.LINKER.organization(
            data.url_ndb_org.key, 'gsoc_update_slot_transfer')
        raise exception.Redirect(url)

  def templatePath(self):
    return 'modules/gsoc/slot_transfer/base.html'

  def context(self, data, check, mutator):
    requests = []
    require_new_link = True
    for i, ent in enumerate(data.slot_transfer_entities):
      requests.append(SlotTransferReadOnlyTemplate(i, instance=ent))
      if ent.status == 'pending':
        require_new_link = False

    context = {
        'page_name': 'Transfer slots to pool',
        'requests': requests,
        }

    if (data.program.allocations_visible and
        data.timeline.beforeStudentsAnnounced()):
      if require_new_link:
        context['new_slot_transfer_page_link'] = links.LINKER.organization(
            data.url_ndb_org.key, 'gsoc_update_slot_transfer')
      else:
        context['edit_slot_transfer_page_link'] = links.LINKER.organization(
            data.url_ndb_org.key, 'gsoc_update_slot_transfer')

    return context


class UpdateSlotTransferPage(base.GSoCRequestHandler):
  """View for transferring the slots."""

  def djangoURLPatterns(self):
    return [
        url(r'slots/transfer/update/%s$' % url_patterns.ORG,
            self, name='gsoc_update_slot_transfer'),
    ]

  def checkAccess(self, data, check, mutator):
    check.isLoggedIn()
    check.isProgramVisible()
    check.isOrganizationInURLActive()
    check.isOrgAdminForOrganization(data.url_ndb_org.key.to_old_key())

    check.isSlotTransferActive()
    mutator.slotTransferEntities()

  def templatePath(self):
    return 'modules/gsoc/slot_transfer/form.html'

  def context(self, data, check, mutator):
    slot_allocation = data.url_ndb_org.slot_allocation

    if data.POST:
      slot_transfer_form = SlotTransferForm(
          max_slots=slot_allocation, data=data.POST)
    else:
      slot_transfer_form = SlotTransferForm(
          max_slots=slot_allocation)

    for ent in data.slot_transfer_entities:
      if ent.status == 'pending':
        if data.POST:
          slot_transfer_form = SlotTransferForm(
              max_slots=slot_allocation, data=data.POST, instance=ent)
        else:
          slot_transfer_form = SlotTransferForm(
              max_slots=slot_allocation, instance=ent)

    context = {
        'page_name': 'Transfer slots to pool',
        'form_header_msg': 'Transfer the slots to the pool',
        'forms': [slot_transfer_form],
        'error': slot_transfer_form.errors
        }

    context['org_home_page_link'] = links.LINKER.organization(
        data.url_ndb_org.key, urls.UrlNames.ORG_HOME)
    context['slot_transfer_page_link'] = links.LINKER.organization(
        data.url_ndb_org.key, 'gsoc_slot_transfer')

    return context

  def createOrUpdateFromForm(self, data):
    """Creates a new proposal based on the data inserted in the form.

    Args:
      data: A RequestData describing the current request.

    Returns:
      a newly created proposal entity or None
    """
    slot_transfer_entity = None

    slot_transfer_form = SlotTransferForm(
         max_slots=data.url_ndb_org.slot_allocation, data=data.POST)

    if not slot_transfer_form.is_valid():
      return None

    slot_transfer_form.cleaned_data['program'] = data.program

    for ent in data.slot_transfer_entities:
      if ent.status == 'pending':
        slot_transfer_entity = ent
        break

    # TODO(daniel): send actual emails when we have email address in User model.
    host_users = user_logic.getHostsForProgram(data.program.key())
    to_emails = []

    def create_or_update_slot_transfer_trx():
      update = False
      if slot_transfer_entity:
        slot_transfer = db.get(slot_transfer_entity.key())
        slot_transfer_form.instance = slot_transfer
        slot_transfer = slot_transfer_form.save(commit=True)

        update = True
      else:
        slot_transfer = slot_transfer_form.create(
            commit=True, parent=data.url_ndb_org.key.to_old_key())

      context = notifications.createOrUpdateSlotTransferContext(
          data, slot_transfer, to_emails, update)
      sub_txn = mailer.getSpawnMailTaskTxn(
          context, parent=slot_transfer.parent())
      sub_txn()

      return slot_transfer

    return db.run_in_transaction(create_or_update_slot_transfer_trx)

  def post(self, data, check, mutator):
    """Handler for HTTP POST request."""
    slot_transfer_entity = self.createOrUpdateFromForm(data)
    if slot_transfer_entity:
      url = links.LINKER.organization(
          data.url_ndb_org.key, 'gsoc_update_slot_transfer')

      # TODO(daniel): there should be utility function to do that
      url += '?validated=True'

      return http.HttpResponseRedirect(url)
    else:
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)
