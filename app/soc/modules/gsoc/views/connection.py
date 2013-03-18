#!/usr/bin/env python2.5
#
# Copyright 2012 the Melange authors.
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
""" Module containing the view for the GSoCConnection page """

import hashlib

from google.appengine.ext import db
from google.appengine.api import users

from django import forms as django_forms
from django.core.urlresolvers import reverse
from django.forms.fields import ChoiceField
from django.forms.widgets import RadioSelect
from django.utils.translation import ugettext

from soc.logic import accounts
from soc.logic import cleaning
from soc.models import connection
from soc.logic import exceptions
from soc.logic.helper import notifications
from soc.models.user import User
from soc.modules.gsoc.logic import connection as connection_logic
from soc.modules.gsoc.logic.helper import notifications as gsoc_notifications
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.models.connection import GSoCAnonymousConnection
from soc.modules.gsoc.models.connection import GSoCConnection
from soc.modules.gsoc.models.connection_message import GSoCConnectionMessage
from soc.modules.gsoc.views import forms as gsoc_forms
from soc.modules.gsoc.views.base import GSoCRequestHandler
from soc.modules.gsoc.views.base_templates import LoggedInMsg
from soc.modules.gsoc.views.forms import GSoCModelForm
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper.url_patterns import url
from soc.views.helper import url_patterns
from soc.views.helper.access_checker import isSet
from soc.tasks import mailer


DEF_NONEXISTANT_USER = 'The user with the email %s does not exist.'
DEF_CONNECTION_EXISTS = 'This connection already exists.'
DEF_EXCEED_RATE_LIMIT = 'Exceeded rate limit, too many pending connections.'
DEF_MAX_PENDING_CONNECTIONS = 3

@db.transactional
def check_existing_connection_txn(user, org):
  """Helper method to check for an existing GSoCConnection between a user
    and an organization transactionally. 
  """
  query = connection_logic.queryForAncestorAndOrganization(user, org, True)
  if query.count(limit=1) > 0:
    return False
  return True

@db.transactional
def send_message_txn(form, profile, connection):
  """Helper method to generate a GSoCConnectionMessage sent from a user.
  """
  properties = {
    'author': profile,
    'content': form.cleaned_data['message']
    }
  message = GSoCConnectionMessage(parent=connection, **properties)
  message.put()

@db.transactional
def generate_message_txn(connection, content):
  """Helper method to generate a GSoCConnectionMessage with programatically
      generated content.
  """
  properties = {
      'is_auto_generated' : True,
      'content': content
      }
  message = GSoCConnectionMessage(parent=connection, **properties)
  message.put()

class ConnectionForm(GSoCModelForm):
  """Django form for the Connection page."""

  role_choice = ChoiceField(widget=django_forms.Select(),
      choices=((connection.MENTOR_STATE, connection.MENTOR_STATE),))
  message = gsoc_forms.CharField(widget=gsoc_forms.Textarea())

  def __init__(self, request_data=None, message=None, is_admin=False, 
      *args, **kwargs):
    super(ConnectionForm, self).__init__(*args, **kwargs) 
    
    self.is_admin = is_admin
    
    # Set up the user-provided message to the other party (org admin or user).
    self.fields['message'].label = ugettext('Message')
    # Place the message field at the bottom
    self.fields['message'].group = ugettext('1. ')
    # Do not require users/org admins to include a message.
    self.fields['message'].required = False

  class Meta:
    model = GSoCConnection

class OrgConnectionForm(ConnectionForm):
  """Django form to show specific fields for an organization."""

  users = gsoc_forms.CharField(label='Link_Id/Email')

  def __init__(self, request_data=None, message=None, *args, **kwargs):
    super(OrgConnectionForm, self).__init__(*args, **kwargs)

    self.request_data = request_data
    self.is_admin = True

    field = self.fields.pop('users')
    field.help_text = ugettext(
        'The link_id or email address of the invitee, '
        ' separate multiple values with a comma')
    # Place the users field at the top of the form.
    self.fields.insert(0, 'users', field)  

    self.fields['role_choice'].choices = (
        (connection.MENTOR_STATE, connection.MENTOR_STATE), 
        (connection.ORG_ADMIN_STATE, connection.ORG_ADMIN_STATE)
        )
    self.fields['role_choice'].label = ugettext('Role to offer the user(s)')
    self.fields['role_choice'].help_text = ugettext(
        'Role that you want to offer to '
        'the specified users in this organization')

    self.fields['message'].help_text = ugettext(
        'Your message to the user(s)') 

  def clean_users(self):
    """Overrides the default cleaning of the link_ids field to add custom
    validation to the users field. 
    """
    id_list = self.cleaned_data['users'].split(',')
    self.request_data.user_connections = []
    self.request_data.anonymous_users = []
    
    field = 'current_user'
    for id in id_list:
      self.cleaned_data[field] = id.strip(' ')
      user, anonymous_user = self._clean_one_id(field)
      if anonymous_user is None:
        self.request_data.user_connections.append(user)
      else:
        self.request_data.anonymous_users.append(anonymous_user)
    del self.cleaned_data[field]
    
  def _clean_one_id(self, field):
    """Apply validation filters to a single link id from the user field.
    If a link_id or email is found to be valid, return the User account
    associated with it.
      Args:
        field: Django TextField instance containing the email address(es)
            or link ids of users with whom connections should be established.

      Returns:
        connected_user will be the user account affiliated with the email
        address found in field or None if no such user exists, at which 
        point the email address will be returned as anonymous_user (None
        if the email address corresponds to an existing User).
    """

    id = None
    connected_user = None
    anonymous_user = None

    if '@' in self.cleaned_data[field]:
      # Current id is an email address.
      cleaner = cleaning.clean_email(field)
      email = cleaner(self)
      
      account = users.User(email)
      user_account = accounts.normalizeAccount(account)
      connected_user = User.all().filter('account', user_account).get()
      if not connected_user or \
          GSoCProfile.all().ancestor(connected_user).count(limit=1) < 1:
        anonymous_user = self.cleaned_data[field]
    else:
      # Current id is a link_id.
      cleaner = cleaning.clean_existing_user(field)
      connected_user = cleaner(self)
      
    return connected_user, anonymous_user

  class Meta:
    model = GSoCConnection
    exclude = GSoCConnection.allFields()


class MessageForm(GSoCModelForm):
  """Django form for the message."""

  def __init__(self, *args, **kwargs):
    super(MessageForm, self).__init__(*args, **kwargs)
    self.fields['content'].label = ugettext(' ')

  class Meta:
    model = GSoCConnectionMessage
    fields = ['content']

  def clean_content(self):
    field_name = 'content'
    wrapped_clean_html_content = cleaning.clean_html_content(field_name)
    content = wrapped_clean_html_content(self)
    if content:
      return content
    else:
      raise django_forms.ValidationError(
          ugettext('Message content cannot be empty.'), code='invalid')

  def templatePath(self):
    return 'v2/modules/gsoc/connection/_message_form.html'

class ConnectionResponseForm(GSoCModelForm):
  """Django form to provide Connection responses in ShowConnection.
  """
  responses = ChoiceField(widget=django_forms.Select())

  def __init__(self, request_data=None, choices=None, *args, **kwargs):
    super(ConnectionResponseForm, self).__init__(*args, **kwargs)

    self.request_data = request_data

    self.fields['responses'].group = ugettext('1. ')
    self.fields['responses'].help_text = ugettext(
        'Select an action to take.')
    self.fields['responses'].choices = choices
    self.fields['responses'].required = False

  def templatePath(self):
    return 'v2/modules/gsoc/connection/_response_form.html'

class UserConnectionForm(ConnectionForm):
  """Django form to show specific fields for a user."""

  def __init__(self, request_data=None, message=None, *args, **kwargs):
    super(UserConnectionForm, self).__init__(*args, **kwargs)
    
    self.fields['message'].help_text = ugettext(
        'Your message to the organization')

  class Meta:
    model = GSoCConnection
    exclude = GSoCConnection.allFields()


class OrgConnectionPage(GSoCRequestHandler):
  """Class to encapsulate the methods for an org admin to initiate a
  connection between the organization and a given user. 
  """
  
  def templatePath(self):
    return 'v2/modules/gsoc/connection/base.html'
    
  def djangoURLPatterns(self):
    return [
        url(r'connect/%s$' % url_patterns.ORG,
            self, name=url_names.GSOC_ORG_CONNECTION)
    ]
    
  def checkAccess(self, data, check, mutator):
    assert isSet(data.organization)
    check.isProgramVisible()
    check.isOrganizationInURLActive()
    check.hasProfile()
    check.isOrgAdminForOrganization(data.organization)
  
  def context(self, data, check, mutator):
    """Handler for GSoCConnection page request for an org."""
    
    connection_form = OrgConnectionForm(
        request_data=data,
        message=data.organization.role_request_message, 
        data=data.POST or None)

    emailed = dupes = None
    if 'emailed' in data.request.GET:
      emailed = data.request.GET['emailed'].split(',')
    if 'dupes' in data.request.GET:
      dupes = data.request.GET['dupes'].split(',')
    
    return {
      'logged_in_msg': LoggedInMsg(data, apply_link=False),
      'page_name': 'Open a connection',
      'program': data.program,
      'connection_form': connection_form,
      'error': bool(connection_form.errors),
      'sent_email_to' : emailed,
      'dupes' : dupes
    }
  
  def post(self, data, check, mutator):
    """Handler for GSoCConnecton post request.

      Returns:
        A get request to this same page that will display a confirmation
        message and indicate whether or not emails were sent inviting new
        users to join the program (via anonymous connections).
    """
    
    if self.generate(data):
      data.redirect.organization()
      extra = []
      if len(data.sent_email_to) > 0:
        emailed = ','.join(data.sent_email_to)
        extra = ['emailed=%s' % emailed, ]
      if len(data.duplicate_email) > 0:
        dupes = ','.join(data.duplicate_email)
        extra.append('dupes=%s' % dupes)
      return data.redirect.to(url_names.GSOC_ORG_CONNECTION, validated=True, 
          extra=extra)
    else:
      return self.get(data, check, mutator)

  def generate(self, data):
    """Create a GSoCConnection instance and notify all parties involved. If
    the org admin provided email addresses of users who do not have profiles
    for the current program, AnonymousConnection instances will be generated
    and emails dispatched inviting them to join the program and accept the 
    offered role.
    """
    
    connection_form = OrgConnectionForm(request_data=data, 
        data=data.POST)
    if not connection_form.is_valid():
      return None
      
    connection_form.cleaned_data['organization'] = data.organization

    message_provided = (connection_form.cleaned_data['message'] != '')

    def create_connection_txn(user, email):
      if not check_existing_connection_txn(user, data.organization):
        raise exceptions.AccessViolation(DEF_CONNECTION_EXISTS)

      connection = connection_form.create(parent=user, commit=False)
      connection.org_state = STATUS_STATE_ACCEPTED
      connection.role =  connection_form.cleaned_data['role_choice']
      connection.put()

      if message_provided:
        send_message_txn(connection_form, profile, connection)

      context = notifications.connectionContext(data, connection, 
          email, connection_form.cleaned_data['message'])
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=connection)
      sub_txn()
      return connection
    
    data.connection = None

    # Traverse the list of cleaned user ids and generate connections to
    # each of them. The current user is the org admin, so we need to get
    # the user object and their profile to populate the Connection instance.
    for user in data.user_connections:
      connection_form.instance = None
      profile = GSoCProfile.all().ancestor(user).get()
      db.run_in_transaction(create_connection_txn, user, profile.email)

    def create_anonymous_connection_txn(email):
      # Create the anonymous connection - a placeholder until the user 
      # registers and activates the real connection.
      connection = GSoCAnonymousConnection(parent=data.organization)
      connection.role = connection_form.cleaned_data['role_choice']
      connection.put()
      
      # Generate a hash of the object's key for later validation.
      m = hashlib.md5()
      m.update(str(connection.key()))
      connection.hash_id = unicode(m.hexdigest())
      connection.email = email
      connection.put()

      # Notify the user that they have a pending connection and can register
      # to accept the elevated role.
      context = notifications.anonymousConnectionContext(data, email, 
          connection.role, connection.hash_id, 
          connection_form.cleaned_data['message'])
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=connection)
      sub_txn()

    q = GSoCAnonymousConnection.all()
    data.sent_email_to = []
    data.duplicate_email = []
    for email in data.anonymous_users:
      new_q = q.filter('email', email).get()
      if not new_q:
        data.sent_email_to.append(email)
        db.run_in_transaction(create_anonymous_connection_txn, email)
      else:
        data.duplicate_email.append(email)
        
    return True


class UserConnectionPage(GSoCRequestHandler):
  """Class to encapsulate the methods for a user to initiate a connection
  between him or her self and an organization.
  """
  
  def templatePath(self):
    return 'v2/modules/gsoc/connection/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'connect/%s$' % url_patterns.CONNECT,
            self, name=url_names.GSOC_USER_CONNECTION)
    ]

  def checkAccess(self, data, check, mutator):
    check.isProgramVisible()
    check.isOrganizationInURLActive()
    check.hasProfile()
    check.notStudent()
    check.notMentor()

  def context(self, data, check, mutator):
    """Handler for GSoCConnection page request."""

    connection_form = UserConnectionForm(request_data=data,
        message=data.organization.role_request_message, 
        is_admin=False,
        data=data.POST or None)
    
    return {
      'logged_in_msg': LoggedInMsg(data, apply_link=False),
      'profile_created': data.GET.get('profile') == 'created',
      'page_name': 'Open a connection',
      'program': data.program,
      'connection_form': connection_form,
    }
    
  def post(self, data, check, mutator):
    """Handler for a GSoC Connection post request for a user."""
    
    if self.generate(data):
      self.redirect.connect(user=data.user)
      return self.redirect.to(url_names.GSOC_USER_CONNECTION, validated=True)
    else:
      return self.get()
    
  def generate(self, data):
    """Create a GSoCConnection instance and notify all parties involved.
    """
    
    assert isSet(data.organization)
    assert isSet(data.user)

    connection_form = UserConnectionForm(request_data=data, data=data.POST,
        is_admin=False)
    if not connection_form.is_valid():
      return None
    
    # When initiating a connection, the User only has the option of requesting
    # a mentoring position, so we don't need to display any selections or set
    # anything other than the user_mentor property for now.
    connection_form.cleaned_data['profile'] = data.profile
    connection_form.cleaned_data['organization'] = data.organization

    # Get the sender and recipient for the notification email.
    q = GSoCProfile.all().filter('org_admin_for', data.organization)
    q = q.filter('status =', 'active').filter('notify_new_requests =', True)
    admins = q.fetch(50)
    receivers = [i.email for i in admins]

    # We don't want to generate a message with empty content in the event that
    # a user does not provide any.
    message_provided = (connection_form.cleaned_data['message'] != '')

    def create_connection(org):
      if not check_existing_connection_txn(data.user, data.organization):
        raise exceptions.AccessViolation(DEF_CONNECTION_EXISTS)

      connection = ConnectionForm.create(
          connection_form, parent=data.user, commit=False)
      connection.user_state = STATUS_STATE_ACCEPTED
      connection.put()

      if message_provided:
        send_message_txn(connection_form, data.profile, connection)

      context = notifications.connectionContext(data, connection, 
          receivers, connection_form.cleaned_data['message'], True)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=connection)
      sub_txn()
    
    db.run_in_transaction(create_connection, data.organization)

    return True

class ShowConnection(GSoCRequestHandler):
  """Class to encapsulate the methods required to display information
  about a GSoCConnection for both Users and Org Admins.
  """
  
  # The actions that will be made available to the user in the dropdown.
  RESPONSES = {
    'none' : ('none', 'None Available'),
    'accept_mentor' : ('accept_mentor', 'Accept Mentor'),
    'reject_mentor' : ('reject_mentor', 'Reject Mentor'),
    'accept_org_admin' : ('accept_org_admin', 'Accept Org Admin'),
    'reject_org_admin' : ('reject_org_admin', 'Reject Org Admin'),
    'withdraw' : ('withdraw', 'Withdraw'),
    'delete' : ('delete', 'Delete')
  }
  is_org_admin_for_org = False
  
  def templatePath(self):
    return 'v2/modules/gsoc/connection/show_connection.html'

  def djangoURLPatterns(self):
    return [
        url(r'connection/%s$' % url_patterns.CONNECTION, self,
            name=url_names.GSOC_SHOW_CONNECTION)
    ]

  def checkAccess(self, data, check, mutator):
    check.isProgramVisible()
    check.hasProfile()

    mutator.connectionFromKwargs()
    mutator.profileFromKwargs()
    # Add org to request data for access checking methods.
    data.organization = data.connection.organization
    check.canViewConnection()

    self.is_org_admin_for_org = data.connection.organization.key() in \
        data.profile.org_admin_for 

  def getMessages(self, data, limit=1000):
    """Gets all the messages for the connection."""
    assert isSet(data.connection)

    query = db.Query(GSoCConnectionMessage).ancestor(data.connection)
    query.order('created')

    return query.fetch(limit=limit)

  def getMentorChoices(self, choices, unreplied, accepted, 
      rejected, withdrawn=True):
    """Helper method to clean up the logic for determining what options a
      user or org admin has for responding to a connection.

      Returns:
        A list of possible responses that will be used by the page's template
        to determine which buttons (response actions) to display to the user.
    """
    responses = []
    if unreplied:
      responses.append(choices['accept'])
      responses.append(choices['reject'])
    elif rejected:
      responses.append(choices['accept'])
    elif accepted:
      responses.append(choices['reject'])
      if not withdrawn:
        responses.append(choices['withdraw'])
    return responses
    
  def context(self, data, check, mutator):
    """Handler for Show GSoCConnection get request."""

    header_name = data.url_user.link_id \
        if self.is_org_admin_for_org else data.organization.name

    # Shortcut for clarity/laziness.
    c = data.connection 
    # This isn't pretty by any stretch of the imagination, but it's going
    # to stay like this for now in the interest of my time and sanity. The 
    # basic rules for displaying options are in the getMentorChoices() method
    # and the code following includes some tweaks for user/org admin.
    choices = []
    if c.isWithdrawn():
      # Allow an org to delete or re-open the connection.
      if self.is_org_admin_for_org:
        if c.isOrgWithdrawn():
          choices.append(self.RESPONSES['accept_mentor'])
          choices.append(self.RESPONSES['accept_org_admin'])
        choices.append(self.RESPONSES['delete'])
      # Allow the user to re-open the connection.
      else:
        if c.isUserWithdrawn():
          choices.append(self.RESPONSES['accept_mentor'])
    elif c.isStalemate() or c.isAccepted():
      # There's nothing else that can be done to the connection in either 
      # case, so the org admin has the option to delete it.
      if self.is_org_admin_for_org:
        choices.append(self.RESPONSES['delete'])
    else:
      mentor_options = {
          'accept' : self.RESPONSES['accept_mentor'],
          'reject' : self.RESPONSES['reject_mentor'],
          'withdraw' : self.RESPONSES['withdraw']
          }
      org_admin_options = {
          'accept' : self.RESPONSES['accept_org_admin'],
          'reject' : self.RESPONSES['reject_org_admin'],
          'withdraw' : self.RESPONSES['withdraw']
          }    
      if self.is_org_admin_for_org:
        choices = self.getMentorChoices(mentor_options, c.isOrgUnreplied(), 
            c.isOrgAccepted(), c.isOrgRejected(), c.isOrgWithdrawn())
        if c.isOrgUnreplied():
          choices.append(self.RESPONSES['accept_org_admin'])
        if c.role == 'Org Admin':
          choices = choices + self.getMentorChoices(org_admin_options, 
            c.isOrgUnreplied(), c.isOrgAccepted(), c.isOrgRejected(),
            c.isOrgWithdrawn()
            )
          if c.isOrgAccepted():
            if self.RESPONSES['reject_mentor'] in choices:
              choices.remove(self.RESPONSES['reject_mentor'])
      else:
        choices = self.getMentorChoices(mentor_options, c.isUserUnreplied(),
            c.isUserAccepted(), c.isUserRejected(), c.isUserWithdrawn())
        if c.role == 'Org Admin':
          choices = choices + self.getMentorChoices(org_admin_options, 
            c.isUserUnreplied(), c.isUserAccepted(), c.isUserRejected(),
            c.isUserWithdrawn())

    if choices.count(self.RESPONSES['withdraw']) > 1:
      choices.remove(self.RESPONSES['withdraw'])

    if len(choices) < 1:
      choices.append(self.RESPONSES['none'])

    response_form = ConnectionResponseForm(
        request_data=data.POST or None,
        choices=choices)

    message_form = MessageForm(data.POST or None)
    message_box = {
        'form' : message_form,
        'action' : reverse(url_names.GSOC_CONNECTION_MESSAGE,
             kwargs=data.kwargs.copy())
        }

    return {
        'page_name': 'Viewing Connection',
        'is_admin' : self.is_org_admin_for_org,
        'header_name': header_name,
        'connection' : data.connection,
        'message_box' : message_box,
        'messages' : self.getMessages(data),
        'response_form' : response_form
        }
    
  def post(self, data, check, mutator):
    """Handler for Show GSoC Connection post request."""

    response = data.POST['responses']
    
    if response == 'accept_mentor':
      self._acceptMentor(data)
    elif response == 'reject_mentor':
      self._rejectMentor(data)
    elif response == 'accept_org_admin':
      self._acceptOrgAdmin(data)
    elif response == 'reject_org_admin':
      self._rejectOrgAdmin(data)
    elif response == 'delete':
      self._deleteConnection(data)
    elif response == 'withdraw':
      self._withdrawConnection(data)
    
    if response != 'none':
      data.redirect.dashboard()
    else:
      return data.redirect.show_connection(user=data.connection.parent(),
          connection=data.connection)
    return data.redirect.to()

  def _acceptMentor(self, data):
    """The User has accepted the Mentoring role, so we need to add the user
    to the organization's list of mentors.
    """
    
    profile_key = data.url_profile.key()
    connection_key = data.connection.key()
    org_key = data.organization.key()
    messages = data.program.getProgramMessages()
    
    def accept_mentor_txn():
      connection = db.get(connection_key)
      
      # Reset both parties' states after a connection becomes active again.
      # The user or org admin re-activating the connection will be marked
      # as accepted anyway in the next lines.
      if connection.isWithdrawn():
        connection.org_state = connection.user_state = STATUS_STATE_UNREPLIED

      if self.is_org_admin_for_org:
        connection.org_state = STATUS_STATE_ACCEPTED
      else:
        connection.user_state = STATUS_STATE_ACCEPTED
      connection.put()
      
      # If both the org admin and user agree to a mentoring role, promote
      # the user to a mentor. It is possible for a user to accept only a
      # mentoring role from an org admin connection, so there need not be
      # any role check.
      if connection.isUserAccepted() and connection.isOrgAccepted():
        profile = db.get(profile_key)

        # Send out a welcome email to new mentors.
        if not profile.is_mentor:
          mentor_mail = notifications.getMentorWelcomeMailContext(
              profile, data, messages)
          if mentor_mail:
            mailer.getSpawnMailTaskTxn(mentor_mail, parent=connection)()

        # This should theoretically never happen, but it improves stability.
        if org_key not in profile.mentor_for:
          profile.is_mentor = True
          profile.mentor_for.append(org_key)
          profile.mentor_for = list(set(profile.mentor_for))
          profile.put()

          generate_message_txn(connection, 
              '%s promoted to Mentor.' % profile.link_id)

    db.run_in_transaction(accept_mentor_txn)
  
  def _rejectMentor(self, data):
    connection_key = data.connection.key()

    def decline_mentor_txn():
      connection = db.get(connection_key)
      if self.is_org_admin_for_org:
        connection.org_state = STATUS_STATE_REJECTED
      else:
        connection.user_state = STATUS_STATE_REJECTED
      connection.put()

      generate_message_txn(connection, 'Mentor Connection Rejected.')
      
    db.run_in_transaction(decline_mentor_txn)
    
  def _acceptOrgAdmin(self, data):
    profile_key = data.url_profile.key()
    connection_key = data.connection.key()
    org_key = data.organization.key()
    messages = data.program.getProgramMessages()
    
    def accept_org_admin_txn():
      connection = db.get(connection_key) 

      # The org accepted a new role for the user, so reset the user's response
      # to give him or her time to review the change.
      if connection.role == 'Mentor':
        connection.user_state = connection.org_state = STATUS_STATE_UNREPLIED

      connection.role = 'Org Admin'

      if self.is_org_admin_for_org:
        connection.org_state = STATUS_STATE_ACCEPTED
      else:
        connection.user_state = STATUS_STATE_ACCEPTED

      connection.put()

      if connection.isOrgAccepted() and connection.isUserAccepted():
        profile = db.get(profile_key)

        # Send out a welcome email to new mentors.
        if not profile.is_mentor:
          mentor_mail = notifications.getMentorWelcomeMailContext(
              profile, data, messages)
          if mentor_mail:
            mailer.getSpawnMailTaskTxn(mentor_mail, parent=connection)()
        
        # Org Admins are mentors by default, so we have to promote the 
        # user twice - one to mentor, one to org admin.
        if org_key not in profile.mentor_for:
          profile.is_mentor = True
          profile.mentor_for.append(org_key)
          profile.mentor_for = list(set(profile.mentor_for))
        
        if org_key not in profile.org_admin_for:
          profile.is_org_admin = True
          profile.org_admin_for.append(org_key)
          profile.org_admin_for = list(set(profile.org_admin_for))
          profile.put()

          generate_message_txn(connection, 
              '%s promoted to Org Admin.' % profile.link_id)
      
    db.run_in_transaction(accept_org_admin_txn)
    
  def _rejectOrgAdmin(self, data):
    connection_key = data.connection.key()

    def decline_org_admin_txn():
      connection = db.get(connection_key)
      if self.is_org_admin_for_org:
        # Org can just 'withdraw' the org admin offer.
        connection.org_state = STATUS_STATE_REJECTED
      else:
        # User rejecting an org admin offer rejects both.
        connection.user_state = STATUS_STATE_REJECTED
      connection.put()

      generate_message_txn(connection, 'Org Admin Connection Rejected.')
      
    db.run_in_transaction(decline_org_admin_txn)


  def _withdrawConnection(self, data):
    connection_key = data.connection_key()

    def withdraw_connection_txn():
      # Mark the connection on the user or org side as 'Rejected' and add an auto-comment
      connection = db.get(connection_key)
      if self.is_org_admin_for_org:
        connection.org_state = STATUS_STATE_WITHDRAWN
      else:
        connection.user_state = STATUS_STATE_WITHDRAWN
      connection.put()

      generate_message_txn(connection, 'Connection withdrawn.')

    db.run_in_transaction(withdraw_connection_txn)

  def _deleteConnection(self, data):
    connection_key = data.connection.key()

    def delete_connection_txn():
      connection = db.get(connection_key)
      db.delete(GSoCConnectionMessage.all().ancestor(connection))
      connection.delete()

    db.run_in_transaction(delete_connection_txn)

class SubmitConnectionMessagePost(GSoCRequestHandler):
  """POST request handler for submission of connection messages."""

  def djangoURLPatterns(self):
    return [
         url(r'connection/message/%s$' % url_patterns.MESSAGE, self, 
             name=url_names.GSOC_CONNECTION_MESSAGE),
    ]

  def checkAccess(self, data, check, mutator):
    check.isProgramVisible()
    check.isProfileActive()
    mutator.userFromKwargs()
    mutator.connectionFromKwargs()
    data.organization = data.connection.organization
    mutator.commentVisible(data.organization)

    self.check.isOrgAdmin()

  def createMessageFromForm(self):
    """Creates a new message based on the data inserted in the form.

    Returns:
      A newly created message entity or None.
    """

    assert isSet(data.connection)

    message_form = MessageForm(data.request.POST)

    if not message_form.is_valid():
      return None

    message_form.cleaned_data['author'] = data.profile

    q = GSoCProfile.all().filter('mentor_for', data.connection.organization)
    q.filter('status', 'active')
    q.filter('notify_public_comments', True)
    to_emails = [i.email for i in q if i.key() != data.profile.key()]

    def create_message_txn():
      message = message_form.create(commit=True, parent=data.connection)

      context = gsoc_notifications.newConnectionMessageContext(
          data, message, to_emails)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=message)
      sub_txn()

      return message

    return db.run_in_transaction(create_message_txn)

  def post(self, data, check, mutator):
    message = self.createMessageFromForm()
    if message:
      data.redirect.show_connection(data.url_user, data.connection)
      data.redirect.to(validated=True)
    else:
      self.redirect.show_connection(data.url_user, data.connection)

      # a bit hacky :-( may be changed when possible
      data.request.method = 'GET'
      request_handler = ShowConnection()
      self.response = request_handler(data.request, *self.args, **self.kwargs)

  def get(self, data, check, mutator):
    raise exceptions.MethodNotAllowed()
