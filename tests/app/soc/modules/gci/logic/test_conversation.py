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

from datetime import datetime
from datetime import timedelta

from google.appengine.ext import ndb

from soc.models import user as user_model

from tests.utils import conversation_utils

from soc.modules.seeder.logic.seeder import logic as seeder_logic

from soc.modules.gci.models import program as gciprogram_model
from soc.modules.gci.models import conversation as gciconversation_model
from soc.modules.gci.models import message as gcimessage_model

from soc.modules.gci.logic import conversation as gciconversation_logic


class GCIConversationTest(unittest.TestCase):
  """Tests the logic for GCI conversations."""

  def setUp(self):
    program = seeder_logic.seed(gciprogram_model.GCIProgram)
    self.program_key = ndb.Key.from_old_key(program.key())
    self.conv_utils = conversation_utils.GCIConversationHelper(self.program_key)

    # Ndb keys of three dummy users
    self.user_keys = []
    for _ in range(3):
      self.user_keys.append(seeder_logic.seed(user_model.User))
    self.user_keys = map(
        lambda user: ndb.Key.from_old_key(user.key()), self.user_keys)

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
