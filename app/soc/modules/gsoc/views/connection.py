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

"""Module containing the view for the Connection page."""

from google.appengine.ext import db
from google.appengine.api import users

from django import forms as django_forms
from django.core.urlresolvers import reverse
from django.forms.fields import ChoiceField
from django.utils.translation import ugettext

from melange.logic import connection as connection_logic
from melange.logic import profile as profile_logic
from melange.models import connection
from melange.request import exception
from melange.utils import rich_bool
from melange.views import connection as connection_view
from soc.logic import accounts
from soc.logic import cleaning
from soc.logic.helper import notifications
from soc.models.user import User
from soc.modules.gsoc.logic import profile as soc_profile_logic
from soc.modules.gsoc.logic import project as project_logic
from soc.modules.gsoc.logic import proposal as proposal_logic
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views import forms as gsoc_forms
from soc.modules.gsoc.views.forms import GSoCModelForm
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper.url_patterns import url
from soc.views.helper import url_patterns
from soc.views.helper.access_checker import isSet


DEF_INVALID_LINK_ID = '%s is not a valid link id.'
DEF_NONEXISTANT_LINK_ID = 'No user with the link id %s exists.'
USER_HAS_ROLE = '%s already has a role with this organization.'
NO_OTHER_ADMIN = '%s is the only administrator for this organization.'

USER_ASSIGNED_MENTOR = '%s promoted to Mentor.'
USER_ASSIGNED_ORG_ADMIN = '%s promoted to Org Admin.'
USER_ASSIGNED_NO_ROLE = '%s no longer has a role for this organizaton.'


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
        DEF_INVALID_LINK_ID % link_id)
  user = User.get_by_key_name(link_id)
  if not user:
    raise gsoc_forms.ValidationError(
        DEF_NONEXISTANT_LINK_ID % link_id)
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

# TODO(drew): Feasible to make this txn safe?
def canUserResignRoleForOrg(profile_key, org_key):
  """Determine whether or not a resignation is legal.

  Args:
    profile: Key of GSoCProfile to evaluate.
    organization: Key of GSoCOrganization to evaluate
  Returns:
    melange.utils.rich_bool.RichBool indicating whether ot not a profile
    can legally resign and a reason as to why or why not.
  """
  profile = db.get(profile_key)

  if org_key in profile.org_admin_for:
    if not soc_profile_logic.canResignAsOrgAdminForOrg(profile, org_key):
      return rich_bool.RichBool(
          value=False, extra=NO_OTHER_ADMIN % profile.name())

  if org_key in profile.mentor_for:
    if proposal_logic.hasMentorProposalAssigned(
        profile, org_key=org_key):
      return rich_bool.RichBool(False,
          value='There is a proposal assigned to %s.' % profile.name())
    if project_logic.hasMentorProjectAssigned(profile, org_key=org_key):
      return rich_bool.RichBool(False,
          value='There is a project assigned to %s.' % profile.name())

  return rich_bool.RichBool(value=True)

class ConnectionForm(GSoCModelForm):
  """Django form for the Connection page."""

  message = gsoc_forms.CharField(widget=gsoc_forms.Textarea())

  def __init__(self, request_data=None, message=None, **kwargs):
    """Initialize ConnectionForm.

    Note that while it appears that message and request_data are not used,
    they are essential for the way connections are generated later through
    the use of this form.

    Args:
        request_data: The RequestData instance for the current request.
        message: A string containing a message to be sent to the other party.
    """
    super(ConnectionForm, self).__init__(**kwargs)

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

  def __init__(self, request_data=None, message=None, **kwargs):
    super(OrgConnectionForm, self).__init__(**kwargs)

    self.request_data = request_data

    field = self.fields.pop('users')
    field.help_text = ugettext(
        'The link_id or email address of the invitee(s), '
        ' separate multiple values with a comma')
    self.fields.insert(0, 'users', field)

    role_choices = (
      (connection.MENTOR_ROLE, 'Mentor'),
      (connection.ORG_ADMIN_ROLE, 'Org Admin'))
    self.fields['org_role'].widget = django_forms.fields.Select(
        choices=role_choices)
    self.fields['org_role'].label = ugettext('Role to offer the user(s)')
    self.fields['org_role'].help_text = ugettext(
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
    fields = ['org_role']


class MessageForm(GSoCModelForm):
  """Django form for the message."""

  def __init__(self, **kwargs):
    super(MessageForm, self).__init__(**kwargs)
    self.fields['content'].label = ugettext(' ')

  class Meta:
    model = connection.ConnectionMessage
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
  role_response = ChoiceField(widget=django_forms.Select())

  def __init__(self, request_data=None, choices=None, **kwargs):
    super(ConnectionResponseForm, self).__init__(**kwargs)

    self.request_data = request_data

    self.fields['role_response'].group = ugettext('1. ')
    self.fields['role_response'].help_text = ugettext(
        'Select an action to take.')
    self.fields['role_response'].choices = choices
    self.fields['role_response'].required = False

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
      connection_view.createConnectionTxn(
          data, profile, data.organization,
          connection_form.cleaned_data['message'],
          notifications.orgConnectionContext, [profile.email],
          org_role=connection_form.cleaned_data['org_role'])

    # anonymous_connections should contain the emails of unregistered users
    # from the form.
    data.unregistered = []
    for user in data.anonymous_users:
      connection_view.createAnonymousConnectionTxn(
          data=data,
          organization=data.organization,
          org_role=connection_form.cleaned_data['org_role'],
          email=user,
          message=connection_form.cleaned_data['message']
          )
      data.unregistered.append(user)

    return True

  def checkAccess(self, data, check, mutator):
    assert isSet(data.organization)
    check.isProgramVisible()
    check.isOrganizationInURLActive()

    check.notStudent()
    check.isOrgAdminForOrganization(data.organization)

  def context(self, data, check, mutator):
    """Handler for Connection page request for an org."""

    connection_form = OrgConnectionForm(
        request_data=data,
        message=data.organization.role_request_message,
        data=data.POST or None)

    unregistered = None
    if 'unregistered' in data.request.GET:
      unregistered = data.request.GET['unregistered'].split(',')

    return {
      'page_name': 'Open a connection',
      'program': data.program,
      'connection_form': connection_form,
      'error': bool(connection_form.errors),
      'unregistered' : unregistered,
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
      if len(data.unregistered) > 0:
        unregistered = ','.join(data.unregistered)
        extra = ['unregistered=%s' % unregistered, ]
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

    connection_view.createConnectionTxn(
        data, data.profile, data.organization,
        connection_form.cleaned_data['message'],
        notifications.userConnectionContext,
        recipients, user_role=connection.ROLE)

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
      return self.get(data, check, mutator)

class ShowConnectionForOrgMemberPage(base.GSoCRequestHandler):
  """A page to show a connection for eligible members
  of the organization in question.
  """

  def templatePath(self):
    return 'modules/gsoc/connection/show_connection.html'

  def djangoURLPatterns(self):
    return [
        url(r'connection/%s$' % url_patterns.SHOW_CONNECTION, self,
            name=url_names.GSOC_SHOW_ORG_CONNECTION)
        ]

  def checkAccess(self, data, check, mutator):
    check.isProgramVisible()
    check.hasProfile()
    check.notStudent()
    check.canOrgMemberAccessConnection()

  def context(self, data, check, mutator):

    response_form = ConnectionResponseForm(choices=connection.ORG_RESPONSES)
    message_kwargs = data.kwargs.copy()
    del message_kwargs['organization']

    message_box = {
        'form' : MessageForm(data=data.POST or None),
        'action' : reverse(url_names.GSOC_CONNECTION_MESSAGE,
            kwargs=message_kwargs)
        }

    return {
        'page_name' : 'Viewing Connection',
        'header_name' : data.url_profile.name(),
        'connection' : data.url_connection,
        'response_form' : response_form,
        'message_box' : message_box
        }

  def _handleMentorSelection(self, data):

    message = data.program.getProgramMessages().mentor_welcome_msg

    @db.transactional(xg=True)
    def org_selected_mentor_txn():
      connection_entity = db.get(data.url_connection.key())
      connection_entity.org_role = connection.MENTOR_ROLE
      connection_entity.put()

      profile = db.get(data.url_connection.parent_key())
      if connection_entity.userRequestedRole():
        if not profile.is_mentor:
          connection_view.sendMentorWelcomeMail(data, profile, message)

        # Make sure that if a user is going from org admin to mentor that
        # they can legally resign as org admins.
        if data.url_connection.organization.key() in profile.org_admin_for:
          can_resign = soc_profile_logic.canResignAsOrgAdminForOrg(
              profile, data.url_connection.organization.key())
          if not can_resign:
            raise gsoc_forms.ValidationError(can_resign.extra())

        profile_logic.assignMentorRoleForOrg(
            profile, data.url_connection.organization.key())

        connection_logic.createConnectionMessage(
            connection_entity, USER_ASSIGNED_MENTOR % profile.name())

    org_selected_mentor_txn()

  def _handleOrgAdminSelection(self, data):

    message = data.program.getProgramMessages().mentor_welcome_msg

    @db.transactional(xg=True)
    def org_selected_orgadmin_txn():
      connection_entity = db.get(data.url_connection.key())
      connection_entity.org_role = connection.ORG_ADMIN_ROLE
      connection_entity.put()

      if connection_entity.userRequestedRole():
        profile = db.get(data.url_connection.parent_key())

        if not profile.is_mentor:
          connection_view.sendMentorWelcomeMail(data, profile, message)
        profile_logic.assignOrgAdminRoleForOrg(
            profile, data.url_connection.organization.key())

        connection_logic.createConnectionMessage(
            connection_entity, USER_ASSIGNED_ORG_ADMIN % profile.name())

    org_selected_orgadmin_txn()

  def _handleNoRoleSelection(self, data):
    @db.transactional(xg=True)
    def org_selected_norole_txn():
      connection_entity = db.get(data.url_connection.key())
      connection_entity.org_role = connection.NO_ROLE
      connection_entity.put()

      profile = db.get(data.url_connection.parent_key())
      org_key = data.url_connection.organization.key()
      if org_key in profile.mentor_for:
        profile_logic.assignNoRoleForOrg(profile, org_key)

        connection_logic.createConnectionMessage(
            connection_entity, USER_ASSIGNED_NO_ROLE % profile.name())

    can_resign = canUserResignRoleForOrg(
      data.url_connection.parent_key(), data.url_connection.organization.key())
    if can_resign:
      org_selected_norole_txn()
    else:
      raise gsoc_forms.ValidationError(can_resign.extra())

  def post(self, data, check, mutator):
    """Handle org selection."""
    response = data.POST['role_response']

    if response == connection.MENTOR_ROLE:
      self._handleMentorSelection(data)
    elif response == connection.ORG_ADMIN_ROLE:
      self._handleOrgAdminSelection(data)
    elif response == connection.NO_ROLE:
      self._handleNoRoleSelection(data)

    return data.redirect.dashboard().to()

class ShowConnectionForUserPage(base.GSoCRequestHandler):
  """A page to show a connection for the user."""

  def djangoURLPatterns(self):
    return [
        url(r'connection/user/%s$' % url_patterns.SHOW_CONNECTION, self,
            name=url_names.GSOC_SHOW_USER_CONNECTION)
    ]

  def templatePath(self):
    return 'modules/gsoc/connection/show_connection.html'

  def checkAccess(self, data, check, mutator):
    check.isProgramVisible()
    check.hasProfile()

    check.notOrgAdmin()
    check.canUserAccessConnection()

  def context(self, data, check, mutator):

    response_form = ConnectionResponseForm(choices=connection.USER_RESPONSES)
    message_kwargs = data.kwargs.copy()
    del message_kwargs['organization']

    message_box = {
      'form' : MessageForm(data=data.POST or None),
      'action' : reverse(url_names.GSOC_CONNECTION_MESSAGE,
        kwargs=message_kwargs)
      }

    return {
      'page_name' : 'Viewing Connection',
      'header_name' : data.url_connection.organization.name,
      'connection' : data.url_connection,
      'response_form' : response_form,
      'message_box' : message_box
      }

  def _handleRoleSelection(self, data):

    message = data.program.getProgramMessages().mentor_welcome_msg

    @db.transactional(xg=True)
    def user_selected_role_txn():
      connection_entity = db.get(data.url_connection.key())
      connection_entity.user_role = connection.ROLE
      connection_entity.put()

      profile = db.get(data.profile.key())

      promoted = False
      if connection_entity.orgOfferedMentorRole():
        promoted = not profile.is_mentor
        profile_logic.assignMentorRoleForOrg(profile,
             data.url_connection.organization.key())
        # Generate a message on the connection to indicate the new role.
        connection_logic.createConnectionMessage(
            connection_entity, USER_ASSIGNED_MENTOR % profile.name())
      elif connection_entity.orgOfferedOrgAdminRole():
        promoted = not profile.is_mentor
        profile_logic.assignOrgAdminRoleForOrg(
            profile, data.url_connection.organization.key())
        # Generate a message on the connection to indicate the new role.
        connection_logic.createConnectionMessage(
            connection_entity, USER_ASSIGNED_ORG_ADMIN % profile.name())

      if promoted:
        connection_view.sendMentorWelcomeMail(data, profile, message)

    user_selected_role_txn()

  def _handleNoRoleSelection(self, data):
    @db.transactional(xg=True)
    def user_selected_norole_txn():
      connection_entity = db.get(data.url_connection.key())
      connection_entity.user_role = connection.NO_ROLE
      connection_entity.put()

      profile = db.get(data.profile.key())

      profile_logic.assignNoRoleForOrg(
          profile, data.url_connection.organization.key())
      # Generate a message on the connection to indicate the removed role.
      connection_logic.createConnectionMessage(
          connection_entity, USER_ASSIGNED_NO_ROLE % profile.name())

    can_resign = canUserResignRoleForOrg(
      data.profile.key(), data.url_connection.organization.key())
    if can_resign:
      user_selected_norole_txn()
    else:
      raise gsoc_forms.ValidationError(can_resign.extra())


  def post(self, data, check, mutator):
    """Handle user selection."""
    response = data.POST['role_response']

    if response == connection.ROLE:
      self._handleRoleSelection(data)
    elif response == connection.NO_ROLE:
      self._handleNoRoleSelection(data)

    return data.redirect.dashboard().to()


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
    data.organization = data.url_connection.organization
    mutator.commentVisible(data.organization)

  def createMessageFromForm(self, data):
    """Creates a new message based on the data inserted in the form.

    Args:
      data: a request_data.RequestData object

    Returns:
      A newly created message entity or None.
    """
    message_form = MessageForm(data=data.request.POST)

    if not message_form.is_valid():
      return None

    message_form.cleaned_data['author'] = data.profile

    q = GSoCProfile.all().filter('mentor_for', data.organization)
    q.filter('status', 'active')
    q.filter('notify_public_comments', True)
    to_emails = [i.email for i in q if i.key() != data.profile.key()]

    def create_message_txn():
      message = message_form.create(commit=True, parent=data.url_connection)

      # TODO(drew): add notifications

      return message

    return db.run_in_transaction(create_message_txn)

  def post(self, data, check, mutator):
    message = self.createMessageFromForm(data)
    if message:
      data.redirect.show_connection(data.url_user, data.url_connection)
      return data.redirect.to(validated=True)
    else:
      data.redirect.show_connection(data.url_user, data.url_connection)

      # TODO(nathaniel): calling GET logic from a POST handling path.
      # a bit hacky :-( may be changed when possible
      data.request.method = 'GET'
      request_handler = ShowConnectionForUserPage()
      return request_handler(data.request, *data.args, **data.kwargs)

  def get(self, data, check, mutator):
    raise exception.MethodNotAllowed()
