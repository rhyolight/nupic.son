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

"""Utils for manipulating conversation data."""

from datetime import datetime

from soc.models import conversation as conversation_model
from soc.models import message as message_model

from soc.modules.seeder.logic.seeder import logic as seeder_logic

from soc.modules.gci.models import conversation as gciconversation_model
from soc.modules.gci.models import message as gcimessage_model


class ConversationHelper(object):
  """Helper class to aid in manipulating conversation data."""

  def __init__(self, program):
    """Initializes the ConversationHelper.

    Args:
      program: Key (ndb) for a program.
    """
    self.program = program
    self.conversation_model_class = conversation_model.Conversation
    self.conversation_user_model_class = conversation_model.ConversationUser
    self.message_model_class = message_model.Message

  def createConversation(
      self, subject, content=None, creator=None, time=None, users=None):
    """Creates a conversation. If content is provided, an initial message will
    be created.

    Args:
      subject: Subject of conversation.
      creator: Key (ndb) of user who created it. Creator can be None if
               message is created by Melange.
      content: If not None, an initial message will be created with this
               content.
      time: Datetime for the conversation and initial message. Defaults to the
            current time.
      users: List of keys (ndb) of users to add to the conversation. The
             creator is added automatically if creator is specified.

    Returns:
      The created GCIConversation entity.
    """
    if time is None:
      time = datetime.utcnow()

    if users is None:
      users = []

    if creator not in users and creator is not None:
      users.append(creator)

    conversation = self.conversation_model_class(
        program=self.program,
        subject=subject,
        creator=creator,
        recipients_type=conversation_model.USER,
        )
    conversation.put()

    # Add users to conversation
    for user in users:
      self.addUser(conversation=conversation.key, user=user)

    # Add initial message
    if content is not None:
      self.addMessage(
          conversation=conversation.key, user=creator, content=content,
          time=time)

    return conversation

  def addUser(self, conversation, user):
    """Creates a conversationuser for the given conversation and user.

    Args:
      conversation: Key (ndb) of conversation.
      user: Key (ndb) of user.

    Returns:
      The created GCIConversationUser entity.
    """
    conv_user = self.conversation_user_model_class(
        conversation=conversation, user=user)
    conv_user.put()

    return conv_user

  def addMessage(
      self, conversation, user=None, content='', time=None):
    """Creates a new message for the conversation and updates related
    models as needed, such as the last_message_sent_on time.

    Args:
      conversation: Key (ndb) of conversation.
      user: Key (ndb) of user sending the message.
      content: Content of the message.
      time: Datetime for the message. Defaults to the current time.

    Returns:
      The created GCIMessage entity.
    """
    if time is None:
      time = datetime.utcnow()
    
    message = self.message_model_class(
        conversation=conversation, author=user, content=content, sent_on=time)
    message.put()

    # Update conversation last_message_on time
    conversation_ent = conversation.get()
    conversation_ent.last_message_on = message.sent_on
    conversation_ent.put()

    # Update conversationuser last_message_on properties by re-putting each
    # entity
    conv_user_query = self.conversation_user_model_class.query(
        self.conversation_user_model_class.conversation == conversation)
    conv_user_query.map(lambda cu: cu.put())

    return message

  def setUserLastSeenTime(self, conversation, user, time):
    """Updates a particular conversationuser's last_message_seen_on time.

    Args:
      conversation: Key (ndb) of conversation.
      user: Key (ndb) of user in conversation.
      time: Datetime for the message.
    """
    conv_users = self.conversation_user_model_class.query(
        self.conversation_user_model_class.conversation == conversation,
        self.conversation_user_model_class.user == user).fetch(1)

    if len(conv_users) == 0:
      raise Exception('User is not in conversation.')

    conv_user = conv_users[0]
    conv_user.last_message_seen_on = time
    conv_user.put()


class GCIConversationHelper(ConversationHelper):
  """Helper class to aid in manipulating GCI conversation data."""

  def __init__(self, program):
    """Initializes the GCIConversationHelper.

    Args:
      program: Key (ndb) for a program.
    """
    self.program = program
    self.conversation_model_class = gciconversation_model.GCIConversation
    self.conversation_user_model_class = (
        gciconversation_model.GCIConversationUser)
    self.message_model_class = gcimessage_model.GCIMessage
