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

from django import forms as django_forms
from django import http
from django.utils import translation

from melange.logic import connection as connection_logic
from melange.models import connection as connection_model
from melange.request import access
from melange.request import exception
from melange.views import connection as connection_view

from codein.templates import readonly
from codein.views.helper import urls

from soc.logic import cleaning
from soc.logic import links
from soc.logic.helper import notifications
from soc.modules.gci.views import base
from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.helper import url_patterns as ci_url_patterns
from soc.views.helper import url_patterns


ACTIONS_FORM_NAME = 'actions_form'
MESSAGE_FORM_NAME = 'message_form'

MANAGE_CONNECTION_AS_USER_PAGE_NAME = translation.ugettext(
    'Manage connection')

START_CONNECTION_AS_USER_PAGE_NAME = translation.ugettext(
    'Start connection with organization')

START_CONNECTION_MESSAGE_LABEL = translation.ugettext(
    'Message')

CONNECTION_AS_USER_FORM_MESSAGE_HELP_TEXT = translation.ugettext(
    'Optional message to the organization')

CONNECTION_FORM_USER_ROLE_HELP_TEXT = translation.ugettext(
    'Whether you request role from organization or not')

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

ROLE_CHOICES = [
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

  message = gci_forms.CharField(widget=gci_forms.Textarea(), required=False)

  def __init__(self, **kwargs):
    """Initializes a new instance of connection form."""
    super(ConnectionForm, self).__init__(**kwargs)

    self.fields['message'].label = START_CONNECTION_MESSAGE_LABEL

    # set widget for user role field
    self.fields['user_role'].widget = django_forms.fields.Select(
        choices=USER_ROLE_CHOICES)
    self.fields['user_role'].label = CONNECTION_FORM_USER_ROLE_LABEL
    self.fields['user_role'].help_text = CONNECTION_FORM_USER_ROLE_HELP_TEXT

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


def _formToStartConnectionAsUser(**kwargs):
  """Returns a Django form to start connection as a user.

  Returns:
    ConnectionForm adjusted to start connection as a user.
  """
  form = ConnectionForm(**kwargs)
  form.removeField('user_role')
  form.setHelpTextForMessage(CONNECTION_AS_USER_FORM_MESSAGE_HELP_TEXT)
  return form


def _formToManageConnectionAsUser(**kwargs):
  """Returns a Django form to manage connection as a user.

  Returns:
    ConnectionForm adjusted to manage connection as a user.
  """
  form = ConnectionForm(**kwargs)
  form.removeField('message')
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
        'page_name': MANAGE_CONNECTION_AS_USER_PAGE_NAME,
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
      return ActionsFormHandler(self)
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


class ActionsFormHandler(FormHandler):
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
        self._handleNoRoleSelection()
      else:
        self._handleRoleSelection()

      url = links.Linker().userId(
          data.url_profile, data.url_connection.key().id(),
          urls.UrlNames.CONNECTION_MANAGE_AS_USER)
      return http.HttpResponseRedirect(url)
    else:
      # TODO(nathaniel): problematic self-use.
      return self._view.get(data, check, mutator)

  def _handleNoRoleSelection(self):
    """Makes all necessary changes if user selects connection_model.NO_ROLE."""
    # TODO(daniel): implement this function
    pass

  def _handleRoleSelection(self):
    """Makes all necessary changes if user selects connection_model.ROLE."""
    # TODO(daniel): implement this function
    pass
