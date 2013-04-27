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

"""Module containing the view for GSoC request page."""

from google.appengine.ext import db

from django.utils.translation import ugettext

from soc.logic.exceptions import AccessViolation
from soc.logic.helper import notifications
from soc.logic import accounts
from soc.models.user import User
from soc.tasks import mailer
from soc.views import forms
from soc.views.helper.access_checker import isSet
from soc.views.helper import url_patterns

from soc.modules.gsoc.logic import profile as profile_logic
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.models.request import GSoCRequest
from soc.modules.gsoc.views.base import GSoCRequestHandler
from soc.modules.gsoc.views.base_templates import LoggedInMsg
from soc.modules.gsoc.views.forms import GSoCModelForm
from soc.modules.gsoc.views.helper.url_patterns import url

DEF_YOU_ARE_ORG_ADMIN = ugettext(
    'You are now an organization administrator for this organization.')

DEF_YOU_ARE_MENTOR = ugettext(
    'You are now a mentor for this organization.')

DEF_USER_ORG_ADMIN = ugettext(
    'This user is now an organization administrator with your organization.')

DEF_USER_MENTOR = ugettext(
    'This user is now a mentor with your organization.')


class RequestForm(GSoCModelForm):
  """Django form for the request page.
  """

  def __init__(self, custom_message=None, *args, **kwargs):
    super(RequestForm, self).__init__(*args, **kwargs)

    if custom_message:
      self.fields['custom_message'] = forms.CharField()
      self.fields['custom_message'].widget = forms.ReadonlyWidget(
          custom_message)
      self.fields['custom_message'].group = ugettext(
          '1. Information from the organization')
      self.fields['message'].group = ugettext(
          '2. Your message to the organization')

  class Meta:
    model = GSoCRequest
    css_prefix = 'gsoc_request'
    fields = ['message']


class RequestPage(GSoCRequestHandler):
  """Encapsulate all the methods required to generate Request page."""

  def templatePath(self):
    return 'v2/modules/gsoc/invite/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'request/%s$' % url_patterns.ORG,
            self, name='gsoc_request')
    ]

  def checkAccess(self, data, check, mutator):
    """Access checks for GSoC Invite page."""
    check.isProgramVisible()

    # check if the current user has a profile, but is not a student
    check.notStudent()

    # check if the organization exists
    check.isOrganizationInURLActive()

    # check if the user is not already mentor role for the organization
    check.notMentor()

    # check if there is already a request
    query = db.Query(GSoCRequest)
    query.filter('type = ', 'Request')
    query.filter('user = ', data.user)
    query.filter('org = ', data.organization)
    if query.get():
      raise AccessViolation(
          'You have already sent a request to this organization.')

  def context(self, data, check, mutator):
    """Handler for GSoC Request Page HTTP get request."""
    request_form = RequestForm(
        data.organization.role_request_message, data=data.POST or None)

    return {
        'logged_in_msg': LoggedInMsg(data, apply_link=False),
        'profile_created': data.GET.get('profile') == 'created',
        'page_name': 'Request to become a mentor',
        'program': data.program,
        'invite_form': request_form,
    }

  def post(self, data, check, mutator):
    """Handler for GSoC Request Page HTTP post request."""
    request = self._createFromForm(data)
    if request:
      data.redirect.request(request)
      return data.redirect.to('show_gsoc_request')
    else:
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)

  def _createFromForm(self, data):
    """Creates a new request based on the data inserted in the form.

    Args:
      data: A RequestData describing the current request.

    Returns:
      a newly created Request entity or None
    """
    assert isSet(data.organization)

    request_form = RequestForm(data=data.POST)

    if not request_form.is_valid():
      return None

    # create a new invitation entity
    request_form.cleaned_data['user'] = data.user
    request_form.cleaned_data['org'] = data.organization
    request_form.cleaned_data['role'] = 'mentor'
    request_form.cleaned_data['type'] = 'Request'

    admins = profile_logic.getOrgAdmins(data.organization)
    admin_emails = [i.email for i in admins]

    def create_request_txn():
      request = request_form.create(commit=True, parent=data.user)
      context = notifications.requestContext(data, request, admin_emails)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=request)
      sub_txn()
      return request

    return db.run_in_transaction(create_request_txn)


class ShowRequest(GSoCRequestHandler):
  """Encapsulate all the methods required to generate Show Request page.
  """
  # maps actions with button names
  ACTIONS = {
      'accept': 'Accept',
      'reject': 'Reject',
      'resubmit': 'Resubmit',
      'withdraw': 'Withdraw',
      'revoke': 'Revoke',
      }

  def templatePath(self):
    return 'soc/request/base.html'


  def djangoURLPatterns(self):
    return [
        url(r'request/%s$' % url_patterns.USER_ID, self,
            name='show_gsoc_request')
    ]

  def checkAccess(self, data, check, mutator):
    check.isProfileActive()

    request_id = int(data.kwargs['id'])
    invited_user_link_id = data.kwargs['user']
    if invited_user_link_id == data.user.link_id:
      invited_user = data.user
    else:
      invited_user = User.get_by_key_name(invited_user_link_id)

    data.invite = data.request_entity = GSoCRequest.get_by_id(
        request_id, parent=invited_user)
    check.isRequestPresent(request_id)

    data.organization = data.request_entity.org
    data.invited_user = data.request_entity.user
    data.requester = data.request_entity.user

    if data.POST:
      data.action = data.POST['action']

      if data.action == self.ACTIONS['accept']:
        check.canRespondToRequest()
      elif data.action == self.ACTIONS['reject']:
        check.canRespondToRequest()
      elif data.action == self.ACTIONS['resubmit']:
        check.canResubmitRequest()
      # withdraw action
    else:
      check.canViewRequest()

    mutator.canRespondForUser()

    key_name = '/'.join([data.program.key().name(), data.requester.link_id])
    data.requester_profile = GSoCProfile.get_by_key_name(
        key_name, parent=data.requester)

  def context(self, data, check, mutator):
    """Handler to for GSoC Show Request Page HTTP get request."""
    assert isSet(data.request_entity)
    assert isSet(data.can_respond)
    assert isSet(data.organization)
    assert isSet(data.requester)

    # This code is dupcliated between request and invite
    status = data.request_entity.status

    can_accept = can_reject = can_withdraw = can_resubmit = can_revoke = False

    if data.can_respond:
      # admin speaking
      if status == 'pending':
        can_accept = True
        can_reject = True
      if status == 'rejected':
        can_accept = True
      if status == 'accepted':
        can_revoke = True
    else:
      # requester speaking
      if status == 'withdrawn':
        can_resubmit = True
      if status == 'pending':
        can_withdraw = True

    show_actions = (can_accept or can_reject or can_withdraw or
                    can_resubmit or can_revoke)

    org_key = data.organization.key()
    status_msg = None

    if data.requester_profile.key() == data.profile.key():
      if org_key in data.requester_profile.org_admin_for:
        status_msg = DEF_YOU_ARE_ORG_ADMIN
      elif org_key in data.requester_profile.mentor_for:
        status_msg = DEF_YOU_ARE_MENTOR
    else:
      if org_key in data.requester_profile.org_admin_for:
        status_msg = DEF_USER_ORG_ADMIN
      elif org_key in data.requester_profile.mentor_for:
        status_msg = DEF_USER_MENTOR

    return {
        'page_name': "Request to become a mentor",
        'request': data.request_entity,
        'org': data.organization,
        'actions': self.ACTIONS,
        'status_msg': status_msg,
        'user_name': data.requester_profile.name(),
        'user_link_id': data.requester.link_id,
        'user_email': accounts.denormalizeAccount(
            data.requester.account).email(),
        'show_actions': show_actions,
        'can_accept': can_accept,
        'can_reject': can_reject,
        'can_withdraw': can_withdraw,
        'can_resubmit': can_resubmit,
        'can_revoke': can_revoke,
        }

  def post(self, data, check, mutator):
    """Handler to for GSoC Show Request Page HTTP post request."""
    assert isSet(data.action)
    assert isSet(data.request_entity)

    if data.action == self.ACTIONS['accept']:
      self._acceptRequest(data)
    elif data.action == self.ACTIONS['reject']:
      self._rejectRequest(data)
    elif data.action == self.ACTIONS['resubmit']:
      self._resubmitRequest(data)
    elif data.action == self.ACTIONS['withdraw']:
      self._withdrawRequest(data)
    elif data.action == self.ACTIONS['revoke']:
      self._revokeRequest(data)

    # TODO(nathaniel): Make this .program() call unnecessary.
    data.redirect.program()

    return data.redirect.to('gsoc_dashboard')

  def _acceptRequest(self, data):
    """Accepts a request."""
    assert isSet(data.organization)
    assert isSet(data.requester_profile)

    request_key = data.request_entity.key()
    profile_key = data.requester_profile.key()
    organization_key = data.organization.key()
    messages = data.program.getProgramMessages()

    def accept_request_txn():
      request = db.get(request_key)
      profile = db.get(profile_key)

      request.status = 'accepted'

      new_mentor = not profile.is_mentor
      profile.is_mentor = True
      profile.mentor_for.append(organization_key)
      profile.mentor_for = list(set(profile.mentor_for))

      # Send out a welcome email to new mentors.
      if new_mentor:
        mentor_mail = notifications.getMentorWelcomeMailContext(
            profile, data, messages)
        if mentor_mail:
          mailer.getSpawnMailTaskTxn(mentor_mail, parent=request)()

      profile.put()
      request.put()

      context = notifications.handledRequestContext(data, request.status)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=request)
      sub_txn()

    db.run_in_transaction(accept_request_txn)

  def _rejectRequest(self, data):
    """Rejects a request."""
    assert isSet(data.request_entity)
    request_key = data.request_entity.key()

    def reject_request_txn():
      request = db.get(request_key)
      request.status = 'rejected'
      request.put()

      context = notifications.handledRequestContext(data, request.status)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=request)
      sub_txn()

    db.run_in_transaction(reject_request_txn)

  def _resubmitRequest(self, data):
    """Resubmits a request."""
    assert isSet(data.request_entity)
    request_key = data.request_entity.key()

    def resubmit_request_txn():
      request = db.get(request_key)
      request.status = 'pending'
      request.put()

    db.run_in_transaction(resubmit_request_txn)

  def _withdrawRequest(self, data):
    """Withdraws an invitation."""
    assert isSet(data.request_entity)
    request_key = data.request_entity.key()

    def withdraw_request_txn():
      request = db.get(request_key)
      request.status = 'withdrawn'
      request.put()

    db.run_in_transaction(withdraw_request_txn)

  def _revokeRequest(self, data):
    """Withdraws an invitation."""
    assert isSet(data.request_entity)
    assert isSet(data.organization)
    assert isSet(data.requester_profile)

    request_key = data.request_entity.key()
    profile_key = data.requester_profile.key()
    organization_key = data.organization.key()

    def revoke_request_txn():
      request = db.get(request_key)
      profile = db.get(profile_key)

      request.status = 'rejected'
      profile.mentor_for.remove(organization_key)
      if not profile.mentor_for:
        profile.is_mentor = False

      profile.put()
      request.put()

      context = notifications.handledRequestContext(data, 'revoked')
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=request)
      sub_txn()

    db.run_in_transaction(revoke_request_txn)
