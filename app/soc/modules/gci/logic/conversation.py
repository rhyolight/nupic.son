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

"""GCIConversationUser logic methods."""

from datetime import timedelta

from soc.modules.gci.models import conversation as gciconversation_model
from soc.modules.gci.models import message as gcimessage_model

from soc.modules.gci.logic import message as gcimessage_logic


def queryForProgramAndUser(program, user):
  """Creates a query for GCIConversationUser entities for the given program and
  user.

  Args:
    program: Key (ndb) of GCIProgram.
    user: Key (ndb) of User.

  Returns:
    An ndb query for GCIConversationUsers for the program and user.
  """
  query = (gciconversation_model.GCIConversationUser.query()
      .filter(gciconversation_model.GCIConversationUser.program == program)
      .filter(gciconversation_model.GCIConversationUser.user == user))

  return query


def queryConversationUserForConversation(conversation):
  """Creates a query for GCIConversationUser entities for a conversation.

  Args:
    conversation: Key (ndb) of GCIConversation.

  Returns:
    An ndb query for GCIConversationUsers for the conversation.
  """
  return gciconversation_model.GCIConversationUser.query(
      gciconversation_model.GCIConversationUser.conversation == conversation)


def queryConversationUserForConversationAndUser(conversation, user):
  """Creates a query for GCIConversationUser entities in a conversation for a
  user.

  Args:
    conversation: Key (ndb) of GCIConversation.
    user: Key (ndb) of User.

  Returns:
    An ndb query for GCIConversationUsers for a conversation and user.
  """
  return queryConversationUserForConversation(conversation).filter(
      gciconversation_model.GCIConversationUser.user == user)


def queryUnreadMessagesForConversationAndUser(conversation, user):
  """Creates a query for unread messages in a conversation for a user.

  Args:
    conversation: Key (ndb) of GCIConversation.
    user: Key (ndb) of User.

  Returns:
    An ndb query for GCIMessages the user has not yet read in the conversation.
    If the user is not part of the conversation, None is returned.
  """
  conversation_user_results = queryConversationUserForConversationAndUser(
      conversation, user).fetch(1)

  if len(conversation_user_results) == 0:
    raise Exception('No GCIConversationUser could be found.')

  conversation_user = conversation_user_results[0]

  date_last_seen = conversation_user.last_message_seen_on

  # The > filter in the query below seemed to still include equivalent
  # datetimes, so incrememting this by a second fixes this.
  date_last_seen += timedelta(seconds=1)

  return (gcimessage_logic.queryForConversation(conversation)
      .filter(gcimessage_model.GCIMessage.sent_on > date_last_seen))


def numUnreadMessagesForConversationAndUser(conversation, user):
  """Calculates the number of unread messages in a conversation for a user.

  Args:
    conversation: Key (ndb) of GCIConversation.
    user: Key (ndb) of User.

  Returns:
    The number of messages the user has not read in the conversation.
    If the user is not involved in the conversation, None is returned.
  """
  query = queryUnreadMessagesForConversationAndUser(conversation, user)
  return None if query is None else query.count()


def markAllReadForConversationAndUser(conversation, user):
  """Marks all messages in a conversation as read for the user.

  Sets the GCIConversationUser's last_message_seen_on to the last message's
  sent_on.

  Args:
    conversation: Key (ndb) of GCIConversation.
    user: Key (ndb) of User.
  """
  conv_user_results = queryConversationUserForConversationAndUser(
      conversation, user).fetch(1)

  if not conv_user_results:
    raise Exception('No GCIConversationUser could be found.')

  conv_user = conv_user_results[0]

  last_message = gcimessage_logic.getLastMessageForConversation(conversation)

  conv_user.last_message_seen_on = last_message.sent_on
  conv_user.put()
