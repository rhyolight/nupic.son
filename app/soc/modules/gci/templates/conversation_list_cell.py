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

"""Module containing template for a styled cell in a conversation list."""

from google.appengine.ext import db
from google.appengine.ext import ndb

from django.utils import html

from soc.views import template

from soc.logic.helper import timeformat as timeformat_helper

from soc.modules.gci.logic import conversation as gciconversation_logic
from soc.modules.gci.logic import message as gcimessage_logic


class ConversationListCell(template.Template):
  """Template for list of conversations."""

  def __init__(self, data, conversation):
    """Initializes template.

    Args:
      data: RequestData for the request.
      conversation: Key (ndb) of the conversation this cell is displaying.
    """
    self.data = data
    self.conversation = conversation

  def context(self):
    """See soc.views.template.Template.context for full specification."""

    conv_model = self.conversation.get()

    context = {
      'subject': conv_model.subject,
      'num_messages': gcimessage_logic.numMessagesInConversation(
          conv_model.key),
      'num_new_messages':
        gciconversation_logic.numUnreadMessagesForConversationAndUser(
          conv_model.key, ndb.Key.from_old_key(self.data.user.key())),
    }

    last_message = gcimessage_logic.getLastMessageForConversation(
        conv_model.key)

    if last_message is not None:
      last_message_author = db.get(ndb.Key.to_old_key(last_message.author))
      context['last_message_author'] = last_message_author.name
      context['last_message_content'] = (html.strip_tags(last_message.content)
          .replace('\r', '').replace('\n', ' ').strip())
      context['last_message_time'] = timeformat_helper.relativeTime(
          last_message.sent_on)
      context['last_message_ctime'] = last_message.sent_on.ctime()

    return context

  def templatePath(self):
    """See soc.views.template.Template.templatePath for full specification."""
    return 'modules/gci/conversations/_cell.html'
