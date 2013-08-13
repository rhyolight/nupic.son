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

from melange.models import connection as connection_model
from melange.request import access
from melange.views import connection as connection_view

from codein.views.helper import urls

from soc.logic import links
from soc.logic.helper import notifications
from soc.modules.gci.views import base
from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.helper import url_patterns as ci_url_patterns
from soc.views.helper import url_patterns


START_CONNECTION_AS_USER_PAGE_NAME = translation.ugettext(
    'Start connection with organization')

START_CONNECTION_MESSAGE_LABEL = translation.ugettext(
    'Message')

START_CONNECTION_AS_USER_FORM_ROLE_LABEL = translation.ugettext(
    'Requested Role')

START_CONNECTION_AS_USER_FORM_MESSAGE_HELP_TEXT = translation.ugettext(
    'Optional message to the organization')

START_CONNECTION_AS_USER_FORM_ROLE_HELP_TEXT = translation.ugettext(
    'Role requested from the organization')

ROLE_CHOICES = [
    (connection_model.MENTOR_ROLE, 'Mentor'),
    (connection_model.ORG_ADMIN_ROLE, 'Organization Admin'),
    ]


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

    # set widget for role field
    self.fields['user_role'].widget = django_forms.fields.Select(
        choices=ROLE_CHOICES)

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

  class Meta:
    model = connection_model.Connection
    fields = ['user_role']


def _formToStartConnectionAsUser(**kwargs):
  """Returns a Django form to start connection as a user.

  Args:
    data: request_data.RequestData object describing the current request.
  """
  form = ConnectionForm(**kwargs)
  form.setLabelForRole(START_CONNECTION_AS_USER_FORM_ROLE_LABEL)
  form.setHelpTextForRole(START_CONNECTION_AS_USER_FORM_ROLE_HELP_TEXT)
  form.setHelpTextForMessage(START_CONNECTION_AS_USER_FORM_MESSAGE_HELP_TEXT)

  return form


class StartConnectionAsUser(base.GCIRequestHandler):
  """View to start connections with organizations as users."""

  access_checker = access.NON_STUDENT_ACCESS_CHECKER

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
  """View manage an existing connection by the user."""

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
    return {}
