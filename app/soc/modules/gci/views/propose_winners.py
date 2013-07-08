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

from melange.request import access
from melange.request import exception

from soc.modules.gci.views.base import GCIRequestHandler

from soc.views.helper import lists
from soc.views.helper import url_patterns

from soc.modules.gci.logic import organization as org_logic
from soc.modules.gci.logic import org_score as org_score_logic
from soc.modules.gci.models import organization as organization_model
from soc.modules.gci.models import profile as profile_model
from soc.modules.gci.models import profile
from soc.modules.gci.templates import org_list
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
          str(self.request_data.organization.proposed_winners[0])

      # check if both grand prize winners are already set
      if len(self.request_data.organization.proposed_winners) > 1:
         self.fields.get('second_proposed_winner').initial = \
             str(self.request_data.organization.proposed_winners[1])

    # check if backup winner is already set
    if self.request_data.organization.backup_winner:
      self.fields.get('backup_proposed_winner').initial = str(
          organization_model.GCIOrganization.backup_winner.
              get_value_for_datastore(self.request_data.organization))


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
    elif list(key_names)[0] != ProposeWinnersForm.EMPTY_CHOICE:
      # it is not OK, when there is one choice which is not empty
      self._errors['__all__'] = DEF_WINNER_MORE_THAN_ONCE_ERROR

  def _getChoiceOption(self, student):
    return (str(student.key()), self._formatPossibleWinner(student))

  def _formatPossibleWinner(self, student):
    return '%s' % student.name()


class ProposeWinnersPage(GCIRequestHandler):
  """Page to propose winners by organization admins"""

  def templatePath(self):
    return 'modules/gci/propose_winners/base.html'

  def djangoURLPatterns(self):
    return [
        gci_url_patterns.url(r'propose_winners/%s$' % url_patterns.ORG, self,
            name=url_names.GCI_ORG_PROPOSE_WINNERS),
    ]

  def checkAccess(self, data, check, mutator):
    check.isOrgAdmin()
    if not data.timeline.allReviewsStopped():
      raise exception.Forbidden(
          message='This page may be accessed when the review period is over')

  def context(self, data, check, mutator):
    form = ProposeWinnersForm(data, data.POST or None)
    context = {
        'page_name': 'Propose winners for %s' % data.organization.name,
        'forms': [form]
    }

    return context

  def post(self, data, check, mutator):
    """Handles POST requests."""
    form = ProposeWinnersForm(data, data.POST)

    if not form.is_valid():
      # TODO(nathaniel): problematic self-call.
      return self.get(data, check, mutator)

    first_key_str = data.POST.get(
        'first_proposed_winner', ProposeWinnersForm.EMPTY_CHOICE)

    second_key_str = data.POST.get(
        'second_proposed_winner', ProposeWinnersForm.EMPTY_CHOICE)

    backup_key_str = data.POST.get(
        'backup_proposed_winner', ProposeWinnersForm.EMPTY_CHOICE)

    proposed_winners = self._getProposedWinnersList(
        first_key_str, second_key_str)

    backup_winner = self._getBackupWinner(backup_key_str)

    def txn():
      organization = organization_model.GCIOrganization.get(
          data.organization.key())
      organization.proposed_winners = proposed_winners
      organization.backup_winner = backup_winner
      organization.put()

    db.run_in_transaction(txn)

    data.redirect.organization()
    return data.redirect.to(url_names.GCI_ORG_PROPOSE_WINNERS)

  def _getProfileByKeyStr(self, key_str):
    """Returns the GCIProfile entity based on the specified string
    representation of db.Key.
    """
    try:
      key = db.Key(key_str)
    except db.BadKeyError:
      return None

    return profile_model.GCIProfile.get(key)

  def _getBackupWinner(self, backup_key_str):
    """Returns the GCIProfile entity belonging to the backup winner chosen
    by the organization.

    Args:
      backup_key_str: the string representation of the key associated with
          the profile proposed by the organization.

    Returns:
      the GCIProfile entity associated with the specified argument or None
      if it does not point to any existing profile
    """
    return self._getProfileByKeyStr(backup_key_str)

  def _getProposedWinnersList(self, first_key_str, second_key_str):
    """Returns the list which contains the keys of the GCIProfile entities
    belonging to students proposed by the organization.

    Args:
      first_key_str: the string representation of the first key associated
          with the profile proposed by the organization.
      second_key_str: the string representation of the second key associated
          with the profile proposed by the organization.

    Returns:
      a list with the keys of GCIProfile entity that correspond to
      the specified arguments.
    """
    proposed_winners = []

    profile = self._getProfileByKeyStr(first_key_str)
    if profile:
      proposed_winners.append(profile.key())

    profile = self._getProfileByKeyStr(second_key_str)
    if profile:
      proposed_winners.append(profile.key())

    return proposed_winners


class OrganizationsForProposeWinnersList(org_list.OrgList):
  """Lists all organizations for which the current user may propose the Grand
  Prize Winner and the row action takes their to ProposeWinnersPage for
  the corresponding organization.
  """

  def _getDescription(self):
    return ugettext('Choose an organization for which to propose the '
        'Grand Prize Winners.')

  def _getRedirect(self):
    def redirect(e, *args):
      # TODO(nathaniel): make this .organization call unnecessary.
      self.data.redirect.organization(organization=e)

      return self.data.redirect.urlOf(url_names.GCI_ORG_PROPOSE_WINNERS)
    return redirect

  def _getListConfig(self):
    """Returns ListConfiguration object for the list.
    """
    list_config = lists.ListConfiguration()
    list_config.addPlainTextColumn('name', 'Name',
        lambda e, *args: e.name.strip())
    list_config.addSimpleColumn('link_id', 'Link ID', hidden=True)
    list_config.setRowAction(self._getRedirect())
    return list_config

  def _getQuery(self):
    """Returns Query object to fetch entities for the list.
    """
    return org_logic.queryForOrgAdminAndStatus(
        self.data.profile, ['new', 'active'])


class ChooseOrganizationForProposeWinnersPage(GCIRequestHandler):
  """View with a list of organizations. When a user clicks on one of them,
  he or she is moved to the propose winner page for this organization.
  """

  access_checker = access.ALL_ALLOWED_ACCESS_CHECKER

  def templatePath(self):
    return 'modules/gci/org_list/base.html'

  def djangoURLPatterns(self):
    return [
        gci_url_patterns.url(
            r'org_choose_for_propose_winners/%s$' % url_patterns.PROGRAM, self,
            name=url_names.GCI_ORG_CHOOSE_FOR_PROPOSE_WINNNERS),
    ]

  def jsonContext(self, data, check, mutator):
    list_content = OrganizationsForProposeWinnersList(data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def context(self, data, check, mutator):
    return {
        'page_name': "Choose an organization for which to display scores.",
        'org_list': OrganizationsForProposeWinnersList(data),
        #'program_select': ProgramSelect(self.data, 'gci_accepted_orgs'),
    }


class ProposedWinnersForOrgsList(org_list.OrgList):
  """Lists all organizations for which the current user may propose the Grand
  Prize Winner and the row action takes their to ProposeWinnersPage for
  the corresponding organization.
  """

  def _getDescription(self):
    return ugettext('Proposed Grand Prize Winners')

  def _getRedirect(self):
    def redirect(e, *args):
      # TODO(nathaniel): make this .organization call unnecessary.
      self.data.redirect.organization(organization=e)

      return self.data.redirect.urlOf(url_names.GCI_ORG_PROPOSE_WINNERS)
    return redirect

  def _getListConfig(self):
    """Returns ListConfiguration object for the list.
    """
    def proposedWinnersFunc(organization, *args):
      profiles = profile_model.GCIProfile.get(organization.proposed_winners)
      return ', '.join([p.name() for p in profiles if p])

    list_config = lists.ListConfiguration()
    list_config.addPlainTextColumn('name', 'Name',
        lambda e, *args: e.name.strip())
    list_config.addPlainTextColumn('proposed_winners', 'Proposed Winners',
        proposedWinnersFunc)
    list_config.addPlainTextColumn('backup_winner', 'Backup Winner',
        lambda e, *args: e.backup_winner.name() if e.backup_winner else '')
    list_config.addSimpleColumn('link_id', 'Link ID', hidden=True)
    list_config.setRowAction(self._getRedirect())

    return list_config

  def _getQuery(self):
    """Returns Query object to fetch entities for the list.
    """
    return org_logic.queryForProgramAndStatus(
        self.data.program, ['new', 'active'])


class ViewProposedWinnersPage(GCIRequestHandler):
  """View with a list of organizations with the proposed Grand Prize Winners.
  """

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def templatePath(self):
    return 'modules/gci/org_list/base.html'

  def djangoURLPatterns(self):
    return [
        gci_url_patterns.url(
            r'view_proposed_winners/%s$' % url_patterns.PROGRAM, self,
            name=url_names.GCI_VIEW_PROPOSED_WINNERS),
    ]

  def jsonContext(self, data, check, mutator):
    list_content = ProposedWinnersForOrgsList(data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def context(self, data, check, mutator):
    return {
        'page_name': "Proposed Grand Prize Winners.",
        'org_list': ProposedWinnersForOrgsList(data),
        #'program_select': ProgramSelect(self.data, 'gci_accepted_orgs'),
    }
