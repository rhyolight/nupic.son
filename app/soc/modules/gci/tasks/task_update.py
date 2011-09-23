#!/usr/bin/env python2.5
#
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

__authors__ = [
    '"Madhusudan.C.S" <madhusudancs@gmail.com>',
    '"Daniel Hans" <dhans@google.com>',
    '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]


import datetime

from google.appengine.api import taskqueue
from google.appengine.ext import db

from django import http
from django.conf.urls.defaults import url
from django.utils.translation import ugettext

from soc.logic import system
from soc.tasks.helper import error_handler
from soc.views.helper import redirects

from soc.modules.gci.logic import task as task_logic
from soc.modules.gci.models.task import GCITask


class TaskUpdate(object):
  """Tasks that are involved in dealing with GCITasks.
  """

  DEF_TASK_UPDATE_SUBJECT_FMT = ugettext(
      '[%(program_name)s Task Update] %(title)s')

  def djangoURLPatterns(self):
    """Returns the URL patterns for the tasks in this module.
    """
    patterns = [
        url(r'^tasks/gci/task/update/(?P<id>(\d+))$', self.updateGCITask,
            name='task_update_GCI_task'),
        url(r'^tasks/gci/task/mail/create$', self.createNotificationMail,
            name='task_create_GCI_comment_notification'),
        url(r'^tasks/gci/task/update/student_status$',
            self.updateTasksPostStudentSignUp, name='task_gci_post_sign_up')]
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

  def createNotificationMail(self, request, *args, **kwargs):
    """Appengine task that sends mail to the subscribed users.

    Expects the following to be present in the POST dict:
      comment_key: Specifies the comment id for which to send the notifications
      task_key: Specifies the task key name for which the comment belongs to

    Args:
      request: Django Request object
    """
    from soc.modules.gci.logic.helper import notifications as gci_notifications

    from soc.modules.gci.logic.models import comment as gci_comment_logic
    from soc.modules.gci.logic.models import task_subscription as \
        gci_task_subscription_logic

    # set default batch size
    batch_size = 10

    post_dict = request.POST

    comment_key = post_dict.get('comment_key')
    task_key = post_dict.get('task_key')

    if not (comment_key and task_key):
      # invalid task data, log and return OK
      return error_handler.logErrorAndReturnOK(
          'Invalid createNotificationMail data: %s' % post_dict)

    comment_key = long(comment_key)

    # get the task entity under which the specified comment was made
    task_entity = gci_task_logic.logic.getFromKeyName(task_key)

    # get the comment for the given id
    comment_entity = gci_comment_logic.logic.getFromID(
        comment_key, task_entity)

    if not comment_entity:
      # invalid comment specified, log and return OK
      return error_handler.logErrorAndReturnOK(
          'Invalid comment specified: %s/%s' % (comment_key, task_key))

    # check and retrieve the subscriber_start_key that has been done last
    idx = post_dict.get('subscriber_start_index', '')
    subscriber_start_index = int(idx) if idx.isdigit() else 0

    # get all subscribers to GCI task
    fields = {
        'task': task_entity,
        }

    ts_entity = gci_task_subscription_logic.logic.getForFields(
        fields, unique=True)

    subscribers = db.get(ts_entity.subscribers[
        subscriber_start_index:subscriber_start_index+batch_size])

    task_url = "http://%(host)s%(task)s" % {
                   'host': system.getHostname(),
                   'task': redirects.getPublicRedirect(
                       task_entity, {'url_name': 'gci/task'}),
                   }

    # create the data for the mail to be sent
    message_properties = {
        'task_url': task_url,
        'redirect_url': "%(task_url)s#c%(cid)d" % {
            'task_url': task_url,
            'cid': comment_entity.key().id_or_name()
            },
        'comment_entity': comment_entity,
        'task_entity': task_entity,
    }

    subject = DEF_TASK_UPDATE_SUBJECT_FMT % {
        'program_name': task_entity.program.short_name,
        'title': task_entity.title,
        }

    for subscriber in subscribers:
      gci_notifications.sendTaskUpdateMail(subscriber, subject,
                                            message_properties)

    if len(subscribers) == batch_size:
      # spawn task for sending out notifications to next set of subscribers
      next_start = subscriber_start_index + batch_size

      task_params = {
          'comment_key': comment_key,
          'task_key': task_key,
          'subscriber_start_index': next_start
          }
      task_url = '/tasks/gci/task/mail/create'

      new_task = taskqueue.Task(params=task_params, url=task_url)
      new_task.add('mail')

    # return OK
    return http.HttpResponse()

  def updateTasksPostStudentSignUp(self, request, *args, **kwargs):
    """Appengine task that updates the GCI Tasks after the student signs up.

    Expects the following to be present in the POST dict:
      student_key: Specifies the student key name who registered

    Args:
      request: Django Request object
    """
    from soc.modules.gci.logic.models import student as gci_student_logic
    from soc.modules.gci.tasks import ranking_update

    post_dict = request.POST

    student_key = post_dict.get('student_key')

    if not student_key:
      # invalid student data, log and return OK
      return error_handler.logErrorAndReturnOK(
          'Invalid Student data: %s' % post_dict)

    student_entity = gci_student_logic.logic.getFromKeyNameOr404(student_key)

    # retrieve all tasks currently assigned to the user
    task_fields = {
        'user': student_entity.user,
        }
    task_entities = gci_task_logic.logic.getForFields(task_fields)

    # TODO(madhusudan) move this to the Task Logic
    # Make sure the tasks store references to the student as well as
    # closing all tasks that are AwaitingRegistration.
    for task_entity in task_entities:
      task_entity.student = student_entity
      if task_entity.status == 'AwaitingRegistration':
        task_entities.remove(task_entity)

        properties = {
            'status': 'Closed',
            'closed_on': datetime.datetime.utcnow()
            }
        changes = [ugettext('User-MelangeAutomatic'),
                   ugettext('Action-Student registered'),
                   ugettext('Status-%s' % (properties['status']))]

        comment_properties = {
            'parent': task_entity,
            'scope_path': task_entity.key().name(),
            'created_by': None,
            'changes': changes,
            'content': ugettext(
                '(The Melange Automated System has detected that the student '
                'has signed up for the program and hence has closed this task.'),
            }

        gci_task_logic.logic.updateEntityPropertiesWithCWS(
            task_entity, properties, comment_properties)

        ranking_update.startUpdatingTask(task_entity)

    db.put(task_entities)

    # return OK
    return http.HttpResponse()


def spawnUpdateTask(entity):
  """Spawns a task to update the state of the task.
  """
  update_url = '/tasks/gci/task/update/%s' %entity.key().id()
  new_task = taskqueue.Task(eta=entity.deadline,
                            url=update_url)
  new_task.add('gci-update')


def spawnCreateNotificationMail(entity):
  """Spawns a task to send mail to the user who has subscribed to the specific
  task.

  Args:
    entity: The Comment entity for which mails must be sent
  """

  task_params = {
      'comment_key': entity.key().id_or_name(),
      'task_key': entity.parent_key().id_or_name(),
      }
  task_url = '/tasks/gci/task/mail/create'

  new_task = taskqueue.Task(params=task_params, url=task_url)
  new_task.add('mail')