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

"""Module for the GCI Organization Admins to propose winners for their orgs."""

from google.appengine.ext import db

from django import forms
from django.utils.translation import ugettext

from soc.modules.gci.views.base import GCIRequestHandler

from soc.views.helper import url_patterns

from soc.modules.gci.logic import org_score as org_score_logic
from soc.modules.gci.models import organization as organization_model
from soc.modules.gci.models import profile as profile_model
from soc.modules.gci.models import profile
from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.helper import url_patterns as gci_url_patterns
from soc.modules.gci.views.helper import url_names


DEF_WINNER_MORE_THAN_ONCE_ERROR = ugettext(
    'You cannot set the same winner more than once')

class ProposeWinnersForm(gci_forms.GCIModelForm):
  """Django form to propose the grand prize winners."""

  EMPTY_CHOICE = 'EMPTY_CHOICE'

  class Meta:
    model = None

  def __init__(self, request_data, *args):
    super(ProposeWinnersForm, self).__init__(*args)
    self.request_data = request_data

    choices = [(ProposeWinnersForm.EMPTY_CHOICE, '---')]

    possible_winners = org_score_logic.getPossibleWinners(
        request_data.organization)

    for possible_winner in possible_winners:
      choices.append(self._getChoiceOption(possible_winner))

    self.fields.get('first_proposed_winner').choices = choices
    self.fields.get('second_proposed_winner').choices = choices
    self.fields.get('backup_proposed_winner').choices = choices

    # check if at least one grand prize winner is already set
    if len(self.request_data.organization.proposed_winners) > 0:
      self.fields.get('first_proposed_winner').initial = \
          self.request_data.organization.proposed_winners[0].name()

      # check if both grand prize winners are already set
      if len(self.request_data.organization.proposed_winners) > 1:
         self.fields.get('second_proposed_winner').initial = \
             self.request_data.organization.proposed_winners[1].name()

    # check if backup winner is already set
    if self.request_data.organization.backup_winner:
      self.fields.get('backup_proposed_winner').initial = (
          organization_model.GCIOrganization.backup_winner.
              get_value_for_datastore(self.request_data.organization).name())


  first_proposed_winner = forms.ChoiceField(label='First Grand Prize Winner')
  second_proposed_winner = forms.ChoiceField(label='Second Grand Prize Winner')
  backup_proposed_winner = forms.ChoiceField(label='Backup Grand Prize Winner')

  def clean(self):
    first_proposed_winner = self.cleaned_data.get(
        'first_proposed_winner', ProposeWinnersForm.EMPTY_CHOICE)
    second_proposed_winner = self.cleaned_data.get(
        'second_proposed_winner', ProposeWinnersForm.EMPTY_CHOICE)
    backup_proposed_winner = self.cleaned_data.get(
        'backup_proposed_winner', ProposeWinnersForm.EMPTY_CHOICE)

    # TODO (daniel): the logic below should be simplified
    key_names = set([
        first_proposed_winner, second_proposed_winner, backup_proposed_winner])

    if len(key_names) == 3:
      # there are three different key_names, so everything is OK
      pass
    elif len(key_names) == 2:
      # it is not OK, because at least one of the fields is duplicated
      self._errors['__all__'] = DEF_WINNER_MORE_THAN_ONCE_ERROR
    else:
      # it is OK, if all the elements are empty
      if list(key_names)[0] != ProposeWinnersForm.EMPTY_CHOICE:
        self._errors['__all__'] = DEF_WINNER_MORE_THAN_ONCE_ERROR

  def _getChoiceOption(self, student):
    return (student.key().name(), self._formatPossibleWinner(student))

  def _formatPossibleWinner(self, student):
    return '%s' % student.name()

class ProposeWinnersPage(GCIRequestHandler):
  """Page to propose winners by organization admins"""

  def templatePath(self):
    return 'v2/modules/gci/propose_winners/base.html'

  def djangoURLPatterns(self):
    return [
        gci_url_patterns.url(r'propose_winners/%s$' % url_patterns.ORG, self,
            name=url_names.GCI_ORG_PROPOSE_WINNERS),
    ]
    
  def checkAccess(self):
    self.check.isOrgAdmin()
    self.data.timeline.allReviewsStopped()
  
  def context(self):
    form = ProposeWinnersForm(
        self.data, self.data.POST or None)
    context = {
        'page_name': 'Propose winners for %s' % (self.data.organization.name),
        'forms': [form]
    }

    return context

  def post(self):
    """Handles POST requests."""
    form = ProposeWinnersForm(self.data, self.data.POST)

    if not form.is_valid():
      # TODO(nathaniel): problematic self-call.
      return self.get()

    first_key_name = self.data.POST.get(
        'first_proposed_winner', ProposeWinnersForm.EMPTY_CHOICE)

    second_key_name = self.data.POST.get(
        'second_proposed_winner', ProposeWinnersForm.EMPTY_CHOICE)

    backup_key_name = self.data.POST.get(
        'backup_proposed_winner', ProposeWinnersForm.EMPTY_CHOICE)

    proposed_winners = self._getProposedWinnersList(
        first_key_name, second_key_name)

    backup_winner = self._getBackupWinner(backup_key_name)

    def txn():
      organization = organization_model.GCIOrganization.get(
          self.data.organization.key())
      organization.proposed_winners = proposed_winners
      organization.backup_winner = backup_winner
      organization.put()

    db.run_in_transaction(txn)

    self.redirect.organization()
    return self.redirect.to(url_names.GCI_ORG_PROPOSE_WINNERS)

  def _getBackupWinner(self, backup_key_name):
    """Returns the GCIProfile entity belonging to the backup winner chosen
    by the organization.

    Args:
      backup_key_name: the key name proposed by the organization

    Returns:
      the GCIProfile entity associated with the specified argument or None
      if it does not point to any existing profile
    """
    parent_key = self._getUserKey(backup_key_name)
    
    profile = None
    if parent_key:
      profile = profile_model.GCIProfile.get_by_key_name(
          backup_key_name, parent_key)

    return profile

  def _getProposedWinnersList(self, first_key_name, second_key_name):
    """Returns the list which contains the keys of the GCIProfile entities
    belonging to students proposed by the organization.
    
    Args:
      first_key_name: the first key name proposed by the organization.
      second_key_name: the second key name proposed by the organization.

    Returns:
      a list with the keys of GCIProfile entity that correspond to
      the specified arguments.
    """
    proposed_winners = []

    parent_key = self._getUserKey(first_key_name)
    if parent_key:
      profile = profile_model.GCIProfile.get_by_key_name(
          first_key_name, parent_key)
      if profile:
        proposed_winners.append(profile.key())

    parent_key = self._getUserKey(second_key_name)
    if parent_key:
      profile = profile_model.GCIProfile.get_by_key_name(
          second_key_name, parent_key)
      if profile:
        proposed_winners.append(profile.key())

    return proposed_winners
    
  # TODO(daniel): discuss if this should go to the logic?
  def _getUserKey(self, key_name):
    """Returns the db.Key instance of the User entity that belong to a parent 
    of the specified profile's key name.
    
    Args:
      key_name: the specified Profile's key name

    Returns:
      db.Key instance or None if the key_name is invalid
    """
    parts = key_name.split('/')
    if len(parts) != 3:
      return None

    # TODO(daniel): check if the element has correct format to be a link_id
    return db.Key.from_path('User', parts[2])
