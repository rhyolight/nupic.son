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

"""This module contains the ConnectionMessage model."""


from google.appengine.ext import db

from django.utils.translation import ugettext

import soc.models.profile


class ConnectionMessage(db.Model):
  """Model of a message that may be sent along with or in response to
  connections.

  Parent:
    soc.models.connection.Connection
  """

  #: A required many:1 relationship with a comment entity indicating
  #: the user who provided that comment.
  author = db.ReferenceProperty(
      reference_class=soc.models.profile.Profile,
      required=False, collection_name="connection_commented")

  #: The rich textual content of this comment
  content = db.TextProperty(verbose_name=ugettext('Content'))

  #: Date when the comment was added
  created = db.DateTimeProperty(auto_now_add=True)

  #: Whether or not the message was generated programatically
  is_auto_generated = db.BooleanProperty(default=False)

  def getAuthor(self):
    if self.is_auto_generated:
      return "Automatically Generated"
    else:
      return self.author.name()

  def getAuthorId(self):
    if self.is_auto_generated:
      return ""
    else:
      return self.author.link_id