#!/usr/bin/env python2.5
#
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

"""Module containing the boiler plate required to construct templates
"""

__authors__ = [
  '"Sverre Rabbelier" <sverre@rabbelier.nl>',
  ]


import os

from google.appengine.ext import db

from soc.logic import system
from soc.logic.helper import xsrfutil
from soc.logic.models.site import logic as site_logic


def default(data):
  """Returns a context dictionary with default values set.

  The following values are available:
      app_version: the current version string of the application
      is_local: whether we are running locally
      posted: if this was a post/redirect-after-post request
      xsrf_token: the xstrf_token for this request
      google_api_key: the google api key for this website
      ga_tracking_num: the google tracking number for this website
  """
  posted = data.request.POST or 'validated' in data.request.GET

  if data.request.method == 'GET':
    get_status = data.request.GET.get('dsw_disabled', '')

    if not db.WRITE_CAPABILITY.is_enabled() or (get_status.isdigit()
        and int(get_status) == 1):
      ds_write_disabled = True
    else:
      ds_write_disabled = False

  xsrf_secret_key = site_logic.getXsrfSecretKey(data.site)
  xsrf_token = xsrfutil.getGeneratedTokenForCurrentUser(xsrf_secret_key)

  if system.isSecondaryHostname(data.request):
    google_api_key = data.site.secondary_google_api_key
  else:
    google_api_key = data.site.google_api_key

  return {
      'app_version': system.getMelangeVersion(),
      'is_local': system.isLocal(),
      'posted': posted,
      'xsrf_token': xsrf_token,
      'google_api_key': google_api_key,
      'ga_tracking_num': data.site.ga_tracking_num,
      'ds_write_disabled': ds_write_disabled,
  }
