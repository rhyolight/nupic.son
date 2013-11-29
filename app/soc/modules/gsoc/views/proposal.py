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

from django import http
from django.utils.translation import ugettext

from melange.request import exception
from melange.request import links

from soc.logic import cleaning
from soc.views.helper import url_patterns
from soc.tasks import mailer

from soc.modules.gsoc.logic import profile as profile_logic
from soc.modules.gsoc.logic.helper import notifications
from soc.modules.gsoc.models.proposal import GSoCProposal
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views import proposal_review as proposal_review_view
from soc.modules.gsoc.views.forms import GSoCModelForm
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper.url_patterns import url


# Key of an item in POST dictionary defining action taken on a proposal.
ACTION_POST_KEY = 'action'

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

class ProposalPage(base.GSoCRequestHandler):
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
    return 'modules/gsoc/proposal/base.html'

  def buttonsTemplate(self):
    return 'modules/gsoc/proposal/_buttons_create.html'

  def context(self, data, check, mutator):
    if data.POST:
      proposal_form = ProposalForm(data=data.POST)
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
    proposal_form = ProposalForm(data=data.POST)

    if not proposal_form.is_valid():
      return None

    # set the organization and program references
    proposal_properties = proposal_form.asDict()
    proposal_properties['org'] = data.organization
    proposal_properties['program'] = data.program

    student_info_key = data.student_info.key()

    extra_attrs = {
        GSoCProfile.notify_new_proposals: [True]
        }
    mentors = profile_logic.getMentors(
        data.organization.key(), extra_attrs=extra_attrs)

    to_emails = [i.email for i in mentors]

    def create_proposal_trx():
      student_info = db.get(student_info_key)
      student_info.number_of_proposals += 1
      student_info.put()

      proposal = GSoCProposal(parent=data.profile, **proposal_properties)
      proposal.put()

      context = notifications.newProposalContext(data, proposal, to_emails)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=proposal)
      sub_txn()

      return proposal

    return db.run_in_transaction(create_proposal_trx)

  def post(self, data, check, mutator):
    """Handler for HTTP POST request."""
    proposal = self.createFromForm(data)
    if proposal:
      url = links.LINKER.userId(
          data.profile.key(), proposal.key().id(), url_names.PROPOSAL_REVIEW)
      return http.HttpResponseRedirect(url)
    else:
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)


class UpdateProposal(base.GSoCRequestHandler):
  """View for the update proposal page.
  """

  ACTIONS = {
      'resubmit': 'Resubmit',
      'update': 'Update',
      'withdraw': 'Withdraw',
      }

  def djangoURLPatterns(self):
    return [
         url(r'proposal/update/%s$' % url_patterns.USER_ID,
         self, name='update_gsoc_proposal'),
    ]

  def checkAccess(self, data, check, mutator):
    check.isLoggedIn()
    check.isActiveStudent()

    data.organization = data.url_proposal.org

    check.canStudentUpdateProposal()

    if data.POST:
      action = data.POST[ACTION_POST_KEY]

      status = data.url_proposal.status
      if status == 'pending' and action == self.ACTIONS['resubmit']:
        error_msg = ugettext('You cannot resubmit a pending proposal')
        raise exception.Forbidden(message=error_msg)
      if status == 'withdrawn' and action == self.ACTIONS['withdraw']:
        error_msg = ugettext('This proposal has already been withdrawn')
        raise exception.Forbidden(message=error_msg)
      if status == 'withdrawn' and action == self.ACTIONS['update']:
        error_msg = ugettext('This proposal has been withdrawn')
        raise exception.Forbidden(message=error_msg)

  def templatePath(self):
    return 'modules/gsoc/proposal/base.html'

  def buttonsTemplate(self):
    return 'modules/gsoc/proposal/_buttons_update.html'

  def context(self, data, check, mutator):
    proposal_form = ProposalForm(
        data=data.POST or None, instance=data.url_proposal)

    return {
        'page_name': 'Update proposal',
        'form_header_message': 'Update proposal to %s' % (
            data.url_proposal.org.name),
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
    proposal_form = ProposalForm(data=data.POST, instance=data.url_proposal)

    if not proposal_form.is_valid():
      return None

    org_key = GSoCProposal.org.get_value_for_datastore(data.url_proposal)
    extra_attrs = {
        GSoCProfile.notify_proposal_updates: [True]
        }
    mentors = profile_logic.getMentors(org_key, extra_attrs=extra_attrs)

    to_emails = [i.email for i in mentors]

    proposal_key = data.url_proposal.key()

    def update_proposal_txn():
      proposal = db.get(proposal_key)
      proposal_form.instance = proposal
      proposal = proposal_form.save(commit=True)

      context = notifications.updatedProposalContext(data, proposal, to_emails)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=proposal)
      sub_txn()

      return proposal

    return db.run_in_transaction(update_proposal_txn)

  def post(self, data, check, mutator):
    """Handler for HTTP POST request."""
    url = links.LINKER.userId(
        data.profile.key(), data.url_proposal.key().id(),
        url_names.PROPOSAL_REVIEW)

    if data.POST[ACTION_POST_KEY] == self.ACTIONS['update']:
      proposal = self._updateFromForm(data)
      if not proposal:
        # TODO(nathaniel): problematic self-use.
        return self.get(data, check, mutator)
      else:
        return http.HttpResponseRedirect(url)
    elif data.POST[ACTION_POST_KEY] == self.ACTIONS['withdraw']:
      handler = proposal_review_view.WithdrawProposalHandler(None, url=url)
      return handler.handle(data, check, mutator)
    elif data.POST[ACTION_POST_KEY] == self.ACTIONS['resubmit']:
      handler = proposal_review_view.ResubmitProposalHandler(None, url=url)
      return handler.handle(data, check, mutator)
