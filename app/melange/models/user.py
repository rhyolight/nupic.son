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

"""This module contains the user related models."""

from google.appengine.ext import ndb
from google.appengine.ext.ndb import msgprop

from protorpc import messages


class Status(messages.Enum):
  """Class that enumerates possible statuses of users."""
  #: The user is active and may register profiles for programs.
  ACTIVE = 1
  #: The user has been banned by site administrators
  BANNED = 2


class User(ndb.Model):
  """Model that represents a user and associated login credentials,
  the fundamental identity entity.

  Melange users are backed up by Google Accounts which are used to login
  so that no application specific infrastructure, like password management,
  is required.
  """
  #: A Google Account associated with this user entity.
  account = ndb.UserProperty()

  #: Unique and permanent identifier associated with the Google Account. This
  #: should be assigned to the value of User.user_id() where User is the
  #: profile referenced in account field.
  account_id = ndb.StringProperty(required=True)

  #: Field storing the status of the user.
  status = msgprop.EnumProperty(Status, default=Status.ACTIVE)

  @property
  def user_id(self):
    """Unique identifier of the user.

    May be displayed publicly and used as parts of various URLs that are
    specific to this user.
    """
    return self.key.id()
