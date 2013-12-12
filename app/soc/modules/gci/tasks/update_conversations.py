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

"""Appengine task to update which conversations a GCI user is involved in."""

import logging

from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from django import http
from django.conf import urls

from soc.tasks.helper import error_handler

from soc.modules.gci.logic import conversation as gciconversation_logic
from soc.modules.gci.views.helper import url_names

UPDATE_CONVERSATIONS_URL = '/tasks/gci/task/update_conversations'


class UpdateConversationsTask:
  """Request handlers for task to update a user's involved conversations."""

  def djangoURLPatterns(self):
    """Returns the URL pattern for the task."""
    return [
        urls.url(
            r'^tasks/gci/task/update_conversations$',
            self.updateConversations,
            name=url_names.GCI_TASK_UPDATE_CONVERSATIONS)
        ]

  def updateConversations(self, request, *args, **kwargs):
    """Handler for task.

    The POST dict should have keys:
      user_key: Key string for User.
      program_key: Key string for GCIProgram.
    """

    post_dict = request.POST

    user_key_str = post_dict.get('user_key')
    if not user_key_str:
      return error_handler.logErrorAndReturnOK(
          'user_key missing from POST data.')

    program_key_str = post_dict.get('program_key')
    if not program_key_str:
      return error_handler.logErrorAndReturnOK(
          'program_key missing from POST data.')

    user_key = ndb.Key(urlsafe=user_key_str)
    program_key = ndb.Key(urlsafe=program_key_str)

    gciconversation_logic.refreshConversationsForUserAndProgram(
        user_key, program_key)

    return http.HttpResponse('OK')


def spawnUpdateConversationsTask(user_key, program_key):
  """Spawns a task to update which conversations a GCI user is involved in.

  User must have an associated GCIProfile for the given program.

  Args:
    user_key: Key (ndb) of User.
    program_key: Key (ndb) of GCIProgram.
  """

  task_params = {
      'user_key': user_key.urlsafe(),
      'program_key': program_key.urlsafe(),
      }

  logging.info(
      'Enqueued update_conversations task for user key "%s" and program key '
      '"%s"', task_params['user_key'], task_params['program_key'])

  task = taskqueue.Task(params=task_params, url=UPDATE_CONVERSATIONS_URL)
  task.add()
