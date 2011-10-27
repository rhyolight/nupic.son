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

"""Module containing the view for GCI invitation page.
"""

__authors__ = [
  '"Daniel Hans" <daniel.m.hans@gmail.com>',
  ]


from django.utils.translation import ugettext

from google.appengine.api import users
from google.appengine.ext import db

from soc.logic import accounts
from soc.logic import cleaning
from soc.logic.exceptions import NotFound
from soc.logic.helper import notifications

from soc.views.helper import url_patterns
from soc.views.helper.access_checker import isSet

from soc.tasks import mailer

from soc.modules.gci.models.profile import GCIProfile
from soc.modules.gci.models.request import GCIRequest

from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.base import RequestHandler
from soc.modules.gci.views.helper.url_patterns import url


USER_DOES_NOT_EXIST = ugettext('User %s not found.')
USER_ALREADY_INVITED = ugettext(
    'User %s has already been invited to become %s.')
USER_HAS_NO_PROFILE = ugettext(
    'User %s must create a profile for this program.')
USER_IS_STUDENT = ugettext('User %s is a student for this program.')
USER_ALREADY_HAS_ROLE = ugettext(
     'User %s already has %s role for this program.')

class InviteForm(gci_forms.GCIModelForm):
  """Django form for the invite page.
  """

  identifiers = gci_forms.CharField(label='Username/Email')

  class Meta:
    model = GCIRequest
    css_prefix = 'gci_intivation'
    fields = ['message']

  def __init__(self, request_data, *args, **kwargs):
    super(InviteForm, self).__init__(*args, **kwargs)

    # store request object to cache results of queries
    self.request_data = request_data

    # reorder the fields so that link_id is the first one
    field = self.fields.pop('identifiers')
    self.fields.insert(0, 'identifiers', field)
    field.help_text = ugettext(
        "Comma separated usernames or emails of the people to invite.")
    
  def clean_identifiers(self):
    """Accepts link_ids or email addresses of users which may be invited.
    """

    assert isSet(self.request_data.organization)

    users_to_invite = []
    identifiers = self.cleaned_data.get('identifiers', '').split(',')

    for identifier in identifiers:
      self.cleaned_data['identifier'] = identifier.strip()
      user = self._clean_identifier(identifier)
      users_to_invite.append(user)

    self.request_data.users_to_invite = users_to_invite

  def _clean_identifier(self, identifier):
    link_id_cleaner = cleaning.clean_link_id('identifier')
    
    # first check if the field represents a valid link_id
    try:
      existing_user_cleaner = cleaning.clean_existing_user('identifier')
      user_to_invite = existing_user_cleaner(self)
    except gci_forms.ValidationError, e:
      if e.code != 'invalid':
        raise
      
      # otherwise check if the field represents a valid email address
      email_cleaner = cleaning.clean_email('identifier')
      try:
        email = email_cleaner(self)
      except:
        if e.code != 'invalid':
          raise

        account = users.User(email_address)
        user_account = accounts.normalizeAccount(account)
        user_to_invite = User.all().filter('account', user_account).get()

    # check if the user entity has been found
    if not user_to_invite:
      raise gci_forms.ValidationError(USER_DOES_NOT_EXIST % (identifier))

    # check if the organization has already sent an invitation to the user
    query = self._getQueryForExistingRequests(user_to_invite)
    if query.get():
      role = self.request_data.kwargs['role']
      raise gci_forms.ValidationError(
          USER_ALREADY_INVITED % (identifier, role))

    # check if the user that is invited does not have the role
    profile = self.request_data.invite_profile \
        = self._getProfile(user_to_invite)

    if not profile:
      raise gci_forms.ValidationError(USER_HAS_NO_PROFILE % identifier)

    if profile.student_info:
      raise gci_forms.ValidationError(USER_IS_STUDENT % identifier)

    if self.request_data.kwargs['role'] == 'org_admin':
      role_for = profile.org_admin_for
    else:
      role_for = set(profile.org_admin_for + profile.mentor_for)

    if self.request_data.organization.key() in role_for:
      role = self.request_data.kwargs['role']
      raise gci_forms.ValidationError(
          USER_ALREADY_HAS_ROLE % (identifier, role))

    return user_to_invite

  def _getQueryForExistingRequests(self, user_to_invite):
    query = db.Query(GCIRequest, keys_only=True)
    query.filter('type', 'Invitation')
    query.filter('user', user_to_invite)
    query.filter('role', self.request_data.kwargs['role'])
    query.filter('org', self.request_data.organization)
    return query
  
  def _getProfile(self, user_to_invite):
    key_name = '/'.join([
        self.request_data.program.key().name(), user_to_invite.link_id])
    return GCIProfile.get_by_key_name(key_name, parent=user_to_invite)


class ManageInviteForm(gci_forms.GCIModelForm):
  """Django form for the manage invitation page.
  """

  class Meta:
    model = GCIRequest
    css_prefix = 'gci_intivation'
    fields = ['message']

class InvitePage(RequestHandler):
  """Encapsulate all the methods required to generate Invite page.
  """

  def templatePath(self):
    return 'v2/modules/gci/invite/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'invite/%s$' % url_patterns.INVITE,
            self, name='gci_invite')
    ]

  def checkAccess(self):
    """Access checks for GCI Invite page.
    """

    self.check.isProgramVisible()
    self.check.isOrgAdmin()

  def context(self):
    """Handler to for GSoC Invitation Page HTTP get request.
    """

    role = 'Org Admin' if self.data.kwargs['role'] == 'org_admin' else 'Mentor'

    invite_form = InviteForm(self.data, self.data.POST or None)

    return {
        'logout_link': self.data.redirect.logout(),
        'page_name': 'Invite a new %s' % role,
        'program': self.data.program,
        'forms': [invite_form]
    }

  def validate(self):
    """Creates new invitation based on the data inserted in the form.

    Returns:
      True if the new invitations have been successfully saved; False otherwise
    """

    assert isSet(self.data.organization)

    invite_form = InviteForm(self.data, self.data.POST)
    
    if not invite_form.is_valid():
      return False

    assert isSet(self.data.users_to_invite)
    assert len(self.data.users_to_invite)

    # create a new invitation entity

    invite_form.cleaned_data['org'] = self.data.organization
    invite_form.cleaned_data['role'] = self.data.kwargs['role']
    invite_form.cleaned_data['type'] = 'Invitation'

    def create_invite_txn():
      invite = invite_form.create(commit=True)
      #context = notifications.inviteContext(self.data, invite)
      #sub_txn = mailer.getSpawnMailTaskTxn(context, parent=invite)
      #sub_txn()
      return invite

    for user in self.data.users_to_invite:
      invite_form.instance = None
      invite_form.cleaned_data['user'] = user
      db.run_in_transaction(create_invite_txn)

    return True

  def post(self):
    """Handler to for GCI Invitation Page HTTP post request.
    """

    if not self.validate():
      self.get()
      return

    self.redirect.dashboard().to()


class ManageInvite(RequestHandler):
  """View to manage the invitation by organization admins.
  """

  def templatePath(self):
    return 'v2/modules/gci/invite/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'invite/manage/%s$' % url_patterns.ID, self,
            name='manage_gci_invite')
    ]

  def checkAccess(self):
    self.check.isProfileActive()
    
    invite_id = int(self.data.kwargs['id'])
    self.data.invite = GCIRequest.get_by_id(invite_id)
    self.check.isInvitePresent(invite_id)

    # get invited user and check if it is not deleted
    self.data.invited_user = self.data.invite.user
    if not self.data.invited_user:
      logging.warning(
          'User entity does not exist for request with id %s', invite_id)
      raise NotFound('Invited user does not exist')

    # get the organization and check if the current user can manage the invite
    self.data.organization = self.data.invite.org
    self.check.isOrgAdmin()

  def context(self):
    page_name = self._constructPageName()

    form = ManageInviteForm(
        self.data.POST or None, instance=self.data.invite)

    button_value = self._constructButtonValue()

    return {
        'page_name': page_name,
        'forms': [form],
        'button_value': button_value
        }

  def _constructPageName(self):
    invite = self.data.invite
    return "%s Invite For %s" % (invite.role, self.data.invited_user.name)

  def _constructButtonValue(self):
    invite = self.data.invite
    if invite.status == 'pending':
      return 'Withdraw'
    if invite.status == 'withdrawn':
      return 'Resubmit'

  def _withdrawInvitation(self):
    """Withdraws an invitation.
    """
    assert isSet(self.data.invite)
    invite_key = self.data.invite.key()

    def withdraw_invite_txn():
      invite = db.get(invite_key)
      invite.status = 'withdrawn'
      invite.put()

      context = notifications.handledInviteContext(self.data)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=invite)
      sub_txn()

    db.run_in_transaction(withdraw_invite_txn)

  def _resubmitInvitation(self):
    """Resubmits an invitation. 
    """
    assert isSet(self.data.invite)
    invite_key = self.data.invite.key()

    def resubmit_invite_txn():
      invite = db.get(invite_key)
      invite.status = 'pending'
      invite.put()

      context = notifications.handledInviteContext(self.data)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=invite)
      sub_txn()

    db.run_in_transaction(resubmit_invite_txn)


class RespondInvite(RequestHandler):
  """View to respond to the invitation by the user.
  """

  def djangoURLPatterns(self):
    return [
        url(r'respond_invite/%s$' % url_patterns.ID, self,
            name='respond_gci_invite')
    ]

  def checkAccess(self):
    pass


class ShowInvite(RequestHandler):
  """Encapsulate all the methods required to generate Show Invite page.
  """

  ACTIONS = {
      'accept': 'Accept',
      'reject': 'Reject',
      'resubmit': 'Resubmit',
      'withdraw': 'Withdraw',
      }

  def templatePath(self):
    return 'v2/soc/request/base.html'


  def djangoURLPatterns(self):
    return [
        url(r'invitation/%s$' % url_patterns.ID, self,
            name='show_gci_invite')
    ]

  def checkAccess(self):
    self.check.isProfileActive()
    
    id = int(self.data.kwargs['id'])
    self.data.invite = Request.get_by_id(id)
    self.check.isRequestPresent(self.data.invite, id)

    self.data.organization = self.data.invite.org
    self.data.invited_user = self.data.invite.user

    if self.data.POST:
      self.data.action = self.data.POST['action']

      if self.data.action == self.ACTIONS['accept']:
        self.check.canRespondToInvite()
      elif self.data.action == self.ACTIONS['reject']:
        self.check.canRespondToInvite()
      elif self.data.action == self.ACTIONS['resubmit']:
        self.check.canResubmitInvite()
    else:
      self.check.canViewInvite()

    self.mutator.canRespondForUser()

    if self.data.user.key() == self.data.invited_user.key():
      self.data.invited_profile = self.data.profile
      return

    key_name = '/'.join([
        self.data.program.key().name(),
        self.data.invited_user.link_id])
    self.data.invited_profile = GCIProfile.get_by_key_name(
        key_name, parent=self.data.invited_user)

  def context(self):
    """Handler to for GSoC Show Invitation Page HTTP get request.
    """

    assert isSet(self.data.invite)
    assert isSet(self.data.can_respond)
    assert isSet(self.data.organization)
    assert isSet(self.data.invited_user)
    assert isSet(self.data.invited_profile)
    assert self.data.invited_profile

    # This code is dupcliated between request and invite
    status = self.data.invite.status

    can_accept = can_reject = can_withdraw = can_resubmit = False

    if self.data.can_respond:
      # invitee speaking
      if status == 'pending':
        can_accept = True
        can_reject = True
      if status == 'rejected':
        can_accept = True
    else:
      # admin speaking
      if status == 'withdrawn':
        can_resubmit = True
      if status == 'pending':
        can_withdraw = True

    show_actions = can_accept or can_reject or can_withdraw or can_resubmit

    org_key = self.data.organization.key()
    status_msg = None

    if self.data.invited_profile.key() == self.data.profile.key():
      if org_key in self.data.invited_profile.org_admin_for:
        status_msg = "You are now an organization administrator for this organization."
      elif org_key in self.data.invited_profile.mentor_for:
        status_msg = "You are now a mentor for this organization."
    else:
      if org_key in self.data.invited_profile.org_admin_for:
        status_msg = "This user is now an organization administrator with your organization."
      elif org_key in self.data.invited_profile.mentor_for:
        status_msg = "This user is now a mentor with your organization."

    return {
        'request': self.data.invite,
        'page_name': "Invite",
        'org': self.data.organization,
        'actions': self.ACTIONS,
        'status_msg': status_msg,
        'user_name': self.data.invited_profile.name(),
        'user_link_id': self.data.invited_user.link_id,
        'user_email': accounts.denormalizeAccount(
            self.data.invited_user.account).email(),
        'show_actions': show_actions,
        'can_accept': can_accept,
        'can_reject': can_reject,
        'can_withdraw': can_withdraw,
        'can_resubmit': can_resubmit,
        } 

  def post(self):
    """Handler to for GSoC Show Invitation Page HTTP post request.
    """

    assert self.data.action
    assert self.data.invite

    if self.data.action == self.ACTIONS['accept']:
      self._acceptInvitation()
    elif self.data.action == self.ACTIONS['reject']:
      self._rejectInvitation()
    elif self.data.action == self.ACTIONS['resubmit']:
      self._resubmitInvitation()
    elif self.data.action == self.ACTIONS['withdraw']:
      self._withdrawInvitation()

    self.redirect.dashboard()
    self.redirect.to()

  def _acceptInvitation(self):
    """Accepts an invitation.
    """

    assert isSet(self.data.organization)

    if not self.data.profile:
      self.redirect.program()
      self.redirect.to('edit_gsoc_profile')

    invite_key = self.data.invite.key()
    profile_key = self.data.profile.key()
    organization_key = self.data.organization.key()

    def accept_invitation_txn():
      invite = db.get(invite_key)
      profile = db.get(profile_key)

      invite.status = 'accepted'

      if invite.role != 'mentor':
        profile.is_org_admin = True
        profile.org_admin_for.append(organization_key)
        profile.org_admin_for = list(set(profile.org_admin_for))

      profile.is_mentor = True
      profile.mentor_for.append(organization_key)
      profile.mentor_for = list(set(profile.mentor_for))

      invite.put()
      profile.put()

    accept_invitation_txn()
    # TODO(SRabbelier): run in txn as soon as we make User Request's parent
    # db.run_in_transaction(accept_invitation_txn)

  def _rejectInvitation(self):
    """Rejects a invitation. 
    """
    assert isSet(self.data.invite)
    invite_key = self.data.invite.key()

    def reject_invite_txn():
      invite = db.get(invite_key)
      invite.status = 'rejected'
      invite.put()

    db.run_in_transaction(reject_invite_txn)
