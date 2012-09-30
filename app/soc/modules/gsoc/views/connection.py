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
from soc.logic.exceptions import AccessViolation
from soc.logic.helper import notifications
from soc.models.connection import RESPONSE_STATE_ACCEPTED
from soc.models.connection import RESPONSE_STATE_REJECTED
from soc.models.connection import RESPONSE_STATE_UNREPLIED
from soc.models.user import User
from soc.modules.gsoc.logic import connection as connection_logic
from soc.modules.gsoc.logic.helper import notifications as gsoc_notifications
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.models.connection import GSoCAnonymousConnection
from soc.modules.gsoc.models.connection import GSoCConnection
from soc.modules.gsoc.models.connection_message import GSoCConnectionMessage
from soc.modules.gsoc.views import forms as gsoc_forms
from soc.modules.gsoc.views.base import RequestHandler
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
  """ Helper method to check for an existing GSoCConnection between a user
  and an organization transactionally. 
  """
  query = connection_logic.queryForAncestorAndOrganization(user, org, True)
  if query.count(limit=1) > 0:
    return False
  return True

class ConnectionForm(GSoCModelForm):
  """ Django form for the ShowConnection page. """

  role = ChoiceField(widget=django_forms.Select(),
      choices=(('1', 'Mentor'), ('2', 'Org Admin')))
  message = gsoc_forms.CharField(widget=gsoc_forms.Textarea())

  def __init__(self, request_data=None, message=None, is_admin=False, 
      *args, **kwargs):
    super(ConnectionForm, self).__init__(*args, **kwargs) 
    
    self.is_admin = is_admin
    
    # Set up the user-provided message to the other party (org admin or user).
    self.fields['message'].label = ugettext('Message')
    # Place the message field at the bottom
    self.fields['message'].group = ugettext('1. ')


class OrgConnectionForm(ConnectionForm):
  """ Django form to show specific fields for an organization. """

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

    self.fields['role'].label = ugettext('Role to offer the user(s)')
    self.fields['role'].help_text = ugettext(
        'Role that you want to offer to '
        'the specified users in this organization')

    self.fields['message'].help_text = ugettext(
        'Your message to the user(s)') 

  def clean_users(self):
    """ Overrides the default cleaning of the link_ids field to add custom
    validation to the users field. 
    """
    id_list = self.cleaned_data['users'].split(',')
    self.request_data.user_connections = []
    self.request_data.anonymous_users = []
    
    field = 'current_user'
    for id in id_list:
      self.cleaned_data[field] = id.strip(' ')
      user, anon_user = self._clean_one_id(field)
      if anon_user is None:
        self.request_data.user_connections.append(user)
      else:
        self.request_data.anonymous_users.append(anon_user)
    del self.cleaned_data[field]
    
  def _clean_one_id(self, field):
    """ Apply validation filters to a single link id from the user field.
    If a link_id or email is found to be valid, return the User account
    associated with it.
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
  """Django form for the message.
  """

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


class UserConnectionForm(ConnectionForm):
  """ Django form to show specific fields for a user. """

  def __init__(self, request_data=None, message=None, *args, **kwargs):
    super(UserConnectionForm, self).__init__(*args, **kwargs)
    
    self.fields['message'].help_text = ugettext(
        'Your message to the organization')

  class Meta:
    model = GSoCConnection
    exclude = GSoCConnection.allFields()


class OrgConnectionPage(RequestHandler):
  """ Class to encapsulate the methods for an org admin to initiate a
  connection between the organization and a given user. """
  
  def templatePath(self):
    return 'v2/modules/gsoc/connection/base.html'
    
  def djangoURLPatterns(self):
    return [
        url(r'connect/%s$' % url_patterns.ORG,
            self, name=url_names.GSOC_ORG_CONNECTION)
    ]
    
  def checkAccess(self):
    assert isSet(self.data.organization)
    self.check.isProgramVisible()
    self.check.isOrganizationInURLActive()
    self.check.hasProfile()
    self.check.isOrgAdminForOrganization(self.data.organization)
  
  def context(self):
    """ Handler for GSoCConnection page request for an org. """
    
    connection_form = OrgConnectionForm(
        request_data=self.data,
        message=self.data.organization.role_request_message, 
        data=self.data.POST or None)

    emailed = dupes = None
    if 'emailed' in self.data.request.GET:
      emailed = self.data.request.GET['emailed'].split(',')
    if 'dupes' in self.data.request.GET:
      dupes = self.data.request.GET['dupes'].split(',')
    
    return {
      'logged_in_msg': LoggedInMsg(self.data, apply_link=False),
      'page_name': 'Open a connection',
      'program': self.data.program,
      'connection_form': connection_form,
      'error': bool(connection_form.errors),
      'sent_email_to' : emailed,
      'dupes' : dupes
    }
  
  def post(self):
    """ Handler for GSoCConnecton post request. """
    
    if self.generate():
      self.redirect.organization()
      extra = []
      if len(self.data.sent_email_to) > 0:
        emailed = ','.join(self.data.sent_email_to)
        extra = ['emailed=%s' % emailed, ]
      if len(self.data.duplicate_email) > 0:
        dupes = ','.join(self.data.duplicate_email)
        extra.append('dupes=%s' % dupes)
      self.redirect.to(url_names.GSOC_ORG_CONNECTION, validated=True, 
          extra=extra)
    else:
      self.get()

  def generate(self):
    """ Create a GSoCConnection instance and notify all parties involved """
    
    connection_form = OrgConnectionForm(request_data=self.data, 
        data=self.data.POST)
    if not connection_form.is_valid():
      return None
      
    connection_form.cleaned_data['organization'] = self.data.organization

    def create_connection_txn(user, email):
      if not check_existing_connection_txn(user, self.data.organization):
        raise AccessViolation(DEF_CONNECTION_EXISTS)

      connection = connection_form.create(parent=user, commit=False)
      # An organization admin is always a mentor, so regardless of the admin's
      # choice the user will be offered a mentoring position.
      connection.acceptMentorRoleByOrg()
      if connection_form.cleaned_data['role'] == '2':
        connection.acceptOrgAdminRoleByOrg()
      connection.put()

      properties = {
          'author': self.data.profile,
          'content': connection_form.cleaned_data['message']
          }
      message = GSoCConnectionMessage(parent=connection, **properties)
      message.put()

      context = notifications.connectionContext(self.data, connection, 
          email, connection_form.cleaned_data['message'])
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=connection)
      sub_txn()
      return connection
    
    self.data.connection = None

    # Traverse the list of cleaned user ids and generate connections to
    # each of them. The current user is the org admin, so we need to get
    # the user object and their profile to populate the Connection instance.
    for user in self.data.user_connections:
      connection_form.instance = None
      profile = GSoCProfile.all().ancestor(user).get()
      db.run_in_transaction(create_connection_txn, user, profile.email)

    def create_anonymous_connection_txn(email):
      # Create the anonymous connection - a placeholder until the user 
      # registers and activates the real connection.
      connection = GSoCAnonymousConnection(parent=self.data.organization)
      connection.put()
      if connection_form.cleaned_data['role'] == '2':
        connection.role = 'org_admin'
      else:
        connection.role = 'mentor' 
      # Generate a hash of the object's key for later validation.
      m = hashlib.md5()
      m.update(str(connection.key()))
      connection.hash_id = unicode(m.hexdigest())
      connection.email = email
      connection.put()

      # Notify the user that they have a pending connection and can register
      # to accept the elevated role.
      context = notifications.anonymousConnectionContext(self.data, email, 
          connection.role, connection.hash_id, 
          connection_form.cleaned_data['message'])
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=connection)
      sub_txn()

    q = GSoCAnonymousConnection.all()
    self.data.sent_email_to = []
    self.data.duplicate_email = []
    for email in self.data.anonymous_users:
      new_q = q.filter('email', email).get()
      if not new_q:
        self.data.sent_email_to.append(email)
        db.run_in_transaction(create_anonymous_connection_txn, email)
      else:
        self.data.duplicate_email.append(email)
        
    return True


class UserConnectionPage(RequestHandler):
  """ Class to encapsulate the methods for a user to initiate a connection
  between him or her self and an organization. """
  
  def templatePath(self):
    return 'v2/modules/gsoc/connection/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'connect/%s$' % url_patterns.CONNECT,
            self, name=url_names.GSOC_USER_CONNECTION)
    ]

  def checkAccess(self):
    self.check.isProgramVisible()
    self.check.isOrganizationInURLActive()
    self.check.hasProfile()
    self.check.notStudent()
    self.check.notMentor()

  def context(self):
    """ Handler for GSoCConnection page request. """

    connection_form = UserConnectionForm(request_data=self.data,
        message=self.data.organization.role_request_message, 
        is_admin=False,
        data=self.data.POST or None)
    
    return {
      'logged_in_msg': LoggedInMsg(self.data, apply_link=False),
      'profile_created': self.data.GET.get('profile') == 'created',
      'page_name': 'Open a connection',
      'program': self.data.program,
      'connection_form': connection_form,
    }
    
  def post(self):
    """ Handler for a GSoC Connection post request for a user. """
    
    if self.generate():
      self.redirect.connect(user=self.data.user)
      self.redirect.to(url_names.GSOC_USER_CONNECTION, validated=True)
    else:
      self.get()
    
  def generate(self):
    """ Create a GSoCConnection instance and notify all parties involved. """
    
    assert isSet(self.data.organization)
    assert isSet(self.data.user)
    
	  # Check the User's rate limit to make sure that there aren't excessive 
	  # outstanding connections.
    def check_outstanding_txn():
      q = GSoCConnection.all(keys_only=True).ancestor(self.data.user)
      q.filter('org_mentor =', RESPONSE_STATE_UNREPLIED)
      q.filter('org_org_admin =', RESPONSE_STATE_UNREPLIED)
      if q.count(limit=5) >= DEF_MAX_PENDING_CONNECTIONS:
        raise AccessViolation('Exceeded rate limit for pending connections.')
    db.run_in_transaction(check_outstanding_txn)

    connection_form = UserConnectionForm(request_data=self.data, 
        data=self.data.POST,
        is_admin=False)
    if not connection_form.is_valid():
      return None
    
    # When initiating a connection, the User only has the option of requesting
    # a mentoring position, so we don't need to display any selections or set
    # anything other than the user_mentor property for now.
    connection_form.cleaned_data['profile'] = self.data.profile
    connection_form.cleaned_data['organization'] = self.data.organization
    connection_form.cleaned_data['user_mentor'] = RESPONSE_STATE_ACCEPTED
	
    # Get the sender and recipient for the notification email.
    q = GSoCProfile.all().filter('org_admin_for', self.data.organization)
    q = q.filter('status =', 'active').filter('notify_new_requests =', True)
    admins = q.fetch(50)
    receivers = [i.email for i in admins]

    def create_connection(org):
      if not check_existing_connection_txn(self.data.user, 
          self.data.organization):
        raise AccessViolation(DEF_CONNECTION_EXISTS)

      connection = ConnectionForm.create(
          connection_form, parent=self.data.user, commit=False)
      connection.acceptMentorRoleByUser()
      connection.put()

      message = connection_form.cleaned_data['message']

      context = notifications.connectionContext(self.data, connection, 
          receivers, connection_form.cleaned_data['message'], True)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=connection)
      sub_txn()
    
    db.run_in_transaction(create_connection, self.data.organization)

    return True

class ShowConnection(RequestHandler):
  """Class to encapsulate the methods required to display information
  about a GSoCConnection for both Users and Org Admins."""
  
  # Each of the below actions corresponds to one two booleans for each side
  # of the Connection object to determine its state.
  ACTIONS = {
    'accept_mentor' : 'Accept Mentor',
    'reject_mentor' : 'Reject Mentor',
    'accept_org_admin' : 'Accept Org Admin',
    'reject_org_admin' : 'Reject Org Admin',
  }
  
  def templatePath(self):
    return 'v2/modules/gsoc/connection/show_connection.html'

  def djangoURLPatterns(self):
    return [
        url(r'connection/%s$' % url_patterns.CONNECTION, self,
            name=url_names.GSOC_SHOW_CONNECTION)
    ]

  def checkAccess(self):
    self.check.isProgramVisible()
    self.check.hasProfile()

    self.mutator.connectionFromKwargs()
    self.mutator.profileFromKwargs()
    # Add org to request data for access checking methods.
    self.data.organization = self.data.connection.organization
    self.check.canViewConnection()

    self.data.is_org_admin = self.data.connection.organization.key() in \
        self.data.profile.org_admin_for 

  def getMessages(self, limit=1000):
    """Gets all the messages for the connection.
    """
    assert isSet(self.data.connection)

    query = db.Query(GSoCConnectionMessage).ancestor(self.data.connection)
    query.order('created')

    return query.fetch(limit=limit)
    
  def context(self):
    """ Handler for Show GSoCConnection get request. """

    header_name = self.data.url_user.link_id \
        if self.data.is_org_admin else self.data.organization.name

    # Determine which buttons will be shown to the user.
    accept_mentor = reject_mentor = accept_org_admin = reject_org_admin = False
    if self.data.is_org_admin:
      # Org can only receive mentor requests, so allow the admin to respond or
      # to offer the user an org admin role.
      if self.data.connection.org_mentor == RESPONSE_STATE_UNREPLIED:
        accept_mentor = reject_mentor = accept_org_admin = True
    else:
      if self.data.connection.user_mentor == RESPONSE_STATE_UNREPLIED:
        accept_mentor = reject_mentor = True
        if self.data.connection.org_org_admin:
          accept_org_admin = reject_org_admin = True
        
    status = self.data.connection.status()

    form = MessageForm(self.data.POST or None)
    message_box = {
      'form' : form,
      'action' : reverse(url_names.GSOC_CONNECTION_MESSAGE,
           kwargs=self.kwargs.copy())
    }

    return {
      'page_name': 'Viewing Connection',
      'is_admin' : self.data.is_org_admin,
      'header_name': header_name,
      'org_name' : self.data.connection.organization.name,
      'status' : status,
      'connection' : self.data.connection,
      'actions' : self.ACTIONS,
      'accept_mentor' : accept_mentor,
      'reject_mentor' : reject_mentor,
      'accept_org_admin' : accept_org_admin,
      'reject_org_admin' : reject_org_admin,
      'message_box' : message_box,
      'messages' : self.getMessages(),
    }
    
  def post(self):
    """ Handler for Show GSoC Connection post request. """

    action = self.data.POST['action']
    
    if action == self.ACTIONS['accept_mentor']:
      self._acceptMentor()
    elif action == self.ACTIONS['reject_mentor']:
      self._rejectMentor()
    elif action == self.ACTIONS['accept_org_admin']:
      self._acceptOrgAdmin()
    elif action == self.ACTIONS['reject_org_admin']:
      self._rejectOrgAdmin()
      
    self.redirect.dashboard()
    self.redirect.to()

  def _acceptMentor(self):
    """ The User has accepted the Mentoring role, so we need to add the user
    to the organization's list of mentors. """
    
    profile_key = self.data.url_profile.key()
    connection_key = self.data.connection.key()
    org_key = self.data.organization.key()
    messages = self.data.program.getProgramMessages()
    
    def accept_mentor_txn():
      connection = db.get(connection_key)
      
      if self.data.is_org_admin:
        connection.org_mentor = RESPONSE_STATE_ACCEPTED
      else:
        connection.user_mentor = RESPONSE_STATE_ACCEPTED
      
      # If both the org admin and user agree to a mentoring role, promote
      # the user to a mentor.
      if connection.user_mentor == RESPONSE_STATE_ACCEPTED and \
          connection.org_mentor == RESPONSE_STATE_ACCEPTED:
        profile = db.get(profile_key)

        # Send out a welcome email to new mentors.
        if not profile.is_mentor:
          mentor_mail = notifications.getMentorWelcomeMailContext(
              profile, self.data, messages)
          if mentor_mail:
            mailer.getSpawnMailTaskTxn(mentor_mail, parent=connection)()

        profile.is_mentor = True
        profile.mentor_for.append(org_key)
        profile.mentor_for = list(set(profile.mentor_for))
        profile.put()

        # Generate a message to mark that the user was promoted.
        properties = {
          'author' : self.data.profile,
          'content': '(AUTO) %s Promoted to Mentor.' % profile.link_id
          }
        message = GSoCConnectionMessage(parent=connection, **properties)
        message.put()
      
      connection.put()
      
    db.run_in_transaction(accept_mentor_txn)
  
  def _rejectMentor(self):
    connection_key = self.data.connection.key()

    def decline_mentor_txn():
      connection = db.get(connection_key)
      if self.data.is_org_admin:
        connection.org_mentor = RESPONSE_STATE_REJECTED
      else:
        connection.user_mentor = RESPONSE_STATE_REJECTED
      connection.put()

      properties = {
          'author' : self.data.profile,
          'content': '(AUTO) Mentor Connection Rejected.'
          }
      message = GSoCConnectionMessage(parent=connection, **properties)
      message.put()
      
    db.run_in_transaction(decline_mentor_txn)
    
  def _acceptOrgAdmin(self):
    profile_key = self.data.url_profile.key()
    connection_key = self.data.connection.key()
    org_key = self.data.organization.key()
    messages = self.data.program.getProgramMessages()
    
    def accept_org_admin_txn():
      connection = db.get(connection_key)

      if self.data.is_org_admin:
        connection.org_org_admin = RESPONSE_STATE_ACCEPTED
        connection.org_mentor = RESPONSE_STATE_ACCEPTED
      else:
        connection.user_org_admin = RESPONSE_STATE_ACCEPTED
        connection.user_mentor = RESPONSE_STATE_ACCEPTED
    
      if connection.org_org_admin == RESPONSE_STATE_ACCEPTED and \
          connection.user_org_admin == RESPONSE_STATE_ACCEPTED:
        profile = db.get(profile_key)

        # Send out a welcome email to new mentors.
        if not profile.is_mentor:
          mentor_mail = notifications.getMentorWelcomeMailContext(
              profile, self.data, messages)
          if mentor_mail:
            mailer.getSpawnMailTaskTxn(mentor_mail, parent=connection)()
        
        # Org Admins are mentors by default, so we have to promote the 
        # user twice - one to mentor, one to org admin.
        profile.is_mentor = True
        profile.mentor_for.append(org_key)
        profile.mentor_for = list(set(profile.mentor_for))
        
        profile.is_org_admin = True
        profile.org_admin_for.append(org_key)
        profile.org_admin_for = list(set(profile.org_admin_for))

        # Generate a message to mark that the user was promoted.
        properties = {
          'author' : self.data.profile,
          'content': '(AUTO) %s Promoted to Org Admin.' % profile.link_id
          }
        message = GSoCConnectionMessage(parent=connection, **properties)
        message.put()
        
        profile.put()
      connection.put()
      
    db.run_in_transaction(accept_org_admin_txn)
    
  def _rejectOrgAdmin(self):
    connection_key = self.data.connection.key()
    
    def decline_org_admin_txn():
      connection = db.get(connection_key)
      if self.data.is_org_admin:
        # Org can just 'withdraw' the org admin offer.
        connection.org_org_admin = RESPONSE_STATE_REJECTED
      else:
        # User rejecting an org admin offer rejects both.
        connection.user_org_admin = RESPONSE_STATE_REJECTED
        connection.user_mentor = RESPONSE_STATE_REJECTED
      connection.put()

      properties = {
          'author' : self.data.profile,
          'content': '(AUTO) Org Admin Connection Rejected.'
          }
      message = GSoCConnectionMessage(parent=connection, **properties)
      message.put()
      
    db.run_in_transaction(decline_org_admin_txn)

class SubmitConnectionMessagePost(RequestHandler):
  """POST request handler for submission of connection messages.
  """

  def djangoURLPatterns(self):
    return [
         url(r'connection/message/%s$' % url_patterns.MESSAGE, self, 
             name=url_names.GSOC_CONNECTION_MESSAGE),
    ]

  def checkAccess(self):
    self.check.isProgramVisible()
    self.check.isProfileActive()
    self.mutator.userFromKwargs()
    self.mutator.connectionFromKwargs()
    self.mutator.commentVisible(self.data.connection.organization)

    self.check.isMentorForOrganization(self.data.connection.organization)

  def createMessageFromForm(self):
    """Creates a new message based on the data inserted in the form.

    Returns:
      a newly created message entity or None
    """

    assert isSet(self.data.connection)

    message_form = MessageForm(self.data.request.POST)

    if not message_form.is_valid():
      return None

    message_form.cleaned_data['author'] = self.data.profile

    q = GSoCProfile.all().filter('mentor_for', 
        self.data.connection.organization)
    q.filter('status', 'active')
    q.filter('notify_public_comments', True)
    to_emails = [i.email for i in q if i.key() != self.data.profile.key()]

    def create_message_txn():
      message = message_form.create(commit=True, parent=self.data.connection)

      context = gsoc_notifications.newConnectionMessageContext(
          self.data, message, to_emails)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=message)
      sub_txn()

      return message

    return db.run_in_transaction(create_message_txn)

  def post(self):
    message = self.createMessageFromForm()
    if message:
      # TODO(dcrodman): Change the org_admin_requests page to org_connections
      self.redirect.show_connection(self.data.url_user, self.data.connection)
      self.redirect.to(validated=True)
    else:
      self.redirect.show_connection(self.data.url_user, self.data.connection)

      # a bit hacky :-( may be changed when possible
      self.request.method = 'GET'
      request_handler = ShowConnection()
      self.response = request_handler(self.request, *self.args, **self.kwargs)

  def get(self):
    self.error(405)
