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

from google.appengine.ext import ndb

from django import forms
from django import http

from melange.logic import settings as settings_logic
from melange.request import access
from melange.views.helper import urls

from soc.logic import cleaning

from soc.views import base
from soc.views.helper import url_patterns


class UserSettingsForm(forms.Form):
  """Form to set user settings for the page."""

  view_as = forms.CharField()

  def clean_view_as(self):
    """Cleans view_as field."""
    user = cleaning.clean_existing_user('view_as')(self)
    return ndb.Key.from_old_key(user.key()) if user else None 
     

class UserSettings(base.RequestHandler):
  """View to list and set all user settings for the page."""

  access_checker = access.DEVELOPER_ACCESS_CHECKER

  def djangoURLPatterns(self):
    """See base.RequestHandler.djangoURLPatterns for specification."""
    return [
        url_patterns.url(
            r'site', r'settings/user/%s$' % url_patterns.USER,
            self, name=urls.UrlNames.USER_SETTINGS)
    ]

  def templatePath(self):
    """See base.RequestHandler.templatePath for specification."""
    return 'melange/settings/user_settings.html'

  def context(self, data, check, mutator):
    """See base.RequestHandler.context for specification."""
    user_settings = settings_logic.getUserSettings(data.url_user.key())

    initial = {}
    if user_settings.view_as is not None:
      initial['view_as'] = user_settings.view_as.id()

    return {'form': UserSettingsForm(data=data.POST or None, initial=initial)}

  def post(self, data, check, mutator):
    """See base.RequestHandler.post for specification."""
    form = UserSettingsForm(data=data.POST)
    if form.is_valid():
      view_as = form.cleaned_data['view_as'] or None

      settings_logic.setUserSettings(
          data.url_user.key(), view_as=view_as)

      return http.HttpResponseRedirect(data.request.get_full_path())
    else:
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)
