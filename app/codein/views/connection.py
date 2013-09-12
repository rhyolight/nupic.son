# Copyright 2013 the Melange authors.
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

"""Module with Code In specific connection views."""

from google.appengine.api import users as gae_users

from django import forms as django_forms
from django import http
from django.utils import translation

from codein.logic import profile as profile_logic
from codein.templates import readonly
from codein.views.helper import urls

from melange.logic import connection as connection_logic
from melange.models import connection as connection_model
from melange.request import access
from melange.request import exception
from melange.views import connection as connection_view

from soc.logic import cleaning
from soc.logic import links
from soc.logic import user as user_logic
from soc.logic.helper import notifications
from soc.models import user as user_model
from soc.modules.gci.views import base
from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.helper import url_patterns as ci_url_patterns
from soc.views.helper import url_patterns


ACTIONS_FORM_NAME = 'actions_form'
MESSAGE_FORM_NAME = 'message_form'

MANAGE_CONNECTION_PAGE_NAME = translation.ugettext(
    'Manage connection')

START_CONNECTION_AS_ORG_PAGE_NAME = translation.ugettext(
    'Start connections with users')

START_CONNECTION_AS_USER_PAGE_NAME = translation.ugettext(
    'Start connection with organization')

START_CONNECTION_MESSAGE_LABEL = translation.ugettext(
    'Message')

CONNECTION_FORM_USERS_HELP_TEXT = translation.ugettext(
    'Comma separated list of usernames')

CONNECTION_FORM_USERS_LABEL = translation.ugettext(
    'Users')

CONNECTION_AS_USER_FORM_MESSAGE_HELP_TEXT = translation.ugettext(
    'Optional message to the organization')

CONNECTION_AS_ORG_FORM_MESSAGE_HELP_TEXT = translation.ugettext(
    'Optional message to users')

MANAGE_CONNECTION_FORM_ORG_ROLE_HELP_TEXT = translation.ugettext(
    'Type of role you designate to the user')

START_CONNECTION_FORM_ORG_ROLE_HELP_TEXT = translation.ugettext(
    'Type of role you designate to the users')

CONNECTION_FORM_USER_ROLE_HELP_TEXT = translation.ugettext(
    'Whether you request role from organization or not')

CONNECTION_FORM_ORG_ROLE_LABEL = translation.ugettext(
    'Role To Assign')

CONNECTION_FORM_USER_ROLE_LABEL = translation.ugettext(
    'Role For Organization')

MESSAGE_FORM_CONTENT_LABEL = translation.ugettext(
    'Send New Message')

ORGANIZATION_ITEM_LABEL = translation.ugettext('Organization')
USER_ITEM_LABEL = translation.ugettext('User')
USER_ROLE_ITEM_LABEL = translation.ugettext('User Requests Role')
ORG_ROLE_ITEM_LABEL = translation.ugettext('Role Granted by Organization')
INITIALIZED_ON_LABEL = translation.ugettext('Initialized On')

USER_ROLE_CHOICES = (
    (connection_model.NO_ROLE, 'No'),
    (connection_model.ROLE, 'Yes'))

ACTUAL_ORG_ROLE_CHOICES = [
    (connection_model.MENTOR_ROLE, 'Mentor'),
    (connection_model.ORG_ADMIN_ROLE, 'Organization Admin'),
    ]

ALL_ORG_ROLE_CHOICES = [
    (connection_model.NO_ROLE, 'No Role'),
    (connection_model.MENTOR_ROLE, 'Mentor'),
    (connection_model.ORG_ADMIN_ROLE, 'Organization Admin'),
    ]


class NoConnectionExistsAccessChecker(access.AccessChecker):
  """AccessChecker that ensures that no connection exists between the user
  and organization which are specified in the URL.
  """

  def checkAccess(self, data, check, mutator):
    """See access.AccessChecker.checkAccess for specification."""
    connection = connection_logic.queryForAncestorAndOrganization(
        data.url_profile, data.url_org).get()
    if connection:
      url = links.Linker().userId(
          data.url_profile, connection.key().id(),
          urls.UrlNames.CONNECTION_MANAGE_AS_USER)
      raise exception.Redirect(url)

NO_CONNECTION_EXISTS_ACCESS_CHECKER = NoConnectionExistsAccessChecker()

  
class ConnectionForm(gci_forms.GCIModelForm):
  """Django form to show specific fields for an organization.

  Upon creation the form can be customized using instance methods so as
  to accommodate actual use cases.
  """

  users = gci_forms.CharField(
      required=True, label=CONNECTION_FORM_USERS_LABEL,
      help_text=CONNECTION_FORM_USERS_HELP_TEXT)
  message = gci_forms.CharField(widget=gci_forms.Textarea(), required=False)
  role = gci_forms.ChoiceField()

  def __init__(self, request_data=None, **kwargs):
    """Initializes a new instance of connection form."""
    super(ConnectionForm, self).__init__(**kwargs)

    self.request_data = request_data

    self.fields['message'].label = START_CONNECTION_MESSAGE_LABEL

    # set widget for user role field
    self.fields['user_role'].widget = django_forms.fields.Select(
        choices=USER_ROLE_CHOICES)
    self.fields['user_role'].label = CONNECTION_FORM_USER_ROLE_LABEL
    self.fields['user_role'].help_text = CONNECTION_FORM_USER_ROLE_HELP_TEXT

  def clean_users(self):
    """Generate lists with the provided link_ids/emails sorted into categories.

    Overrides the default cleaning of the link_ids field to add custom
    validation to the users field.
    """
    identifiers = set([
        token.strip() for token in self.cleaned_data['users'].split(',')])

    emails = []
    users = []
    profiles = []
    error_list = []

    for identifier in identifiers:
      try:
        if '@' in identifier:
          cleaning.cleanEmail(identifier)
          account = gae_users.User(identifier)
          user = user_logic.forAccount(account)
          if not user:
            emails.append(identifier)
          else:
            profile = profile_logic.getProfileForUsername(
                user.url_id, self.request_data.program.key())
            if profile:
              profiles.append(profile)
            else:
              users.append(user)
        else:
          cleaning.cleanLinkID(identifier)
          profile = profile_logic.getProfileForUsername(
              identifier, self.request_data.program.key())
          if profile:
            profiles.append(profile)
          else:
            user = user_model.User.get_by_key_name(identifier)
            if user:
              users.append(user)
            else:
              raise gci_forms.ValidationError(
                  cleaning.USER_DOES_NOT_EXIST_ERROR_MSG % identifier)
      except gci_forms.ValidationError as e:
        error_list.append(e.messages)

    # form is not valid if at least one error occurred
    if error_list:
      raise gci_forms.ValidationError(error_list)

    # TODO(daniel): anonymous connections should be supported
    if users or emails:
      raise gci_forms.ValidationError(
          'Anonymous connections are not supported.')

    return profiles, users, emails

  def setHelpTextForMessage(self, help_text):
    """Sets help text for 'message' field.

    Args:
      help_text: a string containing help text to set.
    """
    self.fields['message'].help_text = help_text

  def setLabelForRole(self, label):
    """Sets label for 'role' field.

    Args:
      label: a string containing the label to set.
    """
    self.fields['user_role'].label = label

  def setHelpTextForRole(self, help_text):
    """Sets help text for 'role' field.

    Args:
      help_text: a string containing help text to set.
    """
    self.fields['user_role'].help_text = help_text

  def removeField(self, key):
    """Removes field with the specified key.

    Args:
      key: a string with a key of a field to remove.
    """
    del self.fields[key]

  class Meta:
    model = connection_model.Connection
    fields = ['user_role']


class MessageForm(gci_forms.GCIModelForm):
  """Django form to submit connection messages."""

  def __init__(self, **kwargs):
    """Initializes a new instance of connection message form."""
    super(MessageForm, self).__init__(**kwargs)
    self.fields['content'].label = MESSAGE_FORM_CONTENT_LABEL

  class Meta:
    model = connection_model.ConnectionMessage
    fields = ['content']

  def clean_content(self):
    field_name = 'content'
    wrapped_clean_html_content = cleaning.clean_html_content(field_name)
    content = wrapped_clean_html_content(self)

    if content:
      return content
    else:
      raise django_forms.ValidationError(
          translation.ugettext('Message content cannot be empty.'),
          code='invalid')


def _formToStartConnectionAsOrg(**kwargs):
  """Returns a Django form to start connection as an organization
  administrator.

  Returns:
    ConnectionForm adjusted to start connection as organization administrator.
  """
  form = ConnectionForm(**kwargs)
  form.removeField('user_role')
  form.fields['role'].label = CONNECTION_FORM_ORG_ROLE_LABEL
  form.fields['role'].help_text = START_CONNECTION_FORM_ORG_ROLE_HELP_TEXT
  form.fields['role'].choices = ACTUAL_ORG_ROLE_CHOICES

  form.setHelpTextForMessage(CONNECTION_AS_ORG_FORM_MESSAGE_HELP_TEXT)
  return form


def _formToStartConnectionAsUser(**kwargs):
  """Returns a Django form to start connection as a user.

  Returns:
    ConnectionForm adjusted to start connection as a user.
  """
  form = ConnectionForm(**kwargs)
  form.removeField('user_role')
  form.removeField('role')
  form.removeField('users')
  form.setHelpTextForMessage(CONNECTION_AS_USER_FORM_MESSAGE_HELP_TEXT)
  return form


def _formToManageConnectionAsUser(**kwargs):
  """Returns a Django form to manage connection as a user.

  Returns:
    ConnectionForm adjusted to manage connection as a user.
  """
  form = ConnectionForm(**kwargs)
  form.removeField('message')
  form.removeField('role')
  form.removeField('users')
  return form


def _formToManageConnectionAsOrg(instance=None, **kwargs):
  """Returns a Django form to manage connection as an organization admin.

  Args:
    instance: connection entity.

  Returns:
    ConnectionForm adjusted to manage connection as an organization admin.
  """
  form = ConnectionForm(instance=instance, **kwargs)
  form.removeField('user_role')
  form.removeField('message')

  form.fields['role'].label = CONNECTION_FORM_ORG_ROLE_LABEL
  form.fields['role'].help_text = MANAGE_CONNECTION_FORM_ORG_ROLE_HELP_TEXT
  form.fields['role'].choices = ALL_ORG_ROLE_CHOICES
  form.fields['role'].initial = instance.org_role

  form.removeField('users')
  return form


def _getValueForUserRoleItem(data):
  """Returns value to be displayed for User Role item of connection summary.

  Args:
    data: request_data.RequestData for the current request.

  Returns:
    a string containing a value for User Role item.
  """
  if data.url_connection.user_role == connection_model.ROLE:
    return 'Yes'
  else:
    return 'No'


START_CONNECTION_AS_USER_ACCESS_CHECKER = access.ConjuctionAccessChecker([
    access.PROGRAM_ACTIVE_ACCESS_CHECKER,
    access.NON_STUDENT_ACCESS_CHECKER,
    NO_CONNECTION_EXISTS_ACCESS_CHECKER])

class StartConnectionAsUser(base.GCIRequestHandler):
  """View to start connections with organizations as users."""

  access_checker = START_CONNECTION_AS_USER_ACCESS_CHECKER

  def djangoURLPatterns(self):
    """See base.GCIRequestHandler.djangoURLPatterns for specification."""
    return [
        ci_url_patterns.url(
            r'connection/start/user/%s$' % url_patterns.USER_ORG,
            self, name=urls.UrlNames.CONNECTION_START_AS_USER)
    ]

  def templatePath(self):
    """See base.GCIRequestHandler.templatePath for specification."""
    return 'modules/gci/form_base.html'

  def context(self, data, check, mutator):
    """See base.GCIRequestHandler.context for specification."""
    return {
        'page_name': START_CONNECTION_AS_USER_PAGE_NAME,
        'organization': data.organization.link_id,
        'forms': [_formToStartConnectionAsUser()]
        }

  def post(self, data, check, mutator):
    """See base.GCIRequestHandler.post for specification."""
    form = _formToStartConnectionAsUser(data=data.POST)
    if form.is_valid():
      # TODO(daniel): get actual recipients of notification email
      connection = connection_view.createConnectionTxn(
          data, data.url_profile, data.organization,
          form.cleaned_data['message'],
          notifications.userConnectionContext, [],
          user_role=connection_model.ROLE)

      url = links.Linker().userId(
          data.url_profile, connection.key().id(),
          urls.UrlNames.CONNECTION_MANAGE_AS_USER)
      return http.HttpResponseRedirect(url)

    else:
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)


class StartConnectionAsOrg(base.GCIRequestHandler):
  """View to start connections with users as organization administrators."""

  # TODO(daniel): add actual access checker
  access_checker = access.ALL_ALLOWED_ACCESS_CHECKER

  def djangoURLPatterns(self):
    """See base.GCIRequestHandler.djangoURLPatterns for specification."""
    return [
        ci_url_patterns.url(
            r'connection/start/org/%s$' % url_patterns.ORG,
            self, name=urls.UrlNames.CONNECTION_START_AS_ORG)
    ]

  def templatePath(self):
    """See base.GCIRequestHandler.templatePath for specification."""
    return 'codein/connection/start_connection_as_org.html'

  def context(self, data, check, mutator):
    """See base.GCIRequestHandler.context for specification."""
    form = _formToStartConnectionAsOrg(
        data=data.POST or None, request_data=data)

    return {
        'page_name': START_CONNECTION_AS_ORG_PAGE_NAME,
        'forms': [form],
        'error': bool(form.errors)
        }

  def post(self, data, check, mutator):
    """See base.GCIRequestHandler.post for specification."""
    form = _formToStartConnectionAsOrg(data=data.POST, request_data=data)
    if form.is_valid():
      profiles, _, _ = form.cleaned_data['users']

      connections = []
      for profile in profiles:
        # TODO(daniel): get actual recipients of notification email
        connections.append(connection_view.createConnectionTxn(
            data=data, profile=profile, organization=data.organization,
            org_role=form.cleaned_data['role'],
            message=form.cleaned_data['message'],
            context=notifications.userConnectionContext,
            recipients=[]))

      # TODO(daniel): add some message with whom connections are started
      url = links.Linker().organization(
          data.organization, urls.UrlNames.CONNECTION_START_AS_ORG)
      return http.HttpResponseRedirect(url)
    else:
      # TODO(nathaniel): problematic self-call.
      return self.get(data, check, mutator)


class ManageConnectionAsUser(base.GCIRequestHandler):
  """View to manage an existing connection by the user."""

  # TODO(daniel): add actual access checker
  access_checker = access.ALL_ALLOWED_ACCESS_CHECKER

  def djangoURLPatterns(self):
    """See base.GCIRequestHandler.djangoURLPatterns for specification."""
    return [
        ci_url_patterns.url(
            r'connection/manage/user/%s$' % url_patterns.USER_ID,
            self, name=urls.UrlNames.CONNECTION_MANAGE_AS_USER)
    ]

  def templatePath(self):
    """See base.GCIRequestHandler.templatePath for specification."""
    return 'codein/connection/manage_connection_as_user.html'

  def context(self, data, check, mutator):
    """See base.GCIRequestHandler.context for specification."""
    actions_form = _formToManageConnectionAsUser(
        data=data.POST or None, instance=data.url_connection,
        name=ACTIONS_FORM_NAME)
    message_form = MessageForm(data=data.POST or None, name=MESSAGE_FORM_NAME)

    summary = readonly.ReadOnlyTemplate(data)
    summary.addItem(
        ORGANIZATION_ITEM_LABEL, data.url_connection.organization.name)
    summary.addItem(USER_ITEM_LABEL, data.url_profile.name())
    summary.addItem(USER_ROLE_ITEM_LABEL, _getValueForUserRoleItem(data))
    summary.addItem(INITIALIZED_ON_LABEL, data.url_connection.created_on)

    messages = connection_logic.getConnectionMessages(data.url_connection)

    return {
        'page_name': MANAGE_CONNECTION_PAGE_NAME,
        'actions_form': actions_form,
        'message_form': message_form,
        'summary': summary,
        'messages': messages,
        }

  def post(self, data, check, mutator):
    """See base.GCIRequestHandler.post for specification."""

    handler = self._dispatchPostData(data)

    return handler.handle(data, check, mutator)

  def _dispatchPostData(self, data):
    """Picks form handler that is capable of handling the data that was sent
    in the the current request.

    Args:
      data: request_data.RequestData for the current request.

    Returns:
      FormHandler implementation to handler the received data.
    """
    if ACTIONS_FORM_NAME in data.POST:
      # TODO(daniel): eliminate passing self object.
      return UserActionsFormHandler(self)
    elif MESSAGE_FORM_NAME in data.POST:
      # TODO(daniel): eliminate passing self object.
      return MessageFormHandler(self)
    else:
      raise exception.BadRequest('No valid form data is found in POST.')


class ManageConnectionAsOrg(base.GCIRequestHandler):
  """View to manage an existing connection by the organization."""

  # TODO(daniel): add actual access checker
  access_checker = access.ALL_ALLOWED_ACCESS_CHECKER

  def djangoURLPatterns(self):
    """See base.GCIRequestHandler.djangoURLPatterns for specification."""
    return [
        ci_url_patterns.url(
            r'connection/manage/org/%s$' % url_patterns.USER_ID,
            self, name=urls.UrlNames.CONNECTION_MANAGE_AS_ORG)
    ]

  def templatePath(self):
    """See base.GCIRequestHandler.templatePath for specification."""
    return 'codein/connection/manage_connection_as_user.html'

  def context(self, data, check, mutator):
    """See base.GCIRequestHandler.context for specification."""
    actions_form = _formToManageConnectionAsOrg(
        data=data.POST or None, instance=data.url_connection,
        name=ACTIONS_FORM_NAME)
    message_form = MessageForm(data=data.POST or None, name=MESSAGE_FORM_NAME)

    summary = readonly.ReadOnlyTemplate(data)
    summary.addItem(
        ORGANIZATION_ITEM_LABEL, data.url_connection.organization.name)
    summary.addItem(USER_ITEM_LABEL, data.url_profile.name())
    summary.addItem(USER_ROLE_ITEM_LABEL, _getValueForUserRoleItem(data))
    summary.addItem(INITIALIZED_ON_LABEL, data.url_connection.created_on)

    messages = connection_logic.getConnectionMessages(data.url_connection)

    return {
        'page_name': MANAGE_CONNECTION_PAGE_NAME,
        'actions_form': actions_form,
        'message_form': message_form,
        'summary': summary,
        'messages': messages,
        }

  def post(self, data, check, mutator):
    """See base.GCIRequestHandler.post for specification."""
    handler = self._dispatchPostData(data)
    return handler.handle(data, check, mutator)

  def _dispatchPostData(self, data):
    """Picks form handler that is capable of handling the data that was sent
    in the the current request.

    Args:
      data: request_data.RequestData for the current request.

    Returns:
      FormHandler implementation to handler the received data.
    """
    if ACTIONS_FORM_NAME in data.POST:
      # TODO(daniel): implement
      return exception.BadRequest('TODO(daniel): not implemented yet.')
    elif MESSAGE_FORM_NAME in data.POST:
      # TODO(daniel): eliminate passing self object.
      return MessageFormHandler(self)
    else:
      raise exception.BadRequest('No valid form data is found in POST.')


class FormHandler(object):
  """Simplified version of request handler that is able to take care of
  the received data.
  """

  def __init__(self, view):
    """Initializes new instance of form handler.

    Args:
      view: callback to implementation of base.RequestHandler
        that creates this object.
    """
    self._view = view

  def handle(self, data, check, mutator):
    """Handles the data that was received in the current request and returns
    an appropriate HTTP response.

    Args:
      data: A soc.views.helper.request_data.RequestData.
      check: A soc.views.helper.access_checker.AccessChecker.
      mutator: A soc.views.helper.access_checker.Mutator.

    Returns:
      An http.HttpResponse appropriate for the given request parameters.
    """
    raise NotImplementedError


class MessageFormHandler(FormHandler):
  """Form handler implementation to handle incoming data that is supposed to
  create a new connection message.
  """

  def handle(self, data, check, mutator):
    """Creates and persists a new connection message based on the data
    that was sent in the current request.

    See FormHandler.handle for specification.
    """
    message_form = MessageForm(data=data.request.POST)
    if message_form.is_valid():
      content = message_form.cleaned_data['content']
      connection_view.createConnectionMessageTxn(
          data.url_connection.key(), data.url_profile.key(), content)

      url = links.Linker().userId(
          data.url_profile, data.url_connection.key().id(),
          urls.UrlNames.CONNECTION_MANAGE_AS_USER)
      return http.HttpResponseRedirect(url)
    else:
      # TODO(nathaniel): problematic self-use.
      return self._view.get(data, check, mutator)


class UserActionsFormHandler(FormHandler):
  """Form handler implementation to handle incoming data that is supposed to
  take an action on the existing connection.
  """

  def handle(self, data, check, mutator):
    """Takes an action on the connection based on the data that was sent
    in the current request.

    See FormHandler.handle for specification.
    """
    actions_form = _formToManageConnectionAsUser(data=data.POST)
    if actions_form.is_valid():
      user_role = actions_form.cleaned_data['user_role']
      if user_role == connection_model.NO_ROLE:
        self._handleNoRoleSelection(data)
      else:
        self._handleRoleSelection(data)

      url = links.Linker().userId(
          data.url_profile, data.url_connection.key().id(),
          urls.UrlNames.CONNECTION_MANAGE_AS_USER)
      return http.HttpResponseRedirect(url)
    else:
      # TODO(nathaniel): problematic self-use.
      return self._view.get(data, check, mutator)

  def _handleNoRoleSelection(self, data):
    """Makes all necessary changes if user selects connection_model.NO_ROLE.

    Args:
      data: A soc.views.helper.request_data.RequestData.
    """
    org_key = connection_model.Connection.organization.get_value_for_datastore(
        data.url_connection)
    is_eligible = profile_logic.isNoRoleEligibleForOrg(
        data.url_profile, org_key)
    if is_eligible:
      connection_view.handleUserNoRoleSelectionTxn(data.url_connection)

    # TODO(daniel): if the user is not eligible, some information should be
    # displayed to them

  def _handleRoleSelection(self, data):
    """Makes all necessary changes if user selects connection_model.ROLE.

    Args:
      data: A soc.views.helper.request_data.RequestData.
    """
    org_key = connection_model.Connection.organization.get_value_for_datastore(
        data.url_connection)
    if data.url_connection.orgOfferedMentorRole():
      is_eligible = profile_logic.isMentorRoleEligibleForOrg(
          data.url_profile, org_key)
    else:
      is_eligible = True

    if is_eligible:
      # TODO(daniel): eliminate these calls by removing data from 
      # the call below. without these now XG transactions may be needed
      data.program
      data.site
      connection_view.handleUserRoleSelectionTxn(data, data.url_connection)

    # TODO(daniel): if the user is not eligible, some information should be
    # displayed to them
