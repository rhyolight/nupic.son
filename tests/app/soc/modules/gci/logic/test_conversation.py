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

"""Tests for GCI logic for conversations."""

import unittest
import json

from datetime import datetime
from datetime import timedelta

from google.appengine.ext import ndb

from soc.models import user as user_model
from soc.models import email as email_model
from soc.models import conversation as conversation_model

from tests.utils import conversation_utils

from soc.modules.seeder.logic.seeder import logic as seeder_logic

from soc.modules.gci.models import program as gciprogram_model
from soc.modules.gci.models import conversation as gciconversation_model
from soc.modules.gci.models import message as gcimessage_model

from soc.modules.gci.logic import conversation as gciconversation_logic


class GCIConversationTest(unittest.TestCase):
  """Tests the logic for GCI conversations."""

  def setUp(self):
    self.conv_utils = conversation_utils.GCIConversationHelper()
    self.program_key = self.conv_utils.program_key

    # Create three dummy users
    user_ranges = range(3)
    self.user_emails = list('user-%d@example.net' % x for x in user_ranges)
    self.user_keys = list(
        self.conv_utils.createUser(return_key=True, email=self.user_emails[x])
        for x in user_ranges)

    # Conversation created by user 0 including user 1
    self.conv_a = self.conv_utils.createConversation(
        subject='A Subject',
        content='This is a first message.',
        creator=self.user_keys[0],
        users=[self.user_keys[1]])

    # Conversation created by user 1 including user 2
    self.conv_b = self.conv_utils.createConversation(
        subject='Another Subject',
        content='This is another first message.',
        creator=self.user_keys[1],
        users=[self.user_keys[2]])

  def testQueryForProgramAndCreator(self):
    """Tests that queryForProgramAndCreator returns a query for all
    GCIConversation entities for a particular program and creator.
    """

    # User 0 should have created the first conversation
    expected_keys = set([self.conv_a.key])
    actual_keys = set(
        gciconversation_logic.queryForProgramAndCreator(
            program=self.program_key, creator=self.user_keys[0])
        .fetch(keys_only=True))
    self.assertEqual(expected_keys, actual_keys)

    # User 1 should have created the second conversation
    expected_keys = set([self.conv_b.key])
    actual_keys = set(
        gciconversation_logic.queryForProgramAndCreator(
            program=self.program_key, creator=self.user_keys[1])
        .fetch(keys_only=True))
    self.assertEqual(expected_keys, actual_keys)

  def testQueryForProgramAndUser(self):
    """Tests that queryForProgramAndUser returns a query for all
    GCIConversationUser entities for a particular program and user.
    """

    # User 0 should be involved in the first conversation only
    expected_keys = set([self.conv_a.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=self.user_keys[0])))
    self.assertEqual(expected_keys, actual_keys)

    # User 1 should be involved in both conversations
    expected_keys = set([self.conv_a.key, self.conv_b.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=self.user_keys[1])))
    self.assertEqual(expected_keys, actual_keys)

    # User 2 should be involved in the second conversation only
    expected_keys = set([self.conv_b.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=self.user_keys[2])))
    self.assertEqual(expected_keys, actual_keys)

  def testQueryConversationsForProgram(self):
    """Tests that queryConversationsForProgram returns a query for all
    GCIConversation entities for a program.
    """

    # Create a new conversation_utils to create a separate program, and add
    # a conversation
    other_conv_utils = conversation_utils.GCIConversationHelper()
    other_conv = other_conv_utils.createConversation(subject='A Subject')

    # Main program has two conversations
    expected_keys = set([self.conv_a.key, self.conv_b.key])
    actual_keys = set(map(
        lambda conversation: conversation.key,
        gciconversation_logic.queryConversationsForProgram(
            program=self.program_key)))
    self.assertEqual(expected_keys, actual_keys)

    # Other program has one conversation
    expected_keys = set([other_conv.key])
    actual_keys = set(map(
        lambda conversation: conversation.key,
        gciconversation_logic.queryConversationsForProgram(
            program=other_conv_utils.program_key)))
    self.assertEqual(expected_keys, actual_keys)

  def testQueryConversationUserForConversation(self):
    """Tests that queryConversationUserForConversation returns a query for all
    GCIConversationUser entities for a particular conversation.
    """

    # The first conversation should include the first two users
    expected_keys = set([self.user_keys[0], self.user_keys[1]])
    actual_keys = set(map(
        lambda conv_user: conv_user.user,
        gciconversation_logic.queryConversationUserForConversation(
            conversation=self.conv_a.key)))
    self.assertEqual(expected_keys, actual_keys)

    # The second conversation should include the second two users
    expected_keys = set([self.user_keys[1], self.user_keys[2]])
    actual_keys = set(map(
        lambda conv_user: conv_user.user,
        gciconversation_logic.queryConversationUserForConversation(
            conversation=self.conv_b.key)))
    self.assertEqual(expected_keys, actual_keys)

  def testQueryUnreadMessagesForConversationAndUser(self):
    """Tests that queryUnreadMessagesForConversationAndUser returns a query for
    all GCIMessage entities a user hasn't yet read in conversation.
    """

    # Create a blank conversation involving the first two users
    conv = self.conv_utils.createConversation(
        subject='A Subject', users=[self.user_keys[0], self.user_keys[1]])

    # Add two messages one minute apart
    message_a = self.conv_utils.addMessage(
        conversation=conv.key, time=(datetime.utcnow() + timedelta(minutes=1)))
    message_b = self.conv_utils.addMessage(
        conversation=conv.key, time=(datetime.utcnow() + timedelta(minutes=2)))

    # Mark both messages as read for the first user
    self.conv_utils.setUserLastSeenTime(
        conversation=conv.key, user=self.user_keys[1], time=message_b.sent_on)

    # Add a third message
    message_c = self.conv_utils.addMessage(
        conversation=conv.key, time=(datetime.utcnow() + timedelta(minutes=3)))

    # Test that, for the first user, all three messages are unread
    expected_keys = set([message_a.key, message_b.key, message_c.key])
    actual_keys = set(map(
        lambda message: message.key,
        gciconversation_logic.queryUnreadMessagesForConversationAndUser(
            conversation=conv.key, user=self.user_keys[0])))
    self.assertEqual(expected_keys, actual_keys)

    # Test that, for the second user, only the last message is unread
    expected_keys = set([message_c.key])
    actual_keys = set(map(
        lambda message: message.key,
        gciconversation_logic.queryUnreadMessagesForConversationAndUser(
            conversation=conv.key, user=self.user_keys[1])))
    self.assertEqual(expected_keys, actual_keys)

    # Test that, for the third user, an exception is raised because they're not
    # involved in the conversation
    with self.assertRaises(Exception):
      gciconversation_logic.queryUnreadMessagesForConversationAndUser(
          conversation=conv.key, user=self.user_keys[2])

  def testNumUnreadMessagesForConversationAndUser(self):
    """Tests that numUnreadMessagesForConversationAndUser returns the correct
    number of unread messages for each user
    """

    # The initial conversation should have one unread message
    expected = 1
    actual = gciconversation_logic.numUnreadMessagesForConversationAndUser(
        conversation=self.conv_a.key, user=self.user_keys[0])
    self.assertEqual(expected, actual)

    # After adding a message one minute later, there should be two unread
    # messages
    new_message = self.conv_utils.addMessage(
        conversation=self.conv_a.key,
        time=(datetime.utcnow() + timedelta(minutes=1)))
    expected = 2
    actual = gciconversation_logic.numUnreadMessagesForConversationAndUser(
        conversation=self.conv_a.key, user=self.user_keys[0])
    self.assertEqual(expected, actual)

    # Simulate the first user having read the first two messages, and then
    # a third message is added
    self.conv_utils.setUserLastSeenTime(
        conversation=self.conv_a.key, user=self.user_keys[0],
        time=new_message.sent_on)
    new_message_b = self.conv_utils.addMessage(
        conversation=self.conv_a.key,
        time=(datetime.utcnow() + timedelta(minutes=2)))
    expected = 1
    actual = gciconversation_logic.numUnreadMessagesForConversationAndUser(
        conversation=self.conv_a.key, user=self.user_keys[0])
    self.assertEqual(expected, actual)

    # But the other user should have three unread messages
    expected = 3
    actual = gciconversation_logic.numUnreadMessagesForConversationAndUser(
        conversation=self.conv_a.key, user=self.user_keys[1])
    self.assertEqual(expected, actual)

    # An exception should be raised if the user is not involved in the
    # conversation. The first user is not involved in the second conversation.
    with self.assertRaises(Exception):
      gciconversation_logic.numUnreadMessagesForConversationAndUser(
          conversation=self.conv_b.key, user=self.user_keys[0])

  def testMarkAllReadForConversationAndUser(self):
    """Tests that markAllReadForConversationAndUser correctly marks the
    conversation as read.
    """

    # Add three new messages to the first conversation, each one minute apart,
    # starting one minute after the last message.
    for x in range(3):
      self.conv_utils.addMessage(
          conversation=self.conv_a.key,
          time=(self.conv_a.last_message_on + timedelta(minutes=x+1)))

    # First user should have four unread messages
    expected = 4
    actual = gciconversation_logic.numUnreadMessagesForConversationAndUser(
        conversation=self.conv_a.key, user=self.user_keys[0])
    self.assertEqual(expected, actual)

    # Mark as read for first user
    gciconversation_logic.markAllReadForConversationAndUser(
        conversation=self.conv_a.key, user=self.user_keys[0])

    # First user should have zero unread messages
    expected = 0
    actual = gciconversation_logic.numUnreadMessagesForConversationAndUser(
        conversation=self.conv_a.key, user=self.user_keys[0])
    self.assertEqual(expected, actual)

    # Add two new messages to the first conversation, each one minute apart,
    # starting one minute after the last message.
    for x in range(2):
      self.conv_utils.addMessage(
          conversation=self.conv_a.key,
          time=(self.conv_a.last_message_on + timedelta(minutes=x+1)))

    # First user should have two unread messages
    expected = 2
    actual = gciconversation_logic.numUnreadMessagesForConversationAndUser(
        conversation=self.conv_a.key, user=self.user_keys[0])
    self.assertEqual(expected, actual)

    # Second user should have six unread messages
    expected = 6
    actual = gciconversation_logic.numUnreadMessagesForConversationAndUser(
        conversation=self.conv_a.key, user=self.user_keys[1])
    self.assertEqual(expected, actual)

    # An exception should be raised if the user is not involved in the
    # conversation. The first user is not involved in the second conversation.
    with self.assertRaises(Exception):
      gciconversation_logic.markAllReadForConversationAndUser(
          conversation=self.conv_b.key, user=self.user_keys[0])

  def testNumUnreadMessagesForProgramAndUser(self):
    """Tests that numUnreadMessagesForProgramAndUser computes the correct number
    of messages for all conversations in a program for a particular user.
    """

    # Add three new messages to the first conversation, each one minute apart,
    # starting one minute after the last message.
    for x in range(3):
      self.conv_utils.addMessage(
          conversation=self.conv_a.key,
          time=(self.conv_a.last_message_on + timedelta(minutes=x+1)))

    # Add two new messages to the second conversation, each one minute apart,
    # starting one minute after the last message.
    for x in range(2):
      self.conv_utils.addMessage(
          conversation=self.conv_b.key,
          time=(self.conv_b.last_message_on + timedelta(minutes=x+1)))

    # The first user, who is only in the first conversation, should have
    # four unread messages
    expected = 4
    actual = gciconversation_logic.numUnreadMessagesForProgramAndUser(
        program=self.program_key, user=self.user_keys[0])
    self.assertEqual(expected, actual)

    # The second user, who is in both conversations, should have
    # seven unread messages
    expected = 7
    actual = gciconversation_logic.numUnreadMessagesForProgramAndUser(
        program=self.program_key, user=self.user_keys[1])
    self.assertEqual(expected, actual)

  def testCreateMessage(self):
    """Test that createMessage correctly creates a new message and updates
    the conversation's last_message_on time.
    """

    # Fresh conversation with no messages
    blank_conversation = self.conv_utils.createConversation(subject='A Subject')

    # Add message
    message = gciconversation_logic.createMessage(
        conversation=blank_conversation.key)

    self.assertIsNotNone(message)

    # Get conversation with updated values
    blank_conversation = blank_conversation.key.get()

    # Conversation's last_message_on should be message's sent_time
    expected = message.sent_on
    actual = blank_conversation.last_message_on
    self.assertEqual(expected, actual)

  def testAddUserToConversation(self):
    """Test that addUserToConversation adds the user to the conversation, but
    only if they're not already involved.
    """

    # Fresh conversation with no messages
    conversation = self.conv_utils.createConversation(subject='A Subject')

    # Add first and third users to conversation
    convuser_a = gciconversation_logic.addUserToConversation(
        conversation=conversation.key, user=self.user_keys[0])
    convuser_b = gciconversation_logic.addUserToConversation(
        conversation=conversation.key, user=self.user_keys[2])

    # Add the first user again to make sure it doesn't create a duplicate
    # GCIConversationUser entity
    convuser_a_duplicate = gciconversation_logic.addUserToConversation(
        conversation=conversation.key, user=self.user_keys[0])
    self.assertEqual(convuser_a, convuser_a_duplicate)

    # Test that GCIConversationUser entities for the users exist
    expected_keys = set([self.user_keys[0], self.user_keys[2]])
    actual_keys = set(map(
        lambda conv_user: conv_user.user,
        gciconversation_logic.queryConversationUserForConversation(
            conversation=conversation.key)))
    self.assertEqual(expected_keys, actual_keys)

  def testRemoveUserFromConversation(self):
    """Test that removeUserFromConversation removes the user from the
    conversation.
    """

    # Fresh conversation with no messages
    conversation = self.conv_utils.createConversation(subject='A Subject')

    # Add all three user to conversation
    gciconversation_logic.addUserToConversation(
        conversation=conversation.key, user=self.user_keys[0])
    gciconversation_logic.addUserToConversation(
        conversation=conversation.key, user=self.user_keys[1])
    gciconversation_logic.addUserToConversation(
        conversation=conversation.key, user=self.user_keys[2])

    # Remove first two users
    gciconversation_logic.removeUserFromConversation(
        conversation=conversation.key, user=self.user_keys[0])
    gciconversation_logic.removeUserFromConversation(
        conversation=conversation.key, user=self.user_keys[1])

    # Remove first user again to make sure nothing bad happens from removing a
    # user who isn't even involved.
    gciconversation_logic.removeUserFromConversation(
        conversation=conversation.key, user=self.user_keys[0])

    # Test that GCIConversationUser entities for the third user exists
    expected_keys = set([self.user_keys[2]])
    actual_keys = set(map(
        lambda conv_user: conv_user.user,
        gciconversation_logic.queryConversationUserForConversation(
            conversation=conversation.key)))
    self.assertEqual(expected_keys, actual_keys)

  def testDoesUserBelongInConversation(self):
    """Tests that doesUserBelongInConversation correctly decides if a user in a
    conversation still belongs in the conversation.
    """

    # Create a couple dummy organizations
    org_keys = map(
        lambda org: ndb.Key.from_old_key(org.key()),
        list(self.conv_utils.program_helper.createNewOrg() for _ in range(2)))

    # Dummy user to create conversation
    creator = self.conv_utils.createUser(return_key=True)

    # Create three dummy admin users, two as admins for the two orgs, then a
    # third that is an admin for both orgs.
    dummy_org_admin_a = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.ADMIN],
        admin_organizations=[org_keys[0]])
    dummy_org_admin_b = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.ADMIN],
        admin_organizations=[org_keys[1]])
    dummy_org_admin_ab = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.ADMIN],
        admin_organizations=[org_keys[0], org_keys[1]])

    # Create three dummy mentor users, two as mentors for the two orgs, then a
    # third that is a mentor for both orgs.
    dummy_org_mentor_a = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.MENTOR],
        mentor_organizations=[org_keys[0]])
    dummy_org_mentor_b = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.MENTOR],
        mentor_organizations=[org_keys[1]])
    dummy_org_mentor_ab = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.MENTOR],
        mentor_organizations=[org_keys[0], org_keys[1]])

    # Create two dummy winner users, each as a winner of each org
    dummy_winner_a = self.conv_utils.createUser(
        return_key=True, winning_organization=org_keys[0],
        roles=[conversation_utils.STUDENT, conversation_utils.WINNER])
    dummy_winner_b = self.conv_utils.createUser(
        return_key=True, winning_organization=org_keys[1],
        roles=[conversation_utils.STUDENT, conversation_utils.WINNER])

    # Fresh conversation with no messages
    conversation = self.conv_utils.createConversation(subject='A Subject')

    # Conversation should include program admins and mentors
    conversation.creator = creator
    conversation.recipients_type = conversation_model.PROGRAM
    conversation.include_admins = True
    conversation.put()

    # Test that doesUserBelongInConversation returns True only for users that
    # should belong.
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=creator))
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_admin_a))
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_admin_b))
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_admin_ab))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_mentor_a))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_mentor_b))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_mentor_ab))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_winner_a))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_winner_b))

    # Conversation should include mentors from the second organization
    conversation.recipients_type = conversation_model.ORGANIZATION
    conversation.organization = org_keys[1]
    conversation.include_admins = False
    conversation.include_mentors = True
    conversation.put()

    # Test that doesUserBelongInConversation returns True only for users that
    # should belong.
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=creator))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_admin_a))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_admin_b))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_admin_ab))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_mentor_a))
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_mentor_b))
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_mentor_ab))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_winner_a))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_winner_b))

    # Conversation is now set to have users specified manually
    conversation.recipients_type = conversation_model.USER
    conversation.put()

    # Test that doesUserBelongInConversation returns True for all users since
    # recipients_type is 'User'.
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=creator))
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_admin_a))
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_admin_b))
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_admin_ab))
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_mentor_a))
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_mentor_b))
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_mentor_ab))
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_winner_a))
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_winner_b))

    # Conversation should include winners from the first organization
    conversation.recipients_type = conversation_model.ORGANIZATION
    conversation.organization = org_keys[0]
    conversation.include_mentors = False
    conversation.include_winners = True
    conversation.put()

    # Test that doesUserBelongInConversation returns True only for the winner
    # of the first organization and the creator.
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=creator))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_admin_a))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_admin_b))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_admin_ab))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_mentor_a))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_mentor_b))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_mentor_ab))
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_winner_a))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_winner_b))

    # Conversation should include winners in the whole program
    conversation.recipients_type = conversation_model.PROGRAM
    conversation.put()

    # Test that doesUserBelongInConversation returns True only for the winners
    # and the creator.
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=creator))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_admin_a))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_admin_b))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_admin_ab))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_mentor_a))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_mentor_b))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_mentor_ab))
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_winner_a))
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_winner_b))

    # Conversation should include students in the program
    conversation.recipients_type = conversation_model.PROGRAM
    conversation.include_winners = False
    conversation.include_students = True
    conversation.put()

    # Test that doesUserBelongInConversation returns True only for students
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=creator))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_admin_a))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_admin_b))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_admin_ab))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_mentor_a))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_mentor_b))
    self.assertFalse(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_org_mentor_ab))
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_winner_a))
    self.assertTrue(gciconversation_logic.doesUserBelongInConversation(
        conversation=conversation.key, user=dummy_winner_b))

  def testRefreshConversationParticipants(self):
    """Test that refreshConversationParticipants adds users to the conversation
    who fit the criteria for involvement, and removes any users who are involved
    but no longer should be.
    """

    # Create dummy admins, mentors, and students, some hybrid users, and a
    # conversation creator
    creator = self.conv_utils.createUser(return_key=True)
    dummy_admin_keys = list(
        self.conv_utils.createUser(
            return_key=True,
            roles=[conversation_utils.ADMIN]) for _ in range(2))
    dummy_mentor_keys = list(
        self.conv_utils.createUser(
            return_key=True,
            roles=[conversation_utils.MENTOR]) for _ in range(2))
    dummy_student_keys = list(
        self.conv_utils.createUser(
            return_key=True,
            roles=[conversation_utils.STUDENT]) for _ in range(2))
    dummy_mentor_student_keys = list(
        self.conv_utils.createUser(
            return_key=True,
            roles=[conversation_utils.STUDENT, conversation_utils.MENTOR])
                for _ in range(2))
    dummy_winner_keys = list(
        self.conv_utils.createUser(
            return_key=True,
            roles=[conversation_utils.STUDENT, conversation_utils.WINNER])
                for _ in range(2))

    # Fresh conversation with no messages
    conversation = self.conv_utils.createConversation(subject='A Subject')

    # Conversation should include program admins and mentors
    conversation.creator = creator
    conversation.recipients_type = conversation_model.PROGRAM
    conversation.include_admins = True
    conversation.include_mentors = True
    conversation.put()

    # After refreshing conversation participants, verify that the correct users
    # are involved.
    gciconversation_logic.refreshConversationParticipants(conversation.key)
    expected_keys = set(
        dummy_admin_keys + dummy_mentor_keys + dummy_mentor_student_keys
        + [creator])
    actual_keys = set(map(
        lambda conv_user: conv_user.user,
        gciconversation_logic.queryConversationUserForConversation(
            conversation=conversation.key)))
    self.assertEqual(expected_keys, actual_keys)

    # Now conversation should only include students in the program
    conversation.include_admins = False
    conversation.include_mentors = False
    conversation.include_students = True
    conversation.put()

    # After refreshing conversation participants, verify that the correct users
    # are involved.
    gciconversation_logic.refreshConversationParticipants(conversation.key)
    expected_keys = set(
        dummy_student_keys + dummy_mentor_student_keys + dummy_winner_keys +
        [creator])
    actual_keys = set(map(
        lambda conv_user: conv_user.user,
        gciconversation_logic.queryConversationUserForConversation(
            conversation=conversation.key)))
    self.assertEqual(expected_keys, actual_keys)

    # Now conversation should only winners in the program, after clearing out
    # existing users.
    conversation.include_students = False
    conversation.put()
    gciconversation_logic.refreshConversationParticipants(conversation.key)
    conversation.include_winners = True
    conversation.put()

    # After refreshing conversation participants, verify that the correct users
    # are involved.
    gciconversation_logic.refreshConversationParticipants(conversation.key)
    expected_keys = set(dummy_winner_keys + [creator])
    actual_keys = set(map(
        lambda conv_user: conv_user.user,
        gciconversation_logic.queryConversationUserForConversation(
            conversation=conversation.key)))
    self.assertEqual(expected_keys, actual_keys)

    # Now conversation should only the creator
    conversation.include_winners = False
    conversation.put()

    # After refreshing conversation participants, verify that only the
    # creator is still involved.
    gciconversation_logic.refreshConversationParticipants(conversation.key)
    expected_keys = set([creator])
    actual_keys = set(map(
        lambda conv_user: conv_user.user,
        gciconversation_logic.queryConversationUserForConversation(
            conversation=conversation.key)))
    self.assertEqual(expected_keys, actual_keys)

    # Create a couple dummy organizations
    org_keys = map(
        lambda org: ndb.Key.from_old_key(org.key()),
        list(self.conv_utils.program_helper.createNewOrg() for _ in range(2)))

    # Create three dummy admin users, two as admins for the two orgs, then a
    # third that is an admin for both orgs.
    dummy_org_admin_a = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.ADMIN],
        admin_organizations=[org_keys[0]])
    dummy_org_admin_b = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.ADMIN],
        admin_organizations=[org_keys[1]])
    dummy_org_admin_ab = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.ADMIN],
        admin_organizations=[org_keys[0], org_keys[1]])

    # Create three dummy mentor users, two as mentors for the two orgs, then a
    # third that is a mentor for both orgs.
    dummy_org_mentor_a = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.MENTOR],
        mentor_organizations=[org_keys[0]])
    dummy_org_mentor_b = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.MENTOR],
        mentor_organizations=[org_keys[1]])
    dummy_org_mentor_ab = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.MENTOR],
        mentor_organizations=[org_keys[0], org_keys[1]])

    # Create two dummy winner users, each as a winner of each org
    dummy_winner_a = self.conv_utils.createUser(
        return_key=True, winning_organization=org_keys[0],
        roles=[conversation_utils.STUDENT, conversation_utils.WINNER])
    dummy_winner_b = self.conv_utils.createUser(
        return_key=True, winning_organization=org_keys[1],
        roles=[conversation_utils.STUDENT, conversation_utils.WINNER])

    # Conversation should now include mentors for the first organization only
    conversation.recipients_type = conversation_model.ORGANIZATION
    conversation.organization = org_keys[0]
    conversation.include_mentors = True
    conversation.put()

    # After refreshing conversation participants, verify that the correct users
    # are involved.
    gciconversation_logic.refreshConversationParticipants(conversation.key)
    expected_keys = set([creator, dummy_org_mentor_a, dummy_org_mentor_ab])
    actual_keys = set(map(
        lambda conv_user: conv_user.user,
        gciconversation_logic.queryConversationUserForConversation(
            conversation=conversation.key)))
    self.assertEqual(expected_keys, actual_keys)

    # Conversation should now include admins for the second organization only
    conversation.organization = org_keys[1]
    conversation.include_admins = True
    conversation.include_mentors = False
    conversation.put()

    # After refreshing conversation participants, verify that the correct users
    # are involved.
    gciconversation_logic.refreshConversationParticipants(conversation.key)
    expected_keys = set([creator, dummy_org_admin_b, dummy_org_admin_ab])
    actual_keys = set(map(
        lambda conv_user: conv_user.user,
        gciconversation_logic.queryConversationUserForConversation(
            conversation=conversation.key)))
    self.assertEqual(expected_keys, actual_keys)

    # Conversation should now include the winner for the first organization only
    conversation.organization = org_keys[0]
    conversation.include_admins = False
    conversation.include_winners = True
    conversation.put()

    # After refreshing conversation participants, verify that the correct users
    # are involved.
    gciconversation_logic.refreshConversationParticipants(conversation.key)
    expected_keys = set([creator, dummy_winner_a])
    actual_keys = set(map(
        lambda conv_user: conv_user.user,
        gciconversation_logic.queryConversationUserForConversation(
            conversation=conversation.key)))
    self.assertEqual(expected_keys, actual_keys)

  def testRefreshConversationsForUser(self):
    """Tests that refreshConversationsForUser correctly adds a user to all
    conversations they should be in but aren't, and removes them from
    conversations they shouldn't be in.
    """

    self.conv_a.key.delete()
    self.conv_b.key.delete()

    # Create a couple dummy organizations
    org_keys = map(
        lambda org: ndb.Key.from_old_key(org.key()),
        list(self.conv_utils.program_helper.createNewOrg() for x in range(2)))

    # Create various dummy users
    user_admin_key = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.ADMIN],
        admin_organizations=[org_keys[0]])
    user_mentor_key = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.MENTOR],
        mentor_organizations=[org_keys[0], org_keys[1]])
    user_mentor_student_key = self.conv_utils.createUser(
        return_key=True,
        roles=[conversation_utils.MENTOR, conversation_utils.STUDENT])
    user_winner_key = self.conv_utils.createUser(
        return_key=True, winning_organization=org_keys[1],
        roles=[conversation_utils.WINNER, conversation_utils.STUDENT])
    
    # Conversation for program admins and mentors
    conv_a = self.conv_utils.createConversation(subject='')
    conv_a.recipients_type = conversation_model.PROGRAM
    conv_a.include_admins = True
    conv_a.include_mentors = True
    conv_a.put()

    # Conversation for first org's admins
    conv_b = self.conv_utils.createConversation(subject='')
    conv_b.recipients_type = conversation_model.ORGANIZATION
    conv_b.organization = org_keys[0]
    conv_b.include_admins = True
    conv_b.put()

    # Conversation for second org's mentors
    conv_c = self.conv_utils.createConversation(subject='')
    conv_c.recipients_type = conversation_model.ORGANIZATION
    conv_c.organization = org_keys[1]
    conv_c.include_mentors = True
    conv_c.put()

    # Conversation for program mentors and students
    conv_d = self.conv_utils.createConversation(subject='')
    conv_d.recipients_type = conversation_model.PROGRAM
    conv_d.include_mentors = True
    conv_d.include_students = True
    conv_d.put()

    # Conversation for program students, created by a non-student
    conv_e = self.conv_utils.createConversation(subject='')
    conv_e.creator = user_admin_key
    conv_e.recipients_type = conversation_model.PROGRAM
    conv_e.include_students = True
    conv_e.put()
    self.conv_utils.addUser(conversation=conv_e.key, user=conv_e.creator)

    # Conversation for basically nobody, in which the participants should not
    # be changed after the conversation's creation, and all users are added.
    # This is to ensure that users won't be removed if the conversation's
    # auto_update_users property is False.
    conv_f = self.conv_utils.createConversation(subject='')
    conv_f.recipients_type = conversation_model.PROGRAM
    conv_f.auto_update_users = False
    conv_f.put()
    self.conv_utils.addUser(conversation=conv_f.key, user=user_admin_key)
    self.conv_utils.addUser(conversation=conv_f.key, user=user_mentor_key)
    self.conv_utils.addUser(
        conversation=conv_f.key, user=user_mentor_student_key)
    self.conv_utils.addUser(conversation=conv_f.key, user=user_winner_key)

    # Conversation for that all users fit the criteria to participate in, but
    # should not be added after the converation's creation.
    conv_g = self.conv_utils.createConversation(subject='')
    conv_g.recipients_type = conversation_model.PROGRAM
    conv_g.include_students = True
    conv_g.include_mentors = True
    conv_g.include_admins = True
    conv_g.auto_update_users = False
    conv_g.put()

    # Conversation for program winners, created by a non-winner
    conv_h = self.conv_utils.createConversation(subject='')
    conv_h.recipients_type = conversation_model.PROGRAM
    conv_h.include_winners = True
    conv_h.put()

    # Conversation for winners of first organization
    conv_i = self.conv_utils.createConversation(subject='')
    conv_i.recipients_type = conversation_model.ORGANIZATION
    conv_i.organization = org_keys[0]
    conv_i.include_winners = True
    conv_i.put()

    # Conversation for winners of second organization
    conv_j = self.conv_utils.createConversation(subject='')
    conv_j.recipients_type = conversation_model.ORGANIZATION
    conv_j.organization = org_keys[1]
    conv_j.include_winners = True
    conv_j.put()

    # Refresh each user's conversations
    gciconversation_logic.refreshConversationsForUserAndProgram(
        user=user_admin_key, program=self.program_key)
    gciconversation_logic.refreshConversationsForUserAndProgram(
        user=user_mentor_key, program=self.program_key)
    gciconversation_logic.refreshConversationsForUserAndProgram(
        user=user_mentor_student_key, program=self.program_key)
    gciconversation_logic.refreshConversationsForUserAndProgram(
        user=user_winner_key, program=self.program_key)

    # Test that admin user is in the correct conversations
    expected_keys = set([conv_a.key, conv_b.key, conv_e.key, conv_f.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_admin_key)))
    self.assertEqual(expected_keys, actual_keys)

    # Test that mentor user is in the correct conversations
    expected_keys = set([conv_a.key, conv_c.key, conv_d.key, conv_f.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_mentor_key)))
    self.assertEqual(expected_keys, actual_keys)

    # Test that mentor/student user is in the correct conversations
    expected_keys = set([conv_a.key, conv_d.key, conv_e.key, conv_f.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_mentor_student_key)))
    self.assertEqual(expected_keys, actual_keys)

    # Test that winner user is in the correct conversations
    expected_keys = set(
        [conv_d.key, conv_e.key, conv_f.key, conv_h.key, conv_j.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_winner_key)))
    self.assertEqual(expected_keys, actual_keys)

    # Add all three users to all conversations
    self.conv_utils.addUser(conversation=conv_b.key, user=user_mentor_key)
    self.conv_utils.addUser(
        conversation=conv_b.key, user=user_mentor_student_key)
    self.conv_utils.addUser(conversation=conv_c.key, user=user_admin_key)
    self.conv_utils.addUser(
        conversation=conv_c.key, user=user_mentor_student_key)
    self.conv_utils.addUser(conversation=conv_d.key, user=user_admin_key)
    self.conv_utils.addUser(conversation=conv_e.key, user=user_mentor_key)
    self.conv_utils.addUser(
        conversation=conv_h.key, user=user_mentor_student_key)
    self.conv_utils.addUser(conversation=conv_h.key, user=user_mentor_key)
    self.conv_utils.addUser(conversation=conv_h.key, user=user_admin_key)
    self.conv_utils.addUser(
        conversation=conv_i.key, user=user_mentor_student_key)
    self.conv_utils.addUser(conversation=conv_i.key, user=user_mentor_key)
    self.conv_utils.addUser(conversation=conv_i.key, user=user_admin_key)
    self.conv_utils.addUser(
        conversation=conv_j.key, user=user_mentor_student_key)
    self.conv_utils.addUser(conversation=conv_j.key, user=user_mentor_key)
    self.conv_utils.addUser(conversation=conv_j.key, user=user_admin_key)
    self.conv_utils.addUser(conversation=conv_a.key, user=user_winner_key)
    self.conv_utils.addUser(conversation=conv_b.key, user=user_winner_key)
    self.conv_utils.addUser(conversation=conv_c.key, user=user_winner_key)
    self.conv_utils.addUser(conversation=conv_i.key, user=user_winner_key)

    # Test that admin user is in all conversations except for G
    expected_keys = set([
        conv_a.key, conv_b.key, conv_c.key, conv_d.key, conv_e.key, conv_f.key,
        conv_h.key, conv_i.key, conv_j.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_admin_key)))

    self.assertEqual(expected_keys, actual_keys)

    # Test that mentor user is in all conversations except for G
    expected_keys = set([
        conv_a.key, conv_b.key, conv_c.key, conv_d.key, conv_e.key, conv_f.key,
        conv_h.key, conv_i.key, conv_j.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_mentor_key)))
    self.assertEqual(expected_keys, actual_keys)

    # Test that mentor/student user is in all conversations except for G
    expected_keys = set([
        conv_a.key, conv_b.key, conv_c.key, conv_d.key, conv_e.key, conv_f.key,
        conv_h.key, conv_i.key, conv_j.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_mentor_student_key)))
    self.assertEqual(expected_keys, actual_keys)

    # Test that winner user is in all conversations except for G
    expected_keys = set([
        conv_a.key, conv_b.key, conv_c.key, conv_d.key, conv_e.key, conv_f.key,
        conv_h.key, conv_i.key, conv_j.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_winner_key)))
    self.assertEqual(expected_keys, actual_keys)

    # Refresh each user's conversations. Because we just added all users to
    # all conversations, refreshing each user should actually remove them from
    # conversations they don't belong to.
    gciconversation_logic.refreshConversationsForUserAndProgram(
        user=user_admin_key, program=self.program_key)
    gciconversation_logic.refreshConversationsForUserAndProgram(
        user=user_mentor_key, program=self.program_key)
    gciconversation_logic.refreshConversationsForUserAndProgram(
        user=user_mentor_student_key, program=self.program_key)
    gciconversation_logic.refreshConversationsForUserAndProgram(
        user=user_winner_key, program=self.program_key)

    # Test that admin user is in the correct conversations
    expected_keys = set([conv_a.key, conv_b.key, conv_e.key, conv_f.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_admin_key)))

    self.assertEqual(expected_keys, actual_keys)

    # Test that mentor user is in the correct conversations
    expected_keys = set([conv_a.key, conv_c.key, conv_d.key, conv_f.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_mentor_key)))
    self.assertEqual(expected_keys, actual_keys)

    # Test that mentor/student user is in the correct conversations
    expected_keys = set([conv_a.key, conv_d.key, conv_e.key, conv_f.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_mentor_student_key)))
    self.assertEqual(expected_keys, actual_keys)

    # Test that winner user is in the correct conversations
    expected_keys = set(
        [conv_d.key, conv_e.key, conv_f.key, conv_h.key, conv_j.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_winner_key)))
    self.assertEqual(expected_keys, actual_keys)

  def testGetSubscribedEmails(self):
    """Tests that getSubscribedEmails correctly returns email addresses of
    users subscribed to a conversation.
    """
    # Create a few users with unique email addresses
    email_a = 'a@example.net'
    user_a_key = self.conv_utils.createUser(
        return_key=True, email=email_a)
    self.conv_utils.addUser(
        conversation=self.conv_a.key, user=user_a_key,
        enable_notifications=False)
    self.conv_utils.addUser(
        conversation=self.conv_b.key, user=user_a_key,
        enable_notifications=False)

    # Add another new user to the two conversations with notifications enabled
    email_b = 'b@example.net'
    user_b_key = self.conv_utils.createUser(
        return_key=True, email=email_b)
    self.conv_utils.addUser(
        conversation=self.conv_a.key, user=user_b_key,
        enable_notifications=True)
    self.conv_utils.addUser(
        conversation=self.conv_b.key, user=user_b_key,
        enable_notifications=True)

    # Test that first conversation has certain subscribed users
    expected = set([self.user_emails[0], self.user_emails[1], email_b])
    actual = set(gciconversation_logic.getSubscribedEmails(self.conv_a.key))
    self.assertEqual(expected, actual)

    # Test that second conversation has certain subscribed users
    expected = set([self.user_emails[1], self.user_emails[2], email_b])
    actual = set(gciconversation_logic.getSubscribedEmails(self.conv_b.key))
    self.assertEqual(expected, actual)

    # Test that second conversation has certain subscribed users, excluding
    # a particular user
    expected = set([self.user_emails[1], email_b])
    actual = set(gciconversation_logic.getSubscribedEmails(
        self.conv_b.key, exclude=[self.user_keys[2]]))
    self.assertEqual(expected, actual)

  def testNotifyParticipantsOfMessage(self):
    """Tests that notifyParticipantsOfMessage sends the correct email
    notification to subscribed recipients of a conversation for a message.
    """
    # Create a few users with unique email addresses
    email_a = 'a@example.net'
    user_a = self.conv_utils.createUser(email=email_a)
    user_a_key = ndb.Key.from_old_key(user_a.key())
    self.conv_utils.addUser(
        conversation=self.conv_a.key, user=user_a_key,
        enable_notifications=False)
    self.conv_utils.addUser(
        conversation=self.conv_b.key, user=user_a_key,
        enable_notifications=False)

    # Add another new user to the two conversations with notifications enabled
    email_b = 'b@example.net'
    user_b = self.conv_utils.createUser(email=email_b)
    user_b_key = ndb.Key.from_old_key(user_b.key())
    self.conv_utils.addUser(
        conversation=self.conv_a.key, user=user_b_key,
        enable_notifications=True)
    self.conv_utils.addUser(
        conversation=self.conv_b.key, user=user_b_key,
        enable_notifications=True)

    # Add a new message and send an email notification for it as if it were the
    # first message.
    content = 'Hello universe?'
    message = self.conv_utils.addMessage(
        self.conv_a.key, user=user_b_key, content=content)
    gciconversation_logic.notifyParticipantsOfMessage(
        message.key, False)

    # Get last entity in email entity group
    email = email_model.Email.all().get()
    email_ctx = json.loads(email.context)
    
    # Test that email has correct recipients
    expected = set([self.user_emails[0], self.user_emails[1]])
    actual = set(email_ctx['bcc'])
    self.assertSetEqual(expected, actual)

    # Test that email subject has conversation subject and sender username
    self.assertIn(self.conv_a.subject, email_ctx['subject'])
    self.assertIn(user_b.name, email_ctx['subject'])

    # Assert that email HTML has correct content
    self.assertIn(content, email_ctx['html'])
    self.assertIn('created', email_ctx['html'])

    # Delete email context from datastore
    email.delete()

    # Add a new message and send an email notification for it as if it were a
    # reply
    content = 'The universe is busy at the moment. Please check back later.'
    message = self.conv_utils.addMessage(
        self.conv_a.key, user=user_a_key, content=content)
    gciconversation_logic.notifyParticipantsOfMessage(
        message.key, True)

    # Get last entity in email entity group
    email = email_model.Email.all().get()
    email_ctx = json.loads(email.context)
    
    # Test that email has correct recipients
    expected = set([self.user_emails[0], self.user_emails[1], email_b])
    actual = set(email_ctx['bcc'])
    self.assertSetEqual(expected, actual)

    # Test that email subject has conversation subject and sender username
    self.assertIn(self.conv_a.subject, email_ctx['subject'])
    self.assertIn(user_a.name, email_ctx['subject'])

    # Assert that email HTML has correct content
    self.assertIn(content, email_ctx['html'])
    self.assertIn('replied', email_ctx['html'])
