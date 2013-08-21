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
from melange.models import connection_message as connection_message_model
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

  def __init__(self, *args, **kwargs):
    """Initializes a new instance of connection message form."""
    super(MessageForm, self).__init__(*args, **kwargs)
    self.fields['content'].label = MESSAGE_FORM_CONTENT_LABEL

  class Meta:
    model = connection_message_model.ConnectionMessage
    fields = ['content']

  def clean_content(self):
    field_name = 'content'
    wrapped_clean_html_content = cleaning.clean_html_content(field_name)
    content = wrapped_clean_html_content(self)

    if content:
      return content
    else:
      raise django_forms.ValidationError(
          translation.ugettext('Message content cannot be empty.'), code='invalid')


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

      url = links.Linker().userOrg(
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
        data=data.POST or None, instance=data.url_connection)
    message_form = MessageForm()

    summary = readonly.ReadOnlyTemplate(data)
    summary.addItem(
        ORGANIZATION_ITEM_LABEL, data.url_connection.organization.name)
    summary.addItem(USER_ITEM_LABEL, data.url_profile.name())
    summary.addItem(USER_ROLE_ITEM_LABEL, _getValueForUserRoleItem(data))
    summary.addItem(INITIALIZED_ON_LABEL, data.url_connection.created_on)

    return {
        'page_name': MANAGE_CONNECTION_AS_USER_PAGE_NAME,
        'actions_form': actions_form,
        'message_form': message_form,
        'summary': summary
        }
