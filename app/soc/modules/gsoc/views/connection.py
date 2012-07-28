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

from django import forms as djangoforms
from django.core.urlresolvers import reverse
from django.forms.fields import ChoiceField
from django.forms.widgets import RadioSelect
from django.utils.translation import ugettext

from soc.logic import accounts
from soc.logic import cleaning
from soc.logic.exceptions import AccessViolation
from soc.logic.helper import notifications
from soc.models.user import User
from soc.modules.gsoc.logic.helper import notifications as gsoc_notifications
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.models.comment import GSoCComment
from soc.modules.gsoc.models.connection import GSoCConnection, GSoCAnonymousConnection
from soc.modules.gsoc.views import forms as gsoc_forms
from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.base_templates import LoggedInMsg
from soc.modules.gsoc.views.forms import GSoCModelForm
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper.url_patterns import url, COMMENT
from soc.modules.gsoc.views.proposal_review import CommentForm, PrivateCommentForm
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

  q = GSoCConnection.all(keys_only=True).ancestor(user)
  q.filter('organization =', org.key())
  if q.count(limit=1) > 0:
    return False
  return True

class ConnectionForm(GSoCModelForm):
  """ Django form for the ShowConnection page. """

  #TODO(dcrodman): Sticking with the dropdown for role selection at the 
  # moment since I don't like how the Radio button ends up staggered,
  # this will be something to work on later.
  #role = ChoiceField(widget=RadioSelect(), 
  #    choices=(('1', 'Org Admin'), ('2', 'Mentor')),
  #    required=True,
  #    initial='2')
  role = ChoiceField(widget=djangoforms.Select(),
      choices=(('1', 'Mentor'), ('2', 'Org Admin')))  
  
  def __init__(self, request_data=None, message=None, is_admin=False, 
      *args, **kwargs):
    super(ConnectionForm, self).__init__(*args, **kwargs) 
    
    self.is_admin = is_admin
    
    #TODO(dcrodman): Custom message.
    
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
      
    self.fields['role'].group = ugettext('0. Role to offer the user')
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
      if user is not None:
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
      anonymous_user = self.cleaned_data[field] if connected_user is None \
          else None
    else:
      # Current id is a link_id.
      cleaner = cleaning.clean_existing_user(field)
      connected_user = cleaner(self)
      
    return connected_user, anonymous_user

  class Meta:
    model = GSoCConnection
    fields = ['message']
    # Override the default rendering of the message field.
    widgets = {
      'message' : gsoc_forms.Textarea(attrs={'cols':80, 'rows':10}), 
    }   


class UserConnectionForm(ConnectionForm):
  """ Django form to show specific fields for a user. """

  def __init__(self, request_data=None, message=None, *args, **kwargs):
    super(UserConnectionForm, self).__init__(*args, **kwargs)
    
    self.fields['message'].help_text = ugettext(
        'Your message to the organization')

  class Meta:
    model = GSoCConnection
    fields = ['message']
    # Override the default rendering of the message field.
    widgets = {
      'message' : gsoc_forms.Textarea(attrs={'cols':80, 'rows':10}), 
    }   


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
        
    return {
      'logged_in_msg': LoggedInMsg(self.data, apply_link=False),
      'page_name': 'Open a connection',
      'program': self.data.program,
      'connection_form': connection_form,
      'error': bool(connection_form.errors)
    }
  
  def post(self):
    """ Handler for GSoCConnecton post request. """
    
    if self.generate():
      self.redirect.organization()
      self.redirect.to(url_names.GSOC_ORG_CONNECTION, validated=True)
    else:
      self.get()

  def generate(self):
    """ Create a GSoCConnection instance and notify all parties involved """
    
    connection_form = OrgConnectionForm(request_data=self.data, 
        data=self.data.POST)
    if not connection_form.is_valid():
      return None
      
    connection_form.cleaned_data['organization'] = self.data.organization

    # An organization admin is always a mentor, so regardless of the admin's
    # choice the user will be offered a mentoring position.
    connection_form.cleaned_data['org_mentor'] = True
    if connection_form.cleaned_data['role'] == '2':
      connection_form.cleaned_data['org_org_admin'] = True

    # Get the user's email for the notification.
    receiver = [GSoCProfile.all().ancestor(self.data.user).get().email,]

    def create_connection(user):
      if not check_existing_connection_txn(user, self.data.organization):
        raise AccessViolation(DEF_CONNECTION_EXISTS)
      connection = connection_form.create(parent=user, commit=True)
      context = notifications.connectionContext(self.data, connection, 
          receiver)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=connection)
      sub_txn()
      return connection
    
    self.data.connection = None

    import logging
    # Traverse the list of cleaned user ids and generate connections to
    # each of them. The current user is the org admin, so we need to get
    # the user object and their profile to populate the Connection instance.
    for user in self.data.user_connections:
      connection_form.instance = None
      connection_form.cleaned_data['user'] = user
      profile = GSoCProfile.all().ancestor(user).get()
      connection_form.cleaned_data['profile'] = profile
      db.run_in_transaction(create_connection, user)

    def create_anonymous_connection(email):
      # Create the anonymous connection - a placeholder until the user 
      # registers and activates the real connection.
      connection = GSoCAnonymousConnection(parent=self.data.organization)
      if connection_form.cleaned_data['role'] == '2':
        connection.role = 'org_admin'
      else:
        connection.role = 'mentor' 
      # Generate a hash of the object's key for later validation.
      m = hashlib.md5()
      m.update(str(connection.key()))
      connection.hash_id = m.hexdigest()
      connection.put()

      # Notify the user that they have a pending connection and can register
      # to accept the elevated role.
      context = notifications.anonymousConnectionContext(self.data, email, 
          connection.role, hash_id)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=connection)
      sub_txn()

    for email in self.data.anonymous_users:
      db.run_in_transaction(create_anonymous_connection, email)
        
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
      q.filter('org_mentor =', None)
      q.filter('org_org_admin =', None)
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
    # anything other than the user_mentor boolean for now.
    connection_form.cleaned_data['profile'] = self.data.profile
    connection_form.cleaned_data['organization'] = self.data.organization
    connection_form.cleaned_data['user_mentor'] = True
	
    # Get the sender and recipient for the notification email.
    q = GSoCProfile.all().filter('org_admin_for', self.data.organization)
    q = q.filter('status =', 'active').filter('notify_new_requests =', True)
    admins = q.fetch(50)
    receivers = [i.email for i in admins]

    def create_connection(org):
      if not check_existing_connection_txn(self.data.user, 
          self.data.organization):
        raise AccessViolation(DEF_CONNECTION_EXISTS)
      connection = ConnectionForm.create(connection_form, 
          parent=self.data.user, 
          commit=True)
      context = notifications.connectionContext(self.data, connection, 
          receivers, True)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=connection)
      sub_txn()
    
    db.run_in_transaction(create_connection, self.data.organization)

    return True

class ShowConnection(RequestHandler):
  """ Class to encapsulate the methods required to display information
  about a GSoCConnection for both Users and Org Admins. """
  
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
        url(r'connection/%s$' % url_patterns.SHOW_CONNECTION,
            self, name=url_names.GSOC_SHOW_CONNECTION)
    ]

  def checkAccess(self):
    self.check.isProgramVisible()
    self.check.hasProfile()

    self.mutator.connectionFromKwargs()

    self.check.canViewConnection()
    self.data.is_org_admin = not (self.data.url_profile == self.data.profile)

  def getComments(self, limit=1000):
    """Gets all the comments for the proposal visible by the current user.
    """
    assert isSet(self.data.connection)

    public_comments = []
    private_comments = []

    query = db.Query(GSoCComment).ancestor(self.data.connection)
    query.order('created')
    all_comments = query.fetch(limit=limit)

    for comment in all_comments:
      if not comment.is_private:
        public_comments.append(comment)
      elif self.data.is_org_admin:
        private_comments.append(comment)

    return public_comments, private_comments
    
  def context(self):
    """ Handler for Show GSoCConnection get request. """

    header_name = self.data.url_profile.public_name \
        if self.data.is_org_admin else self.data.organization.name

    # Determine which buttons will be shown to the user.
    mentor = admin = None
    if self.data.is_org_admin:
      mentor = self.data.connection.org_mentor
      admin = self.data.connection.org_org_admin
    else:
      mentor = self.data.connection.user_mentor
      admin = self.data.connection.user_org_admin

    # Basically button visibility is the opposite of the state they represent.
    accept_mentor = True if not mentor else False
    reject_mentor = True if mentor is True or None else False
    accept_org_admin = True if not admin else False
    reject_org_admin = True if admin is True or None else False
        
    # Fetch the two statuses from the perspective of both parties.
    user_status = self._determineStatus(self.data.connection.user_mentor,
        self.data.connection.user_org_admin)
    org_status = self._determineStatus(self.data.connection.org_mentor,
        self.data.connection.org_org_admin)

    public_comments, private_comments = self.getComments()
    comment_kwargs = self.kwargs.copy()
    form = CommentForm(self.data.POST or None) if not self.data.is_org_admin \
        else PrivateCommentForm(self.data.POST or None)
    comment_box = {
      'form' : form,
      'action' : reverse(url_names.GSOC_COMMENT_CONNECTION,
           kwargs=comment_kwargs)
    }
    
    return {
      'page_name': 'Viewing Connection',
      'is_admin' : self.data.is_org_admin,
      'header_name': header_name,
      'user_email' : self.data.connection.profile.email,
      'org_name' : self.data.connection.organization.name,
      'user_status' : user_status,
      'org_status' : org_status,
      'connection' : self.data.connection,
      'actions' : self.ACTIONS,
      'accept_mentor' : accept_mentor,
      'reject_mentor' : reject_mentor,
      'accept_org_admin' : accept_org_admin,
      'reject_org_admin' : reject_org_admin,
      'comment_box' : comment_box,
      'private_comments_visible' : self.data.is_org_admin,
      'public_comments' : public_comments,
      'private_comments' : private_comments
    }

  def _determineStatus(self, mentor, admin):
    """ Returns an apropriate status message for the viewer depending on the 
    state of the connection and who is viewing the page. 
    """
    status = None

    if mentor:
      if admin:
        status = 'Accepted Org Admin Connection'
      else:
        status = 'Accepted Mentor Connection'
    elif mentor is None:
      status = 'Pending Connection'
    elif not mentor:
      status = 'Rejected Connection'
    return status
    
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
    
    def accept_mentor_txn():
      connection = db.get(connection_key)
      
      if self.data.is_org_admin:
        connection.org_mentor = True
      else:
        connection.user_mentor = True
      
      # If both the org admin and user agree to a mentoring role, promote
      # the user to a mentor.
      if connection.user_mentor and connection.org_mentor:
        profile = db.get(profile_key)
        profile.is_mentor = True
        profile.mentor_for.append(org_key)
        profile.mentor_for = list(set(profile.mentor_for))
        profile.put()
      
      connection.put()
      
    db.run_in_transaction(accept_mentor_txn)
  
  def _rejectMentor(self):
    connection_key = self.data.connection.key()
    
    def decline_mentor_txn():
      connection = db.get(connection_key)
      if self.data.is_org_admin:
        connection.org_mentor = False
      else:
        connection.user_mentor = False
      connection.put()
      
    db.run_in_transaction(decline_mentor_txn)
    
  def _acceptOrgAdmin(self):
    profile_key = self.data.url_profile.key()
    connection_key = self.data.connection.key()
    org_key = self.data.organization.key()
    
    def accept_org_admin_txn():
      connection = db.get(connection_key)
      if self.data.is_org_admin:
        connection.org_org_admin = True
        connection.org_mentor = True
      else:
        connection.user_org_admin = True
        connection.user_mentor = True
    
      if connection.org_org_admin and connection.user_org_admin:
        profile = db.get(profile_key)
        # Org Admins are mentors by default, so we have to promote the 
        # user twice - one to mentor, one to org admin.
        profile.is_mentor = True
        profile.mentor_for.append(org_key)
        profile.mentor_for = list(set(profile.mentor_for))
        
        profile.is_org_admin = True
        profile.org_admin_for.append(org_key)
        profile.org_admin_for = list(set(profile.org_admin_for))
        
        profile.put()
      connection.put()
      
    db.run_in_transaction(accept_org_admin_txn)
    
  def _rejectOrgAdmin(self):
    connection_key = self.data.connection.key()
    
    def decline_org_admin_txn():
      connection = db.get(connection_key)
      if self.data.is_org_admin:
        # Org can just 'withdraw' the org admin offer.
        connection.org_org_admin = False
      else:
        # User rejecting an org admin offer rejects both.
        connection.user_org_admin = False
        connection.user_mentor = False
      connection.put()
      
    db.run_in_transaction(decline_org_admin_txn)


class PostComment(RequestHandler):
  """View which handles publishing comments about a connection
  """

  def djangoURLPatterns(self):
    return [
         url(r'connection/comment/%s$' % COMMENT, self, 
             name=url_names.GSOC_COMMENT_CONNECTION),
    ]

  def checkAccess(self):
    self.check.isProgramVisible()
    self.check.isProfileActive()
    self.mutator.userFromKwargs()
    self.mutator.connectionFromKwargs()
    self.mutator.commentVisible(self.data.connection.organization)

    # check if the comment is given by the author of the proposal
    if self.data.connection.profile.key() == self.data.profile.key():
      self.data.public_only = True
      return

    self.data.public_only = False
    self.check.isMentorForOrganization(self.data.connection.organization)

  def createCommentFromForm(self):
    """Creates a new comment based on the data inserted in the form.

    Returns:
      a newly created comment entity or None
    """

    assert isSet(self.data.public_only)
    assert isSet(self.data.connection)

    if self.data.public_only:
      comment_form = CommentForm(self.data.request.POST)
    else:
      # This form contains checkbox for indicating private/public comments.
      comment_form = PrivateCommentForm(self.data.request.POST)

    if not comment_form.is_valid():
      return None

    if self.data.public_only:
      comment_form.cleaned_data['is_private'] = False
    comment_form.cleaned_data['author'] = self.data.profile

    q = GSoCProfile.all().filter('mentor_for', 
        self.data.connection.organization)
    q = q.filter('status', 'active')
    if comment_form.cleaned_data.get('is_private'):
      q.filter('notify_private_comments', True)
    else:
      q.filter('notify_public_comments', True)
    mentors = q.fetch(1000)

    to_emails = [i.email for i in mentors \
                 if i.key() != self.data.profile.key()]

    def create_comment_txn():
      comment = comment_form.create(commit=True, parent=self.data.connection)
      context = gsoc_notifications.newCommentContext(self.data, comment, to_emails)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=comment)
      sub_txn()
      return comment

    return db.run_in_transaction(create_comment_txn)

  def post(self):

    connection = self.createCommentFromForm()
    if connection:
      # TODO(dcrodman): Change the org_admin_requests page to org_connections
      self.redirect.program()
      self.redirect.to('gsoc_dashboard', anchor='org_admin_requests')
    else:
      self.redirect.show_connection(self.data.user, self.data.organization)
      self.redirect.to(url_names.GSOC_SHOW_CONNECTION, validated=True)

  def get(self):
    self.error(405)