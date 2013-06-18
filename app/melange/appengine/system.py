# Copyright 2008 the Melange authors.
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

"""App Engine platform information functions."""

import os
import settings

from google.appengine.api import app_identity


def getApplicationId():
  """Returns the current application id."""
  return app_identity.get_application_id()


def getApplicationEmail(name):
  """Returns the applications email address.

  Args:
    name: the before-the-@ component.
  """
  app_id = getApplicationId()
  assert app_id

  return "%s@%s.appspotmail.com" % (name, app_id)


def getApplicationNoReplyEmail():
  """Returns the applications no-reply email address."""
  return getApplicationEmail('no-reply')


def getRawHostname():
  """Returns the actual hostname."""
  return os.environ.get('HTTP_HOST', '')


def getSecureHostname():
  """Returns the hostname suitable for https requests."""
  return "%s.appspot.com" % getApplicationId()


def getAppVersion():
  """Returns the Google App Engine "version" of the running instance."""
  return os.environ.get('CURRENT_VERSION_ID')


def getMelangeVersion():
  """Returns the Melange part of the GAE version."""
  return getAppVersion().split('.', 1)[0]


def isLocal():
  """Returns True if Melange application is running locally.

  "Local mode" is currently determined from settings.DEBUG but may become
  more sophisticated in the future.
  """
  return settings.DEBUG


def isDebug():
  """Returns True if Melange application is running in "debug mode".

  "Debug mode" is currently enabled if running locally or if the
  current Melange version is 'devvin'.
  """
  return isLocal() or getMelangeVersion() == 'devvin'