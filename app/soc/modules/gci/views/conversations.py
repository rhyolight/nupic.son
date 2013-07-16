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

"""Module containing the conversations list view."""

from google.appengine.ext import ndb

from melange.request import exception
from soc.views.helper import lists
from soc.views.helper import url_patterns

from soc.modules.gci.logic import conversation as gciconversation_logic
from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.templates import conversation_list
from soc.modules.gci.views.helper.url_patterns import url
from soc.modules.gci.views.helper import url_names


class ConversationsList(conversation_list.ConversationList):
  """List to display all the user's conversations for the program."""

  def _getDescription(self):
    """See ConversationList._getDescription for full specification."""
    return 'List of conversations with which you\'re involved.'

  def _getListConfig(self):
    """See ConversationList._getListConfig for full specification."""
    list_config = lists.ListConfiguration()

    list_config.addPlainTextColumn('subject', 'Subject',
        lambda e, *args: e.conversation.get().subject)
    list_config.addPlainTextColumn('last_message_on', 'Last Message Time (raw)',
        lambda e, *args: e.conversation.get().last_message_on,
        hidden=True)
    list_config.addPlainTextColumn('last_message_on_ctime', 'Last Message Time',
        lambda e, *args: e.conversation.get().last_message_on.ctime())

    list_config.setDefaultPagination(50)
    list_config.setDefaultSort('last_message_on')

    return list_config

  def _getQuery(self):
    """See ConversationList._getQuery for full specification."""
    return gciconversation_logic.queryForProgramAndUser(
        ndb.Key.from_old_key(self.data.program.key()),
        ndb.Key.from_old_key(self.data.user.key()))


class ConversationsPage(GCIRequestHandler):
  """View for the conversations page."""

  def templatePath(self):
    """See soc.views.base.RequestHandler.templatePath for full specification."""
    return 'modules/gci/conversations/base.html'

  def djangoURLPatterns(self):
    """See soc.views.base.RequestHandler.djangoURLPatterns for full
    specification."""
    return [
        url(r'conversations/%s$' % url_patterns.PROGRAM, self,
            name='gci_conversations'),
    ]

  def checkAccess(self, data, check, mutator):
    """See soc.views.base.RequestHandler.checkAccess for full specification."""
    check.isProgramVisible()
    check.isProfileActive()

  def jsonContext(self, data, check, mutator):
    """See soc.views.base.RequestHandler.jsonContext for full specification."""
    list_content = ConversationsList(data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def context(self, data, check, mutator):
    """See soc.views.base.RequestHandler.context for full specification."""
    return {
        'page_name': 'Conversations',
        'conversations_list': ConversationsList(data)
    }
