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

"""Module containing the view for GSoC invitation page.
"""


from google.appengine.ext import db
from google.appengine.api import users

from django import forms as djangoforms
from django.utils.translation import ugettext

from soc.logic import accounts
from soc.logic import cleaning
from soc.logic.helper import notifications
from soc.models.user import User
from soc.views.helper import url_patterns
from soc.views.helper.access_checker import isSet
from soc.tasks import mailer

from soc.modules.gsoc.models.connection import GSoCConnection
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.helper.url_patterns import url
from soc.modules.gsoc.views import forms as gsoc_forms


DEF_STATUS_FOR_USER_MSG = ugettext(
    'You are now %s for this organization.')

DEF_STATUS_FOR_ADMIN_MSG = ugettext(
    'This user is now %s with your organization.')


class ConnectionForm(gsoc_forms.GSoCModelForm):
  """ Django form for creating or editing a connection between a user
   and an organization for mentor/org admin invitations/requests """
  link_id = gsoc_forms.CharField(label='Link ID/Email')
  
  class Meta:
  	model = GSoCConnection
  	fields = ['message']
  	widgets = {
  	    'message':gsoc_forms.Textarea(attrs={'cols':80, 'rows':10})
  	}  	
  	
  def __init__(self, request_data, *args, **kwargs):
    super(ConnectionForm, self).__init__(*args, **kwargs)

    # store request object to cache results of queries
    self.request_data = request_data

    # reorder the fields so that link_id is the first one
    field = self.fields.pop('link_id')
    self.fields.insert(0, 'link_id', field)
    field.help_text = ugettext(
        'The link_id or email address of the invitee, '
        ' separate multiple values with a comma')
        
    field = self.fields['message']
    field.help_text = ugettext('An optional message for the user')
    field.label = ugettext('Message')
    
  def clean_link_id(self):
    """Accepts link_id of users which may be invited.
    """

    assert isSet(self.request_data.organization)

    link_ids = self.cleaned_data.get('link_id', '').split(',')

    self.request_data.connected_user = []

    for link_id in link_ids:
      self.cleaned_data['link_id'] = link_id.strip()
      self._clean_one_link_id()

  def _clean_one_link_id(self):
    connected_user = None

    link_id_cleaner = cleaning.clean_link_id('link_id')

    try:
      link_id = link_id_cleaner(self)
    except djangoforms.ValidationError, e:
      if e.code != 'invalid':
        raise

      email_cleaner = cleaning.clean_email('link_id')

      try:
        email_address = email_cleaner(self)
      except djangoforms.ValidationError, e:
        if e.code != 'invalid':
          raise
        msg = ugettext(u'Enter a valid link_id or email address.')
        raise djangoforms.ValidationError(msg, code='invalid')

      account = users.User(email_address)
      user_account = accounts.normalizeAccount(account)
      invited_user = User.all().filter('account', user_account).get()

      if not connected_user:
        raise djangoforms.ValidationError(
            'There is no user with that email address')

    # get the user entity that the invitation is to
    if not connected_user:
      existing_user_cleaner = cleaning.clean_existing_user('link_id')
      connected_user = existing_user_cleaner(self)

    self.request_data.connected_user.append(connected_user)

    # check if the organization has already sent an invitation to the user
    query = db.Query(GSoCConnection)
    query.filter('user', connected_user)
    query.filter('organization', self.request_data.organization)
    if query.get():
      raise djangoforms.ValidationError(
          'An invitation to this user has already been sent.')

    # check if the user that is invited does not have the role
    key_name = '/'.join([
        self.request_data.program.key().name(),
        connected_user.link_id])
    profile = self.request_data.invite_profile = GSoCProfile.get_by_key_name(
        key_name, parent=connected_user)

    if not profile:
      msg = ('The specified user has a User account (the link_id is valid), '
             'but they do not yet have a profile for this %s. '
             'You cannot invite them until they create a profile.')
      raise djangoforms.ValidationError(msg % self.request_data.program.name)

    if profile.student_info:
      raise djangoforms.ValidationError('That user is a student')

    if self.request_data.kwargs['role'] == 'org_admin':
      role_for = profile.org_admin_for
    else:
      role_for = set(profile.org_admin_for + profile.mentor_for)

    if self.request_data.organization.key() in role_for:
      raise djangoforms.ValidationError('That user already has this role.')


class InvitePage(RequestHandler):
  """Encapsulate all the methods required to generate Invite page.
  """

  def templatePath(self):
    return 'v2/modules/gsoc/invite/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'invite/%s$' % url_patterns.INVITE,
            self, name='gsoc_invite')
    ]

  def checkAccess(self):
    """Access checks for GSoC Invite page.
    """

    self.check.isProgramVisible()
    self.check.isOrgAdmin()

  def context(self):
    """Handler to for GSoC Invitation Page HTTP get request.
    """
    role = 'Org Admin' if self.data.kwargs['role'] == 'org_admin' else 'Mentor'
    
    conn_form = ConnectionForm(self.data, self.data.POST or None)
    return {
        'logout_link': self.data.redirect.logout(),
        'page_name': 'Invite a new %s' % role,
        'program': self.data.program,
        'invite_form': conn_form,
        'error': bool(conn_form.errors)
    }

  def _createFromForm(self):
    """Creates a new connection based on the data inserted in the form.

    Returns:
      a newly created Connection entity or None
    """
    assert isSet(self.data.organization)
	
    connection_form = ConnectionForm(self.data, self.data.POST)
    
    if not connection_form.is_valid():
      return None

    assert isSet(self.data.connected_user)
    assert self.data.connected_user

    # create a new connection entity
    connection_form.cleaned_data['organization'] = self.data.organization
    # temporary fix for a query in dashboard.py
    connection_form.cleaned_data['org_name'] = self.data.organization.name
    connection_form.cleaned_data['user_action'] = 'pending'
    connection_form.cleaned_data['org_action'] = 'accepted'

    def create_invite_txn(user):
      connection = connection_form.create(commit=True, parent=user)
      # TODO(dcrodman): Make this work for connections
      #context = notifications.inviteContext(self.data, connection)
      #sub_txn = mailer.getSpawnMailTaskTxn(context, parent=connection)
      #sub_txn()

    for user in self.data.user_connections:
      connection_form.instance = None
      connection_form.cleaned_data['user'] = user
      db.run_in_transaction(create_invite_txn, user)

    return True

  def post(self):
    """Handler to for GSoC Invitation Page HTTP post request.
    """

    if self._createFromForm():
      self.redirect.invite()
      self.redirect.to('gsoc_invite', validated=True)
    else:
      self.get()


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
        url(r'invitation/%s$' % url_patterns.USER_ID, self,
            name='gsoc_invitation')
    ]

  def checkAccess(self):
    self.check.isProfileActive()

    conn_id = int(self.data.kwargs['id'])
    user_link_id = self.data.kwargs['user']
    if user_link_id == self.data.user.link_id:
      connected_user = self.data.user
    else:
      connected_user = User.get_by_key_name(user_link_id)

    self.data.connection = GSoCConnection.get_by_id(conn_id, 
                                                       parent=connected_user)
    self.check.isConnectionPresent(conn_id)

    self.data.organization = self.data.connection.organization
    self.data.connected_user = connected_user

    if self.data.POST:
      self.data.action = self.data.POST['action']

      if self.data.action == self.ACTIONS['accept']:
        self.check.canRespondToConnection()
      elif self.data.action == self.ACTIONS['reject']:
        self.check.canRespondToConnection()
      elif self.data.action == self.ACTIONS['resubmit']:
        self.check.canResubmitConnection()
    else:
      self.check.canViewConnection()

    self.mutator.canRespondForUser()

    if self.data.user.key() == self.data.connected_user.key():
      self.data.invited_profile = self.data.profile
      return

    key_name = '/'.join([
        self.data.program.key().name(),
        self.data.invited_user.link_id])
    self.data.connected_profile = GSoCProfile.get_by_key_name(
        key_name, parent=self.data.connected_user)

  def context(self):
    """Handler to for GSoC Show Invitation Page HTTP get request.
    """

    assert isSet(self.data.connection)
    assert isSet(self.data.can_respond)
    assert isSet(self.data.organization)
    assert isSet(self.data.connected_user)
    assert isSet(self.data.connected_profile)
    assert self.data.connected_profile

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

    if self.data.connected_profile.key() == self.data.profile.key():
      if org_key in self.data.connected_profile.org_admin_for:
        status_msg =  DEF_STATUS_FOR_USER_MSG % 'an organization administrator'
      elif org_key in self.data.connected_profile.mentor_for:
        status_msg =  DEF_STATUS_FOR_USER_MSG % 'a mentor'
    else:
      if org_key in self.data.connected_profile.org_admin_for:
        status_msg = DEF_STATUS_FOR_ADMIN_MSG % 'an organization administrator'
      elif org_key in self.data.connected_profile.mentor_for:
        status_msg = DEF_STATUS_FOR_ADMIN_MSG % 'a mentor'

    return {
        'request': self.data.connection,
        'page_name': 'Invite',
        'org': self.data.organization,
        'actions': self.ACTIONS,
        'status_msg': status_msg,
        'user_name': self.data.connected_profile.name(),
        'user_link_id': self.data.connected_user.link_id,
        'user_email': accounts.denormalizeAccount(
            self.data.connected_user.account).email(),
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
      self._acceptConnection()
    elif self.data.action == self.ACTIONS['reject']:
      self._rejectConnection()
    elif self.data.action == self.ACTIONS['resubmit']:
      self._resubmitConnection()
    elif self.data.action == self.ACTIONS['withdraw']:
      self._withdrawConnection()

    self.redirect.dashboard()
    self.redirect.to()

  def _acceptConnection(self):
    """Accepts an invitation.
    """

    assert isSet(self.data.organization)

    if not self.data.profile:
      self.redirect.program()
      self.redirect.to('edit_gsoc_profile', secure=True)

    connection_key = self.data.connection.key()
    profile_key = self.data.profile.key()
    organization_key = self.data.organization.key()

    def accept_connection_txn():
      connection = db.get(connection_key)
      profile = db.get(profile_key)

      connection.status = 'accepted'

      if connection.role != 'mentor':
        profile.is_org_admin = True
        profile.org_admin_for.append(organization_key)
        profile.org_admin_for = list(set(profile.org_admin_for))

      profile.is_mentor = True
      profile.mentor_for.append(organization_key)
      profile.mentor_for = list(set(profile.mentor_for))

      connection.put()
      profile.put()

    db.run_in_transaction(accept_connection_txn)

  def _rejectInvitation(self):
    """Rejects a invitation. 
    """
    assert isSet(self.data.connection)
    connection_key = self.data.connection.key()

    def reject_invite_txn():
      connection = db.get(invite_key)
      connection.status = 'rejected'
      connection.put()

    db.run_in_transaction(reject_invite_txn)

  def _resubmitInvitation(self):
    """Resubmits a invitation. 
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
