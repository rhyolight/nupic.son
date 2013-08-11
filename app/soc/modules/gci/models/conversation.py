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

"""Module containing the GCIConversation and GCIConversationUser models."""

from google.appengine.ext import ndb

from soc.models import conversation as conversation_model


class GCIConversation(conversation_model.Conversation):
  """Extension of a Conversation with GCI-specific properties"""

  #: Include all grand prize winners if recipients type is program,
  #: or the organization's winners if recipients type is organization.
  #: Ignored if recipient type is not 'Program' or 'Organization'.
  include_winners = ndb.BooleanProperty(required=False)


class GCIConversationUser(conversation_model.ConversationUser):
  """Extension of a ConversationUser with GCI-specific properties"""

  #: GCIConversation the preferences apply to
  conversation = ndb.KeyProperty(kind=GCIConversation, required=True)
