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

"""Module for the GSoC proposal page."""

from google.appengine.ext import db

from django.utils.translation import ugettext

from soc.logic import cleaning
from soc.logic.exceptions import AccessViolation
from soc.views.helper import url_patterns
from soc.tasks import mailer

from soc.modules.gsoc.logic import proposal as proposal_logic
from soc.modules.gsoc.logic.helper import notifications
from soc.modules.gsoc.models.proposal import GSoCProposal
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.views.base import GSoCRequestHandler
from soc.modules.gsoc.views.forms import GSoCModelForm
from soc.modules.gsoc.views.helper import url_patterns as gsoc_url_patterns
from soc.modules.gsoc.views.helper.url_patterns import url


class ProposalForm(GSoCModelForm):
  """Django form for the proposal page.
  """

  class Meta:
    model = GSoCProposal
    css_prefix = 'gsoc_proposal'
    exclude = ['status', 'mentor', 'possible_mentors', 'org', 'program',
        'is_editable_post_deadline', 'created_on', 'last_modified_on',
        'score', 'nr_scores', 'accept_as_project', 'extra', 'has_mentor']

  clean_content = cleaning.clean_html_content('content')

class ProposalPage(GSoCRequestHandler):
  """View for the submit proposal."""

  def djangoURLPatterns(self):
    return [
        url(r'proposal/submit/%s$' % url_patterns.ORG,
         self, name='submit_gsoc_proposal'),
    ]

  def checkAccess(self, data, check, mutator):
    check.isLoggedIn()
    check.isActiveStudent()
    check.isOrganizationInURLActive()
    check.canStudentPropose()

  def templatePath(self):
    return 'v2/modules/gsoc/proposal/base.html'

  def buttonsTemplate(self):
    return 'v2/modules/gsoc/proposal/_buttons_create.html'

  def context(self, data, check, mutator):
    if data.POST:
      proposal_form = ProposalForm(data.POST)
    else:
      initial = {'content': data.organization.contrib_template}
      proposal_form = ProposalForm(initial=initial)

    return {
        'page_name': 'Submit proposal',
        'form_header_message': 'Submit proposal to %s' % (
            data.organization.name),
        'proposal_form': proposal_form,
        'buttons_template': self.buttonsTemplate()
        }

  def createFromForm(self, data):
    """Creates a new proposal based on the data inserted in the form.

    Args:
      data: A RequestData describing the current request.

    Returns:
      a newly created proposal entity or None
    """
    proposal_form = ProposalForm(data.POST)

    if not proposal_form.is_valid():
      return None

    # set the organization and program references
    proposal_form.cleaned_data['org'] = data.organization
    proposal_form.cleaned_data['program'] = data.program

    student_info_key = data.student_info.key()

    q = GSoCProfile.all().filter('mentor_for', data.organization)
    q = q.filter('status', 'active')
    q.filter('notify_new_proposals', True)
    mentors = q.fetch(1000)

    to_emails = [i.email for i in mentors]

    def create_proposal_trx():
      student_info = db.get(student_info_key)
      student_info.number_of_proposals += 1
      student_info.put()

      proposal = proposal_form.create(commit=True, parent=data.profile)

      context = notifications.newProposalContext(data, proposal, to_emails)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=proposal)
      sub_txn()

      return proposal

    return db.run_in_transaction(create_proposal_trx)

  def post(self, data, check, mutator):
    """Handler for HTTP POST request."""
    proposal = self.createFromForm(data)
    if proposal:
      data.redirect.review(proposal.key().id(), data.user.link_id)
      return data.redirect.to('review_gsoc_proposal')
    else:
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)


class UpdateProposal(GSoCRequestHandler):
  """View for the update proposal page.
  """

  ACTIONS = {
      'resubmit': 'Resubmit',
      'update': 'Update',
      'withdraw': 'Withdraw',
      }

  def djangoURLPatterns(self):
    return [
         url(r'proposal/update/%s$' % gsoc_url_patterns.PROPOSAL,
         self, name='update_gsoc_proposal'),
    ]

  def checkAccess(self, data, check, mutator):
    check.isLoggedIn()
    check.isActiveStudent()

    mutator.proposalFromKwargs()
    data.organization = data.proposal.org

    check.canStudentUpdateProposal()

    if data.POST:
      action = data.POST['action']

      status = data.proposal.status
      if status == 'pending' and action == self.ACTIONS['resubmit']:
        error_msg = ugettext('You cannot resubmit a pending proposal')
        raise AccessViolation(error_msg)
      if status == 'withdrawn' and action == self.ACTIONS['withdraw']:
        error_msg = ugettext('This proposal has already been withdrawn')
        raise AccessViolation(error_msg)
      if status == 'withdrawn' and action == self.ACTIONS['update']:
        error_msg = ugettext('This proposal has been withdrawn')
        raise AccessViolation(error_msg)
      data.action = action

  def templatePath(self):
    return 'v2/modules/gsoc/proposal/base.html'

  def buttonsTemplate(self):
    return 'v2/modules/gsoc/proposal/_buttons_update.html'

  def context(self, data, check, mutator):
    proposal = data.proposal

    proposal_form = ProposalForm(data.POST or None, instance=proposal)

    return {
        'page_name': 'Update proposal',
        'form_header_message': 'Update proposal to %s' % (proposal.org.name),
        'proposal_form': proposal_form,
        'is_pending': data.is_pending,
        'buttons_template': self.buttonsTemplate(),
        }

  def _updateFromForm(self, data):
    """Updates a proposal based on the data inserted in the form.

    Args:
      data: A RequestData describing the current request.

    Returns:
      an updated proposal entity or None
    """
    proposal_form = ProposalForm(data.POST, instance=data.proposal)

    if not proposal_form.is_valid():
      return None

    q = GSoCProfile.all().filter('mentor_for', data.proposal.org)
    q = q.filter('status', 'active')
    q.filter('notify_proposal_updates', True)
    mentors = q.fetch(1000)

    to_emails = [i.email for i in mentors]

    proposal_key = data.proposal.key()

    def update_proposal_txn():
      proposal = db.get(proposal_key)
      proposal_form.instance = proposal
      proposal = proposal_form.save(commit=True)

      context = notifications.updatedProposalContext(data, proposal, to_emails)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=proposal)
      sub_txn()

      return proposal

    return db.run_in_transaction(update_proposal_txn)

  def _withdraw(self, data):
    """Withdraws a proposal."""

    def withdraw_proposal_txn():
      proposal = db.get(data.proposal.key())
      student_info = db.get(data.student_info.key())

      proposal_logic.withdrawProposal(proposal, student_info)

    db.run_in_transaction(withdraw_proposal_txn)

  def _resubmit(self, data):
    """Resubmits a proposal."""

    def resubmit_proposal_txn():
      proposal = db.get(data.proposal.key())
      student_info = db.get(data.student_info.key())
      proposal_logic.resubmitProposal(
          proposal, student_info, data.program, data.program_timeline)

    db.run_in_transaction(resubmit_proposal_txn)

  def post(self, data, check, mutator):
    """Handler for HTTP POST request."""
    if data.action == self.ACTIONS['update']:
      proposal = self._updateFromForm(data)
      if not proposal:
        # TODO(nathaniel): problematic self-use.
        return self.get(data, check, mutator)
    elif data.action == self.ACTIONS['withdraw']:
      self._withdraw(data)
    elif data.action == self.ACTIONS['resubmit']:
      self._resubmit(data)

    data.redirect.review(data.proposal.key().id(), data.user.link_id)
    return data.redirect.to('review_gsoc_proposal')
