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

"""Module containing the Conversation model."""

from google.appengine.ext import ndb

from datetime import datetime

from django.utils import translation

#: Constants for specifiying the type of recipients
PROGRAM       = 'Program'       #: Types of users within the program
ORGANIZATION  = 'Organization'  #: Types of users within the specified org
USER          = 'User'          #: Specific users, specified manually


class Conversation(ndb.Model):
  """Model of a conversation: a thread of messages."""

  #: Subject of the conversation
  subject = ndb.TextProperty(required=True,
                             verbose_name=translation.ugettext('Subject'))

  #: User who created the conversation.
  #: Optional; If None, conversation was created by Melange.
  creator = ndb.KeyProperty(required=False)

  #: When the conversation was created
  created_on = ndb.DateTimeProperty(required=True, auto_now_add=True)

  #: When the last message was added
  last_message_on = ndb.DateTimeProperty(
      default=datetime.min,
      verbose_name=translation.ugettext('Last Message'))

  #: What type of recipients
  recipients_type = ndb.StringProperty(required=True,
                                       choices=[PROGRAM, ORGANIZATION, USER])

  #: Program under which the conversation exists.
  #: If recipient type is 'Program', this is also the scope of recipients.
  program = ndb.KeyProperty(required=True,
                            verbose_name=translation.ugettext('Program'))

  #: Organization to limit to if recipients type is organization.
  #: Ignored if recipient type is not 'Organization'.
  organization = ndb.KeyProperty(
      required=False,
      verbose_name=translation.ugettext('Organization'))

  #: Include admins as recipients if recipients type is program,
  #: or organization admins as recipients if recipients type is organization.
  #: Ignored if recipient type is not 'Program' or 'Organization'.
  include_admins = ndb.BooleanProperty(required=False)

  #: Include mentors as recipients if recipients type is program,
  #: or organization mentors as recipients if recipients type is organization.
  #: Ignored if recipient type is not 'Program' or 'Organization'.
  include_mentors = ndb.BooleanProperty(required=False)

  #: Include students as recipients if recipients type is program.
  #: Ignored if recipient type is not 'Program'.
  include_students = ndb.BooleanProperty(required=False)

  #: Whether users will be automatically added/removed if they start/stop
  #: matching the criteria defined above. Ignored if recipients type is 'User'.
  auto_update_users = ndb.BooleanProperty(
      default=True,
      verbose_name=translation.ugettext('Automatically Update Users'))
  auto_update_users.help_text = translation.ugettext(
      'If set, users will be automatically added and removed from the '
      'conversation if they start to or no longer fit the criteria.')


class ConversationUser(ndb.Model):
  """Model representing a user's involvement in a conversation.

  An instance of this model is created for every user in every conversation.

  In addition to being a record of a user's involvement in a conversation, it
  stores the time of the last message seen by the user, and it also store's the
  user's preferences for this conversation.

  Parent:
    soc.models.conversation.Conversation
  """

  #: Conversation the preferences apply to
  conversation = ndb.KeyProperty(kind=Conversation, required=True)

  #: User the preferences are for
  user = ndb.KeyProperty(required=True)

  #: Conversation's Program, to aid with querying
  program = ndb.ComputedProperty(lambda self: self.conversation.get().program)

  #: Conversation's last_message_on, to aid with querying
  last_message_on = ndb.ComputedProperty(
      lambda self: self.conversation.get().last_message_on)

  #: Time of the last message seen by this user in this conversation
  last_message_seen_on = ndb.DateTimeProperty(default=datetime.min)

  #: Preference for receiving email notifications for new messages
  enable_notifications = ndb.BooleanProperty(
      default=True,
      verbose_name=translation.ugettext('Get Email Notifications'))
  enable_notifications.help_test = translation.ugettext(
      'If set, you will receive email notifications about new '
      'messages in this conversation.')
