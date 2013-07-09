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

"""Module containing the Message and MessageSeen models."""

from google.appengine.ext import ndb

from django.utils import translation

from soc.models import conversation as conversation_model


class Message(ndb.Model):
  """Model of a message within a conversation.

  Parent:
    soc.models.conversation.Conversation
  """

  #: Conversation the message belongs to
  conversation = ndb.KeyProperty(kind=conversation_model.Conversation,
                                 required=True)

  #: User who wrote the message. If None, message was authored by Melange.
  author = ndb.KeyProperty(required=False,
                           verbose_name=translation.ugettext('Author'))

  #: Content of the message
  content = ndb.TextProperty(required=True,
                             verbose_name=translation.ugettext('Message'))

  #: Time when the message was sent
  sent_on = ndb.DateTimeProperty(required=True, auto_now_add=True,
                                 verbose_name=translation.ugettext('Time Sent'))
