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

"""Module containing the view for GCI invitation page."""

import logging

from django.utils.translation import ugettext

from google.appengine.api import users
from google.appengine.ext import db

from melange.request import exception
from soc.logic import accounts
from soc.logic import cleaning
from soc.logic import invite as invite_logic
from soc.logic.helper import notifications

from soc.models.user import User

from soc.views.helper import lists
from soc.views.helper import url_patterns
from soc.views.helper.access_checker import isSet
from soc.views.template import Template

from soc.tasks import mailer

from soc.modules.gci.models.profile import GCIProfile
from soc.modules.gci.models.request import GCIRequest

from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views.helper import url_names
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

  def __init__(self, request_data=None, **kwargs):
    super(InviteForm, self).__init__(**kwargs)

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
    user_to_invite = None

    # first check if the field represents a valid link_id
    try:
      existing_user_cleaner = cleaning.clean_existing_user('identifier')
      user_to_invite = existing_user_cleaner(self)
    except gci_forms.ValidationError as e:
      if e.code != 'invalid':
        raise

      # otherwise check if the field represents a valid email address
      email_cleaner = cleaning.clean_email('identifier')
      try:
        email = email_cleaner(self)
      except gci_forms.ValidationError as e:
        if e.code != 'invalid':
          raise
        msg = ugettext(u'Enter a valid link_id or email address.')
        raise gci_forms.ValidationError(msg, code='invalid')

      account = users.User(email)
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
    # TODO(dhans): in the ideal world, we want to invite Users with no profiles
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


class InvitePage(GCIRequestHandler):
  """Encapsulate all the methods required to generate Invite page."""

  def templatePath(self):
    return 'modules/gci/invite/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'invite/%s$' % url_patterns.INVITE,
            self, name=url_names.GCI_SEND_INVITE)
    ]

  def checkAccess(self, data, check, mutator):
    """Access checks for GCI Invite page."""
    check.isProgramVisible()
    check.isOrgAdmin()

  def context(self, data, check, mutator):
    """Handler to for GCI Invitation Page HTTP get request."""

    role = 'Org Admin' if data.kwargs['role'] == 'org_admin' else 'Mentor'

    invite_form = InviteForm(request_data=data, data=data.POST or None)

    return {
        'logout_link': self.linker.logout(data.request),
        'page_name': 'Invite a new %s' % role,
        'program': data.program,
        'forms': [invite_form],
    }

  def validate(self, data):
    """Creates new invitation based on the data inserted in the form.

    Args:
      data: A RequestHandler describing the current request.

    Returns:
      True if the new invitations have been successfully saved; False otherwise
    """

    assert isSet(data.organization)

    invite_form = InviteForm(request_data=data, data=data.POST)

    if not invite_form.is_valid():
      return False

    assert isSet(data.users_to_invite)
    assert len(data.users_to_invite)

    # create a new invitation entity

    invite_form.cleaned_data['org'] = data.organization
    invite_form.cleaned_data['role'] = data.kwargs['role']
    invite_form.cleaned_data['type'] = 'Invitation'

    def create_invite_txn(user):
      invite = invite_form.create(commit=True, parent=user)
      context = notifications.inviteContext(data, invite)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=invite)
      sub_txn()
      return invite

    for user in data.users_to_invite:
      invite_form.instance = None
      invite_form.cleaned_data['user'] = user
      db.run_in_transaction(create_invite_txn, user)

    return True

  def post(self, data, check, mutator):
    """Handler to for GCI Invitation Page HTTP post request."""
    if self.validate(data):
      return data.redirect.dashboard().to()
    else:
      # TODO(nathaniel): problematic self-call.
      return self.get(data, check, mutator)


class ManageInvite(GCIRequestHandler):
  """View to manage the invitation by organization admins."""

  def templatePath(self):
    return 'modules/gci/invite/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'invite/manage/%s$' % url_patterns.USER_ID, self,
            name=url_names.GCI_MANAGE_INVITE)
    ]

  def checkAccess(self, data, check, mutator):
    check.isProfileActive()

    key_name = data.kwargs['user']
    user_key = db.Key.from_path('User', key_name)

    invite_id = int(data.kwargs['id'])
    data.invite = GCIRequest.get_by_id(invite_id, parent=user_key)
    check.isInvitePresent(invite_id)

    # get invited user and check if it is not deleted
    data.invited_user = data.invite.user
    if not data.invited_user:
      logging.warning(
          'User entity does not exist for request with id %s', invite_id)
      raise exception.NotFound(message='Invited user does not exist')

    # get the organization and check if the current user can manage the invite
    data.organization = data.invite.org
    check.isOrgAdmin()

    if data.POST:
      if 'withdraw' in data.POST:
        check.canInviteBeWithdrawn()
      elif 'resubmit' in data.POST:
        check.canInviteBeResubmitted()
      else:
        raise exception.BadRequest(
            message='No action specified in manage_gci_invite request.')

  def context(self, data, check, mutator):
    page_name = self._constructPageName(data)

    form = ManageInviteForm(data=data.POST or None, instance=data.invite)

    button_name = self._constructButtonName(data)
    button_value = self._constructButtonValue(data)

    return {
        'page_name': page_name,
        'forms': [form],
        'button_name': button_name,
        'button_value': button_value
        }

  def post(self, data, check, mutator):
    # it is needed to handle notifications
    data.invited_profile = self._getInvitedProfile(data)

    if 'withdraw' in data.POST:
      invite_logic.withdrawInvite(data)
    elif 'resubmit' in data.POST:
      invite_logic.resubmitInvite(data)

    return data.redirect.userId().to(url_names.GCI_MANAGE_INVITE)

  def _constructPageName(self, data):
    invite = data.invite
    return "%s Invite For %s" % (invite.role, data.invited_user.name)

  def _constructButtonName(self, data):
    invite = data.invite
    if invite.status == 'pending':
      return 'withdraw'
    if invite.status in ['withdrawn', 'rejected']:
      return 'resubmit'

  def _constructButtonValue(self, data):
    invite = data.invite
    if invite.status == 'pending':
      return 'Withdraw'
    if invite.status in ['withdrawn', 'rejected']:
      return 'Resubmit'

  def _getInvitedProfile(self, data):
    key_name = '/'.join([
        data.program.key().name(),
        data.invited_user.link_id])
    return GCIProfile.get_by_key_name(key_name, parent=data.invited_user)


class RespondInvite(GCIRequestHandler):
  """View to respond to the invitation by the user."""

  def templatePath(self):
    return 'modules/gci/invite/show.html'

  def djangoURLPatterns(self):
    return [
        url(r'invite/respond/%s$' % url_patterns.ID, self,
            name=url_names.GCI_RESPOND_INVITE)
    ]

  def checkAccess(self, data, check, mutator):
    check.isUser()

    invite_id = int(data.kwargs['id'])
    data.invite = GCIRequest.get_by_id(invite_id, parent=data.user)
    check.isInvitePresent(invite_id)

    check.canRespondInvite()
    data.is_respondable = data.invite.status == 'pending'

    # actual response may be sent only to pending requests
    if data.POST:
      if 'accept' not in data.POST and 'reject' not in data.POST:
        raise exception.BadRequest(
            message='Valid action is not specified in the request.')
      check.isInviteRespondable()

  def context(self, data, check, mutator):
    page_name = self._constructPageName(data)
    return {
        'is_respondable': data.is_respondable,
        'page_name': page_name,
        'request': data.invite
        }

  def post(self, data, check, mutator):
    if 'accept' in data.POST:
      if not data.profile:
        # TODO(nathaniel): is this dead code? How is this not overwritten
        # by the data.redirect.id().to(url_names.GCI_RESPOND_INVITE) at the
        # bottom of this method?
        data.redirect.program()
        data.redirect.to('edit_gci_profile')

      invite_logic.acceptInvite(data)
    else: # reject
      invite_logic.rejectInvite(data)

    return data.redirect.id().to(url_names.GCI_RESPOND_INVITE)

  def _constructPageName(self, data):
    invite = data.invite
    return "%s Invite" % (invite.role.capitalize())


class UserInvitesList(Template):
  """Template for list of invites that have been sent to the current user."""

  def __init__(self, data):
    self.data = data

    list_config = lists.ListConfiguration()
    list_config.addPlainTextColumn('org', 'From',
        lambda entity, *args: entity.org.name)
    list_config.addSimpleColumn('status', 'Status')
    list_config.setRowAction(
        lambda e, *args: data.redirect.id(e.key().id())
            .urlOf(url_names.GCI_RESPOND_INVITE))

    self._list_config = list_config

  def getListData(self):
    q = GCIRequest.all()
    q.filter('type', 'Invitation')
    q.filter('user', self.data.user)

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, q, lists.keyStarter)

    return response_builder.build()

  def context(self):
    invite_list = lists.ListConfigurationResponse(
        self.data, self._list_config, 0)

    return {
        'lists': [invite_list],
    }

  def templatePath(self):
    return 'modules/gci/invite/_invite_list.html'


class ListUserInvitesPage(GCIRequestHandler):
  """View for the page that lists all the invites which have been sent to
  the current user.
  """

  def templatePath(self):
    return 'modules/gci/invite/invite_list.html'

  def djangoURLPatterns(self):
    return [
        url(r'invite/list_user/%s$' % url_patterns.PROGRAM, self,
            name=url_names.GCI_LIST_INVITES),
    ]

  def checkAccess(self, data, check, mutator):
    check.isProfileActive()

  def jsonContext(self, data, check, mutator):
    list_content = UserInvitesList(data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def context(self, data, check, mutator):
    return {
        'page_name': 'Invitations to you',
        'invite_list': UserInvitesList(data),
    }
