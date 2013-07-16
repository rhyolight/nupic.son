# Copyright 2013 the Melange authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module containing the conversation view with messages."""


from google.appengine.ext import ndb

from soc.views.helper import url_patterns
from soc.views.helper import access_checker

from soc.modules.gci.logic import conversation as gciconversation_logic
from soc.modules.gci.logic import message as gcimessage_logic

from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views.helper.url_patterns import url
from soc.modules.gci.views.helper import url_names


class ConversationPage(GCIRequestHandler):
  """View for a conversation."""

  def templatePath(self):
    return 'modules/gci/conversation/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'conversation/%s$' % url_patterns.ID, self,
            name=url_names.GCI_CONVERSATION),
    ]

  def checkAccess(self, data, check, mutator):
    check.isProgramVisible()
    check.isProfileActive()
    check.isMessagingEnabled()
    mutator.conversationFromKwargs()
    check.isUserInConversation()

  def context(self, data, check, mutator):
    assert access_checker.isSet(data.conversation)
    assert access_checker.isSet(data.user)

    gciconversation_logic.markAllReadForConversationAndUser(
        data.conversation.key,
        ndb.Key.from_old_key(data.user.key()))

    return {
        'page_name': data.conversation.subject,
        'conversation': data.conversation
    }
