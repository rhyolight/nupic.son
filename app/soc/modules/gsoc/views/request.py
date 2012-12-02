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
  """Encapsulate all the methods required to generate Request page.
  """
  def templatePath(self):
    return 'v2/modules/gsoc/invite/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'request/%s$' % url_patterns.ORG,
            self, name='gsoc_request')
    ]

  def checkAccess(self):
    """Access checks for GSoC Invite page.
    """
    self.check.isProgramVisible()

    # check if the current user has a profile, but is not a student
    self.check.notStudent()

    # check if the organization exists
    self.check.isOrganizationInURLActive()

    # check if the user is not already mentor role for the organization
    self.check.notMentor()

    # check if there is already a request
    query = db.Query(GSoCRequest)
    query.filter('type = ', 'Request')
    query.filter('user = ', self.data.user)
    query.filter('org = ', self.data.organization)
    if query.get():
      raise AccessViolation(
          'You have already sent a request to this organization.')

  def context(self):
    """Handler for GSoC Request Page HTTP get request.
    """
    request_form = RequestForm(
        self.data.organization.role_request_message,
        data=self.data.POST or None)

    return {
        'logged_in_msg': LoggedInMsg(self.data, apply_link=False),
        'profile_created': self.data.GET.get('profile') == 'created',
        'page_name': 'Request to become a mentor',
        'program': self.data.program,
        'invite_form': request_form,
    }

  def post(self):
    """Handler for GSoC Request Page HTTP post request.
    """
    request = self._createFromForm()
    if request:
      self.redirect.request(request)
      self.redirect.to('show_gsoc_request')
    else:
      self.get()

  def _createFromForm(self):
    """Creates a new request based on the data inserted in the form.

    Returns:
      a newly created Request entity or None
    """
    assert isSet(self.data.organization)

    request_form = RequestForm(
        data=self.data.POST)

    if not request_form.is_valid():
      return None

    # create a new invitation entity
    request_form.cleaned_data['user'] = self.data.user
    request_form.cleaned_data['org'] = self.data.organization
    request_form.cleaned_data['role'] = 'mentor'
    request_form.cleaned_data['type'] = 'Request'

    q = GSoCProfile.all().filter('org_admin_for', self.data.organization)
    q = q.filter('status', 'active').filter('notify_new_requests', True)
    admins = q.fetch(1000)
    admin_emails = [i.email for i in admins]

    def create_request_txn():
      request = request_form.create(commit=True, parent=self.data.user)
      context = notifications.requestContext(self.data, request, admin_emails)
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

  def checkAccess(self):
    self.check.isProfileActive()

    request_id = int(self.data.kwargs['id'])
    invited_user_link_id = self.data.kwargs['user']
    if invited_user_link_id == self.data.user.link_id:
      invited_user = self.data.user
    else:
      invited_user = User.get_by_key_name(invited_user_link_id)

    self.data.invite = self.data.request_entity = GSoCRequest.get_by_id(
        request_id, parent=invited_user)
    self.check.isRequestPresent(request_id)

    self.data.organization = self.data.request_entity.org
    self.data.invited_user = self.data.requester = self.data.request_entity.user

    if self.data.POST:
      self.data.action = self.data.POST['action']

      if self.data.action == self.ACTIONS['accept']:
        self.check.canRespondToRequest()
      elif self.data.action == self.ACTIONS['reject']:
        self.check.canRespondToRequest()
      elif self.data.action == self.ACTIONS['resubmit']:
        self.check.canResubmitRequest()
      # withdraw action
    else:
      self.check.canViewRequest()

    self.mutator.canRespondForUser()

    key_name = '/'.join([
        self.data.program.key().name(),
        self.data.requester.link_id])
    self.data.requester_profile = GSoCProfile.get_by_key_name(
        key_name, parent=self.data.requester)

  def context(self):
    """Handler to for GSoC Show Request Page HTTP get request.
    """
    assert isSet(self.data.request_entity)
    assert isSet(self.data.can_respond)
    assert isSet(self.data.organization)
    assert isSet(self.data.requester)

    # This code is dupcliated between request and invite
    status = self.data.request_entity.status

    can_accept = can_reject = can_withdraw = can_resubmit = can_revoke = False

    if self.data.can_respond:
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

    org_key = self.data.organization.key()
    status_msg = None

    if self.data.requester_profile.key() == self.data.profile.key():
      if org_key in self.data.requester_profile.org_admin_for:
        status_msg = DEF_YOU_ARE_ORG_ADMIN
      elif org_key in self.data.requester_profile.mentor_for:
        status_msg = DEF_YOU_ARE_MENTOR
    else:
      if org_key in self.data.requester_profile.org_admin_for:
        status_msg = DEF_USER_ORG_ADMIN
      elif org_key in self.data.requester_profile.mentor_for:
        status_msg = DEF_USER_MENTOR

    return {
        'page_name': "Request to become a mentor",
        'request': self.data.request_entity,
        'org': self.data.organization,
        'actions': self.ACTIONS,
        'status_msg': status_msg,
        'user_name': self.data.requester_profile.name(),
        'user_link_id': self.data.requester.link_id,
        'user_email': accounts.denormalizeAccount(
            self.data.requester.account).email(),
        'show_actions': show_actions,
        'can_accept': can_accept,
        'can_reject': can_reject,
        'can_withdraw': can_withdraw,
        'can_resubmit': can_resubmit,
        'can_revoke': can_revoke,
        }

  def post(self):
    """Handler to for GSoC Show Request Page HTTP post request.
    """
    assert isSet(self.data.action)
    assert isSet(self.data.request_entity)

    if self.data.action == self.ACTIONS['accept']:
      self._acceptRequest()
    elif self.data.action == self.ACTIONS['reject']:
      self._rejectRequest()
    elif self.data.action == self.ACTIONS['resubmit']:
      self._resubmitRequest()
    elif self.data.action == self.ACTIONS['withdraw']:
      self._withdrawRequest()
    elif self.data.action == self.ACTIONS['revoke']:
      self._revokeRequest()

    self.redirect.program()
    self.redirect.to('gsoc_dashboard')

  def _acceptRequest(self):
    """Accepts a request.
    """
    assert isSet(self.data.organization)
    assert isSet(self.data.requester_profile)

    request_key = self.data.request_entity.key()
    profile_key = self.data.requester_profile.key()
    organization_key = self.data.organization.key()
    messages = self.data.program.getProgramMessages()

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
            profile, self.data, messages)
        if mentor_mail:
          mailer.getSpawnMailTaskTxn(mentor_mail, parent=request)()

      profile.put()
      request.put()

      context = notifications.handledRequestContext(self.data, request.status)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=request)
      sub_txn()

    db.run_in_transaction(accept_request_txn)

  def _rejectRequest(self):
    """Rejects a request. 
    """
    assert isSet(self.data.request_entity)
    request_key = self.data.request_entity.key()

    def reject_request_txn():
      request = db.get(request_key)
      request.status = 'rejected'
      request.put()

      context = notifications.handledRequestContext(self.data, request.status)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=request)
      sub_txn()

    db.run_in_transaction(reject_request_txn)

  def _resubmitRequest(self):
    """Resubmits a request.
    """
    assert isSet(self.data.request_entity)
    request_key = self.data.request_entity.key()

    def resubmit_request_txn():
      request = db.get(request_key)
      request.status = 'pending'
      request.put()

    db.run_in_transaction(resubmit_request_txn)

  def _withdrawRequest(self):
    """Withdraws an invitation.
    """
    assert isSet(self.data.request_entity)
    request_key = self.data.request_entity.key()

    def withdraw_request_txn():
      request = db.get(request_key)
      request.status = 'withdrawn'
      request.put()

    db.run_in_transaction(withdraw_request_txn)

  def _revokeRequest(self):
    """Withdraws an invitation.
    """
    assert isSet(self.data.request_entity)
    assert isSet(self.data.organization)
    assert isSet(self.data.requester_profile)

    request_key = self.data.request_entity.key()
    profile_key = self.data.requester_profile.key()
    organization_key = self.data.organization.key()

    def revoke_request_txn():
      request = db.get(request_key)
      profile = db.get(profile_key)

      request.status = 'rejected'
      profile.mentor_for.remove(organization_key)
      if not profile.mentor_for:
        profile.is_mentor = False

      profile.put()
      request.put()

      context = notifications.handledRequestContext(self.data, 'revoked')
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=request)
      sub_txn()

    db.run_in_transaction(revoke_request_txn)
