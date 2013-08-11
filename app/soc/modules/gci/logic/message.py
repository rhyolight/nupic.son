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
 
"""GCIMessage logic methods."""
 
from soc.modules.gci.models import message as gcimessage_model


def queryForConversation(conversation):
  """Creates a query for GCIMessage entities for the given GCIConversation.

  Args:
    conversation: Key (ndb) of GCIConversation.

  Returns:
    An ndb query for GCIMessages in the conversation.
  """
  return gcimessage_model.GCIMessage.query(
      gcimessage_model.GCIMessage.conversation == conversation)
 
 
def getLastMessageForConversation(conversation):
  """Gets the last message for the given GCIConversation.
 
  Args:
    conversation: Key (ndb) of GCIConversation.

  Returns:
    The most recent GCIMessage in the conversation, or None if there are no
    messages in the conversation.
  """
  results = (queryForConversation(conversation)
      .order(-gcimessage_model.GCIMessage.sent_on)
      .fetch(1))
  return results[0] if results else None


def numMessagesInConversation(conversation):
  """Calculates the number of messages in a given GCIConversation.

  Args:
    conversation: Key (ndb) of GCIConversation.

  Returns:
    The number of GCIMessages in the conversation.
  """
  return queryForConversation(conversation).count()
