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

__authors__ = [
  '"Daniel Hans" <daniel.m.hans@gmail.com>',
  ]


from google.appengine.ext import db
from google.appengine.api import users

from django import forms as djangoforms
from django.conf.urls.defaults import url
from django.core import validators
from django.core.urlresolvers import reverse
from django.forms import widgets
from django.utils.translation import ugettext

from soc.logic import accounts
from soc.logic import cleaning
from soc.logic import dicts
from soc.logic.exceptions import NotFound
from soc.models.request import Request
from soc.models.user import User
from soc.views import forms
from soc.views.helper.access_checker import isSet

from soc.modules.gsoc.views.base import RequestHandler

from soc.modules.gsoc.logic.models.organization import logic as org_logic
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.views.helper import access_checker
from soc.modules.gsoc.views.helper import url_patterns


class InviteForm(forms.ModelForm):
  """Django form for the invite page.
  """

  link_id = djangoforms.CharField(label='Link ID/Email')

  class Meta:
    model = Request
    css_prefix = 'gsoc_intivation'
    fields = ['message']

  def __init__(self, request_data, *args, **kwargs):
    super(InviteForm, self).__init__(*args, **kwargs)

    # store request object to cache results of queries
    self.request_data = request_data

    # reorder the fields so that link_id is the first one
    field = self.fields.pop('link_id')
    self.fields.insert(0, 'link_id', field)
    field.help_text = "The link_id or email address of the invitee"
    
  def clean_link_id(self):
    """Accepts link_id of users which may be invited.
    """

    assert isSet(self.request_data.organization)

    invited_user = None

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

      if not invited_user:
        raise djangoforms.ValidationError(
            "There is no user with that email address")

    # get the user entity that the invitation is to
    if not invited_user:
      existing_user_cleaner = cleaning.clean_existing_user('link_id')
      invited_user = existing_user_cleaner(self)

    self.request_data.invited_user = invited_user
    
    # check if the organization has already sent an invitation to the user
    query = db.Query(Request)
    query.filter('type', 'Invitation')
    query.filter('user', invited_user)
    query.filter('role', self.request_data.kwargs['role'])
    query.filter('group', self.request_data.organization)
    if query.get():
      raise djangoforms.ValidationError(
          'An invitation to this user has already been sent.')

    # check if the user that is invited does not have the role
    key_name = '/'.join([
        self.request_data.program.key().name(),
        invited_user.link_id])
    profile = self.request_data.invite_profile = GSoCProfile.get_by_key_name(
        key_name, parent=invited_user)

    if not profile:
      msg = ("The specified user has a User account (the link_id is valid), "
             "but they do not yet have a profile for this %s. "
             "You cannot invite them until they create a profile.")
      raise djangoforms.ValidationError(msg % self.request_data.program.name)

    if profile.student_info:
      raise djangoforms.ValidationError("That user is a student")

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
        url(r'^gsoc/invite/%s$' % url_patterns.INVITE,
            self, name='gsoc_invite')
    ]

  def checkAccess(self):
    """Access checks for GSoC Invite page.
    """

    self.check.isProgramActive()
      
    link_id = self.data.kwargs['organization']
    filter = {
        'link_id': link_id,
        'scope': self.data.program,
        'status': 'active'
        }
    self.data.organization = org_logic.getForFields(filter, unique=True)
    if not self.data.organization:
      msg = ugettext(
          'The organization with link_id %s does not exist for %s.' % 
          (link_id, self.data.program.name))

      raise NotFound(msg)

    self.check.isOrgAdmin()

  def context(self):
    """Handler to for GSoC Invitation Page HTTP get request.
    """

    role = 'Org Admin' if self.data.kwargs['role'] == 'org_admin' else 'Mentor'

    invite_form = InviteForm(self.data, self.data.POST or None)

    return {
        'logout_link': users.create_logout_url(self.data.full_path),
        'page_name': 'Invite a new %s' % role,
        'program': self.data.program,
        'invite_form': invite_form
    }

  def _createFromForm(self):
    """Creates a new invitation based on the data inserted in the form.

    Returns:
      a newly created Request entity or None
    """

    assert isSet(self.data.organization)

    invite_form = InviteForm(self.data, self.data.POST)
    
    if not invite_form.is_valid():
      return None

    assert self.data.invited_user

    # create a new invitation entity
    invite_form.cleaned_data['user'] = self.data.invited_user
    invite_form.cleaned_data['group'] = self.data.organization
    invite_form.cleaned_data['role'] = self.data.kwargs['role']
    invite_form.cleaned_data['type'] = 'Invitation'

    return invite_form.create(commit=True)

  def post(self):
    """Handler to for GSoC Invitation Page HTTP post request.
    """

    if self._createFromForm():
      self.redirect.invite()
      self.redirect.to('gsoc_invite')
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
        url(r'^gsoc/invitation/%s$' % url_patterns.ID, self,
            name='gsoc_invitation')
    ]

  def checkAccess(self):
    self.check.isProfileActive()
    
    id = int(self.data.kwargs['id'])
    self.data.invite = Request.get_by_id(id)
    self.check.isRequestPresent(self.data.invite, id)

    self.data.organization = self.data.invite.group
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
        self.data.requester.link_id])
    self.data.invited_profile = GSoCProfile.get_by_key_name(
        key_name, parent=self.data.requester)

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
        'user_name': self.data.invited_profile.name,
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

    self.data.invite.status = 'accepted'

    if self.data.invite.role == 'mentor':
      self.data.profile.is_mentor = True
      self.data.profile.mentor_for.append(self.data.organization.key())
    else:
      self.data.profile.is_admin = True
      self.data.profile.mentor_for.append(self.data.organization.key())
      self.data.profile.org_admin_for.append(self.data.organization.key())

    self.data.invite.put()
    self.data.profile.put()

  def _rejectInvitation(self):
    """Rejects a invitation. 
    """

    self.data.invite.status = 'rejected'
    self.data.invite.put()

  def _resubmitInvitation(self):
    """Resubmits a invitation. 
    """

    self.data.invite.status = 'pending'
    self.data.invite.put()

  def _withdrawInvitation(self):
    """Withdraws an invitation.
    """

    self.data.invite.status = 'withdrawn'
    self.data.invite.put()
