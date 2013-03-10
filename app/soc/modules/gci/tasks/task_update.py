# Copyright 2009 the Melange authors.
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

"""Appengine Tasks related to GCI Task handling.
"""


from google.appengine.api import taskqueue
from google.appengine.ext import db

from django import http
from django.conf.urls.defaults import url
from django.utils.translation import ugettext

from soc.tasks.helper import error_handler

from soc.modules.gci.logic import task as task_logic
from soc.modules.gci.models.task import GCITask


class TaskUpdate(object):
  """Tasks that are involved in dealing with GCITasks.
  """

  DEF_TASK_UPDATE_SUBJECT = ugettext(
      '[%(program_name)s Task Update] %(title)s')

  def djangoURLPatterns(self):
    """Returns the URL patterns for the tasks in this module.
    """
    patterns = [
        url(r'^tasks/gci/task/update/(?P<id>(\d+))$', self.updateGCITask,
            name='task_update_GCI_task'),
        ]
    return patterns

  def updateGCITask(self, request, id, *args, **kwargs):
    """Method executed by Task Queue API to update a GCI Task to
    relevant state.

    Args:
      request: the standard Django HTTP request object
    """
    id = int(id)

    task = GCITask.get_by_id(id)

    if not task:
      # invalid task data, log and return OK
      return error_handler.logErrorAndReturnOK(
          'No GCITask found for id: %s' % id)

    task_logic.updateTaskStatus(task)

    return http.HttpResponse()


def spawnUpdateTask(entity, transactional=False):
  """Spawns a task to update the state of the task.
  """
  update_url = '/tasks/gci/task/update/%s' %entity.key().id()
  new_task = taskqueue.Task(eta=entity.deadline,
                            url=update_url)
  new_task.add('gci-update', transactional=transactional)
