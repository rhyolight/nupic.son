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

"""Module for displaying the Profile read-only page."""

from google.appengine.ext import db

from django import http

from melange.request import access
from soc.models.user import User
from soc.views import readonly_template
from soc.views.helper import url_patterns
from soc.views.helper.access_checker import isSet
from soc.views.template import Template
from soc.views.toggle_button import ToggleButtonTemplate


class UserReadOnlyTemplate(readonly_template.ModelReadOnlyTemplate):
  """Template to construct readonly Profile data.
  """

  class Meta:
    model = User
    css_prefix = 'gsoc_profile_show'
    fields = ['link_id', 'account']

  def __init__(self, *args, **kwargs):
    super(UserReadOnlyTemplate, self).__init__(*args, **kwargs)
    self.fields['link_id'].group = "1. User info"
    self.fields['account'].group = "1. User info"


class HostActions(Template):
  """Template to render the left side host actions.
  """

  def __init__(self, data):
    super(HostActions, self).__init__(data)
    self.toggle_buttons = []

  def context(self):
    assert isSet(self.data.url_user)
    assert isSet(self.data.url_profile)

    # TODO(nathaniel): Eliminate this state-setting call.
    self.data.redirect.profile()

    is_banned = self.data.url_profile.status == 'invalid'

    profile_banned = ToggleButtonTemplate(
        self.data, 'on_off', 'Banned', 'user-banned',
        self.data.redirect.urlOf(self._getActionURLName()),
        checked=is_banned,
        help_text=self._getHelpText(),
        labels={
            'checked': 'Yes',
            'unchecked': 'No'})
    self.toggle_buttons.append(profile_banned)

    context = {
        'title': 'Host Actions',
        'toggle_buttons': self.toggle_buttons,
        }

    return context

  def templatePath(self):
    return "soc/_user_action.html"

  def _getActionURLName(self):
    raise NotImplementedError

  def _getHelpText(self):
    raise NotImplementedError


class BanProfilePost(object):
  """Handles banning/unbanning of profiles."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
         url_patterns.url(
             self._getModulePrefix(),
             r'profile/ban/%s$' % self._getURLPattern(),
             self, name=self._getURLName()),
    ]

  def post(self, data, check, mutator):
    """See soc.views.base.RequestHandler.post for specification."""
    value = data.POST.get('value')
    profile_key = data.url_profile.key()

    def banProfileTxn(value):
      profile_model = self._getProfileModel()
      profile = profile_model.get(profile_key)
      if value == 'unchecked' and profile.status == 'active':
        profile.status = 'invalid'
        profile.put()
      elif value == 'checked' and profile.status == 'invalid':
        profile.status = 'active'
        profile.put()

    db.run_in_transaction(banProfileTxn, value)

    return http.HttpResponse()

  def _getModulePrefix(self):
    raise NotImplementedError

  def _getURLPattern(self):
    raise NotImplementedError

  def _getURLName(self):
    raise NotImplementedError

  def _getProfileModel(self):
    raise NotImplementedError


class ProfileShowPage(object):
  """View to display the read-only profile page."""

  def checkAccess(self, data, check, mutator):
    """See soc.views.base.RequestHandler.checkAccess for specification."""
    check.isLoggedIn()
    check.hasProfile()

  def context(self, data, check, mutator):
    """See soc.views.base.RequestHandler.context for specification."""
    assert isSet(data.program)
    assert isSet(data.user)

    profile = self._getProfile(data)
    program = data.program

    user_template = self._getUserReadOnlyTemplate(data.user)
    profile_template = self._getProfileReadOnlyTemplate(profile)
    css_prefix = profile_template.Meta.css_prefix

    return {
        'page_name': '%s Profile - %s' % (program.short_name, profile.name()),
        'program_name': program.name,
        'user': user_template,
        'profile': profile_template,
        'css_prefix': css_prefix,
        'tabs': self._getTabs(data)
        }

  def _getUserReadOnlyTemplate(self, user):
    """Returns read-only template to display user data.

    This method should be implemented by concrete subclasses.

    Returns:
      Template instance to be used to display user data.
    """
    raise NotImplementedError

  def _getProfileReadOnlyTemplate(self, profile):
    """Returns read-only template to display profile data.

    This method should be implemented by concrete subclasses.

    Returns:
      Template instance to be used to display user data.
    """
    raise NotImplementedError

  def _getTabs(self, data):
    """Returns navigational tabs for the page.

    Args:
      data: A RequestData describing the current request.

    Returns:
      Tabs to be placed on the page, or None if they are not defined.
    """
    return None

  def _getProfile(self, data):
    """Returns the profile entity whose information should be displayed.

    Some subclasses of this class like profile pages that admin have access
    to use request_data.url_profile instead of request_data.profile. So the
    subclasses should be able to use the profile entity that it needs
    depending on the view it is rendering. So this method provides the
    required abstraction which can be overridden in the subclasses.

    Args:
      data: A RequestData describing the current request.

    Returns:
      The profile entity whose information should be displayed.
    """
    assert isSet(data.profile)
    return data.profile
