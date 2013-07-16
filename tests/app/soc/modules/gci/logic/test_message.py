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

"""Tests for GCI logic for messages."""

import unittest

from datetime import datetime
from datetime import timedelta

from google.appengine.ext import ndb

from soc.models import user as user_model

from tests.utils import conversation_utils

from soc.modules.seeder.logic.seeder import logic as seeder_logic

from soc.modules.gci.logic import message as gcimessage_logic

from soc.modules.gci.models import program as gciprogram_model


class GCIMessage(unittest.TestCase):
  """Tests the logic for GCI messages."""

  def setUp(self):
    program = seeder_logic.seed(gciprogram_model.GCIProgram)
    self.program_key = ndb.Key.from_old_key(program.key())
    self.conv_utils = conversation_utils.GCIConversationHelper(self.program_key)

    # Ndb keys of two dummy users
    self.user_keys = []
    for _ in range(2):
      self.user_keys.append(seeder_logic.seed(user_model.User))
    self.user_keys = map(
        lambda user: ndb.Key.from_old_key(user.key()), self.user_keys)

    # Conversation created by user 0 including user 1, without initial message
    self.conv = self.conv_utils.createConversation(
        subject='A Subject',
        creator=self.user_keys[0],
        users=[self.user_keys[1]])

    # Add three messages, each one minute apart
    self.msg_keys = []
    for x in range(3):
      self.msg_keys.append(
          self.conv_utils.addMessage(
              conversation=self.conv.key,
              time=(datetime.utcnow() + timedelta(minutes=x))))
    self.msg_keys = map(
        lambda message: message.key, self.msg_keys)

  def testQueryForConversation(self):
    """Tests that queryForConversation returns a query for all
    GCIMessage entities for a particular conversation.
    """

    expected_keys = self.msg_keys
    actual_keys = gcimessage_logic.queryForConversation(
        conversation=self.conv.key).fetch(20, keys_only=True)
    self.assertEqual(expected_keys, actual_keys)

  def testGetLastMessageForConversation(self):
    """Tests that getLastMessageForConversation returns the last GCIMessage
    in a conversation.
    """
    
    last_msg = self.msg_keys[-1].get()

    # Make sure we get the last message
    expected = last_msg
    actual = gcimessage_logic.getLastMessageForConversation(
        conversation=self.conv.key)
    self.assertEqual(expected, actual)

    # Add a new message, one minute after the last one
    new_msg = self.conv_utils.addMessage(
        conversation=self.conv.key,
        time=(last_msg.sent_on + timedelta(minutes=1)))

    # Make sure we get the new last message
    expected = new_msg
    actual = gcimessage_logic.getLastMessageForConversation(
        conversation=self.conv.key)
    self.assertEqual(expected, actual)

  def testNumMessagesInConversation(self):
    """Tests that numMessagesInConversation returns the correct number of
    GCIMessages in a conversation.
    """

    # Make sure we get the last message
    expected = len(self.msg_keys)
    actual = gcimessage_logic.numMessagesInConversation(
        conversation=self.conv.key)
    self.assertEqual(expected, actual)

    # Add a new message, one minute after the last one
    self.conv_utils.addMessage(
        conversation=self.conv.key,
        time=(self.msg_keys[-1].get().sent_on + timedelta(minutes=1)))

    # Make sure we get the new last message
    expected = len(self.msg_keys) + 1
    actual = gcimessage_logic.numMessagesInConversation(
        conversation=self.conv.key)
    self.assertEqual(expected, actual)
