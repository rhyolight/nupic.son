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

"""This module contains the UserSettings model."""

from google.appengine.ext import ndb


class UserSettings(ndb.Model):
  """User specific settings and preferences for the site.

  Parent:
    soc.models.user.User
  """
  #: Setting that applies only to developers. If not empty, it specifies
  #: in whose context the site will be displayed. Therefore, developers are
  #: allowed act as if they were logged in with arbitrary accounts.
  view_as = ndb.KeyProperty()
