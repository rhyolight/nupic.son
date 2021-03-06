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

from google.appengine.ext import db
from google.appengine.ext import ndb

from melange.logic import profile as profile_logic
from melange.models import profile as profile_model

from soc.tasks import mailer

from soc.modules.gci.logic import message as gcimessage_logic
from soc.modules.gci.logic.helper import notifications
from soc.modules.gci.models import conversation as gciconversation_model
from soc.modules.gci.models import message as gcimessage_model

from soc.models import conversation as conversation_model


def queryForProgramAndCreator(program, creator):
  """Creates a query for GCIConversation entities for the given program and
  creator.

  Args:
    program: Key (ndb) of GCIProgram.
    creator: Key (ndb) of User who created the conversation.

  Returns:
    An ndb query for GCIConversations for the program and creator.
  """
  query = (gciconversation_model.GCIConversation.query()
      .filter(gciconversation_model.GCIConversation.program == program)
      .filter(gciconversation_model.GCIConversation.creator == creator))

  return query


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


def queryConversationsForProgram(program):
  """Creates a query for GCIConversation entities for the given program.

  Args:
    program: Key (ndb) of GCIProgram.

  Returns:
    An ndb query for GCIConversations for the program.
  """
  return gciconversation_model.GCIConversation.query(
      gciconversation_model.GCIConversation.program == program)


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
  conversation_user = queryConversationUserForConversationAndUser(
      conversation, user).get()

  if not conversation_user:
    return None

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
    If the user is not involved in the conversation, 0 is returned.
  """
  query = queryUnreadMessagesForConversationAndUser(conversation, user)
  return 0 if query is None else query.count()


#TODO(drewgottlieb) use mapreduce for this
def numUnreadMessagesForProgramAndUser(program, user):
  """Returns the number of unread messages for all conversations the user is in
  for a program.

  Args:
    program: Key (ndb) of GCIProgram.
    user: Key (ndb) of User.
  """
  conv_users = queryForProgramAndUser(program, user).fetch(1000)

  unread_count = 0

  for conv_user in conv_users:
    unread_count += numUnreadMessagesForConversationAndUser(
        conv_user.conversation, user)

  return unread_count


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


def reputConversationUsers(conversation):
  """Updates all computed properties in each GCIConversationUser entity for
  a conversation.

  Args:
    conversation: Key (ndb) of GCIConversation.
  """
  @ndb.tasklet
  def reput(conv_user):
    conv_user.put()

  queryConversationUserForConversation(conversation).map(reput)


def createMessage(conversation, user=None, content=''):
  """Creates and returns a new GCIMessage, and updates conversation and
  conversationusers' last_message_sent_on date.

  Args:
    conversation: Key (ndb) of GCIConversation.
    user: Key (ndb) of user who sent the message. Can be None if conversation
          is created by Melange itself.
    content: Content of message. This function will not sanitize it for you.

  Returns:
    The created GCIMessage.
  """
  if content is None: return None

  @ndb.transactional
  def create():
    message = gcimessage_model.GCIMessage(
        parent=conversation,
        conversation=conversation,
        content=content,
        author=user)
    message.put()

    # Update last_message_sent_on in conversation
    conversation_ent = conversation.get()
    conversation_ent.last_message_on = message.sent_on
    conversation_ent.put()

    return message

  message = create()

  # Reput each conversationuser for the conversation to update computed
  # properties such as last_message_sent_on
  reputConversationUsers(conversation)

  return message


def addUserToConversation(conversation, user):
  """Creates a GCIConversationUser adding the user to the conversation, if the
  user is not already part of the conversation.

  Args:
    conversation: Key (ndb) of GCIConversation.
    user: Key (ndb) of User.

  Returns:
    The created (or existing) GCIConversationUser entity representing the
    user's involvement.
  """
  @ndb.transactional
  def txn():
    query = gciconversation_model.GCIConversationUser.query(
        gciconversation_model.GCIConversationUser.user == user,
        gciconversation_model.GCIConversationUser.conversation == conversation,
        ancestor=conversation)
    conv_user = query.get()

    if conv_user:
      return conv_user

    conv_user = gciconversation_model.GCIConversationUser(
        parent=conversation, conversation=conversation, user=user)
    conv_user.put()

    return conv_user

  return txn()


def removeUserFromConversation(conversation, user):
  """Removes the GCIConversationUser for a user and conversation, if it exists.
  Will remove all matching instances, even though there should never be more
  then one.

  Args:
    conversation: Key (ndb) of GCIConversation.
    user: Key (ndb) of User.
  """
  keys = queryConversationUserForConversationAndUser(
      conversation=conversation, user=user).fetch(100, keys_only=True)
  ndb.delete_multi(keys)


def doesConversationUserBelong(
    conversation_user, ignore_auto_update_users=True):
  """Decides whether the user in a conversation belongs in the conversation.

  If ignore_auto_update_users is False, True will be returned if the
  conversation's auto_update_users is False.

  Args:
    conversation_user: Key (ndb) of a GCIConversationUser representing the
                       user's involvement in the conversation.
    ignore_auto_update_users: Whether this should ignore the conversation's
                              auto_update_users property.

  Returns:
    Whether the user belongs in the conversation. If the conversation's
    recipients_type is 'User', True is always returned. Also returns true if
    the user is the conversation's creator.
  """

  conversation_user_ent = conversation_user.get()

  return doesUserBelongInConversation(
      user=conversation_user_ent.user,
      conversation=conversation_user_ent.conversation,
      ignore_auto_update_users=ignore_auto_update_users)

def doesUserBelongInConversation(
    user, conversation, ignore_auto_update_users=True):
  """Decides whether the user in a conversation belongs in the conversation.

  If ignore_auto_update_users is False, True will be returned if the
  conversation's auto_update_users is False.

  Args:
    user: Key (ndb) of a User.
    conversation: Key (ndb) of a GCIConversation.
    ignore_auto_update_users: Whether this should ignore the conversation's
                              auto_update_users property.

  Returns:
    Whether the user belongs in the conversation. If the conversation's
    recipients_type is 'User', True is always returned. Also returns true if
    the user is the conversation's creator.
  """
  conversation_ent = conversation.get()

  if not conversation_ent.auto_update_users and not ignore_auto_update_users:
    return True

  if conversation_ent.creator == user:
    return True

  profile = profile_logic.getProfileForUsername(
      user.id(), conversation_ent.program.to_old_key())

  if not profile:
    raise Exception('Could not find GCIProfile for user and program.')

  if conversation_ent.recipients_type == conversation_model.PROGRAM:
    if conversation_ent.include_admins and profile.is_admin:
      return True
    elif conversation_ent.include_mentors and profile.is_mentor:
      return True
    elif conversation_ent.include_students and profile.is_student:
      return True
    elif (profile.is_student and conversation_ent.include_winners
        and profile.student_data.is_winner):
      return True
    else:
      return False
  elif conversation_ent.recipients_type == conversation_model.ORGANIZATION:
    if (conversation_ent.include_admins and
        conversation_ent.organization in profile.admin_for):
      return True
    elif (conversation_ent.include_mentors and
        conversation_ent.organization in profile.mentor_for):
      return True
    elif (profile.is_student and conversation_ent.include_winners
        and profile.student_data.is_winner and
        conversation_ent.organization == profile.student_data.winner_for):
      return True
    else:
      return False

  # This might be reached if conversation recipients_type is 'User'
  return True


def refreshConversationParticipants(conversation):
  """Creates/deletes GCIConversationUser entities depending on the converation's
  criteria.

  The conversation's owner is always included in the conversation.
  If the conversation's recipients_type is 'User', this function will not do
  anything because it is expected that the GCIConversationUser will be managed
  elsewhere.

  Args:
    conversation: Key (ndb) of GCIConversation.
  """
  conv = conversation.get()

  def addProfile(profile):
    addUserToConversation(
        conversation=conversation,
        user=profile.key.parent())

  def deleteConvUserIfDoesntBelong(conv_user):
    if not doesConversationUserBelong(conversation_user=conv_user.key):
      conv_user.key.delete()

  # Remove any users included who no longer fit the criteria
  if conv.recipients_type != conversation_model.USER:
    conv_user_query = queryConversationUserForConversation(conversation)
    map(deleteConvUserIfDoesntBelong, conv_user_query)

  # Make sure users who fit the criteria are included
  if conv.recipients_type == conversation_model.PROGRAM:
    if conv.include_admins:
      query = profile_model.Profile.query(
          profile_model.Profile.program == conv.program,
          profile_model.Profile.is_admin == True)
      map(addProfile, query)

    if conv.include_mentors:
      query = profile_logic.queryAllMentorsForProgram(conv.program.to_old_key())
      map(addProfile, query)

    if conv.include_students:
      query = profile_model.Profile.query(
          profile_model.Profile.program == conv.program,
          profile_model.Profile.is_student == True)
      map(addProfile, query)

    if conv.include_winners:
      query = profile_model.Profile.query(
          profile_model.Profile.program == conv.program,
          profile_model.Profile.student_data.is_winner == True)
      map(addProfile, query)

  elif conv.recipients_type == conversation_model.ORGANIZATION:
    if conv.include_admins:
      org_admins = profile_logic.getOrgAdmins(conv.organization)
      map(addProfile, org_admins)

    if conv.include_mentors:
      query = profile_model.Profile.query(
          profile_model.Profile.mentor_for == conv.organization,
          profile_model.Profile.status == profile_model.Status.ACTIVE)
      map(addProfile, query)

    if conv.include_winners:
      query = profile_model.Profile.query(
          profile_model.Profile.student_data.winner_for == conv.organization,
          profile_model.Profile.status == profile_model.Status.ACTIVE)
      map(addProfile, query)

  # Make sure conversation's creator is included
  if conv.creator is not None:
    addUserToConversation(conversation=conversation, user=conv.creator)


def refreshConversationsForUserAndProgram(user_key, program_key):
  """Adds/removes the user to/from conversations that they should be involved in
  based on the conversation's criteria.

  For example, if there is a conversation that should include all program
  mentors, and this user is a program mentor who is involved with the program
  but isn't part of the converation, this function will add the user to that
  conversation. Likewise, it will remove the user from converstions they have no
  business being in, unless they're the creator of the conversation or the
  conversation is for specific users.

  This will only look at conversations that have auto_update_users set as
  True, and whoose, recipients_type is not 'User'.

  This function will not add a user to a conversation if the user does not fit
  the conversation's criteria, even if the user is the creator. If the user is
  _only_ the creator of the conversation, the user's GCIConversationUser entity
  should have been created when the conversation was initially created.

  Args:
    user_key: Key (ndb) of the User.
    program_key: Key (ndb) of the GCIProgram.
  """
  profile = profile_logic.getProfileForUsername(
      user_key.id(), program_key.to_old_key())

  if not profile:
    raise Exception('Could not find Profile for user and program.')

  def deleteConvUserIfDoesntBelong(conv_user):
    if not doesConversationUserBelong(
        conversation_user=conv_user.key, ignore_auto_update_users=False):
      conv_user.key.delete()

  # Remove user from any conversations they're in that they don't belong in
  conv_user_query = queryForProgramAndUser(user=user_key, program=program_key)
  map(deleteConvUserIfDoesntBelong, conv_user_query)

  def addToConversation(conversation):
    addUserToConversation(conversation=conversation.key, user=user_key)

  mentor_org_keys = profile.mentor_for
  admin_org_keys = profile.admin_for

  # Make sure user is added to program conversations they belong in as a
  # student
  if profile.is_student:
    query = (queryConversationsForProgram(program_key)
        .filter(gciconversation_model.GCIConversation.recipients_type ==
            conversation_model.PROGRAM)
        .filter(gciconversation_model.GCIConversation.auto_update_users == True)
        .filter(gciconversation_model.GCIConversation.include_students == True))
    map(addToConversation, query)

  # Make sure user is added to program conversations they belong in as a
  # mentor
  if profile.is_mentor:
    query = (queryConversationsForProgram(program_key)
      .filter(gciconversation_model.GCIConversation.recipients_type ==
          conversation_model.PROGRAM)
      .filter(gciconversation_model.GCIConversation.auto_update_users == True)
      .filter(gciconversation_model.GCIConversation.include_mentors == True))
    map(addToConversation, query)

  # Make sure user is added to program conversations they belong in as an
  # admin
  if profile.is_admin:
    query = (queryConversationsForProgram(program_key)
        .filter(gciconversation_model.GCIConversation.recipients_type ==
            conversation_model.PROGRAM)
        .filter(gciconversation_model.GCIConversation.auto_update_users == True)
        .filter(gciconversation_model.GCIConversation.include_admins == True))
    map(addToConversation, query)

  # Make sure user is added to program conversations they belong in as a
  # winner
  if profile.student_data and profile.student_data.is_winner:
    query = (queryConversationsForProgram(program_key)
        .filter(gciconversation_model.GCIConversation.recipients_type ==
            conversation_model.PROGRAM)
        .filter(gciconversation_model.GCIConversation.auto_update_users == True)
        .filter(gciconversation_model.GCIConversation.include_winners == True))
    map(addToConversation, query)

  # Make sure user is added to org conversations they belong in as an org
  # mentor
  if profile.is_mentor and mentor_org_keys:
    query = (queryConversationsForProgram(program_key)
        .filter(gciconversation_model.GCIConversation.recipients_type ==
            conversation_model.ORGANIZATION)
        .filter(gciconversation_model.GCIConversation.auto_update_users == True)
        .filter(gciconversation_model.GCIConversation.include_mentors == True)
        .filter(gciconversation_model.GCIConversation.organization.IN(
            mentor_org_keys)))
    map(addToConversation, query)

  # Make sure user is added to org conversations they belong in as an org
  # admin
  if profile.is_admin and admin_org_keys:
    query = (queryConversationsForProgram(program_key)
        .filter(gciconversation_model.GCIConversation.recipients_type ==
            conversation_model.ORGANIZATION)
        .filter(gciconversation_model.GCIConversation.auto_update_users == True)
        .filter(gciconversation_model.GCIConversation.include_admins == True)
        .filter(gciconversation_model.GCIConversation.organization.IN(
            admin_org_keys)))
    map(addToConversation, query)

  # Make sure user is added to org conversations they belong in as an org
  # winner
  if profile.is_student and profile.student_data.is_winner:
    query = (queryConversationsForProgram(program_key)
        .filter(gciconversation_model.GCIConversation.recipients_type ==
            conversation_model.ORGANIZATION)
        .filter(gciconversation_model.GCIConversation.auto_update_users == True)
        .filter(gciconversation_model.GCIConversation.include_winners == True)
        .filter(gciconversation_model.GCIConversation.organization ==
            profile.student_data.winner_for))
    map(addToConversation, query)


def getSubscribedEmails(conversation, exclude=None):
  """Gets the list of email addresses for all users subscribed to a
  conversation.

  Args:
    conversation: Key (ndb) of GCIConversation.
    exclude: Keys (ndb) of Users that, if given, will not be in the set of
             emails.

  Returns:
    Set of email addresses.
  """
  conversation_ent = conversation.get()
  conv_users = queryConversationUserForConversation(conversation)
  program_key = ndb.Key.to_old_key(conversation_ent.program)
  addresses = set()

  for conv_user in conv_users:
    if conv_user.enable_notifications and (
        not exclude or conv_user.user not in exclude):
      profile = profile_logic.getProfileForUsername(
          conv_user.user.id(), program_key)

      if not profile:
        raise Exception('Could not find GCIProfile for user %s and program. %s'
            % (conv_user.name, program_key.name()))

      addresses.add(profile.contact.email)

  return addresses


def notifyParticipantsOfMessage(message, is_reply):
  """Notifies participants in a conversation's participants of a new message.

  Args:
    message: Key (ndb) of GCIMessage of which to notify participants.
    is_reply: Whether this message is a reply to an existing conversation.
  """
  message_ent = message.get()
  conversation_ent = message_ent.conversation.get()

  to_emails = getSubscribedEmails(
      message_ent.conversation, exclude=[message_ent.author])

  context = notifications.getTaskConversationMessageContext(
      message, list(to_emails), is_reply)

  txn = mailer.getSpawnMailTaskTxn(context, parent=None)
  db.run_in_transaction(txn)
