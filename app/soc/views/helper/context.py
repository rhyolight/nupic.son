# Copyright 2011 the Melange authors.
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

"""Module containing the boiler plate required to construct templates."""

from melange.appengine import system
from soc.logic.helper import xsrfutil
from soc.logic import site
from soc.views.helper.gdata_apis import oauth as oauth_helper


def default(data):
  """Returns a context dictionary with default values set.

  The following values are available:
      app_version: the current version string of the application
      is_local: whether we are running locally
      posted: if this was a post/redirect-after-post request
      xsrf_token: the xstrf_token for this request
      google_api_key: the google api key for this website
      ga_tracking_num: the google tracking number for this website
      ds_write_disabled: if datastore writes are disabled
      css_path: part of the path to the css files to distinguish modules
      gdata_is_logged_in: the string "true" or "false" as appropriate
  """
  app_version = system.getMelangeVersion()

  posted = data.request.POST or 'validated' in data.request.GET

  xsrf_secret_key = site.xsrfSecretKey(data.site)
  xsrf_token = xsrfutil.getGeneratedTokenForCurrentUser(xsrf_secret_key)

  if site.isSecondaryHostname(data):
    google_api_key = data.site.secondary_google_api_key
  else:
    google_api_key = data.site.google_api_key

  css_path = '/'.join([
      'soc', 'content', app_version, 'css', data.css_path])

  gdata_is_logged_in = data.user and oauth_helper.getAccessToken(data.user)

  return {
      'app_version': app_version,
      'is_local': system.isLocal(),
      'posted': posted,
      'xsrf_token': xsrf_token,
      'google_api_key': google_api_key,
      'ga_tracking_num': data.site.ga_tracking_num,
      'ds_write_disabled': data.ds_write_disabled,
      'css_path': css_path,
      'gdata_is_logged_in': str(bool(gdata_is_logged_in)).lower(),
      'site_description': data.site.description,
  }
