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

"""Logic for settings."""

from google.appengine.ext import ndb

from melange.models import settings as settings_model


def setUserSettings(user_key, **kwargs):
  """Sets settings for the specified user.

  This function, if run within a transaction, guarantees that there is at most
  one settings_model.UserSettings entity per user.

  Args:
    user_key: User key.
    kwargs: Initial values for the instance's properties, as keyword arguments.

  Returns:
    settings_model.UserSettings entity for the specified user.
  """
  user_settings = ndb.Query(
      kind=settings_model.UserSettings._get_kind(), ancestor=user_key).get()
  if not user_settings:
    user_settings = settings_model.UserSettings(parent=user_key, **kwargs)
  else:
    user_settings.populate(**kwargs)

  user_settings.put()
  return user_settings


def getUserSettings(user_key):
  """Returns settings for the specified user.

  If no settings_model.UserSettings entity exists for the user, a new one
  is created.

  Args:
    user_key: User key.

  Returns:
    settings_model.UserSettings entity for the specified user.
  """
  user_settings = ndb.Query(
      kind=settings_model.UserSettings._get_kind(), ancestor=user_key).get()
  if user_settings:
    return user_settings
  else:
    return ndb.transaction(lambda: setUserSettings(user_key))
