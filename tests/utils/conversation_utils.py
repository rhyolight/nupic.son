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

from google.appengine.ext import db
from google.appengine.ext import ndb

from soc.models import conversation as conversation_model
from soc.models import message as message_model

from soc.modules.seeder.logic.seeder import logic as seeder_logic

from soc.modules.gci.models import conversation as gciconversation_model
from soc.modules.gci.models import message as gcimessage_model

from tests import program_utils
from tests import profile_utils

# Constants for specifying a profile role in helper functions
ADMIN   = 'Admin'
MENTOR  = 'Mentor'
STUDENT = 'Student'
WINNER  = 'Winner'


class ConversationHelper(object):
  """Helper class to aid in manipulating conversation data."""

  def __init__(self):
    """Initializes the ConversationHelper.

    Args:
      program: Key (ndb) for a program.
    """
    self.program_helper = program_utils.ProgramHelper()
    self.conversation_model_class = conversation_model.Conversation
    self.conversation_user_model_class = conversation_model.ConversationUser
    self.message_model_class = message_model.Message
    self.program_helper.createProgram()
    self.program_key = ndb.Key.from_old_key(self.program_helper.program.key())

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
        program=self.program_key,
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

  def addUser(self, conversation, user, enable_notifications=True):
    """Creates a conversationuser for the given conversation and user.

    Args:
      conversation: Key (ndb) of conversation.
      user: Key (ndb) of user.
      enable_notifications: Whether the user is subscribed to notifications for
                            the conversation.

    Returns:
      The created GCIConversationUser entity.
    """
    conv_user = self.conversation_user_model_class(
        conversation=conversation, user=user,
        enable_notifications=enable_notifications)
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

  def createUser(
      self, roles=None, mentor_organizations=None, admin_organizations=None,
      winning_organization=None, return_key=False, developer=False, email=None):
    """Creates a dummy user with a profile.

    Concrete subclasses must implement this method.

    Args:
      role: A list of role constants for the profile's roles. If None, no roles
            are given.
      mentor_organization: A list of GCIOrganizations the profile is mentoring
                           for. If None, none will be set.
      admin_organizations: A list of GCIOrganizations the profile is admin for.
                           If None, none will be set.
      winning_organization: A GCIConversation the user is a winner for.
      return_key: Whether just an ndb key for the entity will be returned.
      developer: Whether the user is a developer.
      email: The email address for the user's profile.

    Returns:
      If return_key is True, an ndb key for the created user entity is returned.
      Otherwise, the user entity itself is returned.
    """
    raise NotImplementedError()


class GCIConversationHelper(ConversationHelper):
  """Helper class to aid in manipulating GCI conversation data."""

  def __init__(self):
    """Initializes the GCIConversationHelper.

    Args:
      program: Key (ndb) for a program.
    """
    self.program_helper = program_utils.GCIProgramHelper()
    self.conversation_model_class = gciconversation_model.GCIConversation
    self.conversation_user_model_class = (
        gciconversation_model.GCIConversationUser)
    self.message_model_class = gcimessage_model.GCIMessage
    self.program_helper.createProgram()
    self.program_key = ndb.Key.from_old_key(self.program_helper.program.key())

  def createUser(
      self, roles=None, mentor_organizations=None, admin_organizations=None,
      winning_organization=None, return_key=False, developer=False, email=None):
    """Creates a dummy user with a GCIProfile.

    See ConversationHelper.createUser for full specification.
    """

    program_ent = db.get(ndb.Key.to_old_key(self.program_key))
    profile_helper = profile_utils.GCIProfileHelper(program_ent, False)

    roles = set(roles) if roles else set()
    profile = profile_helper.createProfile()
    winner_for = None

    if profile is None:
      raise Exception('profile is none')

    if developer:
      profile.createDeveloper()

    if email:
      profile.email = email

    if mentor_organizations:
      roles.update([MENTOR])
      profile.mentor_for = map(ndb.Key.to_old_key, mentor_organizations)

    if admin_organizations:
      roles.update([ADMIN])
      profile.org_admin_for = map(ndb.Key.to_old_key, admin_organizations)

    if winning_organization:
      roles.update([WINNER])
      winner_for = ndb.Key.to_old_key(winning_organization)

    profile.is_mentor = MENTOR in roles
    profile.is_org_admin = ADMIN in roles
    profile.is_student = STUDENT in roles

    profile.put()

    if winner_for or WINNER in roles:
      profile_helper.createStudent(
          is_winner=WINNER in roles, winner_for=winner_for)

    if return_key:
      return ndb.Key.from_old_key(profile_helper.user.key())
    else:
      return profile_helper.user
