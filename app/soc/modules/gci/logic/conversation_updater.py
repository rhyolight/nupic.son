# Copyright 2014 the Melange authors.
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

"""Class to update a profile's conversations."""

from soc.logic import conversation_updater

from google.appengine.ext import ndb

from soc.models import profile as profile_model

from soc.modules.gci.tasks import update_conversations as update_conversations_task

class ConversationUpdater(conversation_updater.ConversationUpdater):
  """Updates the conversations a profile is involved in.

  Implements the interface defined at
  soc.logic.conversation.ConversationUpdater.

  Args:
    profile: A GCIProfile entity.
  """
  def updateConversationsForProfile(self, profile):
    update_conversations_task.spawnUpdateConversationsTask(
        ndb.Key.from_old_key(profile.parent_key()),
        ndb.Key.from_old_key(
            profile_model.Profile.program.get_value_for_datastore(profile)))

CONVERSATION_UPDATER = ConversationUpdater()
