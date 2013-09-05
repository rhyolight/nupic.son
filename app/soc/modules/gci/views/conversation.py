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

from django.core import urlresolvers
from django.utils import translation
from django.utils import html

from google.appengine.ext import ndb
from google.appengine.ext import db

from melange.request import exception
from soc.views.helper import url_patterns
from soc.views.helper import access_checker

from soc.logic.helper import timeformat as timeformat_helper
from soc.logic import cleaning

from soc.modules.gci.logic import conversation as gciconversation_logic
from soc.modules.gci.logic import message as gcimessage_logic

from soc.modules.gci.models import message as gcimessage_model

from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views.helper.url_patterns import url
from soc.modules.gci.views.helper import url_names

DEF_BLANK_MESSAGE = translation.ugettext('Your message cannot be blank.')


class PostReply(GCIRequestHandler):
  """View which handles submitting replies."""

  def djangoURLPatterns(self):
    return [
        url(r'conversation/reply/%s$' % url_patterns.ID, self,
            name=url_names.GCI_CONVERSATION_REPLY),
    ]

  def checkAccess(self, data, check, mutator):
    check.isProgramVisible()
    check.isProfileActive()
    check.isMessagingEnabled()
    mutator.conversationFromKwargs()
    check.isUserInConversation()

  def createReplyFromForm(self, data):
    """Creates a new message based on the data inserted into the form.

    Args:
      data: A RequestData object for the current request.

    Returns:
      A newly created message entity.
    """
    assert access_checker.isSet(data.conversation)
    assert access_checker.isSet(data.user)

    content = cleaning.sanitize_html_string(
        data.request.POST['content'].strip())

    if len(html.strip_tags(content).strip()) == 0:
      raise exception.Forbidden(message=DEF_BLANK_MESSAGE)

    author = ndb.Key.from_old_key(data.user.key())

    return gciconversation_logic.createMessage(
        data.conversation.key, author, content)

  def post(self, data, check, mutator):
    message = self.createReplyFromForm(data)
    return data.redirect.id().to(
        name=url_names.GCI_CONVERSATION,
        anchor='m%d' % message.key.integer_id())

  def get(self, data, check, mutator):
    """This view only handles POST."""
    raise exception.MethodNotAllowed()


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

    # Marks the conversation as "read" for the user
    gciconversation_logic.markAllReadForConversationAndUser(
        data.conversation.key,
        ndb.Key.from_old_key(data.user.key()))

    num_users = (
        gciconversation_logic.queryConversationUserForConversation(
            data.conversation.key).count())

    messages = gcimessage_logic.queryForConversation(
        data.conversation.key).order(gcimessage_model.GCIMessage.sent_on)

    for message in messages:
      message.author_name = db.get(ndb.Key.to_old_key(message.author)).name
      message.sent_on_relative = timeformat_helper.relativeTime(message.sent_on)
      message.sent_on_ctime = message.sent_on.ctime()

    return {
        'page_name': data.conversation.subject,
        'conversation': data.conversation,
        'num_users': num_users,
        'messages': messages,
        'reply_action': urlresolvers.reverse(url_names.GCI_CONVERSATION_REPLY, 
            kwargs=data.kwargs)
    }
