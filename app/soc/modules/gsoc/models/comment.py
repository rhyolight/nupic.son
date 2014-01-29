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

"""This module contains the GSoC Comment Model."""

from google.appengine.ext import db
from google.appengine.ext import ndb

from django.utils import translation

from soc.models import profile

_IS_PRIVATE_HELP_TEXT = (
    'Private comments are visible to organization administrators and '
    'mentors. Non-private comments will also be visible to the student '
    'proposal author.')


class GSoCComment(db.Model):
  """Model of a comment on a work.

  A comment is usually associated with a GSoCProposal, and with a user,
  the author.
  There are two types of comment, public (i.e. visible to the student),
  or private (i.e. visible to programme/club staff). Neither type are
  visible to people who are not connected to the work being commented on.

  Parent:
    soc.modules.gsoc.models.proposal.Proposal
  """
  #: A required many:1 relationship with a comment entity indicating
  #: the user who provided that comment.
  author = db.ReferenceProperty(reference_class=profile.Profile,
      required=True, collection_name="commented")

  #: The rich textual content of this comment
  content = db.TextProperty(verbose_name='')

  #: Indicated if the comment should be visible to the appropriate student
  is_private = db.BooleanProperty(default=True,
      verbose_name=translation.ugettext('Private'))
  is_private.help_text = translation.ugettext(_IS_PRIVATE_HELP_TEXT)

  #: Date when the comment was added
  created = db.DateTimeProperty(auto_now_add=True)

  def getAuthor(self):
    """Returns author of the comment."""
    return ndb.Key.from_old_key(
        GSoCComment.author.get_value_for_datastore(self)).get()
