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
""" Module containing the view for the Connection page """

import hashlib

from google.appengine.ext import db
from google.appengine.api import users

from django import forms as django_forms
from django.core.urlresolvers import reverse
from django.forms.fields import ChoiceField
from django.utils.translation import ugettext

from melange.request import exception
from melange.logic import connection as connection_logic
from melange.models import connection
from melange.models.connection_message import ConnectionMessage
from soc.logic import accounts
from soc.logic import cleaning
from soc.logic.helper import notifications
from soc.models.user import User
from soc.modules.gsoc.logic.helper import notifications as gsoc_notifications
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views import forms as gsoc_forms
from soc.modules.gsoc.views.forms import GSoCModelForm
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper.url_patterns import url
from soc.views.helper import url_patterns
from soc.views.helper.access_checker import isSet
from soc.tasks import mailer


DEF_NONEXISTANT_USER = 'The user with the email %s does not exist.'

@db.transactional
def create_connection_txn(data, profile, organization,
    role, message, context, recipients,
    org_state=connection.STATE_UNREPLIED,
    user_state=connection.STATE_UNREPLIED):
  """ Create a new Connection entity, attach any messages provided by the
  initiator and send a notification email to the recipient(s).

  Args:
    data: RequestData object for the current request.
    profile: Profile with which to connect.
    organization: Organization with which to connect.
    message: User-provided message for the connection.
    context: The notification context method.
    recipients: List of one or more recipients for the notification email.
    org_state: Org state for the connection.
    user_state: User state for the connection.

  Returns:
    The newly created Connection entity.
  """
  if connection_logic.connectionExists(profile.parent(), organization):
    raise exception.Forbidden(message=connection.CONNECTION_EXISTS_ERROR %
        (profile.name, organization.name))
    # Generate the new connection.
  new_connection = connection_logic.createConnection(
      profile=profile, org=organization,
      org_state=org_state, user_state=user_state,
      role=role)
  # Attach any user-provided messages to the connection.
  if message:
    connection_logic.createConnectionMessage(
      connection=new_connection, author=profile, content=message)
  # Dispatch an email to the user.
  notification = context(data=data, connection=new_connection,
      recipients=recipients, message=message)
  sub_txn = mailer.getSpawnMailTaskTxn(notification, parent=new_connection)
  sub_txn()

  return new_connection

def clean_link_id(link_id):
  """Apply validation filters to a single link id from the user field.

  Returns:
      User instance to which the link_id corresponds or None if the
      link_id does not correspond to an existing User instance.
  Raises:
      forms.ValidationError if a provided link_id is invalid or does
      not correspond to an existing user.
  """
  try:
    cleaning.cleanLinkID(link_id)
  except gsoc_forms.ValidationError:
    # Catch and re-raise the exception to provide a more helpful error
    # message than "One or more Link_ids is not valid."
    raise gsoc_forms.ValidationError(
        '"%s" is not a valid link id.' % link_id)
  user = User.get_by_key_name(link_id)
  if not user:
    raise gsoc_forms.ValidationError(
        '%s does not correspond to a profile.' % link_id)
  return user

def clean_email(email):
  """Apply validation filters to an email from the user field.

  Returns:
      User entity affiliated with the given email address or None if
      either no User with that email address exists or they do not
      have a profile for the current program.

  Raises:
      forms.ValidationError if the email address is invalid.
  """
  # Current id is an email address.
  cleaning.cleanEmail(email)
  # If we can't find a user for the given email, it's an anonymous user.
  account = users.User(email)
  user_account = accounts.normalizeAccount(account)
  user = User.all().filter('account', user_account).get()
  if user and GSoCProfile.all().ancestor(user).count(limit=1) >= 1:
    return user
  else:
    # The User entity does not exist or they do not have a profile.
    return None

class ConnectionForm(GSoCModelForm):
  """Django form for the Connection page."""

  message = gsoc_forms.CharField(widget=gsoc_forms.Textarea())

  def __init__(self, request_data=None, message=None, *args, **kwargs):
    """Initialize ConnectionForm.

    Note that while it appears that message and request_data are not used,
    they are essential for the way connections are generated later through
    the use of this form.

    Args:
        request_data: The RequestData instance for the current request.
        message: A string containing a message to be sent to the other party.
    """
    super(ConnectionForm, self).__init__(*args, **kwargs)

    self.request_data = request_data

    # Set up the user-provided message to the other party (org admin or user).
    self.fields['message'].label = ugettext('Message')
    # Place the message field at the bottom
    self.fields['message'].group = ugettext('1. ')
    self.fields['message'].required = False
    self.fields['message'].help_text = ugettext(
        'Your message to the recipient(s)')

  class Meta:
    model = connection.Connection
    exclude = connection.Connection.allFields()

class OrgConnectionForm(ConnectionForm):
  """Django form to show specific fields for an organization."""

  users = gsoc_forms.CharField(label='Link_Id/Email')

  def __init__(self, request_data=None, message=None, *args, **kwargs):
    super(OrgConnectionForm, self).__init__(*args, **kwargs)

    self.request_data = request_data

    field = self.fields.pop('users')
    field.help_text = ugettext(
        'The link_id or email address of the invitee(s), '
        ' separate multiple values with a comma')
    self.fields.insert(0, 'users', field)

    role_choices = (
      (connection.MENTOR_ROLE, 'Mentor'),
      (connection.ORG_ADMIN_ROLE, 'Org Admin'))
    self.fields['role'].widget = django_forms.fields.Select(
        choices=role_choices)
    self.fields['role'].label = ugettext('Role to offer the user(s)')
    self.fields['role'].help_text = ugettext(
        'Role that you are offering to '
        'the specified users in this organization')

  def clean_users(self):
    """Generate lists with the provided link_ids/emails sorted into categories.

    Overrides the default cleaning of the link_ids field to add custom
    validation to the users field.
    """
    id_list = self.cleaned_data['users'].split(',')
    # List containing User entities referenced via link ids or emails from
    # the form data provided by the org admin.
    self.request_data.valid_users = []
    # List of emails that do not correspond to valid Users.
    self.request_data.anonymous_users = []

    for user_id in id_list:
      if '@' in user_id:
        user = clean_email(user_id)
        if user:
          self.request_data.valid_users.append(user)
        else:
          self.request_data.anonymous_users.append(user_id)
      else:
        user = clean_link_id(user_id)
        self.request_data.valid_users.append(user)

  class Meta:
    model = connection.Connection
    fields = ['role']


class MessageForm(GSoCModelForm):
  """Django form for the message."""

  def __init__(self, *args, **kwargs):
    super(MessageForm, self).__init__(*args, **kwargs)
    self.fields['content'].label = ugettext(' ')

  class Meta:
    model = ConnectionMessage
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
    return 'modules/gsoc/connection/_message_form.html'

class ConnectionResponseForm(GSoCModelForm):
  """Django form to provide Connection responses in ShowConnection.
  """
  responses = django_forms.fields.ChoiceField(widget=django_forms.Select())

  def __init__(self, request_data=None, choices=None, *args, **kwargs):
    super(ConnectionResponseForm, self).__init__(*args, **kwargs)

    self.request_data = request_data

    self.fields['responses'].group = ugettext('1. ')
    self.fields['responses'].help_text = ugettext(
        'Select an action to take.')
    self.fields['responses'].choices = choices
    self.fields['responses'].required = False

  def templatePath(self):
    return 'modules/gsoc/connection/_response_form.html'


class OrgConnectionPage(base.GSoCRequestHandler):
  """Class to encapsulate the methods for an org admin to initiate a
  connection between the organization and a given user.
  """

  def templatePath(self):
    return 'modules/gsoc/connection/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'connect/%s$' % url_patterns.ORG,
            self, name=url_names.GSOC_ORG_CONNECTION)
    ]

  def _generate(self, data):
    """Create a Connection instance and notify all parties involved.

    Take the link_id(s) and email(s) that the org admin provided via
    ConnectionForm instance and create new Connections and AnonymousConnections
    as necessary, dispatching emails to the relevant parties as necessary. If
    the org admin provided email addresses of users who do not have profiles
    for the current program, AnonymousConnection instances will be generated
    and emails dispatched inviting them to join the program and accept the
    offered role. Lists are generated and included in a later self.get() call
    to inform the org admin which connections were established

    Args:
        data: The RequestData object passed with this request.
    Returns:
        True if no errors were encountered or False if the form was invalid.
        Note that it sets data attributes that are handled in the post()
        method of this handler below.
    """
    connection_form = OrgConnectionForm(request_data=data, data=data.POST)

    if not connection_form.is_valid():
      return False

    # The valid_users field should contain a list of User instances populated
    # by the form's cleaning methods.
    for user in data.valid_users:
      connection_form.instance = None
      profile = GSoCProfile.all().ancestor(user).get()
      create_connection_txn(
          data=data, profile=profile, organization=data.organization,
          role=connection_form.cleaned_data['role'],
          message=connection_form.cleaned_data['message'],
          context=notifications.orgConnectionContext,
          recipients=[profile.email], org_state=connection.STATE_ACCEPTED)

    # TODO(drew): This entire section below needs to be replaced with code
    # similar to the lines immediately above or to something else entirely
    # once the new Connection model is implemented.
    def create_anonymous_connection_txn(email):
      # Create the anonymous connection - a placeholder until the user
      # registers and activates the real connection.
      new_connection = connection.AnonymousConnection(parent=data.organization)
      new_connection.role = connection_form.cleaned_data['role']
      new_connection.put()

      # Generate a hash of the object's key for later validation.
      m = hashlib.md5()
      m.update(str(new_connection.key()))
      new_connection.hash_id = unicode(m.hexdigest())
      new_connection.email = email
      new_connection.put()

      # Notify the user that they have a pending connection and can register
      # to accept the elevated role.
      context = notifications.anonymousConnectionContext(data, email,
          new_connection, connection_form.cleaned_data['message'])
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=new_connection)
      sub_txn()

    q = connection.AnonymousConnection.all()
    data.sent_email_to = []
    data.duplicate_email = []
    for email in data.anonymous_users:
      new_q = q.filter('email', email).get()
      if new_q:
        data.duplicate_email.append(email)
      else:
        data.sent_email_to.append(email)
        db.run_in_transaction(create_anonymous_connection_txn, email)

    return True

  def checkAccess(self, data, check, mutator):
    assert isSet(data.organization)
    check.isProgramVisible()
    check.isOrganizationInURLActive()
    check.hasProfile()
    check.isOrgAdminForOrganization(data.organization)

  def context(self, data, check, mutator):
    """Handler for Connection page request for an org."""

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

    if self._generate(data):
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
      # TODO(nathaniel): problematic self-call.
      return self.get(data, check, mutator)


class UserConnectionPage(base.GSoCRequestHandler):
  """Class to encapsulate the methods for a user to initiate a connection
  between him or her self and an organization.
  """

  def templatePath(self):
    return 'modules/gsoc/connection/base.html'

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

  def _generate(self, data):
    """Create a Connection instance and notify all parties involved.
    """

    assert isSet(data.organization)
    assert isSet(data.user)

    connection_form = ConnectionForm(request_data=data, data=data.POST)
    if not connection_form.is_valid():
      return False

    # Get the sender and recipient for the notification email.
    q = GSoCProfile.all().filter('org_admin_for', data.organization)
    q = q.filter('status =', 'active').filter('notify_new_requests =', True)
    admins = q.fetch(50)
    recipients = [i.email for i in admins]

    create_connection_txn(
        data=data, profile=data.profile, organization=data.organization,
        role=connection.MENTOR_ROLE,
        message=connection_form.cleaned_data['message'],
        context=notifications.userConnectionContext,
        recipients=recipients, user_state=connection.STATE_ACCEPTED)

    return True

  def context(self, data, check, mutator):
    """Handler for Connection page request."""

    connection_form = ConnectionForm(request_data=data,
        message=data.organization.role_request_message,
        data=data.POST or None)

    return {
      'profile_created': data.GET.get('profile') == 'created',
      'page_name': 'Open a connection',
      'program': data.program,
      'connection_form': connection_form,
    }

  def post(self, data, check, mutator):
    """Handler for a GSoC Connection post request for a user."""

    if self._generate(data):
      data.redirect.connect_user(user=data.user)
      return data.redirect.to(url_names.GSOC_USER_CONNECTION, validated=True)
    else:
      # TODO(nathaniel): problematic self-call.
      return self.get()


class ShowConnection(base.GSoCRequestHandler):
  """Class to encapsulate the methods required to display information
  about a Connection for both Users and Org Admins.
  """

  # The actions that will be made available to the user in the dropdown.
  RESPONSES = {
    'accept_mentor' : ('accept_mentor', 'Accept Mentor'),
    'reject_mentor' : ('reject_mentor', 'Reject Mentor'),
    'accept_org_admin' : ('accept_org_admin', 'Accept Org Admin'),
    'reject_org_admin' : ('reject_org_admin', 'Reject Org Admin'),
    'withdraw' : ('withdraw', 'Withdraw'),
    'delete' : ('delete', 'Delete')
  }

  def templatePath(self):
    return 'modules/gsoc/connection/show_connection.html'

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

  def getMessages(self, data, limit=1000):
    """Gets all the messages for the connection."""
    assert isSet(data.connection)

    query = db.Query(ConnectionMessage).ancestor(data.connection)
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
    """Handler for Show Connection get request."""
    # Shortcut for clarity/laziness.
    c = data.connection
    is_org_admin = data.orgAdminFor(data.organization)
    header_name = data.url_user.link_id \
        if is_org_admin else data.organization.name

    # This isn't pretty by any stretch of the imagination, but it's going
    # to stay like this for now in the interest of my time and sanity. The
    # basic rules for displaying options are in the getMentorChoices() method
    # and the code following includes some tweaks for user/org admin.
    choices = []
    if c.isWithdrawn():
      # Allow an org to delete or re-open the connection.
      if is_org_admin:
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
      if is_org_admin:
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
      if is_org_admin:
        choices = self.getMentorChoices(mentor_options, c.isOrgUnreplied(),
            c.isOrgAccepted(), c.isOrgRejected(), c.isOrgWithdrawn())
        if c.isOrgUnreplied():
          choices.append(self.RESPONSES['accept_org_admin'])
        if c.role == connection.ORG_ADMIN_ROLE:
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
        if c.role == connection.ORG_ADMIN_ROLE:
          choices = choices + self.getMentorChoices(org_admin_options,
            c.isUserUnreplied(), c.isUserAccepted(), c.isUserRejected(),
            c.isUserWithdrawn())

    if choices.count(self.RESPONSES['withdraw']) > 1:
      choices.remove(self.RESPONSES['withdraw'])

    response_form = None
    if len(choices) > 0:
      response_form = ConnectionResponseForm(
          request_data=data.POST or None,
          choices=choices
          )

    message_form = MessageForm(data.POST or None)
    message_box = {
        'form' : message_form,
        'action' : reverse(url_names.GSOC_CONNECTION_MESSAGE,
             kwargs=data.kwargs.copy())
        }

    return {
        'page_name': 'Viewing Connection',
        'is_admin' : is_org_admin,
        'header_name': header_name,
        'connection' : data.connection,
        'message_box' : message_box,
        'messages' : self.getMessages(data),
        'response_form' : response_form
        }

  def post(self, data, check, mutator):
    """Handler for Show GSoC Connection post request."""

    # TODO(dcrodman): Figure out why this needs to be computed differently
    # than in the context() method above.
    is_org_admin = data.connection.organization.key() in \
        data.profile.org_admin_for
    response = data.POST['responses']

    if response == 'accept_mentor':
      self._acceptMentor(data, is_org_admin)
    elif response == 'reject_mentor':
      self._rejectMentor(data, is_org_admin)
    elif response == 'accept_org_admin':
      self._acceptOrgAdmin(data, is_org_admin)
    elif response == 'reject_org_admin':
      self._rejectOrgAdmin(data, is_org_admin)
    elif response == 'delete':
      self._deleteConnection(data)
    elif response == 'withdraw':
      self._withdrawConnection(data, is_org_admin)

    if response == 'none':
      return data.redirect.show_connection(user=data.connection.parent(),
          connection=data.connection)
    else:
      data.redirect.dashboard()
      return data.redirect.to()

  def _acceptMentor(self, data, is_org_admin):
    """The User has accepted the Mentoring role, so we need to add the user
    to the organization's list of mentors.
    """

    profile_key = data.url_profile.key()
    connection_key = data.connection.key()
    org_key = data.organization.key()
    messages = data.program.getProgramMessages()

    def accept_mentor_txn():
      connection_entity = db.get(connection_key)

      # Reset both parties' states after a connection becomes active again.
      # The user or org admin re-activating the connection will be marked
      # as accepted anyway in the next lines.
      if connection_entity.isWithdrawn():
        connection_entity.org_state = connection.STATE_UNREPLIED
        connection_entity.user_state = connection.STATE_UNREPLIED

      if is_org_admin:
        connection_entity.org_state = connection.STATE_ACCEPTED
      else:
        connection_entity.user_state = connection.STATE_ACCEPTED
      connection_entity.put()

      # If both the org admin and user agree to a mentoring role, promote
      # the user to a mentor. It is possible for a user to accept only a
      # mentoring role from an org admin connection, so there need not be
      # any role check.
      if connection_entity.isUserAccepted() and \
          connection_entity.isOrgAccepted():
        profile = db.get(profile_key)

        # Send out a welcome email to new mentors.
        if not profile.is_mentor:
          mentor_mail = notifications.getMentorWelcomeMailContext(
              profile, data, messages)
          if mentor_mail:
            mailer.getSpawnMailTaskTxn(mentor_mail, parent=connection_entity)()

        # This should theoretically never happen, but it improves stability.
        if org_key not in profile.mentor_for:
          profile.is_mentor = True
          profile.mentor_for.append(org_key)
          profile.mentor_for = list(set(profile.mentor_for))
          profile.put()

          generate_message_txn(connection_entity,
              '%s promoted to Mentor.' % profile.link_id)

    db.run_in_transaction(accept_mentor_txn)

  def _rejectMentor(self, data, is_org_admin):
    connection_key = data.connection.key()

    def decline_mentor_txn():
      connection_entity = db.get(connection_key)
      if is_org_admin:
        connection_entity.org_state = connection.STATE_REJECTED
      else:
        connection_entity.user_state = connection.STATE_REJECTED
      connection_entity.put()

      generate_message_txn(connection_entity, 'Mentor Connection Rejected.')

    db.run_in_transaction(decline_mentor_txn)

  def _acceptOrgAdmin(self, data, is_org_admin):
    profile_key = data.url_profile.key()
    connection_key = data.connection.key()
    org_key = data.organization.key()
    messages = data.program.getProgramMessages()

    def accept_org_admin_txn():
      connection_entity = db.get(connection_key)

      # The org accepted a new role for the user, so reset the user's response
      # to give him or her time to review the change.
      if connection_entity.role == connection.MENTOR_ROLE:
        connection_entity.user_state = connection.STATE_UNREPLIED
        connection_entity.org_state = connection.STATE_UNREPLIED

      connection_entity.role = connection.ORG_ADMIN_ROLE

      if is_org_admin:
        connection_entity.org_state = connection.STATE_ACCEPTED
      else:
        connection_entity.user_state = connection.STATE_ACCEPTED

      connection_entity.put()

      if connection_entity.isOrgAccepted() and connection_entity.isUserAccepted():
        profile = db.get(profile_key)

        # Send out a welcome email to new mentors.
        if not profile.is_mentor:
          mentor_mail = notifications.getMentorWelcomeMailContext(
              profile, data, messages)
          if mentor_mail:
            mailer.getSpawnMailTaskTxn(mentor_mail, parent=connection_entity)()

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

          generate_message_txn(connection_entity,
              '%s promoted to Org Admin.' % profile.link_id)

    db.run_in_transaction(accept_org_admin_txn)

  def _rejectOrgAdmin(self, data, is_org_admin):
    connection_key = data.connection.key()

    def decline_org_admin_txn():
      connection_entity = db.get(connection_key)
      if is_org_admin:
        # Org can just 'withdraw' the org admin offer.
        connection_entity.org_state = connection.STATE_REJECTED
      else:
        # User rejecting an org admin offer rejects both.
        connection_entity.user_state = connection.STATE_REJECTED
      connection_entity.put()

      generate_message_txn(connection_entity, 'Org Admin Connection Rejected.')

    db.run_in_transaction(decline_org_admin_txn)


  def _withdrawConnection(self, data, is_org_admin):
    connection_key = data.connection.key()

    def withdraw_connection_txn():
      # Mark the connection on the user or org side as 'Rejected' and add an auto-comment
      connection_entity = db.get(connection_key)
      if is_org_admin:
        connection_entity.org_state = connection.STATE_WITHDRAWN
      else:
        connection_entity.user_state = connection.STATE_WITHDRAWN
      connection_entity.put()

      generate_message_txn(connection_entity, 'Connection withdrawn.')

    db.run_in_transaction(withdraw_connection_txn)

  def _deleteConnection(self, data):
    connection_key = data.connection.key()

    def delete_connection_txn():
      connection_entity = db.get(connection_key)
      db.delete(ConnectionMessage.all().ancestor(connection_entity))
      connection_entity.delete()

    db.run_in_transaction(delete_connection_txn)

class SubmitConnectionMessagePost(base.GSoCRequestHandler):
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

    check.isOrgAdmin()

  def createMessageFromForm(self, data):
    """Creates a new message based on the data inserted in the form.

    Args:
      data: a request_data.RequestData object

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

      # TODO(drew): add notifications

      return message

    return db.run_in_transaction(create_message_txn)

  def post(self, data, check, mutator):
    message = self.createMessageFromForm(data)
    if message:
      data.redirect.show_connection(data.url_user, data.connection)
      return data.redirect.to(validated=True)
    else:
      data.redirect.show_connection(data.url_user, data.connection)

      # TODO(nathaniel): calling GET logic from a POST handling path.
      # a bit hacky :-( may be changed when possible
      data.request.method = 'GET'
      request_handler = ShowConnection()
      return request_handler(data.request, *data.args, **data.kwargs)

  def get(self, data, check, mutator):
    raise exception.MethodNotAllowed()
