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

"""Module with connection related views."""

import collections

from django import forms as django_forms
from django import http
from django.utils import translation

from google.appengine.ext import db
from google.appengine.ext import ndb

from melange.logic import connection as connection_logic
from melange.logic import profile as profile_logic
from melange.models import connection as connection_model
from melange.models import organization as org_model
from melange.models import user as user_model
from melange.request import access
from melange.request import exception
from melange.request import links
from melange.templates import connection_list
from melange.utils import lists as melange_lists
from melange.utils import rich_bool
from melange.views.helper import form_handler

from soc.logic import cleaning
from soc.logic.helper import notifications
from soc.tasks import mailer
from soc.modules.gsoc.views import forms as gsoc_forms
from soc.views import base
from soc.views import template
from soc.views.helper import lists
from soc.views.helper import url_patterns

# TODO(daniel): do not import GSoC specific things in this module
from soc.modules.gsoc.logic import profile as soc_profile_logic


ACTIONS_FORM_NAME = 'actions_form'
MESSAGE_FORM_NAME = 'message_form'

LIST_CONNECTIONS_FOR_USER_PAGE_NAME = translation.ugettext(
    'List of connections for %s')

LIST_CONNECTIONS_FOR_ORG_ADMIN_PAGE_NAME = translation.ugettext(
    'List connections for organization admin')

MANAGE_CONNECTION_PAGE_NAME = translation.ugettext(
    'Manage connection')

PICK_ORGANIZATION_TO_CONNECT_PAGE_NAME = translation.ugettext(
    'Pick organization to connect with')

PICK_ORGANIZATION_TO_CONNECT_LIST_DESCRIPTION = translation.ugettext(
    'Pick organization to connect with')

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

MESSAGE_CONNECTION_CANNOT_BE_ACCESSED = translation.ugettext(
    'Requested connection cannot by accessed by this user.')

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


def cleanUsers(tokens, program_key):
  """Cleans users field.

  Args:
    tokens: A string containing user tokens.

  Returns:
    Cleaned value for users field. It is a tuple with three elements:
    list of found profile entities, list of found user entities and list
    of email addresses.

  Raises:
    django_forms.ValidationError if the submitted value is not valid.
  """
  identifiers = set(token.strip() for token in tokens.split(','))

  emails = []
  users = []
  profiles = []
  error_list = []

  for identifier in identifiers:
    try:
      if '@' in identifier:
        cleaning.cleanEmail(identifier)
        emails.append(identifier)
      else:
        cleaning.cleanLinkID(identifier)
        profile = profile_logic.getProfileForUsername(identifier, program_key)
        if profile:
          profiles.append(profile)
        else:
          user = user_model.User.get_by_id(identifier)
          if user:
            users.append(user)
          else:
            raise django_forms.ValidationError(
                cleaning.USER_DOES_NOT_EXIST_ERROR_MSG % identifier)
    except django_forms.ValidationError as e:
      error_list.append(e.messages)

  # form is not valid if at least one error occurred
  if error_list:
    raise django_forms.ValidationError(error_list)

  # TODO(daniel): anonymous connections should be supported
  if users or emails:
    raise django_forms.ValidationError(
        'Anonymous connections are not supported at this time. '
        'Please provide usernames of users with profiles only.')

  return profiles, users, emails


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


def _getValueForOrgRoleItem(data):
  """Returns value to be displayed for Organization Role item of connection
  summary

  Args:
    data: request_data.RequestData for the current request.

  Returns:
    a string containing a value for Organization Role item.
  """
  if data.url_connection.org_role == connection_model.NO_ROLE:
    return translation.ugettext('No role')
  elif data.url_connection.org_role == connection_model.MENTOR_ROLE:
    return translation.ugettext('Mentor')
  else:
    return translation.ugettext('Organization Administrator')


def _formToStartConnectionAsOrg(**kwargs):
  """Returns a Django form to start connection as an organization
  administrator.

  Returns:
    ConnectionForm adjusted to start connection as organization administrator.
  """
  form = ConnectionForm(**kwargs)
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
  form.removeField('users')

  form.fields['role'].widget = django_forms.Select(
      choices=USER_ROLE_CHOICES)
  form.fields['role'].label = CONNECTION_FORM_USER_ROLE_LABEL
  form.fields['role'].help_text = CONNECTION_FORM_USER_ROLE_HELP_TEXT

  return form


def _formToManageConnectionAsOrg(**kwargs):
  """Returns a Django form to manage connection as an organization admin.

  Returns:
    ConnectionForm adjusted to manage connection as an organization admin.
  """
  form = ConnectionForm(**kwargs)
  form.removeField('message')
  form.removeField('users')

  form.fields['role'].widget = django_forms.Select(
      choices=ALL_ORG_ROLE_CHOICES)
  form.fields['role'].label = CONNECTION_FORM_ORG_ROLE_LABEL
  form.fields['role'].help_text = MANAGE_CONNECTION_FORM_ORG_ROLE_HELP_TEXT

  return form


# TODO(daniel): this form mustn't inherit from GSoC form
class ConnectionForm(gsoc_forms.GSoCModelForm):
  """Django form to show specific fields for an organization.

  Upon creation the form can be customized using instance methods so as
  to accommodate actual use cases.
  """

  users = django_forms.CharField(
      required=True, label=CONNECTION_FORM_USERS_LABEL,
      help_text=CONNECTION_FORM_USERS_HELP_TEXT)

  message = django_forms.CharField(
      widget=django_forms.Textarea(), required=False)

  role = django_forms.CharField()

  Meta = object

  def __init__(self, request_data=None, **kwargs):
    """Initializes a new instance of connection form."""
    super(ConnectionForm, self).__init__(**kwargs)

    self.request_data = request_data

    self.fields['message'].label = START_CONNECTION_MESSAGE_LABEL

  def clean_users(self):
    """Cleans users field.

    Returns:
      Cleaned value for users field. It is a tuple with three elements:
      list of found profile entities, list of found user entities and list
      of email addresses.

    Raises:
      django_forms.ValidationError if the submitted value is not valid.
    """
    return cleanUsers(
        self.cleaned_data['users'], self.request_data.program.key())

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


# TODO(daniel): this form mustn't inherit from GSoC form
class MessageForm(gsoc_forms.GSoCModelForm):
  """Django form to submit connection messages."""

  content = django_forms.CharField(
      widget=django_forms.Textarea(), required=True)

  Meta = object

  def __init__(self, **kwargs):
    """Initializes a new instance of connection message form."""
    super(MessageForm, self).__init__(**kwargs)
    self.fields['content'].label = MESSAGE_FORM_CONTENT_LABEL

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


START_CONNECTION_AS_ORG_ACCESS_CHECKER = access.ConjuctionAccessChecker([
    access.PROGRAM_ACTIVE_ACCESS_CHECKER,
    access.IS_USER_ORG_ADMIN_FOR_NDB_ORG,
    access.UrlOrgStatusAccessChecker([org_model.Status.ACCEPTED]),
    ])

class StartConnectionAsOrg(base.RequestHandler):
  """View to start connections with users as organization administrators."""

  access_checker = START_CONNECTION_AS_ORG_ACCESS_CHECKER

  def __init__(self, initializer, linker, renderer, error_handler,
      url_pattern_constructor, url_names, template_path):
    """Initializes a new instance of the request handler for the specified
    parameters.

    Args:
      initializer: Implementation of initialize.Initializer interface.
      linker: Instance of links.Linker class.
      renderer: Implementation of render.Renderer interface.
      error_handler: Implementation of error.ErrorHandler interface.
      url_pattern_constructor:
        Implementation of url_patterns.UrlPatternConstructor.
      url_names: Instance of url_names.UrlNames.
      template_path: The path of the template to be used.
    """
    super(StartConnectionAsOrg, self).__init__(
        initializer, linker, renderer, error_handler)
    self.url_pattern_constructor = url_pattern_constructor
    self.url_names = url_names
    self.template_path = template_path

  def djangoURLPatterns(self):
    """See base.RequestHandler.djangoURLPatterns for specification."""
    return [
        self.url_pattern_constructor.construct(
            r'connection/start/org/%s$' % url_patterns.ORG,
            self, name=self.url_names.CONNECTION_START_AS_ORG)
    ]

  def templatePath(self):
    """See base.RequestHandler.templatePath for specification."""
    return self.template_path

  def context(self, data, check, mutator):
    """See base.RequestHandler.context for specification."""
    form = _formToStartConnectionAsOrg(
        data=data.POST or None, request_data=data)

    return {
        'page_name': START_CONNECTION_AS_ORG_PAGE_NAME,
        'forms': [form],
        'error': bool(form.errors)
        }

  def post(self, data, check, mutator):
    """See base.RequestHandler.post for specification."""
    form = _formToStartConnectionAsOrg(data=data.POST, request_data=data)
    if form.is_valid():
      profiles, _, _ = form.cleaned_data['users']

      notification_context_provider = (
          notifications.StartConnectionByOrgContextProvider(
              links.ABSOLUTE_LINKER, self.url_names))
      connections = []
      for profile in profiles:
        connections.append(createConnectionTxn(
            data, profile.key, data.url_ndb_org, None,
            message=form.cleaned_data['message'],
            notification_context_provider=notification_context_provider,
            recipients=[profile.contact.email],
            org_role=form.cleaned_data['role'],
            org_admin=data.ndb_profile))

      # TODO(daniel): add some message with whom connections are started
      url = self.linker.organization(
          data.url_ndb_org.key, self.url_names.CONNECTION_START_AS_ORG)
      return http.HttpResponseRedirect(url)
    else:
      # TODO(nathaniel): problematic self-call.
      return self.get(data, check, mutator)


class NoConnectionExistsAccessChecker(access.AccessChecker):
  """AccessChecker that ensures that no connection exists between the user,
  who is currently logged-in, and organization which is specified in the URL.
  """

  def __init__(self, url_names):
    """Initializes a new instance of this access checker for the specified
    parameters.

    Args:
      url_names: Instance of url_names.UrlNames.
    """
    self.url_names = url_names

  def checkAccess(self, data, check):
    """See access.AccessChecker.checkAccess for specification."""
    connection = connection_logic.connectionForProfileAndOrganization(
        data.ndb_profile.key, data.url_ndb_org.key)
    if connection:
      url = links.LINKER.userId(
          data.ndb_profile.key, connection.key.id(),
          self.url_names.CONNECTION_MANAGE_AS_USER)
      raise exception.Redirect(url)


class StartConnectionAsUser(base.RequestHandler):
  """View to start connections with organizations as users."""

  def __init__(self, initializer, linker, renderer, error_handler,
      url_pattern_constructor, url_names, template_path, access_checker):
    """Initializes a new instance of the request handler for the specified
    parameters.

    Args:
      initializer: Implementation of initialize.Initializer interface.
      linker: Instance of links.Linker class.
      renderer: Implementation of render.Renderer interface.
      error_handler: Implementation of error.ErrorHandler interface.
      url_pattern_constructor:
        Implementation of url_patterns.UrlPatternConstructor.
      url_names: Instance of url_names.UrlNames.
      template_path: The path of the template to be used.
      access_checker: Implementation of access.AccessChecker interface.
    """
    super(StartConnectionAsUser, self).__init__(
        initializer, linker, renderer, error_handler)
    self.url_pattern_constructor = url_pattern_constructor
    self.url_names = url_names
    self.template_path = template_path
    self.access_checker = access_checker

  def djangoURLPatterns(self):
    """See base.RequestHandler.djangoURLPatterns for specification."""
    return [
        self.url_pattern_constructor.construct(
            r'connection/start/user/%s$' % url_patterns.ORG,
            self, name=self.url_names.CONNECTION_START_AS_USER)
    ]

  def templatePath(self):
    """See base.RequestHandler.templatePath for specification."""
    return self.template_path

  def context(self, data, check, mutator):
    """See base.RequestHandler.context for specification."""
    return {
        'page_name': START_CONNECTION_AS_USER_PAGE_NAME,
        'organization': data.organization.org_id,
        'forms': [_formToStartConnectionAsUser()]
        }

  def post(self, data, check, mutator):
    """See base.RequestHandler.post for specification."""
    form = _formToStartConnectionAsUser(data=data.POST)
    if form.is_valid():

      # create notification that will be sent to organization administrators
      org_admins = profile_logic.getOrgAdmins(data.url_ndb_org.key)
      emails = [org_admin.contact.email for org_admin in org_admins]

      context_provider = notifications.StartConnectionByUserContextProvider(
          links.ABSOLUTE_LINKER, self.url_names)

      connection = createConnectionTxn(
          data, data.ndb_profile.key, data.url_ndb_org, None,
          message=form.cleaned_data['message'],
          notification_context_provider=context_provider,
          recipients=emails, user_role=connection_model.ROLE)

      url = links.LINKER.userId(
          data.ndb_profile.key, connection.key.id(),
          self.url_names.CONNECTION_MANAGE_AS_USER)
      return http.HttpResponseRedirect(url)

    else:
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)


class UrlConnectionIsForCurrentUserAccessChecker(access.AccessChecker):
  """AccessChecker that ensures that connection which is retrieved from URL
  data belongs to the user who is currently logged in.
  """

  def checkAccess(self, data, check):
    """See AccessChecker.checkAccess for specification."""
    if (not data.ndb_profile or
        data.url_connection.key.parent() != data.ndb_profile.key):
      raise exception.Forbidden(message=MESSAGE_CONNECTION_CANNOT_BE_ACCESSED)


MANAGE_CONNECTION_AS_USER_ACCESS_CHECKER = access.ConjuctionAccessChecker([
    access.PROGRAM_ACTIVE_ACCESS_CHECKER,
    UrlConnectionIsForCurrentUserAccessChecker(),
    ])

class ManageConnectionAsUser(base.RequestHandler):
  """View to manage an existing connection by the user."""

  access_checker = MANAGE_CONNECTION_AS_USER_ACCESS_CHECKER

  def __init__(self, initializer, linker, renderer, error_handler,
      url_pattern_constructor, url_names, template_path):
    """Initializes a new instance of the request handler for the specified
    parameters.

    Args:
      initializer: Implementation of initialize.Initializer interface.
      linker: Instance of links.Linker class.
      renderer: Implementation of render.Renderer interface.
      error_handler: Implementation of error.ErrorHandler interface.
      url_pattern_constructor:
        Implementation of url_patterns.UrlPatternConstructor.
      url_names: Instance of url_names.UrlNames.
      template_path: The path of the template to be used.
    """
    super(ManageConnectionAsUser, self).__init__(
        initializer, linker, renderer, error_handler)
    self.url_pattern_constructor = url_pattern_constructor
    self.url_names = url_names
    self.template_path = template_path

  def djangoURLPatterns(self):
    """See base.GCIRequestHandler.djangoURLPatterns for specification."""
    return [
        self.url_pattern_constructor.construct(
            r'connection/manage/user/%s$' % url_patterns.USER_ID,
            self, name=self.url_names.CONNECTION_MANAGE_AS_USER)
    ]

  def templatePath(self):
    """See base.GCIRequestHandler.templatePath for specification."""
    return self.template_path

  def context(self, data, check, mutator):
    """See base.GCIRequestHandler.context for specification."""
    form_data = {'role': data.url_connection.user_role}
    actions_form = _formToManageConnectionAsUser(
        data=data.POST or form_data, name=ACTIONS_FORM_NAME)
    message_form = MessageForm(data=data.POST or None, name=MESSAGE_FORM_NAME)

    summary_items = collections.OrderedDict()
    summary_items[USER_ITEM_LABEL] = data.url_ndb_profile.public_name
    summary_items[ORGANIZATION_ITEM_LABEL] = (
        data.url_connection.organization.get().name)
    summary_items[USER_ROLE_ITEM_LABEL] = _getValueForUserRoleItem(data)
    summary_items[ORG_ROLE_ITEM_LABEL] = _getValueForOrgRoleItem(data)
    summary_items[INITIALIZED_ON_LABEL] = data.url_connection.created_on

    messages = connection_logic.getConnectionMessages(data.url_connection.key)

    # TODO(daniel): add mark as seen by user
    # mark_as_seen_url = links.LINKER.userId(
    #    data.url_ndb_profile.key, data.url_connection.key.id(),
    #    self.url_names.CONNECTION_MARK_AS_SEEN_BY_USER)

    return {
        'page_name': MANAGE_CONNECTION_PAGE_NAME,
        'actions_form': actions_form,
        'message_form': message_form,
        'items': summary_items,
        'messages': messages,
     #   'mark_as_seen_url': mark_as_seen_url,
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
      url = links.LINKER.userId(
          data.url_ndb_profile.key, data.url_connection.key.id(),
          self.url_names.CONNECTION_MANAGE_AS_USER)
      # TODO(daniel): eliminate passing self object.
      return UserActionsFormHandler(self, url=url)
    elif MESSAGE_FORM_NAME in data.POST:
      # TODO(daniel): eliminate passing self object.
      return MessageFormHandler(
          self, data.url_ndb_profile.key,
          self.url_names.CONNECTION_MANAGE_AS_USER)
    else:
      raise exception.BadRequest('No valid form data is found in POST.')


class IsUserOrgAdminForUrlConnection(access.AccessChecker):
  """AccessChecker that ensures that the logged in user is organization
  administrator for the connection which is retrieved from the URL data.
  """

  def checkAccess(self, data, check):
    """See AccessChecker.checkAccess for specification."""
    if not data.ndb_profile:
      raise exception.Forbidden(message=access._MESSAGE_NO_PROFILE)

    if data.url_connection.organization not in data.ndb_profile.admin_for:
      raise exception.Forbidden(
          message=access._MESSAGE_NOT_ORG_ADMIN_FOR_ORG %
              data.url_connection.organization.id())


MANAGE_CONNECTION_AS_ORG_ACCESS_CHECKER = access.ConjuctionAccessChecker([
    access.PROGRAM_ACTIVE_ACCESS_CHECKER,
    IsUserOrgAdminForUrlConnection()
    ])

class ManageConnectionAsOrg(base.RequestHandler):
  """View to manage an existing connection by the organization."""

  access_checker = MANAGE_CONNECTION_AS_ORG_ACCESS_CHECKER

  def __init__(self, initializer, linker, renderer, error_handler,
      url_pattern_constructor, url_names, template_path):
    """Initializes a new instance of the request handler for the specified
    parameters.

    Args:
      initializer: Implementation of initialize.Initializer interface.
      linker: Instance of links.Linker class.
      renderer: Implementation of render.Renderer interface.
      error_handler: Implementation of error.ErrorHandler interface.
      url_pattern_constructor:
        Implementation of url_patterns.UrlPatternConstructor.
      url_names: Instance of url_names.UrlNames.
      template_path: The path of the template to be used.
    """
    super(ManageConnectionAsOrg, self).__init__(
        initializer, linker, renderer, error_handler)
    self.url_pattern_constructor = url_pattern_constructor
    self.url_names = url_names
    self.template_path = template_path

  def djangoURLPatterns(self):
    """See base.GCIRequestHandler.djangoURLPatterns for specification."""
    return [
        self.url_pattern_constructor.construct(
            r'connection/manage/org/%s$' % url_patterns.USER_ID,
            self, name=self.url_names.CONNECTION_MANAGE_AS_ORG)
    ]

  def templatePath(self):
    """See base.GCIRequestHandler.templatePath for specification."""
    return self.template_path

  def context(self, data, check, mutator):
    """See base.GCIRequestHandler.context for specification."""
    form_data = {'role': data.url_connection.org_role}
    actions_form = _formToManageConnectionAsOrg(
        data=data.POST or form_data, name=ACTIONS_FORM_NAME)
    message_form = MessageForm(data=data.POST or None, name=MESSAGE_FORM_NAME)

    summary_items = collections.OrderedDict()
    summary_items[USER_ITEM_LABEL] = data.url_ndb_profile.public_name
    summary_items[ORGANIZATION_ITEM_LABEL] = (
        data.url_connection.organization.get().name)
    summary_items[USER_ROLE_ITEM_LABEL] = _getValueForUserRoleItem(data)
    summary_items[ORG_ROLE_ITEM_LABEL] = _getValueForOrgRoleItem(data)
    summary_items[INITIALIZED_ON_LABEL] = data.url_connection.created_on

    messages = connection_logic.getConnectionMessages(data.url_connection.key)

    # TODO(daniel): enable mark as seen
    # mark_as_seen_url = links.LINKER.userId(
    #   data.url_profile.key(), data.url_connection.key().id(),
    #   self.url_names.CONNECTION_MARK_AS_SEEN_BY_ORG)

    return {
        'page_name': MANAGE_CONNECTION_PAGE_NAME,
        'actions_form': actions_form,
        'message_form': message_form,
        'items': summary_items,
        'messages': messages,
    #   'mark_as_seen_url': mark_as_seen_url,
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
      url = links.LINKER.userId(
          data.url_ndb_profile.key, data.url_connection.key.id(),
          self.url_names.CONNECTION_MANAGE_AS_ORG)
      # TODO(daniel): eliminate passing self object.
      return OrgActionsFormHandler(self, url=url)
    elif MESSAGE_FORM_NAME in data.POST:
      # TODO(daniel): eliminate passing self object.
      return MessageFormHandler(
          self, data.ndb_profile.key, self.url_names.CONNECTION_MANAGE_AS_ORG)
    else:
      raise exception.BadRequest('No valid form data is found in POST.')


class UserActionsFormHandler(form_handler.FormHandler):
  """Form handler implementation to handle incoming data that is supposed to
  take an action on the existing connection by users.
  """

  def handle(self, data, check, mutator):
    """Takes an action on the connection based on the data that was sent
    in the current request.

    See form_handler.FormHandler.handle for specification.
    """
    actions_form = _formToManageConnectionAsUser(data=data.POST)
    if actions_form.is_valid():
      role = actions_form.cleaned_data['role']
      if role == connection_model.NO_ROLE:
        success = self._handleNoRoleSelection(data)
      else:
        success = self._handleRoleSelection(data)

      if success:
        return http.HttpResponseRedirect(self._url)
      else:
        raise exception.BadRequest(success.extra)

    else:
      # TODO(nathaniel): problematic self-use.
      return self._view.get(data, check, mutator)

  def _handleNoRoleSelection(self, data):
    """Makes all necessary changes if user selects connection_model.NO_ROLE.

    Args:
      data: A soc.views.helper.request_data.RequestData.

    Returns:
      RichBool whose value is set to True, if the selection has been handled
      successfully. Otherwise, RichBool whose value is set to False and extra
      part is a string representation of the reason why the picked selection
      is not possible.
    """
    is_eligible = soc_profile_logic.isNoRoleEligibleForOrg(
        data.url_ndb_profile, data.url_connection.organization)
    if is_eligible:
      handleUserNoRoleSelectionTxn(data.url_connection, None)

    return is_eligible

  def _handleRoleSelection(self, data):
    """Makes all necessary changes if user selects connection_model.ROLE.

    Args:
      data: A soc.views.helper.request_data.RequestData.

    Returns:
      RichBool whose value is set to True, if the selection has been handled
      successfully. Otherwise, RichBool whose value is set to False and extra
      part is a string representation of the reason why the picked selection
      is not possible.
    """
    if data.url_connection.orgOfferedMentorRole():
      is_eligible = profile_logic.isMentorRoleEligibleForOrg(
          data.url_ndb_profile, data.url_connection.organization)
    else:
      is_eligible = True

    if is_eligible:
      # TODO(daniel): eliminate these calls by removing data from
      # the call below. without these now XG transactions may be needed
      data.program  # pylint: disable=pointless-statement
      data.site  # pylint: disable=pointless-statement
      handleUserRoleSelectionTxn(data, data.url_connection, None)

    return is_eligible


class OrgActionsFormHandler(form_handler.FormHandler):
  """Form handler implementation to handle incoming data that is supposed to
  take an action on the existing connection by organization administrators.
  """

  def handle(self, data, check, mutator):
    """Takes an action on the connection based on the data that was sent
    in the current request.

    See form_handler.FormHandler.handle for specification.
    """
    actions_form = _formToManageConnectionAsOrg(data=data.POST)
    if actions_form.is_valid():
      role = actions_form.cleaned_data['role']
      if role == connection_model.NO_ROLE:
        success = self._handleNoRoleSelection(data)
      elif role == connection_model.MENTOR_ROLE:
        success = self._handleMentorSelection(data)
      else:
        success = self._handleOrgAdminSelection(data)

      if success:
        return http.HttpResponseRedirect(self._url)
      else:
        raise exception.BadRequest(success.extra)

    else:
      # TODO(nathaniel): problematic self-use.
      return self._view.get(data, check, mutator)

  def _handleNoRoleSelection(self, data):
    """Makes all necessary changes if an organization administrator
    selects connection_model.NO_ROLE.

    Args:
      data: A soc.views.helper.request_data.RequestData.

    Returns:
      RichBool whose value is set to True, if the selection has been handled
      successfully. Otherwise, RichBool whose value is set to False and extra
      part is a string representation of the reason why the picked selection
      is not possible.
    """
    is_eligible = soc_profile_logic.isNoRoleEligibleForOrg(
        data.url_ndb_profile, data.url_connection.organization)
    if is_eligible:
      handleOrgNoRoleSelection(data.url_connection, data.ndb_profile, None)
    return is_eligible

  def _handleMentorSelection(self, data):
    """Makes all necessary changes if an organization administrator
    selects connection_model.MENTOR_ROLE.

    Args:
      data: A soc.views.helper.request_data.RequestData.

    Returns:
      RichBool whose value is set to True, if the selection has been handled
      successfully. Otherwise, RichBool whose value is set to False and extra
      part is a string representation of the reason why the picked selection
      is not possible.
    """
    is_eligible = profile_logic.isMentorRoleEligibleForOrg(
        data.url_ndb_profile, data.url_connection.organization)
    if is_eligible:
      handleMentorRoleSelection(data.url_connection, data.ndb_profile, None)
    return is_eligible

  def _handleOrgAdminSelection(self, data):
    """Makes all necessary changes if an organization administrator
    selects connection_model.ORG_ADMIN_ROLE.

    Args:
      data: A soc.views.helper.request_data.RequestData.

    Returns:
      RichBool whose value is set to True, if the selection has been handled
      successfully. Otherwise, RichBool whose value is set to False and extra
      part is a string representation of the reason why the picked selection
      is not possible.
    """
    handleOrgAdminRoleSelection(data.url_connection, data.ndb_profile, None)
    return rich_bool.TRUE


class MessageFormHandler(form_handler.FormHandler):
  """Form handler implementation to handle incoming data that is supposed to
  create a new connection message.
  """

  def __init__(self, view, author_key, url_name):
    """Initializes new instance of form handler.

    Args:
      view: callback to implementation of base.RequestHandler
        that creates this object.
      author_key: profile key of the user who is the author of the message.
      url_name: name of the URL that should be used for redirect after
        the request is handled successfully.
    """
    super(MessageFormHandler, self).__init__(view)
    self._author_key = author_key
    self._url_name = url_name

  def handle(self, data, check, mutator):
    """Creates and persists a new connection message based on the data
    that was sent in the current request.

    See form_handler.FormHandler.handle for specification.
    """
    message_form = MessageForm(data=data.request.POST)
    if message_form.is_valid():
      content = message_form.cleaned_data['content']
      createConnectionMessageTxn(
          data.url_connection.key, self._author_key, content)

      url = links.LINKER.userId(
          data.url_ndb_profile.key, data.url_connection.key.id(),
          self._url_name)
      return http.HttpResponseRedirect(url)
    else:
      # TODO(nathaniel): problematic self-use.
      return self._view.get(data, check, mutator)


LIST_CONNECTIONS_FOR_USER_ACCESS_CHECKER = access.ConjuctionAccessChecker([
    access.PROGRAM_ACTIVE_ACCESS_CHECKER,
    access.NON_STUDENT_PROFILE_ACCESS_CHECKER])

class ListConnectionsForUser(base.RequestHandler):
  """View to list all connections for the currently logged in user."""

  access_checker = LIST_CONNECTIONS_FOR_USER_ACCESS_CHECKER

  def __init__(self, initializer, linker, renderer, error_handler,
      url_pattern_constructor, url_names, template_path):
    """Initializes a new instance of the request handler for the specified
    parameters.

    Args:
      initializer: Implementation of initialize.Initializer interface.
      linker: Instance of links.Linker class.
      renderer: Implementation of render.Renderer interface.
      error_handler: Implementation of error.ErrorHandler interface.
      url_pattern_constructor:
        Implementation of url_patterns.UrlPatternConstructor.
      url_names: Instance of url_names.UrlNames.
      template_path: The path of the template to be used.
    """
    super(ListConnectionsForUser, self).__init__(
        initializer, linker, renderer, error_handler)
    self.url_pattern_constructor = url_pattern_constructor
    self.url_names = url_names
    self.template_path = template_path


  def djangoURLPatterns(self):
    """See base.RequestHandler.djangoURLPatterns for specification."""
    return [
        self.url_pattern_constructor.construct(
            r'connection/list/user/%s$' % url_patterns.PROGRAM,
            self, name=self.url_names.CONNECTION_LIST_FOR_USER)
    ]

  def templatePath(self):
    """See base.RequestHandler.templatePath for specification."""
    return self.template_path

  def context(self, data, check, mutator):
    """See base.RequestHandler.context for specification."""
    page_name = (
        LIST_CONNECTIONS_FOR_USER_PAGE_NAME % data.ndb_profile.profile_id)

    return {
        # TODO(daniel): template path should not be hardcoded here.
        'connection_list':
            connection_list.UserConnectionList(
                self.url_names, 'summerofcode/_list_component.html', data),
        'page_name': page_name,
        }

  def jsonContext(self, data, check, mutator):
    """See base.RequestHandler.jsonContext for specification."""
    list_content = connection_list.UserConnectionList(
        self.url_names, self.template_path, data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.BadRequest(message='This data cannot be accessed.')


class PickOrganizationToConnectListRowRedirect(melange_lists.RedirectCustomRow):
  """Class which provides redirects for rows of pick organization to connect
  with list."""

  def __init__(self, data, url_names):
    """Initializes a new instance of the row redirect.

    Args:
      data: request_data.RequestData for the current request.
      url_names: Instance of url_names.UrlNames.
    """
    super(PickOrganizationToConnectListRowRedirect, self).__init__()
    self.data = data
    self.url_names = url_names

  def getLink(self, item):
    """See lists.RedirectCustomRow.getLink for specification."""
    org_key = ndb.Key(
        self.data.models.ndb_org_model._get_kind(), item['columns']['key'])
    return links.LINKER.organization(
        org_key, self.url_names.CONNECTION_START_AS_USER)


# TODO(daniel): replace this class with a new style list
class PickOrganizationToConnectList(template.Template):
  """List of organizations with options to connect with."""

  def __init__(self, data):
    """See template.Template.__init__ for specification."""
    super(PickOrganizationToConnectList, self).__init__(data)
    self._list_config = lists.ListConfiguration()
    self._list_config.addSimpleColumn('org_id', 'Organization ID', hidden=True)
    self._list_config.addPlainTextColumn(
        'name', 'Name', lambda e, *args: e.name.strip())

  def templatePath(self):
    """See template.Template.templatePath for specification."""
    # TODO(daniel): this path should not be hardcoded to gsoc
    return 'modules/gsoc/admin/_accepted_orgs_list.html'

  def context(self):
    """See template.Template.context for specification."""
    description = PICK_ORGANIZATION_TO_CONNECT_LIST_DESCRIPTION

    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, 0, description)

    return {
        'lists': [list_configuration_response],
    }

PICK_ORGANIZATION_TO_CONNECT_ACCESS_CHECKER = (
    access.ConjuctionAccessChecker([
        access.PROGRAM_ACTIVE_ACCESS_CHECKER,
        access.NON_STUDENT_PROFILE_ACCESS_CHECKER]))

class PickOrganizationToConnectPage(base.RequestHandler):
  """Page for non-student users to pick organization to start connection."""

  access_checker = PICK_ORGANIZATION_TO_CONNECT_ACCESS_CHECKER

  def __init__(self, initializer, linker, renderer, error_handler,
      url_pattern_constructor, url_names, template_path):
    """Initializes a new instance of the request handler for the specified
    parameters.

    Args:
      initializer: Implementation of initialize.Initializer interface.
      linker: Instance of links.Linker class.
      renderer: Implementation of render.Renderer interface.
      error_handler: Implementation of error.ErrorHandler interface.
      url_pattern_constructor:
        Implementation of url_patterns.UrlPatternConstructor.
      url_names: Instance of url_names.UrlNames.
      template_path: The path of the template to be used.
    """
    super(PickOrganizationToConnectPage, self).__init__(
        initializer, linker, renderer, error_handler)
    self.url_pattern_constructor = url_pattern_constructor
    self.url_names = url_names
    self.template_path = template_path

  def templatePath(self):
    """See base.RequestHandler.templatePath for specification."""
    return self.template_path

  def djangoURLPatterns(self):
    """See base.RequestHandler.djangoURLPatterns for specification."""
    return [
        self.url_pattern_constructor.construct(
            r'connection/pick/%s$' % url_patterns.PROGRAM,
            self, name=self.url_names.CONNECTION_PICK_ORG),
    ]

  def jsonContext(self, data, check, mutator):
    """See base.RequestHandler.jsonContext for specification."""
    query = data.models.ndb_org_model.query(
        org_model.Organization.program ==
            ndb.Key.from_old_key(data.program.key()),
        org_model.Organization.status == org_model.Status.ACCEPTED)

    response = melange_lists.JqgridResponse(
        melange_lists.ORGANIZATION_LIST_ID,
        row=PickOrganizationToConnectListRowRedirect(data, self.url_names))

    start = data.GET.get('start')

    return response.getData(query, start=start)

  def context(self, data, check, mutator):
    """See base.GCIRequestHandler.context for specification."""
    return {
        'page_name': PICK_ORGANIZATION_TO_CONNECT_PAGE_NAME,
        'accepted_orgs_list': PickOrganizationToConnectList(data),
    }


def sendMentorWelcomeMail(data, profile, message):
  """Send out a welcome email to new mentors.

  Args:
    data: RequestData object for the current request.
    profile: profile entity to which to send emails.
    messages: message to be sent.
  """
  mentor_mail = notifications.getMentorWelcomeMailContext(
      profile, data, message)
  if mentor_mail:
    mailer.getSpawnMailTaskTxn(mentor_mail, parent=profile)()


@ndb.transactional
def createConnectionTxn(
    data, profile_key, organization, conversation_updater, message=None,
    notification_context_provider=None, recipients=None,
    org_role=connection_model.NO_ROLE, user_role=connection_model.NO_ROLE,
    org_admin=None):
  """Creates a new Connection entity, attach any messages provided by the
  initiator and send a notification email to the recipient(s).

  Args:
    data: RequestData object for the current request.
    profile_key: Profile key with which to connect.
    organization: Organization with which to connect.
    conversation_updater: A ConversationUpdater object to be called if the
                          profile's conversations need updating.
    message: User-provided message for the connection.
    context: The notification context method.
    notification_context_provider: A provider to obtain context of the
      notification email.
    recipients: List of one or more recipients for the notification email.
    org_role: Org role for the connection.
    user_role: User role for the connection.
    org_admin: profile entity of organization administrator who started
      the connection. Should be supplied only if the connection was initialized
      by organization.

  Returns:
    The newly created Connection entity.
  """
  profile = profile_key.get()

  can_create = connection_logic.canCreateConnection(profile, organization.key)

  if not can_create:
    raise exception.BadRequest(message=can_create.extra)
  else:
    # create the new connection.
    connection = connection_logic.createConnection(
        profile, organization.key, user_role, org_role)

    # handle possible role assignment
    if connection.getRole() == connection_model.MENTOR_ROLE:
      profile_logic.assignMentorRoleForOrg(profile, organization.key)
    elif connection.getRole() == connection_model.ORG_ADMIN_ROLE:
      profile_logic.assignOrgAdminRoleForOrg(profile, organization.key)

    # auto-generate a message indicated that the connection has been started
    if org_admin:
      # connection has been initialized by organization
      connection_logic.generateMessageOnStartByOrg(connection, org_admin)
    else:
      # connection has been initialized by user
      connection_logic.generateMessageOnStartByUser(connection.key)

    # attach any user-provided messages to the connection.
    if message:
      connection_logic.createConnectionMessage(
          connection.key, message, author_key=profile.key).put()

    # dispatch an email to the users.
    if notification_context_provider and recipients:
      notification_context = notification_context_provider.getContext(
          recipients, organization, profile, data.program, data.site,
          connection.key, message)
      sub_txn = mailer.getSpawnMailTaskTxn(
          notification_context, parent=connection)
      sub_txn()

    # spawn task to update this user's messages
    if conversation_updater:
      conversation_updater.updateConversationsForProfile(profile)

    return connection

@db.transactional
def createAnonymousConnectionTxn(data, organization, org_role, email, message):
  """Create an AnonymousConnection so that an unregistered user can join
  an organization and dispatch an email to the newly Connected user.

  Args:
    data: RequestData for the current request.
    organization: Organization with which to connect.
    org_role: Role offered to the user.
    email: Email address of the user to which to send the notification.
    message: Any message provided by the organization to the user(s).

  Returns:
    Newly created AnonymousConnection entity.
  """
  anonymous_connection = connection_logic.createAnonymousConnection(
      org=organization, org_role=org_role, email=email)

  notification = notifications.anonymousConnectionContext(
      data=data, connection=anonymous_connection, email=email, message=message)
  sub_txn = mailer.getSpawnMailTaskTxn(
      notification, parent=anonymous_connection)
  sub_txn()

  return anonymous_connection

@ndb.transactional
def createConnectionMessageTxn(connection_key, profile_key, content):
  """Creates a new connection message with the specified content
  for the specified connection.

  Args:
    connection_key: connection key.
    profile_key: profile key of a user who is an author of the comment.
    content: a string containing content of the message.

  Returns:
    a newly created ConnectionMessage entity.
  """
  # connection is retrieved and stored in datastore so that its last_modified
  # property is automatically updated by AppEngine
  connection = connection_key.get()

  message = connection_logic.createConnectionMessage(
      connection_key, content, author_key=profile_key)

  ndb.put_multi([connection, message])

  # TODO(daniel): emails should be enqueued
  return message


@ndb.transactional
def handleUserNoRoleSelectionTxn(connection, conversation_updater):
  """Updates user role of the specified connection and all corresponding
  entities with connection_model.NO_ROLE selection.

  Please note that it should be checked if the user is actually allowed to
  have no role for the organization prior to calling this function.

  Args:
    connection: connection entity.
    conversation_updater: A ConversationUpdater object to be called if the
                          profile's conversations need updating.
  """
  connection = connection.key.get()

  if connection.user_role != connection_model.NO_ROLE:
    old_user_role = connection.user_role

    connection.user_role = connection_model.NO_ROLE
    connection = connection_logic._updateSeenByProperties(
        connection, connection_logic.USER_ACTION_ORIGIN)

    message = connection_logic.generateMessageOnUpdateByUser(
        connection, old_user_role)

    ndb.put_multi([connection, message])

    profile = connection.key.parent().get()
    profile_logic.assignNoRoleForOrg(profile, connection.organization)

    if conversation_updater:
      conversation_updater.updateConversationsForProfile(profile)


@ndb.transactional
def handleUserRoleSelectionTxn(data, connection, conversation_updater):
  """Updates user role of the specified connection and all corresponding
  entities with connection_model.ROLE selection.

  Please note that it should be checked if the user is actually allowed to
  have a role for the organization prior to calling this function.

  Args:
    data: RequestData object for the current request.
    connection: connection entity.
    conversation_updater: A ConversationUpdater object to be called if the
                          profile's conversations need updating.
  """
  connection = connection.key.get()

  if connection.user_role != connection_model.ROLE:
    old_user_role = connection.user_role

    connection.user_role = connection_model.ROLE
    connection = connection_logic._updateSeenByProperties(
        connection, connection_logic.USER_ACTION_ORIGIN)

    message = connection_logic.generateMessageOnUpdateByUser(
        connection, old_user_role)

    ndb.put_multi([connection, message])

    profile = connection.key.parent().get()

    if connection.orgOfferedMentorRole():
      send_email = not profile.is_mentor
      profile_logic.assignMentorRoleForOrg(profile, connection.organization)
      # TODO(daniel): generate connection message
    elif connection.orgOfferedOrgAdminRole():
      send_email = not profile.is_mentor
      profile_logic.assignOrgAdminRoleForOrg(profile, connection.organization)
      # TODO(daniel): generate connection message
    else:
      # no role has been offered by organization
      send_email = False

    if send_email:
      message = 'TODO(daniel): supply actual message.'
      sendMentorWelcomeMail(data, profile, message)

    if conversation_updater:
      conversation_updater.updateConversationsForProfile(profile)


@ndb.transactional
def handleOrgNoRoleSelection(connection, org_admin, conversation_updater):
  """Updates organization role of the specified connection and all
  corresponding entities with connection_model.NO_ROLE selection.

  Please note that it should be checked if the user is actually allowed to
  have no role for the organization prior to calling this function.

  Args:
    connection: connection entity.
    org_admin: profile entity of organization administrator who updates
               organization role for the connection.
    conversation_updater: A ConversationUpdater object to be called if the
                          profile's conversations need updating.
  """
  connection = connection.key.get()

  if connection.org_role != connection_model.NO_ROLE:
    old_org_role = connection.org_role

    connection.org_role = connection_model.NO_ROLE
    connection = connection_logic._updateSeenByProperties(
        connection, connection_logic.ORG_ACTION_ORIGIN)

    message = connection_logic.generateMessageOnUpdateByOrg(
        connection, org_admin, old_org_role)

    ndb.put_multi([connection, message])

    profile = connection.key.parent().get()
    profile_logic.assignNoRoleForOrg(profile, connection.organization)

    if conversation_updater:
      conversation_updater.updateConversationsForProfile(profile)

    # TODO(daniel): generate connection message


@ndb.transactional
def handleMentorRoleSelection(connection, admin, conversation_updater):
  """Updates organization role of the specified connection and all
  corresponding entities with connection_model.MENTOR_ROLE selection.

  Please note that it should be checked if the user is actually allowed to
  have no role for the organization prior to calling this function.

  Args:
    connection: Connection entity.
    admin: Profile entity of organization administrator who updates
      organization role for the connection.
    conversation_updater: A ConversationUpdater object to be called if the
      profile's conversations need updating.
  """

  connection = connection.key.get()

  if connection.org_role != connection_model.MENTOR_ROLE:
    old_org_role = connection.org_role

    connection.org_role = connection_model.MENTOR_ROLE
    connection = connection_logic._updateSeenByProperties(
        connection, connection_logic.ORG_ACTION_ORIGIN)

    message = connection_logic.generateMessageOnUpdateByOrg(
        connection, admin, old_org_role)

    ndb.put_multi([connection, message])

    if connection.userRequestedRole():
      profile = connection.key.parent().get()
      send_email = not profile.is_mentor

      profile_logic.assignMentorRoleForOrg(profile, connection.organization)

      if conversation_updater:
        conversation_updater.updateConversationsForProfile(profile)

      if send_email:
        pass
        # TODO(daniel): send actual welcome email


@ndb.transactional
def handleOrgAdminRoleSelection(connection, admin, conversation_updater):
  """Updates organization role of the specified connection and all
  corresponding entities with connection_model.ORG_ADMIN_ROLE selection.

  Please note that it should be checked if the user is actually allowed to
  have no role for the organization prior to calling this function.

  Args:
    connection: Connection entity.
    admin: Profile entity of organization administrator who updates
      organization role for the connection.
    conversation_updater: A ConversationUpdater object to be called if the
      profile's conversations need updating.
  """
  connection = connection.key.get()

  if connection.org_role != connection_model.ORG_ADMIN_ROLE:
    old_org_role = connection.org_role

    connection.org_role = connection_model.ORG_ADMIN_ROLE
    connection = connection_logic._updateSeenByProperties(
        connection, connection_logic.ORG_ACTION_ORIGIN)

    message = connection_logic.generateMessageOnUpdateByOrg(
        connection, admin, old_org_role)

    ndb.put_multi([connection, message])

    if connection.userRequestedRole():
      profile = connection.key.parent().get()
      send_email = not profile.is_mentor

      profile_logic.assignOrgAdminRoleForOrg(profile, connection.organization)

      if conversation_updater:
        conversation_updater.updateConversationsForProfile(profile)

      if send_email:
        pass
        # TODO(daniel): send actual welcome email


@ndb.transactional
def markConnectionAsSeenByOrg(connection_key):
  """Marks the specified connection as seen by organization.

  Args:
    connection: Connection key.
  """
  connection = connection_key.get()
  connection.seen_by_org = True
  connection.put()


@ndb.transactional
def markConnectionAsSeenByUser(connection_key):
  """Marks the specified connection as seen by organization.

  Args:
    connection: Connection key.
  """
  connection = connection_key.get()
  connection.seen_by_user = True
  connection.put()
