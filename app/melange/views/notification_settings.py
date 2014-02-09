# Copyright 2014 the Melange authors.
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

"""Module containing the notification related views."""

from django import forms as django_forms
from django import http
from django.utils import translation

from melange.logic import profile as profile_logic
from melange.models import profile as profile_model
from melange.request import access
from melange.request import exception

from soc.modules.gsoc.views import forms as gsoc_forms
from soc.views import base
from soc.views.helper import url_patterns


_NOTIFICATION_SETTINGS_PAGE_NAME = translation.ugettext('Notification settings')

_ORG_CONNECTIONS_HELP_TEXT = translation.ugettext('TODO(daniel): complete')

_USER_CONNECTIONS_HELP_TEXT = translation.ugettext('TODO(daniel): complete')

_ORG_CONNECTIONS_LABEL = translation.ugettext(
    'Notify of organization connections')

_USER_CONNECTIONS_LABEL = translation.ugettext(
    'Notify of user connections')

_NOTIFICATION_SETTINGS_PROPERTIES_FORM_KEYS = [
    'org_connections', 'user_connections']


# TODO(daniel): this form mustn't inherit from GSoC form
class NotificationSettingsForm(gsoc_forms.GSoCModelForm):
  """Django form to show specific fields for notification settings.

  Upon creation the form can be customized so as to accommodate
  actual use cases.
  """

  org_connections = django_forms.BooleanField(
      required=False, label=_ORG_CONNECTIONS_LABEL,
      help_text=_ORG_CONNECTIONS_HELP_TEXT)

  user_connections = django_forms.BooleanField(
      required=False, label=_USER_CONNECTIONS_LABEL,
      help_text=_USER_CONNECTIONS_HELP_TEXT)

  def getNotificationSettingsProperties(self):
    """Returns properties of the notification settings that were submitted
    in this form.

    Returns:
      A dict mapping notification settings properties to the
      corresponding values.
    """
    return self._getPropertiesForFields(
        _NOTIFICATION_SETTINGS_PROPERTIES_FORM_KEYS)


class NotificationSettingsPage(base.RequestHandler):
  """View to start connections with users as organization administrators."""

  access_checker = access.HAS_PROFILE_ACCESS_CHECKER

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
    super(NotificationSettingsPage, self).__init__(
        initializer, linker, renderer, error_handler)
    self.url_pattern_constructor = url_pattern_constructor
    self.url_names = url_names
    self.template_path = template_path

  def djangoURLPatterns(self):
    """See base.RequestHandler.djangoURLPatterns for specification."""
    return [
        self.url_pattern_constructor.construct(
            r'profile/notifications/%s$' % url_patterns.PROGRAM,
            self, name=self.url_names.PROFILE_NOTIFICATION_SETTINGS)
    ]

  def templatePath(self):
    """See base.RequestHandler.templatePath for specification."""
    return self.template_path

  def context(self, data, check, mutator):
    """See base.RequestHandler.context for specification."""
    form_data = data.ndb_profile.notification_settings.to_dict()

    # TODO(daniel): different form should be passed for different types of users
    form = NotificationSettingsForm(data=data.POST or form_data)

    return {
        'page_name': _NOTIFICATION_SETTINGS_PAGE_NAME,
        'forms': [form],
        'error': bool(form.errors)
        }

  def post(self, data, check, mutator):
    """See base.RequestHandler.post for specification."""
    form = NotificationSettingsForm(data=data.POST)
    if form.is_valid():
      properties = form.getNotificationSettingsProperties()
      profile_properties = {
          profile_model.Profile.notification_settings._name:
              profile_logic.createtNotificationSettings(properties)
          }

      result = profile_logic.editProfile(
          data.ndb_profile.key, profile_properties)
      if not result:
        raise exception.BadRequest(message=result.extra)
      else:
        url = self.linker.program(
            data.program, self.url_names.PROFILE_NOTIFICATION_SETTINGS)
      return http.HttpResponseRedirect(url)
    else:
      # TODO(nathaniel): problematic self-call.
      return self.get(data, check, mutator)
